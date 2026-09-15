# FireTwin FIRMS Next-Day Learned Forecast Artifacts

These are leave-one-fire-out forecast artifacts for next-day FIRMS active-fire evidence.
They are intended for diagnostics and future Explorer layers, not operational spread prediction.

| Case | Training cases | Samples | Grid | Brier | Persistence Brier | Brier improvement | Precision | Recall | IoU | Predicted + frac | Target + frac | Artifact |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| carlton_complex_2014 | king_2014,big_cougar_2014 | 28 | 662x493 | 0.00278 | 0.00362 | +0.00084 | 0.225 | 0.202 | 0.119 | 0.01139 | 0.01266 | `data/forecasts/firms_next_day/carlton_complex_2014_learned_forecast.zarr` |
| king_2014 | carlton_complex_2014,big_cougar_2014 | 23 | 462x312 | 0.00382 | 0.00462 | +0.00080 | 0.492 | 0.307 | 0.233 | 0.01487 | 0.02383 | `data/forecasts/firms_next_day/king_2014_learned_forecast.zarr` |
| big_cougar_2014 | carlton_complex_2014,king_2014 | 8 | 349x239 | 0.00631 | 0.01033 | +0.00402 | 0.168 | 0.144 | 0.084 | 0.03142 | 0.03665 | `data/forecasts/firms_next_day/big_cougar_2014_learned_forecast.zarr` |

## Aggregate

- Mean learned-forecast Brier: 0.00430
- Mean persistence Brier: 0.00619
- Mean Brier improvement vs persistence: +0.00188
- Thresholded mask probability cutoff: 0.05

## Artifact Contents

- `forecast_probability`: learned next-day FIRMS positive-observation probability.
- `forecast_positive_mask`: thresholded display/evaluation mask.
- `target_detection_probability` and `target_positive_observation_mask`: observed next-day FIRMS evidence for diagnostics.
- `input_detection_probability` and `input_cumulative_detection_probability`: reference-day FIRMS context for UI comparison.

## Guardrails

- Each forecast is generated with leave-one-fire-out training, so the held-out fire is not used to train its own forecast.
- Final burned extent is excluded as an input.
- Target zeros are no-positive-evidence cells, not confirmed unburned cells.
- These artifacts forecast satellite-observed active-fire evidence, not exact perimeter spread.
