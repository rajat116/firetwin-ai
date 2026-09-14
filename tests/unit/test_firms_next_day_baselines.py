"""Tests for next-day FIRMS baseline evaluation."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from firetwin.evaluation.firms_next_day import (
    evaluate_firms_next_day_baselines,
    evaluate_firms_next_day_prediction,
    fuel_terrain_prior,
    render_firms_next_day_baseline_report,
)


def write_sample_artifact(path: Path) -> None:
    """Write a tiny next-day FIRMS sample artifact."""
    input_detection = np.zeros((2, 2, 2), dtype=np.float32)
    input_detection[0, 0, 0] = 0.8
    input_detection[1, 0, 1] = 0.6
    cumulative = np.maximum.accumulate(input_detection, axis=0)

    target_probability = np.zeros((2, 2, 2), dtype=np.float32)
    target_probability[0, 0, 0] = 0.7
    target_probability[1, 1, 1] = 0.9
    target_mask = (target_probability > 0).astype(np.uint8)

    ds = xr.Dataset(
        data_vars={
            "fuel_model": (["y", "x"], np.array([[101, 101], [0, 102]], dtype=np.int16)),
            "fuel_load_kg_m2": (
                ["y", "x"],
                np.array([[0.3, 0.8], [0.0, 1.2]], dtype=np.float32),
            ),
            "fuel_moisture_percent": (
                ["y", "x"],
                np.array([[8.0, 6.0], [0.0, 5.0]], dtype=np.float32),
            ),
            "slope_degrees": (
                ["y", "x"],
                np.array([[5.0, 10.0], [0.0, 20.0]], dtype=np.float32),
            ),
            "input_detection_probability": (["sample", "y", "x"], input_detection),
            "input_cumulative_detection_probability": (["sample", "y", "x"], cumulative),
            "target_detection_probability": (["sample", "y", "x"], target_probability),
            "target_positive_observation_mask": (["sample", "y", "x"], target_mask),
        },
        coords={
            "sample": [0, 1],
            "reference_time": (["sample"], pd.to_datetime(["2014-01-01", "2014-01-02"])),
            "target_time": (["sample"], pd.to_datetime(["2014-01-02", "2014-01-03"])),
            "y": [0, 1],
            "x": [0, 1],
        },
        attrs={
            "case_id": "baseline_test",
            "sample_type": "firms_next_day_active_fire_probability",
            "excludes_final_extent_as_input": "true",
        },
    )
    ds.to_zarr(path, mode="w")


def test_evaluate_firms_next_day_prediction_metrics() -> None:
    """Metric helper should compute threshold diagnostics against positive observations."""
    prediction = np.array([0.8, 0.2, 0.7, 0.1], dtype=np.float32)
    target_probability = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    target_mask = target_probability > 0

    metrics = evaluate_firms_next_day_prediction(
        prediction,
        target_probability,
        target_mask,
        threshold=0.5,
    )

    assert metrics["predicted_positive_cell_count"] == 2
    assert metrics["target_positive_cell_count"] == 1
    assert metrics["precision_at_threshold"] == 0.5
    assert metrics["recall_at_threshold"] == 1.0
    assert metrics["mean_prediction_on_target_positive"] == pytest.approx(0.8)


def test_fuel_terrain_prior_uses_static_covariates(tmp_path: Path) -> None:
    """Fuel/terrain prior should be burnable-only and bounded."""
    sample_path = tmp_path / "samples.zarr"
    write_sample_artifact(sample_path)
    ds = xr.open_zarr(sample_path)
    try:
        prior = fuel_terrain_prior(ds)
    finally:
        ds.close()

    assert prior.shape == (2, 2)
    assert float(prior.min()) >= 0.0
    assert float(prior.max()) <= 1.0
    assert prior[1, 0] == 0.0
    assert prior[1, 1] > prior[0, 0]


def test_evaluate_firms_next_day_baselines_and_report(tmp_path: Path) -> None:
    """Baseline evaluator should return all expected baselines and report guardrails."""
    sample_path = tmp_path / "samples.zarr"
    write_sample_artifact(sample_path)

    results = evaluate_firms_next_day_baselines(sample_path, threshold=0.5)
    report = render_firms_next_day_baseline_report(results)

    assert {result.baseline for result in results} == {
        "persistence",
        "cumulative_history",
        "fuel_terrain_prior",
    }
    assert all(result.case_id == "baseline_test" for result in results)
    assert all(result.sample_count == 2 for result in results)
    assert "positive-unlabeled" in report
