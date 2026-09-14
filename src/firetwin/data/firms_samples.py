"""Build leakage-safe next-day FIRMS active-fire training samples."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

FIRMS_SAMPLE_VERSION = "phase5a_firms_next_day_v1"


@dataclass(frozen=True)
class FIRMSNextDaySampleSummary:
    """Summary of one generated FIRMS next-day sample artifact."""

    case_id: str
    output_path: str
    sample_count: int
    first_reference_time: str | None
    last_target_time: str | None
    grid_shape: str
    target_positive_cell_count: int
    input_cumulative_positive_cell_count: int
    initial_active_cell_count: int
    target_positive_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""
        return asdict(self)


def _require_vars(ds: xr.Dataset, path: Path, variable_names: list[str]) -> None:
    """Raise a clear error if an artifact is missing required variables."""
    missing = [name for name in variable_names if name not in ds]
    if missing:
        raise ValueError(f"{path} is missing required variables: {', '.join(missing)}")


def _load_daily_progression_arrays(
    progression: xr.Dataset,
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return progression arrays reindexed to a continuous daily calendar."""
    if progression.sizes.get("time", 0) < 2:
        raise ValueError("At least two FIRMS progression time slices are required")

    source_times = pd.DatetimeIndex(progression.coords["time"].values).normalize()
    daily_times = pd.date_range(source_times.min(), source_times.max(), freq="D")
    height = int(progression.sizes["y"])
    width = int(progression.sizes["x"])

    detection_probability = np.zeros((len(daily_times), height, width), dtype=np.float32)
    positive_mask = np.zeros((len(daily_times), height, width), dtype=np.uint8)
    detection_count = np.zeros((len(daily_times), height, width), dtype=np.uint16)

    daily_lookup = {timestamp: index for index, timestamp in enumerate(daily_times)}
    for source_index, timestamp in enumerate(source_times):
        day_index = daily_lookup[timestamp]
        detection_probability[day_index] = np.maximum(
            detection_probability[day_index],
            progression["detection_probability"].isel(time=source_index).values.astype(np.float32),
        )
        positive_mask[day_index] = np.maximum(
            positive_mask[day_index],
            progression["positive_observation_mask"]
            .isel(time=source_index)
            .values.astype(np.uint8),
        )
        detection_count[day_index] = np.maximum(
            detection_count[day_index],
            progression["detection_count"].isel(time=source_index).values.astype(np.uint16),
        )

    cumulative_probability = np.maximum.accumulate(detection_probability, axis=0)
    return (
        daily_times,
        detection_probability,
        positive_mask,
        detection_count,
        cumulative_probability,
    )


