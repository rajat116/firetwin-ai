"""Validate and visualize FIRMS label and initial-state companion artifacts."""

from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.evaluation.firms_artifacts import (
    render_firms_artifact_validation_markdown,
    validate_firms_artifacts,
)


def main() -> bool:
    """Validate all generated FIRMS companion artifacts."""
    print("FireTwin FIRMS Artifact Validation")
    print("=" * 70)

    summaries = []
    for spec in PILOT_LABEL_SPECS:
        case_path = Path("data/fire_cases") / f"{spec.case_id}.zarr"
        progression_path = Path("data/labels") / f"{spec.case_id}_firms_progression.zarr"
        initial_state_path = (
            Path("data/initial_states") / f"{spec.case_id}_firms_initial_state.zarr"
        )
        figure_path = Path("reports/figures") / f"{spec.case_id}_firms_overlay.png"

        print(f"\nValidating {spec.case_id}")
        summary = validate_firms_artifacts(
            case_path=case_path,
            progression_path=progression_path,
            initial_state_path=initial_state_path,
            figure_path=figure_path,
        )
        summaries.append(summary)
        print(
            f"  progression precision={summary.progression_precision_vs_final:.3f} "
            f"recall={summary.progression_recall_vs_final:.3f} "
            f"outside={summary.progression_outside_final_cells:,}"
        )
        print(
            f"  initial precision={summary.initial_precision_vs_final:.3f} "
            f"recall={summary.initial_recall_vs_final:.3f} "
            f"outside={summary.initial_outside_final_cells:,}"
        )
        print(f"  wrote {figure_path}")

    report_path = Path("reports/firms_artifact_validation.md")
    report_path.write_text(render_firms_artifact_validation_markdown(summaries), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS artifact validation complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
