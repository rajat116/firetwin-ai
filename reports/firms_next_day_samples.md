# FireTwin FIRMS Next-Day Sample Artifacts

These artifacts are Phase 5A supervised-learning samples for next-day FIRMS active-fire evidence.
They are positive-unlabeled observation targets, not exact burned-perimeter labels.

| Case | Samples | Grid | Target positive cells | Target positive fraction | Initial active cells | First reference | Last target | Artifact |
|---|---:|---|---:|---:|---:|---|---|---|
| carlton_complex_2014 | 28 | 662x493 | 115,685 | 0.01266 | 213 | 2014-07-14T00:00:00 | 2014-08-11T00:00:00 | `data/training/firms_next_day/carlton_complex_2014_samples.zarr` |
| king_2014 | 23 | 462x312 | 78,991 | 0.02383 | 4,351 | 2014-09-14T00:00:00 | 2014-10-07T00:00:00 | `data/training/firms_next_day/king_2014_samples.zarr` |
| big_cougar_2014 | 8 | 349x239 | 24,455 | 0.03665 | 1,641 | 2014-08-03T00:00:00 | 2014-08-11T00:00:00 | `data/training/firms_next_day/big_cougar_2014_samples.zarr` |

## Semantics

- Inputs include real terrain, LANDFIRE fuel classes/proxies, ERA5 scalar weather, FIRMS initial state and FIRMS history available at the reference day.
- Targets are next-calendar-day FIRMS positive-observation probability and positive-observation masks.
- Final burned extent is excluded from the sample artifacts as a model input.
- Target zeros mean no positive FIRMS evidence in that daily bin, not confirmed unburned.
- These samples support honest Phase 5A active-fire probability modeling before any simulator-conditioned arrival-time field.
