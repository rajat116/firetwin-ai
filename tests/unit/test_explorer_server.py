"""Tests for the allowlisted Explorer preview server."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVE_EXPLORER_PATH = REPO_ROOT / "scripts/serve_explorer.py"
SPEC = importlib.util.spec_from_file_location("serve_explorer", SERVE_EXPLORER_PATH)
assert SPEC is not None
serve_explorer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(serve_explorer)

resolve_explorer_request = serve_explorer.resolve_explorer_request


def test_resolve_explorer_request_allows_public_assets() -> None:
    """The local preview server should resolve only known Explorer assets."""
    assert resolve_explorer_request("/") == serve_explorer.REPO_ROOT / "frontend/index.html"
    assert (
        resolve_explorer_request("/frontend/") == serve_explorer.REPO_ROOT / "frontend/index.html"
    )
    assert (
        resolve_explorer_request("/frontend/app.js") == serve_explorer.REPO_ROOT / "frontend/app.js"
    )
    assert (
        resolve_explorer_request("/data/manifests/firms_next_day_explorer_manifest.json")
        == serve_explorer.REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"
    )


def test_resolve_explorer_request_rejects_secrets_and_unrelated_reports() -> None:
    """The local preview server must not expose arbitrary repository files."""
    assert resolve_explorer_request("/.env") is None
    assert resolve_explorer_request("/pyproject.toml") is None
    assert resolve_explorer_request("/frontend/../.env") is None
    assert resolve_explorer_request("/reports/firms_next_day_explorer_assets.md") is None


def test_resolve_explorer_request_limits_figures_to_explorer_assets() -> None:
    """Only figure PNGs needed by the Explorer should be served."""
    allowed = resolve_explorer_request(
        "/reports/figures/carlton_complex_2014_explorer_forecast_preview.png"
    )
    forecast_overlay = resolve_explorer_request(
        "/reports/figures/carlton_complex_2014_globe_forecast_overlay.png"
    )
    observed_overlay = resolve_explorer_request(
        "/reports/figures/carlton_complex_2014_globe_observed_overlay.png"
    )
    blocked = resolve_explorer_request("/reports/figures/carlton_complex_2014_firms_overlay.png")

    assert allowed == Path(
        serve_explorer.REPO_ROOT
        / "reports/figures/carlton_complex_2014_explorer_forecast_preview.png"
    )
    assert forecast_overlay == Path(
        serve_explorer.REPO_ROOT / "reports/figures/carlton_complex_2014_globe_forecast_overlay.png"
    )
    assert observed_overlay == Path(
        serve_explorer.REPO_ROOT / "reports/figures/carlton_complex_2014_globe_observed_overlay.png"
    )
    assert blocked is None
