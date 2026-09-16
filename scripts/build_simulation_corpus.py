"""Build a Phase 5B synthetic simulation corpus for surrogate development."""

from __future__ import annotations

import argparse
from pathlib import Path

from firetwin.simulation import (
    SimulationCorpusConfig,
    build_simulation_corpus,
    load_simulation_corpus_profiles,
    render_simulation_corpus_report,
    simulation_corpus_profile_report,
)


def main() -> None:
    """Run the Phase 5B corpus builder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=None)
    parser.add_argument(
        "--profiles-path",
        default="configs/simulation_corpus_profiles.json",
        type=Path,
    )
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--output-dir", default=None, type=Path)
    parser.add_argument("--case-count", default=None, type=int)
    parser.add_argument("--grid-height", default=None, type=int)
    parser.add_argument("--grid-width", default=None, type=int)
    parser.add_argument("--resolution-m", default=None, type=float)
    parser.add_argument("--forecast-hours", default=None)
    parser.add_argument("--seed", default=None, type=int)
    parser.add_argument("--report-path", default=None, type=Path)
    args = parser.parse_args()

    profiles = load_simulation_corpus_profiles(args.profiles_path)
    if args.list_profiles:
        print("# Available Phase 5B Simulation Corpus Profiles\n")
        for profile in profiles.values():
            print(simulation_corpus_profile_report(profile))
        return

    profile = profiles.get(args.profile) if args.profile else None
    if args.profile and profile is None:
        raise ValueError(
            f"Unknown corpus profile {args.profile!r}; available: {', '.join(sorted(profiles))}"
        )

    default_config = profile.config if profile else SimulationCorpusConfig()
    forecast_hours = (
        tuple(float(value) for value in args.forecast_hours.split(",") if value)
        if args.forecast_hours
        else default_config.forecast_hours
    )
    config = SimulationCorpusConfig(
        case_count=args.case_count or default_config.case_count,
        grid_height=args.grid_height or default_config.grid_height,
        grid_width=args.grid_width or default_config.grid_width,
        resolution_m=args.resolution_m or default_config.resolution_m,
        forecast_hours=forecast_hours,
        seed=args.seed or default_config.seed,
        base_spread_rate_min_m_h=default_config.base_spread_rate_min_m_h,
        base_spread_rate_max_m_h=default_config.base_spread_rate_max_m_h,
    )
    output_dir = args.output_dir or (
        profile.output_dir if profile else Path("data/simulation/phase5b_synthetic")
    )
    report_path = args.report_path or (
        profile.report_path if profile else Path("reports/phase5b_simulation_corpus.md")
    )
    summary = build_simulation_corpus(
        output_dir=output_dir,
        config=config,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_simulation_corpus_report(summary), encoding="utf-8")
    print(
        "Simulation corpus built: "
        f"{summary.sample_count} samples, "
        f"{summary.total_final_burned_cells:,} final burned cells, "
        f"manifest={summary.manifest_path}, "
        f"report={report_path.as_posix()}"
    )


if __name__ == "__main__":
    main()
