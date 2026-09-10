# FireTwin Progression Label Audit

This report audits whether current pilot fires support time-resolved labels.

Hourly perimeter labels are treated as unsupported unless timestamped observations prove otherwise.

## Carlton Complex (2014)

- Audit window: 2014-07-14 to 2014-08-25
- Hourly labels defensible: False
- Supported targets: final_burned_extent, active_fire_detection_probability, irregular_hotspot_progression
- Recommended next step: Prototype irregular progression labels with uncertainty; do not call them hourly perimeter truth.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2015-02-20T00:00:00 | 2015-02-20T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | missing | 0 | 0 | 0 | - | - | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | available | 7588 | 170 | 27 | 2014-07-14T10:00:00 | 2014-08-22T05:45:00 | FRP range: 0.0-2923.6 MW. Can support irregular hotspot/time-window labels after filtering. |

## KING (2014)

- Audit window: 2014-09-13 to 2014-10-09
- Hourly labels defensible: False
- Supported targets: final_burned_extent, active_fire_detection_probability, irregular_hotspot_progression
- Recommended next step: Prototype irregular progression labels with uncertainty; do not call them hourly perimeter truth.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2019-01-02T00:00:00 | 2019-01-02T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | available | 1 | 1 | 1 | 2014-09-13T02:00:00 | 2014-09-13T02:00:00 | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | available | 5584 | 88 | 21 | 2014-09-13T22:02:00 | 2014-10-09T11:13:00 | FRP range: 0.0-3860.2 MW. Can support irregular hotspot/time-window labels after filtering. |

## Big Cougar (2014)

- Audit window: 2014-08-02 to 2014-09-15
- Hourly labels defensible: False
- Supported targets: final_burned_extent, active_fire_detection_probability, irregular_hotspot_progression
- Recommended next step: Prototype irregular progression labels with uncertainty; do not call them hourly perimeter truth.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2014-08-26T00:00:00 | 2014-08-26T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | available | 1 | 1 | 1 | 2014-08-03T02:00:00 | 2014-08-03T02:00:00 | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | available | 3002 | 126 | 28 | 2014-08-03T08:45:00 | 2014-09-13T20:43:00 | FRP range: 0.1-719.4 MW. Can support irregular hotspot/time-window labels after filtering. |

## Conclusion

The current pilot artifacts remain final-extent cases until FIRMS detections or other timestamped progression observations are audited and converted into uncertainty-aware labels.
