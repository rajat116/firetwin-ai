"""Latency benchmarks for Phase 5B simulator and surrogate inference."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from firetwin.models.baselines import EllipticalBaseline
from firetwin.models.surrogate.simulation import (
    load_simulation_surrogate_model,
    predict_simulation_sample,
    sample_paths_from_manifest,
)
from firetwin.schemas import (
    BoundingBox,
    CoordinateSystem,
    FireCase,
    FireCaseMetadata,
    FireState,
    FuelData,
    TerrainData,
    WeatherData,
)


@dataclass(frozen=True)
class SimulationLatencyBenchmarkRow:
    """Latency measurements for one simulation-corpus sample."""

    case_id: str
    grid_cells: int
    horizon_count: int
    repetitions: int
    simulator_median_ms: float
    simulator_p95_ms: float
    surrogate_median_ms: float
    surrogate_p95_ms: float
    median_speedup: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable benchmark row."""
        return asdict(self)


@dataclass(frozen=True)
class SimulationLatencyBenchmarkSummary:
    """Aggregate latency benchmark summary."""

    corpus_dir: str
    model_path: str
    sample_count: int
    repetitions: int
    warmup: int
    mean_simulator_median_ms: float
    mean_surrogate_median_ms: float
    mean_median_speedup: float
    median_of_speedups: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable benchmark summary."""
        return asdict(self)


def benchmark_simulation_surrogate_latency(
    *,
    corpus_dir: Path,
    model_path: Path,
    repetitions: int = 9,
    warmup: int = 2,
    max_samples: int | None = None,
) -> tuple[SimulationLatencyBenchmarkSummary, list[SimulationLatencyBenchmarkRow]]:
    """Benchmark simulator forecasts against trained surrogate predictions.

    The simulator timing measures `EllipticalBaseline.forecast` on a reconstructed in-memory
    `FireCase`. The surrogate timing measures the current artifact-backed inference path,
    including NPZ loading, feature construction and logistic probability prediction.
    """
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")

    model = load_simulation_surrogate_model(model_path)
    sample_paths = sample_paths_from_manifest(corpus_dir)
    if max_samples is not None:
        if max_samples <= 0:
            raise ValueError("max_samples must be positive when provided")
        sample_paths = sample_paths[:max_samples]

    rows = []
    for sample_path in sample_paths:
        case, forecast_hours, base_spread_rate = fire_case_from_simulation_sample(sample_path)
        simulator = EllipticalBaseline(base_spread_rate_m_h=base_spread_rate)

        for _ in range(warmup):
            simulator.forecast(case, forecast_hours)
            predict_simulation_sample(model, sample_path)

        simulator_operation = partial(simulator.forecast, case, forecast_hours)
        surrogate_operation = partial(predict_simulation_sample, model, sample_path)
        simulator_times = [_elapsed_ms(simulator_operation) for _ in range(repetitions)]
        surrogate_times = [_elapsed_ms(surrogate_operation) for _ in range(repetitions)]

        simulator_median = float(np.median(simulator_times))
        surrogate_median = float(np.median(surrogate_times))
        rows.append(
            SimulationLatencyBenchmarkRow(
                case_id=sample_path.stem,
                grid_cells=int(np.prod(case.grid_shape)),
                horizon_count=len(forecast_hours),
                repetitions=repetitions,
                simulator_median_ms=simulator_median,
                simulator_p95_ms=float(np.percentile(simulator_times, 95)),
                surrogate_median_ms=surrogate_median,
                surrogate_p95_ms=float(np.percentile(surrogate_times, 95)),
                median_speedup=simulator_median / max(surrogate_median, 1e-9),
            )
        )

    summary = SimulationLatencyBenchmarkSummary(
        corpus_dir=corpus_dir.as_posix(),
        model_path=model_path.as_posix(),
        sample_count=len(rows),
        repetitions=repetitions,
        warmup=warmup,
        mean_simulator_median_ms=float(np.mean([row.simulator_median_ms for row in rows])),
        mean_surrogate_median_ms=float(np.mean([row.surrogate_median_ms for row in rows])),
        mean_median_speedup=float(np.mean([row.median_speedup for row in rows])),
        median_of_speedups=float(np.median([row.median_speedup for row in rows])),
    )
    return summary, rows


def fire_case_from_simulation_sample(
    sample_path: Path,
) -> tuple[FireCase, list[float], float]:
    """Reconstruct an in-memory `FireCase` from one simulation-corpus NPZ sample."""
    with np.load(sample_path) as sample:
        resolution_m = _resolution_from_sample(sample)
        height, width = sample["initial_burned"].shape
        bbox = BoundingBox(
            min_x=-120.0,
            max_x=-120.0 + width * resolution_m / 111_000.0,
            min_y=40.0,
            max_y=40.0 + height * resolution_m / 111_000.0,
            crs=CoordinateSystem.WGS84,
        )
        timestamp = datetime(2024, 8, 15, 12, 0, 0)
        weather_values = sample["weather"].astype(np.float32)
        initial_burned = sample["initial_burned"].astype(np.int32)
        case = FireCase(
            metadata=FireCaseMetadata(
                case_id=sample_path.stem,
                name=f"Simulation sample {sample_path.stem}",
                description="Reconstructed from Phase 5B simulation-corpus artifact",
                is_synthetic=True,
                source="simulation_corpus",
                tags=["phase5b", "simulation", "benchmark"],
                target_type="simulated_fire_spread_masks",
                data_quality="synthetic_simulator",
                covariate_status="synthetic",
                limitations=["Synthetic simulator corpus; not observed wildfire truth."],
            ),
            terrain=TerrainData(
                elevation_m=sample["elevation_m"].astype(np.float32),
                slope_degrees=sample["slope_degrees"].astype(np.float32),
                aspect_degrees=sample["aspect_degrees"].astype(np.float32),
                resolution_m=resolution_m,
                bbox=bbox,
            ),
            fuels=FuelData(
                fuel_model=sample["fuel_model"].astype(np.int32),
                fuel_load_kg_m2=sample["fuel_load_kg_m2"].astype(np.float32),
                fuel_moisture_percent=sample["fuel_moisture_percent"].astype(np.float32),
                resolution_m=resolution_m,
            ),
            weather=WeatherData(
                wind_speed_m_s=float(weather_values[0]),
                wind_direction_degrees=float(weather_values[1]),
                temperature_c=float(weather_values[2]),
                relative_humidity_percent=float(weather_values[3]),
                timestamp=timestamp,
            ),
            initial_state=FireState(
                burned=initial_burned,
                active_front=initial_burned.copy(),
                timestamp=timestamp,
                resolution_m=resolution_m,
                bbox=bbox,
            ),
        )
        forecast_hours = [float(hour) for hour in sample["forecast_hours"].tolist()]
        base_spread_rate = float(sample["base_spread_rate_m_h"][0])
    return case, forecast_hours, base_spread_rate


def render_simulation_latency_report(
    summary: SimulationLatencyBenchmarkSummary,
    rows: list[SimulationLatencyBenchmarkRow],
) -> str:
    """Render a Markdown report for Phase 5B latency benchmarking."""
    lines = [
        "# FireTwin Phase 5B Simulation Surrogate Latency",
        "",
        f"- Corpus: `{summary.corpus_dir}`",
        f"- Model artifact: `{summary.model_path}`",
        f"- Samples: {summary.sample_count}",
        f"- Repetitions per sample: {summary.repetitions}",
        f"- Warmup runs per sample: {summary.warmup}",
        f"- Mean simulator median latency: {summary.mean_simulator_median_ms:.3f} ms",
        f"- Mean surrogate median latency: {summary.mean_surrogate_median_ms:.3f} ms",
        f"- Mean median speedup: {summary.mean_median_speedup:.2f}x",
        f"- Median of sample speedups: {summary.median_of_speedups:.2f}x",
        "",
        "| Case | Cells | Horizons | Simulator median ms | Simulator p95 ms | Surrogate median ms | Surrogate p95 ms | Speedup |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.case_id} | {row.grid_cells:,} | {row.horizon_count} | "
            f"{row.simulator_median_ms:.3f} | {row.simulator_p95_ms:.3f} | "
            f"{row.surrogate_median_ms:.3f} | {row.surrogate_p95_ms:.3f} | "
            f"{row.median_speedup:.2f}x |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Simulator timings measure `EllipticalBaseline.forecast` on reconstructed in-memory cases.",
            "- Surrogate timings measure artifact-backed NPZ loading, feature construction and prediction.",
            "- These timings are for engineering direction, not a production SLA.",
            "",
        ]
    )
    return "\n".join(lines)


def _elapsed_ms(operation: Callable[[], Any]) -> float:
    start = time.perf_counter()
    operation()
    return (time.perf_counter() - start) * 1000.0


def _resolution_from_sample(sample: Any) -> float:
    if "resolution_m" in getattr(sample, "files", []):
        return float(sample["resolution_m"][0])
    return 60.0
