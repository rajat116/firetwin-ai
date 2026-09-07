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

from datetime import date
from pathlib import Path

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

        # Build years, months, days lists
        years = list(range(start_date.year, end_date.year + 1))
        months = list(range(1, 13))
        days = list(range(1, 32))

        # Build CDS API request
        request = {
            "variable": variables,
            "year": [str(y) for y in years],
            "month": [f"{m:02d}" for m in months],
            "day": [f"{d:02d}" for d in days],
            "time": hours,
            "area": bbox,  # [North, West, South, East]
            "format": "netcdf",
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
