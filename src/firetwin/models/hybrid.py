"""Phase 6 hybrid forecast utilities.

The first hybrid layer combines an observed-label ML forecast with a physics/simulator prior.
It is deliberately small: the goal is to establish the contract, evaluation semantics and
guardrails before replacing the prior with richer simulator-conditioned fields.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from firetwin.evaluation.firms_next_day import evaluate_firms_next_day_prediction

HYBRID_MODEL_NAME = "phase6_convex_ml_physics_blend_v1"


@dataclass(frozen=True)
class HybridBlendModel:
    """Convex blend between observed-label ML probability and a physics/simulator prior."""

    ml_weight: float
    model_name: str = HYBRID_MODEL_NAME

    @property
    def physics_weight(self) -> float:
        """Return the implied physics-prior weight."""
        return 1.0 - self.ml_weight

    def predict_probability(
        self, ml_probability: np.ndarray, physics_prior: np.ndarray
    ) -> np.ndarray:
        """Blend probabilities after validating compatible shapes and probability bounds."""
        return hybrid_blend_probability(
            ml_probability=ml_probability,
            physics_prior=physics_prior,
            ml_weight=self.ml_weight,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable model summary."""
        return asdict(self) | {"physics_weight": self.physics_weight}


@dataclass(frozen=True)
class HybridBlendEvaluation:
    """Evaluation result for one fitted hybrid blend."""

    model_name: str
    ml_weight: float
    physics_weight: float
    hybrid_brier_score: float
    ml_brier_score: float
    physics_brier_score: float
    hybrid_improvement_vs_ml: float
    hybrid_improvement_vs_physics: float
    precision_at_threshold: float
    recall_at_threshold: float
    iou_at_threshold: float
    predicted_positive_fraction: float
    target_positive_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable evaluation summary."""
        return asdict(self)


def hybrid_blend_probability(
    *,
    ml_probability: np.ndarray,
    physics_prior: np.ndarray,
    ml_weight: float,
) -> np.ndarray:
    """Return a clipped convex blend of ML and physics/simulator probabilities."""
    if ml_probability.shape != physics_prior.shape:
        raise ValueError(
            f"ml_probability shape {ml_probability.shape} does not match "
            f"physics_prior shape {physics_prior.shape}"
        )
    if not 0.0 <= ml_weight <= 1.0:
        raise ValueError("ml_weight must be between 0 and 1")

    ml = np.clip(ml_probability.astype(np.float32), 0.0, 1.0)
    physics = np.clip(physics_prior.astype(np.float32), 0.0, 1.0)
    return np.clip(ml_weight * ml + (1.0 - ml_weight) * physics, 0.0, 1.0).astype(np.float32)


def fit_hybrid_blend_model(
    *,
    ml_probability: np.ndarray,
    physics_prior: np.ndarray,
    target_probability: np.ndarray,
    candidate_weights: np.ndarray | None = None,
) -> HybridBlendModel:
    """Choose the ML/physics blend weight that minimizes observed-label Brier score."""
    if (
        ml_probability.shape != physics_prior.shape
        or ml_probability.shape != target_probability.shape
    ):
        raise ValueError("ml_probability, physics_prior and target_probability must share shape")
    candidates = (
        candidate_weights
        if candidate_weights is not None
        else np.linspace(0.0, 1.0, 21, dtype=np.float32)
    )
    if candidates.size == 0:
        raise ValueError("candidate_weights must not be empty")

    target = np.clip(target_probability.astype(np.float32), 0.0, 1.0)
    best_weight = 1.0
    best_brier = float("inf")
    for candidate in candidates:
        weight = float(candidate)
        prediction = hybrid_blend_probability(
            ml_probability=ml_probability,
            physics_prior=physics_prior,
            ml_weight=weight,
        )
        brier = float(np.mean((prediction - target) ** 2))
        if brier < best_brier:
            best_brier = brier
            best_weight = weight
    return HybridBlendModel(ml_weight=best_weight)


def evaluate_hybrid_blend(
    *,
    model: HybridBlendModel,
    ml_probability: np.ndarray,
    physics_prior: np.ndarray,
    target_probability: np.ndarray,
    target_positive_mask: np.ndarray,
    threshold: float,
) -> HybridBlendEvaluation:
    """Evaluate a fitted hybrid blend against ML-only and physics-only probabilities."""
    hybrid = model.predict_probability(ml_probability, physics_prior)
    target = np.clip(target_probability.astype(np.float32), 0.0, 1.0)
    ml = np.clip(ml_probability.astype(np.float32), 0.0, 1.0)
    physics = np.clip(physics_prior.astype(np.float32), 0.0, 1.0)
    metrics = evaluate_firms_next_day_prediction(
        prediction=hybrid,
        target_probability=target,
        target_positive_mask=target_positive_mask.astype(bool),
        threshold=threshold,
    )
    hybrid_brier = float(metrics["observed_brier_score"])
    ml_brier = float(np.mean((ml - target) ** 2))
    physics_brier = float(np.mean((physics - target) ** 2))
    return HybridBlendEvaluation(
        model_name=model.model_name,
        ml_weight=model.ml_weight,
        physics_weight=model.physics_weight,
        hybrid_brier_score=hybrid_brier,
        ml_brier_score=ml_brier,
        physics_brier_score=physics_brier,
        hybrid_improvement_vs_ml=ml_brier - hybrid_brier,
        hybrid_improvement_vs_physics=physics_brier - hybrid_brier,
        precision_at_threshold=float(metrics["precision_at_threshold"]),
        recall_at_threshold=float(metrics["recall_at_threshold"]),
        iou_at_threshold=float(metrics["iou_at_threshold"]),
        predicted_positive_fraction=float(metrics["predicted_positive_fraction"]),
        target_positive_fraction=float(metrics["target_positive_fraction"]),
    )


def render_hybrid_blend_report(evaluations: list[HybridBlendEvaluation]) -> str:
    """Render Phase 6 hybrid blend diagnostics as Markdown."""
    lines = [
        "# FireTwin Phase 6 Hybrid Blend Diagnostics",
        "",
        "This report evaluates the first Phase 6 contract: a convex blend of observed-label ML",
        "probabilities and a physics/simulator prior. Targets remain FIRMS positive-observation",
        "evidence unless a later report explicitly states otherwise.",
        "",
        "| Model | ML weight | Physics weight | Hybrid Brier | ML Brier | Physics Brier | vs ML | vs Physics | Precision | Recall | IoU |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for evaluation in evaluations:
        lines.append(
            f"| {evaluation.model_name} | {evaluation.ml_weight:.2f} | "
            f"{evaluation.physics_weight:.2f} | {evaluation.hybrid_brier_score:.5f} | "
            f"{evaluation.ml_brier_score:.5f} | {evaluation.physics_brier_score:.5f} | "
            f"{evaluation.hybrid_improvement_vs_ml:+.5f} | "
            f"{evaluation.hybrid_improvement_vs_physics:+.5f} | "
            f"{evaluation.precision_at_threshold:.3f} | {evaluation.recall_at_threshold:.3f} | "
            f"{evaluation.iou_at_threshold:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This is a Phase 6 contract scaffold, not the final hybrid wildfire model.",
            "- The physics prior must declare its target semantics before blending.",
            "- Final-extent masks must not be used as short-horizon labels.",
            "",
        ]
    )
    return "\n".join(lines)
