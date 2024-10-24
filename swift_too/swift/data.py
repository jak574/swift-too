import os
import warnings
from fnmatch import fnmatch

import boto3
import requests
from botocore import UNSIGNED
from botocore.client import Config

from ..base.common import TOOAPIBaseClass
from ..base.status import TOOStatus
from .obsid import TOOAPIObsID

try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        """A real simple replacement for tqdm if it's not locally installed"""
        if "display" in kwargs.keys() and kwargs["display"] is not False:
            print(f"Downloading {len(args[0])} files...")
        return args[0]


class SwiftDataFile(TOOAPIBaseClass):
    """Class containing information about a swift data file that can be
    downloaded from the Swift Science Data Center

    Attributes:
    ----------
    filename : str
        filename
    path : str
        path to file
    url : str
        URL where file exists
    type : str
        Text description of file type
    localpath : str
        full path of file on disk
    size : int
        size of file in bytes
    outdir : str
        local directory in which to download file (default '.')
    """

    # API name
    api_name = "SwiftData_File"
    # Attributes
    filename = None
    path = None
    url = None
    quicklook = None
    type = None
    localpath = None
    s3 = None
    outdir = "."
    # Core API definitions
    _parameters = ["filename", "path", "url", "quicklook", "type"]
    _attributes = ["size", "localpath"]

    @property
    def size(self):
        if self.localpath is not None:
            return os.path.getsize(self.localpath)
        else:
            return None

    def download(self, outdir=None):
        """Download the file into a given `outdir`"""
        if outdir is not None:
            self.outdir = outdir
        # Make the directories for the full path if they don't exist
        fulldir = os.path.join(self.outdir, self.path)
        if not os.path.exists(fulldir):
            os.makedirs(fulldir)

        # Download the data
        fullfilepath = os.path.join(self.outdir, self.path, self.filename)

        if "heasarc" in self.url and self.quicklook is False and self.s3 is not None:
            # Download HEASARC hosted data from AWS
            key_name = self.url.replace("https://heasarc.gsfc.nasa.gov/FTP/", "")
            self.s3.download_file("nasa-heasarc", key_name, fullfilepath)
        else:
            r = requests.get(self.url, stream=True, allow_redirects=True)
            if r.ok:
                filedata = r.raw.read()
                with open(fullfilepath, "wb") as outfile:
                    outfile.write(filedata)
                self.localpath = fullfilepath
            else:
                return False

        return True


