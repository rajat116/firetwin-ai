# FireTwin Phase 5B Simulation Surrogate Latency

- Corpus: `data/simulation/phase5b_synthetic_smoke`
- Model artifact: `data/models/phase5b_surrogate_smoke.npz`
- Samples: 6
- Repetitions per sample: 9
- Warmup runs per sample: 2
- Mean simulator median latency: 77.819 ms
- Mean surrogate median latency: 4.848 ms
- Mean median speedup: 16.31x
- Median of sample speedups: 17.52x

| Case | Cells | Horizons | Simulator median ms | Simulator p95 ms | Surrogate median ms | Surrogate p95 ms | Speedup |
|---|---:|---:|---:|---:|---:|---:|---:|
| phase5b_sim_0000 | 1,600 | 3 | 123.458 | 138.772 | 4.521 | 5.043 | 27.31x |
| phase5b_sim_0001 | 1,600 | 3 | 75.784 | 81.696 | 4.587 | 5.153 | 16.52x |
| phase5b_sim_0002 | 1,600 | 3 | 83.211 | 89.455 | 4.493 | 4.965 | 18.52x |
| phase5b_sim_0003 | 1,600 | 3 | 86.380 | 91.148 | 4.557 | 5.619 | 18.96x |
| phase5b_sim_0004 | 1,600 | 3 | 81.341 | 86.611 | 6.265 | 9.835 | 12.98x |
| phase5b_sim_0005 | 1,600 | 3 | 16.737 | 18.937 | 4.667 | 6.104 | 3.59x |

## Guardrails

- Simulator timings measure `EllipticalBaseline.forecast` on reconstructed in-memory cases.
- Surrogate timings measure artifact-backed NPZ loading, feature construction and prediction.
- These smoke-corpus timings are for engineering direction, not a production SLA.
