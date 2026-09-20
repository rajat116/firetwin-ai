# FireTwin Phase 5B Simulation Surrogate Latency

- Corpus: `data/simulation/phase5b_synthetic_development`
- Model artifact: `data/models/phase5b_surrogate_development.npz`
- Samples: 12
- Repetitions per sample: 3
- Warmup runs per sample: 1
- Mean simulator median latency: 1154.775 ms
- Mean surrogate median latency: 9.968 ms
- Mean median speedup: 116.78x
- Median of sample speedups: 63.04x

| Case | Cells | Horizons | Simulator median ms | Simulator p95 ms | Surrogate median ms | Surrogate p95 ms | Speedup |
|---|---:|---:|---:|---:|---:|---:|---:|
| phase5b_sim_0000 | 4,096 | 4 | 229.860 | 252.302 | 9.398 | 10.167 | 24.46x |
| phase5b_sim_0001 | 4,096 | 4 | 1117.849 | 1120.220 | 9.313 | 9.374 | 120.03x |
| phase5b_sim_0002 | 4,096 | 4 | 365.487 | 380.794 | 9.241 | 10.704 | 39.55x |
| phase5b_sim_0003 | 4,096 | 4 | 1453.173 | 1496.450 | 9.354 | 10.188 | 155.35x |
| phase5b_sim_0004 | 4,096 | 4 | 2834.611 | 2852.307 | 9.554 | 11.253 | 296.70x |
| phase5b_sim_0005 | 4,096 | 4 | 221.988 | 229.098 | 9.105 | 9.302 | 24.38x |
| phase5b_sim_0006 | 4,096 | 4 | 172.767 | 182.469 | 9.333 | 9.372 | 18.51x |
| phase5b_sim_0007 | 4,096 | 4 | 582.038 | 657.468 | 9.352 | 9.590 | 62.23x |
| phase5b_sim_0008 | 4,096 | 4 | 493.737 | 502.187 | 14.438 | 17.551 | 34.20x |
| phase5b_sim_0009 | 4,096 | 4 | 3271.725 | 3276.236 | 9.341 | 12.650 | 350.26x |
| phase5b_sim_0010 | 4,096 | 4 | 2521.325 | 2548.811 | 11.904 | 11.994 | 211.80x |
| phase5b_sim_0011 | 4,096 | 4 | 592.737 | 600.651 | 9.285 | 10.483 | 63.84x |

## Guardrails

- Simulator timings measure `EllipticalBaseline.forecast` on reconstructed in-memory cases.
- Surrogate timings measure artifact-backed NPZ loading, feature construction and prediction.
- These timings are for engineering direction, not a production SLA.
