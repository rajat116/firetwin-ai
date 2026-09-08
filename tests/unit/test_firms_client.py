"""Unit tests for FIRMS API client."""

from datetime import date
from unittest.mock import Mock, patch

import geopandas as gpd
import pytest

from firetwin.data.clients.firms import FIRMSClient, FIRMSDetection, FIRMSSatellite


def _has_pyarrow() -> bool:
    """Check if pyarrow is available."""
    try:
        import pyarrow  # noqa: F401

        return True
    except ImportError:
        return False


# Sample FIRMS CSV response (VIIRS format)
SAMPLE_CSV_RESPONSE = """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight
38.5,-120.3,330.2,0.4,0.4,2024-08-15,1830,N,VIIRS,95,2.0NRT,290.5,25.3,D
38.6,-120.4,325.1,0.4,0.4,2024-08-15,1831,N,VIIRS,nominal,2.0NRT,288.2,18.7,D
"""


@pytest.fixture
def firms_client() -> FIRMSClient:
    """Create FIRMS client with test API key."""
    return FIRMSClient(map_key="test_key_12345")


def test_firms_client_init_with_key() -> None:
    """Test FIRMSClient initialization with explicit key."""
    client = FIRMSClient(map_key="my_test_key")
    assert client.map_key == "my_test_key"


def test_firms_client_init_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test FIRMSClient initialization without key raises error."""
    monkeypatch.setattr("firetwin.data.clients.firms.settings.firms_map_key", None)
    with pytest.raises(ValueError, match="FIRMS MAP_KEY is required"):
        FIRMSClient()
    with pytest.raises(ValueError, match="FIRMS MAP_KEY is required"):
        FIRMSClient(map_key="")


def test_firms_detection_model() -> None:
    """Test FIRMSDetection model validation."""
    detection = FIRMSDetection(
        latitude=38.5,
        longitude=-120.3,
        brightness=330.2,
        scan=0.4,
        track=0.4,
        acq_date=date(2024, 8, 15),
        acq_time="1830",
        satellite="N",
        instrument="VIIRS",
        confidence=95,
        version="2.0NRT",
        bright_t31=290.5,
        frp=25.3,
        daynight="D",
    )

    assert detection.latitude == 38.5
    assert detection.longitude == -120.3
    assert detection.confidence == 95


def test_firms_detection_acquisition_datetime() -> None:
    """Test acquisition datetime property."""
    detection = FIRMSDetection(
        latitude=38.5,
        longitude=-120.3,
        brightness=330.2,
        scan=0.4,
        track=0.4,
        acq_date=date(2024, 8, 15),
        acq_time="1830",
        satellite="N",
        instrument="VIIRS",
        confidence=95,
        version="2.0NRT",
        frp=25.3,
        daynight="D",
    )

    dt = detection.acquisition_datetime
    assert dt.year == 2024
    assert dt.month == 8
    assert dt.day == 15
    assert dt.hour == 18
    assert dt.minute == 30


def test_firms_detection_to_point() -> None:
    """Test conversion to Shapely Point."""
    detection = FIRMSDetection(
        latitude=38.5,
        longitude=-120.3,
        brightness=330.2,
        scan=0.4,
        track=0.4,
        acq_date=date(2024, 8, 15),
        acq_time="1830",
        satellite="N",
        instrument="VIIRS",
        confidence=95,
        version="2.0NRT",
        frp=25.3,
        daynight="D",
    )

    point = detection.to_point()
    assert point.x == -120.3
    assert point.y == 38.5


@patch("firetwin.data.clients.firms.requests.get")
def test_get_area_detections_success(mock_get: Mock, firms_client: FIRMSClient) -> None:
    """Test successful area detection query."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_CSV_RESPONSE
    mock_get.return_value = mock_response

    detections = firms_client.get_area_detections(
        satellite=FIRMSSatellite.VIIRS_SNPP,
        min_lon=-121.0,
        min_lat=38.0,
        max_lon=-120.0,
        max_lat=39.0,
        day_range=1,
    )

    assert len(detections) == 2
    assert detections[0].latitude == 38.5
    assert detections[0].longitude == -120.3
    assert detections[0].brightness == 330.2
    assert detections[1].confidence == "nominal"  # String confidence value


