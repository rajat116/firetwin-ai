"""Audit whether real fire cases can support progression labels."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
from shapely import wkt
from shapely.geometry import box

from firetwin.data.clients import (
    FIRMS_MAX_DAY_RANGE,
    FIRMSClient,
    FIRMSDetection,
    FIRMSSatellite,
    MTBSClient,
    MTBSFire,
    NIFCHistoricalClient,
    NIFCHistoricalPerimeter,
)


@dataclass(frozen=True)
class PilotFireSpec:
    """Pilot fire metadata required for progression-label auditing."""

    name: str
    year: int
    bbox: tuple[float, float, float, float]
    start_date: date
    end_date: date


@dataclass
class ProgressionSourceSummary:
    """Observation availability summary for one progression source."""

    source: str
    status: str
    observation_count: int = 0
    unique_timestamps: int = 0
    unique_dates: int = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    min_acres: float | None = None
    max_acres: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class ProgressionAuditResult:
    """Combined progression-label audit result for one fire."""

    fire_name: str
    fire_year: int
    bbox: tuple[float, float, float, float]
    audit_window: tuple[str, str]
    nifc: ProgressionSourceSummary
    mtbs: ProgressionSourceSummary
    firms: ProgressionSourceSummary
    hourly_labels_defensible: bool
    recommended_next_step: str
    supported_targets: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly representation."""
        return asdict(self)


def _intersects_bbox(geometry_wkt: str, bbox: tuple[float, float, float, float]) -> bool:
    """Return True if a WKT geometry intersects a WGS84 bbox."""
    return bool(wkt.loads(geometry_wkt).intersects(box(*bbox)))


def _iso_timestamp(value: datetime | None) -> str | None:
    """Convert a datetime to ISO text if present."""
    return value.isoformat() if value is not None else None


def date_chunks(
    start_date: date, end_date: date, max_days: int = FIRMS_MAX_DAY_RANGE
) -> Iterator[tuple[date, date]]:
    """Yield inclusive FIRMS date chunks no larger than max_days."""
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    if max_days < 1:
        raise ValueError("max_days must be positive")

    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=max_days - 1), end_date)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def historical_firms_sources(year: int) -> list[FIRMSSatellite]:
    """Return FIRMS sources appropriate for a historical fire year."""
    sources = [FIRMSSatellite.MODIS_SP]
    if year >= 2012:
        sources.insert(0, FIRMSSatellite.VIIRS_SNPP_SP)
    if year >= 2018:
        sources.append(FIRMSSatellite.VIIRS_NOAA20_SP)
    return sources


def summarize_nifc_perimeters(
    perimeters: list[NIFCHistoricalPerimeter],
    bbox: tuple[float, float, float, float],
) -> ProgressionSourceSummary:
    """Summarize NIFC historical perimeter observations inside the fire bbox."""
    matching = [p for p in perimeters if _intersects_bbox(p.geometry_wkt, bbox)]
    timestamps = sorted(dt for p in matching if (dt := p.get_date()) is not None)
    unique_timestamps = sorted(set(timestamps))
    unique_dates = {dt.date() for dt in unique_timestamps}
    acres = [p.gis_acres for p in matching if p.gis_acres > 0]

    summary = ProgressionSourceSummary(
        source="NIFC Historical Perimeters",
        status="available" if matching else "missing",
        observation_count=len(matching),
        unique_timestamps=len(unique_timestamps),
        unique_dates=len(unique_dates),
        first_timestamp=_iso_timestamp(unique_timestamps[0]) if unique_timestamps else None,
        last_timestamp=_iso_timestamp(unique_timestamps[-1]) if unique_timestamps else None,
        min_acres=min(acres) if acres else None,
        max_acres=max(acres) if acres else None,
    )

    if len(unique_timestamps) < 2:
        summary.notes.append("No perimeter progression: source has fewer than 2 timestamps.")
    elif len(unique_timestamps) < 4:
        summary.notes.append("Limited perimeter progression: too sparse for hourly labels.")
    else:
        summary.notes.append("Irregular perimeter progression candidate; still not hourly truth.")

    return summary