class SwiftData(TOOAPIBaseClass, TOOAPIObsID):
    """
    Class to download Swift data from the UK or US SDC for a given observation
    ID.

    Attributes
    ----------
    obsid : str / int
        the observation ID of the data to download. Can be in SDC or spacecraft
        format. Note: can also use target_id and segment, but must supply both.
    auxil : boolean
        Set to True to download Auxillary data (default = True)
    bat : boolean
        Set to True to download BAT data.
    xrt : boolean
        Set to True to download XRT data.
    uvot : boolean
        Set to True to download UVOT data.
    log : boolean
        Set to True to download SDC processing logs.
    all : boolean
        Set to True to download all data products.
    quicklook : boolean
        Set to True to only search Quicklook data. Default searches archive,
        then quicklook if the data are not there. If data are known to be recent
        this may speed up result.
    clobber : boolean
        overwrite existing data on disk (default: False)
    outdir : str
        Directory where data should be downloaded to.
    fetch : boolean
        Download the data straight away (default: True).
    quiet  : boolean
        When downloading, don't print anything out. (default: False)
    entries : list
        List of files associated with data (')
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    status : TOOStatus
        Status of API request
    """

    # Core API definitions
    api_name = "SwiftData"
    # Classes used by this class
    _subclasses = [SwiftDataFile, TOOStatus]
    # Values to send and return through the API
    _parameters = [
        "username",
        "obsid",
        "quicklook",
        "auxil",
        "bat",
        "xrt",
        "uvot",
        "subthresh",
        "log",
        "tdrss",
        "uksdc",
        "itsdc",
    ]
    # Local and alias parameters
    _local = [
        "outdir",
        "clobber",
        "obsnum",
        "targetid",
        "target_id",
        "seg",
        "segment",
        "shared_secret",
        "fetch",
        "match",
        "quiet",
        "aws",
    ]
    _attributes = ["entries", "status"]

    def __init__(self, *args, **kwargs):
        """
        Construct the SwiftData class, and download data if required parameters
        are supplied.

        Parameters
        ----------
        obsid : str / int
            the observation ID of the data to download. Can be in SDC or
            spacecraft format. Note: can also use target_id and segment, but
            must supply both.
        auxil : boolean
            Set to True to download Auxillary data (default = True)
        bat : boolean
            Set to True to download BAT data.
        xrt : boolean
            Set to True to download XRT data.
        uvot : boolean
            Set to True to download UVOT data.
        subthresh : boolean
            Set to True to download BAT Subthreshold trigger data
        log : boolean
            Set to True to download SDC processing logs.
        all : boolean
            Set to True to download all data products.
        uksdc : boolean
            Set to True to download from the UK Swift SDC
        itsdc : boolean
            Set to True to download from the Italian Swift SDC
        quicklook : boolean
            Set to True to only search Quicklook data. Default searches archive,
            then quicklook if the data are not there. If data are known to be
            recent this may speed up result.
        clobber : boolean
            overwrite existing data on disk (default: False)
        outdir : str
            Directory where data should be downloaded to.
        fetch : boolean
            Download the data straight away (default: True).
        quiet : boolean
            When downloading, don't print anything out. (default: False)
        match : str / list
            Only download files matching this filename pattern (e.g.
            "*xrt*pc*"). If multiple templates are given as a list, files
            matching any of filename patterns will be downloaded. Uses standard
            UNIX style filename pattern matching with Python `fnmatch` module.
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        aws : boolean
            Download data from AWS instead of HEASARC (note only if uksdc and itsdc
            are False). (default 'False').
        """
        # Parameters
        self.username = "anonymous"
        self.obsid = None
        # Only look in quicklook
        self.quicklook = False
        # Download data from AWS instead of HEASARC
        self.aws = False
        # Download from UK SDC
        self.uksdc = None
        # Download from the Italian SDC
        self.itsdc = None
        # Data types to download. Always download auxil as default
        self.auxil = True
        self.bat = None
        self.uvot = None
        self.xrt = None
        self.tdrss = None
        self.subthresh = None
        self.log = None
        # Should we display anything when downloading
        self.quiet = False
        # Download data straight away
        self.fetch = True
        # Only download files matching this expression
        self.match = None
        # Default to not overwrite existing data
        self.clobber = False
        # Directory to save data
        self.outdir = "."
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # The resultant data
        self.entries = list()
        self.status = TOOStatus()

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
            # ...and if requested, download the data
            if self.fetch:
                self.download()
        else:
            self.status.clear()

    def __getitem__(self, i):
        return self.entries[i]

    @property
    def _table(self):
        header = ["Path", "Filename", "Description"]
        tabdata = []
        lastpath = ""
        for file in self.entries:
            if file.path != lastpath:
                path = file.path
                lastpath = path
            else:
                path = "''"
            tabdata.append([path, file.filename, file.type])
        return header, tabdata

    @property
    def all(self):
        if (
            self.xrt
            and self.uvot
            and self.bat
            and self.log
            and self.auxil
            and self.tdrss
        ):
            return True
        return False

    @all.setter
    def all(self, bool):
        if self.all is not None:
            self.xrt = self.bat = self.uvot = self.log = self.auxil = self.tdrss = bool

    def _post_process(self):
        """A place to do things to API results after they have been fetched."""
        # Filter out files that don't match `match` expression
        if not self.uksdc and not self.itsdc and self.aws is True:
            # Set up S3 stuff
            config = Config(
                connect_timeout=5,
                retries={"max_attempts": 0},
                signature_version=UNSIGNED,
            )
            s3 = boto3.client("s3", config=config)
            for file in self.entries:
                file.s3 = s3
        if self.match is not None:
            if isinstance(self.match, str):
                self.match = [self.match]
            i = 0
            while i < len(self.entries):
                keep = False
                for match in self.match:
                    if fnmatch(
                        f"{self.entries[i].path}/{self.entries[i].filename}",
                        match,
                    ):
                        keep = True
                if not keep:
                    del self.entries[i]
                else:
                    i += 1

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if self.uksdc is True and self.itsdc is True:
            self.status.error("Cannot download from UK and Italian SDC")
        if self.obsid is None:
            self.status.error("Must supply Observation ID")
        if (
            self.auxil is not True
            and self.xrt is not True
            and self.log is not True
            and self.bat is not True
            and self.uvot is not True
            and self.subthresh is not True
        ):
            self.status.error("No data products selected")
            self.status.status = "Rejected"
        if len(self.status.errors) > 0:
            return False
        else:
            return True

    def download(self, outdir=None):
        """Download Swift data for selected instruments to `outdir`"""
        # If outdir is passed as an argument, update the value
        if outdir is not None:
            self.outdir = outdir

        # If no files, return error
        if len(self.entries) == 0:
            self.status.error(f"No data found for {self.obsid}.")
            self.status.status = "Rejected"
            return False

        # Translate any ~, "." and $ENV in the output path
        if self.outdir == "" or self.outdir is None:
            self.outdir = "."
        self.outdir = os.path.expanduser(self.outdir)
        self.outdir = os.path.expandvars(self.outdir)
        self.outdir = os.path.abspath(self.outdir)

        # Index any existing files
        for i in range(len(self.entries)):
            fullfilepath = os.path.join(
                self.outdir, self.entries[i].path, self.entries[i].filename
            )
            if os.path.exists(fullfilepath):
                self.entries[i].localpath = fullfilepath

        # Download files to outdir
        if self.quiet:
            dfiles = self.entries
        else:
            dfiles = tqdm(self.entries, desc="Downloading files", unit="files")
        for dfile in dfiles:
            # Don't re-download a file unless clobber=True
            localfile = f"{self.outdir}/{dfile.path}/{dfile.filename}"
            if not self.clobber and os.path.exists(localfile) and not self.quiet:
                warnings.warn(
                    f"{dfile.filename} exists and not overwritten (set clobber=True to override this)."
                )
            elif not dfile.download(outdir=self.outdir):
                self.status.error(f"Error downloading {dfile.filename}")
                return False

        # Everything worked we assume so return True
        return True


# Shorthand Aliases for better PEP8 compliant and future compat
Data = SwiftData
DataFile = SwiftDataFile
SwiftData_File = SwiftDataFile


class TOOAPIDownloadData:
    """Mixin to add add download method to any class that has an associated obsid."""

    def download(self, *args, **kwargs):
        """Download data from SDC"""
        # Set up the Data class
        data = SwiftData()
        params = SwiftData._parameters + SwiftData._local
        # Read in arguments
        for i in range(len(args)):
            setattr(data, params[i + 1], args[i])
        # Parse argument keywords
        for key in kwargs.keys():
            if key in params + self._local:
                setattr(data, key, kwargs[key])
            else:
                raise TypeError(
                    f"{self.api_name} got an unexpected keyword argument '{key}'"
                )
        # Set up and download data
        data.obsid = self.obsid
        data.username = self.username
        data.shared_secret = self.shared_secret
        data.submit()
        if data.fetch:
            data.download()
        # Return the SwiftData class on completion
        return data
