"""Evaluate learned next-day FIRMS forecast calibration and thresholds."""

from __future__ import annotations

import os
from pathlib import Path

from firetwin.data.pilot_fires import PILOT_LABEL_SPECS
from firetwin.evaluation.firms_forecasts import (
    ForecastArtifactDiagnostics,
    evaluate_forecast_artifact,
    render_forecast_calibration_report,
)

_CACHE_ROOT = Path("/tmp") / "firetwin_plot_cache"
(_CACHE_ROOT / "matplotlib").mkdir(parents=True, exist_ok=True)
(_CACHE_ROOT / "xdg").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))


def write_reliability_figure(
    diagnostic: ForecastArtifactDiagnostics,
    output_path: Path,
) -> None:
    """Write a compact reliability plot for one forecast diagnostic."""
    import matplotlib.pyplot as plt

    populated_bins = [
        bin_result for bin_result in diagnostic.reliability_bins if bin_result.cell_count
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0.0, 1.0], [0.0, 1.0], color="#666666", linewidth=1.0, linestyle="--")
    ax.scatter(
        [bin_result.mean_prediction for bin_result in populated_bins],
        [bin_result.observed_frequency for bin_result in populated_bins],
        s=[max(20.0, 800.0 * bin_result.cell_fraction) for bin_result in populated_bins],
        color="#d1495b",
        alpha=0.85,
        edgecolor="#2f2f2f",
        linewidth=0.4,
    )
    ax.set_title(diagnostic.summary.case_id)
    ax.set_xlabel("Mean forecast probability")
    ax.set_ylabel("Observed FIRMS frequency")
    ax.set_xlim(0.0, 0.35)
    ax.set_ylim(0.0, 0.35)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> bool:
    """Evaluate all learned forecast artifacts."""
    print("FireTwin FIRMS Next-Day Forecast Calibration")
    print("=" * 70)

    diagnostics = []
    figure_paths: dict[str, str] = {}
    for spec in PILOT_LABEL_SPECS:
        forecast_path = (
            Path("data/forecasts/firms_next_day") / f"{spec.case_id}_learned_forecast.zarr"
        )
        diagnostic = evaluate_forecast_artifact(forecast_path)
        diagnostics.append(diagnostic)

        figure_path = Path("reports/figures") / f"{spec.case_id}_forecast_reliability.png"
        write_reliability_figure(diagnostic, figure_path)
        figure_paths[diagnostic.summary.case_id] = str(figure_path)

        summary = diagnostic.summary
        print(
            f"\n{summary.case_id}: ece={summary.expected_calibration_error:.5f} "
            f"threshold={summary.recommended_threshold:.3f} "
            f"f1={summary.recommended_f1_score:.3f} "
            f"precision={summary.recommended_precision:.3f} "
            f"recall={summary.recommended_recall:.3f}"
        )
        print(f"  wrote {figure_path}")

    report_path = Path("reports/firms_next_day_forecast_calibration.md")
    report_path.write_text(
        render_forecast_calibration_report(diagnostics, figure_paths=figure_paths),
        encoding="utf-8",
    )
    print(f"\nWrote report: {report_path}")
    print("OK FIRMS next-day forecast calibration diagnostics complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
