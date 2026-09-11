"""Tests for FIRMS hotspot progression label construction."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from firetwin.data.firms_labels import (
    FIRMSLabelConfig,
    add_grid_indices,
    build_firms_label_artifact,
    confidence_score,
    filter_firms_records,
    rasterize_firms_records,
    read_case_grid,
)


def write_test_case_zarr(path: Path) -> None:
    """Write a minimal FireCase-like Zarr with WGS84 grid metadata."""
    burned = np.zeros((2, 2, 2), dtype=np.uint8)
    burned[-1, 0, 0] = 1
    burned[-1, 1, 1] = 1
    ds = xr.Dataset(
        data_vars={"burned": (["time", "y", "x"], burned)},
        coords={"time": pd.to_datetime(["2014-01-01", "2014-01-02"]), "y": [0, 1], "x": [0, 1]},
        attrs={
            "case_id": "label_test",
            "name": "Label Test",
            "bbox_min_x": 0.0,
            "bbox_min_y": 0.0,
            "bbox_max_x": 2.0,
            "bbox_max_y": 2.0,
            "bbox_crs": "EPSG:4326",
            "resolution_m": 1.0,
        },
    )
    ds.to_zarr(path, mode="w")


def sample_records() -> pd.DataFrame:
    """Create FIRMS-like records for label tests."""
    return pd.DataFrame(
        [
            {
                "source": "VIIRS_SNPP_SP",
                "latitude": 1.5,
                "longitude": 0.5,
                "scan": 0.0,
                "track": 0.0,
                "acquisition_datetime": "2014-01-01T10:00:00",
                "confidence": "nominal",
                "frp": 20.0,
            },
            {
                "source": "VIIRS_SNPP_SP",
                "latitude": 0.5,
                "longitude": 0.5,
                "scan": 0.0,
                "track": 0.0,
                "acquisition_datetime": "2014-01-01T11:00:00",
                "confidence": "high",
                "frp": 30.0,
            },
            {
                "source": "MODIS_SP",
                "latitude": 0.5,
                "longitude": 1.5,
                "scan": 0.0,
                "track": 0.0,
                "acquisition_datetime": "2014-01-02T10:00:00",
                "confidence": 10,
                "frp": 30.0,
            },
        ]
    )


def test_confidence_score_normalizes_numeric_and_text_values() -> None:
    """FIRMS numeric and categorical confidence values should share a 0-1 scale."""
    assert confidence_score("low") == 0.30
    assert confidence_score("nominal") == 0.60
    assert confidence_score("high") == 0.90
    assert confidence_score(95) == 0.95
    assert confidence_score("0.4") == 0.4
    assert confidence_score("unknown") == 0.0


def test_add_grid_indices_uses_top_left_grid_origin(tmp_path: Path) -> None:
    """WGS84 points should map to the same top-left origin convention as rasterio."""
    case_path = tmp_path / "case.zarr"
    write_test_case_zarr(case_path)
    grid = read_case_grid(case_path)

    indexed = add_grid_indices(sample_records().iloc[:2], grid)

    assert indexed[["row", "col"]].to_dict("records") == [
        {"row": 0, "col": 0},
        {"row": 1, "col": 0},
    ]


def test_filter_firms_records_applies_quality_and_final_extent_qc(tmp_path: Path) -> None:
    """Filtering should remove low confidence and off-final-extent detections."""
    case_path = tmp_path / "case.zarr"
    write_test_case_zarr(case_path)
    grid = read_case_grid(case_path)

    filtered = filter_firms_records(sample_records(), grid, FIRMSLabelConfig())

    assert len(filtered) == 1
    assert filtered.iloc[0]["row"] == 0
    assert filtered.iloc[0]["col"] == 0
    assert filtered.iloc[0]["confidence_score"] == 0.60


def test_rasterize_firms_records_preserves_missing_as_unknown(tmp_path: Path) -> None:
    """Zero cells should be documented as unknown, not negative labels."""
    case_path = tmp_path / "case.zarr"
    write_test_case_zarr(case_path)
    grid = read_case_grid(case_path)

    ds = rasterize_firms_records(
        sample_records(),
        grid,
        FIRMSLabelConfig(use_detection_footprint=False),
    )

    assert ds.attrs["label_type"] == "irregular_firms_hotspot_progression"
    assert ds.attrs["time_bin"] == "date"
    assert ds.attrs["not_hourly_perimeter_truth"] == "true"
    assert ds.attrs["non_detection_semantics"] == "missing_or_unobserved_not_unburned"
    assert ds.sizes["time"] == 1
    assert int(ds["detection_count"].sum().item()) == 1
    assert float(ds["detection_probability"].max().item()) == pytest.approx(0.60)
    assert int(ds["positive_observation_mask"].sum().item()) == 1


def test_rasterize_firms_records_can_use_raw_timestamps(tmp_path: Path) -> None:
    """Timestamp binning should remain available for later high-cadence experiments."""
    case_path = tmp_path / "case.zarr"
    write_test_case_zarr(case_path)
    grid = read_case_grid(case_path)

    ds = rasterize_firms_records(
        sample_records(),
        grid,
        FIRMSLabelConfig(
            use_detection_footprint=False,
            mask_to_final_extent=False,
            time_bin="timestamp",
        ),
    )

    assert ds.attrs["time_bin"] == "timestamp"
    assert ds.sizes["time"] == 2


def test_build_firms_label_artifact_writes_zarr_summary(tmp_path: Path) -> None:
    """The artifact builder should save an aligned Zarr label product."""
    case_path = tmp_path / "case.zarr"
    output_path = tmp_path / "labels.zarr"
    write_test_case_zarr(case_path)

    summary = build_firms_label_artifact(
        case_path,
        sample_records(),
        output_path,
        FIRMSLabelConfig(use_detection_footprint=False),
    )

    assert output_path.exists()
    assert summary.case_id == "label_test"
    assert summary.retained_detection_count == 1
    assert summary.time_slice_count == 1

    ds = xr.open_zarr(output_path)
    try:
        assert ds.attrs["target_type"] == "active_fire_detection_probability"
        assert "cumulative_detection_probability" in ds
    finally:
        ds.close()
