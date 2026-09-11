"""Build uncertainty-aware FIRMS hotspot progression label artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Transformer

from firetwin.data.clients import FIRMSClient, FIRMSDetection, FIRMSSatellite
from firetwin.data.progression_audit import PilotFireSpec, date_chunks, historical_firms_sources

FIRMS_LABEL_VERSION = "phase4e_firms_hotspot_v1"


@dataclass(frozen=True)
class FIRMSLabelConfig:
    """Configuration for FIRMS hotspot label construction."""

    time_bin: str = "date"
    min_confidence_score: float = 0.30
    min_frp_mw: float = 0.0
    mask_to_final_extent: bool = True
    use_detection_footprint: bool = True
    min_footprint_radius_cells: int = 1
    max_footprint_radius_cells: int = 4


@dataclass(frozen=True)
class CaseGrid:
    """Projected FireTwin grid metadata needed for label alignment."""

    case_id: str
    name: str
    width: int
    height: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    crs: str
    resolution_m: float
    final_extent_mask: np.ndarray


@dataclass(frozen=True)
class FIRMSLabelSummary:
    """Summary of one generated FIRMS label artifact."""

    case_id: str
    output_path: str
    input_detection_count: int
    retained_detection_count: int
    time_slice_count: int
    unique_date_count: int
    positive_cell_count: int
    cumulative_positive_cell_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    min_confidence_score: float
    min_frp_mw: float
    mask_to_final_extent: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


def confidence_score(confidence: int | float | str) -> float:
    """Normalize FIRMS confidence values to a 0-1 score."""
    if isinstance(confidence, int | float):
        value = float(confidence)
        return float(np.clip(value if value <= 1.0 else value / 100.0, 0.0, 1.0))

    confidence_text = str(confidence).strip().lower()
    confidence_map = {
        "low": 0.30,
        "l": 0.30,
        "nominal": 0.60,
        "n": 0.60,
        "high": 0.90,
        "h": 0.90,
    }
    if confidence_text in confidence_map:
        return confidence_map[confidence_text]

    try:
        value = float(confidence_text)
    except ValueError:
        return 0.0
    return float(np.clip(value if value <= 1.0 else value / 100.0, 0.0, 1.0))


def detection_records(
    detections: list[FIRMSDetection], source: FIRMSSatellite | str
) -> list[dict[str, Any]]:
    """Convert FIRMS detections to flat records with query-source provenance."""
    source_value = source.value if isinstance(source, FIRMSSatellite) else str(source)
    return [
        {
            "source": source_value,
            "latitude": detection.latitude,
            "longitude": detection.longitude,
            "brightness": detection.brightness,
            "scan": detection.scan,
            "track": detection.track,
            "acq_date": detection.acq_date.isoformat(),
            "acq_time": detection.acq_time,
            "acquisition_datetime": detection.acquisition_datetime.isoformat(),
            "satellite": detection.satellite,
            "instrument": detection.instrument,
            "confidence": detection.confidence,
            "version": detection.version,
            "bright_t31": detection.bright_t31,
            "frp": detection.frp,
            "daynight": detection.daynight,
        }
        for detection in detections
    ]


def read_case_grid(case_path: Path) -> CaseGrid:
    """Read grid metadata and final extent mask from a FireCase Zarr artifact."""
    ds = xr.open_zarr(case_path)
    try:
        final_extent = ds["burned"].isel(time=-1).values.astype(bool)
        height, width = final_extent.shape
        return CaseGrid(
            case_id=str(ds.attrs["case_id"]),
            name=str(ds.attrs["name"]),
            width=int(width),
            height=int(height),
            min_x=float(ds.attrs["bbox_min_x"]),
            min_y=float(ds.attrs["bbox_min_y"]),
            max_x=float(ds.attrs["bbox_max_x"]),
            max_y=float(ds.attrs["bbox_max_y"]),
            crs=str(ds.attrs["bbox_crs"]),
            resolution_m=float(ds.attrs["resolution_m"]),
            final_extent_mask=final_extent,
        )
    finally:
        ds.close()


def fetch_or_load_firms_records(
    client: FIRMSClient,
    spec: PilotFireSpec,
    cache_path: Path,
    sources: list[FIRMSSatellite] | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Fetch FIRMS detections with provenance, or load a cached CSV copy."""
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path)

    records: list[dict[str, Any]] = []
    min_lon, min_lat, max_lon, max_lat = spec.bbox

    for source in sources or historical_firms_sources(spec.year):
        for chunk_start, chunk_end in date_chunks(spec.start_date, spec.end_date):
            day_range = (chunk_end - chunk_start).days + 1
            detections = client.get_area_detections(
                satellite=source,
                min_lon=min_lon,
                min_lat=min_lat,
                max_lon=max_lon,
                max_lat=max_lat,
                day_range=day_range,
                date=chunk_start,
            )
            records.extend(detection_records(detections, source))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame.from_records(records)
    df.to_csv(cache_path, index=False)
    return df


