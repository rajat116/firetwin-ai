"""FastAPI application for FireTwin forecast exploration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from firetwin import __version__
from firetwin.api.explorer import (
    DEFAULT_MANIFEST_PATH,
    ExplorerCatalogError,
    build_forecast_response,
    get_explorer_case,
    list_explorer_cases,
    load_explorer_manifest,
)
from firetwin.api.simulation import (
    DEFAULT_SIMULATION_CORPUS_DIR,
    DEFAULT_SIMULATION_MODEL_PATH,
    SimulationInferenceError,
    SimulationScenarioRequest,
    build_simulation_scenario_response,
    list_simulation_samples,
)


def create_app(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    simulation_corpus_dir: Path = DEFAULT_SIMULATION_CORPUS_DIR,
    simulation_model_path: Path = DEFAULT_SIMULATION_MODEL_PATH,
) -> FastAPI:
    """Create the FireTwin API app."""
    app = FastAPI(
        title="FireTwin API",
        version=__version__,
        description=(
            "Research API for FireTwin forecast exploration. Current forecast responses are "
            "validated artifact-backed outputs for satellite-visible FIRMS active-fire evidence."
        ),
    )

    def manifest() -> dict[str, Any]:
        try:
            return load_explorer_manifest(manifest_path)
        except ExplorerCatalogError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/health")
    def health() -> dict[str, Any]:
        loaded_manifest = manifest()
        return {
            "status": "ok",
            "service": "firetwin-api",
            "version": __version__,
            "case_count": len(loaded_manifest["cases"]),
            "forecast_semantics": loaded_manifest["forecast_semantics"],
            "not_operational": loaded_manifest["not_operational"],
        }

    @app.get("/api/explorer/manifest")
    def explorer_manifest() -> dict[str, Any]:
        return manifest()

    @app.get("/api/explorer/cases")
    def explorer_cases() -> dict[str, Any]:
        loaded_manifest = manifest()
        return {
            "cases": list_explorer_cases(loaded_manifest),
            "case_count": len(loaded_manifest["cases"]),
            "forecast_semantics": loaded_manifest["forecast_semantics"],
            "not_operational": loaded_manifest["not_operational"],
        }

    @app.get("/api/explorer/cases/{case_id}")
    def explorer_case(case_id: str) -> dict[str, Any]:
        loaded_manifest = manifest()
        try:
            return get_explorer_case(loaded_manifest, case_id)
        except ExplorerCatalogError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/forecast/firms-next-day/{case_id}")
    def forecast_firms_next_day(case_id: str) -> dict[str, Any]:
        loaded_manifest = manifest()
        try:
            return build_forecast_response(loaded_manifest, case_id=case_id)
        except ExplorerCatalogError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/simulation/samples")
    def simulation_samples() -> dict[str, Any]:
        try:
            samples = list_simulation_samples(simulation_corpus_dir)
        except SimulationInferenceError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "samples": samples,
            "sample_count": len(samples),
            "not_operational": True,
            "forecast_mode": "simulation_surrogate_on_demand",
        }

    @app.post("/api/simulation/surrogate/{case_id}")
    def simulation_surrogate(
        case_id: str,
        request: SimulationScenarioRequest | None = None,
    ) -> dict[str, Any]:
        try:
            return build_simulation_scenario_response(
                case_id=case_id,
                request=request,
                corpus_dir=simulation_corpus_dir,
                model_path=simulation_model_path,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except SimulationInferenceError as exc:
            status_code = 404 if "Unknown simulation sample" in str(exc) else 503
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return app


app = create_app()
