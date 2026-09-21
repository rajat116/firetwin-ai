"""Lightweight surrogate model for Phase 5B simulation-corpus artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

SIMULATION_SURROGATE_MODEL_NAME = "phase5b_logistic_simulation_surrogate_v1"

FEATURE_NAMES = [
    "initial_burned",
    "fuel_model",
    "fuel_load_kg_m2",
    "fuel_moisture_percent",
    "slope_degrees",
    "elevation_m",
    "aspect_sin",
    "aspect_cos",
    "horizon_hours",
    "wind_speed_m_s",
    "wind_direction_sin",
    "wind_direction_cos",
    "temperature_c",
    "relative_humidity_percent",
    "base_spread_rate_m_h",
    "x_along_fire_m",
    "y_along_fire_m",
    "crosswind_distance_m",
    "distance_to_initial_m",
    "head_capacity_m",
    "flank_capacity_m",
    "back_capacity_m",
    "is_downwind",
]


@dataclass(frozen=True)
class SimulationSurrogateModel:
    """Small NumPy logistic surrogate for simulator-derived burned masks."""

    feature_mean: np.ndarray
    feature_scale: np.ndarray
    weights: np.ndarray
    bias: float
    threshold: float
    feature_names: tuple[str, ...] = tuple(FEATURE_NAMES)
    model_name: str = SIMULATION_SURROGATE_MODEL_NAME

    def predict_probability(self, features: np.ndarray) -> np.ndarray:
        """Predict burned probability for feature rows."""
        standardized = (features.astype(np.float32) - self.feature_mean) / self.feature_scale
        logits = np.clip(standardized @ self.weights + self.bias, -50.0, 50.0)
        return cast(np.ndarray, (1.0 / (1.0 + np.exp(-logits))).astype(np.float32))


@dataclass(frozen=True)
class SimulationSurrogateEvaluation:
    """Evaluation metrics for one held-out simulation sample."""

    case_id: str
    training_cases: int
    cell_count: int
    threshold: float
    brier_score: float
    persistence_brier_score: float
    brier_improvement_vs_persistence: float
    precision: float
    recall: float
    iou: float
    target_positive_fraction: float
    predicted_positive_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable evaluation row."""
        return asdict(self)


@dataclass(frozen=True)
class SimulationSurrogateTrainingSummary:
    """Summary for a trained surrogate artifact and evaluation run."""

    model_name: str
    corpus_dir: str
    model_path: str
    sample_count: int
    feature_count: int
    threshold: float
    mean_brier_score: float
    mean_persistence_brier_score: float
    mean_brier_improvement_vs_persistence: float
    mean_iou: float
    mean_precision: float
    mean_recall: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable training summary."""
        return asdict(self)


@dataclass(frozen=True)
class SimulationScenarioControls:
    """Scenario controls applied before surrogate inference."""

    wind_speed_multiplier: float = 1.0
    wind_direction_delta_degrees: float = 0.0
    base_spread_rate_multiplier: float = 1.0
    threshold: float | None = None

    def validate(self) -> None:
        """Validate scenario-control bounds for experimental inference."""
        if not 0.2 <= self.wind_speed_multiplier <= 3.0:
            raise ValueError("wind_speed_multiplier must be between 0.2 and 3.0")
        if not -180.0 <= self.wind_direction_delta_degrees <= 180.0:
            raise ValueError("wind_direction_delta_degrees must be between -180 and 180")
        if not 0.2 <= self.base_spread_rate_multiplier <= 3.0:
            raise ValueError("base_spread_rate_multiplier must be between 0.2 and 3.0")
        if self.threshold is not None and not 0.05 <= self.threshold <= 0.95:
            raise ValueError("threshold must be between 0.05 and 0.95")

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable controls payload."""
        return asdict(self)


