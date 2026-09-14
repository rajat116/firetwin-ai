# FireTwin FIRMS Next-Day Baseline Diagnostics

These are observation-label diagnostics for next-day FIRMS active-fire evidence.
Target zeros are positive-unlabeled no-evidence cells, not confirmed unburned cells.

| Case | Baseline | Samples | Brier | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac | Mean pred on target + | Mean pred on unlabeled |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| carlton_complex_2014 | persistence | 28 | 0.00362 | 0.00809 | 0.232 | 0.151 | 0.100 | 0.00823 | 0.01266 | 0.091 | 0.004 |
| carlton_complex_2014 | cumulative_history | 28 | 0.04625 | 0.09459 | 0.015 | 0.195 | 0.014 | 0.16239 | 0.01266 | 0.117 | 0.091 |
| carlton_complex_2014 | fuel_terrain_prior | 28 | 0.10389 | 0.27812 | 0.012 | 0.390 | 0.012 | 0.41010 | 0.01266 | 0.280 | 0.279 |
| king_2014 | persistence | 23 | 0.00462 | 0.01130 | 0.488 | 0.307 | 0.232 | 0.01500 | 0.02383 | 0.179 | 0.005 |
| king_2014 | cumulative_history | 23 | 0.05117 | 0.10064 | 0.054 | 0.407 | 0.050 | 0.17837 | 0.02383 | 0.230 | 0.096 |
| king_2014 | fuel_terrain_prior | 23 | 0.16213 | 0.38059 | 0.022 | 0.714 | 0.021 | 0.78574 | 0.02383 | 0.365 | 0.386 |
| big_cougar_2014 | persistence | 8 | 0.01033 | 0.02385 | 0.172 | 0.108 | 0.071 | 0.02305 | 0.03665 | 0.065 | 0.012 |
| big_cougar_2014 | cumulative_history | 8 | 0.03054 | 0.06778 | 0.051 | 0.140 | 0.039 | 0.10057 | 0.03665 | 0.083 | 0.058 |
| big_cougar_2014 | fuel_terrain_prior | 8 | 0.08057 | 0.26003 | 0.028 | 0.230 | 0.026 | 0.29614 | 0.03665 | 0.251 | 0.264 |

## Baselines

- `persistence`: predicts tomorrow from same-day FIRMS detection probability.
- `cumulative_history`: predicts tomorrow from all prior FIRMS positive evidence.
- `fuel_terrain_prior`: static prior from fuel load, fuel moisture proxy and slope.

## Interpretation Guardrails

- Lower Brier/MAE is better for the observed FIRMS probability proxy.
- Precision/recall/IoU are threshold diagnostics against positive FIRMS observations only.
- These metrics are not perimeter accuracy and should not be reported as operational spread skill.
