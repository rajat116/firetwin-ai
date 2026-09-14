"""Build Phase 5A next-day FIRMS active-fire training samples."""

from pathlib import Path

from firetwin.data.firms_samples import (
    build_firms_next_day_sample_artifact,
    render_firms_next_day_sample_summary_markdown,
)
from firetwin.data.pilot_fires import PILOT_LABEL_SPECS


def main() -> bool:
    """Build per-case next-day FIRMS sample artifacts for all pilot fires."""
    print("FireTwin FIRMS Next-Day Sample Builder")
    print("=" * 70)

    summaries = []
    for spec in PILOT_LABEL_SPECS:
        case_path = Path("data/fire_cases") / f"{spec.case_id}.zarr"
        progression_path = Path("data/labels") / f"{spec.case_id}_firms_progression.zarr"
        initial_state_path = (
            Path("data/initial_states") / f"{spec.case_id}_firms_initial_state.zarr"
        )
        output_path = Path("data/training/firms_next_day") / f"{spec.case_id}_samples.zarr"

        print(f"\nBuilding {spec.case_id}")
        summary = build_firms_next_day_sample_artifact(
            case_path=case_path,
            progression_path=progression_path,
            initial_state_path=initial_state_path,
            output_path=output_path,
        )
        summaries.append(summary)
        print(
            f"  samples={summary.sample_count:,} grid={summary.grid_shape} "
            f"target_positive={summary.target_positive_cell_count:,} "
            f"target_fraction={summary.target_positive_fraction:.5f}"
        )
        print(f"  wrote {output_path}")

    report_path = Path("reports/firms_next_day_samples.md")
    report_path.write_text(
        render_firms_next_day_sample_summary_markdown(summaries),
        encoding="utf-8",
    )
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS next-day sample build complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
