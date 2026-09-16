"""Explorer-ready exports for learned FIRMS next-day forecast artifacts."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.evaluation.firms_forecasts import evaluate_forecast_artifact

EXPLORER_SCHEMA_VERSION = "firetwin.firms_next_day_explorer.v1"
FORECAST_SEMANTICS = "next_calendar_day_firms_active_fire_detection_probability"
TARGET_TYPE = "active_fire_detection_probability"

EXPLORER_GUARDRAILS = [
    "Research prototype; not for operational wildfire response, evacuation planning or safety-critical decisions.",
    "Forecasts estimate satellite-visible FIRMS active-fire evidence, not exact burned perimeter spread.",
    "Cells without FIRMS detections are no-positive-evidence cells, not confirmed unburned cells.",
    "Recommended thresholds are display diagnostics, not emergency decision thresholds.",
]

_CASE_NAMES = {spec.case_id: f"{spec.fire.name} ({spec.fire.year})" for spec in PILOT_LABEL_SPECS}


@dataclass(frozen=True)
class ExplorerCaseExport:
    """Manifest entry for one Explorer-ready forecast preview."""

    case_id: str
    case_name: str
    forecast_artifact: str
    preview_png: str
    sample_index: int
    selection_rule: str
    reference_time: str
    target_time: str
    grid_shape: dict[str, int]
    grid_crs: str
    bbox: dict[str, float]
    resolution_m: float | None
    recommended_threshold: float
    observed_brier_score: float
    persistence_brier_score: float
    brier_improvement_vs_persistence: float
    expected_calibration_error: float
    recommended_f1_score: float
    recommended_precision: float
    recommended_recall: float
    sample_peak_probability: float
    sample_mean_probability: float
    sample_predicted_positive_fraction: float
    sample_target_positive_fraction: float
    target_type: str = TARGET_TYPE
    forecast_semantics: str = FORECAST_SEMANTICS

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable manifest entry."""
        return asdict(self)


def select_peak_forecast_sample(forecast_probability: np.ndarray) -> int:
    """Choose the sample with the largest forecast probability mass."""
    probability = np.asarray(forecast_probability, dtype=np.float32)
    if probability.ndim != 3:
        raise ValueError("forecast_probability must have shape (sample, y, x)")
    if probability.shape[0] == 0:
        raise ValueError("forecast_probability must contain at least one sample")

    risk_mass = np.sum(np.clip(probability, 0.0, 1.0), axis=(1, 2))
    return int(np.argmax(risk_mass))


def build_explorer_manifest(exports: list[ExplorerCaseExport]) -> dict[str, Any]:
    """Build the top-level Explorer manifest."""
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": EXPLORER_SCHEMA_VERSION,
        "generated_at": generated_at,
        "target_type": TARGET_TYPE,
        "forecast_semantics": FORECAST_SEMANTICS,
        "not_operational": True,
        "guardrails": EXPLORER_GUARDRAILS,
        "cases": [export.to_dict() for export in exports],
    }


def export_forecast_artifact_for_explorer(
    forecast_path: Path,
    *,
    figure_dir: Path,
) -> ExplorerCaseExport:
    """Export one learned forecast artifact to a small Explorer preview asset."""
    diagnostic = evaluate_forecast_artifact(forecast_path)
    summary = diagnostic.summary

    ds = xr.open_zarr(forecast_path)
    try:
        case_id = str(ds.attrs["case_id"])
        probability = ds["forecast_probability"].values.astype(np.float32)
        target_probability = ds["target_detection_probability"].values.astype(np.float32)
        target_positive = ds["target_positive_observation_mask"].values.astype(bool)
        sample_index = select_peak_forecast_sample(probability)
        threshold = summary.recommended_threshold
        sample_probability = np.clip(probability[sample_index], 0.0, 1.0)
        sample_target_probability = np.clip(target_probability[sample_index], 0.0, 1.0)
        sample_target_positive = target_positive[sample_index]

        preview_path = figure_dir / f"{case_id}_explorer_forecast_preview.png"
        write_explorer_preview_png(
            probability=sample_probability,
            target_positive=sample_target_positive,
            threshold=threshold,
            output_path=preview_path,
            title=f"{_case_name(ds)} forecast preview",
        )

        return ExplorerCaseExport(
            case_id=case_id,
            case_name=_case_name(ds),
            forecast_artifact=forecast_path.as_posix(),
            preview_png=preview_path.as_posix(),
            sample_index=sample_index,
            selection_rule="peak_forecast_probability_mass",
            reference_time=_sample_coord_as_text(ds, "reference_time", sample_index),
            target_time=_sample_coord_as_text(ds, "target_time", sample_index),
            grid_shape={"height": int(ds.sizes["y"]), "width": int(ds.sizes["x"])},
            grid_crs=str(ds.attrs.get("grid_crs", "unknown")),
            bbox=_bbox_from_attrs(ds),
            resolution_m=_optional_float_attr(ds, "resolution_m"),
            recommended_threshold=threshold,
            observed_brier_score=summary.observed_brier_score,
            persistence_brier_score=float(ds.attrs["persistence_brier_score"]),
            brier_improvement_vs_persistence=float(ds.attrs["brier_improvement_vs_persistence"]),
            expected_calibration_error=summary.expected_calibration_error,
            recommended_f1_score=summary.recommended_f1_score,
            recommended_precision=summary.recommended_precision,
            recommended_recall=summary.recommended_recall,
            sample_peak_probability=float(np.max(sample_probability)),
            sample_mean_probability=float(np.mean(sample_probability)),
            sample_predicted_positive_fraction=float(np.mean(sample_probability >= threshold)),
            sample_target_positive_fraction=float(np.mean(sample_target_probability > 0.0)),
        )
    finally:
        ds.close()


