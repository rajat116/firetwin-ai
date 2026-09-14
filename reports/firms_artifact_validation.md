# FireTwin FIRMS Artifact Validation

This report compares FIRMS companion artifacts with the final burned extent for context.
The overlap values are diagnostics only; FIRMS detections remain observation evidence, not exact perimeter truth.

| Case | Final cells | FIRMS cumulative cells | FIRMS overlap | FIRMS precision | FIRMS recall | Initial cells | Initial overlap | Initial precision | Initial recall | Figure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| carlton_complex_2014 | 111,486 | 83,333 | 83,333 | 1.000 | 0.747 | 213 | 213 | 1.000 | 0.002 | `reports/figures/carlton_complex_2014_firms_overlay.png` |
| king_2014 | 39,605 | 37,702 | 37,702 | 1.000 | 0.952 | 4,351 | 3,894 | 0.895 | 0.098 | `reports/figures/king_2014_firms_overlay.png` |
| big_cougar_2014 | 26,419 | 20,489 | 20,489 | 1.000 | 0.776 | 1,641 | 1,641 | 1.000 | 0.062 | `reports/figures/big_cougar_2014_firms_overlay.png` |

## Interpretation Guardrails

- Precision here means the fraction of FIRMS-positive cells that fall inside final extent.
- Recall here means the fraction of final burned cells touched by FIRMS-positive evidence.
- FIRMS non-detections remain missing/unobserved, not confirmed unburned.
- Initial-state overlays use earliest-window FIRMS evidence and do not use final extent for QC.