def add_grid_indices(records: pd.DataFrame, grid: CaseGrid) -> pd.DataFrame:
    """Project WGS84 detection coordinates to FireTwin row/column indices."""
    if records.empty:
        return records.assign(row=pd.Series(dtype="int64"), col=pd.Series(dtype="int64"))

    transformer = Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)
    projected_x, projected_y = transformer.transform(
        records["longitude"].to_numpy(dtype=float),
        records["latitude"].to_numpy(dtype=float),
    )

    indexed = records.copy()
    indexed["projected_x"] = projected_x
    indexed["projected_y"] = projected_y
    indexed["col"] = np.floor((indexed["projected_x"] - grid.min_x) / grid.resolution_m).astype(int)
    indexed["row"] = np.floor((grid.max_y - indexed["projected_y"]) / grid.resolution_m).astype(int)
    return indexed


def filter_firms_records(
    records: pd.DataFrame, grid: CaseGrid, config: FIRMSLabelConfig
) -> pd.DataFrame:
    """Apply quality, grid and final-extent filters to FIRMS records."""
    if records.empty:
        return records.copy()

    filtered = records.copy()
    filtered["acquisition_datetime"] = pd.to_datetime(filtered["acquisition_datetime"])
    filtered["confidence_score"] = filtered["confidence"].map(confidence_score)
    filtered["frp"] = pd.to_numeric(filtered["frp"], errors="coerce").fillna(0.0)
    filtered["scan"] = pd.to_numeric(filtered["scan"], errors="coerce").fillna(0.0)
    filtered["track"] = pd.to_numeric(filtered["track"], errors="coerce").fillna(0.0)
    filtered = filtered[
        (filtered["confidence_score"] >= config.min_confidence_score)
        & (filtered["frp"] >= config.min_frp_mw)
    ]
    filtered = add_grid_indices(filtered, grid)
    filtered = filtered[
        (filtered["row"] >= 0)
        & (filtered["row"] < grid.height)
        & (filtered["col"] >= 0)
        & (filtered["col"] < grid.width)
    ]

    if config.mask_to_final_extent and not filtered.empty:
        rows = filtered["row"].to_numpy(dtype=int)
        cols = filtered["col"].to_numpy(dtype=int)
        filtered = filtered[grid.final_extent_mask[rows, cols]]

    return filtered.sort_values("acquisition_datetime").reset_index(drop=True)


def _footprint_radius_cells(record: pd.Series, grid: CaseGrid, config: FIRMSLabelConfig) -> int:
    """Estimate an uncertainty footprint radius from FIRMS scan/track size."""
    if not config.use_detection_footprint:
        return 0

    footprint_m = max(float(record["scan"]), float(record["track"])) * 1000.0
    radius = int(np.ceil((footprint_m / 2.0) / grid.resolution_m))
    return int(
        np.clip(
            max(radius, config.min_footprint_radius_cells),
            config.min_footprint_radius_cells,
            config.max_footprint_radius_cells,
        )
    )


