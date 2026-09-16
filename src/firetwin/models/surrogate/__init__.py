"""Learned surrogate models for simulator-derived fire spread."""

from firetwin.models.surrogate.benchmark import (
    SimulationLatencyBenchmarkRow,
    SimulationLatencyBenchmarkSummary,
    benchmark_simulation_surrogate_latency,
    fire_case_from_simulation_sample,
    render_simulation_latency_report,
)
from firetwin.models.surrogate.simulation import (
    SIMULATION_SURROGATE_MODEL_NAME,
    SimulationSurrogateEvaluation,
    SimulationSurrogateModel,
    SimulationSurrogateTrainingSummary,
    evaluate_simulation_surrogate_leave_one_out,
    fit_and_save_simulation_surrogate,
    load_simulation_surrogate_model,
    predict_simulation_sample,
    render_simulation_surrogate_report,
    save_simulation_surrogate_model,
    train_simulation_surrogate,
)

__all__ = [
    "SIMULATION_SURROGATE_MODEL_NAME",
    "SimulationLatencyBenchmarkRow",
    "SimulationLatencyBenchmarkSummary",
    "SimulationSurrogateEvaluation",
    "SimulationSurrogateModel",
    "SimulationSurrogateTrainingSummary",
    "benchmark_simulation_surrogate_latency",
    "evaluate_simulation_surrogate_leave_one_out",
    "fire_case_from_simulation_sample",
    "fit_and_save_simulation_surrogate",
    "load_simulation_surrogate_model",
    "predict_simulation_sample",
    "render_simulation_latency_report",
    "render_simulation_surrogate_report",
    "save_simulation_surrogate_model",
    "train_simulation_surrogate",
]
