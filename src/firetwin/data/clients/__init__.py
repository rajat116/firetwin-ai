"""Data source clients for external APIs and services."""

from firetwin.data.clients.era5 import ERA5LandClient
from firetwin.data.clients.firms import (
    FIRMS_MAX_DAY_RANGE,
    FIRMSClient,
    FIRMSDetection,
    FIRMSSatellite,
)
from firetwin.data.clients.landfire import LANDFIREClient
from firetwin.data.clients.mtbs import MTBSClient, MTBSFire
from firetwin.data.clients.nifc import NIFCClient
from firetwin.data.clients.nifc_historical import (
    NIFCHistoricalClient,
    NIFCHistoricalPerimeter,
)
from firetwin.data.clients.usgs import USGS3DEPClient

__all__ = [
    "ERA5LandClient",
    "FIRMS_MAX_DAY_RANGE",
    "FIRMSClient",
    "FIRMSDetection",
    "FIRMSSatellite",
    "LANDFIREClient",
    "MTBSClient",
    "MTBSFire",
    "NIFCClient",
    "NIFCHistoricalClient",
    "NIFCHistoricalPerimeter",
    "USGS3DEPClient",
]
