# FireTwin Evaluation Protocol

**Last Updated**: 2026-09-09
**Status**: Phase 0-4A baseline protocol before real fuel/weather model work

> Research prototype. Not for operational wildfire response, evacuation planning or safety-critical decision-making.

## Purpose

This document defines how FireTwin evaluates forecasts without leaking future information or overstating what current labels support.

## Current Dataset Status

The current pilot fire cases are **final-burned-extent cases**:

- Carlton Complex 2014
- King 2014
- Big Cougar 2014

They currently contain real NIFC/MTBS-derived final perimeter masks and real USGS 3DEP
terrain-derived elevation, slope and aspect. Fuel, weather and initial-state fields remain
placeholders. They must not be used as 3-, 6-, 12- or 24-hour fire-progression labels until
time-stamped observations are reconstructed and validated.

## Target Types

Keep target types separate:

- `active_fire_detection_probability`: probability of satellite active-fire detection.
- `burned_extent_at_time`: burned/unburned state at a known later timestamp.
- `fire_arrival_time`: estimated arrival time per cell.
- `final_burned_extent`: final burned/unburned mask.
- `burn_severity`: post-fire severity class or continuous severity proxy.

Metrics must state which target type they evaluate.

## No-Leakage Rules

For every forecast reference time:

- Use only observations, weather and covariates available at or before the reference time.
- Do not use final perimeters, MTBS products, post-fire imagery or future weather as model inputs.
- Treat missing active-fire observations as missing/uncertain, not unburned.
- Split by fire, not by pixel or timestep.
- Record the source timestamp and processing timestamp for every target.

## Deterministic Metrics

For burned masks and perimeter-style outputs:

- Intersection over Union.
- Dice score.
- Precision and recall with class prevalence.
- Area error.
- Symmetric boundary distance where geometry is meaningful.
- Fire-arrival-time MAE only when valid arrival-time labels exist.

Hourly horizons such as 3, 6, 12 and 24 hours may only be reported when observation cadence supports those horizons.

## Probabilistic Metrics

For probability forecasts:

- Brier score.
- Negative log likelihood where the output distribution supports it.
- Reliability diagrams.
- Expected calibration error, with caveats for spatial dependence.
- Empirical coverage of 50%, 80% and 95% regions.
- Sharpness or predicted region area.

## Baseline Requirements

Every advanced model must be compared with:

- Persistence/no-growth.
- Isotropic radial spread.
- Wind-oriented elliptical spread.
- No-intervention baseline for intervention experiments.

If a simple baseline wins, report that result plainly.

## Current Pilot Validation

The current validation gate checks that each local pilot Zarr case:

- Loads through Xarray/Zarr.
- Contains required metadata, including target type and known limitations.
- Uses the expected projected CRS.
- Contains initial and target fire-state arrays on the stored time axis.
- Produces a final burned area within tolerance of the documented fire size.
- Explicitly marks `covariate_status=partial_real_terrain`.
- Records covariate-source provenance, including USGS 3DEP terrain.
- Contains finite, non-flat USGS 3DEP elevation and derived slope/aspect.
- Still warns that fuel and weather covariates are placeholders.

Passing this gate means the cases are valid **final-extent artifacts with terrain covariates**, not
forecast-ready real-data progression samples.

## Phase 4B Entry Criteria

Do not start real-data model evaluation until:

- `configs/data_sources.yaml` exists and names source URLs, access dates and known limitations.
- All Phase 0-3 unit tests pass.
- `scripts/validate_fire_cases.py` passes against regenerated pilot fire artifacts.
- The generated artifacts carry `target_type=final_burned_extent` and
  `covariate_status=partial_real_terrain`.
- Any baseline evaluation script refuses to treat final extent as hourly progression.
- Fuel and weather enrichment status is explicit in metadata and validation output.

## Reporting

Each result table must include:

- Fire ID and region.
- Target type.
- Forecast reference time or `final_extent_only`.
- Horizon when valid.
- Model name and version.
- Data cutoff time.
- Metric values and confidence intervals when enough fires exist.
- Known limitations affecting interpretation.
