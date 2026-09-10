"""Tests for progression-label audit helpers."""

from datetime import date, datetime

from firetwin.data.clients import FIRMSDetection, FIRMSSatellite, MTBSFire, NIFCHistoricalPerimeter
from firetwin.data.progression_audit import (
    PilotFireSpec,
    audit_progression_sources,
    date_chunks,
    historical_firms_sources,
    render_progression_audit_markdown,
    summarize_firms_detections,
    summarize_mtbs_fires,
    summarize_nifc_perimeters,
)


def make_nifc_perimeter(date_current: str, acres: float = 100.0) -> NIFCHistoricalPerimeter:
    """Create a minimal NIFC perimeter intersecting the test bbox."""
    return NIFCHistoricalPerimeter(
        incident_name="TEST",
        fire_year=2014,
        gis_acres=acres,
        date_current=date_current,
        unique_fire_id="test",
        irwin_id=None,
        agency=None,
        source=None,
        map_method=None,
        geometry_wkt="POLYGON ((-121 38, -120 38, -120 39, -121 39, -121 38))",
    )


def make_mtbs_fire() -> MTBSFire:
    """Create a minimal MTBS fire intersecting the test bbox."""
    return MTBSFire(
        fire_id="CA00000120140913",
        fire_name="TEST",
        fire_year=2014,
        ignition_date=datetime(2014, 9, 13),
        acres=100.0,
        fire_type="Wildfire",
        geometry_wkt="POLYGON ((-121 38, -120 38, -120 39, -121 39, -121 38))",
    )


def make_firms_detection(acq_date: date, acq_time: str = "1830") -> FIRMSDetection:
    """Create a FIRMS detection for tests."""
    return FIRMSDetection(
        latitude=38.5,
        longitude=-120.5,
        brightness=330.0,
        scan=0.4,
        track=0.4,
        acq_date=acq_date,
        acq_time=acq_time,
        satellite="N",
        instrument="VIIRS",
        confidence="nominal",
        version="2.0",
        frp=25.0,
        daynight="D",
    )


class FakeNIFCClient:
    """Fake NIFC client for audit orchestration tests."""

    def get_fire_by_name(self, fire_name, year=None):
        return [make_nifc_perimeter("20140914000000")]


class FakeMTBSClient:
    """Fake MTBS client for audit orchestration tests."""

    def get_fire_by_name(self, fire_name, year=None):
        return [make_mtbs_fire()]


def test_date_chunks_are_inclusive_and_limited() -> None:
    """FIRMS chunking should obey the current 5-day API window."""
    chunks = list(date_chunks(date(2014, 9, 13), date(2014, 9, 24)))

    assert chunks == [
        (date(2014, 9, 13), date(2014, 9, 17)),
        (date(2014, 9, 18), date(2014, 9, 22)),
        (date(2014, 9, 23), date(2014, 9, 24)),
    ]


def test_historical_firms_sources_include_2014_archives() -> None:
    """2014 fires should use historical standard-processing FIRMS sources."""
    sources = historical_firms_sources(2014)

    assert sources == [FIRMSSatellite.VIIRS_SNPP_SP, FIRMSSatellite.MODIS_SP]


def test_summarize_nifc_perimeters_detects_sparse_progression() -> None:
    """NIFC summary should count unique perimeter timestamps."""
    summary = summarize_nifc_perimeters(
        [
            make_nifc_perimeter("20140914000000", acres=100.0),
            make_nifc_perimeter("20140916000000", acres=200.0),
        ],
        bbox=(-121.5, 37.5, -119.5, 39.5),
    )

    assert summary.status == "available"
    assert summary.observation_count == 2
    assert summary.unique_timestamps == 2
    assert summary.min_acres == 100.0
    assert summary.max_acres == 200.0
    assert "too sparse for hourly labels" in summary.notes[0]


def test_summarize_mtbs_records_final_extent_limitation() -> None:
    """MTBS summary should be explicit that it is not progression data."""
    summary = summarize_mtbs_fires([make_mtbs_fire()], bbox=(-121.5, 37.5, -119.5, 39.5))

    assert summary.status == "available"
    assert summary.unique_dates == 1
    assert "not hourly progression" in summary.notes[0]


def test_summarize_firms_detections_supports_irregular_hotspots() -> None:
    """Multiple FIRMS dates should support hotspot progression candidates."""
    summary = summarize_firms_detections(
        [make_firms_detection(date(2014, 9, 13)), make_firms_detection(date(2014, 9, 14))]
    )

    assert summary.status == "available"
    assert summary.unique_dates == 2
    assert "hotspot/time-window labels" in summary.notes[1]


def test_audit_progression_sources_without_firms_key_marks_next_step() -> None:
    """Audit orchestration should stay useful without FIRMS credentials."""
    spec = PilotFireSpec(
        name="TEST",
        year=2014,
        bbox=(-121.5, 37.5, -119.5, 39.5),
        start_date=date(2014, 9, 13),
        end_date=date(2014, 9, 20),
    )

    result = audit_progression_sources(
        spec,
        nifc_client=FakeNIFCClient(),
        mtbs_client=FakeMTBSClient(),
        firms_client=None,
    )

    assert not result.hourly_labels_defensible
    assert result.firms.status == "missing_credentials"
    assert result.supported_targets == ["final_burned_extent"]
    assert "FIRMS MAP_KEY" in result.recommended_next_step


def test_render_progression_audit_markdown() -> None:
    """Markdown rendering should include source status and conclusion."""
    spec = PilotFireSpec(
        name="TEST",
        year=2014,
        bbox=(-121.5, 37.5, -119.5, 39.5),
        start_date=date(2014, 9, 13),
        end_date=date(2014, 9, 20),
    )
    result = audit_progression_sources(
        spec,
        nifc_client=FakeNIFCClient(),
        mtbs_client=FakeMTBSClient(),
        firms_client=None,
    )

    markdown = render_progression_audit_markdown([result])

    assert "FireTwin Progression Label Audit" in markdown
    assert "missing_credentials" in markdown
    assert "Hourly perimeter labels" in markdown
