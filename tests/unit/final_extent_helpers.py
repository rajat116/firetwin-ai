"""Shared test helpers for final-extent cases."""

from datetime import datetime, timedelta

import numpy as np

from firetwin.schemas import (
    BoundingBox,
    CoordinateSystem,
    FireCase,
    FireCaseMetadata,
    FireState,
    FuelData,
    TerrainData,
    WeatherData,
)


def make_final_extent_case(target_type: str = "final_burned_extent") -> FireCase:
    """Create a small final-extent case for deterministic tests."""
    bbox = BoundingBox(
        min_x=0.0,
        max_x=400.0,
        min_y=0.0,
        max_y=400.0,
        crs=CoordinateSystem.UTM_10N,
    )
    target = np.zeros((4, 4), dtype=np.int32)
    target[1:3, 1:3] = 1

    return FireCase(
        metadata=FireCaseMetadata(
            case_id="final_test",
            name="Final Test",
            is_synthetic=False,
            source="unit_test",
            target_type=target_type,
            covariate_status="partial_real_terrain_fuels_weather",
        ),
        terrain=TerrainData(
            elevation_m=np.arange(16, dtype=np.float32).reshape(4, 4),
            slope_degrees=np.full((4, 4), 10.0, dtype=np.float32),
            aspect_degrees=np.full((4, 4), 180.0, dtype=np.float32),
            resolution_m=100.0,
            bbox=bbox,
        ),
        fuels=FuelData(
            fuel_model=np.array(
                [
                    [0, 101, 101, 0],
                    [101, 102, 102, 101],
                    [101, 102, 102, 101],
                    [0, 101, 101, 0],
                ],
                dtype=np.int32,
            ),
            fuel_load_kg_m2=np.array(
                [
                    [0.0, 0.2, 0.2, 0.0],
                    [0.2, 1.0, 1.0, 0.2],
                    [0.2, 1.0, 1.0, 0.2],
                    [0.0, 0.2, 0.2, 0.0],
                ],
                dtype=np.float32,
            ),
            fuel_moisture_percent=np.full((4, 4), 10.0, dtype=np.float32),
            resolution_m=100.0,
        ),
        weather=WeatherData(
            temperature_c=25.0,
            relative_humidity_percent=30.0,
            wind_speed_m_s=1.0,
            wind_direction_degrees=270.0,
            timestamp=datetime(2014, 1, 1),
        ),
        initial_state=FireState(
            burned=np.zeros((4, 4), dtype=np.int32),
            active_front=np.zeros((4, 4), dtype=np.int32),
            timestamp=datetime(2014, 1, 1),
            resolution_m=100.0,
            bbox=bbox,
        ),
        target_states=[
            FireState(
                burned=target,
                active_front=target,
                timestamp=datetime(2014, 1, 1) + timedelta(days=10),
                resolution_m=100.0,
                bbox=bbox,
            )
        ],
    )
