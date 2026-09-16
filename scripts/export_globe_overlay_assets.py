"""Export transparent globe overlays from committed FIRMS forecast Zarr artifacts."""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import zlib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "data/manifests/firms_next_day_explorer_manifest.json"
DEFAULT_FIGURE_DIR = REPO_ROOT / "reports/figures"


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    """Write an 8-bit RGBA PNG without third-party dependencies."""
    expected_length = width * height * 4
    if len(rgba) != expected_length:
        raise ValueError(f"Expected {expected_length} RGBA bytes, got {len(rgba)}")

    rows = bytearray()
    stride = width * 4
    for row in range(height):
        rows.append(0)
        start = row * stride
        rows.extend(rgba[start : start + stride])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )


def _decompress_chunk(path: Path, zstd_binary: str) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(path)
    return subprocess.check_output([zstd_binary, "-dc", str(path)])


def _load_zarr_array_sample(
    array_root: Path,
    *,
    sample_index: int,
    zstd_binary: str,
) -> tuple[int, int, list[float]]:
    metadata = json.loads(array_root.joinpath("zarr.json").read_text(encoding="utf-8"))
    shape = metadata["shape"]
    chunk_shape = metadata["chunk_grid"]["configuration"]["chunk_shape"]
    dtype = metadata["data_type"]
    if len(shape) != 3 or len(chunk_shape) != 3:
        raise ValueError(f"Expected a 3D sample/y/x array: {array_root}")
    if sample_index < 0 or sample_index >= int(shape[0]):
        raise ValueError(f"Sample index {sample_index} is outside {array_root}")

    sample_chunk = sample_index // int(chunk_shape[0])
    sample_offset = sample_index % int(chunk_shape[0])
    height = int(shape[1])
    width = int(shape[2])
    chunk_height = int(chunk_shape[1])
    chunk_width = int(chunk_shape[2])
    values = [0.0] * (height * width)

    for y_chunk, y_start in enumerate(range(0, height, chunk_height)):
        for x_chunk, x_start in enumerate(range(0, width, chunk_width)):
            chunk_path = array_root / "c" / str(sample_chunk) / str(y_chunk) / str(x_chunk)
            chunk = _decompress_chunk(chunk_path, zstd_binary)
            y_count = min(chunk_height, height - y_start)
            x_count = min(chunk_width, width - x_start)
            for local_y in range(y_count):
                row_offset = ((sample_offset * chunk_height + local_y) * chunk_width) * _dtype_size(
                    dtype
                )
                for local_x in range(x_count):
                    value_offset = row_offset + local_x * _dtype_size(dtype)
                    values[(y_start + local_y) * width + x_start + local_x] = _unpack_value(
                        chunk,
                        value_offset,
                        dtype,
                    )
    return width, height, values


def _dtype_size(dtype: str) -> int:
    if dtype == "float32":
        return 4
    if dtype == "uint8":
        return 1
    raise ValueError(f"Unsupported overlay dtype: {dtype}")


def _unpack_value(chunk: bytes, offset: int, dtype: str) -> float:
    if dtype == "float32":
        value = struct.unpack_from("<f", chunk, offset)[0]
        return 0.0 if not math.isfinite(value) else float(value)
    if dtype == "uint8":
        return float(chunk[offset])
    raise ValueError(f"Unsupported overlay dtype: {dtype}")


def _forecast_color(value: float, *, threshold: float, peak: float) -> tuple[int, int, int, int]:
    if value < threshold:
        return (0, 0, 0, 0)
    span = max(peak - threshold, 0.001)
    t = min(1.0, max(0.0, (value - threshold) / span))
    if t < 0.5:
        local = t / 0.5
        red = 255
        green = round(205 - 82 * local)
        blue = round(70 - 42 * local)
    else:
        local = (t - 0.5) / 0.5
        red = 255
        green = round(123 - 91 * local)
        blue = round(28 - 20 * local)
    alpha = round(72 + 178 * t)
    return (red, green, blue, alpha)


def _forecast_overlay_rgba(values: list[float], *, threshold: float) -> bytes:
    peak = max((value for value in values if math.isfinite(value)), default=threshold)
    rgba = bytearray()
    for value in values:
        rgba.extend(_forecast_color(value, threshold=threshold, peak=peak))
    return bytes(rgba)


def _observed_overlay_rgba(values: list[float]) -> bytes:
    rgba = bytearray()
    for value in values:
        if value > 0:
            rgba.extend((54, 218, 255, 235))
        else:
            rgba.extend((0, 0, 0, 0))
    return bytes(rgba)


def export_case_globe_overlays(
    case: dict[str, Any],
    *,
    figure_dir: Path,
    zstd_binary: str,
) -> dict[str, str]:
    """Export forecast and observed overlays for one manifest case."""
    case_id = str(case["case_id"])
    forecast_path = REPO_ROOT / str(case["forecast_artifact"])
    sample_index = int(case["sample_index"])
    threshold = float(case["recommended_threshold"])

    width, height, probability = _load_zarr_array_sample(
        forecast_path / "forecast_probability",
        sample_index=sample_index,
        zstd_binary=zstd_binary,
    )
    observed_width, observed_height, observed = _load_zarr_array_sample(
        forecast_path / "target_positive_observation_mask",
        sample_index=sample_index,
        zstd_binary=zstd_binary,
    )
    if (width, height) != (observed_width, observed_height):
        raise ValueError(f"Forecast and observed grids disagree for {case_id}")

    forecast_overlay = figure_dir / f"{case_id}_globe_forecast_overlay.png"
    observed_overlay = figure_dir / f"{case_id}_globe_observed_overlay.png"
    write_rgba_png(
        forecast_overlay,
        width,
        height,
        _forecast_overlay_rgba(probability, threshold=threshold),
    )
    write_rgba_png(observed_overlay, width, height, _observed_overlay_rgba(observed))
    return {
        "forecast_overlay_png": forecast_overlay.relative_to(REPO_ROOT).as_posix(),
        "observed_overlay_png": observed_overlay.relative_to(REPO_ROOT).as_posix(),
    }


def export_globe_overlay_assets(
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    figure_dir: Path = DEFAULT_FIGURE_DIR,
    zstd_binary: str = "zstd",
) -> dict[str, Any]:
    """Export all globe overlays and update the Explorer manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for case in manifest["cases"]:
        case.update(
            export_case_globe_overlays(
                case,
                figure_dir=figure_dir,
                zstd_binary=zstd_binary,
            )
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH, type=Path)
    parser.add_argument("--figure-dir", default=DEFAULT_FIGURE_DIR, type=Path)
    parser.add_argument("--zstd-binary", default="zstd")
    args = parser.parse_args()

    manifest = export_globe_overlay_assets(
        manifest_path=args.manifest_path,
        figure_dir=args.figure_dir,
        zstd_binary=args.zstd_binary,
    )
    print(f"Exported globe overlays for {len(manifest['cases'])} cases")


if __name__ == "__main__":
    main()
