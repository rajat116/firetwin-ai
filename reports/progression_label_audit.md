# FireTwin Progression Label Audit

This report audits whether current pilot fires support time-resolved labels.

Hourly perimeter labels are treated as unsupported unless timestamped observations prove otherwise.

## Carlton Complex (2014)

- Audit window: 2014-07-14 to 2014-08-25
- Hourly labels defensible: False
- Supported targets: final_burned_extent
- Recommended next step: Configure NASA FIRMS MAP_KEY, rerun audit, then decide label strategy.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2015-02-20T00:00:00 | 2015-02-20T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | missing | 0 | 0 | 0 | - | - | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | missing_credentials | 0 | 0 | 0 | - | - | FIRMS MAP_KEY is required for historical detection audit. |

## KING (2014)

- Audit window: 2014-09-13 to 2014-10-09
- Hourly labels defensible: False
- Supported targets: final_burned_extent
- Recommended next step: Configure NASA FIRMS MAP_KEY, rerun audit, then decide label strategy.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2019-01-02T00:00:00 | 2019-01-02T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | available | 1 | 1 | 1 | 2014-09-13T02:00:00 | 2014-09-13T02:00:00 | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | missing_credentials | 0 | 0 | 0 | - | - | FIRMS MAP_KEY is required for historical detection audit. |

## Big Cougar (2014)

- Audit window: 2014-08-02 to 2014-09-15
- Hourly labels defensible: False
- Supported targets: final_burned_extent
- Recommended next step: Configure NASA FIRMS MAP_KEY, rerun audit, then decide label strategy.

| Source | Status | Obs | Unique timestamps | Unique dates | First | Last | Notes |
|---|---:|---:|---:|---:|---|---|---|
| NIFC Historical Perimeters | available | 1 | 1 | 1 | 2014-08-26T00:00:00 | 2014-08-26T00:00:00 | No perimeter progression: source has fewer than 2 timestamps. |
| MTBS | available | 1 | 1 | 1 | 2014-08-03T02:00:00 | 2014-08-03T02:00:00 | MTBS supports validated final extent and ignition metadata, not hourly progression. |
| NASA FIRMS | missing_credentials | 0 | 0 | 0 | - | - | FIRMS MAP_KEY is required for historical detection audit. |

## Conclusion

The current pilot artifacts remain final-extent cases until FIRMS detections or other timestamped progression observations are audited and converted into uncertainty-aware labels.
