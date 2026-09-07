"""Historical fire case builder.

This module provides tools to build complete FireCase objects from
real-world data sources, integrating multiple data streams into the
canonical format for model training and evaluation.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from firetwin.data.clients import (
    ERA5LandClient,
    FIRMSClient,
    LANDFIREClient,
    MTBSClient,
    NIFCClient,
    USGS3DEPClient,
)
from firetwin.schemas.fire_case import FireCase


@dataclass
class CaseBuilderConfig:
    """Configuration for building a fire case."""

    fire_id: str
    fire_name: str
    bbox: tuple[float, float, float, float]  # (minx, miny, maxx, maxy) WGS84
    start_date: date
    end_date: date
    grid_resolution_m: float = 60.0  # Default 60m grid

    # API credentials
    firms_map_key: str | None = None
    cds_api_url: str | None = None
    cds_api_key: str | None = None

    # Data source flags
    fetch_firms: bool = True
    fetch_nifc: bool = True
    fetch_mtbs: bool = True
    fetch_era5: bool = True
    fetch_landfire: bool = False  # Manual download required
    fetch_3dep: bool = True


class FireCaseBuilder:
    """Build complete FireCase objects from real-world data sources.
    
    This class orchestrates data acquisition from multiple sources,
    spatial/temporal alignment, and conversion to canonical format.
    """

    def __init__(self, config: CaseBuilderConfig) -> None:
        """Initialize fire case builder.
        
        Args:
            config: Case builder configuration
        """
        self.config = config

        # Initialize data clients
        self.firms_client = None
        if config.fetch_firms and config.firms_map_key:
            self.firms_client = FIRMSClient(map_key=config.firms_map_key)

        self.nifc_client = None
        if config.fetch_nifc:
            self.nifc_client = NIFCClient()

        self.mtbs_client = None
        if config.fetch_mtbs:
            self.mtbs_client = MTBSClient()

        self.era5_client = None
        if config.fetch_era5:
            if config.cds_api_url and config.cds_api_key:
                self.era5_client = ERA5LandClient(
                    url=config.cds_api_url, key=config.cds_api_key
                )
            else:
                # Try using ~/.cdsapirc
                try:
                    self.era5_client = ERA5LandClient()
                except Exception:
                    pass  # Skip if credentials not available

        self.landfire_client = None
        if config.fetch_landfire:
            self.landfire_client = LANDFIREClient()

        self.usgs_client = None
        if config.fetch_3dep:
            self.usgs_client = USGS3DEPClient()

        # Data storage
        self.raw_data: dict[str, Any] = {}

    def fetch_all_data(self) -> dict[str, Any]:
        """Fetch all available data for this fire case.
        
        Returns:
            Dictionary with data from each source
        """
        print(f"Fetching data for {self.config.fire_name}...")

        # Fetch FIRMS detections
        if self.firms_client:
            print("  - Fetching FIRMS detections...")
            try:
                minx, miny, maxx, maxy = self.config.bbox
                # FIRMS uses day_range parameter
                days = (self.config.end_date - self.config.start_date).days + 1

                detections = self.firms_client.get_area_detections(
                    bbox=(minx, miny, maxx, maxy),
                    start_date=self.config.start_date.isoformat(),
                    day_range=min(days, 10),  # FIRMS limits to 10 days
                )

                self.raw_data["firms"] = detections
                print(f"    Found {len(detections)} detections")
            except Exception as e:
                print(f"    FIRMS fetch failed: {e}")
                self.raw_data["firms"] = []

        # Fetch NIFC perimeters
        if self.nifc_client:
            print("  - Fetching NIFC perimeters...")
            try:
                perimeters = self.nifc_client.get_fire_by_name(
                    fire_name=self.config.fire_name
                )
                self.raw_data["nifc"] = perimeters
                print(f"    Found {len(perimeters)} perimeters")
            except Exception as e:
                print(f"    NIFC fetch failed: {e}")
                self.raw_data["nifc"] = []

        # Fetch MTBS perimeter
        if self.mtbs_client:
            print("  - Fetching MTBS perimeter...")
            try:
                fires = self.mtbs_client.get_fire_by_name(
                    fire_name=self.config.fire_name
                )
                self.raw_data["mtbs"] = fires
                print(f"    Found {len(fires)} MTBS records")
            except Exception as e:
                print(f"    MTBS fetch failed: {e}")
                self.raw_data["mtbs"] = []

        # Fetch ERA5-Land weather
        if self.era5_client:
            print("  - Fetching ERA5-Land weather...")
            try:
                output_path = Path(f"data/raw/era5/{self.config.fire_id}.nc")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                weather_path = self.era5_client.download_area(
                    bbox=self.config.bbox,
                    start_date=self.config.start_date,
                    end_date=self.config.end_date,
                    output_path=output_path,
                )

                self.raw_data["era5"] = str(weather_path)
                print(f"    Downloaded to {weather_path}")
            except Exception as e:
                print(f"    ERA5 fetch failed: {e}")
                self.raw_data["era5"] = None

        # Fetch USGS 3DEP elevation
        if self.usgs_client:
            print("  - Fetching USGS 3DEP elevation...")
            try:
                output_dir = Path(f"data/raw/3dep/{self.config.fire_id}")
                output_dir.mkdir(parents=True, exist_ok=True)

                dem_files = self.usgs_client.download_bbox(
                    bbox=self.config.bbox,
                    output_dir=output_dir,
                )

                self.raw_data["3dep"] = [str(f) for f in dem_files]
                print(f"    Downloaded {len(dem_files)} DEM tiles")
            except Exception as e:
                print(f"    3DEP fetch failed: {e}")
                self.raw_data["3dep"] = []

        # LANDFIRE requires manual download
        if self.landfire_client:
            print("  - LANDFIRE: Manual download required")
            print("    Visit: https://landfire.gov/getdata.php")
            print(f"    AOI: {self.config.bbox}")
            self.raw_data["landfire"] = None

        return self.raw_data

    def get_data_summary(self) -> dict[str, Any]:
        """Get summary of fetched data.
        
        Returns:
            Dictionary with data availability and counts
        """
        summary = {
            "fire_id": self.config.fire_id,
            "fire_name": self.config.fire_name,
            "date_range": f"{self.config.start_date} to {self.config.end_date}",
            "bbox": self.config.bbox,
            "data_sources": {},
        }

        if "firms" in self.raw_data:
            summary["data_sources"]["FIRMS"] = {
                "available": len(self.raw_data["firms"]) > 0,
                "count": len(self.raw_data["firms"]),
            }

        if "nifc" in self.raw_data:
            summary["data_sources"]["NIFC"] = {
                "available": len(self.raw_data["nifc"]) > 0,
                "count": len(self.raw_data["nifc"]),
            }

        if "mtbs" in self.raw_data:
            summary["data_sources"]["MTBS"] = {
                "available": len(self.raw_data["mtbs"]) > 0,
                "count": len(self.raw_data["mtbs"]),
            }

        if "era5" in self.raw_data:
            summary["data_sources"]["ERA5"] = {
                "available": self.raw_data["era5"] is not None,
                "path": self.raw_data["era5"],
            }

        if "3dep" in self.raw_data:
            summary["data_sources"]["3DEP"] = {
                "available": len(self.raw_data["3dep"]) > 0,
                "count": len(self.raw_data["3dep"]),
            }

        if "landfire" in self.raw_data:
            summary["data_sources"]["LANDFIRE"] = {
                "available": self.raw_data["landfire"] is not None,
                "note": "Manual download required",
            }

        return summary

    def build_case(self) -> FireCase | None:
        """Build complete FireCase from fetched data.
        
        Returns:
            FireCase object or None if insufficient data
        
        Note:
            This is a placeholder. Full implementation requires:
            - Spatial alignment and regridding
            - Temporal interpolation
            - CRS reprojection
            - Grid creation
        """
        # This will be implemented in subsequent steps
        raise NotImplementedError(
            "Full case building not yet implemented. "
            "Use fetch_all_data() and get_data_summary() for now."
        )
