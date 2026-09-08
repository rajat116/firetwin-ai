"""NASA FIRMS (Fire Information for Resource Management System) API client.

Official documentation:
- API: https://firms.modaps.eosdis.nasa.gov/api/
- Active Fire Data: https://firms.modaps.eosdis.nasa.gov/active_fire/
- Map Services: https://firms.modaps.eosdis.nasa.gov/map-services/

FIRMS provides active fire/thermal anomaly detections from:
- MODIS (Moderate Resolution Imaging Spectroradiometer)
- VIIRS (Visible Infrared Imaging Radiometer Suite)

Requires a free MAP_KEY from: https://firms.modaps.eosdis.nasa.gov/api/
"""

from datetime import date, datetime
from enum import StrEnum
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from pydantic import BaseModel, Field
from shapely.geometry import Point

from firetwin.settings import settings


class FIRMSSatellite(StrEnum):
    """Available FIRMS satellite instruments."""

    MODIS_C6_1 = "MODIS_NRT"  # MODIS Collection 6.1 NRT
    VIIRS_SNPP = "VIIRS_SNPP_NRT"  # VIIRS S-NPP NRT
    VIIRS_NOAA20 = "VIIRS_NOAA20_NRT"  # VIIRS NOAA-20 NRT


class FIRMSDetection(BaseModel):
    """Single FIRMS active fire detection point."""

    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    brightness: float = Field(..., description="Brightness temperature (Kelvin)")
    scan: float = Field(..., description="Along-scan pixel size (km)")
    track: float = Field(..., description="Along-track pixel size (km)")
    acq_date: date = Field(..., description="Acquisition date")
    acq_time: str = Field(..., description="Acquisition time (HHMM UTC)")
    satellite: str = Field(..., description="Satellite identifier")
    instrument: str = Field(..., description="Instrument name")
    confidence: int | str = Field(
        ..., description="Detection confidence (0-100 or low/nominal/high)"
    )
    version: str = Field(..., description="Collection version")
    bright_t31: float | None = Field(None, description="Brightness temperature I-4 channel (K)")
    frp: float = Field(..., description="Fire Radiative Power (MW)")
    daynight: str = Field(..., description="Day or night detection (D/N)")

    class Config:
        """Pydantic config."""

        frozen = True

    @property
    def acquisition_datetime(self) -> datetime:
        """Parse acquisition date and time into datetime."""
        time_str = self.acq_time.zfill(4)  # Ensure 4 digits (HHMM)
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        return datetime.combine(self.acq_date, datetime.min.time()).replace(
            hour=hour, minute=minute, tzinfo=None
        )

    def to_point(self) -> Point:
        """Convert detection to Shapely Point geometry."""
        return Point(self.longitude, self.latitude)


