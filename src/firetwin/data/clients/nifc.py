"""NIFC WFIGS (Wildland Fire Information and Geospatial Services) API client.

Official documentation:
- Portal: https://data-nifc.opendata.arcgis.com
- REST Services: https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services
- Current Perimeters: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0

WFIGS provides authoritative wildfire perimeter data from multiple federal agencies including:
- USDA Forest Service
- Department of Interior (BLM, NPS, FWS, BIA)
- State agencies coordinating through NIFC

The perimeter data includes active fires, prescribed fires, and final perimeters.
Data is updated approximately every 5 minutes during active fire seasons.
"""

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import requests
from pydantic import BaseModel, Field
from shapely.geometry import shape


class NIFCPerimeter(BaseModel):
    """Single NIFC fire perimeter polygon."""

    incident_name: str = Field(..., description="Fire incident name")
    incident_type: str = Field(..., description="Incident type (WF, RX, etc.)")
    gis_acres: float = Field(..., description="GIS-calculated perimeter acres")
    percent_contained: float | None = Field(None, description="Percent containment (0-100)")
    fire_discovery_datetime: datetime = Field(..., description="Fire discovery date/time")
    map_id: str = Field(..., description="Unique perimeter ID")
    irwin_id: str | None = Field(None, description="IRWIN incident ID")
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


class NIFCClient:
    """Client for NIFC WFIGS fire perimeter API."""

    BASE_URL = (
        "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
        "WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
    )

    # User agent to avoid ESRI blocking automated requests
    DEFAULT_HEADERS = {
        "User-Agent": "FireTwin/1.0 (Research Project; https://github.com/rajat116/firetwin-ai)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.arcgis.com/",
    }

    def __init__(self, timeout: int = 30) -> None:
        """Initialize NIFC client.

        Args:
            timeout: HTTP request timeout in seconds (default: 30)
        """
        self.timeout = timeout

    def get_current_perimeters(
        self,
        incident_type: str | None = None,
        min_acres: float | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        max_records: int = 2000,
    ) -> list[NIFCPerimeter]:
        """Get current fire perimeters from WFIGS.

        Args:
            incident_type: Filter by incident type ('WF' for wildfire, 'RX' for prescribed)
            min_acres: Minimum fire size in acres
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            max_records: Maximum number of records to return (max 2000)

        Returns:
            List of NIFCPerimeter objects

        Raises:
            ValueError: If max_records > 2000
            requests.HTTPError: If API request fails
        """
        if max_records > 2000:
            raise ValueError("max_records cannot exceed 2000 (ESRI API limit)")

        # Build where clause
        where_conditions = []
        if incident_type:
            where_conditions.append(f"attr_IncidentTypeCategory='{incident_type}'")
        if min_acres:
            where_conditions.append(f"poly_GISAcres>={min_acres}")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Build query parameters
        params = {
            "where": where_clause,
            "outFields": (
                "poly_IncidentName,attr_IncidentTypeCategory,poly_GISAcres,"
                "attr_PercentContained,attr_FireDiscoveryDateTime,poly_MapID,"
                "attr_IrwinID"
            ),
            "f": "geojson",
            "outSR": "4326",  # WGS84
            "returnGeometry": "true",
            "resultRecordCount": max_records,
            "geometryPrecision": 6,  # 6 decimal places (~0.1m precision)
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

    def get_fire_by_name(self, fire_name: str) -> list[NIFCPerimeter]:
        """Get perimeters for a specific fire by name.

        Args:
            fire_name: Incident name (partial match supported)

        Returns:
            List of NIFCPerimeter objects matching the fire name
        """
        params = {
            "where": f"poly_IncidentName LIKE '%{fire_name}%'",
            "outFields": (
                "poly_IncidentName,attr_IncidentTypeCategory,poly_GISAcres,"
                "attr_PercentContained,attr_FireDiscoveryDateTime,poly_MapID,"
                "attr_IrwinID"
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

    def _parse_geojson_response(self, geojson_data: dict) -> list[NIFCPerimeter]:
        """Parse GeoJSON response into NIFCPerimeter objects.

        Args:
            geojson_data: GeoJSON FeatureCollection from ESRI API

        Returns:
            List of NIFCPerimeter objects
        """
        perimeters = []

        if "features" not in geojson_data:
            return perimeters

        for feature in geojson_data["features"]:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")

            if not geometry:
                continue

            # Convert GeoJSON geometry to WKT
            geom_shapely = shape(geometry)

            # Parse datetime (format: "2024-08-15T18:30:00Z")
            fire_datetime_str = properties.get("attr_FireDiscoveryDateTime")
            fire_datetime = datetime.fromisoformat(fire_datetime_str.replace("Z", "+00:00"))

            perimeter = NIFCPerimeter(
                incident_name=properties.get("poly_IncidentName", "Unknown"),
                incident_type=properties.get("attr_IncidentTypeCategory", "Unknown"),
                gis_acres=float(properties.get("poly_GISAcres", 0.0)),
                percent_contained=float(properties["attr_PercentContained"])
                if properties.get("attr_PercentContained") is not None
                else None,
                fire_discovery_datetime=fire_datetime,
                map_id=properties.get("poly_MapID", ""),
                irwin_id=properties.get("attr_IrwinID"),
                geometry_wkt=geom_shapely.wkt,
            )
            perimeters.append(perimeter)

        return perimeters

    def perimeters_to_geodataframe(self, perimeters: list[NIFCPerimeter]) -> gpd.GeoDataFrame:
        """Convert list of perimeters to GeoDataFrame.

        Args:
            perimeters: List of NIFCPerimeter objects

        Returns:
            GeoDataFrame with perimeter polygons and attributes
        """
        if not perimeters:
            return gpd.GeoDataFrame(
                columns=[
                    "incident_name",
                    "incident_type",
                    "gis_acres",
                    "percent_contained",
                    "fire_discovery_datetime",
                    "map_id",
                    "irwin_id",
                    "geometry",
                ],
                crs="EPSG:4326",
            )

        data = {
            "incident_name": [p.incident_name for p in perimeters],
            "incident_type": [p.incident_type for p in perimeters],
            "gis_acres": [p.gis_acres for p in perimeters],
            "percent_contained": [p.percent_contained for p in perimeters],
            "fire_discovery_datetime": [p.fire_discovery_datetime for p in perimeters],
            "map_id": [p.map_id for p in perimeters],
            "irwin_id": [p.irwin_id for p in perimeters],
            "geometry": [p.to_shapely_polygon() for p in perimeters],
        }

        return gpd.GeoDataFrame(data, crs="EPSG:4326")

    def save_perimeters(
        self,
        perimeters: list[NIFCPerimeter],
        output_path: Path,
        format: str = "gpkg",
    ) -> None:
        """Save fire perimeters to file.

        Args:
            perimeters: List of NIFCPerimeter objects
            output_path: Output file path
            format: Output format ('gpkg', 'geojson', 'shapefile')

        Raises:
            ValueError: If format is unsupported
        """
        gdf = self.perimeters_to_geodataframe(perimeters)

        if format.lower() == "gpkg" or str(output_path).endswith(".gpkg"):
            gdf.to_file(output_path, driver="GPKG")
        elif format.lower() == "geojson" or str(output_path).endswith(".geojson"):
            gdf.to_file(output_path, driver="GeoJSON")
        elif format.lower() == "shapefile" or str(output_path).endswith(".shp"):
            gdf.to_file(output_path, driver="ESRI Shapefile")
        else:
            raise ValueError(f"Unsupported format: {format}")
