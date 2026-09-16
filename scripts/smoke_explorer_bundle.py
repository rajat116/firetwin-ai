"""Smoke-test a deployable FireTwin Explorer static bundle."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_CASE_FIELDS = (
    "case_id",
    "case_name",
    "forecast_semantics",
    "grid_crs",
    "grid_shape",
    "observed_brier_score",
    "preview_png",
    "recommended_f1_score",
    "recommended_precision",
    "recommended_recall",
    "recommended_threshold",
    "reference_time",
    "resolution_m",
    "sample_index",
    "sample_peak_probability",
    "sample_predicted_positive_fraction",
    "sample_target_positive_fraction",
    "target_time",
    "target_type",
)

REQUIRED_FRONTEND_IDS = (
    "caseList",
    "guardrailList",
    "caseName",
    "previewImage",
    "forecastFootprint",
    "observedEvidence",
    "evidenceBalance",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_probability(case: dict[str, Any], field: str) -> None:
    value = float(case[field])
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{case.get('case_id', '<unknown>')} has invalid {field}: {value}")


def _assert_png(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    header = path.read_bytes()[:8]
    if header != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Preview is not a PNG: {path}")
    if path.stat().st_size < 10_000:
        raise ValueError(f"Preview PNG is unexpectedly small: {path}")


def validate_explorer_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Validate that a built Explorer bundle is render-ready and self-contained."""
    index_path = bundle_dir / "index.html"
    app_path = bundle_dir / "app.js"
    styles_path = bundle_dir / "styles.css"
    manifest_path = bundle_dir / "data/manifests/firms_next_day_explorer_manifest.json"

    for path in (index_path, app_path, styles_path, manifest_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    html = index_path.read_text(encoding="utf-8")
    app_js = app_path.read_text(encoding="utf-8")
    manifest = _load_json(manifest_path)

    if "./styles.css" not in html or "./app.js" not in html:
        raise ValueError("Explorer HTML must reference local CSS and JS assets")
    for element_id in REQUIRED_FRONTEND_IDS:
        if element_id not in html and element_id not in app_js:
            raise ValueError(f"Explorer bundle is missing UI hook: {element_id}")
    if "data/manifests/firms_next_day_explorer_manifest.json" not in app_js:
        raise ValueError("Explorer app does not load the committed manifest path")

    if manifest.get("schema_version") != "firetwin.firms_next_day_explorer.v1":
        raise ValueError("Unexpected Explorer manifest schema version")
    if manifest.get("not_operational") is not True:
        raise ValueError("Explorer manifest must retain not_operational=true")
    if manifest.get("target_type") != "active_fire_detection_probability":
        raise ValueError("Explorer manifest target_type is not active-fire probability")
    if len(manifest.get("guardrails", [])) < 3:
        raise ValueError("Explorer manifest should include public-facing guardrails")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        raise ValueError("Explorer manifest should include the three pilot fire cases")

    preview_paths: list[str] = []
    for case in cases:
        missing = [field for field in REQUIRED_CASE_FIELDS if field not in case]
        if missing:
            raise ValueError(f"{case.get('case_id', '<unknown>')} missing fields: {missing}")
        if case["target_type"] != "active_fire_detection_probability":
            raise ValueError(f"{case['case_id']} target_type is not active-fire probability")
        if case["forecast_semantics"] != manifest["forecast_semantics"]:
            raise ValueError(f"{case['case_id']} forecast semantics disagree with manifest")
        for field in (
            "observed_brier_score",
            "recommended_f1_score",
            "recommended_precision",
            "recommended_recall",
            "recommended_threshold",
            "sample_peak_probability",
            "sample_predicted_positive_fraction",
            "sample_target_positive_fraction",
        ):
            _assert_probability(case, field)

        preview_path = Path(case["preview_png"])
        if preview_path.is_absolute() or ".." in preview_path.parts:
            raise ValueError(f"Unsafe preview path in manifest: {preview_path}")
        _assert_png(bundle_dir / preview_path)
        preview_paths.append(case["preview_png"])

    for leaked_name in (".env", "pyproject.toml", ".git"):
        if bundle_dir.joinpath(leaked_name).exists():
            raise ValueError(f"Static bundle leaked repository/private file: {leaked_name}")

    return {
        "case_count": len(cases),
        "guardrail_count": len(manifest["guardrails"]),
        "preview_count": len(preview_paths),
        "previews": preview_paths,
    }


def main() -> None:
    """Run the Explorer bundle smoke test from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", default="dist/explorer", type=Path)
    args = parser.parse_args()

    summary = validate_explorer_bundle(args.bundle_dir)
    print(
        "Explorer smoke test passed: "
        f"{summary['case_count']} cases, "
        f"{summary['guardrail_count']} guardrails, "
        f"{summary['preview_count']} preview PNGs"
    )


if __name__ == "__main__":
    main()
