"""Unit tests for NIFC WFIGS API client."""

from datetime import datetime
from unittest.mock import Mock, patch

import geopandas as gpd
import pytest

from firetwin.data.clients.nifc import NIFCClient, NIFCPerimeter

# Sample GeoJSON response (WFIGS format)
SAMPLE_GEOJSON_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-120.5, 38.5],
                        [-120.4, 38.5],
                        [-120.4, 38.6],
                        [-120.5, 38.6],
                        [-120.5, 38.5],
                    ]
                ],
            },
            "properties": {
                "poly_IncidentName": "Creek Fire",
                "attr_IncidentTypeCategory": "WF",
                "poly_GISAcres": 1250.5,
                "attr_PercentContained": 25.0,
                "attr_FireDiscoveryDateTime": "2024-08-15T14:30:00Z",
                "poly_MapID": "CF-2024-001",
                "attr_IrwinID": "ABC123",
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-121.0, 39.0],
                        [-120.9, 39.0],
                        [-120.9, 39.1],
                        [-121.0, 39.1],
                        [-121.0, 39.0],
                    ]
                ],
            },
            "properties": {
                "poly_IncidentName": "Basin Fire",
                "attr_IncidentTypeCategory": "RX",
                "poly_GISAcres": 500.0,
                "attr_PercentContained": None,
                "attr_FireDiscoveryDateTime": "2024-08-10T10:00:00Z",
                "poly_MapID": "BF-2024-002",
                "attr_IrwinID": None,
            },
        },
    ],
}


@pytest.fixture
def nifc_client() -> NIFCClient:
    """Create NIFC client fixture."""
    return NIFCClient(timeout=10)


def test_nifc_client_init() -> None:
    """Test NIFC client initialization."""
    client = NIFCClient(timeout=30)
    assert client.timeout == 30


def test_nifc_perimeter_model() -> None:
    """Test NIFCPerimeter model validation."""
    perimeter = NIFCPerimeter(
        incident_name="Test Fire",
        incident_type="WF",
        gis_acres=1000.0,
        percent_contained=50.0,
        fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
        map_id="TF-2024-001",
        irwin_id="TEST123",
        geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
    )

    assert perimeter.incident_name == "Test Fire"
    assert perimeter.incident_type == "WF"
    assert perimeter.gis_acres == 1000.0
    assert perimeter.percent_contained == 50.0


def test_nifc_perimeter_to_shapely_polygon() -> None:
    """Test converting NIFCPerimeter to Shapely polygon."""
    perimeter = NIFCPerimeter(
        incident_name="Test Fire",
        incident_type="WF",
        gis_acres=1000.0,
        percent_contained=50.0,
        fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
        map_id="TF-2024-001",
        irwin_id="TEST123",
        geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
    )

    polygon = perimeter.to_shapely_polygon()
    assert polygon.geom_type == "Polygon"
    assert polygon.is_valid


@patch("firetwin.data.clients.nifc.requests.get")
def test_get_current_perimeters_success(mock_get: Mock, nifc_client: NIFCClient) -> None:
    """Test successful perimeter query."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    perimeters = nifc_client.get_current_perimeters()

    assert len(perimeters) == 2
    assert perimeters[0].incident_name == "Creek Fire"
    assert perimeters[0].incident_type == "WF"
    assert perimeters[0].gis_acres == 1250.5
    assert perimeters[1].incident_name == "Basin Fire"
    assert perimeters[1].percent_contained is None


@patch("firetwin.data.clients.nifc.requests.get")
def test_get_current_perimeters_with_filters(mock_get: Mock, nifc_client: NIFCClient) -> None:
    """Test perimeter query with filters."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    _perimeters = nifc_client.get_current_perimeters(
        incident_type="WF",
        min_acres=1000.0,
        bbox=(-121.0, 38.0, -120.0, 39.5),
    )

    # Verify request was made with correct parameters
    call_args = mock_get.call_args
    assert "where" in call_args[1]["params"]
    assert "geometry" in call_args[1]["params"]
    assert call_args[1]["params"]["geometryType"] == "esriGeometryEnvelope"


