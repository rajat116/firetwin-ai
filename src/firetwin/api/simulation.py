"""Backend services for experimental simulation-surrogate inference."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from firetwin.models.surrogate import (
    SimulationScenarioControls,
    load_simulation_corpus_manifest,
    load_simulation_surrogate_model,
    predict_simulation_sample_with_controls,
)

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SIMULATION_CORPUS_DIR = DEFAULT_REPO_ROOT / "data/simulation/phase5b_synthetic_smoke"
DEFAULT_SIMULATION_MODEL_PATH = DEFAULT_REPO_ROOT / "data/models/phase5b_surrogate_development.npz"


class SimulationInferenceError(RuntimeError):
    """Raised when simulation-surrogate inference cannot be completed."""


@dataclass(frozen=True)
class SimulationScenarioRequest:
    """Validated request for experimental simulation-surrogate inference."""

    wind_speed_multiplier: float = 1.0
    wind_direction_delta_degrees: float = 0.0
    base_spread_rate_multiplier: float = 1.0
    threshold: float | None = None
    include_probability_grid: bool = False
    max_grid_size: int = 48

    def controls(self) -> SimulationScenarioControls:
        """Return model-layer controls after request validation."""
        if self.max_grid_size < 8 or self.max_grid_size > 128:
            raise ValueError("max_grid_size must be between 8 and 128")
        controls = SimulationScenarioControls(
            wind_speed_multiplier=self.wind_speed_multiplier,
            wind_direction_delta_degrees=self.wind_direction_delta_degrees,
            base_spread_rate_multiplier=self.base_spread_rate_multiplier,
            threshold=self.threshold,
        )
        controls.validate()
        return controls

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable request payload."""
        return asdict(self)


def list_simulation_samples(
    corpus_dir: Path = DEFAULT_SIMULATION_CORPUS_DIR,
) -> list[dict[str, Any]]:
    """Return public summaries for simulation-corpus samples."""
    manifest = _load_manifest(corpus_dir)
    return [
        {
            "case_id": sample["case_id"],
            "grid_shape": sample["grid_shape"],
            "resolution_m": sample["resolution_m"],
            "forecast_hours": sample["forecast_hours"],
            "initial_burned_cells": sample["initial_burned_cells"],
            "final_burned_cells": sample["final_burned_cells"],
            "wind_speed_m_s": sample["wind_speed_m_s"],
            "wind_direction_degrees": sample["wind_direction_degrees"],
            "base_spread_rate_m_h": sample["base_spread_rate_m_h"],
        }
        for sample in manifest["samples"]
    ]


def build_simulation_scenario_response(
    *,
    case_id: str,
    request: SimulationScenarioRequest | None = None,
    corpus_dir: Path = DEFAULT_SIMULATION_CORPUS_DIR,
    model_path: Path = DEFAULT_SIMULATION_MODEL_PATH,
) -> dict[str, Any]:
    """Run artifact-backed simulation-surrogate inference for one sample and controls."""
    request = request or SimulationScenarioRequest()
    controls = request.controls()
    manifest = _load_manifest(corpus_dir)
    sample_meta = _sample_metadata(manifest, case_id)
    sample_path = corpus_dir / str(sample_meta["artifact"])
    if not sample_path.is_file():
        raise SimulationInferenceError(f"Simulation sample artifact not found: {sample_path}")
    if not model_path.is_file():
        raise SimulationInferenceError(f"Simulation surrogate model not found: {model_path}")

    model = load_simulation_surrogate_model(model_path)
    prediction = predict_simulation_sample_with_controls(model, sample_path, controls)
    threshold = controls.threshold if controls.threshold is not None else model.threshold
    summary = _prediction_summary(prediction=prediction, threshold=threshold)
    response: dict[str, Any] = {
        "case_id": case_id,
        "forecast_mode": "simulation_surrogate_on_demand",
        "model_name": model.model_name,
        "model_path": _relative_to_repo(model_path),
        "corpus_dir": _relative_to_repo(corpus_dir),
        "target_type": manifest["target"],
        "not_operational": True,
        "simulator_truth": False,
        "controls": controls.to_dict(),
        "threshold": threshold,
        "grid_shape": sample_meta["grid_shape"],
        "resolution_m": sample_meta["resolution_m"],
        "forecast_hours": sample_meta["forecast_hours"],
        "summary": summary,
        "guardrails": [
            "Experimental simulator-trained surrogate inference, not observed wildfire truth.",
            "Controls recompute surrogate probabilities from scenario covariates; they do not run a full physics simulator.",
            "Not for operational wildfire response, evacuation planning or safety-critical decisions.",
        ],
    }
    if request.include_probability_grid:
        response["probability_grid"] = _downsample_prediction(
            prediction,
            max_grid_size=request.max_grid_size,
        )
    return response


def _load_manifest(corpus_dir: Path) -> dict[str, Any]:
    try:
        return load_simulation_corpus_manifest(corpus_dir)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        raise SimulationInferenceError(str(exc)) from exc


def _sample_metadata(manifest: dict[str, Any], case_id: str) -> dict[str, Any]:
    for sample in manifest.get("samples", []):
        if sample.get("case_id") == case_id:
            return cast(dict[str, Any], sample)
    raise SimulationInferenceError(f"Unknown simulation sample: {case_id}")


def _prediction_summary(*, prediction: np.ndarray, threshold: float) -> dict[str, Any]:
    predicted = prediction >= threshold
    return {
        "peak_probability": float(np.max(prediction)),
        "mean_probability": float(np.mean(prediction)),
        "predicted_positive_fraction": float(np.mean(predicted)),
        "per_horizon": [
            {
                "horizon_index": index,
                "peak_probability": float(np.max(probability)),
                "mean_probability": float(np.mean(probability)),
                "predicted_positive_fraction": float(np.mean(predicted[index])),
            }
            for index, probability in enumerate(prediction)
        ],
    }


def _downsample_prediction(
    prediction: np.ndarray, *, max_grid_size: int
) -> list[list[list[float]]]:
    _, height, width = prediction.shape
    stride = max(1, int(np.ceil(max(height, width) / max_grid_size)))
    downsampled = prediction[:, ::stride, ::stride]
    return cast(list[list[list[float]]], np.round(downsampled, decimals=4).tolist())


def _relative_to_repo(path: Path) -> str:
    try:
        return path.relative_to(DEFAULT_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
