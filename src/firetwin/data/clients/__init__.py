"""Data source clients for external APIs and services."""

from firetwin.data.clients.era5 import ERA5LandClient
from firetwin.data.clients.firms import FIRMSClient
from firetwin.data.clients.landfire import LANDFIREClient
from firetwin.data.clients.mtbs import MTBSClient
from firetwin.data.clients.nifc import NIFCClient
from firetwin.data.clients.nifc_historical import NIFCHistoricalClient
from firetwin.data.clients.usgs import USGS3DEPClient

__all__ = [
    "ERA5LandClient",
    "FIRMSClient",
    "LANDFIREClient",
    "MTBSClient",
    "NIFCClient",
    "NIFCHistoricalClient",
    "USGS3DEPClient",
]
