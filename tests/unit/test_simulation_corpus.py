"""Tests for Phase 5B simulation-corpus generation."""

import json
from pathlib import Path

import numpy as np
import pytest

from firetwin.simulation import (
    SIMULATION_CORPUS_SCHEMA_VERSION,
    SimulationCorpusConfig,
    build_simulation_corpus,
    render_simulation_corpus_report,
    sample_simulation_scenario,
)


def test_sample_simulation_scenario_is_deterministic_and_varied() -> None:
    """Scenario sampling should be reproducible without collapsing all cases together."""
    first = sample_simulation_scenario(0, seed=123)
    first_again = sample_simulation_scenario(0, seed=123)
    second = sample_simulation_scenario(1, seed=123)

    assert first == first_again
    assert first != second
    assert 0.5 <= first.wind_speed_m_s <= 14.0
    assert 0.0 <= first.wind_direction_degrees < 360.0
    assert 12.0 <= first.relative_humidity_percent <= 55.0


def test_build_simulation_corpus_writes_manifest_and_npz_samples(tmp_path: Path) -> None:
    """Phase 5B corpus should write loadable artifacts with stable array contracts."""
    output_dir = tmp_path / "corpus"
    summary = build_simulation_corpus(
        output_dir=output_dir,
        config=SimulationCorpusConfig(
            case_count=3,
            grid_height=24,
            grid_width=28,
            resolution_m=90.0,
            forecast_hours=(3.0, 6.0, 12.0),
            seed=42,
        ),
    )
    manifest = json.loads(output_dir.joinpath("manifest.json").read_text(encoding="utf-8"))

    assert summary.schema_version == SIMULATION_CORPUS_SCHEMA_VERSION
    assert summary.sample_count == 3
    assert summary.total_final_burned_cells > 0
    assert manifest["schema_version"] == SIMULATION_CORPUS_SCHEMA_VERSION
    assert manifest["not_real_wildfire_truth"] is True
    assert manifest["sample_count"] == 3
    assert len(manifest["samples"]) == 3

    sample_path = output_dir / manifest["samples"][0]["artifact"]
    with np.load(sample_path) as sample:
        assert sample["initial_burned"].shape == (24, 28)
        assert sample["forecast_burned"].shape == (3, 24, 28)
        assert sample["forecast_active_front"].shape == (3, 24, 28)
        assert sample["resolution_m"].tolist() == [90.0]
        assert sample["weather"].shape == (4,)
        assert sample["forecast_hours"].tolist() == [3.0, 6.0, 12.0]
        burned_cells = sample["forecast_burned"].sum(axis=(1, 2))
        assert np.all(np.diff(burned_cells) >= 0)


def test_build_simulation_corpus_is_reproducible(tmp_path: Path) -> None:
    """Same config and seed should produce identical sample arrays."""
    config = SimulationCorpusConfig(
        case_count=2,
        grid_height=20,
        grid_width=20,
        resolution_m=60.0,
        forecast_hours=(2.0, 4.0),
        seed=7,
    )
    first = tmp_path / "first"
    second = tmp_path / "second"

    build_simulation_corpus(output_dir=first, config=config)
    build_simulation_corpus(output_dir=second, config=config)

    with (
        np.load(first / "samples/phase5b_sim_0000.npz") as sample_a,
        np.load(second / "samples/phase5b_sim_0000.npz") as sample_b,
    ):
        assert np.array_equal(sample_a["forecast_burned"], sample_b["forecast_burned"])
        assert np.array_equal(sample_a["weather"], sample_b["weather"])


def test_simulation_corpus_config_validates_inputs() -> None:
    """Invalid corpus settings should fail before writing artifacts."""
    with pytest.raises(ValueError, match="case_count"):
        SimulationCorpusConfig(case_count=0).validate()
    with pytest.raises(ValueError, match="sorted"):
        SimulationCorpusConfig(forecast_hours=(6.0, 3.0)).validate()


def test_render_simulation_corpus_report(tmp_path: Path) -> None:
    """Corpus report should provide concise provenance for generated artifacts."""
    summary = build_simulation_corpus(
        output_dir=tmp_path / "corpus",
        config=SimulationCorpusConfig(case_count=1, grid_height=18, grid_width=18, seed=5),
    )
    report = render_simulation_corpus_report(summary)

    assert "Phase 5B Simulation Corpus" in report
    assert "not as real" in report
    assert str(summary.sample_count) in report
