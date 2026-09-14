"""Evaluation metrics and benchmarking tools."""

from firetwin.evaluation.final_extent import (
    evaluate_final_extent_baselines,
    fuel_potential_mask,
    get_final_extent_target,
)
from firetwin.evaluation.firms_artifacts import (
    FIRMSArtifactValidationSummary,
    render_firms_artifact_validation_markdown,
    validate_firms_artifacts,
    write_firms_overlay_figure,
)
from firetwin.evaluation.firms_next_day import (
    FIRMSNextDayBaselineResult,
    evaluate_firms_next_day_baselines,
    evaluate_firms_next_day_prediction,
    fuel_terrain_prior,
    render_firms_next_day_baseline_report,
)
from firetwin.evaluation.metrics import (
    area_error,
    boundary_distance,
    dice_score,
    evaluate_forecast,
    iou_score,
)

__all__ = [
    "evaluate_final_extent_baselines",
    "iou_score",
    "dice_score",
    "boundary_distance",
    "area_error",
    "evaluate_forecast",
    "fuel_potential_mask",
    "get_final_extent_target",
    "FIRMSArtifactValidationSummary",
    "validate_firms_artifacts",
    "write_firms_overlay_figure",
    "render_firms_artifact_validation_markdown",
    "FIRMSNextDayBaselineResult",
    "evaluate_firms_next_day_baselines",
    "evaluate_firms_next_day_prediction",
    "fuel_terrain_prior",
    "render_firms_next_day_baseline_report",
]
