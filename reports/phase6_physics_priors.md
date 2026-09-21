# FireTwin Phase 6 Physics-Prior Artifacts

These artifacts provide sample-aligned physics-style priors for hybrid blending.
They use same-day FIRMS evidence, cumulative history, fuel/terrain susceptibility and
reference-time wind. They do not use final burned extent or next-day targets as inputs.

| Case | Samples | Grid | Brier | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac | Artifact |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| carlton_complex_2014 | 28 | 662x493 | 0.00526 | 0.04639 | 0.015 | 0.347 | 0.014 | 0.29993 | 0.01266 | `data/forecasts/phase6_physics_priors/carlton_complex_2014_physics_prior.zarr` |
| king_2014 | 23 | 462x312 | 0.00705 | 0.06071 | 0.043 | 0.610 | 0.042 | 0.33595 | 0.02383 | `data/forecasts/phase6_physics_priors/king_2014_physics_prior.zarr` |
| big_cougar_2014 | 8 | 349x239 | 0.00866 | 0.05085 | 0.049 | 0.248 | 0.043 | 0.18482 | 0.03665 | `data/forecasts/phase6_physics_priors/big_cougar_2014_physics_prior.zarr` |

## Interpretation Guardrails

- This is a prior field for Phase 6 hybrid experiments, not an operational spread forecast.
- Metrics are against FIRMS positive-observation evidence, not verified perimeter growth.
- The prior is deterministic and intentionally simple so the hybrid evaluation can compare
  ML-only, physics-only and blended probabilities with matching tensor shapes.
