"""Final-extent evaluation helpers for real historical fire cases."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from firetwin.evaluation.metrics import evaluate_forecast
from firetwin.schemas import FireCase

M2_PER_ACRE = 4046.86


def get_final_extent_target(case: FireCase) -> np.ndarray:
    """Return the final burned extent target, refusing non-final-extent cases."""
    if case.metadata.target_type != "final_burned_extent":
        raise ValueError(
            "Final-extent evaluation requires target_type=final_burned_extent; "
            f"got {case.metadata.target_type!r}."
        )

    if not case.target_states:
        raise ValueError("Final-extent evaluation requires at least one target state.")

    return case.target_states[-1].burned.astype(bool)


def fuel_potential_mask(case: FireCase, quantile: float = 0.70) -> np.ndarray:
    """Build a fuel-only potential mask from load and moisture covariates.

    This is a spatial prior, not a forecast. It deliberately avoids using the target burned area.
    """
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("fuel potential quantile must be in [0, 1]")

    burnable = case.fuels.fuel_model > 0
    if not np.any(burnable):
        return np.zeros(case.grid_shape, dtype=bool)

    load = case.fuels.fuel_load_kg_m2.astype(float)
    moisture = np.clip(case.fuels.fuel_moisture_percent.astype(float), 0.0, None)
    potential = np.zeros(case.grid_shape, dtype=float)
    potential[burnable] = load[burnable] / (1.0 + moisture[burnable] / 100.0)

    threshold = float(np.quantile(potential[burnable], quantile))
    return burnable & (potential >= threshold)


def evaluate_final_extent_baselines(
    case: FireCase,
    fuel_potential_quantile: float = 0.70,
) -> list[dict[str, Any]]:
    """Evaluate simple non-temporal baselines against a final burned extent target."""
    target = get_final_extent_target(case)
    burnable = case.fuels.fuel_model > 0
    top_percent = int(round((1.0 - fuel_potential_quantile) * 100.0))

    baseline_masks = {
        "initial_state": case.initial_state.burned.astype(bool),
        "burnable_fuel_mask": burnable,
        f"top_fuel_potential_{top_percent}pct": fuel_potential_mask(
            case, quantile=fuel_potential_quantile
        ),
    }

    target_pixels = int(np.sum(target))
    target_area_m2 = float(target_pixels * case.resolution_m**2)
    target_area_acres = target_area_m2 / M2_PER_ACRE

    results: list[dict[str, Any]] = []
    for baseline_name, predicted in baseline_masks.items():
        metrics = evaluate_forecast(predicted, target, case.resolution_m)
        area = cast(dict[str, float], metrics["area"])
        predicted_area_m2 = float(area["predicted_area_m2"])
        relative_area_error = float(area["relative_error"])

        results.append(
            {
                "baseline": baseline_name,
                "target_type": case.metadata.target_type,
                "uses_target_area": False,
                "iou": float(cast(float, metrics["iou"])),
                "dice": float(cast(float, metrics["dice"])),
                "boundary_distance_mean_m": float(cast(float, metrics["boundary_distance_mean_m"])),
                "predicted_area_acres": predicted_area_m2 / M2_PER_ACRE,
                "target_area_acres": target_area_acres,
                "relative_area_error": relative_area_error,
                "predicted_fraction": float(np.mean(predicted)),
                "target_fraction": float(np.mean(target)),
            }
        )

    return results