def build_firms_next_day_sample_dataset(
    case_path: Path,
    progression_path: Path,
    initial_state_path: Path,
) -> xr.Dataset:
    """Build a per-case next-day FIRMS active-fire sample dataset.

    The target is next-calendar-day FIRMS positive-observation evidence. Zeros are not treated as
    confirmed unburned cells; they are cells without positive satellite evidence in that daily bin.
    """
    case = xr.open_zarr(case_path)
    progression = xr.open_zarr(progression_path)
    initial_state = xr.open_zarr(initial_state_path)
    try:
        _require_vars(
            case,
            case_path,
            [
                "elevation_m",
                "slope_degrees",
                "aspect_degrees",
                "fuel_model",
                "fuel_load_kg_m2",
                "fuel_moisture_percent",
            ],
        )
        _require_vars(
            progression,
            progression_path,
            [
                "detection_probability",
                "positive_observation_mask",
                "detection_count",
            ],
        )
        _require_vars(
            initial_state,
            initial_state_path,
            ["initial_burned_probability", "initial_active_front"],
        )

        if case.attrs.get("target_type") != "final_burned_extent":
            raise ValueError(f"{case_path} must be a final-burned-extent FireCase")
        if progression.attrs.get("target_type") != "active_fire_detection_probability":
            raise ValueError(f"{progression_path} must target active_fire_detection_probability")
        if initial_state.attrs.get("target_type") != "initial_active_fire_state":
            raise ValueError(f"{initial_state_path} must target initial_active_fire_state")
        if initial_state.attrs.get("uses_final_extent_for_qc") != "false":
            raise ValueError("Initial-state artifact must not use final extent for QC")

        (
            daily_times,
            detection_probability,
            positive_mask,
            detection_count,
            cumulative_probability,
        ) = _load_daily_progression_arrays(progression)
        sample_count = len(daily_times) - 1
        if sample_count < 1:
            raise ValueError("At least one next-day sample is required")

        shape = tuple(case["elevation_m"].shape)
        progression_shape = tuple(detection_probability.shape[1:])
        initial_shape = tuple(initial_state["initial_burned_probability"].shape)
        if progression_shape != shape or initial_shape != shape:
            raise ValueError(
                f"Artifact shapes must match FireCase grid: case={shape}, "
                f"progression={progression_shape}, initial={initial_shape}"
            )

        reference_times = daily_times[:-1]
        target_times = daily_times[1:]
        case_id = str(case.attrs.get("case_id", case_path.stem))

        weather_temperature = np.full(
            sample_count, float(case.attrs["temperature_c"]), dtype=np.float32
        )
        weather_rh = np.full(
            sample_count,
            float(case.attrs["relative_humidity_percent"]),
            dtype=np.float32,
        )
        weather_wind_speed = np.full(
            sample_count,
            float(case.attrs["wind_speed_m_s"]),
            dtype=np.float32,
        )
        weather_wind_direction = np.full(
            sample_count,
            float(case.attrs["wind_direction_degrees"]),
            dtype=np.float32,
        )

        ds = xr.Dataset(
            data_vars={
                "elevation_m": (["y", "x"], case["elevation_m"].values.astype(np.float32)),
                "slope_degrees": (["y", "x"], case["slope_degrees"].values.astype(np.float32)),
                "aspect_degrees": (["y", "x"], case["aspect_degrees"].values.astype(np.float32)),
                "fuel_model": (["y", "x"], case["fuel_model"].values.astype(np.int16)),
                "fuel_load_kg_m2": (
                    ["y", "x"],
                    case["fuel_load_kg_m2"].values.astype(np.float32),
                ),
                "fuel_moisture_percent": (
                    ["y", "x"],
                    case["fuel_moisture_percent"].values.astype(np.float32),
                ),
                "initial_burned_probability": (
                    ["y", "x"],
                    initial_state["initial_burned_probability"].values.astype(np.float32),
                ),
                "initial_active_front": (
                    ["y", "x"],
                    initial_state["initial_active_front"].values.astype(np.uint8),
                ),
                "input_detection_probability": (
                    ["sample", "y", "x"],
                    detection_probability[:-1],
                ),
                "input_cumulative_detection_probability": (
                    ["sample", "y", "x"],
                    cumulative_probability[:-1],
                ),
                "input_positive_observation_mask": (
                    ["sample", "y", "x"],
                    positive_mask[:-1],
                ),
                "input_detection_count": (
                    ["sample", "y", "x"],
                    detection_count[:-1],
                ),
                "target_detection_probability": (
                    ["sample", "y", "x"],
                    detection_probability[1:],
                ),
                "target_positive_observation_mask": (
                    ["sample", "y", "x"],
                    positive_mask[1:],
                ),
                "target_detection_count": (
                    ["sample", "y", "x"],
                    detection_count[1:],
                ),
                "weather_temperature_c": (["sample"], weather_temperature),
                "weather_relative_humidity_percent": (["sample"], weather_rh),
                "weather_wind_speed_m_s": (["sample"], weather_wind_speed),
                "weather_wind_direction_degrees": (["sample"], weather_wind_direction),
            },
            coords={
                "sample": np.arange(sample_count),
                "reference_time": (["sample"], reference_times.to_numpy(dtype="datetime64[ns]")),
                "target_time": (["sample"], target_times.to_numpy(dtype="datetime64[ns]")),
                "lead_time_hours": (["sample"], np.full(sample_count, 24.0, dtype=np.float32)),
                "y": np.arange(shape[0]),
                "x": np.arange(shape[1]),
            },
            attrs={
                "case_id": case_id,
                "case_name": str(case.attrs.get("name", "")),
                "sample_version": FIRMS_SAMPLE_VERSION,
                "sample_type": "firms_next_day_active_fire_probability",
                "target_type": "active_fire_detection_probability",
                "target_semantics": "next_calendar_day_firms_positive_observation_evidence",
                "positive_unlabeled_semantics": "zeros_are_no_positive_firms_evidence_not_confirmed_unburned",
                "input_modalities": "terrain,fuel_model,weather,firms_initial_state,firms_progression_history",
                "excludes_final_extent_as_input": "true",
                "not_hourly_perimeter_truth": "true",
                "source_case_path": str(case_path),
                "source_progression_path": str(progression_path),
                "source_initial_state_path": str(initial_state_path),
                "grid_crs": str(case.attrs.get("bbox_crs", "")),
                "resolution_m": float(case.attrs["resolution_m"]),
                "bbox_min_x": float(case.attrs["bbox_min_x"]),
                "bbox_min_y": float(case.attrs["bbox_min_y"]),
                "bbox_max_x": float(case.attrs["bbox_max_x"]),
                "bbox_max_y": float(case.attrs["bbox_max_y"]),
                "creation_timestamp": datetime.utcnow().isoformat(),
            },
        )
    finally:
        case.close()
        progression.close()
        initial_state.close()

    ds["target_detection_probability"].attrs = {
        "description": "Next-day FIRMS positive active-fire evidence; zero is not a confirmed negative."
    }
    ds["target_positive_observation_mask"].attrs = {
        "description": "1 where the next day has positive FIRMS evidence; 0 means no positive evidence."
    }
    ds["input_cumulative_detection_probability"].attrs = {
        "description": "Cumulative FIRMS positive evidence available at the reference day."
    }
    return ds


