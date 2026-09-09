"""Tests for real fire case conversion semantics."""

import numpy as np

from firetwin.data.converter import (
    PLACEHOLDER_COVARIATE_LIMITATIONS,
    REAL_TERRAIN_LIMITATIONS,
    RealFireCaseConverter,
)
from firetwin.schemas import BoundingBox, CoordinateSystem, TerrainData


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
