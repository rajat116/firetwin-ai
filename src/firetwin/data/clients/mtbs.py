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
    fire_year: int = Field(..., description="Fire year")
    start_date: datetime | None = Field(None, description="Fire start date")
    end_date: datetime | None = Field(None, description="Fire end date")
    acres: float = Field(..., description="Fire size in acres")
    state: str = Field(..., description="State code")
    agency: str | None = Field(None, description="Managing agency")
    fire_type: str | None = Field(None, description="Fire type (Wildfire, Prescribed)")
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
        state: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        max_records: int = 2000,
    ) -> list[MTBSFire]:
        """Get MTBS fire perimeters for a specific year.

        Args:
            year: Fire year (1984-present)
            min_acres: Minimum fire size in acres
            state: State code filter (e.g., 'CA', 'OR')
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            max_records: Maximum number of records to return (max 2000)

        Returns:
            List of MTBSFire objects

        Raises:
            ValueError: If max_records > 2000 or year < 1984
        """
        if max_records > 2000:
            raise ValueError("max_records cannot exceed 2000 (ESRI API limit)")
        if year < 1984:
            raise ValueError("MTBS data starts from 1984")

        # Build where clause
        where_conditions = [f"FIRE_YEAR={year}"]
        if min_acres:
            where_conditions.append(f"ACRES>={min_acres}")
        if state:
            where_conditions.append(f"STATE='{state.upper()}'")

        where_clause = " AND ".join(where_conditions)

        # Build query parameters
        params = {
            "where": where_clause,
            "outFields": (
                "FIRE_ID,FIRE_NAME,FIRE_YEAR,START_DATE,END_DATE,ACRES,STATE,AGENCY,FIRE_TYPE"
            ),
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

        return self._parse_geojson_response(geojson_data)

    def get_fire_by_name(self, fire_name: str, year: int | None = None) -> list[MTBSFire]:
        """Get MTBS fires by name (partial match supported).

        Args:
            fire_name: Fire name (partial match)
            year: Optional year filter

        Returns:
            List of MTBSFire objects matching the fire name
        """
        where_parts = [f"FIRE_NAME LIKE '%{fire_name}%'"]
        if year:
            where_parts.append(f"FIRE_YEAR={year}")

        where_clause = " AND ".join(where_parts)

        params = {
            "where": where_clause,
            "outFields": (
                "FIRE_ID,FIRE_NAME,FIRE_YEAR,START_DATE,END_DATE,ACRES,STATE,AGENCY,FIRE_TYPE"
            ),
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
        return self._parse_geojson_response(geojson_data)

    def _parse_geojson_response(self, geojson_data: dict) -> list[MTBSFire]:
        """Parse GeoJSON response into MTBSFire objects.

        Args:
            geojson_data: GeoJSON FeatureCollection from ESRI API

        Returns:
            List of MTBSFire objects
        """
        fires: list[MTBSFire] = []

        if "features" not in geojson_data:
            return fires

        for feature in geojson_data["features"]:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # Convert GeoJSON geometry to WKT
            geom_shapely = shape(geometry)

            # Parse dates (Unix timestamps in milliseconds)
            start_date = None
            if properties.get("START_DATE"):
                start_date = datetime.fromtimestamp(properties["START_DATE"] / 1000)

            end_date = None
            if properties.get("END_DATE"):
                end_date = datetime.fromtimestamp(properties["END_DATE"] / 1000)

            fire = MTBSFire(
                fire_id=properties.get("FIRE_ID", ""),
                fire_name=properties.get("FIRE_NAME", "Unknown"),
                fire_year=int(properties.get("FIRE_YEAR", 0)),
                start_date=start_date,
                end_date=end_date,
                acres=float(properties.get("ACRES", 0.0)),
                state=properties.get("STATE", ""),
                agency=properties.get("AGENCY"),
                fire_type=properties.get("FIRE_TYPE"),
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
                    "start_date",
                    "end_date",
                    "acres",
                    "state",
                    "agency",
                    "fire_type",
                    "geometry",
                ],
                crs="EPSG:4326",
            )

        data = {
            "fire_id": [f.fire_id for f in fires],
            "fire_name": [f.fire_name for f in fires],
            "fire_year": [f.fire_year for f in fires],
            "start_date": [f.start_date for f in fires],
            "end_date": [f.end_date for f in fires],
            "acres": [f.acres for f in fires],
            "state": [f.state for f in fires],
            "agency": [f.agency for f in fires],
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
