"""Unit tests for ERA5-Land API client."""

from datetime import date, datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest
import xarray as xr

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
    assert request["product_type"] == ["reanalysis"]
    assert request["data_format"] == "netcdf"
    assert request["download_format"] == "unarchived"
    assert request["area"] == bbox
    assert request["year"] == ["2024"]
    assert request["month"] == ["08"]
    assert request["day"] == ["01", "02"]


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


def test_wgs84_bbox_to_cds_area() -> None:
    """Test conversion from FireTwin bbox order to CDS area order."""
    assert ERA5LandClient.wgs84_bbox_to_cds_area((-121.5, 38.5, -120.0, 39.5)) == (
        39.5,
        -121.5,
        38.5,
        -120.0,
    )


def test_summarize_weather_dataset() -> None:
    """Test converting ERA5 variables to scalar WeatherData."""
    times = np.array(["2014-09-13T23:00:00", "2014-09-14T00:00:00"], dtype="datetime64[ns]")
    latitudes = np.array([39.5, 39.4])
    longitudes = np.array([-120.7, -120.6])
    ds = xr.Dataset(
        data_vars={
            "t2m": (
                ["time", "latitude", "longitude"],
                np.full((2, 2, 2), 300.15, dtype=np.float32),
            ),
            "d2m": (
                ["time", "latitude", "longitude"],
                np.full((2, 2, 2), 290.15, dtype=np.float32),
            ),
            "u10": (
                ["time", "latitude", "longitude"],
                np.full((2, 2, 2), 3.0, dtype=np.float32),
            ),
            "v10": (
                ["time", "latitude", "longitude"],
                np.full((2, 2, 2), 4.0, dtype=np.float32),
            ),
        },
        coords={"time": times, "latitude": latitudes, "longitude": longitudes},
    )

    weather = ERA5LandClient.summarize_weather_dataset(
        ds,
        timestamp=datetime(2014, 9, 13, 23),
        bbox=(-121.0, 39.0, -120.0, 40.0),
    )

    assert weather.timestamp == datetime(2014, 9, 13, 23)
    assert weather.temperature_c == pytest.approx(27.0)
    assert weather.relative_humidity_percent == pytest.approx(54.3, abs=0.2)
    assert weather.wind_speed_m_s == pytest.approx(5.0)
    assert weather.wind_direction_degrees == pytest.approx(216.87, abs=0.01)


def test_load_weather_data_reads_netcdf(era5_client: ERA5LandClient, tmp_path) -> None:
    """Test loading a cached ERA5 NetCDF into WeatherData."""
    netcdf_path = tmp_path / "weather.nc"
    ds = xr.Dataset(
        data_vars={
            "2m_temperature": (["time"], np.array([298.15], dtype=np.float32)),
            "2m_dewpoint_temperature": (["time"], np.array([288.15], dtype=np.float32)),
            "10m_u_component_of_wind": (["time"], np.array([0.0], dtype=np.float32)),
            "10m_v_component_of_wind": (["time"], np.array([-2.0], dtype=np.float32)),
        },
        coords={"time": np.array(["2014-07-14T12:00:00"], dtype="datetime64[ns]")},
    )
    ds.to_netcdf(netcdf_path)

    weather = era5_client.load_weather_data(
        netcdf_path,
        timestamp=datetime(2014, 7, 14, 12),
    )

    assert weather.temperature_c == pytest.approx(25.0)
    assert weather.wind_speed_m_s == pytest.approx(2.0)
    assert weather.wind_direction_degrees == pytest.approx(0.0)


def test_build_weather_data_uses_cached_file(
    monkeypatch,
    era5_client: ERA5LandClient,
    tmp_path,
) -> None:
    """Test cache-aware weather build avoids a CDS request when NetCDF exists."""
    netcdf_path = tmp_path / "cached.nc"
    ds = xr.Dataset(
        data_vars={
            "t2m": (["time"], np.array([295.15], dtype=np.float32)),
            "d2m": (["time"], np.array([285.15], dtype=np.float32)),
            "u10": (["time"], np.array([1.0], dtype=np.float32)),
            "v10": (["time"], np.array([0.0], dtype=np.float32)),
        },
        coords={"time": np.array(["2014-08-02T12:00:00"], dtype="datetime64[ns]")},
    )
    ds.to_netcdf(netcdf_path)
    era5_client.download_area = Mock()

    weather = era5_client.build_weather_data(
        bbox=(-117.5, 45.4, -116.2, 46.6),
        start_datetime=datetime(2014, 8, 2, 12),
        end_datetime=datetime(2014, 8, 3, 11),
        output_path=netcdf_path,
    )

    era5_client.download_area.assert_not_called()
    assert weather.temperature_c == pytest.approx(22.0)
    assert weather.wind_speed_m_s == pytest.approx(1.0)


def test_build_weather_data_rejects_invalid_datetime_range(
    era5_client: ERA5LandClient, tmp_path
) -> None:
    """Test weather build rejects reversed datetime ranges."""
    with pytest.raises(ValueError, match="start_datetime"):
        era5_client.build_weather_data(
            bbox=(-117.5, 45.4, -116.2, 46.6),
            start_datetime=datetime(2014, 8, 3, 12),
            end_datetime=datetime(2014, 8, 2, 12),
            output_path=tmp_path / "weather.nc",
        )
