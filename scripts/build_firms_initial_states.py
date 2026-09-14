"""Build FIRMS-derived initial-state artifacts for pilot fires."""

from pathlib import Path

from firetwin.data.clients import FIRMSClient
from firetwin.data.firms_labels import (
    FIRMSInitialStateConfig,
    build_firms_initial_state_artifact,
    fetch_or_load_firms_records,
    render_firms_initial_state_summary_markdown,
)
from firetwin.data.pilot_fires import PILOT_LABEL_SPECS


def main() -> bool:
    """Build FIRMS initial-state artifacts for all pilot fires."""
    print("FireTwin FIRMS Initial-State Builder")
    print("=" * 70)

    firms_client = FIRMSClient()
    config = FIRMSInitialStateConfig(
        initial_window_hours=24.0,
        min_confidence_score=0.30,
        min_frp_mw=0.0,
        use_detection_footprint=True,
    )

    summaries = []
    for spec in PILOT_LABEL_SPECS:
        case_path = Path("data/fire_cases") / f"{spec.case_id}.zarr"
        cache_path = Path("data/raw/firms") / f"{spec.case_id}_firms_detections.csv"
        output_path = Path("data/initial_states") / f"{spec.case_id}_firms_initial_state.zarr"

        print(f"\nBuilding {spec.case_id}")
        records = fetch_or_load_firms_records(firms_client, spec.fire, cache_path)
        summary = build_firms_initial_state_artifact(case_path, records, output_path, config)
        summaries.append(summary)
        print(
            f"  input={summary.input_detection_count:,} "
            f"retained={summary.retained_detection_count:,} "
            f"window={summary.window_detection_count:,} "
            f"active_cells={summary.active_cell_count:,}"
        )
        print(
            f"  reference={summary.reference_timestamp} window_end={summary.window_end_timestamp}"
        )
        print(f"  wrote {output_path}")

    report_path = Path("reports/firms_initial_state_artifacts.md")
    report_path.write_text(render_firms_initial_state_summary_markdown(summaries), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS initial-state artifact build complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
