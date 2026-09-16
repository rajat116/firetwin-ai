"""Build a Phase 5B synthetic simulation corpus for surrogate development."""

from __future__ import annotations

import argparse
from pathlib import Path

from firetwin.simulation import (
    SimulationCorpusConfig,
    build_simulation_corpus,
    render_simulation_corpus_report,
)


def main() -> None:
    """Run the Phase 5B corpus builder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data/simulation/phase5b_synthetic", type=Path)
    parser.add_argument("--case-count", default=24, type=int)
    parser.add_argument("--grid-height", default=64, type=int)
    parser.add_argument("--grid-width", default=64, type=int)
    parser.add_argument("--resolution-m", default=60.0, type=float)
    parser.add_argument("--forecast-hours", default="3,6,12,24")
    parser.add_argument("--seed", default=1729, type=int)
    parser.add_argument("--report-path", default="reports/phase5b_simulation_corpus.md", type=Path)
    args = parser.parse_args()

    forecast_hours = tuple(float(value) for value in args.forecast_hours.split(",") if value)
    summary = build_simulation_corpus(
        output_dir=args.output_dir,
        config=SimulationCorpusConfig(
            case_count=args.case_count,
            grid_height=args.grid_height,
            grid_width=args.grid_width,
            resolution_m=args.resolution_m,
            forecast_hours=forecast_hours,
            seed=args.seed,
        ),
    )
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(render_simulation_corpus_report(summary), encoding="utf-8")
    print(
        "Simulation corpus built: "
        f"{summary.sample_count} samples, "
        f"{summary.total_final_burned_cells:,} final burned cells, "
        f"manifest={summary.manifest_path}"
    )


if __name__ == "__main__":
    main()
