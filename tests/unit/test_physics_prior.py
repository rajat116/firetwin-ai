"""Tests for Phase 6 physics-prior fields."""

from pathlib import Path

import numpy as np
import xarray as xr
from tests.unit.test_firms_next_day_baselines import write_sample_artifact

from firetwin.models.physics_prior import (
    PHYSICS_PRIOR_NAME,
    build_physics_prior_artifacts,
    build_physics_prior_dataset,
    render_physics_prior_report,
    wind_aware_fuel_spread_prior,
)


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
