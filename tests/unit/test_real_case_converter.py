"""Tests for real fire case conversion semantics."""

from datetime import datetime
from unittest.mock import patch

import numpy as np

from firetwin.data.converter import (
    PLACEHOLDER_COVARIATE_LIMITATIONS,
    REAL_FUELS_LIMITATIONS,
    REAL_TERRAIN_FUELS_LIMITATIONS,
    REAL_TERRAIN_FUELS_WEATHER_LIMITATIONS,
    REAL_TERRAIN_LIMITATIONS,
    RealFireCaseConverter,
)
from firetwin.schemas import BoundingBox, CoordinateSystem, FuelData, TerrainData, WeatherData


def test_real_case_converter_does_not_create_era5_client_until_fetch():
    """Constructing a converter for schema work should not initialize external weather clients."""
    with patch("firetwin.data.converter.ERA5LandClient") as era5_client:
        converter = RealFireCaseConverter(
            fire_name="KING",
            fire_year=2014,
            bbox=(-121.5, 38.5, -120.0, 39.5),
            target_resolution_m=100.0,
            target_crs="EPSG:32610",
        )

    assert converter.era5 is None
    era5_client.assert_not_called()


def test_real_case_converter_preserves_target_crs_and_limitations():
    """Real final-extent cases should carry CRS and limitation metadata."""
    converter = RealFireCaseConverter(
        fire_name="Big Cougar",
        fire_year=2014,
        bbox=(-117.5, 45.4, -116.2, 46.6),
        target_resolution_m=100.0,
        target_crs="EPSG:32611",
    )
    converter.aligned_data = {
        "grid_shape": (4, 5),
        "grid_bounds": (500000.0, 5000000.0, 500500.0, 5000400.0),
        "burned_mask": np.ones((4, 5), dtype=np.uint8),
    }

    fire_case = converter.build_fire_case()

    assert fire_case is not None
    assert fire_case.terrain.bbox.crs == CoordinateSystem.UTM_11N
    assert fire_case.metadata.target_type == "final_burned_extent"
    assert fire_case.metadata.covariate_status == "placeholder"
    assert "final_extent_only" in fire_case.metadata.tags
    assert "placeholder_covariates" in fire_case.metadata.tags
    assert fire_case.metadata.limitations == PLACEHOLDER_COVARIATE_LIMITATIONS
    assert fire_case.metadata.covariate_sources["terrain"] == "placeholder_flat_1000m"


def test_real_case_converter_uses_real_terrain_when_aligned():
    """Aligned USGS terrain should replace placeholder terrain and update metadata."""
    converter = RealFireCaseConverter(
        fire_name="KING",
        fire_year=2014,
        bbox=(-121.5, 38.5, -120.0, 39.5),
        target_resolution_m=100.0,
        target_crs="EPSG:32610",
    )
    terrain = TerrainData(
        elevation_m=np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0,
        slope_degrees=np.full((4, 5), 12.0, dtype=np.float32),
        aspect_degrees=np.full((4, 5), 180.0, dtype=np.float32),
        resolution_m=100.0,
        bbox=BoundingBox(
            min_x=500000.0,
            max_x=500500.0,
            min_y=5000000.0,
            max_y=5000400.0,
            crs=CoordinateSystem.UTM_10N,
        ),
    )
    converter.aligned_data = {
        "grid_shape": (4, 5),
        "grid_bounds": (500000.0, 5000000.0, 500500.0, 5000400.0),
        "burned_mask": np.ones((4, 5), dtype=np.uint8),
        "terrain": terrain,
    }

    fire_case = converter.build_fire_case()

    assert fire_case is not None
    assert fire_case.terrain is terrain
    assert fire_case.metadata.source == "NIFC/MTBS/USGS 3DEP"
    assert fire_case.metadata.covariate_status == "partial_real_terrain"
    assert fire_case.metadata.data_quality == "phase4a_real_terrain_final_extent"
    assert "real_terrain" in fire_case.metadata.tags
    assert "placeholder_covariates" not in fire_case.metadata.tags
    assert fire_case.metadata.limitations == REAL_TERRAIN_LIMITATIONS
    assert "USGS 3DEP" in fire_case.metadata.covariate_sources["terrain"]
    assert fire_case.metadata.covariate_sources["fuels"] == "placeholder_uniform_fbfm_10"


