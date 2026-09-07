"""Unit tests for ERA5-Land API client."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from firetwin.data.clients.era5 import ERA5LandClient


@pytest.fixture
def era5_client() -> ERA5LandClient:
    """Create ERA5-Land client fixture with mocked cdsapi."""
    with patch("firetwin.data.clients.era5.cdsapi") as mock_cdsapi:
        mock_cdsapi.Client.return_value = Mock()
        client = ERA5LandClient()
        return client


def test_era5_client_init_with_credentials() -> None:
    """Test ERA5-Land client initialization with credentials."""
    with patch("firetwin.data.clients.era5.cdsapi") as mock_cdsapi:
        mock_client = Mock()
        mock_cdsapi.Client.return_value = mock_client

        client = ERA5LandClient(url="https://test.url", key="test:key")

        mock_cdsapi.Client.assert_called_once_with(url="https://test.url", key="test:key")
        assert client.client == mock_client


def test_era5_client_init_without_cdsapi() -> None:
    """Test ERA5-Land client raises error if cdsapi not installed."""
    with (
        patch("firetwin.data.clients.era5.cdsapi", None),
        pytest.raises(ImportError, match="cdsapi package required"),
    ):
        ERA5LandClient()


def test_download_area_success(era5_client: ERA5LandClient, tmp_path) -> None:
    """Test successful area download."""
    bbox = (39.0, -121.0, 38.0, -120.0)
    start_date = date(2024, 8, 1)
    end_date = date(2024, 8, 2)
    output_path = tmp_path / "test.nc"

    # Mock the retrieve method
    era5_client.client.retrieve = Mock()

    result_path = era5_client.download_area(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
    )

    assert result_path == output_path
    era5_client.client.retrieve.assert_called_once()

    # Verify request structure
    call_args = era5_client.client.retrieve.call_args
    request = call_args[0][1]
    assert "variable" in request
    assert "year" in request
    assert "area" in request
    assert request["area"] == bbox


def test_download_area_invalid_dates(era5_client: ERA5LandClient) -> None:
    """Test download with invalid date range raises error."""
    bbox = (39.0, -121.0, 38.0, -120.0)
    start_date = date(2024, 8, 2)
    end_date = date(2024, 8, 1)

    with pytest.raises(ValueError, match="start_date must be"):
        era5_client.download_area(bbox=bbox, start_date=start_date, end_date=end_date)


def test_download_point_success(era5_client: ERA5LandClient, tmp_path) -> None:
    """Test successful point download."""
    lat, lon = 38.5, -120.5
    start_date = date(2024, 8, 1)
    end_date = date(2024, 8, 1)
    output_path = tmp_path / "test.nc"

    # Mock the retrieve method
    era5_client.client.retrieve = Mock()

    result_path = era5_client.download_point(
        lat=lat,
        lon=lon,
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
    )

    assert result_path == output_path
    era5_client.client.retrieve.assert_called_once()

    # Verify bbox was created around point
    call_args = era5_client.client.retrieve.call_args
    request = call_args[0][1]
    bbox = request["area"]
    assert isinstance(bbox, tuple)
    assert len(bbox) == 4


def test_download_with_custom_variables(era5_client: ERA5LandClient, tmp_path) -> None:
    """Test download with custom variables."""
    bbox = (39.0, -121.0, 38.0, -120.0)
    start_date = date(2024, 8, 1)
    end_date = date(2024, 8, 1)
    custom_vars = ["2m_temperature", "total_precipitation"]

    era5_client.client.retrieve = Mock()

    era5_client.download_area(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        variables=custom_vars,
    )

    call_args = era5_client.client.retrieve.call_args
    request = call_args[0][1]
    assert request["variable"] == custom_vars


def test_download_with_custom_hours(era5_client: ERA5LandClient, tmp_path) -> None:
    """Test download with custom hours."""
    bbox = (39.0, -121.0, 38.0, -120.0)
    start_date = date(2024, 8, 1)
    end_date = date(2024, 8, 1)
    custom_hours = ["00:00", "12:00"]

    era5_client.client.retrieve = Mock()

    era5_client.download_area(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        hours=custom_hours,
    )

    call_args = era5_client.client.retrieve.call_args
    request = call_args[0][1]
    assert request["time"] == custom_hours


def test_list_available_variables() -> None:
    """Test listing available variables."""
    vars_dict = ERA5LandClient.list_available_variables()

    assert isinstance(vars_dict, dict)
    assert "2m_temperature" in vars_dict
    assert "10m_u_component_of_wind" in vars_dict
    assert all(isinstance(v, str) for v in vars_dict.values())
