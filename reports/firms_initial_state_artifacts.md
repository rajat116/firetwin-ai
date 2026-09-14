# FireTwin FIRMS Initial-State Artifacts

These artifacts estimate the initial active-fire state from earliest FIRMS detections.

| Case | Input detections | Retained | Window detections | Active cells | Reference | Window end | Artifact |
|---|---:|---:|---:|---:|---|---|---|
| carlton_complex_2014 | 7,588 | 6,723 | 6 | 213 | 2014-07-14T19:12:00 | 2014-07-15T19:12:00 | `data/initial_states/carlton_complex_2014_firms_initial_state.zarr` |
| king_2014 | 5,584 | 5,441 | 264 | 4,351 | 2014-09-14T10:41:00 | 2014-09-15T10:41:00 | `data/initial_states/king_2014_firms_initial_state.zarr` |
| big_cougar_2014 | 3,002 | 1,491 | 63 | 1,641 | 2014-08-03T08:45:00 | 2014-08-04T08:45:00 | `data/initial_states/big_cougar_2014_firms_initial_state.zarr` |

## Semantics

- `initial_burned_probability` is an earliest-window FIRMS confidence proxy.
- `initial_active_front=1` marks cells with early active-fire evidence after footprint expansion.
- Final burned extent is not used for initial-state quality control.
- Non-detection means missing/unobserved, not known unburned.
- These artifacts are suitable for initialization experiments, not operational ignition mapping.
