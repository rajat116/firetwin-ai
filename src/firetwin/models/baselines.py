"""Baseline fire spread forecast models for benchmarking."""

from abc import ABC, abstractmethod
from datetime import timedelta

import numpy as np
from scipy import ndimage

from firetwin.schemas import FireCase, FireState


class BaselineForecastModel(ABC):
    """Abstract base class for baseline forecast models."""

    @abstractmethod
    def forecast(
        self, case: FireCase, forecast_hours: list[float]
    ) -> dict[float, FireState]:
        """Generate forecasts at specified hours from initial state.

        Args:
            case: FireCase with initial state
            forecast_hours: List of forecast horizons in hours (e.g., [3, 6, 12, 24])

        Returns:
            Dictionary mapping forecast_hour -> FireState
        """
        pass


class PersistenceBaseline(BaselineForecastModel):
    """Persistence forecast: future state = current state.

    This is the simplest baseline - assumes no change.
    """

    def forecast(
        self, case: FireCase, forecast_hours: list[float]
    ) -> dict[float, FireState]:
        """Generate persistence forecasts."""
        forecasts = {}

        for hours in forecast_hours:
            # Simply copy the initial state
            forecast_time = case.initial_state.timestamp + timedelta(hours=hours)
            forecasts[hours] = FireState(
                burned=case.initial_state.burned.copy(),
                active_front=case.initial_state.active_front.copy(),
                timestamp=forecast_time,
                resolution_m=case.resolution_m,
                bbox=case.terrain.bbox,
            )

        return forecasts


class RadialBaseline(BaselineForecastModel):
    """Radial spread baseline: uniform circular expansion.

    Spreads fire radially from the initial burned area at a constant rate,
    respecting non-burnable fuels.

    Args:
        spread_rate_m_h: Spread rate in meters per hour (default: 100)
    """

    def __init__(self, spread_rate_m_h: float = 100.0):
        """Initialize radial baseline."""
        self.spread_rate_m_h = spread_rate_m_h

    def forecast(
        self, case: FireCase, forecast_hours: list[float]
    ) -> dict[float, FireState]:
        """Generate radial spread forecasts."""
        forecasts = {}
        resolution_m = case.resolution_m

        for hours in forecast_hours:
            # Calculate spread distance in cells
            spread_distance_m = self.spread_rate_m_h * hours
            spread_cells = int(np.ceil(spread_distance_m / resolution_m))

            # Dilate burned area by spread distance
            burned = case.initial_state.burned.copy()

            # Create circular structuring element
            radius = spread_cells
            y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
            kernel = x**2 + y**2 <= radius**2

            # Dilate to simulate spread
            burned_forecast = ndimage.binary_dilation(
                burned, structure=kernel, iterations=1
            ).astype(np.int32)

            # Respect non-burnable fuels (fuel_model == 0)
            burnable = case.fuels.fuel_model > 0
            burned_forecast = burned_forecast & burnable

            # Active front is new burned area
            active_front = (burned_forecast & ~burned).astype(np.int32)

            forecast_time = case.initial_state.timestamp + timedelta(hours=hours)
            forecasts[hours] = FireState(
                burned=burned_forecast,
                active_front=active_front,
                timestamp=forecast_time,
                resolution_m=resolution_m,
                bbox=case.terrain.bbox,
            )

        return forecasts


class EllipticalBaseline(BaselineForecastModel):
    """Wind-driven elliptical spread baseline.

    Spreads fire in an elliptical pattern aligned with wind direction.
    Common operational baseline (e.g., Rothermel-based models).

    Args:
        base_spread_rate_m_h: Base spread rate in meters per hour
        wind_factor: Multiplier for spread in wind direction (default: 2.0)
        lateral_factor: Multiplier for lateral spread (default: 0.5)
    """

    def __init__(
        self,
        base_spread_rate_m_h: float = 100.0,
        wind_factor: float = 2.0,
        lateral_factor: float = 0.5,
    ):
        """Initialize elliptical baseline."""
        self.base_spread_rate_m_h = base_spread_rate_m_h
        self.wind_factor = wind_factor
        self.lateral_factor = lateral_factor

    def forecast(
        self, case: FireCase, forecast_hours: list[float]
    ) -> dict[float, FireState]:
        """Generate elliptical spread forecasts."""
        forecasts = {}
        resolution_m = case.resolution_m

        # Wind direction (degrees from north, clockwise)
        wind_dir_deg = case.weather.wind_direction_degrees
        wind_dir_rad = np.deg2rad(wind_dir_deg)

        # Adjust spread rate by wind speed
        wind_multiplier = 1.0 + (case.weather.wind_speed_m_s / 10.0)  # Normalized

        for hours in forecast_hours:
            # Calculate spread distances
            head_fire_rate = (
                self.base_spread_rate_m_h * self.wind_factor * wind_multiplier
            )
            flank_fire_rate = self.base_spread_rate_m_h * self.lateral_factor
            back_fire_rate = self.base_spread_rate_m_h * 0.3  # Very slow backing

            # Spread in wind direction (head)
            head_spread_m = head_fire_rate * hours
            # Spread perpendicular to wind (flanks)
            flank_spread_m = flank_fire_rate * hours
            # Spread opposite wind (back)
            back_spread_m = back_fire_rate * hours

            # Create elliptical kernel
            # Major axis aligned with wind direction
            a = int(np.ceil(head_spread_m / resolution_m))  # Downwind
            b = int(np.ceil(flank_spread_m / resolution_m))  # Crosswind
            c = int(np.ceil(back_spread_m / resolution_m))  # Upwind

            # Create kernel grid
            max_radius = max(a, b, c)
            y_grid, x_grid = np.ogrid[
                -max_radius : max_radius + 1, -max_radius : max_radius + 1
            ]

            # Rotate grid to align with wind
            # Wind direction is "from" direction, fire spreads "to" opposite
            fire_dir_rad = wind_dir_rad + np.pi  # Fire spreads opposite wind origin
            cos_theta = np.cos(fire_dir_rad)
            sin_theta = np.sin(fire_dir_rad)

            # Rotate coordinates
            x_rot = x_grid * cos_theta - y_grid * sin_theta
            y_rot = x_grid * sin_theta + y_grid * cos_theta

            # Elliptical condition (different radii for each direction)
            # Positive y_rot is downwind, negative is upwind
            kernel = np.zeros_like(x_rot, dtype=bool)
            kernel[(y_rot >= 0) & ((x_rot**2 / b**2) + (y_rot**2 / a**2) <= 1)] = True
            kernel[(y_rot < 0) & ((x_rot**2 / b**2) + (y_rot**2 / c**2) <= 1)] = True

            # Dilate burned area
            burned = case.initial_state.burned.copy()
            burned_forecast = ndimage.binary_dilation(
                burned, structure=kernel, iterations=1
            ).astype(np.int32)

            # Respect non-burnable fuels
            burnable = case.fuels.fuel_model > 0
            burned_forecast = burned_forecast & burnable

            # Active front
            active_front = (burned_forecast & ~burned).astype(np.int32)

            forecast_time = case.initial_state.timestamp + timedelta(hours=hours)
            forecasts[hours] = FireState(
                burned=burned_forecast,
                active_front=active_front,
                timestamp=forecast_time,
                resolution_m=resolution_m,
                bbox=case.terrain.bbox,
            )

        return forecasts