@patch("firetwin.data.clients.nifc.requests.get")
def test_get_current_perimeters_max_records_exceeded(
    mock_get: Mock, nifc_client: NIFCClient
) -> None:
    """Test that max_records > 2000 raises error."""
    with pytest.raises(ValueError, match="cannot exceed 2000"):
        nifc_client.get_current_perimeters(max_records=3000)


@patch("firetwin.data.clients.nifc.requests.get")
def test_get_fire_by_name_success(mock_get: Mock, nifc_client: NIFCClient) -> None:
    """Test getting fire by name."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    _perimeters = nifc_client.get_fire_by_name("Creek")

    # Verify LIKE query was constructed
    call_args = mock_get.call_args
    assert "LIKE" in call_args[1]["params"]["where"]
    assert "Creek" in call_args[1]["params"]["where"]


@patch("firetwin.data.clients.nifc.requests.get")
def test_parse_empty_geojson(mock_get: Mock, nifc_client: NIFCClient) -> None:
    """Test parsing empty GeoJSON response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"type": "FeatureCollection", "features": []}
    mock_get.return_value = mock_response

    perimeters = nifc_client.get_current_perimeters()

    assert len(perimeters) == 0


def test_perimeters_to_geodataframe(nifc_client: NIFCClient) -> None:
    """Test converting perimeters to GeoDataFrame."""
    perimeters = [
        NIFCPerimeter(
            incident_name="Test Fire",
            incident_type="WF",
            gis_acres=1000.0,
            percent_contained=50.0,
            fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
            map_id="TF-2024-001",
            irwin_id="TEST123",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    gdf = nifc_client.perimeters_to_geodataframe(perimeters)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 1
    assert gdf.crs == "EPSG:4326"
    assert gdf.iloc[0]["incident_name"] == "Test Fire"
    assert gdf.iloc[0]["gis_acres"] == 1000.0


def test_perimeters_to_geodataframe_empty(nifc_client: NIFCClient) -> None:
    """Test converting empty list to GeoDataFrame."""
    gdf = nifc_client.perimeters_to_geodataframe([])

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 0
    assert gdf.crs == "EPSG:4326"
    assert "geometry" in gdf.columns


def test_save_perimeters_gpkg(nifc_client: NIFCClient, tmp_path) -> None:
    """Test saving perimeters to GeoPackage format."""
    perimeters = [
        NIFCPerimeter(
            incident_name="Test Fire",
            incident_type="WF",
            gis_acres=1000.0,
            percent_contained=50.0,
            fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
            map_id="TF-2024-001",
            irwin_id="TEST123",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    output_path = tmp_path / "perimeters.gpkg"
    nifc_client.save_perimeters(perimeters, output_path, format="gpkg")

    assert output_path.exists()

    # Read back and verify
    gdf = gpd.read_file(output_path)
    assert len(gdf) == 1
    assert gdf.iloc[0]["incident_name"] == "Test Fire"


def test_save_perimeters_geojson(nifc_client: NIFCClient, tmp_path) -> None:
    """Test saving perimeters to GeoJSON format."""
    perimeters = [
        NIFCPerimeter(
            incident_name="Test Fire",
            incident_type="WF",
            gis_acres=1000.0,
            percent_contained=50.0,
            fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
            map_id="TF-2024-001",
            irwin_id="TEST123",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    output_path = tmp_path / "perimeters.geojson"
    nifc_client.save_perimeters(perimeters, output_path, format="geojson")

    assert output_path.exists()

    # Read back and verify
    gdf = gpd.read_file(output_path)
    assert len(gdf) == 1


def test_save_perimeters_invalid_format(nifc_client: NIFCClient, tmp_path) -> None:
    """Test saving perimeters with invalid format raises error."""
    perimeters = [
        NIFCPerimeter(
            incident_name="Test Fire",
            incident_type="WF",
            gis_acres=1000.0,
            percent_contained=50.0,
            fire_discovery_datetime=datetime(2024, 8, 15, 14, 30),
            map_id="TF-2024-001",
            irwin_id="TEST123",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    output_path = tmp_path / "perimeters.xyz"
    with pytest.raises(ValueError, match="Unsupported format"):
        nifc_client.save_perimeters(perimeters, output_path, format="invalid")
