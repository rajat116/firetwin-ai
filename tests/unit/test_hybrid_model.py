"""Tests for Phase 6 hybrid model contracts."""

import numpy as np
import pytest

from firetwin.models.hybrid import (
    evaluate_hybrid_blend,
    fit_hybrid_blend_model,
    hybrid_blend_probability,
    render_hybrid_blend_report,
)


def test_hybrid_blend_probability_validates_shape_and_weight() -> None:
    """Hybrid blending should be bounded and reject incompatible inputs."""
    ml = np.array([[0.2, 0.8]], dtype=np.float32)
    physics = np.array([[0.4, 0.6]], dtype=np.float32)

    blended = hybrid_blend_probability(ml_probability=ml, physics_prior=physics, ml_weight=0.75)

    assert blended.shape == ml.shape
    assert np.allclose(blended, np.array([[0.25, 0.75]], dtype=np.float32))
    with pytest.raises(ValueError, match="shape"):
        hybrid_blend_probability(
            ml_probability=ml,
            physics_prior=np.zeros((2, 2), dtype=np.float32),
            ml_weight=0.5,
        )
    with pytest.raises(ValueError, match="ml_weight"):
        hybrid_blend_probability(ml_probability=ml, physics_prior=physics, ml_weight=1.5)


def test_fit_hybrid_blend_model_selects_best_validation_weight() -> None:
    """Fitting should select a blend that improves over a weak single source."""
    target = np.array([[[0.0, 1.0], [0.0, 1.0]]], dtype=np.float32)
    ml = np.array([[[0.1, 0.9], [0.2, 0.8]]], dtype=np.float32)
    physics = np.array([[[0.4, 0.6], [0.1, 0.95]]], dtype=np.float32)

    model = fit_hybrid_blend_model(
        ml_probability=ml,
        physics_prior=physics,
        target_probability=target,
        candidate_weights=np.asarray([0.0, 0.5, 1.0], dtype=np.float32),
    )
    evaluation = evaluate_hybrid_blend(
        model=model,
        ml_probability=ml,
        physics_prior=physics,
        target_probability=target,
        target_positive_mask=target > 0.5,
        threshold=0.5,
    )
    report = render_hybrid_blend_report([evaluation])

    assert model.ml_weight in {0.5, 1.0}
    assert evaluation.hybrid_brier_score <= evaluation.physics_brier_score
    assert "Phase 6" in report
    assert "Final-extent masks" in report
