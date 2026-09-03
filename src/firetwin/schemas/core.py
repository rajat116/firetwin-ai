"""Core data schemas for geospatial fire modeling."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

import numpy as np
from pydantic import BaseModel, Field, field_validator


class CoordinateSystem(StrEnum):
    """Supported coordinate reference systems."""

    WGS84 = "EPSG:4326"  # Lat/lon
    WEB_MERCATOR = "EPSG:3857"  # Web maps
    UTM_10N = "EPSG:32610"  # Western US
    UTM_11N = "EPSG:32611"  # Western US
    ALBERS_CONUS = "ESRI:102003"  # Equal-area CONUS


class FuelModel(StrEnum):
    """Standard fuel model classifications (FBFM13/FBFM40 compatible)."""

    GRASS = "grass"
    SHRUB = "shrub"
    TIMBER = "timber"
    SLASH = "slash"
    NON_BURNABLE = "non_burnable"


class BoundingBox(BaseModel):
    """Geospatial bounding box with CRS."""

    min_x: float = Field(..., description="Minimum X coordinate (west/left)")
    max_x: float = Field(..., description="Maximum X coordinate (east/right)")
    min_y: float = Field(..., description="Minimum Y coordinate (south/bottom)")
    max_y: float = Field(..., description="Maximum Y coordinate (north/top)")
    crs: CoordinateSystem = Field(
        default=CoordinateSystem.WGS84, description="Coordinate reference system"
    )

    @field_validator("max_x")
    @classmethod
    def validate_x_bounds(cls, v: float, info) -> float:  # type: ignore[no-untyped-def]
        """Ensure max_x > min_x."""
        if "min_x" in info.data and v <= info.data["min_x"]:
            raise ValueError("max_x must be greater than min_x")
        return v

    @field_validator("max_y")
    @classmethod
    def validate_y_bounds(cls, v: float, info) -> float:  # type: ignore[no-untyped-def]
        """Ensure max_y > min_y."""
        if "min_y" in info.data and v <= info.data["min_y"]:
            raise ValueError("max_y must be greater than min_y")
        return v

    def center(self) -> tuple[float, float]:
        """Return (x, y) center coordinates."""
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    def extent(self) -> tuple[float, float]:
        """Return (width, height) in CRS units."""
        return (self.max_x - self.min_x, self.max_y - self.min_y)


class TerrainData(BaseModel):
    """Digital elevation model and derived terrain attributes."""

    elevation_m: Annotated[
        np.ndarray, Field(..., description="Elevation in meters (H x W)")
    ]
    slope_degrees: Annotated[
        np.ndarray, Field(..., description="Slope angle in degrees (H x W)")
    ]
    aspect_degrees: Annotated[
        np.ndarray, Field(..., description="Aspect in degrees from north (H x W)")
    ]
    resolution_m: Annotated[float, Field(..., gt=0, description="Grid resolution in meters")]
    bbox: BoundingBox

    class Config:  # type: ignore[override]
        """Pydantic config for numpy arrays."""

        arbitrary_types_allowed = True

    @field_validator("elevation_m", "slope_degrees", "aspect_degrees")
    @classmethod
    def validate_grid_shape(cls, v: np.ndarray, info) -> np.ndarray:  # type: ignore[no-untyped-def]
        """Ensure all grids have same shape and 2D."""
        if v.ndim != 2:
            raise ValueError(f"{info.field_name} must be 2D array")
        if "elevation_m" in info.data and v.shape != info.data["elevation_m"].shape:
            raise ValueError(
                f"{info.field_name} shape {v.shape} must match elevation shape {info.data['elevation_m'].shape}"
            )
        return v


class FuelData(BaseModel):
    """Fuel model and moisture content."""

    fuel_model: Annotated[
        np.ndarray, Field(..., description="Fuel type classification (H x W)")
    ]
    fuel_load_kg_m2: Annotated[
        np.ndarray, Field(..., description="Fuel load in kg/m² (H x W)")
    ]
    fuel_moisture_percent: Annotated[
        np.ndarray, Field(..., description="Fuel moisture content percentage (H x W)")
    ]
    resolution_m: Annotated[float, Field(..., gt=0)]

    class Config:  # type: ignore[override]
        """Pydantic config for numpy arrays."""

        arbitrary_types_allowed = True

    @field_validator("fuel_model", "fuel_load_kg_m2", "fuel_moisture_percent")
    @classmethod
    def validate_grid_shape(cls, v: np.ndarray, info) -> np.ndarray:  # type: ignore[no-untyped-def]
        """Ensure consistent shapes."""
        if v.ndim != 2:
            raise ValueError(f"{info.field_name} must be 2D array")
        if "fuel_model" in info.data and v.shape != info.data["fuel_model"].shape:
            raise ValueError("All fuel grids must have same shape")
        return v


class WeatherData(BaseModel):
    """Meteorological conditions."""

    wind_speed_m_s: Annotated[float, Field(..., ge=0, description="Wind speed in m/s")]
    wind_direction_degrees: Annotated[
        float, Field(..., ge=0, lt=360, description="Wind direction (degrees from north)")
    ]
    temperature_c: Annotated[float, Field(..., description="Temperature in Celsius")]
    relative_humidity_percent: Annotated[
        float, Field(..., ge=0, le=100, description="Relative humidity percentage")
    ]
    timestamp: datetime = Field(..., description="Observation/forecast time")


class FireState(BaseModel):
    """Fire perimeter and active burning state at a specific time."""

    burned: Annotated[
        np.ndarray, Field(..., description="Binary burned/not-burned mask (H x W)")
    ]
    active_front: Annotated[
        np.ndarray, Field(..., description="Binary active burning front (H x W)")
    ]
    timestamp: datetime = Field(..., description="State observation time")
    resolution_m: Annotated[float, Field(..., gt=0)]
    bbox: BoundingBox

    class Config:  # type: ignore[override]
        """Pydantic config for numpy arrays."""

        arbitrary_types_allowed = True

    @field_validator("burned", "active_front")
    @classmethod
    def validate_binary_mask(cls, v: np.ndarray, info) -> np.ndarray:  # type: ignore[no-untyped-def]
        """Ensure masks are 2D binary arrays."""
        if v.ndim != 2:
            raise ValueError(f"{info.field_name} must be 2D array")
        if not np.isin(v, [0, 1]).all():
            raise ValueError(f"{info.field_name} must be binary (0 or 1)")
        if "burned" in info.data and v.shape != info.data["burned"].shape:
            raise ValueError("All fire state grids must have same shape")
        return v

    @property
    def burned_area_m2(self) -> float:
        """Calculate burned area in square meters."""
        return float(np.sum(self.burned) * self.resolution_m**2)

    @property
    def active_area_m2(self) -> float:
        """Calculate active burning area in square meters."""
        return float(np.sum(self.active_front) * self.resolution_m**2)
