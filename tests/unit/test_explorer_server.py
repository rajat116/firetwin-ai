"""Tests for the allowlisted Explorer preview server."""

from pathlib import Path

from scripts.serve_explorer import REPO_ROOT, resolve_explorer_request


def test_resolve_explorer_request_allows_public_assets() -> None:
    """The local preview server should resolve only known Explorer assets."""
    assert resolve_explorer_request("/") == REPO_ROOT / "frontend/index.html"
    assert resolve_explorer_request("/frontend/") == REPO_ROOT / "frontend/index.html"
    assert resolve_explorer_request("/frontend/app.js") == REPO_ROOT / "frontend/app.js"
    assert (
        resolve_explorer_request("/data/manifests/firms_next_day_explorer_manifest.json")
        == REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"
    )


def test_resolve_explorer_request_rejects_secrets_and_unrelated_reports() -> None:
    """The local preview server must not expose arbitrary repository files."""
    assert resolve_explorer_request("/.env") is None
    assert resolve_explorer_request("/pyproject.toml") is None
    assert resolve_explorer_request("/frontend/../.env") is None
    assert resolve_explorer_request("/reports/firms_next_day_explorer_assets.md") is None


def test_resolve_explorer_request_limits_figures_to_explorer_previews() -> None:
    """Only preview PNGs needed by the Explorer should be served."""
    allowed = resolve_explorer_request(
        "/reports/figures/carlton_complex_2014_explorer_forecast_preview.png"
    )
    blocked = resolve_explorer_request("/reports/figures/carlton_complex_2014_firms_overlay.png")

    assert allowed == Path(
        REPO_ROOT / "reports/figures/carlton_complex_2014_explorer_forecast_preview.png"
    )
    assert blocked is None
