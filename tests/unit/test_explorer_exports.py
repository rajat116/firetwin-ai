"""Tests for Explorer-ready FIRMS forecast exports."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from firetwin.data.explorer_exports import (
    EXPLORER_SCHEMA_VERSION,
    export_firms_next_day_explorer_assets,
    render_explorer_export_report,
    select_peak_forecast_sample,
)


def write_tiny_forecast_artifact(path: Path) -> None:
    """Write a tiny learned forecast artifact for export tests."""
    prediction = np.array(
        [
            [[0.01, 0.02], [0.03, 0.04]],
            [[0.20, 0.30], [0.10, 0.05]],
        ],
        dtype=np.float32,
    )
    target = np.array(
        [
            [[0.0, 0.0], [0.0, 0.0]],
            [[1.0, 0.0], [1.0, 0.0]],
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
            "case_id": "explorer_test",
            "case_name": "Explorer Test Fire",
            "forecast_type": "leave_one_fire_out_next_day_firms_active_fire_probability",
            "excludes_final_extent_as_input": "true",
            "not_hourly_perimeter_truth": "true",
            "persistence_brier_score": 0.02,
            "brier_improvement_vs_persistence": 0.01,
            "grid_crs": "EPSG:32610",
            "resolution_m": 100.0,
            "bbox_min_x": 1.0,
            "bbox_min_y": 2.0,
            "bbox_max_x": 3.0,
            "bbox_max_y": 4.0,
        },
    )
    ds.to_zarr(path, mode="w")


def test_select_peak_forecast_sample() -> None:
    """The Explorer sample should be selected by total forecast probability mass."""
    probability = np.array(
        [
            [[0.1, 0.1], [0.1, 0.1]],
            [[0.5, 0.2], [0.0, 0.0]],
        ],
        dtype=np.float32,
    )

    assert select_peak_forecast_sample(probability) == 1


def test_export_firms_next_day_explorer_assets(tmp_path: Path) -> None:
    """Explorer export should write a manifest, preview PNG and Markdown report."""
    forecast_path = tmp_path / "forecast.zarr"
    manifest_path = tmp_path / "data" / "manifests" / "explorer.json"
    figure_dir = tmp_path / "reports" / "figures"
    report_path = tmp_path / "reports" / "explorer.md"
    write_tiny_forecast_artifact(forecast_path)

    exports = export_firms_next_day_explorer_assets(
        forecast_paths=[forecast_path],
        manifest_path=manifest_path,
        figure_dir=figure_dir,
        report_path=report_path,
    )
    report = render_explorer_export_report(exports, manifest_path=manifest_path)
    manifest_text = manifest_path.read_text(encoding="utf-8")

    assert len(exports) == 1
    assert exports[0].case_id == "explorer_test"
    assert exports[0].sample_index == 1
    assert exports[0].persistence_brier_score == 0.02
    assert exports[0].brier_improvement_vs_persistence == 0.01
    assert exports[0].reference_time == "2014-01-02T00:00:00"
    assert exports[0].grid_shape == {"height": 2, "width": 2}
    assert exports[0].wgs84_bbox["west"] < exports[0].wgs84_bbox["east"]
    assert exports[0].wgs84_bbox["south"] < exports[0].wgs84_bbox["north"]
    assert -180.0 <= exports[0].center_lon_lat["lon"] <= 180.0
    assert -90.0 <= exports[0].center_lon_lat["lat"] <= 90.0
    assert Path(exports[0].preview_png).exists()
    assert manifest_path.exists()
    assert report_path.exists()
    assert EXPLORER_SCHEMA_VERSION in manifest_text
    assert "not for operational wildfire response" in manifest_text
    assert "Explorer-ready" in report
