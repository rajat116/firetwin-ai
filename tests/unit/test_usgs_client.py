"""Unit tests for USGS 3DEP client."""

from unittest.mock import Mock, patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

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
    mock_response.raise_for_status.assert_called_once()
    params = mock_get.call_args.kwargs["params"]
    assert params["datasets"] == USGS3DEPClient.DEFAULT_DATASET
    assert params["prodFormats"] == "GeoTIFF"


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
        "items": [
            {
                "title": "USGS 1 Arc Second n39w121 20250101",
                "downloadURL": "https://example.com/n39w121/USGS_1_n39w121_20250101.tif",
                "format": "GeoTIFF",
                "publicationDate": "2025-01-01",
            }
        ]
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


@patch("firetwin.data.clients.usgs.requests.get")
def test_download_bbox_uses_cached_tiles_when_search_fails(
    mock_get: Mock,
    usgs_client: USGS3DEPClient,
    tmp_path,
) -> None:
    """Cached DEMs should keep rebuilds reproducible during transient TNM outages."""
    import requests

    cached_tile = tmp_path / "cached_dem.tif"
    cached_tile.write_bytes(b"cached")
    mock_get.side_effect = requests.Timeout("temporary outage")

    files = usgs_client.download_bbox(
        bbox=(-121.0, 38.0, -120.0, 39.0),
        output_dir=tmp_path,
    )

    assert files == [cached_tile]


def test_select_latest_geotiff_tiles() -> None:
    """Only the newest GeoTIFF for each tile should be selected."""
    items = [
        {
            "title": "USGS 1 Arc Second n39w121 20200101",
            "downloadURL": "https://example.com/n39w121/old.tif",
            "format": "GeoTIFF",
            "publicationDate": "2020-01-01",
        },
        {
            "title": "USGS 1 Arc Second n39w121 20250101",
            "downloadURL": "https://example.com/n39w121/new.tif",
            "format": "GeoTIFF",
            "publicationDate": "2025-01-01",
        },
        {
            "title": "USGS 1 Arc Second n40w121 20240101",
            "downloadURL": "https://example.com/n40w121/current.tif",
            "format": "GeoTIFF",
            "publicationDate": "2024-01-01",
        },
        {
            "title": "USGS 1 Arc Second n40w121 20260101",
            "downloadURL": "https://example.com/n40w121/current.img",
            "format": "IMG",
            "publicationDate": "2026-01-01",
        },
    ]

    selected = USGS3DEPClient.select_latest_geotiff_tiles(items)

    assert [item["downloadURL"] for item in selected] == [
        "https://example.com/n39w121/new.tif",
        "https://example.com/n40w121/current.tif",
    ]


def test_load_aligned_dem_and_derive_terrain(tmp_path, usgs_client: USGS3DEPClient) -> None:
    """DEM loading should preserve real elevation variation on the target grid."""
    dem_path = tmp_path / "dem.tif"
    transform = from_origin(500000.0, 500400.0, 100.0, 100.0)
    elevation = np.array(
        [
            [100.0, 110.0, 120.0, 130.0],
            [105.0, 115.0, 125.0, 135.0],
            [110.0, 120.0, 130.0, 140.0],
            [115.0, 125.0, 135.0, 145.0],
        ],
        dtype=np.float32,
    )

    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="float32",
        crs="EPSG:32610",
        transform=transform,
    ) as dataset:
        dataset.write(elevation, 1)

    aligned = usgs_client.load_aligned_dem(
        dem_paths=[dem_path],
        grid_bounds=(500000.0, 500000.0, 500400.0, 500400.0),
        grid_shape=(4, 4),
        target_crs="EPSG:32610",
    )
    slope, aspect = usgs_client.derive_slope_aspect(aligned, resolution_m=100.0)

    assert aligned.shape == (4, 4)
    assert float(aligned.max()) > float(aligned.min())
    assert np.isfinite(aligned).all()
    assert np.all(slope > 0.0)
    assert np.all((aspect >= 0.0) & (aspect < 360.0))


def test_list_available_datasets() -> None:
    """Test listing available datasets."""
    datasets = USGS3DEPClient.list_available_datasets()

    assert isinstance(datasets, dict)
    assert len(datasets) > 0
    assert all(isinstance(v, str) for v in datasets.values())
