"""Unit tests for LANDFIRE client."""

import pytest

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
    """Test download raises NotImplementedError (requires web portal)."""
    with pytest.raises(NotImplementedError, match="LANDFIRE requires manual"):
        landfire_client.download_product(
            product="fbfm40", _version="2.3.0", _output_path=tmp_path / "test.tif"
        )


def test_get_download_instructions() -> None:
    """Test getting download instructions."""
    instructions = LANDFIREClient.get_download_instructions()

    assert isinstance(instructions, str)
    assert "landfire.gov" in instructions
    assert "AOI" in instructions
