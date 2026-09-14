"""Tests for the first learned next-day FIRMS model."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from firetwin.models.firms_next_day import (
    evaluate_learned_model_leave_one_fire_out,
    feature_matrix_for_indices,
    render_learned_model_report,
    sample_training_indices,
    train_observed_label_logistic_model,
)


def write_model_sample(path: Path, case_id: str, positive_corner: tuple[int, int]) -> None:
    """Write a tiny sample artifact with separable static and temporal features."""
    sample_count = 2
    shape = (3, 3)
    input_detection = np.zeros((sample_count, *shape), dtype=np.float32)
    cumulative = np.zeros((sample_count, *shape), dtype=np.float32)
    target_probability = np.zeros((sample_count, *shape), dtype=np.float32)

    row, col = positive_corner
    input_detection[:, row, col] = 0.8
    cumulative[:, row, col] = 0.8
    target_probability[:, row, col] = 0.9

    fuel_load = np.ones(shape, dtype=np.float32) * 0.2
    fuel_load[row, col] = 1.0
    ds = xr.Dataset(
        data_vars={
            "input_detection_probability": (["sample", "y", "x"], input_detection),
            "input_cumulative_detection_probability": (["sample", "y", "x"], cumulative),
            "target_detection_probability": (["sample", "y", "x"], target_probability),
            "target_positive_observation_mask": (
                ["sample", "y", "x"],
                (target_probability > 0).astype(np.uint8),
            ),
            "initial_burned_probability": (["y", "x"], cumulative[0]),
            "initial_active_front": (["y", "x"], (cumulative[0] > 0).astype(np.uint8)),
            "fuel_model": (["y", "x"], np.ones(shape, dtype=np.int16) * 101),
            "fuel_load_kg_m2": (["y", "x"], fuel_load),
            "fuel_moisture_percent": (["y", "x"], np.ones(shape, dtype=np.float32) * 8),
            "slope_degrees": (["y", "x"], np.ones(shape, dtype=np.float32) * 5),
            "elevation_m": (["y", "x"], np.ones(shape, dtype=np.float32) * 1000),
            "aspect_degrees": (["y", "x"], np.ones(shape, dtype=np.float32) * 180),
            "weather_temperature_c": (["sample"], np.ones(sample_count, dtype=np.float32) * 25),
            "weather_relative_humidity_percent": (
                ["sample"],
                np.ones(sample_count, dtype=np.float32) * 30,
            ),
            "weather_wind_speed_m_s": (["sample"], np.ones(sample_count, dtype=np.float32) * 3),
            "weather_wind_direction_degrees": (
                ["sample"],
                np.ones(sample_count, dtype=np.float32) * 270,
            ),
        },
        coords={
            "sample": np.arange(sample_count),
            "reference_time": (["sample"], pd.to_datetime(["2014-01-01", "2014-01-02"])),
            "target_time": (["sample"], pd.to_datetime(["2014-01-02", "2014-01-03"])),
            "y": np.arange(shape[0]),
            "x": np.arange(shape[1]),
        },
        attrs={
            "case_id": case_id,
            "sample_type": "firms_next_day_active_fire_probability",
            "excludes_final_extent_as_input": "true",
        },
    )
    ds.to_zarr(path, mode="w")


def test_feature_matrix_and_sampling(tmp_path: Path) -> None:
    """Feature extraction should produce stable rows and sampled binary targets."""
    sample_path = tmp_path / "case_a.zarr"
    write_model_sample(sample_path, "case_a", (0, 0))
    ds = xr.open_zarr(sample_path)
    try:
        indices = sample_training_indices(
            ds,
            rng=np.random.default_rng(1),
            max_positive_cells=2,
            negative_ratio=2,
        )
        features = feature_matrix_for_indices(ds, indices)
    finally:
        ds.close()

    assert indices.size == 6
    assert features.shape[0] == 6
    assert features.shape[1] >= 10


def test_train_and_evaluate_leave_one_fire_out(tmp_path: Path) -> None:
    """The learned model pipeline should run leave-one-fire-out diagnostics."""
    paths = []
    for case_id, corner in [
        ("case_a", (0, 0)),
        ("case_b", (1, 1)),
        ("case_c", (2, 2)),
    ]:
        path = tmp_path / f"{case_id}_samples.zarr"
        write_model_sample(path, case_id, corner)
        paths.append(path)

    model = train_observed_label_logistic_model(
        paths[:2],
        random_seed=7,
        max_positive_cells_per_case=2,
        negative_ratio=2,
    )
    assert hasattr(model, "predict_proba")

    results = evaluate_learned_model_leave_one_fire_out(paths, random_seed=7)
    report = render_learned_model_report(results)

    assert len(results) == 3
    assert all(result.model_name == "observed_label_logistic_sgd" for result in results)
    assert "leave-one-fire-out" in report
