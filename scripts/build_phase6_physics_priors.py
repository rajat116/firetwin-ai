"""Build Phase 6 physics-prior artifacts aligned to next-day FIRMS samples."""

from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.models.physics_prior import (
    build_physics_prior_artifacts,
    render_physics_prior_report,
)


def main() -> bool:
    """Generate aligned Phase 6 physics priors for all pilot fires."""
    print("FireTwin Phase 6 Physics-Prior Builder")
    print("=" * 70)

    sample_paths = [
        Path("data/training/firms_next_day") / f"{spec.case_id}_samples.zarr"
        for spec in PILOT_LABEL_SPECS
    ]
    summaries = build_physics_prior_artifacts(
        sample_paths=sample_paths,
        output_dir=Path("data/forecasts/phase6_physics_priors"),
    )

    for summary in summaries:
        print(
            f"\nPrior {summary.case_id}: brier={summary.observed_brier_score:.5f} "
            f"precision={summary.precision_at_threshold:.3f} "
            f"recall={summary.recall_at_threshold:.3f} "
            f"pred_frac={summary.predicted_positive_fraction:.5f}"
        )
        print(f"  wrote {summary.output_path}")

    report_path = Path("reports/phase6_physics_priors.md")
    report_path.write_text(render_physics_prior_report(summaries), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK Phase 6 physics-prior artifacts complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
