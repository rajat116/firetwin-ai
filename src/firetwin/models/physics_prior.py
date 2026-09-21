"""Phase 6 physics-prior fields aligned to FIRMS next-day sample artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from firetwin.evaluation.firms_next_day import (
    evaluate_firms_next_day_prediction,
    fuel_terrain_prior,
)

PHYSICS_PRIOR_NAME = "phase6_wind_aware_fuel_spread_prior_v1"


@dataclass(frozen=True)
class PhysicsPriorArtifactSummary:
    """Summary for one aligned Phase 6 physics-prior artifact."""

    case_id: str
    output_path: str
    sample_count: int
    grid_shape: str
    prior_source: str
    threshold: float
    observed_brier_score: float
    observed_mae: float
    precision_at_threshold: float
    recall_at_threshold: float
    iou_at_threshold: float
    predicted_positive_fraction: float
    target_positive_fraction: float
    mean_prior_on_target_positive: float
    mean_prior_on_unlabeled: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


def _shift_without_wrap(values: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Shift a 2D array while filling newly exposed cells with zero."""
    shifted = np.zeros_like(values, dtype=np.float32)
    src_y_start = max(0, -dy)
    src_y_stop = values.shape[0] - max(0, dy)
    src_x_start = max(0, -dx)
    src_x_stop = values.shape[1] - max(0, dx)
    dst_y_start = max(0, dy)
    dst_y_stop = values.shape[0] - max(0, -dy)
    dst_x_start = max(0, dx)
    dst_x_stop = values.shape[1] - max(0, -dx)

    if src_y_start < src_y_stop and src_x_start < src_x_stop:
        shifted[dst_y_start:dst_y_stop, dst_x_start:dst_x_stop] = values[
            src_y_start:src_y_stop, src_x_start:src_x_stop
        ]
    return shifted


def _wind_to_spread_vector(wind_direction_degrees: float) -> tuple[float, float]:
    """Convert meteorological wind-from degrees into downwind x/y spread components."""
    radians = np.deg2rad((wind_direction_degrees + 180.0) % 360.0)
    x_component = float(np.sin(radians))
    y_component = float(-np.cos(radians))
    return x_component, y_component


def _wind_directional_expansion(
    source_probability: np.ndarray,
    *,
    wind_direction_degrees: float,
    wind_speed_m_s: float,
) -> np.ndarray:
    """Expand same-day active-fire evidence one cell, favoring downwind neighbors."""
    spread_x, spread_y = _wind_to_spread_vector(wind_direction_degrees)
    wind_strength = float(np.clip(wind_speed_m_s / 12.0, 0.0, 1.0))
    expanded = np.zeros(source_probability.shape, dtype=np.float32)

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            norm = float(np.hypot(dx, dy))
            alignment = (dx / norm) * spread_x + (dy / norm) * spread_y
            directional_weight = 0.35 + 0.65 * max(0.0, alignment) * wind_strength
            distance_weight = 1.0 if norm == 1.0 else 0.7
            expanded = np.maximum(
                expanded,
                _shift_without_wrap(source_probability, dy, dx)
                * directional_weight
                * distance_weight,
            )
    return expanded


