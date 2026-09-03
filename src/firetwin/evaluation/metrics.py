"""Evaluation metrics for fire spread forecasts."""

import numpy as np
from scipy import ndimage


def iou_score(predicted: np.ndarray, target: np.ndarray) -> float:
    """Calculate Intersection over Union (IoU/Jaccard index).

    Args:
        predicted: Binary prediction mask
        target: Binary ground truth mask

    Returns:
        IoU score in [0, 1]
    """
    intersection = np.logical_and(predicted, target).sum()
    union = np.logical_or(predicted, target).sum()

    if union == 0:
        return 1.0 if intersection == 0 else 0.0

    return float(intersection / union)


def dice_score(predicted: np.ndarray, target: np.ndarray) -> float:
    """Calculate Dice coefficient (F1 score for binary masks).

    Args:
        predicted: Binary prediction mask
        target: Binary ground truth mask

    Returns:
        Dice score in [0, 1]
    """
    intersection = np.logical_and(predicted, target).sum()
    total = predicted.sum() + target.sum()

    if total == 0:
        return 1.0 if intersection == 0 else 0.0

    return float(2 * intersection / total)


def boundary_distance(
    predicted: np.ndarray, target: np.ndarray, resolution_m: float
) -> dict[str, float]:
    """Calculate boundary distance metrics.

    Measures how far predicted perimeter is from true perimeter.

    Args:
        predicted: Binary prediction mask
        target: Binary ground truth mask
        resolution_m: Grid resolution in meters

    Returns:
        Dictionary with mean, max, and median boundary distances in meters
    """
    # Find boundaries
    pred_boundary = predicted & ~ndimage.binary_erosion(predicted)
    target_boundary = target & ~ndimage.binary_erosion(target)

    if not pred_boundary.any() or not target_boundary.any():
        return {"mean_m": 0.0, "max_m": 0.0, "median_m": 0.0}

    # Distance transform from target boundary
    dist_from_target = ndimage.distance_transform_edt(~target_boundary)

    # Sample distances at predicted boundary points
    distances_cells = dist_from_target[pred_boundary]
    distances_m = distances_cells * resolution_m

    return {
        "mean_m": float(np.mean(distances_m)),
        "max_m": float(np.max(distances_m)),
        "median_m": float(np.median(distances_m)),
    }


def area_error(predicted: np.ndarray, target: np.ndarray, resolution_m: float) -> dict[str, float]:
    """Calculate area-based errors.

    Args:
        predicted: Binary prediction mask
        target: Binary ground truth mask
        resolution_m: Grid resolution in meters

    Returns:
        Dictionary with absolute and relative area errors
    """
    pred_area_m2 = float(predicted.sum() * resolution_m**2)
    target_area_m2 = float(target.sum() * resolution_m**2)

    abs_error_m2 = pred_area_m2 - target_area_m2
    rel_error = abs_error_m2 / target_area_m2 if target_area_m2 > 0 else 0.0

    return {
        "predicted_area_m2": pred_area_m2,
        "target_area_m2": target_area_m2,
        "absolute_error_m2": abs_error_m2,
        "relative_error": rel_error,
        "overestimate": abs_error_m2 > 0,
    }


def evaluate_forecast(
    predicted: np.ndarray, target: np.ndarray, resolution_m: float
) -> dict[str, float | dict[str, float]]:
    """Calculate all evaluation metrics for a forecast.

    Args:
        predicted: Binary prediction mask
        target: Binary ground truth mask
        resolution_m: Grid resolution in meters

    Returns:
        Dictionary with all metrics
    """
    metrics: dict[str, float | dict[str, float]] = {
        "iou": iou_score(predicted, target),
        "dice": dice_score(predicted, target),
    }

    boundary_metrics = boundary_distance(predicted, target, resolution_m)
    metrics["boundary_distance_mean_m"] = boundary_metrics["mean_m"]
    metrics["boundary_distance_max_m"] = boundary_metrics["max_m"]
    metrics["boundary_distance_median_m"] = boundary_metrics["median_m"]

    area_metrics = area_error(predicted, target, resolution_m)
    metrics["area"] = area_metrics

    return metrics
