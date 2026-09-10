"""Tests for final-extent baseline evaluation."""

import numpy as np
import pytest
from final_extent_helpers import make_final_extent_case

from firetwin.evaluation import evaluate_final_extent_baselines, fuel_potential_mask


def test_fuel_potential_mask_uses_covariates_not_target_area() -> None:
    """Fuel-potential mask should identify high-potential burnable cells."""
    case = make_final_extent_case()

    mask = fuel_potential_mask(case, quantile=0.70)

    assert mask.dtype == bool
    assert int(mask.sum()) == 4
    np.testing.assert_array_equal(mask.astype(np.int32), case.target_states[-1].burned)


def test_evaluate_final_extent_baselines_reports_non_temporal_results() -> None:
    """Final-extent baselines should produce metrics without forecast horizons."""
    case = make_final_extent_case()

    results = evaluate_final_extent_baselines(case)

    names = {result["baseline"] for result in results}
    assert names == {"initial_state", "burnable_fuel_mask", "top_fuel_potential_30pct"}
    assert all(result["target_type"] == "final_burned_extent" for result in results)
    assert all(result["uses_target_area"] is False for result in results)
    assert all("forecast_horizon_h" not in result for result in results)

    fuel_result = next(
        result for result in results if result["baseline"] == "top_fuel_potential_30pct"
    )
    assert fuel_result["iou"] == pytest.approx(1.0)
    assert fuel_result["relative_area_error"] == pytest.approx(0.0)


def test_evaluate_final_extent_baselines_rejects_non_final_extent_case() -> None:
    """Final-extent evaluator should reject time-resolved forecast cases."""
    case = make_final_extent_case(target_type="forecast_progression")

    with pytest.raises(ValueError, match="target_type=final_burned_extent"):
        evaluate_final_extent_baselines(case)
