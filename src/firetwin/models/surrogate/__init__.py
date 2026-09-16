"""Learned surrogate models for simulator-derived fire spread."""

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
    "SimulationSurrogateEvaluation",
    "SimulationSurrogateModel",
    "SimulationSurrogateTrainingSummary",
    "evaluate_simulation_surrogate_leave_one_out",
    "fit_and_save_simulation_surrogate",
    "load_simulation_surrogate_model",
    "predict_simulation_sample",
    "render_simulation_surrogate_report",
    "save_simulation_surrogate_model",
    "train_simulation_surrogate",
]
