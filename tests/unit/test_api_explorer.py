"""Tests for the FireTwin Explorer API."""

from pathlib import Path

from fastapi.testclient import TestClient

from firetwin.api.explorer import load_explorer_manifest
from firetwin.api.main import create_app

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
