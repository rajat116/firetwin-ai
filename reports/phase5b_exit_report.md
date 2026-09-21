# FireTwin Phase 5B Exit Report

Phase 5B established the first interactive scenario-inference layer for FireTwin. It is complete as
an engineering milestone for simulator-derived what-if controls, but it is not a real wildfire
spread model and must remain labelled experimental until later hybrid and assimilation phases.

## Completed Scope

- Deterministic synthetic simulation-corpus generation with named smoke, development and showcase
  profiles.
- Committed smoke corpus for CI and demo-contract checks.
- Larger local development corpus report for stronger surrogate iteration.
- Lightweight NumPy logistic surrogate trained on simulator-derived masks.
- Leave-one-simulation-out evaluation against initial-state persistence.
- Latency benchmark comparing the surrogate path with reconstructed `EllipticalBaseline`
  simulation.
- FastAPI scenario endpoints:
  - `GET /api/simulation/samples`
  - `POST /api/simulation/surrogate/{case_id}`
- Scenario controls for wind-speed multiplier, wind-direction delta and spread-rate multiplier.
- Downsampled probability-grid response for browser overlays.
- Globe Explorer wiring for API-backed scenario readouts and probability overlays.
- Public-facing Explorer entry screen with guided demo affordance and 3D globe handoff.
- Local demo runbook for serving the API and Explorer together.

## Key Results

- Development surrogate mean Brier: `0.06998`
- Development persistence mean Brier: `0.18185`
- Mean Brier improvement: `+0.11187`
- Mean IoU at threshold `0.52`: `0.755`
- Development latency benchmark:
  - Simulator median latency mean: `1154.775 ms`
  - Surrogate median latency mean: `9.968 ms`
  - Mean median speedup: `116.78x`

## Product Status

The current public demo can:

- Load three prepared historical fire cases.
- Show FIRMS next-day active-fire prediction previews.
- Open a 3D globe with forecast, observed and scenario layers.
- Call the local scenario API when an API base is provided.
- Update wind/spread scenario summaries and overlay probabilities.

The current public demo cannot yet:

- Assimilate new observations into a live state estimate.
- Run a hybrid real-data physics-ML spread model.
- Provide calibrated ensemble uncertainty for scenario controls.
- Simulate containment/intervention plans.
- Support operational or safety-critical decisions.

## Guardrails

- Phase 5A forecasts target next-calendar-day FIRMS active-fire evidence, not exact burned
  perimeter spread.
- Phase 5B scenario overlays are simulator-trained surrogate outputs, not observed wildfire truth.
- Scenario controls recompute surrogate probabilities from modified covariates; they do not run a
  full physics simulator.
- FireTwin remains a research prototype and is not for operational wildfire response, evacuation
  planning or safety-critical decision-making.

## Exit Gates

- Unit tests pass.
- Ruff lint passes.
- Ruff format check passes.
- MyPy passes.
- Local API health, simulation sample catalog and scenario inference endpoints have been verified.
- Static Explorer bundle can be built and smoke-tested.

## Phase 6 Handoff

Phase 6 should start from the Phase 5B data contracts instead of replacing them:

1. Keep the simulation-corpus NPZ contract as the surrogate training baseline.
2. Add a hybrid model that combines simulator-derived spread features with observed FIRMS sample
   features.
3. Evaluate hybrid forecasts against both simulator masks and FIRMS observed-label artifacts,
   clearly separating target semantics.
4. Preserve the same API shape so the product frontend can switch from baseline surrogate to hybrid
   inference without redesigning the UI.
