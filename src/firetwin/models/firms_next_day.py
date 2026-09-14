"""First learned model for next-day FIRMS active-fire observation labels."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from firetwin.evaluation.firms_next_day import (
    evaluate_firms_next_day_prediction,
    firms_next_day_baseline_predictions,
)

FEATURE_NAMES = [
    "input_detection_probability",
    "input_cumulative_detection_probability",
    "initial_burned_probability",
    "initial_active_front",
    "fuel_model",
    "fuel_load_kg_m2",
    "fuel_moisture_percent",
    "slope_degrees",
    "elevation_m",
    "aspect_sin",
    "aspect_cos",
    "weather_temperature_c",
    "weather_relative_humidity_percent",
    "weather_wind_speed_m_s",
    "weather_wind_direction_sin",
    "weather_wind_direction_cos",
]


@dataclass(frozen=True)
class FIRMSLearnedModelResult:
    """Leave-one-fire-out learned-model result."""

    case_id: str
    model_name: str
    training_cases: str
    sample_count: int
    threshold: float
    observed_brier_score: float
    observed_mae: float
    precision_at_threshold: float
    recall_at_threshold: float
    iou_at_threshold: float
    predicted_positive_fraction: float
    target_positive_fraction: float
    persistence_brier_score: float
    brier_improvement_vs_persistence: float
    mean_prediction_on_target_positive: float
    mean_prediction_on_unlabeled: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable result."""
        return asdict(self)


