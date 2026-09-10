"""Unit tests for historical fire case builder orchestration."""

from datetime import date

from firetwin.data.case_builder import CaseBuilderConfig, FireCaseBuilder


def test_case_builder_fetches_firms_in_five_day_chunks(monkeypatch) -> None:
    """FIRMS Area API requests should cover the full window in 5-day chunks."""
    calls = []

    class FakeFIRMSClient:
        def __init__(self, map_key: str) -> None:
            assert map_key == "test-key"

        def get_area_detections(self, **kwargs):
            calls.append(kwargs)
            return [kwargs["date"].isoformat()]

    monkeypatch.setattr("firetwin.data.case_builder.FIRMSClient", FakeFIRMSClient)

    builder = FireCaseBuilder(
        CaseBuilderConfig(
            fire_id="test",
            fire_name="Test Fire",
            bbox=(-121.0, 38.0, -120.0, 39.0),
            start_date=date(2014, 9, 13),
            end_date=date(2014, 9, 24),
            firms_map_key="test-key",
            fetch_firms=True,
            fetch_nifc=False,
            fetch_mtbs=False,
            fetch_era5=False,
            fetch_landfire=False,
            fetch_3dep=False,
        )
    )

    data = builder.fetch_all_data()

    assert data["firms"] == ["2014-09-13", "2014-09-18", "2014-09-23"]
    assert [call["day_range"] for call in calls] == [5, 5, 2]
    assert [call["date"] for call in calls] == [
        date(2014, 9, 13),
        date(2014, 9, 18),
        date(2014, 9, 23),
    ]
