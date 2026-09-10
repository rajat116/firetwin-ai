"""Audit whether pilot fires can support progression labels."""

from datetime import date
from pathlib import Path

from firetwin.data.clients import FIRMSClient
from firetwin.data.progression_audit import (
    PilotFireSpec,
    audit_progression_sources,
    render_progression_audit_markdown,
)

PILOT_FIRE_SPECS = [
    PilotFireSpec(
        name="Carlton Complex",
        year=2014,
        bbox=(-120.5, 47.5, -119.5, 48.5),
        start_date=date(2014, 7, 14),
        end_date=date(2014, 8, 25),
    ),
    PilotFireSpec(
        name="KING",
        year=2014,
        bbox=(-121.5, 38.5, -120.0, 39.5),
        start_date=date(2014, 9, 13),
        end_date=date(2014, 10, 9),
    ),
    PilotFireSpec(
        name="Big Cougar",
        year=2014,
        bbox=(-117.5, 45.4, -116.2, 46.6),
        start_date=date(2014, 8, 2),
        end_date=date(2014, 9, 15),
    ),
]


def main() -> bool:
    """Run the progression-label audit for all pilot fires."""
    print("FireTwin Progression Label Audit")
    print("=" * 70)

    try:
        firms_client = FIRMSClient()
        print("OK FIRMS MAP_KEY configured; auditing historical detections")
    except ValueError:
        firms_client = None
        print("WARN FIRMS MAP_KEY not configured; FIRMS detection audit skipped")

    results = []
    for spec in PILOT_FIRE_SPECS:
        print(f"\nAuditing {spec.name} ({spec.year})")
        result = audit_progression_sources(spec, firms_client=firms_client)
        results.append(result)
        print(
            f"   NIFC timestamps: {result.nifc.unique_timestamps}; "
            f"FIRMS dates: {result.firms.unique_dates}; "
            f"hourly labels defensible: {result.hourly_labels_defensible}"
        )
        print(f"   Next: {result.recommended_next_step}")

    output_path = Path("reports/progression_label_audit.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_progression_audit_markdown(results), encoding="utf-8")

    print(f"\nWrote audit report: {output_path}")
    print("OK Progression audit complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
