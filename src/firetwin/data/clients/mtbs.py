"""MTBS (Monitoring Trends in Burn Severity) API client.

Official documentation:
- Portal: https://www.mtbs.gov
- Burn Severity Portal: https://burnseverity.cr.usgs.gov
- Direct Download: https://burnseverity.cr.usgs.gov/direct-download
- REST Services: https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer

MTBS provides final burned area boundaries and burn severity data for large fires:
- Western US: fires > 1,000 acres
- Eastern US: fires > 500 acres
- Data from 1984 to present using Landsat imagery
- Includes burn severity classifications

Partnership between USGS EROS and USDA Forest Service GTAC.
"""

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import requests
from pydantic import BaseModel, Field
from shapely.geometry import shape


class MTBSFire(BaseModel):
    """Single MTBS fire perimeter with burn severity metadata."""

    fire_id: str = Field(..., description="Unique MTBS fire identifier")
    fire_name: str = Field(..., description="Fire name")
    fire_year: int = Field(..., description="Fire year (extracted from fire_id)")
    ignition_date: datetime | None = Field(
        None, description="Ignition date (from ig_date timestamp)"
    )
    acres: float = Field(..., description="Fire size in acres")
    fire_type: str | None = Field(None, description="Fire type (Wildfire, Prescribed, Unknown)")
    geometry_wkt: str = Field(..., description="Polygon geometry as WKT")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def to_shapely_polygon(self) -> shape:
        """Convert WKT geometry to Shapely polygon.

        Returns:
            Shapely polygon geometry
        """
        from shapely import wkt

        return wkt.loads(self.geometry_wkt)


