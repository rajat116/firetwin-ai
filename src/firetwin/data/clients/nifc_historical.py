"""NIFC Historical Fire Perimeters API client.

Official service:
- Service: InterAgencyFirePerimeterHistory_All_Years_View
- URL: https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/
       InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0

This service provides historical wildfire perimeter data from multiple agencies:
- USDA Forest Service
- Department of Interior (BLM, NPS, FWS, BIA)
- State agencies (CALFIRE, etc.)
- Alaska Interagency Fire Center

Data availability: Historical fires from 2000-2021+ (varies by agency and year)
Update frequency: Fires added after containment and final perimeter mapping
"""

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import requests
from pydantic import BaseModel, Field
from shapely.geometry import shape


class NIFCHistoricalPerimeter(BaseModel):
    """Single NIFC historical fire perimeter."""

    incident_name: str = Field(..., description="Fire incident name")
    fire_year: int = Field(..., description="Fire year")
    gis_acres: float = Field(..., description="GIS-calculated perimeter acres")
    date_current: str | None = Field(None, description="Perimeter date (YYYYMMDDHHMMSS)")
    unique_fire_id: str | None = Field(None, description="Unique fire identifier")
    irwin_id: str | None = Field(None, description="IRWIN incident ID")
    agency: str | None = Field(None, description="Managing agency")
    source: str | None = Field(None, description="Data source")
    map_method: str | None = Field(None, description="Mapping method")
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

    def get_date(self) -> datetime | None:
        """Parse DATE_CUR field to datetime.

        Returns:
            Datetime object or None if parsing fails
        """
        if not self.date_current or len(self.date_current) < 8:
            return None

        try:
            # Format: YYYYMMDDHHMMSS or YYYYMMDD
            if len(self.date_current) >= 14:
                return datetime.strptime(self.date_current[:14], "%Y%m%d%H%M%S")
            else:
                return datetime.strptime(self.date_current[:8], "%Y%m%d")
        except ValueError:
            return None


