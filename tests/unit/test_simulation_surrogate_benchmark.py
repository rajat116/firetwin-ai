"""Tests for Phase 5B surrogate latency benchmarking."""

from pathlib import Path

import numpy as np

from firetwin.models.surrogate import fit_and_save_simulation_surrogate
from firetwin.models.surrogate.benchmark import (
    benchmark_simulation_surrogate_latency,
    fire_case_from_simulation_sample,
    render_simulation_latency_report,
)
from firetwin.simulation import SimulationCorpusConfig, build_simulation_corpus


def _build_test_corpus(tmp_path: Path) -> Path:
    corpus_dir = tmp_path / "corpus"
    build_simulation_corpus(
        output_dir=corpus_dir,
        config=SimulationCorpusConfig(
            case_count=3,
            grid_height=18,
            grid_width=20,
            resolution_m=75.0,
            forecast_hours=(3.0, 6.0),
            seed=511,
        ),
    )
    return corpus_dir


def test_fire_case_from_simulation_sample_reconstructs_baseline_inputs(tmp_path: Path) -> None:
    """Simulation-corpus samples should reconstruct valid FireCase inputs."""
    corpus_dir = _build_test_corpus(tmp_path)
    sample_path = sorted(corpus_dir.joinpath("samples").glob("*.npz"))[0]
    case, forecast_hours, base_spread_rate = fire_case_from_simulation_sample(sample_path)

    with np.load(sample_path) as sample:
        assert case.grid_shape == sample["initial_burned"].shape
        assert case.resolution_m == 75.0
        assert forecast_hours == [3.0, 6.0]
        assert base_spread_rate == float(sample["base_spread_rate_m_h"][0])
        assert case.weather.wind_speed_m_s == float(sample["weather"][0])


def test_benchmark_simulation_surrogate_latency_reports_positive_timings(
    tmp_path: Path,
) -> None:
    """Latency benchmark should produce serializable positive timing metrics."""
    corpus_dir = _build_test_corpus(tmp_path)
    model_path = tmp_path / "surrogate.npz"
    fit_and_save_simulation_surrogate(
        corpus_dir=corpus_dir,
        model_path=model_path,
        random_seed=17,
    )

    summary, rows = benchmark_simulation_surrogate_latency(
        corpus_dir=corpus_dir,
        model_path=model_path,
        repetitions=2,
        warmup=1,
        max_samples=2,
    )
    report = render_simulation_latency_report(summary, rows)

    assert summary.sample_count == 2
    assert summary.repetitions == 2
    assert summary.mean_simulator_median_ms > 0.0
    assert summary.mean_surrogate_median_ms > 0.0
    assert summary.mean_median_speedup > 0.0
    assert len(rows) == 2
    assert all(row.grid_cells == 360 for row in rows)
    assert "Phase 5B Simulation Surrogate Latency" in report
    assert "artifact-backed NPZ loading" in report
