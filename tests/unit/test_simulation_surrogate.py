"""Tests for the Phase 5B simulation surrogate."""

from pathlib import Path

import numpy as np

from firetwin.models.surrogate import (
    evaluate_simulation_surrogate_leave_one_out,
    fit_and_save_simulation_surrogate,
    load_simulation_surrogate_model,
    predict_simulation_sample,
    render_simulation_surrogate_report,
    train_simulation_surrogate,
)
from firetwin.simulation import SimulationCorpusConfig, build_simulation_corpus


def _build_test_corpus(tmp_path: Path) -> Path:
    corpus_dir = tmp_path / "corpus"
    build_simulation_corpus(
        output_dir=corpus_dir,
        config=SimulationCorpusConfig(
            case_count=4,
            grid_height=24,
            grid_width=24,
            resolution_m=60.0,
            forecast_hours=(3.0, 6.0, 12.0),
            seed=117,
        ),
    )
    return corpus_dir


def test_train_simulation_surrogate_predicts_probability_masks(tmp_path: Path) -> None:
    """Trained surrogate should produce bounded probabilities with the target shape."""
    corpus_dir = _build_test_corpus(tmp_path)
    sample_paths = sorted(corpus_dir.joinpath("samples").glob("*.npz"))
    model = train_simulation_surrogate(sample_paths[:3], random_seed=3, epochs=30)
    prediction = predict_simulation_sample(model, sample_paths[3])

    with np.load(sample_paths[3]) as sample:
        assert prediction.shape == sample["forecast_burned"].shape
        assert np.all(prediction >= 0.0)
        assert np.all(prediction <= 1.0)
        assert prediction[-1].mean() > prediction[0].mean()


def test_evaluate_simulation_surrogate_leave_one_out_beats_persistence(tmp_path: Path) -> None:
    """Surrogate should beat initial-state persistence on simulator-derived holdouts."""
    corpus_dir = _build_test_corpus(tmp_path)
    evaluations = evaluate_simulation_surrogate_leave_one_out(corpus_dir, random_seed=5)

    assert len(evaluations) == 4
    assert np.mean([row.brier_improvement_vs_persistence for row in evaluations]) > 0.0
    assert np.mean([row.iou for row in evaluations]) > 0.15
    assert all(0.0 <= row.predicted_positive_fraction <= 1.0 for row in evaluations)


def test_fit_save_load_and_report_simulation_surrogate(tmp_path: Path) -> None:
    """Training helper should save reloadable model artifacts and reports."""
    corpus_dir = _build_test_corpus(tmp_path)
    model_path = tmp_path / "surrogate.npz"
    model, summary, evaluations = fit_and_save_simulation_surrogate(
        corpus_dir=corpus_dir,
        model_path=model_path,
        random_seed=9,
    )
    loaded = load_simulation_surrogate_model(model_path)
    sample_path = sorted(corpus_dir.joinpath("samples").glob("*.npz"))[0]
    original_prediction = predict_simulation_sample(model, sample_path)
    loaded_prediction = predict_simulation_sample(loaded, sample_path)
    report = render_simulation_surrogate_report(summary, evaluations)

    assert model_path.exists()
    assert np.allclose(original_prediction, loaded_prediction)
    assert summary.sample_count == 4
    assert summary.mean_brier_improvement_vs_persistence > 0.0
    assert "Phase 5B Simulation Surrogate" in report
    assert "not observed wildfire truth" in report