def rasterize_firms_records(
    records: pd.DataFrame, grid: CaseGrid, config: FIRMSLabelConfig
) -> xr.Dataset:
    """Rasterize filtered FIRMS detections into an irregular time-stack label dataset."""
    filtered = filter_firms_records(records, grid, config)
    if config.time_bin not in {"date", "timestamp"}:
        raise ValueError("time_bin must be 'date' or 'timestamp'")

    if config.time_bin == "date":
        filtered["label_time"] = filtered["acquisition_datetime"].dt.normalize()
    else:
        filtered["label_time"] = filtered["acquisition_datetime"]

    times = pd.DatetimeIndex(sorted(filtered["label_time"].unique()))
    time_count = len(times)

    detection_count = np.zeros((time_count, grid.height, grid.width), dtype=np.uint16)
    detection_probability = np.zeros((time_count, grid.height, grid.width), dtype=np.float32)
    frp_max = np.zeros((time_count, grid.height, grid.width), dtype=np.float32)
    time_lookup = {timestamp: index for index, timestamp in enumerate(times)}

    for _, record in filtered.iterrows():
        time_index = time_lookup[pd.Timestamp(record["label_time"])]
        row = int(record["row"])
        col = int(record["col"])
        score = float(record["confidence_score"])
        frp = float(record["frp"])
        radius = _footprint_radius_cells(record, grid, config)

        detection_count[time_index, row, col] += 1
        for rr in range(max(0, row - radius), min(grid.height, row + radius + 1)):
            for cc in range(max(0, col - radius), min(grid.width, col + radius + 1)):
                distance = float(np.hypot(rr - row, cc - col))
                if distance > radius + 0.5:
                    continue
                spatial_weight = 1.0 if radius == 0 else max(0.25, 1.0 - distance / (radius + 1))
                detection_probability[time_index, rr, cc] = max(
                    detection_probability[time_index, rr, cc],
                    np.float32(score * spatial_weight),
                )
                frp_max[time_index, rr, cc] = max(frp_max[time_index, rr, cc], np.float32(frp))

    if config.mask_to_final_extent and time_count:
        detection_probability *= grid.final_extent_mask[np.newaxis, :, :]
        frp_max *= grid.final_extent_mask[np.newaxis, :, :]

    cumulative_probability = (
        np.maximum.accumulate(detection_probability, axis=0)
        if time_count
        else np.zeros_like(detection_probability)
    )
    positive_mask = detection_probability > 0

    ds = xr.Dataset(
        data_vars={
            "detection_count": (["time", "y", "x"], detection_count),
            "detection_probability": (["time", "y", "x"], detection_probability),
            "cumulative_detection_probability": (
                ["time", "y", "x"],
                cumulative_probability.astype(np.float32),
            ),
            "positive_observation_mask": (["time", "y", "x"], positive_mask.astype(np.uint8)),
            "frp_max_mw": (["time", "y", "x"], frp_max),
        },
        coords={
            "time": times.to_numpy(dtype="datetime64[ns]"),
            "y": np.arange(grid.height),
            "x": np.arange(grid.width),
        },
        attrs={
            "case_id": grid.case_id,
            "case_name": grid.name,
            "label_version": FIRMS_LABEL_VERSION,
            "label_type": "irregular_firms_hotspot_progression",
            "time_bin": config.time_bin,
            "target_type": "active_fire_detection_probability",
            "source": "NASA FIRMS MODIS/VIIRS active-fire detections",
            "not_hourly_perimeter_truth": "true",
            "non_detection_semantics": "missing_or_unobserved_not_unburned",
            "uses_final_extent_for_qc": str(config.mask_to_final_extent).lower(),
            "grid_crs": grid.crs,
            "resolution_m": grid.resolution_m,
            "bbox_min_x": grid.min_x,
            "bbox_min_y": grid.min_y,
            "bbox_max_x": grid.max_x,
            "bbox_max_y": grid.max_y,
            "input_detection_count": int(len(records)),
            "retained_detection_count": int(len(filtered)),
            "min_confidence_score": config.min_confidence_score,
            "min_frp_mw": config.min_frp_mw,
            "creation_timestamp": datetime.utcnow().isoformat(),
        },
    )
    ds["detection_count"].attrs = {
        "long_name": "FIRMS detections per central grid cell and timestamp"
    }
    ds["detection_probability"].attrs = {
        "long_name": "FIRMS positive-observation confidence proxy",
        "description": "Positive detection evidence spread over the approximate sensor footprint.",
    }
    ds["cumulative_detection_probability"].attrs = {
        "long_name": "Cumulative FIRMS positive-observation confidence proxy"
    }
    ds["positive_observation_mask"].attrs = {
        "description": "1 where FIRMS provides positive active-fire evidence; 0 is not a negative label."
    }
    ds["frp_max_mw"].attrs = {"units": "MW", "long_name": "Maximum fire radiative power"}
    return ds


