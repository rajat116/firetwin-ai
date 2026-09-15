"""Build learned next-day FIRMS active-fire forecast artifacts."""

from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.models.firms_next_day import (
    build_leave_one_fire_out_forecast_artifacts,
    render_forecast_artifact_report,
)


def main() -> bool:
    """Generate leave-one-fire-out learned forecast artifacts for all pilot fires."""
    print("FireTwin FIRMS Next-Day Learned Forecast Builder")
    print("=" * 70)

    sample_paths = [
        Path("data/training/firms_next_day") / f"{spec.case_id}_samples.zarr"
        for spec in PILOT_LABEL_SPECS
    ]
    output_dir = Path("data/forecasts/firms_next_day")
    summaries = build_leave_one_fire_out_forecast_artifacts(
        sample_paths=sample_paths,
        output_dir=output_dir,
    )

    for summary in summaries:
        print(
            f"\nForecast {summary.case_id}: brier={summary.observed_brier_score:.5f} "
            f"persistence={summary.persistence_brier_score:.5f} "
            f"improvement={summary.brier_improvement_vs_persistence:+.5f} "
            f"precision={summary.precision_at_threshold:.3f} "
            f"recall={summary.recall_at_threshold:.3f}"
        )
        print(f"  wrote {summary.output_path}")

    report_path = Path("reports/firms_next_day_forecasts.md")
    report_path.write_text(render_forecast_artifact_report(summaries), encoding="utf-8")
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS next-day learned forecast artifacts complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
