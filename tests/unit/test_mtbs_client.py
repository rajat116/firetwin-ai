"""Unit tests for MTBS API client."""

from datetime import datetime
from unittest.mock import Mock, patch

import geopandas as gpd
import pytest

from firetwin.data.clients.mtbs import MTBSClient, MTBSFire

# Sample GeoJSON response (MTBS format)
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
                "FIRE_ID": "CA4179612416320200815",
                "FIRE_NAME": "Creek Fire",
                "FIRE_YEAR": 2020,
                "START_DATE": 1597449600000,  # Unix timestamp in ms
                "END_DATE": 1597536000000,
                "ACRES": 379895.0,
                "STATE": "CA",
                "AGENCY": "USFS",
                "FIRE_TYPE": "Wildfire",
            },
        }
    ],
}


@pytest.fixture
def mtbs_client() -> MTBSClient:
    """Create MTBS client fixture."""
    return MTBSClient(timeout=10)


def test_mtbs_client_init() -> None:
    """Test MTBS client initialization."""
    client = MTBSClient(timeout=30)
    assert client.timeout == 30


def test_mtbs_fire_model() -> None:
    """Test MTBSFire model validation."""
    fire = MTBSFire(
        fire_id="TEST123",
        fire_name="Test Fire",
        fire_year=2020,
        start_date=datetime(2020, 8, 15),
        end_date=datetime(2020, 8, 16),
        acres=10000.0,
        state="CA",
        agency="USFS",
        fire_type="Wildfire",
        geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
    )

    assert fire.fire_name == "Test Fire"
    assert fire.fire_year == 2020
    assert fire.acres == 10000.0


def test_mtbs_fire_to_shapely_polygon() -> None:
    """Test converting MTBSFire to Shapely polygon."""
    fire = MTBSFire(
        fire_id="TEST123",
        fire_name="Test Fire",
        fire_year=2020,
        start_date=datetime(2020, 8, 15),
        end_date=datetime(2020, 8, 16),
        acres=10000.0,
        state="CA",
        agency="USFS",
        fire_type="Wildfire",
        geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
    )

    polygon = fire.to_shapely_polygon()
    assert polygon.geom_type == "Polygon"
    assert polygon.is_valid


@patch("firetwin.data.clients.mtbs.requests.get")
def test_get_fires_by_year_success(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test successful fire query by year."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    fires = mtbs_client.get_fires_by_year(year=2020)

    assert len(fires) == 1
    assert fires[0].fire_name == "Creek Fire"
    assert fires[0].fire_year == 2020
    assert fires[0].acres == 379895.0


@patch("firetwin.data.clients.mtbs.requests.get")
def test_get_fires_by_year_with_filters(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test fire query with filters."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    _fires = mtbs_client.get_fires_by_year(
        year=2020,
        min_acres=1000.0,
        state="CA",
        bbox=(-121.0, 38.0, -120.0, 39.5),
    )

    # Verify request was made with correct parameters
    call_args = mock_get.call_args
    assert "where" in call_args[1]["params"]
    assert "FIRE_YEAR=2020" in call_args[1]["params"]["where"]
    assert "STATE='CA'" in call_args[1]["params"]["where"]


@patch("firetwin.data.clients.mtbs.requests.get")
def test_get_fires_invalid_year(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test that year < 1984 raises error."""
    with pytest.raises(ValueError, match="MTBS data starts from 1984"):
        mtbs_client.get_fires_by_year(year=1980)


@patch("firetwin.data.clients.mtbs.requests.get")
def test_get_fires_max_records_exceeded(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test that max_records > 2000 raises error."""
    with pytest.raises(ValueError, match="cannot exceed 2000"):
        mtbs_client.get_fires_by_year(year=2020, max_records=3000)


@patch("firetwin.data.clients.mtbs.requests.get")
def test_get_fire_by_name_success(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test getting fire by name."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_GEOJSON_RESPONSE
    mock_get.return_value = mock_response

    _fires = mtbs_client.get_fire_by_name("Creek", year=2020)

    # Verify LIKE query was constructed
    call_args = mock_get.call_args
    assert "LIKE" in call_args[1]["params"]["where"]
    assert "Creek" in call_args[1]["params"]["where"]
    assert "FIRE_YEAR=2020" in call_args[1]["params"]["where"]


@patch("firetwin.data.clients.mtbs.requests.get")
def test_parse_empty_geojson(mock_get: Mock, mtbs_client: MTBSClient) -> None:
    """Test parsing empty GeoJSON response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"type": "FeatureCollection", "features": []}
    mock_get.return_value = mock_response

    fires = mtbs_client.get_fires_by_year(year=2020)

    assert len(fires) == 0


def test_fires_to_geodataframe(mtbs_client: MTBSClient) -> None:
    """Test converting fires to GeoDataFrame."""
    fires = [
        MTBSFire(
            fire_id="TEST123",
            fire_name="Test Fire",
            fire_year=2020,
            start_date=datetime(2020, 8, 15),
            end_date=datetime(2020, 8, 16),
            acres=10000.0,
            state="CA",
            agency="USFS",
            fire_type="Wildfire",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    gdf = mtbs_client.fires_to_geodataframe(fires)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 1
    assert gdf.crs == "EPSG:4326"
    assert gdf.iloc[0]["fire_name"] == "Test Fire"
    assert gdf.iloc[0]["acres"] == 10000.0


def test_fires_to_geodataframe_empty(mtbs_client: MTBSClient) -> None:
    """Test converting empty list to GeoDataFrame."""
    gdf = mtbs_client.fires_to_geodataframe([])

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 0
    assert gdf.crs == "EPSG:4326"
    assert "geometry" in gdf.columns


def test_save_fires_gpkg(mtbs_client: MTBSClient, tmp_path) -> None:
    """Test saving fires to GeoPackage format."""
    fires = [
        MTBSFire(
            fire_id="TEST123",
            fire_name="Test Fire",
            fire_year=2020,
            start_date=datetime(2020, 8, 15),
            end_date=datetime(2020, 8, 16),
            acres=10000.0,
            state="CA",
            agency="USFS",
            fire_type="Wildfire",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    output_path = tmp_path / "fires.gpkg"
    mtbs_client.save_fires(fires, output_path, format="gpkg")

    assert output_path.exists()

    # Read back and verify
    gdf = gpd.read_file(output_path)
    assert len(gdf) == 1
    assert gdf.iloc[0]["fire_name"] == "Test Fire"


def test_save_fires_invalid_format(mtbs_client: MTBSClient, tmp_path) -> None:
    """Test saving fires with invalid format raises error."""
    fires = [
        MTBSFire(
            fire_id="TEST123",
            fire_name="Test Fire",
            fire_year=2020,
            start_date=datetime(2020, 8, 15),
            end_date=datetime(2020, 8, 16),
            acres=10000.0,
            state="CA",
            agency="USFS",
            fire_type="Wildfire",
            geometry_wkt="POLYGON ((-120 38, -119 38, -119 39, -120 39, -120 38))",
        )
    ]

    output_path = tmp_path / "fires.xyz"
    with pytest.raises(ValueError, match="Unsupported format"):
        mtbs_client.save_fires(fires, output_path, format="invalid")