def wind_aware_fuel_spread_prior(sample_ds: xr.Dataset) -> np.ndarray:
    """Build a sample-aligned physics-style prior for next-day active-fire evidence.

    The prior uses only same-day detection evidence, cumulative history, static fuel/terrain
    susceptibility and reference-time weather. It is aligned to the Phase 5A sample tensor and does
    not inspect next-day targets or final burned extent.
    """
    if sample_ds.attrs.get("sample_type") != "firms_next_day_active_fire_probability":
        raise ValueError("sample_ds must contain firms_next_day_active_fire_probability samples")
    if sample_ds.attrs.get("excludes_final_extent_as_input") != "true":
        raise ValueError("sample_ds must exclude final extent as a model input")

    input_detection = np.clip(
        sample_ds["input_detection_probability"].values.astype(np.float32), 0.0, 1.0
    )
    cumulative = np.clip(
        sample_ds["input_cumulative_detection_probability"].values.astype(np.float32), 0.0, 1.0
    )
    static_prior = fuel_terrain_prior(sample_ds)
    burnable = sample_ds["fuel_model"].values > 0
    sample_count = int(sample_ds.sizes["sample"])
    prior = np.zeros_like(input_detection, dtype=np.float32)

    wind_speed = (
        sample_ds["weather_wind_speed_m_s"].values.astype(np.float32)
        if "weather_wind_speed_m_s" in sample_ds
        else np.full(sample_count, 3.0, dtype=np.float32)
    )
    wind_direction = (
        sample_ds["weather_wind_direction_degrees"].values.astype(np.float32)
        if "weather_wind_direction_degrees" in sample_ds
        else np.zeros(sample_count, dtype=np.float32)
    )

    for sample_index in range(sample_count):
        expanded = _wind_directional_expansion(
            input_detection[sample_index],
            wind_direction_degrees=float(wind_direction[sample_index]),
            wind_speed_m_s=float(wind_speed[sample_index]),
        )
        prior[sample_index] = (
            0.46 * expanded
            + 0.28 * input_detection[sample_index]
            + 0.16 * cumulative[sample_index]
            + 0.10 * static_prior
        )
        prior[sample_index, ~burnable] = 0.0

    return np.clip(prior, 0.0, 1.0).astype(np.float32)


def build_physics_prior_dataset(
    sample_ds: xr.Dataset,
    prior_probability: np.ndarray,
    *,
    source_sample_path: Path,
    threshold: float = 0.05,
) -> xr.Dataset:
    """Package an aligned physics prior as a zarr-ready dataset."""
    expected_shape = (
        int(sample_ds.sizes["sample"]),
        int(sample_ds.sizes["y"]),
        int(sample_ds.sizes["x"]),
    )
    if prior_probability.shape != expected_shape:
        raise ValueError(
            f"prior_probability shape {prior_probability.shape} does not match {expected_shape}"
        )

    prior = np.clip(prior_probability.astype(np.float32), 0.0, 1.0)
    target_probability = sample_ds["target_detection_probability"].values.astype(np.float32)
    target_positive = sample_ds["target_positive_observation_mask"].values.astype(np.uint8)
    metrics = evaluate_firms_next_day_prediction(
        prediction=prior,
        target_probability=target_probability,
        target_positive_mask=target_positive.astype(bool),
        threshold=threshold,
    )

    ds = xr.Dataset(
        data_vars={
            "physics_prior_probability": (["sample", "y", "x"], prior),
            "physics_prior_positive_mask": (
                ["sample", "y", "x"],
                (prior >= threshold).astype(np.uint8),
            ),
            "target_detection_probability": (["sample", "y", "x"], target_probability),
            "target_positive_observation_mask": (["sample", "y", "x"], target_positive),
            "input_detection_probability": (
                ["sample", "y", "x"],
                sample_ds["input_detection_probability"].values.astype(np.float32),
            ),
        },
        coords={
            "sample": sample_ds.coords["sample"].values,
            "reference_time": (["sample"], sample_ds.coords["reference_time"].values),
            "target_time": (["sample"], sample_ds.coords["target_time"].values),
            "y": sample_ds.coords["y"].values,
            "x": sample_ds.coords["x"].values,
        },
        attrs={
            "case_id": str(sample_ds.attrs["case_id"]),
            "case_name": str(sample_ds.attrs.get("case_name", "")),
            "prior_source": PHYSICS_PRIOR_NAME,
            "prior_type": "wind_aware_fuel_spread_probability",
            "source_sample_path": str(source_sample_path),
            "target_type": "active_fire_detection_probability",
            "target_semantics": "next_calendar_day_firms_positive_observation_evidence",
            "excludes_final_extent_as_input": "true",
            "not_hourly_perimeter_truth": "true",
            "threshold": float(threshold),
            "observed_brier_score": float(metrics["observed_brier_score"]),
            "observed_mae": float(metrics["observed_mae"]),
            "precision_at_threshold": float(metrics["precision_at_threshold"]),
            "recall_at_threshold": float(metrics["recall_at_threshold"]),
            "iou_at_threshold": float(metrics["iou_at_threshold"]),
            "predicted_positive_fraction": float(metrics["predicted_positive_fraction"]),
            "target_positive_fraction": float(metrics["target_positive_fraction"]),
            "creation_timestamp": datetime.utcnow().isoformat(),
        },
    )
    ds["physics_prior_probability"].attrs = {
        "description": "Phase 6 wind-aware physics prior aligned to FIRMS next-day samples."
    }
    return ds


