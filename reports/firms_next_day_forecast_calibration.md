# FireTwin FIRMS Next-Day Forecast Calibration

This report evaluates calibration and threshold behavior for leave-one-fire-out learned forecast artifacts.
Targets are FIRMS positive-observation evidence, not exact perimeter spread.

| Case | Samples | Grid | Brier | MAE | ECE | Max calib error | Recommended threshold | Precision | Recall | F1 | IoU | Predicted + frac | Target + frac |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| carlton_complex_2014 | 28 | 662x493 | 0.00278 | 0.03317 | 0.02462 | 0.33546 | 0.050 | 0.225 | 0.202 | 0.213 | 0.119 | 0.01139 | 0.01266 |
| king_2014 | 23 | 462x312 | 0.00382 | 0.03363 | 0.01871 | 0.30488 | 0.050 | 0.492 | 0.307 | 0.378 | 0.233 | 0.01487 | 0.02383 |
| big_cougar_2014 | 8 | 349x239 | 0.00631 | 0.03383 | 0.01018 | 0.70755 | 0.025 | 0.149 | 0.195 | 0.169 | 0.092 | 0.04805 | 0.03665 |

## Aggregate

- Mean observed-label Brier: 0.00430
- Mean observed-label ECE: 0.01784
- Recommended threshold candidates: 0.025, 0.050

## Reliability Figures

- big_cougar_2014: `reports/figures/big_cougar_2014_forecast_reliability.png`
- carlton_complex_2014: `reports/figures/carlton_complex_2014_forecast_reliability.png`
- king_2014: `reports/figures/king_2014_forecast_reliability.png`

## Threshold Sweeps

| Case | Threshold | Precision | Recall | F1 | IoU | Predicted + frac | Target + frac |
|---|---:|---:|---:|---:|---:|---:|---:|
| carlton_complex_2014 | 0.010 | 0.013 | 1.000 | 0.025 | 0.013 | 1.00000 | 0.01266 |
| carlton_complex_2014 | 0.025 | 0.013 | 0.965 | 0.026 | 0.013 | 0.93162 | 0.01266 |
| carlton_complex_2014 | 0.050 | 0.225 | 0.202 | 0.213 | 0.119 | 0.01139 | 0.01266 |
| carlton_complex_2014 | 0.075 | 0.238 | 0.141 | 0.177 | 0.097 | 0.00750 | 0.01266 |
| carlton_complex_2014 | 0.100 | 0.248 | 0.098 | 0.140 | 0.075 | 0.00498 | 0.01266 |
| carlton_complex_2014 | 0.150 | 0.271 | 0.046 | 0.079 | 0.041 | 0.00217 | 0.01266 |
| carlton_complex_2014 | 0.200 | 0.297 | 0.022 | 0.041 | 0.021 | 0.00095 | 0.01266 |
| carlton_complex_2014 | 0.300 | 0.309 | 0.004 | 0.008 | 0.004 | 0.00017 | 0.01266 |
| king_2014 | 0.010 | 0.024 | 1.000 | 0.047 | 0.024 | 1.00000 | 0.02383 |
| king_2014 | 0.025 | 0.028 | 0.952 | 0.054 | 0.028 | 0.81460 | 0.02383 |
| king_2014 | 0.050 | 0.492 | 0.307 | 0.378 | 0.233 | 0.01487 | 0.02383 |
| king_2014 | 0.075 | 0.542 | 0.116 | 0.191 | 0.106 | 0.00510 | 0.02383 |
| king_2014 | 0.100 | 0.579 | 0.045 | 0.083 | 0.043 | 0.00185 | 0.02383 |
| king_2014 | 0.150 | 0.598 | 0.009 | 0.017 | 0.009 | 0.00035 | 0.02383 |
| king_2014 | 0.200 | 0.579 | 0.003 | 0.005 | 0.003 | 0.00011 | 0.02383 |
| king_2014 | 0.300 | 0.000 | 0.000 | 0.000 | 0.000 | 0.00000 | 0.02383 |
| big_cougar_2014 | 0.010 | 0.037 | 1.000 | 0.071 | 0.037 | 1.00000 | 0.03665 |
| big_cougar_2014 | 0.025 | 0.149 | 0.195 | 0.169 | 0.092 | 0.04805 | 0.03665 |
| big_cougar_2014 | 0.050 | 0.168 | 0.144 | 0.155 | 0.084 | 0.03142 | 0.03665 |
| big_cougar_2014 | 0.075 | 0.170 | 0.110 | 0.133 | 0.071 | 0.02376 | 0.03665 |
| big_cougar_2014 | 0.100 | 0.171 | 0.089 | 0.118 | 0.062 | 0.01912 | 0.03665 |
| big_cougar_2014 | 0.150 | 0.173 | 0.057 | 0.086 | 0.045 | 0.01212 | 0.03665 |
| big_cougar_2014 | 0.200 | 0.172 | 0.031 | 0.053 | 0.027 | 0.00666 | 0.03665 |
| big_cougar_2014 | 0.300 | 0.175 | 0.013 | 0.025 | 0.013 | 0.00280 | 0.03665 |

## Reliability Bins

| Case | Bin | Probability range | Mean prediction | Observed frequency | Cell fraction |
|---|---:|---|---:|---:|---:|
| carlton_complex_2014 | 0 | [0.00, 0.10] | 0.02883 | 0.00443 | 0.99502 |
| carlton_complex_2014 | 1 | [0.10, 0.20] | 0.13373 | 0.08683 | 0.00403 |
| carlton_complex_2014 | 2 | [0.20, 0.30] | 0.24331 | 0.10404 | 0.00078 |
| carlton_complex_2014 | 3 | [0.30, 0.40] | 0.34599 | 0.11947 | 0.00011 |
| carlton_complex_2014 | 4 | [0.40, 0.50] | 0.43227 | 0.09681 | 0.00006 |
| king_2014 | 0 | [0.00, 0.10] | 0.02689 | 0.00830 | 0.99815 |
| king_2014 | 1 | [0.10, 0.20] | 0.12872 | 0.21722 | 0.00174 |
| king_2014 | 2 | [0.20, 0.30] | 0.21746 | 0.21880 | 0.00011 |
| king_2014 | 3 | [0.30, 0.40] | 0.30488 | 0.00000 | 0.00000 |
| big_cougar_2014 | 0 | [0.00, 0.10] | 0.01974 | 0.01242 | 0.98088 |
| big_cougar_2014 | 1 | [0.10, 0.20] | 0.14281 | 0.05239 | 0.01246 |
| big_cougar_2014 | 2 | [0.20, 0.30] | 0.25610 | 0.04839 | 0.00386 |
| big_cougar_2014 | 3 | [0.30, 0.40] | 0.35120 | 0.05090 | 0.00135 |
| big_cougar_2014 | 4 | [0.40, 0.50] | 0.42969 | 0.04872 | 0.00080 |
| big_cougar_2014 | 5 | [0.50, 0.60] | 0.52403 | 0.03406 | 0.00031 |
| big_cougar_2014 | 6 | [0.60, 0.70] | 0.64330 | 0.06326 | 0.00025 |
| big_cougar_2014 | 7 | [0.70, 0.80] | 0.74090 | 0.03335 | 0.00009 |

## Guardrails

- ECE is computed against observed FIRMS probability labels; no-positive-evidence cells are not confirmed negatives.
- Recommended thresholds are diagnostic display thresholds, not evacuation or operational decision thresholds.
- Reliability should be revisited after adding more fires and richer weather/fuel covariates.
