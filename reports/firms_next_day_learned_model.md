# FireTwin FIRMS Next-Day Learned Model Diagnostics

This report evaluates a simple observed-label logistic model with leave-one-fire-out validation.
It predicts next-day FIRMS positive-observation evidence, not perimeter spread.
Thresholded metrics use probability threshold 0.05.

| Holdout case | Training cases | Brier | Persistence Brier | Brier improvement | MAE | Precision | Recall | IoU | Predicted + frac | Target + frac |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| carlton_complex_2014 | king_2014,big_cougar_2014 | 0.00278 | 0.00362 | +0.00084 | 0.03317 | 0.225 | 0.202 | 0.119 | 0.01139 | 0.01266 |
| king_2014 | carlton_complex_2014,big_cougar_2014 | 0.00382 | 0.00462 | +0.00080 | 0.03363 | 0.492 | 0.307 | 0.233 | 0.01487 | 0.02383 |
| big_cougar_2014 | carlton_complex_2014,king_2014 | 0.00631 | 0.01033 | +0.00402 | 0.03383 | 0.168 | 0.144 | 0.084 | 0.03142 | 0.03665 |

## Aggregate

- Mean learned-model Brier: 0.00430
- Mean persistence Brier: 0.00619
- Mean Brier improvement vs persistence: +0.00188

## Interpretation Guardrails

- The model treats no-positive-evidence cells as observed no-evidence labels, which is useful for benchmarking but not identical to true negatives.
- Leave-one-fire-out validation tests cross-fire transfer on only three pilot fires, so results are early diagnostics.
- A model must beat persistence on held-out fires before it is useful for the public FireTwin Explorer forecast layer.