def export_firms_next_day_explorer_assets(
    *,
    forecast_paths: list[Path],
    manifest_path: Path,
    figure_dir: Path,
    report_path: Path | None = None,
) -> list[ExplorerCaseExport]:
    """Export forecast previews and a JSON manifest for the public Explorer."""
    if not forecast_paths:
        raise ValueError("At least one forecast path is required")

    exports = [
        export_forecast_artifact_for_explorer(path, figure_dir=figure_dir)
        for path in forecast_paths
    ]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(build_explorer_manifest(exports), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            render_explorer_export_report(exports, manifest_path=manifest_path),
            encoding="utf-8",
        )
    return exports


def render_explorer_export_report(
    exports: list[ExplorerCaseExport],
    *,
    manifest_path: Path,
) -> str:
    """Render a Markdown report for Explorer preview assets."""
    lines = [
        "# FireTwin FIRMS Next-Day Explorer Assets",
        "",
        "This report documents Explorer-ready lightweight assets generated from learned next-day FIRMS forecast artifacts.",
        "The assets are intended for a future public Explorer UI and preserve the same scientific guardrails as the model reports.",
        "",
        f"- Manifest: `{manifest_path.as_posix()}`",
        f"- Schema: `{EXPLORER_SCHEMA_VERSION}`",
        f"- Target: `{TARGET_TYPE}`",
        "",
        "| Case | Sample | Reference time | Target time | Threshold | Brier | Persistence Brier | Brier improvement | ECE | Peak probability | Predicted + frac | Target + frac | Preview |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for export in exports:
        lines.append(
            f"| {export.case_id} | {export.sample_index} | {export.reference_time} | "
            f"{export.target_time} | {export.recommended_threshold:.3f} | "
            f"{export.observed_brier_score:.5f} | {export.persistence_brier_score:.5f} | "
            f"{export.brier_improvement_vs_persistence:+.5f} | "
            f"{export.expected_calibration_error:.5f} | "
            f"{export.sample_peak_probability:.3f} | "
            f"{export.sample_predicted_positive_fraction:.5f} | "
            f"{export.sample_target_positive_fraction:.5f} | `{export.preview_png}` |"
        )

    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {guardrail}" for guardrail in EXPLORER_GUARDRAILS)
    lines.append("")
    return "\n".join(lines)


def write_explorer_preview_png(
    *,
    probability: np.ndarray,
    target_positive: np.ndarray,
    threshold: float,
    output_path: Path,
    title: str,
) -> None:
    """Write a compact PNG preview for one forecast sample."""
    _configure_plot_cache()
    import matplotlib.pyplot as plt

    probability = np.clip(np.asarray(probability, dtype=np.float32), 0.0, 1.0)
    target_positive = np.asarray(target_positive, dtype=bool)
    if probability.shape != target_positive.shape:
        raise ValueError("probability and target_positive must have the same shape")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    display_max = max(0.10, float(np.nanpercentile(probability, 99.5)), threshold * 2.0)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    fig.suptitle(title, fontsize=12)

    probability_image = axes[0].imshow(
        probability,
        cmap="inferno",
        vmin=0.0,
        vmax=display_max,
        interpolation="nearest",
    )
    axes[0].set_title("Forecast probability")
    fig.colorbar(probability_image, ax=axes[0], fraction=0.046, pad=0.04)

    axes[1].imshow(probability >= threshold, cmap="Reds", interpolation="nearest")
    axes[1].set_title(f"Forecast >= {threshold:.3f}")

    axes[2].imshow(target_positive, cmap="Greys", interpolation="nearest")
    axes[2].set_title("Next-day FIRMS evidence")

    for axis in axes:
        axis.set_xticks([])
        axis.set_yticks([])

    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _configure_plot_cache() -> None:
    """Keep matplotlib cache writes inside a predictable temporary directory."""
    cache_root = Path(os.environ.get("FIRETWIN_PLOT_CACHE", "/tmp/firetwin_plot_cache"))
    matplotlib_cache = cache_root / "matplotlib"
    xdg_cache = cache_root / "xdg"
    matplotlib_cache.mkdir(parents=True, exist_ok=True)
    xdg_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))
    os.environ.setdefault("XDG_CACHE_HOME", str(xdg_cache))


def _case_name(ds: xr.Dataset) -> str:
    case_id = str(ds.attrs["case_id"])
    return str(ds.attrs.get("case_name", _CASE_NAMES.get(case_id, case_id)))


def _sample_coord_as_text(ds: xr.Dataset, name: str, sample_index: int) -> str:
    if name not in ds.coords:
        return "unknown"
    value = ds.coords[name].values[sample_index]
    if np.issubdtype(np.asarray(value).dtype, np.datetime64):
        return str(np.datetime_as_string(value, unit="s"))
    return str(value)


def _bbox_from_attrs(ds: xr.Dataset) -> dict[str, float]:
    keys = ("bbox_min_x", "bbox_min_y", "bbox_max_x", "bbox_max_y")
    if not all(key in ds.attrs for key in keys):
        return {}
    return {key: float(ds.attrs[key]) for key in keys}


def _optional_float_attr(ds: xr.Dataset, name: str) -> float | None:
    if name not in ds.attrs:
        return None
    return float(ds.attrs[name])
