"""Build FIRMS hotspot progression label artifacts for pilot fires."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from firetwin.data.clients import FIRMSClient
from firetwin.data.firms_labels import (
    FIRMSLabelConfig,
    build_firms_label_artifact,
    fetch_or_load_firms_records,
    render_firms_label_summary_markdown,
)
from firetwin.data.progression_audit import PilotFireSpec


@dataclass(frozen=True)
class PilotLabelSpec:
    """Pilot fire configuration for FIRMS label artifact generation."""

    case_id: str
    fire: PilotFireSpec


PILOT_LABEL_SPECS = [
    PilotLabelSpec(
        case_id="carlton_complex_2014",
        fire=PilotFireSpec(
            name="Carlton Complex",
            year=2014,
            bbox=(-120.5, 47.5, -119.5, 48.5),
            start_date=date(2014, 7, 14),
            end_date=date(2014, 8, 25),
        ),
    ),
    PilotLabelSpec(
        case_id="king_2014",
        fire=PilotFireSpec(
            name="KING",
            year=2014,
            bbox=(-121.5, 38.5, -120.0, 39.5),
            start_date=date(2014, 9, 13),
            end_date=date(2014, 10, 9),
        ),
    ),
    PilotLabelSpec(
        case_id="big_cougar_2014",
        fire=PilotFireSpec(
            name="Big Cougar",
            year=2014,
            bbox=(-117.5, 45.4, -116.2, 46.6),
            start_date=date(2014, 8, 2),
            end_date=date(2014, 9, 15),
        ),
    ),
]


def main() -> bool:
    """Build FIRMS label artifacts for all pilot fires."""
    print("FireTwin FIRMS Progression Label Builder")
    print("=" * 70)

    firms_client = FIRMSClient()
    config = FIRMSLabelConfig(
        time_bin="date",
        min_confidence_score=0.30,
        min_frp_mw=0.0,
        mask_to_final_extent=True,
        use_detection_footprint=True,
    )

    summaries = []
    for spec in PILOT_LABEL_SPECS:
        case_path = Path("data/fire_cases") / f"{spec.case_id}.zarr"
        cache_path = Path("data/raw/firms") / f"{spec.case_id}_firms_detections.csv"
        output_path = Path("data/labels") / f"{spec.case_id}_firms_progression.zarr"

        print(f"\nBuilding {spec.case_id}")
        records = fetch_or_load_firms_records(firms_client, spec.fire, cache_path)
        summary = build_firms_label_artifact(case_path, records, output_path, config)
        summaries.append(summary)
        print(
            f"  input={summary.input_detection_count:,} "
            f"retained={summary.retained_detection_count:,} "
            f"times={summary.time_slice_count:,} "
            f"dates={summary.unique_date_count:,} "
            f"cells={summary.cumulative_positive_cell_count:,}"
        )
        print(f"  wrote {output_path}")

    report_path = Path("reports/firms_label_artifacts.md")
    report_path.write_text(render_firms_label_summary_markdown(summaries), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS label artifact build complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
