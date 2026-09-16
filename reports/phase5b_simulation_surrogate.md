# FireTwin Phase 5B Simulation Surrogate

- Model: `phase5b_logistic_simulation_surrogate_v1`
- Corpus: `data/simulation/phase5b_synthetic_smoke`
- Model artifact: `data/models/phase5b_surrogate_smoke.npz`
- Samples: 6
- Features: 23
- Mean Brier: 0.11628
- Mean persistence Brier: 0.20062
- Mean Brier improvement: +0.08434
- Mean IoU @ 0.40: 0.678

| Holdout | Train cases | Brier | Persistence Brier | Improvement | Precision | Recall | IoU | Target + frac | Predicted + frac |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| phase5b_sim_0000 | 5 | 0.14632 | 0.32417 | +0.17785 | 0.764 | 0.971 | 0.747 | 0.327 | 0.416 |
| phase5b_sim_0001 | 5 | 0.15279 | 0.30333 | +0.15055 | 0.813 | 0.936 | 0.770 | 0.306 | 0.353 |
| phase5b_sim_0002 | 5 | 0.11774 | 0.19792 | +0.08018 | 0.820 | 0.899 | 0.751 | 0.201 | 0.221 |
| phase5b_sim_0003 | 5 | 0.08763 | 0.12937 | +0.04174 | 0.782 | 0.883 | 0.708 | 0.132 | 0.149 |
| phase5b_sim_0004 | 5 | 0.10317 | 0.16083 | +0.05767 | 0.927 | 0.546 | 0.524 | 0.164 | 0.097 |
| phase5b_sim_0005 | 5 | 0.09006 | 0.08812 | -0.00193 | 0.916 | 0.598 | 0.567 | 0.091 | 0.060 |

## Guardrails

- This surrogate is trained on simulator-derived synthetic masks, not observed wildfire truth.
- It is a Phase 5B baseline for latency/data-contract work before hybrid modeling.
- Scenario controls should remain labeled experimental until validated on stronger corpora.
