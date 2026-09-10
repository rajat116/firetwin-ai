"""Tests for Phase 3 fire-case validation."""

import importlib.util
from datetime import datetime
from pathlib import Path

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

VALIDATOR_PATH = Path(__file__).resolve().parents[2] / "scripts" / "validate_fire_cases.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_fire_cases", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
assert VALIDATOR_SPEC.loader is not None
validator_module = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(validator_module)
validate_fire_case = validator_module.validate_fire_case


def test_validate_fire_case_computes_known_final_extent_area(tmp_path):
    """Validator should check the actual Zarr fire-state layout and acreage."""
    resolution_m = 100.0
    burned = np.zeros((3, 3), dtype=np.uint8)
    burned[0, 0] = 1
    burned[1, 1] = 1
    expected_acres = 2 * resolution_m**2 / 4046.86

    bbox = BoundingBox(
        min_x=0.0,
        max_x=300.0,
        min_y=0.0,
        max_y=300.0,
        crs=CoordinateSystem.UTM_10N,
    )
    fire_case = FireCase(
        metadata=FireCaseMetadata(
            case_id="known_area",
            name="Known Area",
            is_synthetic=False,
            source="test",
            tags=["final_extent_only", "placeholder_covariates"],
            target_type="final_burned_extent",
            data_quality="test",
            covariate_status="placeholder",
            limitations=["Target state is final burned extent, not progression."],
            covariate_sources={
                "terrain": "placeholder_flat_1000m",
                "fuels": "placeholder_uniform_fbfm_10",
                "weather": "placeholder_scalar_moderate_conditions",
            },
        ),
        terrain=TerrainData(
            elevation_m=np.full((3, 3), 1000.0, dtype=np.float32),
            slope_degrees=np.zeros((3, 3), dtype=np.float32),
            aspect_degrees=np.zeros((3, 3), dtype=np.float32),
            resolution_m=resolution_m,
            bbox=bbox,
        ),
        fuels=FuelData(
            fuel_model=np.full((3, 3), 10, dtype=np.int32),
            fuel_load_kg_m2=np.full((3, 3), 2.0, dtype=np.float32),
            fuel_moisture_percent=np.full((3, 3), 8.0, dtype=np.float32),
            resolution_m=resolution_m,
        ),
        weather=WeatherData(
            temperature_c=25.0,
            relative_humidity_percent=30.0,
            wind_speed_m_s=5.0,
            wind_direction_degrees=270.0,
            timestamp=datetime(2014, 7, 1),
        ),
        initial_state=FireState(
            burned=np.zeros((3, 3), dtype=np.uint8),
            active_front=np.zeros((3, 3), dtype=np.uint8),
            timestamp=datetime(2014, 1, 1),
            resolution_m=resolution_m,
            bbox=bbox,
        ),
        target_states=[
            FireState(
                burned=burned,
                active_front=np.zeros((3, 3), dtype=np.uint8),
                timestamp=datetime(2014, 12, 31),
                resolution_m=resolution_m,
                bbox=bbox,
            )
        ],
    )
    zarr_path = tmp_path / "known_area.zarr"
    fire_case.save_to_zarr(zarr_path)
    loaded = FireCase.load_from_zarr(zarr_path)

    results = validate_fire_case(zarr_path, expected_acres, "EPSG:32610")

    assert loaded.metadata.covariate_sources["terrain"] == "placeholder_flat_1000m"
    assert not results["failed"]
    assert results["burned_pixels"] == 2
    assert results["burned_area_acres"] == expected_acres


def test_validate_fire_case_accepts_real_weather_gate(tmp_path):
    """Validator should accept Phase 4C metadata with ERA5 weather provenance."""
    resolution_m = 100.0
    burned = np.ones((3, 3), dtype=np.uint8)
    expected_acres = 9 * resolution_m**2 / 4046.86

    bbox = BoundingBox(
        min_x=0.0,
        max_x=300.0,
        min_y=0.0,
        max_y=300.0,
        crs=CoordinateSystem.UTM_10N,
    )
    fire_case = FireCase(
        metadata=FireCaseMetadata(
            case_id="real_weather",
            name="Real Weather",
            is_synthetic=False,
            source="NIFC/MTBS/USGS 3DEP/LANDFIRE/ERA5-Land",
            tags=["final_extent_only", "real_terrain", "real_fbfm40", "real_weather"],
            target_type="final_burned_extent",
            data_quality="phase4c_real_terrain_fuels_weather_final_extent",
            covariate_status="partial_real_terrain_fuels_weather",
            limitations=["Target state is final burned extent, not progression."],
            covariate_sources={
                "terrain": "USGS 3DEP National Elevation Dataset",
                "fuel_model": "LANDFIRE LF2022 FBFM40 CONUS ImageServer",
                "fuel_load_kg_m2": "derived_proxy_from_landfire_fbfm40_class",
                "fuel_moisture_percent": "static_proxy_from_landfire_fbfm40_class",
                "weather": "ERA5-Land hourly reanalysis via Copernicus Climate Data Store",
            },
        ),
        terrain=TerrainData(
            elevation_m=np.arange(9, dtype=np.float32).reshape(3, 3) + 1000.0,
            slope_degrees=np.ones((3, 3), dtype=np.float32),
            aspect_degrees=np.zeros((3, 3), dtype=np.float32),
            resolution_m=resolution_m,
            bbox=bbox,
        ),
        fuels=FuelData(
            fuel_model=np.array(
                [
                    [0, 101, 102],
                    [121, 141, 161],
                    [181, 182, 202],
                ],
                dtype=np.int32,
            ),
            fuel_load_kg_m2=np.array(
                [
                    [0.0, 0.25, 0.33],
                    [0.75, 1.0, 1.35],
                    [1.6, 1.78, 2.55],
                ],
                dtype=np.float32,
            ),
            fuel_moisture_percent=np.array(
                [
                    [0.0, 6.0, 6.0],
                    [7.0, 8.0, 9.0],
                    [10.0, 10.0, 8.0],
                ],
                dtype=np.float32,
            ),
            resolution_m=resolution_m,
        ),
        weather=WeatherData(
            temperature_c=22.0,
            relative_humidity_percent=45.0,
            wind_speed_m_s=3.0,
            wind_direction_degrees=180.0,
            timestamp=datetime(2014, 7, 14, 12),
        ),
        initial_state=FireState(
            burned=np.zeros((3, 3), dtype=np.uint8),
            active_front=np.zeros((3, 3), dtype=np.uint8),
            timestamp=datetime(2014, 7, 14, 12),
            resolution_m=resolution_m,
            bbox=bbox,
        ),
        target_states=[
            FireState(
                burned=burned,
                active_front=np.zeros((3, 3), dtype=np.uint8),
                timestamp=datetime(2014, 8, 1),
                resolution_m=resolution_m,
                bbox=bbox,
            )
        ],
    )
    zarr_path = tmp_path / "real_weather.zarr"
    fire_case.save_to_zarr(zarr_path)

    results = validate_fire_case(
        zarr_path,
        expected_acres,
        "EPSG:32610",
        require_real_terrain=True,
        require_real_fuels=True,
        require_real_weather=True,
    )

    assert not results["failed"]
