"""Validation and visualization helpers for FIRMS companion artifacts."""

from __future__ import annotations

import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


@dataclass(frozen=True)
class FIRMSArtifactValidationSummary:
    """Validation summary for one pilot fire's FIRMS companion artifacts."""

    case_id: str
    case_path: str
    progression_path: str
    initial_state_path: str
    figure_path: str
    final_burned_cells: int
    progression_positive_cells: int
    progression_overlap_cells: int
    progression_outside_final_cells: int
    progression_precision_vs_final: float
    progression_recall_vs_final: float
    progression_iou_vs_final: float
    initial_active_cells: int
    initial_overlap_cells: int
    initial_outside_final_cells: int
    initial_precision_vs_final: float
    initial_recall_vs_final: float
    initial_iou_vs_final: float
    progression_time_slices: int
    initial_window_detection_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


def _safe_ratio(numerator: int, denominator: int) -> float:
    """Return a stable ratio for sparse masks."""
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _read_final_burned_mask(case_path: Path) -> tuple[str, np.ndarray]:
    """Load the final burned extent mask from a FireCase Zarr."""
    ds = xr.open_zarr(case_path)
    try:
        if ds.attrs.get("target_type") != "final_burned_extent":
            raise ValueError(
                f"{case_path} must have target_type=final_burned_extent; "
                f"got {ds.attrs.get('target_type')!r}"
            )
        if "burned" not in ds or "time" not in ds["burned"].dims:
            raise ValueError(f"{case_path} does not contain a time-varying burned array")

        case_id = str(ds.attrs.get("case_id") or case_path.stem)
        final_burned = ds["burned"].isel(time=-1).values.astype(bool)
        return case_id, final_burned
    finally:
        ds.close()


def _read_progression_mask(progression_path: Path) -> tuple[np.ndarray, int]:
    """Load the cumulative positive FIRMS progression mask."""
    ds = xr.open_zarr(progression_path)
    try:
        if ds.attrs.get("target_type") != "active_fire_detection_probability":
            raise ValueError(
                f"{progression_path} must target active_fire_detection_probability; "
                f"got {ds.attrs.get('target_type')!r}"
            )
        if "cumulative_detection_probability" in ds:
            mask = ds["cumulative_detection_probability"].isel(time=-1).values > 0.0
        elif "positive_observation_mask" in ds:
            mask = ds["positive_observation_mask"].any(dim="time").values.astype(bool)
        else:
            raise ValueError(
                f"{progression_path} must contain cumulative_detection_probability "
                "or positive_observation_mask"
            )
        return mask.astype(bool), int(ds.sizes.get("time", 0))
    finally:
        ds.close()


def _read_initial_state_mask(initial_state_path: Path) -> tuple[np.ndarray, int]:
    """Load the initial active-front mask from a FIRMS initial-state artifact."""
    ds = xr.open_zarr(initial_state_path)
    try:
        if ds.attrs.get("target_type") != "initial_active_fire_state":
            raise ValueError(
                f"{initial_state_path} must target initial_active_fire_state; "
                f"got {ds.attrs.get('target_type')!r}"
            )
        if ds.attrs.get("uses_final_extent_for_qc") != "false":
            raise ValueError(f"{initial_state_path} must not use final extent for QC")
        if "initial_active_front" not in ds:
            raise ValueError(f"{initial_state_path} is missing initial_active_front")

        mask = ds["initial_active_front"].values.astype(bool)
        window_detection_count = int(ds.attrs.get("window_detection_count", 0))
        return mask, window_detection_count
    finally:
        ds.close()


def _overlap_metrics(predicted: np.ndarray, target: np.ndarray) -> dict[str, int | float]:
    """Compute overlap diagnostics without treating FIRMS masks as ground-truth perimeters."""
    predicted_bool = predicted.astype(bool)
    target_bool = target.astype(bool)
    overlap = predicted_bool & target_bool
    outside = predicted_bool & ~target_bool
    union = predicted_bool | target_bool

    predicted_cells = int(np.sum(predicted_bool))
    target_cells = int(np.sum(target_bool))
    overlap_cells = int(np.sum(overlap))
    outside_cells = int(np.sum(outside))
    union_cells = int(np.sum(union))

    return {
        "predicted_cells": predicted_cells,
        "target_cells": target_cells,
        "overlap_cells": overlap_cells,
        "outside_cells": outside_cells,
        "precision_vs_final": _safe_ratio(overlap_cells, predicted_cells),
        "recall_vs_final": _safe_ratio(overlap_cells, target_cells),
        "iou_vs_final": _safe_ratio(overlap_cells, union_cells),
    }