def summarize_mtbs_fires(
    fires: list[MTBSFire],
    bbox: tuple[float, float, float, float],
) -> ProgressionSourceSummary:
    """Summarize MTBS final perimeters and ignition metadata inside the fire bbox."""
    matching = [fire for fire in fires if _intersects_bbox(fire.geometry_wkt, bbox)]
    ignition_dates = sorted(fire.ignition_date for fire in matching if fire.ignition_date)
    acres = [fire.acres for fire in matching if fire.acres > 0]

    return ProgressionSourceSummary(
        source="MTBS",
        status="available" if matching else "missing",
        observation_count=len(matching),
        unique_timestamps=len(set(ignition_dates)),
        unique_dates=len({dt.date() for dt in ignition_dates}),
        first_timestamp=_iso_timestamp(ignition_dates[0]) if ignition_dates else None,
        last_timestamp=_iso_timestamp(ignition_dates[-1]) if ignition_dates else None,
        min_acres=min(acres) if acres else None,
        max_acres=max(acres) if acres else None,
        notes=[
            "MTBS supports validated final extent and ignition metadata, not hourly progression."
        ],
    )


def summarize_firms_detections(detections: list[FIRMSDetection]) -> ProgressionSourceSummary:
    """Summarize timestamped FIRMS detections."""
    timestamps = sorted(detection.acquisition_datetime for detection in detections)
    unique_timestamps = sorted(set(timestamps))
    unique_dates = {dt.date() for dt in unique_timestamps}
    frp = [detection.frp for detection in detections]

    summary = ProgressionSourceSummary(
        source="NASA FIRMS",
        status="available" if detections else "missing",
        observation_count=len(detections),
        unique_timestamps=len(unique_timestamps),
        unique_dates=len(unique_dates),
        first_timestamp=_iso_timestamp(unique_timestamps[0]) if unique_timestamps else None,
        last_timestamp=_iso_timestamp(unique_timestamps[-1]) if unique_timestamps else None,
    )

    if frp:
        summary.notes.append(f"FRP range: {float(np.min(frp)):.1f}-{float(np.max(frp)):.1f} MW.")
    if len(unique_dates) >= 2:
        summary.notes.append("Can support irregular hotspot/time-window labels after filtering.")
    else:
        summary.notes.append("Too few detection dates for progression reconstruction.")

    return summary


def fetch_firms_detections(
    client: FIRMSClient,
    spec: PilotFireSpec,
    sources: list[FIRMSSatellite] | None = None,
) -> list[FIRMSDetection]:
    """Fetch FIRMS detections over the audit window using current 5-day API chunks."""
    min_lon, min_lat, max_lon, max_lat = spec.bbox
    detections: list[FIRMSDetection] = []

    for source in sources or historical_firms_sources(spec.year):
        for chunk_start, chunk_end in date_chunks(spec.start_date, spec.end_date):
            day_range = (chunk_end - chunk_start).days + 1
            detections.extend(
                client.get_area_detections(
                    satellite=source,
                    min_lon=min_lon,
                    min_lat=min_lat,
                    max_lon=max_lon,
                    max_lat=max_lat,
                    day_range=day_range,
                    date=chunk_start,
                )
            )

    return detections


def classify_progression_support(
    nifc: ProgressionSourceSummary,
    mtbs: ProgressionSourceSummary,
    firms: ProgressionSourceSummary,
) -> tuple[bool, list[str], str]:
    """Classify which target types are defensible from audited observations."""
    _ = mtbs
    supported_targets = ["final_burned_extent"]

    if nifc.unique_timestamps >= 2:
        supported_targets.append("irregular_perimeter_progression")
    if firms.unique_dates >= 2:
        supported_targets.append("active_fire_detection_probability")
        supported_targets.append("irregular_hotspot_progression")

    hourly_labels_defensible = False
    if firms.status == "missing_credentials":
        next_step = "Configure NASA FIRMS MAP_KEY, rerun audit, then decide label strategy."
    elif nifc.unique_timestamps < 2 and firms.unique_dates < 2:
        next_step = "Select newer/better-documented fires or add FIRMS detections before labels."
    else:
        next_step = (
            "Prototype irregular progression labels with uncertainty; do not call them hourly "
            "perimeter truth."
        )

    return hourly_labels_defensible, supported_targets, next_step


