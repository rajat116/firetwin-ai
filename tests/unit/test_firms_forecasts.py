"""Tests for learned FIRMS forecast calibration diagnostics."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from firetwin.evaluation.firms_forecasts import (
    evaluate_forecast_artifact,
    reliability_bins_for_forecast,
    render_forecast_calibration_report,
    threshold_diagnostics_for_forecast,
)


def write_forecast_artifact(path: Path) -> None:
    """Write a tiny learned forecast artifact."""
    prediction = np.array(
        [
            [[0.02, 0.08], [0.20, 0.60]],
            [[0.01, 0.06], [0.12, 0.70]],
        ],
        dtype=np.float32,
    )
    target = np.array(
        [
            [[0.0, 0.0], [0.0, 1.0]],
            [[0.0, 0.0], [1.0, 1.0]],
        ],
        dtype=np.float32,
    )
    ds = xr.Dataset(
        data_vars={
            "forecast_probability": (["sample", "y", "x"], prediction),
            "forecast_positive_mask": (["sample", "y", "x"], (prediction >= 0.05).astype(np.uint8)),
            "target_detection_probability": (["sample", "y", "x"], target),
            "target_positive_observation_mask": (
                ["sample", "y", "x"],
                (target > 0).astype(np.uint8),
            ),
            "input_detection_probability": (["sample", "y", "x"], np.zeros_like(prediction)),
            "input_cumulative_detection_probability": (
                ["sample", "y", "x"],
                np.zeros_like(prediction),
            ),
        },
        coords={
            "sample": [0, 1],
            "reference_time": (["sample"], pd.to_datetime(["2014-01-01", "2014-01-02"])),
            "target_time": (["sample"], pd.to_datetime(["2014-01-02", "2014-01-03"])),
            "lead_time_hours": (["sample"], np.full(2, 24.0, dtype=np.float32)),
            "y": [0, 1],
            "x": [0, 1],
        },
        attrs={
            "case_id": "forecast_test",
            "forecast_type": "leave_one_fire_out_next_day_firms_active_fire_probability",
            "excludes_final_extent_as_input": "true",
            "not_hourly_perimeter_truth": "true",
        },
    )
    ds.to_zarr(path, mode="w")


def test_reliability_bins_and_threshold_diagnostics() -> None:
    """Calibration and threshold helpers should compute bounded diagnostics."""
    prediction = np.array([0.01, 0.05, 0.20, 0.70], dtype=np.float32)
    target = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32)

    bins = reliability_bins_for_forecast(
        case_id="toy",
        prediction=prediction,
        target_probability=target,
        bin_count=5,
    )
    thresholds = threshold_diagnostics_for_forecast(
        case_id="toy",
        prediction=prediction,
        target_positive_mask=target > 0,
        thresholds=(0.05, 0.20),
    )

    assert len(bins) == 5
    assert sum(bin_result.cell_count for bin_result in bins) == 4
    assert thresholds[0].recall == 1.0
    assert thresholds[1].precision == 1.0


def test_evaluate_forecast_artifact_and_report(tmp_path: Path) -> None:
    """Forecast artifact evaluation should return reportable calibration diagnostics."""
    forecast_path = tmp_path / "forecast.zarr"
    write_forecast_artifact(forecast_path)

    diagnostic = evaluate_forecast_artifact(
        forecast_path,
        thresholds=(0.05, 0.20, 0.50),
        bin_count=5,
    )
    report = render_forecast_calibration_report([diagnostic])

    assert diagnostic.summary.case_id == "forecast_test"
    assert diagnostic.summary.expected_calibration_error >= 0.0
    assert diagnostic.summary.recommended_threshold in {0.05, 0.20, 0.50}
    assert "Recommended threshold" in report
    assert "positive-observation evidence" in report
