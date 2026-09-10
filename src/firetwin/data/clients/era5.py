"""ERA5-Land weather data client via Copernicus Climate Data Store (CDS) API.

Official documentation:
- CDS Portal: https://cds.climate.copernicus.eu
- API Setup: https://cds.climate.copernicus.eu/how-to-api
- ERA5-Land Dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

ERA5-Land provides hourly reanalysis data at 9km resolution from 1950-present:
- Temperature, wind, precipitation
- Soil moisture, snow depth
- Solar radiation, surface pressure

Requires:
- Free CDS account and API key
- cdsapi package (already in environment.yml)
- Accept dataset license terms
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import xarray as xr

from firetwin.schemas.core import WeatherData

try:
    import cdsapi
except ImportError:
    cdsapi = None


class ERA5LandClient:
    """Client for ERA5-Land hourly weather data via CDS API.

    Requires CDS API credentials in ~/.cdsapirc:
        url: https://cds.climate.copernicus.eu/api
        key: <YOUR-UID>:<YOUR-API-KEY>
    """

    DATASET = "reanalysis-era5-land"
    WEATHER_SOURCE = "ERA5-Land hourly reanalysis via Copernicus Climate Data Store"

    # Common weather variables for fire modeling
    FIRE_WEATHER_VARS = [
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "total_precipitation",
        "surface_pressure",
        "2m_dewpoint_temperature",
    ]

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        """Initialize ERA5-Land client.

        Args:
            url: Optional CDS API URL (overrides ~/.cdsapirc)
            key: Optional CDS API key (overrides ~/.cdsapirc)

        Raises:
            ImportError: If cdsapi package not installed
            RuntimeError: If credentials not configured
        """
        if cdsapi is None:
            raise ImportError("cdsapi package required. Install with: pip install cdsapi>=0.7.0")

        # Initialize CDS client with optional credentials
        if url and key:
            self.client = cdsapi.Client(url=url, key=key)
        else:
            # Uses ~/.cdsapirc if available
            self.client = cdsapi.Client()

    @staticmethod
    def wgs84_bbox_to_cds_area(
        bbox: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        """Convert WGS84 bounds to CDS area order: north, west, south, east."""
        min_lon, min_lat, max_lon, max_lat = bbox
        return (max_lat, min_lon, min_lat, max_lon)

    @staticmethod
    def _date_range(start_date: date, end_date: date) -> list[date]:
        """Return all dates in an inclusive date range."""
        days = (end_date - start_date).days
        return [start_date + timedelta(days=offset) for offset in range(days + 1)]

    @classmethod
    def _date_components(cls, start_date: date, end_date: date) -> dict[str, list[str]]:
        """Build exact year/month/day request lists for an inclusive date range."""
        dates = cls._date_range(start_date, end_date)
        return {
            "year": sorted({str(d.year) for d in dates}),
            "month": sorted({f"{d.month:02d}" for d in dates}),
            "day": sorted({f"{d.day:02d}" for d in dates}),
        }

    def download_area(
        self,
        bbox: tuple[float, float, float, float],
        start_date: date,
        end_date: date,
        variables: list[str] | None = None,
        hours: list[str] | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """Download ERA5-Land data for a bounding box and time range.

        Args:
            bbox: Bounding box as (north, west, south, east) in degrees
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            variables: List of variable names (default: FIRE_WEATHER_VARS)
            hours: List of hours as strings (default: all 24 hours)
            output_path: Output NetCDF file path (default: auto-generated)

        Returns:
            Path to downloaded NetCDF file

        Raises:
            ValueError: If date range is invalid
        """
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        # Use fire weather variables if not specified
        if variables is None:
            variables = self.FIRE_WEATHER_VARS

        # Default to all hours if not specified
        if hours is None:
            hours = [f"{h:02d}:00" for h in range(24)]

        # Generate output path if not provided
        if output_path is None:
            output_path = Path(f"era5land_{start_date.isoformat()}_{end_date.isoformat()}.nc")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        date_components = self._date_components(start_date, end_date)

        # Build CDS API request
        request = {
            "product_type": ["reanalysis"],
            "variable": variables,
            "year": date_components["year"],
            "month": date_components["month"],
            "day": date_components["day"],
            "time": hours,
            "area": bbox,  # [North, West, South, East]
            "data_format": "netcdf",
            "download_format": "unarchived",
        }

        # Submit request to CDS
        self.client.retrieve(self.DATASET, request, str(output_path))

        return output_path

    def download_point(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        variables: list[str] | None = None,
        hours: list[str] | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """Download ERA5-Land data for a single point (small bbox).

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            variables: List of variable names (default: FIRE_WEATHER_VARS)
            hours: List of hours as strings (default: all 24 hours)
            output_path: Output NetCDF file path (default: auto-generated)

        Returns:
            Path to downloaded NetCDF file
        """
        # Create small bbox around point (±0.1 degrees)
        bbox = (lat + 0.1, lon - 0.1, lat - 0.1, lon + 0.1)

        return self.download_area(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            variables=variables,
            hours=hours,
            output_path=output_path,
        )

    @staticmethod
    def _resolve_variable(ds: xr.Dataset, candidates: tuple[str, ...]) -> str:
        """Find the first available variable name from common ERA5 naming variants."""
        for name in candidates:
            if name in ds:
                return name
        raise ValueError(f"None of the expected variables are present: {candidates}")

    @staticmethod
    def _to_celsius(value: float) -> float:
        """Convert Kelvin-like temperatures to Celsius while accepting Celsius inputs."""
        return value - 273.15 if value > 150.0 else value

    @staticmethod
    def _relative_humidity_from_dewpoint(
        temperature_c: float,
        dewpoint_c: float,
    ) -> float:
        """Estimate relative humidity from temperature and dewpoint in Celsius."""
        saturation = np.exp((17.625 * temperature_c) / (243.04 + temperature_c))
        actual = np.exp((17.625 * dewpoint_c) / (243.04 + dewpoint_c))
        return float(np.clip(100.0 * actual / saturation, 0.0, 100.0))

    @staticmethod
    def _wind_direction_from_components(u_m_s: float, v_m_s: float) -> float:
        """Return meteorological wind direction degrees from north."""
        return float((270.0 - np.degrees(np.arctan2(v_m_s, u_m_s))) % 360.0)

    @staticmethod
    def _spatial_subset(
        da: xr.DataArray,
        bbox: tuple[float, float, float, float] | None,
    ) -> xr.DataArray:
        """Subset a DataArray by WGS84 bbox if latitude/longitude coordinates exist."""
        if bbox is None:
            return da
        if "latitude" not in da.coords or "longitude" not in da.coords:
            return da

        min_lon, min_lat, max_lon, max_lat = bbox
        lat_values = da.coords["latitude"].values
        lat_slice = (
            slice(max_lat, min_lat) if lat_values[0] > lat_values[-1] else slice(min_lat, max_lat)
        )
        return da.sel(latitude=lat_slice, longitude=slice(min_lon, max_lon))

    @classmethod
    def summarize_weather_dataset(
        cls,
        ds: xr.Dataset,
        timestamp: datetime | None = None,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> WeatherData:
        """Convert an ERA5-Land dataset into FireTwin scalar weather forcing.

        The scalar is a spatial mean over the requested AOI at the requested hour
        or, if no timestamp is supplied, a mean over all available times.
        """
        temp_var = cls._resolve_variable(ds, ("t2m", "2m_temperature"))
        dewpoint_var = cls._resolve_variable(ds, ("d2m", "2m_dewpoint_temperature"))
        u_var = cls._resolve_variable(ds, ("u10", "10m_u_component_of_wind"))
        v_var = cls._resolve_variable(ds, ("v10", "10m_v_component_of_wind"))

        selected = ds
        weather_timestamp = timestamp
        if timestamp is not None and "time" in ds.coords:
            selected = ds.sel(time=np.datetime64(timestamp), method="nearest")
            time_value = selected.coords["time"].values
            weather_timestamp = np.datetime64(time_value).astype("datetime64[s]").astype(datetime)
        elif "time" in ds.coords:
            time_value = ds.coords["time"].values[0]
            weather_timestamp = np.datetime64(time_value).astype("datetime64[s]").astype(datetime)

        if weather_timestamp is None:
            weather_timestamp = datetime.combine(date.today(), time())

        def mean_value(variable: str) -> float:
            da = cls._spatial_subset(selected[variable], bbox)
            if da.size == 0:
                raise ValueError(f"ERA5 variable {variable} has no cells within bbox")
            return float(da.mean(skipna=True).values)

        temperature_c = cls._to_celsius(mean_value(temp_var))
        dewpoint_c = cls._to_celsius(mean_value(dewpoint_var))
        u_m_s = mean_value(u_var)
        v_m_s = mean_value(v_var)

        return WeatherData(
            temperature_c=float(temperature_c),
            relative_humidity_percent=cls._relative_humidity_from_dewpoint(
                temperature_c,
                dewpoint_c,
            ),
            wind_speed_m_s=float(np.hypot(u_m_s, v_m_s)),
            wind_direction_degrees=cls._wind_direction_from_components(u_m_s, v_m_s),
            timestamp=weather_timestamp,
        )

    def load_weather_data(
        self,
        netcdf_path: Path,
        timestamp: datetime | None = None,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> WeatherData:
        """Load a cached ERA5-Land NetCDF file and summarize it to WeatherData."""
        with xr.open_dataset(netcdf_path) as ds:
            return self.summarize_weather_dataset(ds, timestamp=timestamp, bbox=bbox)

    def build_weather_data(
        self,
        bbox: tuple[float, float, float, float],
        start_datetime: datetime,
        end_datetime: datetime,
        output_path: Path,
    ) -> WeatherData:
        """Download/cache ERA5-Land and return scalar FireTwin weather forcing."""
        if start_datetime > end_datetime:
            raise ValueError("start_datetime must be <= end_datetime")

        cds_area = self.wgs84_bbox_to_cds_area(bbox)
        if not output_path.exists() or output_path.stat().st_size == 0:
            hours = sorted(
                {
                    f"{(start_datetime + timedelta(hours=hour)).hour:02d}:00"
                    for hour in range(
                        int((end_datetime - start_datetime).total_seconds() // 3600) + 1
                    )
                }
            )
            self.download_area(
                bbox=cds_area,
                start_date=start_datetime.date(),
                end_date=end_datetime.date(),
                hours=hours,
                output_path=output_path,
            )

        return self.load_weather_data(
            netcdf_path=output_path,
            timestamp=start_datetime,
            bbox=bbox,
        )

    @staticmethod
    def list_available_variables() -> dict[str, str]:
        """Get dictionary of available ERA5-Land variables.

        Returns:
            Dict mapping variable names to descriptions
        """
        return {
            "2m_temperature": "2-meter air temperature (K)",
            "10m_u_component_of_wind": "10m U wind component (m/s)",
            "10m_v_component_of_wind": "10m V wind component (m/s)",
            "total_precipitation": "Total precipitation (m)",
            "surface_pressure": "Surface pressure (Pa)",
            "2m_dewpoint_temperature": "2m dewpoint temperature (K)",
            "soil_temperature_level_1": "Soil temperature 0-7cm (K)",
            "volumetric_soil_water_layer_1": "Soil moisture 0-7cm (m³/m³)",
            "snow_depth": "Snow depth (m)",
            "surface_solar_radiation_downwards": "Solar radiation (J/m²)",
            "surface_thermal_radiation_downwards": "Thermal radiation (J/m²)",
        }