class NIFCHistoricalClient:
    """Client for NIFC historical fire perimeter API."""

    BASE_URL = (
        "https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/"
        "InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0/query"
    )

    DEFAULT_HEADERS = {
        "User-Agent": "FireTwin/1.0 (Research Project; https://github.com/rajat116/firetwin-ai)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.arcgis.com/",
    }

    def __init__(self, timeout: int = 30) -> None:
        """Initialize NIFC historical client.

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
    ) -> list[NIFCHistoricalPerimeter]:
        """Get historical fire perimeters for a specific year.

        Args:
            year: Fire year (2000-present, varies by agency)
            min_acres: Minimum fire size in acres
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            max_records: Maximum number of records to return (max 2000)

        Returns:
            List of NIFCHistoricalPerimeter objects

        Raises:
            ValueError: If max_records > 2000
            requests.HTTPError: If API request fails
        """
        if max_records > 2000:
            raise ValueError("max_records cannot exceed 2000 (ESRI API limit)")

        # Build WHERE clause
        where_clauses = [f"FIRE_YEAR_INT={year}"]
        if min_acres is not None:
            where_clauses.append(f"GIS_ACRES>={min_acres}")

        params = {
            "where": " AND ".join(where_clauses),
            "outFields": (
                "INCIDENT,GIS_ACRES,FIRE_YEAR_INT,DATE_CUR,UNQE_FIRE_ID,"
                "IRWINID,AGENCY,SOURCE,MAP_METHOD"
            ),
            "f": "geojson",
            "outSR": "4326",
            "returnGeometry": "true",
            "resultRecordCount": max_records,
            "geometryPrecision": 6,
        }

        # Add bbox geometry filter if provided
        if bbox:
            minx, miny, maxx, maxy = bbox
            params["geometry"] = f"{minx},{miny},{maxx},{maxy}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"

        response = requests.get(
            self.BASE_URL,
            params=params,
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()

        geojson_data = response.json()
        return self._parse_geojson_response(geojson_data)

    def get_fire_by_name(
        self, fire_name: str, year: int | None = None
    ) -> list[NIFCHistoricalPerimeter]:
        """Get historical fires by name.

        Args:
            fire_name: Incident name (partial match supported)
            year: Optional year filter

        Returns:
            List of NIFCHistoricalPerimeter objects matching the fire name
        """
        # Use UPPER for case-insensitive matching
        search_name = fire_name.upper().replace("'", "''")  # SQL escape
        where_parts = [f"UPPER(INCIDENT) LIKE '%{search_name}%'"]

        if year:
            where_parts.append(f"FIRE_YEAR_INT={year}")

        params = {
            "where": " AND ".join(where_parts),
            "outFields": (
                "INCIDENT,GIS_ACRES,FIRE_YEAR_INT,DATE_CUR,UNQE_FIRE_ID,"
                "IRWINID,AGENCY,SOURCE,MAP_METHOD"
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

    def _parse_geojson_response(self, geojson_data: dict) -> list[NIFCHistoricalPerimeter]:
        """Parse GeoJSON response into NIFCHistoricalPerimeter objects.

        Args:
            geojson_data: GeoJSON FeatureCollection from ESRI API

        Returns:
            List of NIFCHistoricalPerimeter objects
        """
        perimeters: list[NIFCHistoricalPerimeter] = []

        if "features" not in geojson_data:
            return perimeters

        for feature in geojson_data["features"]:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # Convert GeoJSON geometry to WKT
            geom_shapely = shape(geometry)

            perimeter = NIFCHistoricalPerimeter(
                incident_name=properties.get("INCIDENT", "Unknown"),
                fire_year=int(properties.get("FIRE_YEAR_INT", 0)),
                gis_acres=float(properties.get("GIS_ACRES", 0.0)),
                date_current=properties.get("DATE_CUR"),
                unique_fire_id=properties.get("UNQE_FIRE_ID"),
                irwin_id=properties.get("IRWINID"),
                agency=properties.get("AGENCY"),
                source=properties.get("SOURCE"),
                map_method=properties.get("MAP_METHOD"),
                geometry_wkt=geom_shapely.wkt,
            )
            perimeters.append(perimeter)

        return perimeters

    def perimeters_to_geodataframe(
        self, perimeters: list[NIFCHistoricalPerimeter]
    ) -> gpd.GeoDataFrame:
        """Convert list of perimeters to GeoDataFrame.

        Args:
            perimeters: List of NIFCHistoricalPerimeter objects

        Returns:
            GeoDataFrame with fire polygons and attributes
        """
        if not perimeters:
            return gpd.GeoDataFrame(
                columns=[
                    "incident_name",
                    "fire_year",
                    "gis_acres",
                    "date_current",
                    "unique_fire_id",
                    "irwin_id",
                    "agency",
                    "source",
                    "geometry",
                ],
                crs="EPSG:4326",
            )

        data = {
            "incident_name": [p.incident_name for p in perimeters],
            "fire_year": [p.fire_year for p in perimeters],
            "gis_acres": [p.gis_acres for p in perimeters],
            "date_current": [p.date_current for p in perimeters],
            "unique_fire_id": [p.unique_fire_id for p in perimeters],
            "irwin_id": [p.irwin_id for p in perimeters],
            "agency": [p.agency for p in perimeters],
            "source": [p.source for p in perimeters],
            "geometry": [p.to_shapely_polygon() for p in perimeters],
        }

        return gpd.GeoDataFrame(data, crs="EPSG:4326")

    def save_perimeters(
        self,
        perimeters: list[NIFCHistoricalPerimeter],
        output_path: Path,
        format: str = "gpkg",
    ) -> None:
        """Save fire perimeters to file.

        Args:
            perimeters: List of NIFCHistoricalPerimeter objects
            output_path: Output file path
            format: Output format ('gpkg', 'geojson', 'shp')

        Raises:
            ValueError: If format is not supported
        """
        gdf = self.perimeters_to_geodataframe(perimeters)

        if format == "gpkg":
            gdf.to_file(output_path, driver="GPKG")
        elif format == "geojson":
            gdf.to_file(output_path, driver="GeoJSON")
        elif format == "shp":
            gdf.to_file(output_path, driver="ESRI Shapefile")
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'gpkg', 'geojson', or 'shp'.")