def save_firms_next_day_sample_dataset(ds: xr.Dataset, output_path: Path) -> None:
    """Save a FIRMS next-day sample dataset to Zarr."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(output_path, mode="w")


def build_firms_next_day_sample_artifact(
    case_path: Path,
    progression_path: Path,
    initial_state_path: Path,
    output_path: Path,
) -> FIRMSNextDaySampleSummary:
    """Build and save a FIRMS next-day sample artifact."""
    ds = build_firms_next_day_sample_dataset(case_path, progression_path, initial_state_path)
    save_firms_next_day_sample_dataset(ds, output_path)

    target_positive_cells = int(ds["target_positive_observation_mask"].sum().item())
    input_cumulative_positive_cells = int(
        (ds["input_cumulative_detection_probability"].values > 0).sum()
    )
    initial_active_cells = int(ds["initial_active_front"].sum().item())
    total_target_cells = int(np.prod(ds["target_positive_observation_mask"].shape))

    return FIRMSNextDaySampleSummary(
        case_id=str(ds.attrs["case_id"]),
        output_path=str(output_path),
        sample_count=int(ds.sizes["sample"]),
        first_reference_time=pd.Timestamp(ds.coords["reference_time"].values[0]).isoformat()
        if ds.sizes["sample"]
        else None,
        last_target_time=pd.Timestamp(ds.coords["target_time"].values[-1]).isoformat()
        if ds.sizes["sample"]
        else None,
        grid_shape=f"{ds.sizes['y']}x{ds.sizes['x']}",
        target_positive_cell_count=target_positive_cells,
        input_cumulative_positive_cell_count=input_cumulative_positive_cells,
        initial_active_cell_count=initial_active_cells,
        target_positive_fraction=target_positive_cells / total_target_cells
        if total_target_cells
        else 0.0,
    )


def render_firms_next_day_sample_summary_markdown(
    summaries: list[FIRMSNextDaySampleSummary],
) -> str:
    """Render FIRMS next-day sample artifact summaries as Markdown."""
    lines = [
        "# FireTwin FIRMS Next-Day Sample Artifacts",
        "",
        "These artifacts are Phase 5A supervised-learning samples for next-day FIRMS active-fire evidence.",
        "They are positive-unlabeled observation targets, not exact burned-perimeter labels.",
        "",
        "| Case | Samples | Grid | Target positive cells | Target positive fraction | Initial active cells | First reference | Last target | Artifact |",
        "|---|---:|---|---:|---:|---:|---|---|---|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.case_id} | {summary.sample_count:,} | {summary.grid_shape} | "
            f"{summary.target_positive_cell_count:,} | "
            f"{summary.target_positive_fraction:.5f} | "
            f"{summary.initial_active_cell_count:,} | "
            f"{summary.first_reference_time or '-'} | {summary.last_target_time or '-'} | "
            f"`{summary.output_path}` |"
        )

    lines.extend(
        [
            "",
            "## Semantics",
            "",
            "- Inputs include real terrain, LANDFIRE fuel classes/proxies, ERA5 scalar weather, FIRMS initial state and FIRMS history available at the reference day.",
            "- Targets are next-calendar-day FIRMS positive-observation probability and positive-observation masks.",
            "- Final burned extent is excluded from the sample artifacts as a model input.",
            "- Target zeros mean no positive FIRMS evidence in that daily bin, not confirmed unburned.",
            "- These samples support honest Phase 5A active-fire probability modeling before any simulator-conditioned arrival-time field.",
            "",
        ]
    )
    return "\n".join(lines)