class MTBSClient:
    """Client for MTBS burned area boundary API."""

    # MTBS uses multiple layers by year - we'll query all via layer 0 (all years)
    BASE_URL = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/0/query"

    DEFAULT_HEADERS = {
        "User-Agent": "FireTwin/1.0 (Research Project; https://github.com/rajat116/firetwin-ai)",
        "Accept": "application/json",
    }

    def __init__(self, timeout: int = 30) -> None:
        """Initialize MTBS client.

        Args:
            timeout: HTTP request timeout in seconds (default: 30)
        """
        self.timeout = timeout

    def get_fires_by_year(
        self,
        year: int,
        min_acres: float | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        max_records: int = 2000,
    ) -> list[MTBSFire]:
        """Get MTBS fire perimeters for a specific year.

        Args:
            year: Fire year (1984-present)
            min_acres: Minimum fire size in acres
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            max_records: Maximum number of records to return (max 2000)

        Returns:
            List of MTBSFire objects

        Raises:
            ValueError: If max_records > 2000 or year < 1984

        Note:
            MTBS API does not have a Fire_Year field. This method fetches all fires
            within the bbox/criteria and filters by year in Python after parsing.
        """
        if max_records > 2000:
            raise ValueError("max_records cannot exceed 2000 (ESRI API limit)")
        if year < 1984:
            raise ValueError("MTBS data starts from 1984")

        if not bbox:
            raise ValueError(
                "bbox is required for year queries - MTBS API does not support "
                "temporal filtering, so spatial bounds are needed to limit results"
            )

        # Build where clause
        # Note: MTBS API does not support ig_date range queries (returns 400 error)
        # Year filtering is done in Python after fetch using fire_id date extraction
        where_conditions = ["1=1"]  # Get all records within bbox
        if min_acres:
            where_conditions.append(f"acres>={min_acres}")

        where_clause = " AND ".join(where_conditions)

        # Build query parameters (use lowercase field names)
        params = {
            "where": where_clause,
            "outFields": "fire_id,fire_name,acres,ig_date,fire_type",
            "f": "geojson",
            "outSR": "4326",  # WGS84
            "returnGeometry": "true",
            "resultRecordCount": max_records,
            "geometryPrecision": 6,
        }

        # Add bbox geometry filter if provided
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            params["geometry"] = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"

        # Make request
        response = requests.get(
            self.BASE_URL,
            params=params,
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()

        # Parse GeoJSON response
        geojson_data = response.json()
        all_fires = self._parse_geojson_response(geojson_data)

        # Filter by year in Python (year extracted from fire_id during parsing)
        return [f for f in all_fires if f.fire_year == year]

    def get_fire_by_name(self, fire_name: str, year: int | None = None) -> list[MTBSFire]:
        """Get MTBS fires by name (partial match supported).

        Args:
            fire_name: Fire name (partial match)
            year: Optional year filter (applied in Python after fetch)

        Returns:
            List of MTBSFire objects matching the fire name

        Note:
            Case-insensitive search using UPPER() function.
        """
        # Use UPPER for case-insensitive matching
        search_name = fire_name.upper().replace("'", "''")  # SQL escape
        where_clause = f"UPPER(fire_name) LIKE '%{search_name}%'"

        params = {
            "where": where_clause,
            "outFields": "fire_id,fire_name,acres,ig_date,fire_type",
            "f": "geojson",
            "outSR": "4326",
            "returnGeometry": "true",
            "resultRecordCount": 2000,
            "geometryPrecision": 6,
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()

        geojson_data = response.json()
        fires = self._parse_geojson_response(geojson_data)

        # Filter by year if specified
        if year:
            fires = [f for f in fires if f.fire_year == year]

        return fires

    def _parse_geojson_response(self, geojson_data: dict) -> list[MTBSFire]:
        """Parse GeoJSON response into MTBSFire objects.

        Args:
            geojson_data: GeoJSON FeatureCollection from ESRI API

        Returns:
            List of MTBSFire objects

        Note:
            Extracts year from fire_id (format: STATE+COORDS+YYYYMMDD).
            Example: "CA3630511215520200904" -> year=2020
        """
        fires: list[MTBSFire] = []

        if "features" not in geojson_data:
            return fires

        for feature in geojson_data["features"]:
            # ESRI REST API can return properties under either 'properties' or 'attributes'
            properties = feature.get("properties", {}) or feature.get("attributes", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # Convert GeoJSON geometry to WKT
            geom_shapely = shape(geometry)

            # Get fire_id and extract year from it
            fire_id = properties.get("fire_id", "")

            # Extract year from fire_id (last 8 digits are YYYYMMDD)
            # Example: "CA3630511215520200904" -> "20200904" -> year=2020
            try:
                if len(fire_id) >= 8:
                    date_str = fire_id[-8:]  # YYYYMMDD
                    fire_year = int(date_str[:4])
                else:
                    fire_year = 0
            except (ValueError, IndexError):
                fire_year = 0

            # Parse ignition date from ig_date (Unix timestamp in milliseconds)
            ignition_date = None
            ig_date_ms = properties.get("ig_date")
            if ig_date_ms:
                try:
                    ignition_date = datetime.fromtimestamp(ig_date_ms / 1000)
                    # If year extraction failed, try to get it from ignition date
                    if fire_year == 0:
                        fire_year = ignition_date.year
                except (ValueError, OSError):
                    pass

            fire = MTBSFire(
                fire_id=fire_id,
                fire_name=properties.get("fire_name", "Unknown"),
                fire_year=fire_year,
                ignition_date=ignition_date,
                acres=float(properties.get("acres", 0.0)),
                fire_type=properties.get("fire_type", "Unknown"),
                geometry_wkt=geom_shapely.wkt,
            )
            fires.append(fire)

        return fires

    def fires_to_geodataframe(self, fires: list[MTBSFire]) -> gpd.GeoDataFrame:
        """Convert list of fires to GeoDataFrame.

        Args:
            fires: List of MTBSFire objects

        Returns:
            GeoDataFrame with fire polygons and attributes
        """
        if not fires:
            return gpd.GeoDataFrame(
                columns=[
                    "fire_id",
                    "fire_name",
                    "fire_year",
                    "ignition_date",
                    "acres",
                    "fire_type",
                    "geometry",
                ],
                crs="EPSG:4326",
            )

        data = {
            "fire_id": [f.fire_id for f in fires],
            "fire_name": [f.fire_name for f in fires],
            "fire_year": [f.fire_year for f in fires],
            "ignition_date": [f.ignition_date for f in fires],
            "acres": [f.acres for f in fires],
            "fire_type": [f.fire_type for f in fires],
            "geometry": [f.to_shapely_polygon() for f in fires],
        }

        return gpd.GeoDataFrame(data, crs="EPSG:4326")

    def save_fires(
        self,
        fires: list[MTBSFire],
        output_path: Path,
        format: str = "gpkg",
    ) -> None:
        """Save fire perimeters to file.

        Args:
            fires: List of MTBSFire objects
            output_path: Output file path
            format: Output format ('gpkg', 'geojson', 'shapefile')

        Raises:
            ValueError: If format is unsupported
        """
        gdf = self.fires_to_geodataframe(fires)

        if format.lower() == "gpkg" or str(output_path).endswith(".gpkg"):
            gdf.to_file(output_path, driver="GPKG")
        elif format.lower() == "geojson" or str(output_path).endswith(".geojson"):
            gdf.to_file(output_path, driver="GeoJSON")
        elif format.lower() == "shapefile" or str(output_path).endswith(".shp"):
            gdf.to_file(output_path, driver="ESRI Shapefile")
        else:
            raise ValueError(f"Unsupported format: {format}")
