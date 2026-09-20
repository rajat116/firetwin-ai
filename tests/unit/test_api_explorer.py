"""Tests for the FireTwin Explorer API."""

from pathlib import Path

from fastapi.testclient import TestClient

from firetwin.api.explorer import load_explorer_manifest
from firetwin.api.main import create_app
from firetwin.models.surrogate import fit_and_save_simulation_surrogate
from firetwin.simulation import SimulationCorpusConfig, build_simulation_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"


def test_load_explorer_manifest_reads_committed_cases() -> None:
    """API service should load the committed Explorer forecast catalog."""
    manifest = load_explorer_manifest(MANIFEST_PATH)

    assert manifest["not_operational"] is True
    assert manifest["forecast_semantics"] == (
        "next_calendar_day_firms_active_fire_detection_probability"
    )
    assert len(manifest["cases"]) == 3
    assert all(case["brier_improvement_vs_persistence"] > 0 for case in manifest["cases"])


def test_api_health_and_case_catalog() -> None:
    """FastAPI app should expose health and case catalog endpoints."""
    client = TestClient(create_app(MANIFEST_PATH))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["case_count"] == 3
    assert health.json()["not_operational"] is True

    response = client.get("/api/explorer/cases")
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] == 3
    assert {case["case_id"] for case in body["cases"]} == {
        "carlton_complex_2014",
        "king_2014",
        "big_cougar_2014",
    }
    assert all("center_lon_lat" in case for case in body["cases"])


def test_api_forecast_response_is_artifact_backed_and_guarded() -> None:
    """Forecast endpoint should return the validated artifact-backed forecast contract."""
    client = TestClient(create_app(MANIFEST_PATH))

    response = client.post("/api/forecast/firms-next-day/carlton_complex_2014")

    assert response.status_code == 200
    body = response.json()
    assert body["forecast_mode"] == "artifact_backed_live_api"
    assert body["not_operational"] is True
    assert body["metrics"]["brier_improvement_vs_persistence"] > 0
    assert body["footprint"]["peak_probability"] > 0
    assert -180 <= body["provenance"]["center_lon_lat"]["lon"] <= 180
    assert -90 <= body["provenance"]["center_lon_lat"]["lat"] <= 90
    assert body["provenance"]["forecast_artifact"].endswith("_learned_forecast.zarr")
    assert body["guardrails"]


def test_api_unknown_case_returns_404() -> None:
    """Unknown case IDs should fail cleanly."""
    client = TestClient(create_app(MANIFEST_PATH))

    response = client.post("/api/forecast/firms-next-day/nope")

    assert response.status_code == 404
    assert "Unknown Explorer case" in response.json()["detail"]


def test_api_simulation_surrogate_runs_artifact_backed_scenario(tmp_path: Path) -> None:
    """Simulation endpoint should run real surrogate inference with scenario controls."""
    corpus_dir = tmp_path / "corpus"
    build_simulation_corpus(
        output_dir=corpus_dir,
        config=SimulationCorpusConfig(
            case_count=4,
            grid_height=20,
            grid_width=20,
            forecast_hours=(3.0, 6.0),
            seed=812,
        ),
    )
    model_path = tmp_path / "surrogate.npz"
    fit_and_save_simulation_surrogate(
        corpus_dir=corpus_dir,
        model_path=model_path,
        random_seed=22,
    )
    client = TestClient(
        create_app(
            MANIFEST_PATH,
            simulation_corpus_dir=corpus_dir,
            simulation_model_path=model_path,
        )
    )

    samples = client.get("/api/simulation/samples")
    assert samples.status_code == 200
    assert samples.json()["sample_count"] == 4

    response = client.post(
        "/api/simulation/surrogate/phase5b_sim_0000",
        json={
            "wind_speed_multiplier": 1.4,
            "wind_direction_delta_degrees": 25.0,
            "base_spread_rate_multiplier": 1.2,
            "include_probability_grid": True,
            "max_grid_size": 16,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["forecast_mode"] == "simulation_surrogate_on_demand"
    assert body["not_operational"] is True
    assert body["simulator_truth"] is False
    assert body["controls"]["wind_speed_multiplier"] == 1.4
    assert body["summary"]["peak_probability"] > 0.0
    assert len(body["summary"]["per_horizon"]) == 2
    assert len(body["probability_grid"]) == 2
    assert body["guardrails"]


def test_api_simulation_surrogate_rejects_invalid_controls(tmp_path: Path) -> None:
    """Invalid experimental controls should fail before inference."""
    corpus_dir = tmp_path / "corpus"
    build_simulation_corpus(
        output_dir=corpus_dir,
        config=SimulationCorpusConfig(case_count=2, grid_height=18, grid_width=18, seed=33),
    )
    model_path = tmp_path / "surrogate.npz"
    fit_and_save_simulation_surrogate(
        corpus_dir=corpus_dir,
        model_path=model_path,
        random_seed=33,
    )
    client = TestClient(
        create_app(
            MANIFEST_PATH,
            simulation_corpus_dir=corpus_dir,
            simulation_model_path=model_path,
        )
    )

    response = client.post(
        "/api/simulation/surrogate/phase5b_sim_0000",
        json={"wind_speed_multiplier": 9.0},
    )

    assert response.status_code == 422
    assert "wind_speed_multiplier" in response.json()["detail"]
