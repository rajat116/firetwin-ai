"""Baseline evaluation for next-day FIRMS active-fire sample artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


@dataclass(frozen=True)
class FIRMSNextDayBaselineResult:
    """Metrics for one next-day FIRMS baseline on one sample artifact."""

    case_id: str
    baseline: str
    sample_count: int
    threshold: float
    observed_brier_score: float
    observed_mae: float
    precision_at_threshold: float
    recall_at_threshold: float
    iou_at_threshold: float
    predicted_positive_fraction: float
    target_positive_fraction: float
    target_positive_cell_count: int
    predicted_positive_cell_count: int
    mean_prediction_on_target_positive: float
    mean_prediction_on_unlabeled: float
    sample_path: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


def _safe_ratio(numerator: int, denominator: int) -> float:
    """Return a stable ratio."""
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _normalize_positive(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """Normalize non-negative values to [0, 1] with optional valid mask."""
    values_float = np.asarray(values, dtype=np.float32)
    if mask is None:
        mask = np.ones(values_float.shape, dtype=bool)

    normalized = np.zeros(values_float.shape, dtype=np.float32)
    valid_values = values_float[mask]
    if valid_values.size == 0:
        return normalized

    min_value = float(np.nanmin(valid_values))
    max_value = float(np.nanmax(valid_values))
    if not np.isfinite(min_value) or not np.isfinite(max_value) or max_value <= min_value:
        normalized[mask] = 1.0 if max_value > 0 else 0.0
        return normalized

    normalized[mask] = (values_float[mask] - min_value) / (max_value - min_value)
    return normalized


def fuel_terrain_prior(sample_ds: xr.Dataset) -> np.ndarray:
    """Build a static fuel/terrain active-fire prior without using target labels."""
    burnable = sample_ds["fuel_model"].values > 0
    fuel_load = sample_ds["fuel_load_kg_m2"].values.astype(np.float32)
    moisture = sample_ds["fuel_moisture_percent"].values.astype(np.float32)
    slope = sample_ds["slope_degrees"].values.astype(np.float32)

    load_score = _normalize_positive(fuel_load, burnable)
    slope_score = _normalize_positive(slope, burnable)
    moisture_score = np.zeros(moisture.shape, dtype=np.float32)
    if np.any(burnable):
        max_moisture = float(np.nanmax(moisture[burnable]))
        if max_moisture > 0:
            moisture_score[burnable] = 1.0 - np.clip(moisture[burnable] / max_moisture, 0.0, 1.0)

    prior = np.zeros(fuel_load.shape, dtype=np.float32)
    prior[burnable] = (
        0.50 * load_score[burnable] + 0.25 * slope_score[burnable] + 0.25 * moisture_score[burnable]
    )
    return np.clip(prior, 0.0, 1.0)


def firms_next_day_baseline_predictions(sample_ds: xr.Dataset) -> dict[str, np.ndarray]:
    """Generate baseline probability predictions for a next-day FIRMS sample artifact."""
    sample_count = int(sample_ds.sizes["sample"])
    static_prior = fuel_terrain_prior(sample_ds)

    return {
        "persistence": np.clip(
            sample_ds["input_detection_probability"].values.astype(np.float32), 0.0, 1.0
        ),
        "cumulative_history": np.clip(
            sample_ds["input_cumulative_detection_probability"].values.astype(np.float32),
            0.0,
            1.0,
        ),
        "fuel_terrain_prior": np.broadcast_to(
            static_prior[np.newaxis, :, :],
            (sample_count, *static_prior.shape),
        ).astype(np.float32),
    }


def evaluate_firms_next_day_prediction(
    prediction: np.ndarray,
    target_probability: np.ndarray,
    target_positive_mask: np.ndarray,
    threshold: float,
) -> dict[str, float | int]:
    """Evaluate one probability prediction against FIRMS observation labels."""
    prediction_clipped = np.clip(prediction.astype(np.float32), 0.0, 1.0)
    target_probability_float = np.clip(target_probability.astype(np.float32), 0.0, 1.0)
    target_positive = target_positive_mask.astype(bool)
    predicted_positive = prediction_clipped >= threshold

    overlap = predicted_positive & target_positive
    union = predicted_positive | target_positive
    predicted_positive_count = int(np.sum(predicted_positive))
    target_positive_count = int(np.sum(target_positive))
    overlap_count = int(np.sum(overlap))
    total_count = int(prediction_clipped.size)

    if target_positive_count:
        mean_on_positive = float(np.mean(prediction_clipped[target_positive]))
    else:
        mean_on_positive = 0.0

    unlabeled = ~target_positive
    mean_on_unlabeled = float(np.mean(prediction_clipped[unlabeled])) if np.any(unlabeled) else 0.0

    return {
        "observed_brier_score": float(
            np.mean((prediction_clipped - target_probability_float) ** 2)
        ),
        "observed_mae": float(np.mean(np.abs(prediction_clipped - target_probability_float))),
        "precision_at_threshold": _safe_ratio(overlap_count, predicted_positive_count),
        "recall_at_threshold": _safe_ratio(overlap_count, target_positive_count),
        "iou_at_threshold": _safe_ratio(overlap_count, int(np.sum(union))),
        "predicted_positive_fraction": _safe_ratio(predicted_positive_count, total_count),
        "target_positive_fraction": _safe_ratio(target_positive_count, total_count),
        "target_positive_cell_count": target_positive_count,
        "predicted_positive_cell_count": predicted_positive_count,
        "mean_prediction_on_target_positive": mean_on_positive,
        "mean_prediction_on_unlabeled": mean_on_unlabeled,
    }


def evaluate_firms_next_day_baselines(
    sample_path: Path,
    threshold: float = 0.30,
) -> list[FIRMSNextDayBaselineResult]:
    """Evaluate simple baselines for one FIRMS next-day sample artifact."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")

    ds = xr.open_zarr(sample_path)
    try:
        if ds.attrs.get("sample_type") != "firms_next_day_active_fire_probability":
            raise ValueError(
                f"{sample_path} must contain firms_next_day_active_fire_probability samples"
            )
        if ds.attrs.get("excludes_final_extent_as_input") != "true":
            raise ValueError(f"{sample_path} must exclude final extent as a model input")

        target_probability = ds["target_detection_probability"].values.astype(np.float32)
        target_positive = ds["target_positive_observation_mask"].values.astype(bool)
        predictions = firms_next_day_baseline_predictions(ds)
        case_id = str(ds.attrs["case_id"])
        sample_count = int(ds.sizes["sample"])

        results = []
        for baseline_name, prediction in predictions.items():
            metrics = evaluate_firms_next_day_prediction(
                prediction=prediction,
                target_probability=target_probability,
                target_positive_mask=target_positive,
                threshold=threshold,
            )
            results.append(
                FIRMSNextDayBaselineResult(
                    case_id=case_id,
                    baseline=baseline_name,
                    sample_count=sample_count,
                    threshold=threshold,
                    observed_brier_score=float(metrics["observed_brier_score"]),
                    observed_mae=float(metrics["observed_mae"]),
                    precision_at_threshold=float(metrics["precision_at_threshold"]),
                    recall_at_threshold=float(metrics["recall_at_threshold"]),
                    iou_at_threshold=float(metrics["iou_at_threshold"]),
                    predicted_positive_fraction=float(metrics["predicted_positive_fraction"]),
                    target_positive_fraction=float(metrics["target_positive_fraction"]),
                    target_positive_cell_count=int(metrics["target_positive_cell_count"]),
                    predicted_positive_cell_count=int(metrics["predicted_positive_cell_count"]),
                    mean_prediction_on_target_positive=float(
                        metrics["mean_prediction_on_target_positive"]
                    ),
                    mean_prediction_on_unlabeled=float(metrics["mean_prediction_on_unlabeled"]),
                    sample_path=str(sample_path),
                )
            )
        return results
    finally:
        ds.close()


