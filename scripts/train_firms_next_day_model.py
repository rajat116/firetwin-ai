"""Train and evaluate the first learned next-day FIRMS active-fire model."""

from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.models.firms_next_day import (
    evaluate_learned_model_leave_one_fire_out,
    render_learned_model_report,
)


def main() -> bool:
    """Run leave-one-fire-out diagnostics for the learned next-day FIRMS model."""
    print("FireTwin FIRMS Next-Day Learned Model")
    print("=" * 70)

    sample_paths = [
        Path("data/training/firms_next_day") / f"{spec.case_id}_samples.zarr"
        for spec in PILOT_LABEL_SPECS
    ]
    results = evaluate_learned_model_leave_one_fire_out(sample_paths)
    for result in results:
        print(
            f"\nHoldout {result.case_id}: brier={result.observed_brier_score:.5f} "
            f"persistence={result.persistence_brier_score:.5f} "
            f"improvement={result.brier_improvement_vs_persistence:+.5f} "
            f"precision={result.precision_at_threshold:.3f} "
            f"recall={result.recall_at_threshold:.3f}"
        )

    report_path = Path("reports/firms_next_day_learned_model.md")
    report_path.write_text(render_learned_model_report(results), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS next-day learned model diagnostics complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
