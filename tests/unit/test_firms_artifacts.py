"""Tests for FIRMS artifact validation diagnostics."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from firetwin.evaluation.firms_artifacts import (
    render_firms_artifact_validation_markdown,
    validate_firms_artifacts,
)


def write_case(path: Path) -> None:
    """Write a tiny final-extent FireCase-like dataset."""
    burned = np.zeros((2, 2, 3), dtype=np.uint8)
    burned[-1, 0, 0] = 1
    burned[-1, 0, 1] = 1
    burned[-1, 1, 1] = 1
    ds = xr.Dataset(
        data_vars={"burned": (["time", "y", "x"], burned)},
        coords={
            "time": pd.to_datetime(["2014-01-01", "2014-01-02"]),
            "y": [0, 1],
            "x": [0, 1, 2],
        },
        attrs={
            "case_id": "validation_test",
            "target_type": "final_burned_extent",
        },
    )
    ds.to_zarr(path, mode="w")


def write_progression(path: Path) -> None:
    """Write a tiny FIRMS progression artifact."""
    cumulative = np.zeros((1, 2, 3), dtype=np.float32)
    cumulative[0, 0, 0] = 0.6
    cumulative[0, 1, 2] = 0.9
    ds = xr.Dataset(
        data_vars={"cumulative_detection_probability": (["time", "y", "x"], cumulative)},
        coords={"time": pd.to_datetime(["2014-01-01"]), "y": [0, 1], "x": [0, 1, 2]},
        attrs={"target_type": "active_fire_detection_probability"},
    )
    ds.to_zarr(path, mode="w")


def write_initial(path: Path) -> None:
    """Write a tiny FIRMS initial-state artifact."""
    active = np.zeros((2, 3), dtype=np.uint8)
    active[0, 1] = 1
    active[1, 2] = 1
    ds = xr.Dataset(
        data_vars={"initial_active_front": (["y", "x"], active)},
        coords={"y": [0, 1], "x": [0, 1, 2]},
        attrs={
            "target_type": "initial_active_fire_state",
            "uses_final_extent_for_qc": "false",
            "window_detection_count": 2,
        },
    )
    ds.to_zarr(path, mode="w")


def test_validate_firms_artifacts_computes_context_overlap(tmp_path: Path) -> None:
    """Overlap diagnostics should compare FIRMS evidence to final extent without relabeling it."""
    case_path = tmp_path / "case.zarr"
    progression_path = tmp_path / "progression.zarr"
    initial_path = tmp_path / "initial.zarr"
    figure_path = tmp_path / "overlay.png"
    write_case(case_path)
    write_progression(progression_path)
    write_initial(initial_path)

    summary = validate_firms_artifacts(
        case_path=case_path,
        progression_path=progression_path,
        initial_state_path=initial_path,
        figure_path=figure_path,
    )

    assert summary.case_id == "validation_test"
    assert summary.final_burned_cells == 3
    assert summary.progression_positive_cells == 2
    assert summary.progression_overlap_cells == 1
    assert summary.progression_outside_final_cells == 1
    assert summary.progression_precision_vs_final == 0.5
    assert summary.progression_recall_vs_final == 1 / 3
    assert summary.initial_active_cells == 2
    assert summary.initial_overlap_cells == 1
    assert summary.initial_window_detection_count == 2
    assert figure_path.exists()


def test_render_firms_artifact_validation_markdown(tmp_path: Path) -> None:
    """The validation report should record semantics and links."""
    case_path = tmp_path / "case.zarr"
    progression_path = tmp_path / "progression.zarr"
    initial_path = tmp_path / "initial.zarr"
    write_case(case_path)
    write_progression(progression_path)
    write_initial(initial_path)

    summary = validate_firms_artifacts(case_path, progression_path, initial_path)
    markdown = render_firms_artifact_validation_markdown([summary])

    assert "FireTwin FIRMS Artifact Validation" in markdown
    assert "validation_test" in markdown
    assert "diagnostics only" in markdown