def load_simulation_corpus_manifest(corpus_dir: Path) -> dict[str, Any]:
    """Load a Phase 5B simulation-corpus manifest."""
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def sample_paths_from_manifest(corpus_dir: Path) -> list[Path]:
    """Return simulation sample artifact paths from a corpus manifest."""
    manifest = load_simulation_corpus_manifest(corpus_dir)
    samples = manifest.get("samples", [])
    if not samples:
        raise ValueError("Simulation corpus manifest has no samples")
    paths = [corpus_dir / sample["artifact"] for sample in samples]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing[0])
    return paths


def train_simulation_surrogate(
    sample_paths: list[Path],
    *,
    random_seed: int = 42,
    max_cells_per_horizon: int = 12_000,
    negative_ratio: int = 3,
    epochs: int = 80,
    learning_rate: float = 0.08,
) -> SimulationSurrogateModel:
    """Train a lightweight logistic surrogate from simulation NPZ samples."""
    if not sample_paths:
        raise ValueError("At least one simulation sample is required")
    if max_cells_per_horizon <= 0:
        raise ValueError("max_cells_per_horizon must be positive")
    if negative_ratio <= 0:
        raise ValueError("negative_ratio must be positive")

    rng = np.random.default_rng(random_seed)
    features: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    for path in sample_paths:
        with np.load(path) as sample:
            horizon_count = int(sample["forecast_burned"].shape[0])
            for horizon_index in range(horizon_count):
                selected = _sample_cell_indices(
                    sample["forecast_burned"][horizon_index].astype(bool).ravel(),
                    rng=rng,
                    max_cells=max_cells_per_horizon,
                    negative_ratio=negative_ratio,
                )
                features.append(_feature_matrix(sample, horizon_index, selected))
                targets.append(sample["forecast_burned"][horizon_index].ravel()[selected])

    x_train = np.vstack(features).astype(np.float32)
    y_train = np.concatenate(targets).astype(np.float32)
    feature_mean = x_train.mean(axis=0).astype(np.float32)
    feature_scale = x_train.std(axis=0).astype(np.float32)
    feature_scale = np.where(feature_scale < 1e-6, 1.0, feature_scale).astype(np.float32)
    x_train = ((x_train - feature_mean) / feature_scale).astype(np.float32)

    weights = np.zeros(x_train.shape[1], dtype=np.float32)
    positive_fraction = float(np.clip(y_train.mean(), 1e-6, 1.0 - 1e-6))
    bias = float(np.log(positive_fraction / (1.0 - positive_fraction)))
    l2_penalty = 1e-4
    for epoch in range(epochs):
        order = rng.permutation(y_train.size)
        epoch_rate = learning_rate / np.sqrt(epoch + 1.0)
        for start in range(0, y_train.size, 65_536):
            batch_indices = order[start : start + 65_536]
            batch_x = x_train[batch_indices]
            batch_y = y_train[batch_indices]
            probabilities = 1.0 / (1.0 + np.exp(-np.clip(batch_x @ weights + bias, -50.0, 50.0)))
            error = probabilities - batch_y
            gradient = batch_x.T @ error / batch_y.size + l2_penalty * weights
            weights -= epoch_rate * gradient.astype(np.float32)
            bias -= epoch_rate * float(error.mean())

    training_probabilities = 1.0 / (1.0 + np.exp(-np.clip(x_train @ weights + bias, -50.0, 50.0)))
    return SimulationSurrogateModel(
        feature_mean=feature_mean,
        feature_scale=feature_scale,
        weights=weights.astype(np.float32),
        bias=bias,
        threshold=_best_iou_threshold(training_probabilities, y_train.astype(bool)),
    )


def predict_simulation_sample(
    model: SimulationSurrogateModel,
    sample_path: Path,
) -> np.ndarray:
    """Predict burned probability masks for every horizon in one simulation sample."""
    with np.load(sample_path) as sample:
        return _predict_loaded_simulation_sample(model, sample)


