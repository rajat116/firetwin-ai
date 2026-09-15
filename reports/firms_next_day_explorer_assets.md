# FireTwin FIRMS Next-Day Explorer Assets

This report documents Explorer-ready lightweight assets generated from learned next-day FIRMS forecast artifacts.
The assets are intended for a future public Explorer UI and preserve the same scientific guardrails as the model reports.

- Manifest: `data/manifests/firms_next_day_explorer_manifest.json`
- Schema: `firetwin.firms_next_day_explorer.v1`
- Target: `active_fire_detection_probability`

| Case | Sample | Reference time | Target time | Threshold | Brier | ECE | Peak probability | Predicted + frac | Target + frac | Preview |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| carlton_complex_2014 | 4 | 2014-07-18T00:00:00 | 2014-07-19T00:00:00 | 0.050 | 0.00278 | 0.02462 | 0.470 | 0.15377 | 0.03273 | `reports/figures/carlton_complex_2014_explorer_forecast_preview.png` |
| king_2014 | 4 | 2014-09-18T00:00:00 | 2014-09-19T00:00:00 | 0.050 | 0.00382 | 0.01871 | 0.216 | 0.08094 | 0.06150 | `reports/figures/king_2014_explorer_forecast_preview.png` |
| big_cougar_2014 | 5 | 2014-08-08T00:00:00 | 2014-08-09T00:00:00 | 0.025 | 0.00631 | 0.01018 | 0.753 | 0.07171 | 0.03004 | `reports/figures/big_cougar_2014_explorer_forecast_preview.png` |

## Guardrails

- Research prototype; not for operational wildfire response, evacuation planning or safety-critical decisions.
- Forecasts estimate satellite-visible FIRMS active-fire evidence, not exact burned perimeter spread.
- Cells without FIRMS detections are no-positive-evidence cells, not confirmed unburned cells.
- Recommended thresholds are display diagnostics, not emergency decision thresholds.
