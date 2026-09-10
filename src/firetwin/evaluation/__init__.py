"""Evaluation metrics and benchmarking tools."""

from firetwin.evaluation.final_extent import (
    evaluate_final_extent_baselines,
    fuel_potential_mask,
    get_final_extent_target,
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
]
