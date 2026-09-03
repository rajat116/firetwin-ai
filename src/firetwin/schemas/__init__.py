"""Data schemas and contracts for FireTwin.

This module defines Pydantic models for all major data structures,
ensuring type safety and validation throughout the pipeline.
"""

from firetwin.schemas.core import (
    BoundingBox,
    CoordinateSystem,
    FireState,
    FuelData,
    TerrainData,
    WeatherData,
)
from firetwin.schemas.fire_case import FireCase, FireCaseMetadata

__all__ = [
    "BoundingBox",
    "CoordinateSystem",
    "FireState",
    "FuelData",
    "TerrainData",
    "WeatherData",
    "FireCase",
    "FireCaseMetadata",
]