def save_firms_label_dataset(ds: xr.Dataset, output_path: Path) -> None:
    """Save a FIRMS label dataset to Zarr."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(output_path, mode="w")


def build_firms_label_artifact(
    case_path: Path,
    records: pd.DataFrame,
    output_path: Path,
    config: FIRMSLabelConfig | None = None,
) -> FIRMSLabelSummary:
    """Build and save a FIRMS label artifact aligned to an existing FireCase."""
    label_config = config or FIRMSLabelConfig()
    grid = read_case_grid(case_path)
    ds = rasterize_firms_records(records, grid, label_config)
    save_firms_label_dataset(ds, output_path)

    times = pd.DatetimeIndex(ds.coords["time"].values)
    positive_cells = int(ds["positive_observation_mask"].sum().item())
    cumulative_positive_cells = int((ds["cumulative_detection_probability"].values > 0).sum())

    return FIRMSLabelSummary(
        case_id=grid.case_id,
        output_path=str(output_path),
        input_detection_count=int(ds.attrs["input_detection_count"]),
        retained_detection_count=int(ds.attrs["retained_detection_count"]),
        time_slice_count=len(times),
        unique_date_count=len({timestamp.date() for timestamp in times}),
        positive_cell_count=positive_cells,
        cumulative_positive_cell_count=cumulative_positive_cells,
        first_timestamp=times[0].isoformat() if len(times) else None,
        last_timestamp=times[-1].isoformat() if len(times) else None,
        min_confidence_score=label_config.min_confidence_score,
        min_frp_mw=label_config.min_frp_mw,
        mask_to_final_extent=label_config.mask_to_final_extent,
    )


def render_firms_label_summary_markdown(summaries: list[FIRMSLabelSummary]) -> str:
    """Render generated FIRMS label summaries as Markdown."""
    lines = [
        "# FireTwin FIRMS Label Artifacts",
        "",
        "These artifacts are irregular active-fire observation labels, not hourly perimeter truth.",
        "",
        "| Case | Input detections | Retained | Time slices | Dates | Positive cells | Cumulative cells | First | Last | Artifact |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.case_id} | {summary.input_detection_count:,} | "
            f"{summary.retained_detection_count:,} | {summary.time_slice_count:,} | "
            f"{summary.unique_date_count:,} | {summary.positive_cell_count:,} | "
            f"{summary.cumulative_positive_cell_count:,} | "
            f"{summary.first_timestamp or '-'} | {summary.last_timestamp or '-'} | "
            f"`{summary.output_path}` |"
        )

    lines.extend(
        [
            "",
            "## Semantics",
            "",
            "- `detection_probability` is positive active-fire evidence from FIRMS confidence, spread over the approximate sensor footprint.",
            "- The default artifact is daily-binned to avoid implying true hourly perimeter labels.",
            "- `positive_observation_mask=0` means missing/unobserved, not confirmed unburned.",
            "- Final burned extent is used only as target-construction quality control to remove unrelated detections inside broad bounding boxes.",
            "- These labels support irregular hotspot/progression learning and assimilation experiments, not exact hourly perimeter evaluation.",
            "",
        ]
    )
    return "\n".join(lines)