def _flat_sample_yx(
    ds: xr.Dataset, flat_indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert flattened sample/y/x indices to separate index arrays."""
    sample_count = int(ds.sizes["sample"])
    height = int(ds.sizes["y"])
    width = int(ds.sizes["x"])
    sample_index, y_index, x_index = np.unravel_index(flat_indices, (sample_count, height, width))
    return sample_index.astype(np.int64), y_index.astype(np.int64), x_index.astype(np.int64)


def feature_matrix_for_indices(ds: xr.Dataset, flat_indices: np.ndarray) -> np.ndarray:
    """Build feature rows for flattened sample/y/x indices."""
    sample_index, y_index, x_index = _flat_sample_yx(ds, flat_indices)

    aspect_radians = np.deg2rad(ds["aspect_degrees"].values[y_index, x_index].astype(np.float32))
    wind_radians = np.deg2rad(
        ds["weather_wind_direction_degrees"].values[sample_index].astype(np.float32)
    )

    columns = [
        ds["input_detection_probability"].values[sample_index, y_index, x_index],
        ds["input_cumulative_detection_probability"].values[sample_index, y_index, x_index],
        ds["initial_burned_probability"].values[y_index, x_index],
        ds["initial_active_front"].values[y_index, x_index],
        ds["fuel_model"].values[y_index, x_index],
        ds["fuel_load_kg_m2"].values[y_index, x_index],
        ds["fuel_moisture_percent"].values[y_index, x_index],
        ds["slope_degrees"].values[y_index, x_index],
        ds["elevation_m"].values[y_index, x_index],
        np.sin(aspect_radians),
        np.cos(aspect_radians),
        ds["weather_temperature_c"].values[sample_index],
        ds["weather_relative_humidity_percent"].values[sample_index],
        ds["weather_wind_speed_m_s"].values[sample_index],
        np.sin(wind_radians),
        np.cos(wind_radians),
    ]
    return np.column_stack(columns).astype(np.float32)


def target_for_indices(ds: xr.Dataset, flat_indices: np.ndarray) -> np.ndarray:
    """Return binary observed-label targets for flattened sample/y/x indices."""
    target = ds["target_positive_observation_mask"].values.astype(bool).ravel()
    return target[flat_indices].astype(np.uint8)


def sample_training_indices(
    ds: xr.Dataset,
    rng: np.random.Generator,
    max_positive_cells: int = 40_000,
    negative_ratio: int = 4,
) -> np.ndarray:
    """Sample positive and no-evidence cells for observed-label training."""
    if max_positive_cells <= 0:
        raise ValueError("max_positive_cells must be positive")
    if negative_ratio <= 0:
        raise ValueError("negative_ratio must be positive")

    target = ds["target_positive_observation_mask"].values.astype(bool).ravel()
    positive_indices = np.flatnonzero(target)
    no_evidence_indices = np.flatnonzero(~target)
    if positive_indices.size == 0 or no_evidence_indices.size == 0:
        raise ValueError("Training artifact must contain both positive and no-evidence cells")

    positive_count = min(max_positive_cells, positive_indices.size)
    sampled_positive = rng.choice(positive_indices, size=positive_count, replace=False)

    negative_count = min(no_evidence_indices.size, positive_count * negative_ratio)
    sampled_no_evidence = rng.choice(no_evidence_indices, size=negative_count, replace=False)

    sampled = np.concatenate([sampled_positive, sampled_no_evidence])
    rng.shuffle(sampled)
    return sampled


def train_observed_label_logistic_model(
    training_paths: list[Path],
    random_seed: int = 42,
    max_positive_cells_per_case: int = 20_000,
    negative_ratio: int = 50,
) -> Pipeline:
    """Train a simple observed-label logistic model from next-day FIRMS samples."""
    if not training_paths:
        raise ValueError("At least one training path is required")

    rng = np.random.default_rng(random_seed)
    features = []
    targets = []
    for sample_path in training_paths:
        ds = xr.open_zarr(sample_path)
        try:
            sampled_indices = sample_training_indices(
                ds,
                rng=rng,
                max_positive_cells=max_positive_cells_per_case,
                negative_ratio=negative_ratio,
            )
            features.append(feature_matrix_for_indices(ds, sampled_indices))
            targets.append(target_for_indices(ds, sampled_indices))
        finally:
            ds.close()

    x_train = np.vstack(features)
    y_train = np.concatenate(targets)

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                SGDClassifier(
                    loss="log_loss",
                    penalty="l2",
                    alpha=1e-4,
                    max_iter=1000,
                    tol=1e-3,
                    random_state=random_seed,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    return model


def predict_observed_label_probability(
    model: Pipeline,
    ds: xr.Dataset,
    batch_size: int = 250_000,
) -> np.ndarray:
    """Predict next-day FIRMS positive-observation probabilities for a sample artifact."""
    total_cells = int(ds.sizes["sample"] * ds.sizes["y"] * ds.sizes["x"])
    prediction = np.zeros(total_cells, dtype=np.float32)
    for start in range(0, total_cells, batch_size):
        stop = min(start + batch_size, total_cells)
        flat_indices = np.arange(start, stop, dtype=np.int64)
        features = feature_matrix_for_indices(ds, flat_indices)
        prediction[start:stop] = model.predict_proba(features)[:, 1].astype(np.float32)

    return prediction.reshape((int(ds.sizes["sample"]), int(ds.sizes["y"]), int(ds.sizes["x"])))


def evaluate_learned_model_leave_one_fire_out(
    sample_paths: list[Path],
    threshold: float = 0.30,
    random_seed: int = 42,
) -> list[FIRMSLearnedModelResult]:
    """Evaluate the learned model with leave-one-fire-out validation."""
    if len(sample_paths) < 2:
        raise ValueError("At least two sample artifacts are required for holdout evaluation")

    results: list[FIRMSLearnedModelResult] = []
    for holdout_index, holdout_path in enumerate(sample_paths):
        training_paths = [
            sample_path for index, sample_path in enumerate(sample_paths) if index != holdout_index
        ]
        model = train_observed_label_logistic_model(
            training_paths,
            random_seed=random_seed + holdout_index,
        )

        ds = xr.open_zarr(holdout_path)
        try:
            prediction = predict_observed_label_probability(model, ds)
            target_probability = ds["target_detection_probability"].values.astype(np.float32)
            target_positive = ds["target_positive_observation_mask"].values.astype(bool)
            metrics = evaluate_firms_next_day_prediction(
                prediction=prediction,
                target_probability=target_probability,
                target_positive_mask=target_positive,
                threshold=threshold,
            )
            persistence = firms_next_day_baseline_predictions(ds)["persistence"]
            persistence_metrics = evaluate_firms_next_day_prediction(
                prediction=persistence,
                target_probability=target_probability,
                target_positive_mask=target_positive,
                threshold=threshold,
            )
            case_id = str(ds.attrs["case_id"])
            persistence_brier = float(persistence_metrics["observed_brier_score"])
            observed_brier = float(metrics["observed_brier_score"])
            results.append(
                FIRMSLearnedModelResult(
                    case_id=case_id,
                    model_name="observed_label_logistic_sgd",
                    training_cases=",".join(
                        path.stem.replace("_samples", "") for path in training_paths
                    ),
                    sample_count=int(ds.sizes["sample"]),
                    threshold=threshold,
                    observed_brier_score=observed_brier,
                    observed_mae=float(metrics["observed_mae"]),
                    precision_at_threshold=float(metrics["precision_at_threshold"]),
                    recall_at_threshold=float(metrics["recall_at_threshold"]),
                    iou_at_threshold=float(metrics["iou_at_threshold"]),
                    predicted_positive_fraction=float(metrics["predicted_positive_fraction"]),
                    target_positive_fraction=float(metrics["target_positive_fraction"]),
                    persistence_brier_score=persistence_brier,
                    brier_improvement_vs_persistence=persistence_brier - observed_brier,
                    mean_prediction_on_target_positive=float(
                        metrics["mean_prediction_on_target_positive"]
                    ),
                    mean_prediction_on_unlabeled=float(metrics["mean_prediction_on_unlabeled"]),
                )
            )
        finally:
            ds.close()

    return results


def render_learned_model_report(results: list[FIRMSLearnedModelResult]) -> str:
    """Render leave-one-fire-out learned-model results as Markdown."""
    lines = [
        "# FireTwin FIRMS Next-Day Learned Model Diagnostics",
        "",
        "This report evaluates a simple observed-label logistic model with leave-one-fire-out validation.",
        "It predicts next-day FIRMS positive-observation evidence, not perimeter spread.",
        "",
        "| Holdout case | Training cases | Brier | Persistence Brier | Brier improvement | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.case_id} | {result.training_cases} | "
            f"{result.observed_brier_score:.5f} | "
            f"{result.persistence_brier_score:.5f} | "
            f"{result.brier_improvement_vs_persistence:+.5f} | "
            f"{result.observed_mae:.5f} | "
            f"{result.precision_at_threshold:.3f} | {result.recall_at_threshold:.3f} | "
            f"{result.iou_at_threshold:.3f} | {result.predicted_positive_fraction:.5f} | "
            f"{result.target_positive_fraction:.5f} |"
        )

    mean_brier = (
        float(np.mean([result.observed_brier_score for result in results])) if results else 0.0
    )
    mean_persistence_brier = (
        float(np.mean([result.persistence_brier_score for result in results])) if results else 0.0
    )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Mean learned-model Brier: {mean_brier:.5f}",
            f"- Mean persistence Brier: {mean_persistence_brier:.5f}",
            f"- Mean Brier improvement vs persistence: {mean_persistence_brier - mean_brier:+.5f}",
            "",
            "## Interpretation Guardrails",
            "",
            "- The model treats no-positive-evidence cells as observed no-evidence labels, which is useful for benchmarking but not identical to true negatives.",
            "- Leave-one-fire-out validation tests cross-fire transfer on only three pilot fires, so results are early diagnostics.",
            "- A model must beat persistence on held-out fires before it is useful for the public FireTwin Explorer forecast layer.",
            "",
        ]
    )
    return "\n".join(lines)