def validate_firms_artifacts(
    case_path: Path,
    progression_path: Path,
    initial_state_path: Path,
    figure_path: Path | None = None,
) -> FIRMSArtifactValidationSummary:
    """Validate FIRMS label and initial-state artifacts against final extent context."""
    case_id, final_burned = _read_final_burned_mask(case_path)
    progression_mask, progression_time_slices = _read_progression_mask(progression_path)
    initial_mask, initial_window_detection_count = _read_initial_state_mask(initial_state_path)

    if progression_mask.shape != final_burned.shape:
        raise ValueError(
            f"Progression artifact shape {progression_mask.shape} does not match "
            f"final extent shape {final_burned.shape}"
        )
    if initial_mask.shape != final_burned.shape:
        raise ValueError(
            f"Initial-state artifact shape {initial_mask.shape} does not match "
            f"final extent shape {final_burned.shape}"
        )

    progression_metrics = _overlap_metrics(progression_mask, final_burned)
    initial_metrics = _overlap_metrics(initial_mask, final_burned)

    if figure_path is not None:
        write_firms_overlay_figure(
            final_burned=final_burned,
            progression_mask=progression_mask,
            initial_mask=initial_mask,
            case_id=case_id,
            output_path=figure_path,
        )

    return FIRMSArtifactValidationSummary(
        case_id=case_id,
        case_path=str(case_path),
        progression_path=str(progression_path),
        initial_state_path=str(initial_state_path),
        figure_path=str(figure_path) if figure_path is not None else "",
        final_burned_cells=int(np.sum(final_burned)),
        progression_positive_cells=int(progression_metrics["predicted_cells"]),
        progression_overlap_cells=int(progression_metrics["overlap_cells"]),
        progression_outside_final_cells=int(progression_metrics["outside_cells"]),
        progression_precision_vs_final=float(progression_metrics["precision_vs_final"]),
        progression_recall_vs_final=float(progression_metrics["recall_vs_final"]),
        progression_iou_vs_final=float(progression_metrics["iou_vs_final"]),
        initial_active_cells=int(initial_metrics["predicted_cells"]),
        initial_overlap_cells=int(initial_metrics["overlap_cells"]),
        initial_outside_final_cells=int(initial_metrics["outside_cells"]),
        initial_precision_vs_final=float(initial_metrics["precision_vs_final"]),
        initial_recall_vs_final=float(initial_metrics["recall_vs_final"]),
        initial_iou_vs_final=float(initial_metrics["iou_vs_final"]),
        progression_time_slices=progression_time_slices,
        initial_window_detection_count=initial_window_detection_count,
    )


def write_firms_overlay_figure(
    final_burned: np.ndarray,
    progression_mask: np.ndarray,
    initial_mask: np.ndarray,
    case_id: str,
    output_path: Path,
) -> None:
    """Write a compact overlay image for human inspection."""
    os.environ.setdefault(
        "MPLCONFIGDIR",
        str(Path(tempfile.gettempdir()) / "firetwin-matplotlib"),
    )

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.5, 7.5), constrained_layout=True)
    ax.imshow(final_burned, cmap="Greys", alpha=0.35, interpolation="nearest")
    ax.imshow(
        np.ma.masked_where(~progression_mask, progression_mask),
        cmap="autumn",
        alpha=0.55,
        interpolation="nearest",
    )
    ax.imshow(
        np.ma.masked_where(~initial_mask, initial_mask),
        cmap="winter",
        alpha=0.85,
        interpolation="nearest",
    )
    ax.set_title(f"{case_id}: FIRMS artifacts vs final extent")
    ax.set_axis_off()
    ax.legend(
        handles=[
            mpatches.Patch(color="0.45", alpha=0.35, label="Final burned extent"),
            mpatches.Patch(color="#ff8c00", alpha=0.55, label="Cumulative FIRMS positives"),
            mpatches.Patch(color="#0077bb", alpha=0.85, label="Initial active state"),
        ],
        loc="lower left",
        frameon=True,
    )
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def render_firms_artifact_validation_markdown(
    summaries: list[FIRMSArtifactValidationSummary],
) -> str:
    """Render FIRMS artifact validation summaries as Markdown."""
    lines = [
        "# FireTwin FIRMS Artifact Validation",
        "",
        "This report compares FIRMS companion artifacts with the final burned extent for context.",
        "The overlap values are diagnostics only; FIRMS detections remain observation evidence, not exact perimeter truth.",
        "",
        "| Case | Final cells | FIRMS cumulative cells | FIRMS overlap | FIRMS precision | FIRMS recall | Initial cells | Initial overlap | Initial precision | Initial recall | Figure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.case_id} | {summary.final_burned_cells:,} | "
            f"{summary.progression_positive_cells:,} | "
            f"{summary.progression_overlap_cells:,} | "
            f"{summary.progression_precision_vs_final:.3f} | "
            f"{summary.progression_recall_vs_final:.3f} | "
            f"{summary.initial_active_cells:,} | {summary.initial_overlap_cells:,} | "
            f"{summary.initial_precision_vs_final:.3f} | "
            f"{summary.initial_recall_vs_final:.3f} | "
            f"`{summary.figure_path}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- Precision here means the fraction of FIRMS-positive cells that fall inside final extent.",
            "- Recall here means the fraction of final burned cells touched by FIRMS-positive evidence.",
            "- FIRMS non-detections remain missing/unobserved, not confirmed unburned.",
            "- Initial-state overlays use earliest-window FIRMS evidence and do not use final extent for QC.",
            "",
        ]
    )
    return "\n".join(lines)
