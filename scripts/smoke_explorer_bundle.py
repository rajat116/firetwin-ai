"""Smoke-test a deployable FireTwin Explorer static bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import zlib
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
    "persistence_brier_score",
    "brier_improvement_vs_persistence",
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
    "brierImprovement",
    "persistenceBrier",
    "forecastFootprint",
    "observedEvidence",
    "evidenceBalance",
)


def _paeth_predictor(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    distance_left = abs(estimate - left)
    distance_above = abs(estimate - above)
    distance_upper_left = abs(estimate - upper_left)
    if distance_left <= distance_above and distance_left <= distance_upper_left:
        return left
    if distance_above <= distance_upper_left:
        return above
    return upper_left


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_probability(case: dict[str, Any], field: str) -> None:
    value = float(case[field])
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{case.get('case_id', '<unknown>')} has invalid {field}: {value}")


def _decode_png_rgba(path: Path) -> tuple[int, int, bytes]:
    content = path.read_bytes()
    if content[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Preview is not a PNG: {path}")

    offset = 8
    width: int | None = None
    height: int | None = None
    bit_depth: int | None = None
    color_type: int | None = None
    interlace_method: int | None = None
    compressed = bytearray()

    while offset < len(content):
        if offset + 8 > len(content):
            raise ValueError(f"Malformed PNG chunk header: {path}")
        chunk_length = struct.unpack(">I", content[offset : offset + 4])[0]
        chunk_type = content[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_length
        if chunk_end + 4 > len(content):
            raise ValueError(f"Malformed PNG chunk payload: {path}")
        chunk_data = content[chunk_start:chunk_end]
        offset = chunk_end + 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace_method = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError(f"PNG is missing IHDR metadata: {path}")
    if bit_depth != 8 or color_type not in {2, 6} or interlace_method != 0:
        raise ValueError(
            f"Unsupported PNG format for visual smoke test: "
            f"bit_depth={bit_depth}, color_type={color_type}, interlace={interlace_method}"
        )

    channels = 4 if color_type == 6 else 3
    bytes_per_pixel = channels
    row_width = width * channels
    decompressed = zlib.decompress(bytes(compressed))
    expected_length = (row_width + 1) * height
    if len(decompressed) != expected_length:
        raise ValueError(f"Unexpected PNG pixel buffer length for {path}")

    rows: list[bytes] = []
    previous = bytes(row_width)
    read_offset = 0
    for _ in range(height):
        filter_type = decompressed[read_offset]
        read_offset += 1
        source = decompressed[read_offset : read_offset + row_width]
        read_offset += row_width
        current = bytearray(row_width)
        for index, value in enumerate(source):
            left = current[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                restored = value
            elif filter_type == 1:
                restored = value + left
            elif filter_type == 2:
                restored = value + above
            elif filter_type == 3:
                restored = value + ((left + above) // 2)
            elif filter_type == 4:
                restored = value + _paeth_predictor(left, above, upper_left)
            else:
                raise ValueError(f"Unsupported PNG row filter {filter_type} in {path}")
            current[index] = restored & 0xFF
        rows.append(bytes(current))
        previous = bytes(current)

    return width, height, b"".join(rows)


def _assert_png(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size < 10_000:
        raise ValueError(f"Preview PNG is unexpectedly small: {path}")
    width, height, pixels = _decode_png_rgba(path)
    if width < 1000 or height < 400:
        raise ValueError(f"Preview PNG is too small for demo QA: {path} ({width}x{height})")

    sample_step = max(1, len(pixels) // 80_000)
    sampled = pixels[::sample_step]
    min_pixel = min(sampled)
    max_pixel = max(sampled)
    if max_pixel - min_pixel < 24:
        raise ValueError(f"Preview PNG appears visually blank or flat: {path}")

    return {
        "path": path.as_posix(),
        "width": width,
        "height": height,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pixel_range": max_pixel - min_pixel,
    }


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

    previews: list[dict[str, Any]] = []
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
            "persistence_brier_score",
            "recommended_f1_score",
            "recommended_precision",
            "recommended_recall",
            "recommended_threshold",
            "sample_peak_probability",
            "sample_predicted_positive_fraction",
            "sample_target_positive_fraction",
        ):
            _assert_probability(case, field)
        improvement = float(case["brier_improvement_vs_persistence"])
        if not math.isfinite(improvement):
            raise ValueError(f"{case['case_id']} has invalid Brier improvement")
        if improvement <= 0:
            raise ValueError(f"{case['case_id']} does not beat persistence by Brier score")

        preview_path = Path(case["preview_png"])
        if preview_path.is_absolute() or ".." in preview_path.parts:
            raise ValueError(f"Unsafe preview path in manifest: {preview_path}")
        preview = _assert_png(bundle_dir / preview_path)
        preview["manifest_path"] = case["preview_png"]
        previews.append(preview)

    unique_preview_hashes = {preview["sha256"] for preview in previews}
    if len(unique_preview_hashes) != len(previews):
        raise ValueError("Explorer preview PNGs should be distinct across cases")

    for leaked_name in (".env", "pyproject.toml", ".git"):
        if bundle_dir.joinpath(leaked_name).exists():
            raise ValueError(f"Static bundle leaked repository/private file: {leaked_name}")

    return {
        "case_count": len(cases),
        "guardrail_count": len(manifest["guardrails"]),
        "preview_count": len(previews),
        "previews": previews,
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
