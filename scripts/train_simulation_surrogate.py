"""Train and evaluate the Phase 5B simulation surrogate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from firetwin.models.surrogate import (
    fit_and_save_simulation_surrogate,
    render_simulation_surrogate_report,
)


def main() -> None:
    """Run Phase 5B surrogate training on a simulation corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir", default="data/simulation/phase5b_synthetic_smoke", type=Path
    )
    parser.add_argument(
        "--model-path", default="data/models/phase5b_surrogate_smoke.npz", type=Path
    )
    parser.add_argument(
        "--report-path", default="reports/phase5b_simulation_surrogate.md", type=Path
    )
    parser.add_argument(
        "--metrics-json",
        default="reports/phase5b_simulation_surrogate_metrics.json",
        type=Path,
    )
    parser.add_argument("--seed", default=42, type=int)
    args = parser.parse_args()

    _model, summary, evaluations = fit_and_save_simulation_surrogate(
        corpus_dir=args.corpus_dir,
        model_path=args.model_path,
        random_seed=args.seed,
    )
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(
        render_simulation_surrogate_report(summary, evaluations),
        encoding="utf-8",
    )
    args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_json.write_text(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "evaluations": [evaluation.to_dict() for evaluation in evaluations],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "Simulation surrogate trained: "
        f"mean_iou={summary.mean_iou:.3f}, "
        f"mean_brier={summary.mean_brier_score:.5f}, "
        f"model={summary.model_path}"
    )


if __name__ == "__main__":
    main()
