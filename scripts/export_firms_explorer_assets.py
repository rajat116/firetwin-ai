"""Export learned FIRMS forecasts into lightweight Explorer assets."""

from __future__ import annotations

from pathlib import Path

from firetwin.data.explorer_exports import export_firms_next_day_explorer_assets
from firetwin.data.pilot_fires import PILOT_LABEL_SPECS


def main() -> bool:
    """Generate Explorer manifest and preview figures for all pilot forecasts."""
    print("FireTwin FIRMS Explorer Asset Export")
    print("=" * 70)

    forecast_paths = [
        Path("data/forecasts/firms_next_day") / f"{spec.case_id}_learned_forecast.zarr"
        for spec in PILOT_LABEL_SPECS
    ]
    exports = export_firms_next_day_explorer_assets(
        forecast_paths=forecast_paths,
        manifest_path=Path("data/manifests/firms_next_day_explorer_manifest.json"),
        figure_dir=Path("reports/figures"),
        report_path=Path("reports/firms_next_day_explorer_assets.md"),
    )

    for export in exports:
        print(
            f"\n{export.case_id}: sample={export.sample_index} "
            f"threshold={export.recommended_threshold:.3f} "
            f"peak_probability={export.sample_peak_probability:.3f} "
            f"predicted_positive_fraction={export.sample_predicted_positive_fraction:.5f}"
        )
        print(f"  preview {export.preview_png}")

    print("\nWrote manifest: data/manifests/firms_next_day_explorer_manifest.json")
    print("Wrote report: reports/firms_next_day_explorer_assets.md")
    print("OK FIRMS Explorer assets complete")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
