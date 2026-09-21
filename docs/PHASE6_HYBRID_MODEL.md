# Phase 6 Hybrid Model Plan

**Status**: STARTED  
**Purpose**: Combine the honest observed-label learning path from Phase 5A with the simulator and
surrogate contracts from Phase 5B, while preserving target semantics and no-leakage guardrails.

## Definition Of Hybrid

For FireTwin, a hybrid model is not simply a larger ML model. It must combine:

- **Observed evidence features**: FIRMS initial state, current-day detections, cumulative history,
  terrain, fuel and weather features from Phase 5A samples.
- **Physics/simulator priors**: spread-shape, arrival-likelihood or scenario probability fields
  derived from the Phase 5B simulation/surrogate contract.
- **Learned calibration**: a data-driven layer that decides how much to trust observed evidence and
  physics priors for each forecast setting.

The first committed Phase 6 contract is a convex blend:

```text
hybrid_probability =
  ml_weight * observed_label_ml_probability
  + (1 - ml_weight) * physics_or_simulator_prior
```

This is intentionally simple. It creates the evaluation and artifact contract before adding richer
architecture.

## Phase 6 Entry Contract

- Inputs must be probability arrays with matching shape.
- The observed-label target remains next-day FIRMS positive-observation evidence unless a report
  explicitly states otherwise.
- Final burned extent must not be used as a short-horizon label.
- The physics prior must declare whether it comes from the simulator, surrogate, baseline geometry,
  or another source.
- Hybrid evaluation must report performance against ML-only and physics-only sources.

## Acceptance Criteria

- A hybrid blend utility exists with tests.
- The blend weight is selected from validation data only.
- The hybrid report includes guardrails and target semantics.
- The hybrid result can be packaged into the existing forecast artifact/API shape in a later task.
- A hybrid candidate must beat or tie at least one constituent source before it is promoted in the
  product UI.

## Next Implementation Tasks

1. Generate physics-prior fields aligned to FIRMS next-day sample artifacts.
2. Evaluate leave-one-fire-out hybrid blending on the three pilot fires.
3. Package hybrid forecast artifacts alongside Phase 5A learned forecasts.
4. Export hybrid Explorer preview and globe overlays.
5. Add API/frontend model selection between observed-label ML and hybrid forecasts.

## Guardrails

- Hybrid outputs are still research forecasts.
- FIRMS observed-label learning is not exact perimeter spread.
- Simulator-trained scenario overlays are not observed wildfire truth.
- Operational wildfire response, evacuation planning and safety-critical decisions remain out of
  scope.