def predict_simulation_sample_with_controls(
    model: SimulationSurrogateModel,
    sample_path: Path,
    controls: SimulationScenarioControls,
) -> np.ndarray:
    """Predict burned probabilities after applying experimental scenario controls."""
    controls.validate()
    with np.load(sample_path) as sample:
        controlled_sample = _controlled_sample_arrays(sample, controls)
        return _predict_loaded_simulation_sample(model, controlled_sample)


def evaluate_simulation_surrogate_leave_one_out(
    corpus_dir: Path,
    *,
    random_seed: int = 42,
) -> list[SimulationSurrogateEvaluation]:
    """Evaluate the simulation surrogate with leave-one-scenario-out validation."""
    sample_paths = sample_paths_from_manifest(corpus_dir)
    evaluations: list[SimulationSurrogateEvaluation] = []
    for holdout_index, holdout_path in enumerate(sample_paths):
        training_paths = [path for index, path in enumerate(sample_paths) if index != holdout_index]
        model = train_simulation_surrogate(
            training_paths,
            random_seed=random_seed + holdout_index,
        )
        prediction = predict_simulation_sample(model, holdout_path)
        with np.load(holdout_path) as sample:
            evaluations.append(
                _evaluate_prediction(
                    case_id=holdout_path.stem,
                    prediction=prediction,
                    target=sample["forecast_burned"].astype(np.uint8),
                    persistence=sample["initial_burned"].astype(np.uint8),
                    training_cases=len(training_paths),
                    threshold=model.threshold,
                )
            )
    return evaluations


def fit_and_save_simulation_surrogate(
    *,
    corpus_dir: Path,
    model_path: Path,
    random_seed: int = 42,
) -> tuple[
    SimulationSurrogateModel,
    SimulationSurrogateTrainingSummary,
    list[SimulationSurrogateEvaluation],
]:
    """Train on all corpus samples, save the model and return evaluation summary."""
    sample_paths = sample_paths_from_manifest(corpus_dir)
    evaluations = evaluate_simulation_surrogate_leave_one_out(
        corpus_dir,
        random_seed=random_seed,
    )
    model = train_simulation_surrogate(sample_paths, random_seed=random_seed)
    save_simulation_surrogate_model(model, model_path)
    summary = _training_summary(
        corpus_dir=corpus_dir,
        model_path=model_path,
        model=model,
        evaluations=evaluations,
        sample_count=len(sample_paths),
    )
    return model, summary, evaluations


