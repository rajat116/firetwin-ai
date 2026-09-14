"""Tests for FIRMS next-day sample artifact construction."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from firetwin.data.firms_samples import (
    build_firms_next_day_sample_artifact,
    build_firms_next_day_sample_dataset,
    render_firms_next_day_sample_summary_markdown,
)


def write_case(path: Path) -> None:
    """Write a tiny FireCase-like Zarr with real covariate variables."""
    shape = (2, 2)
    ds = xr.Dataset(
        data_vars={
            "elevation_m": (["y", "x"], np.ones(shape, dtype=np.float32)),
            "slope_degrees": (["y", "x"], np.ones(shape, dtype=np.float32) * 5),
            "aspect_degrees": (["y", "x"], np.ones(shape, dtype=np.float32) * 180),
            "fuel_model": (["y", "x"], np.ones(shape, dtype=np.int16) * 101),
            "fuel_load_kg_m2": (["y", "x"], np.ones(shape, dtype=np.float32) * 0.4),
            "fuel_moisture_percent": (["y", "x"], np.ones(shape, dtype=np.float32) * 8),
            "burned": (["time", "y", "x"], np.zeros((2, 2, 2), dtype=np.uint8)),
        },
        coords={"time": pd.to_datetime(["2014-01-01", "2014-01-10"]), "y": [0, 1], "x": [0, 1]},
        attrs={
            "case_id": "sample_test",
            "name": "Sample Test",
            "target_type": "final_burned_extent",
            "resolution_m": 100.0,
            "bbox_crs": "EPSG:32610",
            "bbox_min_x": 0.0,
            "bbox_min_y": 0.0,
            "bbox_max_x": 200.0,
            "bbox_max_y": 200.0,
            "temperature_c": 22.0,
            "relative_humidity_percent": 35.0,
            "wind_speed_m_s": 4.0,
            "wind_direction_degrees": 270.0,
        },
    )
    ds.to_zarr(path, mode="w")


def write_progression(path: Path) -> None:
    """Write sparse daily FIRMS progression labels with a missing calendar day."""
    detection_probability = np.zeros((2, 2, 2), dtype=np.float32)
    detection_probability[0, 0, 0] = 0.6
    detection_probability[1, 1, 1] = 0.9
    positive_mask = (detection_probability > 0).astype(np.uint8)
    detection_count = positive_mask.astype(np.uint16)
    ds = xr.Dataset(
        data_vars={
            "detection_probability": (["time", "y", "x"], detection_probability),
            "positive_observation_mask": (["time", "y", "x"], positive_mask),
            "detection_count": (["time", "y", "x"], detection_count),
        },
        coords={"time": pd.to_datetime(["2014-01-01", "2014-01-03"]), "y": [0, 1], "x": [0, 1]},
        attrs={"target_type": "active_fire_detection_probability"},
    )
    ds.to_zarr(path, mode="w")


def write_initial(path: Path) -> None:
    """Write a tiny FIRMS initial-state artifact."""
    initial_probability = np.zeros((2, 2), dtype=np.float32)
    initial_probability[0, 0] = 0.7
    active_front = (initial_probability > 0).astype(np.uint8)
    ds = xr.Dataset(
        data_vars={
            "initial_burned_probability": (["y", "x"], initial_probability),
            "initial_active_front": (["y", "x"], active_front),
        },
        coords={"y": [0, 1], "x": [0, 1]},
        attrs={
            "target_type": "initial_active_fire_state",
            "uses_final_extent_for_qc": "false",
        },
    )
    ds.to_zarr(path, mode="w")


def test_build_firms_next_day_sample_dataset_reindexes_daily_without_leakage(
    tmp_path: Path,
) -> None:
    """Samples should use a continuous daily calendar and exclude final extent inputs."""
    case_path = tmp_path / "case.zarr"
    progression_path = tmp_path / "progression.zarr"
    initial_path = tmp_path / "initial.zarr"
    write_case(case_path)
    write_progression(progression_path)
    write_initial(initial_path)

    ds = build_firms_next_day_sample_dataset(case_path, progression_path, initial_path)

    assert ds.attrs["sample_type"] == "firms_next_day_active_fire_probability"
    assert ds.attrs["excludes_final_extent_as_input"] == "true"
    assert ds.attrs["positive_unlabeled_semantics"].startswith("zeros_are_no_positive")
    assert "burned" not in ds
    assert ds.sizes["sample"] == 2
    assert pd.Timestamp(ds.coords["reference_time"].values[0]) == pd.Timestamp("2014-01-01")
    assert pd.Timestamp(ds.coords["target_time"].values[0]) == pd.Timestamp("2014-01-02")
    assert int(ds["target_positive_observation_mask"].isel(sample=0).sum().item()) == 0
    assert int(ds["target_positive_observation_mask"].isel(sample=1).sum().item()) == 1
    assert float(
        ds["input_cumulative_detection_probability"].isel(sample=1, y=0, x=0).item()
    ) == pytest.approx(0.6)


def test_build_firms_next_day_sample_artifact_writes_summary(tmp_path: Path) -> None:
    """The artifact builder should save Zarr and render a report summary."""
    case_path = tmp_path / "case.zarr"
    progression_path = tmp_path / "progression.zarr"
    initial_path = tmp_path / "initial.zarr"
    output_path = tmp_path / "samples.zarr"
    write_case(case_path)
    write_progression(progression_path)
    write_initial(initial_path)

    summary = build_firms_next_day_sample_artifact(
        case_path,
        progression_path,
        initial_path,
        output_path,
    )
    markdown = render_firms_next_day_sample_summary_markdown([summary])

    assert output_path.exists()
    assert summary.case_id == "sample_test"
    assert summary.sample_count == 2
    assert summary.target_positive_cell_count == 1
    assert "positive-unlabeled" in markdown