def render_firms_next_day_baseline_report(
    results: list[FIRMSNextDayBaselineResult],
) -> str:
    """Render a Markdown report for FIRMS next-day baseline diagnostics."""
    lines = [
        "# FireTwin FIRMS Next-Day Baseline Diagnostics",
        "",
        "These are observation-label diagnostics for next-day FIRMS active-fire evidence.",
        "Target zeros are positive-unlabeled no-evidence cells, not confirmed unburned cells.",
        "",
        "| Case | Baseline | Samples | Brier | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac | Mean pred on target + | Mean pred on unlabeled |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.case_id} | {result.baseline} | {result.sample_count:,} | "
            f"{result.observed_brier_score:.5f} | {result.observed_mae:.5f} | "
            f"{result.precision_at_threshold:.3f} | {result.recall_at_threshold:.3f} | "
            f"{result.iou_at_threshold:.3f} | {result.predicted_positive_fraction:.5f} | "
            f"{result.target_positive_fraction:.5f} | "
            f"{result.mean_prediction_on_target_positive:.3f} | "
            f"{result.mean_prediction_on_unlabeled:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Baselines",
            "",
            "- `persistence`: predicts tomorrow from same-day FIRMS detection probability.",
            "- `cumulative_history`: predicts tomorrow from all prior FIRMS positive evidence.",
            "- `fuel_terrain_prior`: static prior from fuel load, fuel moisture proxy and slope.",
            "",
            "## Interpretation Guardrails",
            "",
            "- Lower Brier/MAE is better for the observed FIRMS probability proxy.",
            "- Precision/recall/IoU are threshold diagnostics against positive FIRMS observations only.",
            "- These metrics are not perimeter accuracy and should not be reported as operational spread skill.",
            "",
        ]
    )
    return "\n".join(lines)
