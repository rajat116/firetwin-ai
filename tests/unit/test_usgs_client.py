"""Unit tests for USGS 3DEP client."""

from unittest.mock import Mock, patch

import pytest

from firetwin.data.clients.usgs import USGS3DEPClient


@pytest.fixture
def usgs_client() -> USGS3DEPClient:
    """Create USGS client fixture."""
    return USGS3DEPClient()


def test_usgs_client_init() -> None:
    """Test USGS client initialization."""
    client = USGS3DEPClient(timeout=60)
    assert client.timeout == 60


@patch("firetwin.data.clients.usgs.requests.get")
def test_search_datasets_success(mock_get: Mock, usgs_client: USGS3DEPClient) -> None:
    """Test successful dataset search."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [{"title": "Test DEM", "downloadURL": "https://example.com/dem.tif"}]
    }
    mock_get.return_value = mock_response

    bbox = (-121.0, 38.0, -120.0, 39.0)
    results = usgs_client.search_datasets(bbox=bbox)

    assert len(results) == 1
    assert results[0]["title"] == "Test DEM"


@patch("firetwin.data.clients.usgs.requests.get")
def test_download_dataset_success(mock_get: Mock, usgs_client: USGS3DEPClient, tmp_path) -> None:
    """Test successful dataset download."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content = Mock(return_value=[b"test data"])
    mock_get.return_value = mock_response

    output_path = tmp_path / "test.tif"
    result = usgs_client.download_dataset(
        dataset_url="https://example.com/dem.tif", output_path=output_path
    )

    assert result == output_path
    assert output_path.exists()


@patch("firetwin.data.clients.usgs.requests.get")
def test_download_bbox_success(mock_get: Mock, usgs_client: USGS3DEPClient, tmp_path) -> None:
    """Test successful bbox download."""
    # Mock search response
    search_response = Mock()
    search_response.status_code = 200
    search_response.json.return_value = {
        "items": [{"title": "Test DEM", "downloadURL": "https://example.com/dem.tif"}]
    }

    # Mock download response
    download_response = Mock()
    download_response.status_code = 200
    download_response.iter_content = Mock(return_value=[b"test data"])

    mock_get.side_effect = [search_response, download_response]

    bbox = (-121.0, 38.0, -120.0, 39.0)
    files = usgs_client.download_bbox(bbox=bbox, output_dir=tmp_path)

    assert len(files) == 1
    assert files[0].exists()


def test_list_available_datasets() -> None:
    """Test listing available datasets."""
    datasets = USGS3DEPClient.list_available_datasets()

    assert isinstance(datasets, dict)
    assert len(datasets) > 0
    assert all(isinstance(v, str) for v in datasets.values())
