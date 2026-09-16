"""Build a deployable static bundle for the FireTwin Explorer."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
MANIFEST_PATH = REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"
FRONTEND_FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "globe.html",
    "globe.css",
    "globe.js",
)
CASE_ASSET_FIELDS = (
    "preview_png",
    "forecast_overlay_png",
    "observed_overlay_png",
)


def build_explorer_site(output_dir: Path) -> list[Path]:
    """Copy the Explorer and its allowlisted assets into a static output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []

    for filename in FRONTEND_FILES:
        source = FRONTEND_DIR / filename
        destination = output_dir / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(destination)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_destination = output_dir / "data/manifests" / MANIFEST_PATH.name
    manifest_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_PATH, manifest_destination)
    copied.append(manifest_destination)

    for case in manifest["cases"]:
        for field in CASE_ASSET_FIELDS:
            asset_path = Path(case[field])
            if asset_path.is_absolute() or ".." in asset_path.parts:
                raise ValueError(f"Unsafe {field} path in manifest: {asset_path}")
            source = REPO_ROOT / asset_path
            if not source.is_file():
                raise FileNotFoundError(source)
            destination = output_dir / asset_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(destination)

    return copied


def main() -> None:
    """Build the static Explorer bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist/explorer", type=Path)
    args = parser.parse_args()

    copied = build_explorer_site(args.output_dir)
    print(f"Built FireTwin Explorer static bundle: {args.output_dir}")
    print(f"Copied {len(copied)} files")
    print(f"Open {args.output_dir / 'index.html'} through a static file server.")


if __name__ == "__main__":
    main()
