"""Unit tests for LANDFIRE client."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from firetwin.data.clients.landfire import LANDFIREClient


@pytest.fixture
def landfire_client() -> LANDFIREClient:
    """Create LANDFIRE client fixture."""
    return LANDFIREClient()


def test_landfire_client_init() -> None:
    """Test LANDFIRE client initialization."""
    client = LANDFIREClient(timeout=60)
    assert client.timeout == 60


def test_list_available_products() -> None:
    """Test listing available products."""
    products = LANDFIREClient.list_available_products()

    assert isinstance(products, dict)
    assert "fbfm40" in products
    assert "cc" in products
    assert "slp" in products


def test_download_product_invalid_product(landfire_client: LANDFIREClient, tmp_path) -> None:
    """Test download with invalid product raises error."""
    with pytest.raises(ValueError, match="Unknown product"):
        landfire_client.download_product(
            product="invalid", _version="2.3.0", _output_path=tmp_path / "test.tif"
        )


def test_download_product_not_implemented(landfire_client: LANDFIREClient, tmp_path) -> None:
    """Test generic download raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="Use export_fbfm40"):
        landfire_client.download_product(
            product="fbfm40", _version="2.3.0", _output_path=tmp_path / "test.tif"
        )


def test_export_fbfm40_downloads_image(monkeypatch, landfire_client: LANDFIREClient, tmp_path):
    """Test FBFM40 ImageServer export request and image download."""
    calls = []

    class FakeResponse:
        def __init__(self, json_payload=None, content=b"") -> None:
            self._json_payload = json_payload
            self._content = content

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return self._json_payload

        def iter_content(self, chunk_size: int):
            yield self._content[:chunk_size]

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/exportImage"):
            return FakeResponse(json_payload={"href": "https://example.test/fbfm40.tif"})
        return FakeResponse(content=b"geotiff-bytes")

    monkeypatch.setattr("firetwin.data.clients.landfire.requests.get", fake_get)

    output_path = landfire_client.export_fbfm40(
        grid_bounds=(0.0, 10.0, 300.0, 210.0),
        grid_shape=(2, 3),
        target_crs="EPSG:32610",
        output_path=tmp_path / "fbfm40.tif",
    )

    assert output_path.read_bytes() == b"geotiff-bytes"
    export_url, export_kwargs = calls[0]
    assert export_url.endswith("/exportImage")
    assert export_kwargs["params"]["bboxSR"] == "32610"
    assert export_kwargs["params"]["imageSR"] == "32610"
    assert export_kwargs["params"]["size"] == "3,2"
    assert export_kwargs["params"]["interpolation"] == "RSP_NearestNeighbor"
    assert calls[1][0] == "https://example.test/fbfm40.tif"


def test_load_aligned_fbfm40_normalizes_non_burnable(
    landfire_client: LANDFIREClient, tmp_path
) -> None:
    """Test nearest-neighbor loading and non-burnable normalization."""
    raster_path = tmp_path / "fbfm40.tif"
    transform = from_bounds(0.0, 0.0, 300.0, 200.0, 3, 2)
    raw = np.array(
        [
            [91, 101, 141],
            [98, 181, 202],
        ],
        dtype=np.int16,
    )
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=2,
        width=3,
        count=1,
        dtype="int16",
        crs="EPSG:32610",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(raw, 1)

    aligned = landfire_client.load_aligned_fbfm40(
        raster_path=raster_path,
        grid_bounds=(0.0, 0.0, 300.0, 200.0),
        grid_shape=(2, 3),
        target_crs="EPSG:32610",
    )

    np.testing.assert_array_equal(
        aligned,
        np.array(
            [
                [0, 101, 141],
                [0, 181, 202],
            ],
            dtype=np.int32,
        ),
    )


def test_derive_fuel_properties_from_fbfm40() -> None:
    """Test deterministic proxy fuel properties for common FBFM40 groups."""
    fuel_model = np.array([[0, 101, 124], [149, 165, 204]], dtype=np.int32)

    fuel_load, moisture = LANDFIREClient.derive_fuel_properties(fuel_model)

    assert fuel_load.dtype == np.float32
    assert moisture.dtype == np.float32
    assert fuel_load[0, 0] == 0.0
    assert moisture[0, 0] == 0.0
    assert fuel_load[0, 1] > 0.0
    assert fuel_load[1, 2] > fuel_load[0, 1]
    assert moisture[0, 1] == 6.0
    assert moisture[1, 1] == 9.0


def test_get_download_instructions() -> None:
    """Test getting download instructions."""
    instructions = LANDFIREClient.get_download_instructions()

    assert isinstance(instructions, str)
    assert "landfire.gov" in instructions
    assert "export_fbfm40" in instructions
