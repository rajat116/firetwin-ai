"""Evaluate Phase 5A next-day FIRMS active-fire baselines."""

from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.evaluation.firms_next_day import (
    evaluate_firms_next_day_baselines,
    render_firms_next_day_baseline_report,
)


def main() -> bool:
    """Evaluate all next-day FIRMS baseline diagnostics."""
    print("FireTwin FIRMS Next-Day Baseline Evaluator")
    print("=" * 70)

    all_results = []
    for spec in PILOT_LABEL_SPECS:
        sample_path = Path("data/training/firms_next_day") / f"{spec.case_id}_samples.zarr"
        print(f"\nEvaluating {spec.case_id}")
        results = evaluate_firms_next_day_baselines(sample_path)
        all_results.extend(results)
        for result in results:
            print(
                f"  {result.baseline}: brier={result.observed_brier_score:.5f} "
                f"precision={result.precision_at_threshold:.3f} "
                f"recall={result.recall_at_threshold:.3f} "
                f"pred_frac={result.predicted_positive_fraction:.5f}"
            )

    report_path = Path("reports/firms_next_day_baselines.md")
    report_path.write_text(render_firms_next_day_baseline_report(all_results), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS next-day baseline evaluation complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
