"""Diagnostics for learned next-day FIRMS forecast artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

DEFAULT_THRESHOLDS = (0.01, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)


@dataclass(frozen=True)
class ForecastReliabilityBin:
    """One reliability bin for an observed-label probability forecast."""

    case_id: str
    bin_index: int
    probability_min: float
    probability_max: float
    mean_prediction: float
    observed_frequency: float
    cell_count: int
    cell_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


@dataclass(frozen=True)
class ForecastThresholdDiagnostic:
    """Thresholded diagnostic for a learned forecast artifact."""

    case_id: str
    threshold: float
    precision: float
    recall: float
    f1_score: float
    iou: float
    predicted_positive_fraction: float
    target_positive_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


@dataclass(frozen=True)
class ForecastCalibrationDiagnostic:
    """Calibration and threshold summary for one forecast artifact."""

    case_id: str
    forecast_path: str
    sample_count: int
    grid_shape: str
    observed_brier_score: float
    observed_mae: float
    expected_calibration_error: float
    max_calibration_error: float
    recommended_threshold: float
    recommended_precision: float
    recommended_recall: float
    recommended_f1_score: float
    recommended_iou: float
    recommended_predicted_positive_fraction: float
    target_positive_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


@dataclass(frozen=True)
class ForecastArtifactDiagnostics:
    """Full diagnostics for one learned forecast artifact."""

    summary: ForecastCalibrationDiagnostic
    reliability_bins: list[ForecastReliabilityBin]
    threshold_diagnostics: list[ForecastThresholdDiagnostic]


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    """Return a stable ratio."""
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def reliability_bins_for_forecast(
    *,
    case_id: str,
    prediction: np.ndarray,
    target_probability: np.ndarray,
    bin_count: int = 10,
) -> list[ForecastReliabilityBin]:
    """Compute reliability bins against observed FIRMS probability labels."""
    if bin_count <= 0:
        raise ValueError("bin_count must be positive")

    prediction_flat = np.clip(prediction.astype(np.float32).ravel(), 0.0, 1.0)
    target_flat = np.clip(target_probability.astype(np.float32).ravel(), 0.0, 1.0)
    if prediction_flat.shape != target_flat.shape:
        raise ValueError("prediction and target_probability must have the same flattened shape")

    edges = np.linspace(0.0, 1.0, bin_count + 1, dtype=np.float32)
    total_count = int(prediction_flat.size)
    bins: list[ForecastReliabilityBin] = []
    for bin_index in range(bin_count):
        lower = float(edges[bin_index])
        upper = float(edges[bin_index + 1])
        if bin_index == bin_count - 1:
            mask = (prediction_flat >= lower) & (prediction_flat <= upper)
        else:
            mask = (prediction_flat >= lower) & (prediction_flat < upper)

        cell_count = int(np.sum(mask))
        if cell_count:
            mean_prediction = float(np.mean(prediction_flat[mask]))
            observed_frequency = float(np.mean(target_flat[mask]))
        else:
            mean_prediction = 0.0
            observed_frequency = 0.0

        bins.append(
            ForecastReliabilityBin(
                case_id=case_id,
                bin_index=bin_index,
                probability_min=lower,
                probability_max=upper,
                mean_prediction=mean_prediction,
                observed_frequency=observed_frequency,
                cell_count=cell_count,
                cell_fraction=_safe_ratio(cell_count, total_count),
            )
        )
    return bins


def expected_calibration_error(bins: list[ForecastReliabilityBin]) -> float:
    """Compute weighted expected calibration error from reliability bins."""
    return float(
        sum(
            bin_result.cell_fraction
            * abs(bin_result.mean_prediction - bin_result.observed_frequency)
            for bin_result in bins
        )
    )


def max_calibration_error(bins: list[ForecastReliabilityBin]) -> float:
    """Compute maximum populated-bin calibration error."""
    populated = [bin_result for bin_result in bins if bin_result.cell_count > 0]
    if not populated:
        return 0.0
    return float(
        max(
            abs(bin_result.mean_prediction - bin_result.observed_frequency)
            for bin_result in populated
        )
    )


def threshold_diagnostics_for_forecast(
    *,
    case_id: str,
    prediction: np.ndarray,
    target_positive_mask: np.ndarray,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
) -> list[ForecastThresholdDiagnostic]:
    """Compute thresholded precision/recall diagnostics for a forecast."""
    prediction_clipped = np.clip(prediction.astype(np.float32), 0.0, 1.0)
    target_positive = target_positive_mask.astype(bool)
    target_positive_count = int(np.sum(target_positive))
    total_count = int(prediction_clipped.size)
    results: list[ForecastThresholdDiagnostic] = []

    for threshold in thresholds:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("thresholds must be in [0, 1]")
        predicted_positive = prediction_clipped >= threshold
        predicted_positive_count = int(np.sum(predicted_positive))
        overlap_count = int(np.sum(predicted_positive & target_positive))
        union_count = int(np.sum(predicted_positive | target_positive))
        precision = _safe_ratio(overlap_count, predicted_positive_count)
        recall = _safe_ratio(overlap_count, target_positive_count)
        f1_score = _safe_ratio(2.0 * precision * recall, precision + recall)
        results.append(
            ForecastThresholdDiagnostic(
                case_id=case_id,
                threshold=float(threshold),
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                iou=_safe_ratio(overlap_count, union_count),
                predicted_positive_fraction=_safe_ratio(predicted_positive_count, total_count),
                target_positive_fraction=_safe_ratio(target_positive_count, total_count),
            )
        )
    return results


def select_recommended_threshold(
    diagnostics: list[ForecastThresholdDiagnostic],
) -> ForecastThresholdDiagnostic:
    """Choose a demo diagnostic threshold from thresholded forecast results."""
    if not diagnostics:
        raise ValueError("At least one threshold diagnostic is required")
    return max(
        diagnostics,
        key=lambda result: (
            result.f1_score,
            result.iou,
            -abs(result.predicted_positive_fraction - result.target_positive_fraction),
        ),
    )


def evaluate_forecast_artifact(
    forecast_path: Path,
    *,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    bin_count: int = 10,
) -> ForecastArtifactDiagnostics:
    """Evaluate one learned next-day FIRMS forecast artifact."""
    ds = xr.open_zarr(forecast_path)
    try:
        if (
            ds.attrs.get("forecast_type")
            != "leave_one_fire_out_next_day_firms_active_fire_probability"
        ):
            raise ValueError(f"{forecast_path} must be a learned next-day FIRMS forecast artifact")
        if ds.attrs.get("excludes_final_extent_as_input") != "true":
            raise ValueError(f"{forecast_path} must exclude final extent as a model input")

        case_id = str(ds.attrs["case_id"])
        prediction = ds["forecast_probability"].values.astype(np.float32)
        target_probability = ds["target_detection_probability"].values.astype(np.float32)
        target_positive = ds["target_positive_observation_mask"].values.astype(bool)

        reliability = reliability_bins_for_forecast(
            case_id=case_id,
            prediction=prediction,
            target_probability=target_probability,
            bin_count=bin_count,
        )
        threshold_results = threshold_diagnostics_for_forecast(
            case_id=case_id,
            prediction=prediction,
            target_positive_mask=target_positive,
            thresholds=thresholds,
        )
        recommended = select_recommended_threshold(threshold_results)
        prediction_clipped = np.clip(prediction, 0.0, 1.0)
        target_clipped = np.clip(target_probability, 0.0, 1.0)

        return ForecastArtifactDiagnostics(
            summary=ForecastCalibrationDiagnostic(
                case_id=case_id,
                forecast_path=str(forecast_path),
                sample_count=int(ds.sizes["sample"]),
                grid_shape=f"{ds.sizes['y']}x{ds.sizes['x']}",
                observed_brier_score=float(np.mean((prediction_clipped - target_clipped) ** 2)),
                observed_mae=float(np.mean(np.abs(prediction_clipped - target_clipped))),
                expected_calibration_error=expected_calibration_error(reliability),
                max_calibration_error=max_calibration_error(reliability),
                recommended_threshold=recommended.threshold,
                recommended_precision=recommended.precision,
                recommended_recall=recommended.recall,
                recommended_f1_score=recommended.f1_score,
                recommended_iou=recommended.iou,
                recommended_predicted_positive_fraction=recommended.predicted_positive_fraction,
                target_positive_fraction=recommended.target_positive_fraction,
            ),
            reliability_bins=reliability,
            threshold_diagnostics=threshold_results,
        )
    finally:
        ds.close()


def render_forecast_calibration_report(
    diagnostics: list[ForecastArtifactDiagnostics],
    *,
    figure_paths: dict[str, str] | None = None,
) -> str:
    """Render a Markdown report for forecast calibration and threshold diagnostics."""
    figure_paths = figure_paths or {}
    lines = [
        "# FireTwin FIRMS Next-Day Forecast Calibration",
        "",
        "This report evaluates calibration and threshold behavior for leave-one-fire-out learned forecast artifacts.",
        "Targets are FIRMS positive-observation evidence, not exact perimeter spread.",
        "",
        "| Case | Samples | Grid | Brier | MAE | ECE | Max calib error | Recommended threshold | Precision | Recall | F1 | IoU | Predicted + frac | Target + frac |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for diagnostic in diagnostics:
        summary = diagnostic.summary
        lines.append(
            f"| {summary.case_id} | {summary.sample_count:,} | {summary.grid_shape} | "
            f"{summary.observed_brier_score:.5f} | {summary.observed_mae:.5f} | "
            f"{summary.expected_calibration_error:.5f} | {summary.max_calibration_error:.5f} | "
            f"{summary.recommended_threshold:.3f} | {summary.recommended_precision:.3f} | "
            f"{summary.recommended_recall:.3f} | {summary.recommended_f1_score:.3f} | "
            f"{summary.recommended_iou:.3f} | "
            f"{summary.recommended_predicted_positive_fraction:.5f} | "
            f"{summary.target_positive_fraction:.5f} |"
        )

    if diagnostics:
        mean_ece = float(
            np.mean([diagnostic.summary.expected_calibration_error for diagnostic in diagnostics])
        )
        mean_brier = float(
            np.mean([diagnostic.summary.observed_brier_score for diagnostic in diagnostics])
        )
        recommended_thresholds = sorted(
            {diagnostic.summary.recommended_threshold for diagnostic in diagnostics}
        )
    else:
        mean_ece = 0.0
        mean_brier = 0.0
        recommended_thresholds = []

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Mean observed-label Brier: {mean_brier:.5f}",
            f"- Mean observed-label ECE: {mean_ece:.5f}",
            "- Recommended threshold candidates: "
            + (
                ", ".join(f"{threshold:.3f}" for threshold in recommended_thresholds)
                if recommended_thresholds
                else "none"
            ),
            "",
        ]
    )

    if figure_paths:
        lines.extend(["## Reliability Figures", ""])
        for case_id, figure_path in sorted(figure_paths.items()):
            lines.append(f"- {case_id}: `{figure_path}`")
        lines.append("")

    lines.extend(
        [
            "## Threshold Sweeps",
            "",
            "| Case | Threshold | Precision | Recall | F1 | IoU | Predicted + frac | Target + frac |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for diagnostic in diagnostics:
        for result in diagnostic.threshold_diagnostics:
            lines.append(
                f"| {result.case_id} | {result.threshold:.3f} | "
                f"{result.precision:.3f} | {result.recall:.3f} | "
                f"{result.f1_score:.3f} | {result.iou:.3f} | "
                f"{result.predicted_positive_fraction:.5f} | "
                f"{result.target_positive_fraction:.5f} |"
            )

    lines.extend(
        [
            "",
            "## Reliability Bins",
            "",
            "| Case | Bin | Probability range | Mean prediction | Observed frequency | Cell fraction |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for diagnostic in diagnostics:
        for bin_result in diagnostic.reliability_bins:
            if bin_result.cell_count == 0:
                continue
            lines.append(
                f"| {bin_result.case_id} | {bin_result.bin_index} | "
                f"[{bin_result.probability_min:.2f}, {bin_result.probability_max:.2f}] | "
                f"{bin_result.mean_prediction:.5f} | "
                f"{bin_result.observed_frequency:.5f} | {bin_result.cell_fraction:.5f} |"
            )

    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- ECE is computed against observed FIRMS probability labels; no-positive-evidence cells are not confirmed negatives.",
            "- Recommended thresholds are diagnostic display thresholds, not evacuation or operational decision thresholds.",
            "- Reliability should be revisited after adding more fires and richer weather/fuel covariates.",
            "",
        ]
    )
    return "\n".join(lines)