def build_physics_prior_artifacts(
    sample_paths: list[Path],
    output_dir: Path,
    *,
    threshold: float = 0.05,
) -> list[PhysicsPriorArtifactSummary]:
    """Generate aligned physics-prior artifacts for FIRMS next-day sample paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[PhysicsPriorArtifactSummary] = []
    for sample_path in sample_paths:
        sample_ds = xr.open_zarr(sample_path)
        try:
            prior = wind_aware_fuel_spread_prior(sample_ds)
            target_probability = sample_ds["target_detection_probability"].values.astype(np.float32)
            target_positive = sample_ds["target_positive_observation_mask"].values.astype(bool)
            metrics = evaluate_firms_next_day_prediction(
                prior,
                target_probability,
                target_positive,
                threshold,
            )
            prior_ds = build_physics_prior_dataset(
                sample_ds=sample_ds,
                prior_probability=prior,
                source_sample_path=sample_path,
                threshold=threshold,
            )
            prior_attrs = dict(prior_ds.attrs)
            case_id = str(sample_ds.attrs["case_id"])
            output_path = output_dir / f"{case_id}_physics_prior.zarr"
            prior_ds.to_zarr(output_path, mode="w")
            prior_ds.close()

            summaries.append(
                PhysicsPriorArtifactSummary(
                    case_id=case_id,
                    output_path=str(output_path),
                    sample_count=int(sample_ds.sizes["sample"]),
                    grid_shape=f"{sample_ds.sizes['y']}x{sample_ds.sizes['x']}",
                    prior_source=PHYSICS_PRIOR_NAME,
                    threshold=threshold,
                    observed_brier_score=float(prior_attrs["observed_brier_score"]),
                    observed_mae=float(prior_attrs["observed_mae"]),
                    precision_at_threshold=float(prior_attrs["precision_at_threshold"]),
                    recall_at_threshold=float(prior_attrs["recall_at_threshold"]),
                    iou_at_threshold=float(prior_attrs["iou_at_threshold"]),
                    predicted_positive_fraction=float(prior_attrs["predicted_positive_fraction"]),
                    target_positive_fraction=float(prior_attrs["target_positive_fraction"]),
                    mean_prior_on_target_positive=float(
                        metrics["mean_prediction_on_target_positive"]
                    ),
                    mean_prior_on_unlabeled=float(metrics["mean_prediction_on_unlabeled"]),
                )
            )
        finally:
            sample_ds.close()
    return summaries


def render_physics_prior_report(summaries: list[PhysicsPriorArtifactSummary]) -> str:
    """Render a Markdown report for Phase 6 physics-prior artifacts."""
    lines = [
        "# FireTwin Phase 6 Physics-Prior Artifacts",
        "",
        "These artifacts provide sample-aligned physics-style priors for hybrid blending.",
        "They use same-day FIRMS evidence, cumulative history, fuel/terrain susceptibility and",
        "reference-time wind. They do not use final burned extent or next-day targets as inputs.",
        "",
        "| Case | Samples | Grid | Brier | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac | Artifact |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.case_id} | {summary.sample_count:,} | {summary.grid_shape} | "
            f"{summary.observed_brier_score:.5f} | {summary.observed_mae:.5f} | "
            f"{summary.precision_at_threshold:.3f} | {summary.recall_at_threshold:.3f} | "
            f"{summary.iou_at_threshold:.3f} | {summary.predicted_positive_fraction:.5f} | "
            f"{summary.target_positive_fraction:.5f} | `{summary.output_path}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- This is a prior field for Phase 6 hybrid experiments, not an operational spread forecast.",
            "- Metrics are against FIRMS positive-observation evidence, not verified perimeter growth.",
            "- The prior is deterministic and intentionally simple so the hybrid evaluation can compare",
            "  ML-only, physics-only and blended probabilities with matching tensor shapes.",
            "",
        ]
    )
    return "\n".join(lines)
