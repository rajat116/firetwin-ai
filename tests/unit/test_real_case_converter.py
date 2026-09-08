"""Tests for real fire case conversion semantics."""

import numpy as np

from firetwin.data.converter import PLACEHOLDER_COVARIATE_LIMITATIONS, RealFireCaseConverter
from firetwin.schemas import CoordinateSystem


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
    assert fire_case.metadata.limitations == PLACEHOLDER_COVARIATE_LIMITATIONS
