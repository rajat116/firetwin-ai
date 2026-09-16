"""Tests for the deployable FireTwin Explorer static bundle."""

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT_PATH = REPO_ROOT / "scripts/build_explorer_site.py"
SPEC = importlib.util.spec_from_file_location("build_explorer_site", BUILD_SCRIPT_PATH)
assert SPEC is not None
build_explorer_site_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_explorer_site_module)


def test_build_explorer_site_copies_only_deployable_assets(tmp_path: Path) -> None:
    """Static bundle should contain the Explorer, manifest and referenced preview images."""
    output_dir = tmp_path / "explorer"
    copied = build_explorer_site_module.build_explorer_site(output_dir)
    manifest_path = output_dir / "data/manifests/firms_next_day_explorer_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert output_dir.joinpath("index.html").exists()
    assert output_dir.joinpath("styles.css").exists()
    assert output_dir.joinpath("app.js").exists()
    assert manifest_path.exists()
    assert not output_dir.joinpath(".env").exists()
    assert not output_dir.joinpath("pyproject.toml").exists()
    assert len(copied) == 4 + len(manifest["cases"])

    for case in manifest["cases"]:
        assert output_dir.joinpath(case["preview_png"]).exists()


def test_frontend_asset_paths_support_repo_and_static_bundle() -> None:
    """Frontend path logic should support /frontend/ and root static deployments."""
    app_js = REPO_ROOT.joinpath("frontend/app.js").read_text(encoding="utf-8")

    assert 'includes("/frontend/") ? "../" : "./"' in app_js
    assert 'assetUrl("data/manifests/firms_next_day_explorer_manifest.json")' in app_js