def audit_progression_sources(
    spec: PilotFireSpec,
    nifc_client: NIFCHistoricalClient | None = None,
    mtbs_client: MTBSClient | None = None,
    firms_client: FIRMSClient | None = None,
) -> ProgressionAuditResult:
    """Audit available progression sources for one pilot fire."""
    nifc_client = nifc_client or NIFCHistoricalClient()
    mtbs_client = mtbs_client or MTBSClient()

    try:
        nifc_summary = summarize_nifc_perimeters(
            nifc_client.get_fire_by_name(spec.name, year=spec.year),
            spec.bbox,
        )
    except Exception as exc:
        nifc_summary = ProgressionSourceSummary(
            source="NIFC Historical Perimeters",
            status="error",
            notes=[str(exc)],
        )

    try:
        mtbs_summary = summarize_mtbs_fires(
            mtbs_client.get_fire_by_name(spec.name, year=spec.year),
            spec.bbox,
        )
    except Exception as exc:
        mtbs_summary = ProgressionSourceSummary(
            source="MTBS",
            status="error",
            notes=[str(exc)],
        )

    if firms_client is None:
        firms_summary = ProgressionSourceSummary(
            source="NASA FIRMS",
            status="missing_credentials",
            notes=["FIRMS MAP_KEY is required for historical detection audit."],
        )
    else:
        try:
            firms_summary = summarize_firms_detections(fetch_firms_detections(firms_client, spec))
        except Exception as exc:
            firms_summary = ProgressionSourceSummary(
                source="NASA FIRMS",
                status="error",
                notes=[str(exc)],
            )

    hourly, targets, next_step = classify_progression_support(
        nifc_summary,
        mtbs_summary,
        firms_summary,
    )

    return ProgressionAuditResult(
        fire_name=spec.name,
        fire_year=spec.year,
        bbox=spec.bbox,
        audit_window=(spec.start_date.isoformat(), spec.end_date.isoformat()),
        nifc=nifc_summary,
        mtbs=mtbs_summary,
        firms=firms_summary,
        hourly_labels_defensible=hourly,
        recommended_next_step=next_step,
        supported_targets=targets,
    )


def render_progression_audit_markdown(results: list[ProgressionAuditResult]) -> str:
    """Render progression audit results as Markdown."""
    lines = [
        "# FireTwin Progression Label Audit",
        "",
        "This report audits whether current pilot fires support time-resolved labels.",
        "",
        "Hourly perimeter labels are treated as unsupported unless timestamped observations prove otherwise.",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"## {result.fire_name} ({result.fire_year})",
                "",
                f"- Audit window: {result.audit_window[0]} to {result.audit_window[1]}",
                f"- Hourly labels defensible: {result.hourly_labels_defensible}",
                f"- Supported targets: {', '.join(result.supported_targets)}",
                f"- Recommended next step: {result.recommended_next_step}",
                "",
                "| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |",
                "|---|---:|---:|---:|---:|---|---|---|",
            ]
        )
        for summary in [result.nifc, result.mtbs, result.firms]:
            notes = " ".join(summary.notes)
            lines.append(
                "| "
                f"{summary.source} | {summary.status} | {summary.observation_count} | "
                f"{summary.unique_timestamps} | {summary.unique_dates} | "
                f"{summary.first_timestamp or '-'} | {summary.last_timestamp or '-'} | "
                f"{notes or '-'} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Conclusion",
            "",
            "The current pilot artifacts remain final-extent cases until FIRMS detections or other "
            "timestamped progression observations are audited and converted into uncertainty-aware labels.",
            "",
        ]
    )
    return "\n".join(lines)