def test_real_case_converter_uses_real_fuels_when_aligned():
    """Aligned LANDFIRE fuels should replace placeholder fuels and update metadata."""
    converter = RealFireCaseConverter(
        fire_name="KING",
        fire_year=2014,
        bbox=(-121.5, 38.5, -120.0, 39.5),
        target_resolution_m=100.0,
        target_crs="EPSG:32610",
    )
    terrain = TerrainData(
        elevation_m=np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0,
        slope_degrees=np.full((4, 5), 12.0, dtype=np.float32),
        aspect_degrees=np.full((4, 5), 180.0, dtype=np.float32),
        resolution_m=100.0,
        bbox=BoundingBox(
            min_x=500000.0,
            max_x=500500.0,
            min_y=5000000.0,
            max_y=5000400.0,
            crs=CoordinateSystem.UTM_10N,
        ),
    )
    fuels = FuelData(
        fuel_model=np.array(
            [
                [0, 101, 102, 141, 142],
                [101, 121, 122, 181, 202],
                [141, 142, 161, 181, 202],
                [0, 101, 141, 181, 202],
            ],
            dtype=np.int32,
        ),
        fuel_load_kg_m2=np.ones((4, 5), dtype=np.float32),
        fuel_moisture_percent=np.full((4, 5), 8.0, dtype=np.float32),
        resolution_m=100.0,
    )
    converter.aligned_data = {
        "grid_shape": (4, 5),
        "grid_bounds": (500000.0, 5000000.0, 500500.0, 5000400.0),
        "burned_mask": np.ones((4, 5), dtype=np.uint8),
        "terrain": terrain,
        "fuels": fuels,
    }

    fire_case = converter.build_fire_case()

    assert fire_case is not None
    assert fire_case.fuels is fuels
    assert fire_case.metadata.source == "NIFC/MTBS/USGS 3DEP/LANDFIRE"
    assert fire_case.metadata.covariate_status == "partial_real_terrain_fuels"
    assert fire_case.metadata.data_quality == "phase4b_real_terrain_fuels_final_extent"
    assert "real_terrain" in fire_case.metadata.tags
    assert "real_fbfm40" in fire_case.metadata.tags
    assert "placeholder_fuels" not in fire_case.metadata.tags
    assert fire_case.metadata.limitations == REAL_TERRAIN_FUELS_LIMITATIONS
    assert "LANDFIRE LF2022 FBFM40" in fire_case.metadata.covariate_sources["fuel_model"]
    assert (
        fire_case.metadata.covariate_sources["fuel_load_kg_m2"]
        == "derived_proxy_from_landfire_fbfm40_class"
    )


def test_real_case_converter_marks_fuel_only_fallback_honestly():
    """Real fuels without real terrain should not be mislabeled as all-placeholder."""
    converter = RealFireCaseConverter(
        fire_name="KING",
        fire_year=2014,
        bbox=(-121.5, 38.5, -120.0, 39.5),
        target_resolution_m=100.0,
        target_crs="EPSG:32610",
    )
    fuels = FuelData(
        fuel_model=np.full((4, 5), 101, dtype=np.int32),
        fuel_load_kg_m2=np.full((4, 5), 0.25, dtype=np.float32),
        fuel_moisture_percent=np.full((4, 5), 6.0, dtype=np.float32),
        resolution_m=100.0,
    )
    converter.aligned_data = {
        "grid_shape": (4, 5),
        "grid_bounds": (500000.0, 5000000.0, 500500.0, 5000400.0),
        "burned_mask": np.ones((4, 5), dtype=np.uint8),
        "fuels": fuels,
    }

    fire_case = converter.build_fire_case()

    assert fire_case is not None
    assert fire_case.metadata.covariate_status == "partial_real_fuels"
    assert fire_case.metadata.source == "NIFC/MTBS/LANDFIRE"
    assert "placeholder_terrain" in fire_case.metadata.tags
    assert "real_fbfm40" in fire_case.metadata.tags
    assert fire_case.metadata.limitations == REAL_FUELS_LIMITATIONS
    assert fire_case.metadata.covariate_sources["terrain"] == "placeholder_flat_1000m"
    assert "LANDFIRE LF2022 FBFM40" in fire_case.metadata.covariate_sources["fuel_model"]


def test_real_case_converter_uses_real_weather_when_aligned():
    """Aligned ERA5 weather should replace placeholder weather and update metadata."""
    converter = RealFireCaseConverter(
        fire_name="KING",
        fire_year=2014,
        bbox=(-121.5, 38.5, -120.0, 39.5),
        target_resolution_m=100.0,
        target_crs="EPSG:32610",
    )
    bbox = BoundingBox(
        min_x=500000.0,
        max_x=500500.0,
        min_y=5000000.0,
        max_y=5000400.0,
        crs=CoordinateSystem.UTM_10N,
    )
    terrain = TerrainData(
        elevation_m=np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0,
        slope_degrees=np.full((4, 5), 12.0, dtype=np.float32),
        aspect_degrees=np.full((4, 5), 180.0, dtype=np.float32),
        resolution_m=100.0,
        bbox=bbox,
    )
    fuels = FuelData(
        fuel_model=np.full((4, 5), 101, dtype=np.int32),
        fuel_load_kg_m2=np.full((4, 5), 0.25, dtype=np.float32),
        fuel_moisture_percent=np.full((4, 5), 6.0, dtype=np.float32),
        resolution_m=100.0,
    )
    weather = WeatherData(
        temperature_c=27.0,
        relative_humidity_percent=20.0,
        wind_speed_m_s=6.0,
        wind_direction_degrees=225.0,
        timestamp=datetime(2014, 9, 13, 23),
    )
    converter.aligned_data = {
        "grid_shape": (4, 5),
        "grid_bounds": (500000.0, 5000000.0, 500500.0, 5000400.0),
        "burned_mask": np.ones((4, 5), dtype=np.uint8),
        "terrain": terrain,
        "fuels": fuels,
        "weather": weather,
    }

    fire_case = converter.build_fire_case()

    assert fire_case is not None
    assert fire_case.weather is weather
    assert fire_case.metadata.source == "NIFC/MTBS/USGS 3DEP/LANDFIRE/ERA5-Land"
    assert fire_case.metadata.covariate_status == "partial_real_terrain_fuels_weather"
    assert fire_case.metadata.data_quality == "phase4c_real_terrain_fuels_weather_final_extent"
    assert "real_weather" in fire_case.metadata.tags
    assert "placeholder_weather" not in fire_case.metadata.tags
    assert fire_case.metadata.limitations == REAL_TERRAIN_FUELS_WEATHER_LIMITATIONS
    assert "ERA5-Land hourly reanalysis" in fire_case.metadata.covariate_sources["weather"]
