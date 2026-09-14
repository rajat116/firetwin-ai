# FireTwin FIRMS Next-Day Learned Model Diagnostics

This report evaluates a simple observed-label logistic model with leave-one-fire-out validation.
It predicts next-day FIRMS positive-observation evidence, not perimeter spread.

| Holdout case | Training cases | Brier | Persistence Brier | Brier improvement | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| carlton_complex_2014 | king_2014,big_cougar_2014 | 0.00279 | 0.00362 | +0.00083 | 0.02419 | 0.277 | 0.049 | 0.043 | 0.00223 | 0.01266 |
| king_2014 | carlton_complex_2014,big_cougar_2014 | 0.00345 | 0.00462 | +0.00116 | 0.02199 | 0.551 | 0.026 | 0.025 | 0.00111 | 0.02383 |
| big_cougar_2014 | carlton_complex_2014,king_2014 | 0.01023 | 0.01033 | +0.00010 | 0.03875 | 0.167 | 0.075 | 0.055 | 0.01651 | 0.03665 |

## Aggregate

- Mean learned-model Brier: 0.00549
- Mean persistence Brier: 0.00619
- Mean Brier improvement vs persistence: +0.00070

## Interpretation Guardrails

- The model treats no-positive-evidence cells as observed no-evidence labels, which is useful for benchmarking but not identical to true negatives.
- Leave-one-fire-out validation tests cross-fire transfer on only three pilot fires, so results are early diagnostics.
- A model must beat persistence on held-out fires before it is useful for the public FireTwin Explorer forecast layer.
