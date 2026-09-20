"""Static checks for the FireTwin Explorer frontend."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"


def test_frontend_references_committed_explorer_assets() -> None:
    """Frontend should load the committed manifest and real preview assets."""
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    globe_html = (FRONTEND_DIR / "globe.html").read_text(encoding="utf-8")
    globe_js = (FRONTEND_DIR / "globe.js").read_text(encoding="utf-8")
    manifest_path = REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "./app.js" in html
    assert "./styles.css" in html
    assert "firms_next_day_explorer_manifest.json" in app_js
    assert "forecastFootprint" in html
    assert "brierImprovement" in html
    assert "persistenceBrier" in html
    assert "sample_predicted_positive_fraction" in app_js
    assert "sample_target_positive_fraction" in app_js
    assert "brier_improvement_vs_persistence" in app_js
    assert "persistence_brier_score" in app_js
    assert "Cesium.js" in globe_html
    assert "globeCaseList" in globe_html
    assert "forecastLayerToggle" in globe_html
    assert "overlayOpacity" in globe_html
    assert "windSpeedMultiplier" in globe_html
    assert "windDirectionDelta" in globe_html
    assert "spreadRateMultiplier" in globe_html
    assert "runScenario" in globe_html
    assert "scenarioLayerToggle" in globe_html
    assert "zoomIn" in globe_html
    assert "zoomOut" in globe_html
    assert "World_Imagery" in globe_js
    assert "UrlTemplateImageryProvider" in globe_js
    assert "ImageMaterialProperty" in globe_js
    assert "/api/simulation/samples" in globe_js
    assert "/api/simulation/surrogate/" in globe_js
    assert "wind_speed_multiplier" in globe_js
    assert "base_spread_rate_multiplier" in globe_js
    assert "include_probability_grid: true" in globe_js
    assert "scenarioCanvasFromGrid" in globe_js
    assert "forecast_overlay_png" in globe_js
    assert "observed_overlay_png" in globe_js
    assert "wgs84_bbox" in globe_js
    assert "center_lon_lat" in globe_js
    assert manifest["cases"]
    for case in manifest["cases"]:
        assert case["brier_improvement_vs_persistence"] > 0
        assert -180 <= case["center_lon_lat"]["lon"] <= 180
        assert -90 <= case["center_lon_lat"]["lat"] <= 90
        assert (REPO_ROOT / case["preview_png"]).exists()
        assert (REPO_ROOT / case["forecast_overlay_png"]).exists()
        assert (REPO_ROOT / case["observed_overlay_png"]).exists()


def test_frontend_avoids_placeholder_copy() -> None:
    """Explorer copy should be scoped to real FIRMS forecast assets."""
    combined = "\n".join(
        [
            (FRONTEND_DIR / "index.html").read_text(encoding="utf-8"),
            (FRONTEND_DIR / "app.js").read_text(encoding="utf-8"),
        ]
    ).lower()

    assert "lorem" not in combined
    assert "dummy" not in combined
    assert "active-fire" in combined
