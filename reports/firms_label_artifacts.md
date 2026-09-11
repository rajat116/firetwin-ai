# FireTwin FIRMS Label Artifacts

These artifacts are irregular active-fire observation labels, not hourly perimeter truth.

| Case | Input detections | Retained | Time slices | Dates | Positive cells | Cumulative cells | First | Last | Artifact |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| carlton_complex_2014 | 7,588 | 6,495 | 25 | 25 | 115,861 | 1,746,994 | 2014-07-14T00:00:00 | 2014-08-11T00:00:00 | `data/labels/carlton_complex_2014_firms_progression.zarr` |
| king_2014 | 5,584 | 4,977 | 14 | 14 | 80,793 | 399,856 | 2014-09-14T00:00:00 | 2014-10-07T00:00:00 | `data/labels/king_2014_firms_progression.zarr` |
| big_cougar_2014 | 3,002 | 1,441 | 9 | 9 | 26,056 | 123,901 | 2014-08-03T00:00:00 | 2014-08-11T00:00:00 | `data/labels/big_cougar_2014_firms_progression.zarr` |

## Semantics

- `detection_probability` is positive active-fire evidence from FIRMS confidence, spread over the approximate sensor footprint.
- The default artifact is daily-binned to avoid implying true hourly perimeter labels.
- `positive_observation_mask=0` means missing/unobserved, not confirmed unburned.
- Final burned extent is used only as target-construction quality control to remove unrelated detections inside broad bounding boxes.
- These labels support irregular hotspot/progression learning and assimilation experiments, not exact hourly perimeter evaluation.
