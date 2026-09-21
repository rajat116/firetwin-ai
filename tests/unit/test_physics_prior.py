"""Tests for Phase 6 physics-prior fields."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from firetwin.models.physics_prior import (
    PHYSICS_PRIOR_NAME,
    build_physics_prior_artifacts,
    build_physics_prior_dataset,
    render_physics_prior_report,
    wind_aware_fuel_spread_prior,
)


def write_sample_artifact(path: Path) -> None:
    """Write a tiny next-day FIRMS sample artifact for physics-prior tests."""
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
            "weather_wind_speed_m_s": (["sample"], np.array([4.0, 8.0], dtype=np.float32)),
            "weather_wind_direction_degrees": (
                ["sample"],
                np.array([270.0, 180.0], dtype=np.float32),
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


def test_wind_aware_fuel_spread_prior_is_aligned_and_bounded(tmp_path: Path) -> None:
    """Physics prior should match the sample tensor and use only burnable cells."""
    sample_path = tmp_path / "samples.zarr"
    write_sample_artifact(sample_path)
    ds = xr.open_zarr(sample_path)
    try:
        prior = wind_aware_fuel_spread_prior(ds)
    finally:
        ds.close()

    assert prior.shape == (2, 2, 2)
    assert prior.dtype == np.float32
    assert float(prior.min()) >= 0.0
    assert float(prior.max()) <= 1.0
    assert np.all(prior[:, 1, 0] == 0.0)
    assert prior[0, 0, 1] > 0.0


def test_build_physics_prior_dataset_preserves_guardrails(tmp_path: Path) -> None:
    """Packaged prior dataset should preserve Phase 6 target semantics."""
    sample_path = tmp_path / "samples.zarr"
    write_sample_artifact(sample_path)
    ds = xr.open_zarr(sample_path)
    try:
        prior = wind_aware_fuel_spread_prior(ds)
        prior_ds = build_physics_prior_dataset(
            sample_ds=ds,
            prior_probability=prior,
            source_sample_path=sample_path,
            threshold=0.5,
        )
    finally:
        ds.close()

    try:
        assert prior_ds["physics_prior_probability"].shape == prior.shape
        assert prior_ds.attrs["prior_source"] == PHYSICS_PRIOR_NAME
        assert prior_ds.attrs["excludes_final_extent_as_input"] == "true"
        assert "next_calendar_day_firms" in prior_ds.attrs["target_semantics"]
    finally:
        prior_ds.close()


def test_build_physics_prior_artifacts_and_report(tmp_path: Path) -> None:
    """Artifact builder should write one zarr prior and a guardrail report."""
    sample_path = tmp_path / "samples.zarr"
    output_dir = tmp_path / "priors"
    write_sample_artifact(sample_path)

    summaries = build_physics_prior_artifacts([sample_path], output_dir=output_dir, threshold=0.5)
    report = render_physics_prior_report(summaries)

    assert len(summaries) == 1
    assert summaries[0].case_id == "baseline_test"
    assert Path(summaries[0].output_path).exists()
    assert "Phase 6" in report
    assert "not an operational spread forecast" in report
