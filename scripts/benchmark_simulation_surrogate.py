"""Benchmark Phase 5B simulator and surrogate latency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from firetwin.models.surrogate.benchmark import (
    benchmark_simulation_surrogate_latency,
    render_simulation_latency_report,
)


def main() -> None:
    """Run simulator-vs-surrogate latency benchmarking."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir", default="data/simulation/phase5b_synthetic_smoke", type=Path
    )
    parser.add_argument(
        "--model-path", default="data/models/phase5b_surrogate_smoke.npz", type=Path
    )
    parser.add_argument(
        "--report-path",
        default="reports/phase5b_simulation_surrogate_latency.md",
        type=Path,
    )
    parser.add_argument(
        "--metrics-json",
        default="reports/phase5b_simulation_surrogate_latency_metrics.json",
        type=Path,
    )
    parser.add_argument("--repetitions", default=9, type=int)
    parser.add_argument("--warmup", default=2, type=int)
    parser.add_argument("--max-samples", default=None, type=int)
    args = parser.parse_args()

    summary, rows = benchmark_simulation_surrogate_latency(
        corpus_dir=args.corpus_dir,
        model_path=args.model_path,
        repetitions=args.repetitions,
        warmup=args.warmup,
        max_samples=args.max_samples,
    )

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(render_simulation_latency_report(summary, rows), encoding="utf-8")
    args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_json.write_text(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "rows": [row.to_dict() for row in rows],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "Simulation surrogate latency benchmarked: "
        f"speedup={summary.mean_median_speedup:.2f}x, "
        f"surrogate_median={summary.mean_surrogate_median_ms:.3f}ms, "
        f"simulator_median={summary.mean_simulator_median_ms:.3f}ms"
    )


if __name__ == "__main__":
    main()