@patch("firetwin.data.clients.firms.requests.get")
def test_get_area_detections_with_date(mock_get: Mock, firms_client: FIRMSClient) -> None:
    """Test area detection query with specific date."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_CSV_RESPONSE
    mock_get.return_value = mock_response

    target_date = date(2024, 8, 15)
    detections = firms_client.get_area_detections(
        satellite=FIRMSSatellite.VIIRS_SNPP,
        min_lon=-121.0,
        min_lat=38.0,
        max_lon=-120.0,
        max_lat=39.0,
        day_range=1,
        date=target_date,
    )

    # Verify URL was constructed with date
    called_url = mock_get.call_args[0][0]
    assert "2024-08-15" in called_url
    assert len(detections) == 2


def test_get_area_detections_invalid_lon(firms_client: FIRMSClient) -> None:
    """Test area detection with invalid longitude raises error."""
    with pytest.raises(ValueError, match="Longitude must be between"):
        firms_client.get_area_detections(
            satellite=FIRMSSatellite.VIIRS_SNPP,
            min_lon=-200.0,  # Invalid
            min_lat=38.0,
            max_lon=-120.0,
            max_lat=39.0,
        )


def test_get_area_detections_invalid_lat(firms_client: FIRMSClient) -> None:
    """Test area detection with invalid latitude raises error."""
    with pytest.raises(ValueError, match="Latitude must be between"):
        firms_client.get_area_detections(
            satellite=FIRMSSatellite.VIIRS_SNPP,
            min_lon=-121.0,
            min_lat=-100.0,  # Invalid
            max_lon=-120.0,
            max_lat=39.0,
        )


def test_get_area_detections_invalid_day_range(firms_client: FIRMSClient) -> None:
    """Test area detection with invalid day range raises error."""
    with pytest.raises(ValueError, match="day_range must be between"):
        firms_client.get_area_detections(
            satellite=FIRMSSatellite.VIIRS_SNPP,
            min_lon=-121.0,
            min_lat=38.0,
            max_lon=-120.0,
            max_lat=39.0,
            day_range=15,  # Invalid (max is 10)
        )


@patch("firetwin.data.clients.firms.requests.get")
def test_get_country_detections_success(mock_get: Mock, firms_client: FIRMSClient) -> None:
    """Test successful country detection query."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_CSV_RESPONSE
    mock_get.return_value = mock_response

    detections = firms_client.get_country_detections(
        satellite=FIRMSSatellite.VIIRS_SNPP, country_code="US", day_range=1
    )

    # Verify URL construction
    called_url = mock_get.call_args[0][0]
    assert "/country/csv/" in called_url
    assert "/US/" in called_url
    assert len(detections) == 2


def test_get_country_detections_invalid_code(firms_client: FIRMSClient) -> None:
    """Test country detection with invalid country code raises error."""
    with pytest.raises(ValueError, match="country_code must be 2-letter"):
        firms_client.get_country_detections(
            satellite=FIRMSSatellite.VIIRS_SNPP,
            country_code="USA",
            day_range=1,  # Invalid (3 letters)
        )


@patch("firetwin.data.clients.firms.requests.get")
def test_parse_empty_csv(mock_get: Mock, firms_client: FIRMSClient) -> None:
    """Test parsing empty CSV response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "latitude,longitude,brightness\n"  # Header only
    mock_get.return_value = mock_response

    detections = firms_client.get_area_detections(
        satellite=FIRMSSatellite.VIIRS_SNPP,
        min_lon=-121.0,
        min_lat=38.0,
        max_lon=-120.0,
        max_lat=39.0,
    )

    assert len(detections) == 0


def test_detections_to_geodataframe(firms_client: FIRMSClient) -> None:
    """Test conversion of detections to GeoDataFrame."""
    detections = [
        FIRMSDetection(
            latitude=38.5,
            longitude=-120.3,
            brightness=330.2,
            scan=0.4,
            track=0.4,
            acq_date=date(2024, 8, 15),
            acq_time="1830",
            satellite="N",
            instrument="VIIRS",
            confidence=95,
            version="2.0NRT",
            frp=25.3,
            daynight="D",
        )
    ]

    gdf = firms_client.detections_to_geodataframe(detections)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 1
    assert gdf.crs == "EPSG:4326"
    assert "geometry" in gdf.columns
    assert "brightness" in gdf.columns
    assert "confidence" in gdf.columns
    assert gdf.iloc[0].geometry.x == -120.3
    assert gdf.iloc[0].geometry.y == 38.5


def test_detections_to_geodataframe_empty(firms_client: FIRMSClient) -> None:
    """Test conversion of empty detection list to GeoDataFrame."""
    gdf = firms_client.detections_to_geodataframe([])

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 0
    assert gdf.crs == "EPSG:4326"
    assert "geometry" in gdf.columns


@pytest.mark.skipif(
    not _has_pyarrow(),
    reason="pyarrow not installed",
)
def test_save_detections_parquet(firms_client: FIRMSClient, tmp_path) -> None:
    """Test saving detections to Parquet format."""
    detections = [
        FIRMSDetection(
            latitude=38.5,
            longitude=-120.3,
            brightness=330.2,
            scan=0.4,
            track=0.4,
            acq_date=date(2024, 8, 15),
            acq_time="1830",
            satellite="N",
            instrument="VIIRS",
            confidence=95,
            version="2.0NRT",
            frp=25.3,
            daynight="D",
        )
    ]

    output_path = tmp_path / "detections.parquet"
    firms_client.save_detections(detections, output_path, format="parquet")

    assert output_path.exists()

    # Read back and verify
    gdf = gpd.read_parquet(output_path)
    assert len(gdf) == 1
    assert gdf.iloc[0]["brightness"] == 330.2


def test_save_detections_invalid_format(firms_client: FIRMSClient, tmp_path) -> None:
    """Test saving detections with invalid format raises error."""
    detections = [
        FIRMSDetection(
            latitude=38.5,
            longitude=-120.3,
            brightness=330.2,
            scan=0.4,
            track=0.4,
            acq_date=date(2024, 8, 15),
            acq_time="1830",
            satellite="N",
            instrument="VIIRS",
            confidence=95,
            version="2.0NRT",
            frp=25.3,
            daynight="D",
        )
    ]

    output_path = tmp_path / "detections.xyz"
    with pytest.raises(ValueError, match="Unsupported format"):
        firms_client.save_detections(detections, output_path, format="invalid")
