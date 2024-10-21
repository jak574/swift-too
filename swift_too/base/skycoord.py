HAS_ASTROPY = False
try:
    import astropy.units as u  # type: ignore[import]
    from astropy.coordinates import SkyCoord  # type: ignore[import]
    from astropy.coordinates.angles import Latitude, Longitude  # type: ignore[import]

    HAS_ASTROPY = True
except ImportError:
    pass


class SkyCoordSchema:
    """Add Skycoord support to any class that has ra and dec properties."""

    @property
    def skycoord(self):
        """Allow TOO requesters to give an astropy SkyCoord object instead of
        RA/Dec. Handy if you want to do things like submit 1950 coordinates or
        Galactic Coordinates."""
        # Check if the RA/Dec match the SkyCoord, and if they don't modify the skycoord
        if HAS_ASTROPY:
            return SkyCoord(self.ra, self.dec, unit="deg", frame="fk5")
        else:
            raise ImportError("To use skycoord, astropy needs to be installed.")

    @skycoord.setter
    def skycoord(self, sc):
        """Convert the SkyCoord into RA/Dec (J2000) when set."""
        if HAS_ASTROPY:
            if sc is None:
                self._skycoord = None
            elif type(sc) is SkyCoord:
                self._skycoord = sc
                self.ra = sc.fk5.ra.deg
                self.dec = sc.fk5.dec.deg
            else:
                raise TypeError("Needs to be assigned an Astropy SkyCoord")
        else:
            raise ImportError("To use skycoord, astropy needs to be installed.")


class TOOAPISkyCoord(SkyCoordSchema):
    """Mixin to support for using a SkyCoord in place of RA/Dec. Note that
    swift_too only support SkyCoords if astropy itself is installed. astropy is
    not a dependency for swift_too so will not get installed if you don't already
    have it."""

    _skycoord = None
    _radius = None
    _ra = None
    _dec = None

    @property
    def ra(self):
        return self._ra

    @ra.setter
    def ra(self, ra):
        if HAS_ASTROPY and (type(ra) is u.quantity.Quantity or type(ra) is Longitude):
            ra = ra.to(u.deg).value
        self._ra = ra

    @property
    def dec(self):
        return self._dec

    @dec.setter
    def dec(self, dec):
        if HAS_ASTROPY and (type(dec) is u.quantity.Quantity or type(dec) is Latitude):
            dec = dec.to(u.deg).value
        self._dec = dec

    @property
    def radius(self):
        if self.ra is not None and self.dec is not None and self._radius is None:
            # Set the default radius if coordinates are given
            self._radius = 11.8 / 60  # Default 11.8 arcmin - XRT FOV
        return self._radius

    @radius.setter
    def radius(self, radius):
        if HAS_ASTROPY and type(radius) is u.quantity.Quantity:
            radius = radius.to(u.deg).value
        self._radius = radius

    # poserr - used by TOO request for position error in arcmins
    @property
    def poserr(self):
        return self._poserr

    @poserr.setter
    def poserr(self, poserr):
        if HAS_ASTROPY and type(poserr) is u.quantity.Quantity:
            poserr = poserr.to(u.arcmin).value
        self._poserr = poserr

    # Aliases
    RA = ra
    declination = dec