class FIRMSClient:
    """Client for NASA FIRMS active fire data API.

    Attributes:
        map_key: FIRMS API key (obtain from https://firms.modaps.eosdis.nasa.gov/api/)
        base_url: FIRMS API base URL
    """

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"

    def __init__(self, map_key: str | None = None) -> None:
        """Initialize FIRMS client.

        Args:
            map_key: FIRMS MAP_KEY. If None, reads from settings.firms_map_key

        Raises:
            ValueError: If no API key is provided
        """
        self.map_key = map_key or settings.firms_map_key
        if not self.map_key:
            raise ValueError(
                "FIRMS MAP_KEY is required. Provide via map_key parameter or FIRMS_MAP_KEY environment variable"
            )
        if not self.map_key:
            raise ValueError(
                "FIRMS MAP_KEY is required. Set FIRMS_MAP_KEY environment variable "
                "or pass map_key parameter. Get a key from: "
                "https://firms.modaps.eosdis.nasa.gov/api/"
            )

    def get_area_detections(
        self,
        satellite: FIRMSSatellite,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        day_range: int = 1,
        date: date | None = None,
    ) -> list[FIRMSDetection]:
        """Fetch active fire detections for a bounding box area.

        Args:
            satellite: Satellite instrument to query
            min_lon: Minimum longitude (west bound)
            min_lat: Minimum latitude (south bound)
            max_lon: Maximum longitude (east bound)
            max_lat: Maximum latitude (north bound)
            day_range: Number of days to fetch (1-10)
            date: Specific date to query. If None, uses most recent data

        Returns:
            List of FIRMSDetection objects

        Raises:
            ValueError: If parameters are invalid
            requests.HTTPError: If API request fails
        """
        if not (-180 <= min_lon <= 180) or not (-180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= min_lat <= 90) or not (-90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not 1 <= day_range <= 10:
            raise ValueError("day_range must be between 1 and 10")

        # Build URL
        if date:
            date_str = date.strftime("%Y-%m-%d")
            url = (
                f"{self.BASE_URL}/area/csv/{self.map_key}/{satellite.value}/"
                f"{min_lon},{min_lat},{max_lon},{max_lat}/{day_range}/{date_str}"
            )
        else:
            url = (
                f"{self.BASE_URL}/area/csv/{self.map_key}/{satellite.value}/"
                f"{min_lon},{min_lat},{max_lon},{max_lat}/{day_range}"
            )

        # Fetch data
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse CSV
        return self._parse_csv_response(response.text)

    def get_country_detections(
        self,
        satellite: FIRMSSatellite,
        country_code: str,
        day_range: int = 1,
        date: date | None = None,
    ) -> list[FIRMSDetection]:
        """Fetch active fire detections for a country.

        Args:
            satellite: Satellite instrument to query
            country_code: Two-letter ISO country code (e.g., 'US', 'CA')
            day_range: Number of days to fetch (1-10)
            date: Specific date to query. If None, uses most recent data

        Returns:
            List of FIRMSDetection objects

        Raises:
            ValueError: If parameters are invalid
            requests.HTTPError: If API request fails
        """
        if len(country_code) != 2:
            raise ValueError("country_code must be 2-letter ISO code (e.g., 'US')")
        if not 1 <= day_range <= 10:
            raise ValueError("day_range must be between 1 and 10")

        # Build URL
        country_upper = country_code.upper()
        if date:
            date_str = date.strftime("%Y-%m-%d")
            url = (
                f"{self.BASE_URL}/country/csv/{self.map_key}/{satellite.value}/"
                f"{country_upper}/{day_range}/{date_str}"
            )
        else:
            url = (
                f"{self.BASE_URL}/country/csv/{self.map_key}/{satellite.value}/"
                f"{country_upper}/{day_range}"
            )

        # Fetch data
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse CSV
        return self._parse_csv_response(response.text)

    def _parse_csv_response(self, csv_text: str) -> list[FIRMSDetection]:
        """Parse CSV response from FIRMS API into detection objects.

        Args:
            csv_text: Raw CSV text from API

        Returns:
            List of FIRMSDetection objects
        """
        # FIRMS CSV format has header row
        lines = csv_text.strip().split("\n")
        if len(lines) < 2:
            return []  # No detections

        # Parse with pandas
        from io import StringIO

        df = pd.read_csv(StringIO(csv_text))

        # Convert to detection objects
        detections = []
        for _, row in df.iterrows():
            detection = FIRMSDetection(
                latitude=row["latitude"],
                longitude=row["longitude"],
                brightness=row["brightness"],
                scan=row["scan"],
                track=row["track"],
                acq_date=pd.to_datetime(row["acq_date"]).date(),
                acq_time=str(row["acq_time"]).zfill(4),
                satellite=row["satellite"],
                instrument=row["instrument"],
                confidence=row["confidence"],
                version=row["version"],
                bright_t31=row.get("bright_t31"),
                frp=row["frp"],
                daynight=row["daynight"],
            )
            detections.append(detection)

        return detections

    def detections_to_geodataframe(
        self, detections: list[FIRMSDetection], crs: str = "EPSG:4326"
    ) -> gpd.GeoDataFrame:
        """Convert FIRMS detections to GeoDataFrame.

        Args:
            detections: List of FIRMSDetection objects
            crs: Coordinate reference system (default: WGS84)

        Returns:
            GeoDataFrame with detection points and attributes
        """
        if not detections:
            # Return empty GeoDataFrame with correct schema
            return gpd.GeoDataFrame(
                columns=[
                    "geometry",
                    "acquisition_datetime",
                    "brightness",
                    "confidence",
                    "frp",
                    "satellite",
                    "daynight",
                ],
                crs=crs,
            )

        # Build GeoDataFrame
        data = {
            "geometry": [d.to_point() for d in detections],
            "acquisition_datetime": [d.acquisition_datetime for d in detections],
            "brightness": [d.brightness for d in detections],
            "scan_km": [d.scan for d in detections],
            "track_km": [d.track for d in detections],
            "confidence": [d.confidence for d in detections],
            "frp": [d.frp for d in detections],
            "satellite": [d.satellite for d in detections],
            "instrument": [d.instrument for d in detections],
            "daynight": [d.daynight for d in detections],
            "version": [d.version for d in detections],
        }

        gdf = gpd.GeoDataFrame(data, crs=crs)
        return gdf

    def save_detections(
        self,
        detections: list[FIRMSDetection],
        output_path: Path,
        format: str = "parquet",
    ) -> None:
        """Save FIRMS detections to file.

        Args:
            detections: List of FIRMSDetection objects
            output_path: Output file path
            format: Output format ('parquet', 'geojson', 'csv')

        Raises:
            ValueError: If format is not supported
        """
        gdf = self.detections_to_geodataframe(detections)

        if format == "parquet":
            gdf.to_parquet(output_path)
        elif format == "geojson":
            gdf.to_file(output_path, driver="GeoJSON")
        elif format == "csv":
            # Drop geometry for CSV
            df = pd.DataFrame(gdf.drop(columns="geometry"))
            df["latitude"] = gdf.geometry.y
            df["longitude"] = gdf.geometry.x
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'parquet', 'geojson', or 'csv'")