def save_simulation_surrogate_model(model: SimulationSurrogateModel, path: Path) -> None:
    """Save a trained simulation surrogate model as a compact NPZ artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        model_name=np.asarray([model.model_name]),
        feature_names=np.asarray(model.feature_names),
        feature_mean=model.feature_mean.astype(np.float32),
        feature_scale=model.feature_scale.astype(np.float32),
        weights=model.weights.astype(np.float32),
        bias=np.asarray([model.bias], dtype=np.float32),
        threshold=np.asarray([model.threshold], dtype=np.float32),
    )


def load_simulation_surrogate_model(path: Path) -> SimulationSurrogateModel:
    """Load a saved simulation surrogate model."""
    with np.load(path) as artifact:
        return SimulationSurrogateModel(
            feature_mean=artifact["feature_mean"].astype(np.float32),
            feature_scale=artifact["feature_scale"].astype(np.float32),
            weights=artifact["weights"].astype(np.float32),
            bias=float(artifact["bias"][0]),
            threshold=float(artifact["threshold"][0]),
            feature_names=tuple(str(name) for name in artifact["feature_names"].tolist()),
            model_name=str(artifact["model_name"][0]),
        )


def render_simulation_surrogate_report(
    summary: SimulationSurrogateTrainingSummary,
    evaluations: list[SimulationSurrogateEvaluation],
) -> str:
    """Render a Markdown report for Phase 5B surrogate evaluation."""
    lines = [
        "# FireTwin Phase 5B Simulation Surrogate",
        "",
        f"- Model: `{summary.model_name}`",
        f"- Corpus: `{summary.corpus_dir}`",
        f"- Model artifact: `{summary.model_path}`",
        f"- Samples: {summary.sample_count}",
        f"- Features: {summary.feature_count}",
        f"- Mean Brier: {summary.mean_brier_score:.5f}",
        f"- Mean persistence Brier: {summary.mean_persistence_brier_score:.5f}",
        f"- Mean Brier improvement: {summary.mean_brier_improvement_vs_persistence:+.5f}",
        f"- Mean IoU @ {summary.threshold:.2f}: {summary.mean_iou:.3f}",
        "",
        "| Holdout | Train cases | Brier | Persistence Brier | Improvement | Precision | Recall | IoU | Target + frac | Predicted + frac |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for evaluation in evaluations:
        lines.append(
            f"| {evaluation.case_id} | {evaluation.training_cases} | "
            f"{evaluation.brier_score:.5f} | {evaluation.persistence_brier_score:.5f} | "
            f"{evaluation.brier_improvement_vs_persistence:+.5f} | "
            f"{evaluation.precision:.3f} | {evaluation.recall:.3f} | "
            f"{evaluation.iou:.3f} | {evaluation.target_positive_fraction:.3f} | "
            f"{evaluation.predicted_positive_fraction:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This surrogate is trained on simulator-derived synthetic masks, not observed wildfire truth.",
            "- It is a Phase 5B baseline for latency/data-contract work before hybrid modeling.",
            "- Scenario controls should remain labeled experimental until validated on stronger corpora.",
            "",
        ]
    )
    return "\n".join(lines)


def _sample_cell_indices(
    target: np.ndarray,
    *,
    rng: np.random.Generator,
    max_cells: int,
    negative_ratio: int,
) -> np.ndarray:
    positive = np.flatnonzero(target)
    negative = np.flatnonzero(~target)
    if positive.size == 0 or negative.size == 0:
        return rng.choice(target.size, size=min(max_cells, target.size), replace=False)
    positive_count = min(positive.size, max_cells // (negative_ratio + 1))
    positive_count = max(1, positive_count)
    negative_count = min(negative.size, positive_count * negative_ratio)
    selected = np.concatenate(
        [
            rng.choice(positive, size=positive_count, replace=False),
            rng.choice(negative, size=negative_count, replace=False),
        ]
    )
    rng.shuffle(selected)
    return selected.astype(np.int64)


def _best_iou_threshold(probability: np.ndarray, target: np.ndarray) -> float:
    """Choose an operating threshold from training data only."""
    candidates = np.linspace(0.10, 0.90, 33, dtype=np.float32)
    best_threshold = 0.5
    best_iou = -1.0
    target_bool = target.astype(bool)
    for threshold in candidates:
        predicted = probability >= float(threshold)
        true_positive = int(np.sum(predicted & target_bool))
        false_positive = int(np.sum(predicted & ~target_bool))
        false_negative = int(np.sum(~predicted & target_bool))
        iou = true_positive / max(1, true_positive + false_positive + false_negative)
        if iou > best_iou:
            best_iou = iou
            best_threshold = float(threshold)
    return best_threshold


def _feature_matrix(
    sample: Any,
    horizon_index: int,
    cell_indices: np.ndarray | None = None,
) -> np.ndarray:
    initial = sample["initial_burned"].astype(np.float32)
    height, width = initial.shape
    total_cells = height * width
    if cell_indices is None:
        cell_indices = np.arange(total_cells, dtype=np.int64)

    rows, cols = np.unravel_index(cell_indices, (height, width))
    weather = sample["weather"].astype(np.float32)
    wind_speed, wind_direction, temperature, humidity = [float(value) for value in weather]
    base_spread_rate = float(sample["base_spread_rate_m_h"][0])
    horizon_hours = float(sample["forecast_hours"][horizon_index])
    centroid_row, centroid_col = _initial_centroid(initial)
    row_offset_m = (rows.astype(np.float32) - centroid_row) * _resolution_from_sample(sample)
    col_offset_m = (cols.astype(np.float32) - centroid_col) * _resolution_from_sample(sample)
    fire_direction = np.deg2rad(wind_direction + 180.0)
    cos_theta = float(np.cos(fire_direction))
    sin_theta = float(np.sin(fire_direction))
    x_along = col_offset_m * cos_theta - row_offset_m * sin_theta
    y_along = col_offset_m * sin_theta + row_offset_m * cos_theta
    distance_to_initial = _distance_to_initial(initial, rows, cols) * _resolution_from_sample(
        sample
    )
    aspect_radians = np.deg2rad(sample["aspect_degrees"].ravel()[cell_indices].astype(np.float32))

    columns = [
        initial.ravel()[cell_indices],
        sample["fuel_model"].ravel()[cell_indices],
        sample["fuel_load_kg_m2"].ravel()[cell_indices],
        sample["fuel_moisture_percent"].ravel()[cell_indices],
        sample["slope_degrees"].ravel()[cell_indices],
        sample["elevation_m"].ravel()[cell_indices],
        np.sin(aspect_radians),
        np.cos(aspect_radians),
        np.full(cell_indices.size, horizon_hours, dtype=np.float32),
        np.full(cell_indices.size, wind_speed, dtype=np.float32),
        np.full(cell_indices.size, np.sin(np.deg2rad(wind_direction)), dtype=np.float32),
        np.full(cell_indices.size, np.cos(np.deg2rad(wind_direction)), dtype=np.float32),
        np.full(cell_indices.size, temperature, dtype=np.float32),
        np.full(cell_indices.size, humidity, dtype=np.float32),
        np.full(cell_indices.size, base_spread_rate, dtype=np.float32),
        x_along,
        y_along,
        np.abs(x_along),
        distance_to_initial,
        np.full(
            cell_indices.size,
            base_spread_rate * 2.0 * (1.0 + wind_speed / 10.0) * horizon_hours,
            dtype=np.float32,
        ),
        np.full(cell_indices.size, base_spread_rate * 0.5 * horizon_hours, dtype=np.float32),
        np.full(cell_indices.size, base_spread_rate * 0.3 * horizon_hours, dtype=np.float32),
        (y_along >= 0).astype(np.float32),
    ]
    return np.column_stack(columns).astype(np.float32)


def _predict_loaded_simulation_sample(
    model: SimulationSurrogateModel,
    sample: Any,
) -> np.ndarray:
    horizon_count, height, width = sample["forecast_burned"].shape
    prediction = np.zeros((horizon_count, height, width), dtype=np.float32)
    for horizon_index in range(horizon_count):
        features = _feature_matrix(sample, horizon_index)
        prediction[horizon_index] = model.predict_probability(features).reshape(height, width)
    return prediction


def _controlled_sample_arrays(
    sample: Any,
    controls: SimulationScenarioControls,
) -> dict[str, np.ndarray]:
    arrays = {name: sample[name].copy() for name in sample.files}
    weather = arrays["weather"].astype(np.float32).copy()
    weather[0] = np.float32(weather[0] * controls.wind_speed_multiplier)
    weather[1] = np.float32((weather[1] + controls.wind_direction_delta_degrees) % 360.0)
    arrays["weather"] = weather
    arrays["base_spread_rate_m_h"] = (
        arrays["base_spread_rate_m_h"].astype(np.float32) * controls.base_spread_rate_multiplier
    )
    return arrays


def _initial_centroid(initial_burned: np.ndarray) -> tuple[float, float]:
    positions = np.argwhere(initial_burned > 0).astype(np.float32)
    if positions.size == 0:
        return ((initial_burned.shape[0] - 1) / 2.0, (initial_burned.shape[1] - 1) / 2.0)
    return (float(np.mean(positions[:, 0])), float(np.mean(positions[:, 1])))


def _distance_to_initial(
    initial_burned: np.ndarray, rows: np.ndarray, cols: np.ndarray
) -> np.ndarray:
    burned_positions = np.argwhere(initial_burned > 0)
    if burned_positions.size == 0:
        positions = np.asarray([_initial_centroid(initial_burned)], dtype=np.float32)
    else:
        positions = burned_positions.astype(np.float32)
    row_delta = rows[:, None].astype(np.float32) - positions[None, :, 0].astype(np.float32)
    col_delta = cols[:, None].astype(np.float32) - positions[None, :, 1].astype(np.float32)
    return cast(np.ndarray, np.sqrt(np.min(row_delta**2 + col_delta**2, axis=1)).astype(np.float32))


def _resolution_from_sample(sample: Any) -> float:
    if isinstance(sample, dict) and "resolution_m" in sample:
        return float(sample["resolution_m"][0])
    if "resolution_m" in getattr(sample, "files", []):
        return float(sample["resolution_m"][0])
    return 60.0


def _evaluate_prediction(
    *,
    case_id: str,
    prediction: np.ndarray,
    target: np.ndarray,
    persistence: np.ndarray,
    training_cases: int,
    threshold: float,
) -> SimulationSurrogateEvaluation:
    target_bool = target.astype(bool)
    prediction_clipped = np.clip(prediction.astype(np.float32), 0.0, 1.0)
    predicted_bool = prediction_clipped >= threshold
    persistence_stack = np.broadcast_to(persistence.astype(np.float32), target.shape)
    true_positive = int(np.sum(predicted_bool & target_bool))
    false_positive = int(np.sum(predicted_bool & ~target_bool))
    false_negative = int(np.sum(~predicted_bool & target_bool))
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    iou = true_positive / max(1, true_positive + false_positive + false_negative)
    brier = float(np.mean((prediction_clipped - target.astype(np.float32)) ** 2))
    persistence_brier = float(np.mean((persistence_stack - target.astype(np.float32)) ** 2))
    return SimulationSurrogateEvaluation(
        case_id=case_id,
        training_cases=training_cases,
        cell_count=int(target.size),
        threshold=threshold,
        brier_score=brier,
        persistence_brier_score=persistence_brier,
        brier_improvement_vs_persistence=persistence_brier - brier,
        precision=float(precision),
        recall=float(recall),
        iou=float(iou),
        target_positive_fraction=float(np.mean(target_bool)),
        predicted_positive_fraction=float(np.mean(predicted_bool)),
    )


def _training_summary(
    *,
    corpus_dir: Path,
    model_path: Path,
    model: SimulationSurrogateModel,
    evaluations: list[SimulationSurrogateEvaluation],
    sample_count: int,
) -> SimulationSurrogateTrainingSummary:
    mean = _mean_metric(evaluations)
    return SimulationSurrogateTrainingSummary(
        model_name=model.model_name,
        corpus_dir=corpus_dir.as_posix(),
        model_path=model_path.as_posix(),
        sample_count=sample_count,
        feature_count=len(model.feature_names),
        threshold=model.threshold,
        mean_brier_score=mean("brier_score"),
        mean_persistence_brier_score=mean("persistence_brier_score"),
        mean_brier_improvement_vs_persistence=mean("brier_improvement_vs_persistence"),
        mean_iou=mean("iou"),
        mean_precision=mean("precision"),
        mean_recall=mean("recall"),
    )


def _mean_metric(evaluations: list[SimulationSurrogateEvaluation]):
    if not evaluations:
        raise ValueError("At least one evaluation is required")

    def mean(field: str) -> float:
        return float(np.mean([getattr(evaluation, field) for evaluation in evaluations]))

    return mean
