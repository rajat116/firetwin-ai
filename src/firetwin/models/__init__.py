"""Fire spread forecast models and baselines."""

from firetwin.models.baselines import EllipticalBaseline, PersistenceBaseline, RadialBaseline
from firetwin.models.firms_next_day import (
    FIRMSForecastArtifactSummary,
    FIRMSLearnedModelResult,
    ObservedLabelLogisticModel,
    build_firms_next_day_forecast_dataset,
    build_leave_one_fire_out_forecast_artifacts,
    evaluate_learned_model_leave_one_fire_out,
    predict_observed_label_probability,
    render_forecast_artifact_report,
    render_learned_model_report,
    train_observed_label_logistic_model,
)

__all__ = [
    "PersistenceBaseline",
    "RadialBaseline",
    "EllipticalBaseline",
    "FIRMSLearnedModelResult",
    "FIRMSForecastArtifactSummary",
    "ObservedLabelLogisticModel",
    "train_observed_label_logistic_model",
    "predict_observed_label_probability",
    "evaluate_learned_model_leave_one_fire_out",
    "render_learned_model_report",
    "build_firms_next_day_forecast_dataset",
    "build_leave_one_fire_out_forecast_artifacts",
    "render_forecast_artifact_report",
]
