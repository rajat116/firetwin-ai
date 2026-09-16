# FireTwin Project Status

**Last Updated**: 2026-09-16
**Current Phase**: Phase 5B 🚧 - Scaled Simulation Corpus and Surrogate Foundation

## Phase 0: Repository and Engineering Foundation ✅

**Status**: COMPLETED (2026-09-03)

### Completed Tasks

- [x] Initialize Git repository with correct credentials
- [x] Create comprehensive directory structure
- [x] Set up conda environment with all required dependencies (Python 3.11 & 3.12)
- [x] Configure Python package structure with pyproject.toml
- [x] Implement CLI with `firetwin doctor` command
- [x] Add code quality tools (Ruff, MyPy, Pytest)
- [x] Configure pre-commit hooks
- [x] Set up GitHub Actions CI pipeline
- [x] Add Apache-2.0 license
- [x] Create initial documentation structure
- [x] Write comprehensive README with data sources, specs, demo scripts
- [x] Create Makefile for development commands

### Acceptance Criteria

- [x] Fresh clone can install from documented commands
- [x] `pytest`, `ruff check`, `ruff format --check` and `mypy` pass
- [x] CI passes on ubuntu/macos × Python 3.11/3.12
- [x] No credentials or large data committed

### Key Decisions

- Used conda over uv for geospatial dependencies (GDAL, rasterio)
- Configured MyPy with `--no-site-packages` for Python 3.12 compatibility
- Apache 2.0 license for commercial-friendly open source

## Phase 1: Synthetic End-to-End Vertical Slice ✅

**Status**: COMPLETED (2026-09-03)

**Purpose**: Validate production ML pipeline architecture with synthetic data before real data integration.

### Completed Tasks

- [x] **Data Layer**: Pydantic schemas for type-safe data contracts
  - FireCase, TerrainData, FuelData, WeatherData, FireState
- [x] **Synthetic Generation**: Realistic terrain, fuel, and fire evolution
  - Fractal-like elevation with slope/aspect computation
  - Patch-based fuel distribution (grass, shrub, timber)
  - Stochastic fire spread with fuel and wind effects
- [x] **Storage**: Xarray/Zarr format with provenance
  - Canonical multidimensional data format
  - Efficient compression and chunking
- [x] **Baseline Models**:
  - Persistence (no-change forecast)
  - Radial spread (uniform circular)
  - Elliptical spread (wind-driven)
- [x] **Evaluation Metrics**:
  - IoU and Dice scores for burned area
  - Boundary distance for perimeter accuracy
  - Area error for over/under-prediction
- [x] **CLI Commands**:
  - `generate-synthetic`: Create test cases
  - `run-baselines`: Execute forecast models
  - `evaluate`: Calculate metrics
- [x] **Golden Tests**: 8 automated tests for CI
  - Deterministic generation
  - Fire spread validation
  - Baseline model correctness

### Acceptance Criteria

- [x] One command builds synthetic case
- [x] One command runs all baselines
- [x] One command produces evaluation report
- [x] Demo visibly distinguishes observed, predicted, and target states
- [x] All tests pass in CI

### Results

Elliptical baseline outperforms radial and persistence on 6-hour forecasts:
- **Elliptical**: IoU=0.168, Dice=0.287
- **Radial**: IoU=0.078, Dice=0.145
- **Persistence**: IoU=0.038, Dice=0.073

### Not Completed (Deferred)

- MLflow experiment tracking (can add incrementally)
- Streamlit dashboard (Phase 9 will have production React frontend)

## Phase 2: Real Data Infrastructure ✅

**Status**: COMPLETED (2026-09-07)

**Purpose**: Build production-grade data acquisition and validation infrastructure for all fire-related data sources.

### Completed Tasks

**Data Source Clients** (61 tests, 92-100% coverage):
- [x] Build FIRMS API client (NASA active fire detections)
- [x] Build NIFC/WFIGS client (current fire perimeters)
- [x] Build MTBS client (historical burned area data)
- [x] Build ERA5-Land client (weather/climate reanalysis via CDS API)
- [x] Build LANDFIRE client (fuel and vegetation data)
- [x] Build USGS 3DEP client (elevation and terrain via National Map API)

**Data Validation & Quality**:
- [x] Validate CRS, timestamps, geometries, units for all sources
- [x] Document unit conversions and value ranges
- [x] Define geometry validation protocols (points, polygons, rasters)
- [x] Establish temporal standards (ISO 8601, UTC timezone)

**Fire Inventory System** (12 tests, 90% coverage):
- [x] Build candidate fire inventory with quality scoring (0-100)
- [x] Implement searchable fire case database
- [x] Multi-criteria search (quality, area, temporal, spatial, data requirements)
- [x] Save/load inventory to CSV/Parquet

**Data Audit & Documentation**:
- [x] Produce comprehensive data availability audit report
- [x] Document quality issues, coverage gaps, and recommendations per source
- [x] Cross-source complementarity analysis
- [x] Define data quality tiers (Tier 1/2/3)
- [x] Create DATA_VALIDATION.md documentation
- [x] Update DATA_SOURCES.md with complete technical details

### Acceptance Criteria

- [x] All 6 data source clients implemented with tests
- [x] Data validation framework documented
- [x] Fire inventory system functional
- [x] Audit report generated
- [x] All tests pass in CI (73 total tests)

### Key Results

**Test Coverage**:
- 61 data client tests (17 FIRMS, 13 NIFC, 13 MTBS, 8 ERA5, 5 LANDFIRE, 5 USGS)
- 12 inventory system tests
- All passing in CI across Ubuntu/macOS, Python 3.11/3.12

**Data Quality Tiers**:
- **Tier 1** (80-100 pts): All 6 sources, 50+ FIRMS detections, 5+ perimeter updates
- **Tier 2** (60-79 pts): 4-5 sources, 20+ detections, 2+ perimeters
- **Tier 3** (40-59 pts): 3-4 sources, basic coverage

**Known Limitations**:
- Geographic coverage: Mostly US-only (except FIRMS and ERA5)
- Temporal lags: LANDFIRE (2-3 years), MTBS (1-2 years)
- Resolution mismatches: ERA5 (9km) vs LANDFIRE/3DEP (30m)

### Documentation

- `docs/DATA_SOURCES.md`: Complete data source registry
- `docs/DATA_VALIDATION.md`: Validation protocols and standards
- `reports/data_availability_audit.md`: Comprehensive audit report
- `src/firetwin/data/clients/`: All 6 client implementations
- `src/firetwin/data/inventory.py`: Fire inventory system
- `src/firetwin/data/audit.py`: Data auditor

## Phase 3: Historical Fire Case Builder ✅

**Status**: COMPLETED (2026-09-08)

**Purpose**: Build complete FireCase objects from real historical wildfire data.

**Scientific Scope**: Phase 3 produces validated **final-burned-extent** artifacts. These are
not yet time-resolved forecast samples and must not be reported as 3/6/12/24-hour progression
labels.

### Completed Tasks

**RealFireCaseConverter Implementation**:
- [x] Multi-source data fetching (NIFC Historical, MTBS)
- [x] Spatial alignment and CRS reprojection
- [x] Grid computation with configurable resolution (100m default)
- [x] Fire perimeter rasterization using rasterio
- [x] Canonical FireCase construction
- [x] Zarr format export with compression

**3 Pilot Fires Built**:
- [x] Carlton Complex 2014 (WA) - 251,965 acres
- [x] King Fire 2014 (CA) - 97,685 acres  
- [x] Big Cougar 2014 (OR/ID) - 65,305 acres

**Scripts and Testing**:
- [x] Individual fire test script (`test_converter_carlton.py`)
- [x] Batch build script (`build_all_pilot_fires.py`)
- [x] Validation script checks actual Zarr layout, final burned area, CRS, and limitation metadata
- [x] Regression tests cover final-extent metadata and CRS preservation

### Acceptance Criteria

- [x] Successfully fetch real fire perimeter data
- [x] Reproject and align to target CRS
- [x] Rasterize perimeters to canonical grid
- [x] Build complete FireCase objects
- [x] Save to Zarr format
- [x] Generate 3 diverse pilot fires
- [x] Machine-readable data-source registry exists (`configs/data_sources.yaml`)
- [x] Evaluation protocol exists (`docs/EVALUATION_PROTOCOL.md`)
- [x] Final-extent limitation is stored in case metadata

### Key Results

**Generated Fire Cases**:
- 3 complete FireCase objects with real perimeters
- Geographic diversity: Pacific NW, Sierra Nevada, Northern Rockies
- Scale diversity: 65k - 252k acres
- Total storage: ~24MB compressed Zarr

**Known Limitations**:
- Terrain, fuels, weather using placeholder data (real integration in Phase 4)
- Final/static extent only (no validated time-resolved progression labels yet)
- Limited to fires with NIFC Historical coverage
- Artifacts generated before the metadata/schema cleanup must be regenerated before the stricter
  validator will pass

### Documentation

- `docs/PHASE3_STATUS.md`: Complete phase status and lessons learned
- `docs/PHASE3_PILOT_FIRES.md`: Fire selection rationale
- `src/firetwin/data/converter.py`: Core converter implementation
- `scripts/build_all_pilot_fires.py`: Batch processing script

## Phase 4A: Real Terrain Enrichment ✅

**Status**: COMPLETED (2026-09-08)

**Purpose**: Replace flat placeholder terrain in the pilot fire cases with real USGS 3DEP DEM
covariates aligned to the canonical FireTwin grid.

### Completed Tasks

- [x] Updated USGS 3DEP client to use current TNM dataset names.
- [x] Select latest GeoTIFF product per 1-degree DEM tile instead of historical duplicates.
- [x] Download and cache DEM tiles under ignored `data/raw/3dep/`.
- [x] Reproject/resample DEM tiles onto each target FireTwin grid.
- [x] Derive slope and aspect from aligned elevation arrays.
- [x] Store real terrain arrays in generated Zarr fire cases.
- [x] Mark generated cases with `covariate_status=partial_real_terrain`.
- [x] Store covariate-source provenance in case metadata and Zarr attributes.
- [x] Tighten validation so pilot cases fail if terrain remains flat/placeholder.
- [x] Add unit tests for DEM selection, alignment, derivative computation and converter metadata.

### Result-Wise Validation

- Carlton Complex: elevation 218-2255m, mean slope 13.5°, final burned area 9.3% from reference.
- King: elevation 388-2371m, mean slope 14.5°, final burned area 0.2% from reference.
- Big Cougar: elevation 240-1671m, mean slope 19.9°, final burned area ~0.0% from reference.

### Remaining Phase 4 Work

- [x] Phase 4C: Replace scalar placeholder weather with real ERA5-Land/weather covariates.
- [x] Phase 4D: Add real-data baselines that respect `target_type=final_burned_extent`.

## Phase 4B: Real LANDFIRE Fuel Enrichment ✅

**Status**: COMPLETED (2026-09-09)

**Purpose**: Replace uniform placeholder FBFM 10 fuel grids in the pilot fire cases with real
LANDFIRE LF2022 FBFM40 categorical fuel-model rasters aligned to the canonical FireTwin grid.

### Completed Tasks

- [x] Added LANDFIRE LF2022 FBFM40 ImageServer export support.
- [x] Export and cache grid-aligned GeoTIFF rasters under ignored `data/raw/landfire/`.
- [x] Use nearest-neighbor resampling for categorical fuel-model classes.
- [x] Preserve burnable FBFM40 class codes and convert LANDFIRE non-burnable codes to `0`.
- [x] Derive deterministic fuel-load and fuel-moisture proxy grids from FBFM40 class groups.
- [x] Store real fuel arrays in generated Zarr fire cases.
- [x] Mark generated cases with `covariate_status=partial_real_terrain_fuels`.
- [x] Store LANDFIRE fuel-model provenance in case metadata and Zarr attributes.
- [x] Tighten validation so pilot cases fail if fuels remain uniform FBFM 10.
- [x] Add unit tests for LANDFIRE export parameters, raster normalization, proxy derivation and
  converter metadata.

### Result-Wise Validation

- Carlton Complex: 21 fuel classes, 88.5% burnable cells, final burned area 9.3% from reference.
- King: 26 fuel classes, 95.7% burnable cells, final burned area 0.2% from reference.
- Big Cougar: 21 fuel classes, 95.2% burnable cells, final burned area ~0.0% from reference.

### Remaining Phase 4 Work

- [x] Phase 4D: Add real-data baselines that respect `target_type=final_burned_extent`.
- [ ] Replace fuel-load and fuel-moisture proxies with source-derived/live fuel attributes when
  that data source is selected.

## Phase 4C: Real ERA5-Land Weather Enrichment ✅

**Status**: COMPLETE (2026-09-10)

**Purpose**: Replace scalar placeholder weather in pilot fire cases with real ERA5-Land hourly
reanalysis summarized at the ignition/discovery weather reference time.

### Completed Tasks

- [x] Added exact-date CDS request construction for ERA5-Land downloads.
- [x] Added FireTwin WGS84 bbox to CDS area-order conversion.
- [x] Added cached NetCDF loading and scalar weather summarization.
- [x] Derive temperature in Celsius, relative humidity from dewpoint, wind speed and
  meteorological wind direction from ERA5 variables.
- [x] Thread optional `weather_start`/`weather_end` windows through the converter and pilot builder.
- [x] Add metadata/status support for `partial_real_terrain_fuels_weather`.
- [x] Add validator support for a real-weather gate.
- [x] Add unit tests for ERA5 request structure, weather math, cache behavior, converter metadata
  and real-weather validation.

### Artifact Verification

- [x] Configured CDS credentials outside Git using `~/.cdsapirc`.
- [x] Rebuilt all three pilot cases with ERA5-Land NetCDF downloads.
- [x] Enabled and passed `scripts/validate_fire_cases.py` with the real-weather gate.
- [x] Marked generated Zarrs with `covariate_status=partial_real_terrain_fuels_weather`.
- [x] Result-wise weather values inspected:
  - Carlton Complex: 2014-07-14T12:00:00, 26.9C, RH 31%, wind 0.9 m/s from 306 deg.
  - King: 2014-09-13T23:00:00, 22.8C, RH 29%, wind 0.7 m/s from 185 deg.
  - Big Cougar: 2014-08-02T12:00:00, 26.3C, RH 32%, wind 0.1 m/s from 140 deg.

## Phase 4D: Final-Extent Baseline Diagnostics ✅

**Status**: COMPLETE (2026-09-10)

**Purpose**: Provide honest real-data baseline diagnostics for final burned extent artifacts while
blocking accidental use of final masks as 3/6/12/24-hour forecast labels.

### Completed Tasks

- [x] Added `evaluate_final_extent_baselines` for non-temporal final-extent evaluation.
- [x] Added covariate-only baselines: initial state, burnable fuel mask and top fuel-potential
  mask.
- [x] Added `firetwin evaluate-final-extent` CLI command.
- [x] Added guardrails so `firetwin run-baselines` and `firetwin evaluate` reject
  `target_type=final_burned_extent` cases.
- [x] Added unit tests covering final-extent evaluation, CLI command behavior and forecast-label
  rejection.

### Result-Wise Baseline Diagnostics

These are spatial diagnostics, not hourly spread forecasts.

- Carlton Complex:
  - Burnable fuel mask: IoU 0.338, Dice 0.505, area error +159.1%.
  - Top fuel-potential 30%: IoU 0.142, Dice 0.249, area error -16.3%.
- King:
  - Burnable fuel mask: IoU 0.280, Dice 0.438, area error +248.4%.
  - Top fuel-potential 30%: IoU 0.103, Dice 0.186, area error +84.7%.
- Big Cougar:
  - Burnable fuel mask: IoU 0.314, Dice 0.478, area error +200.7%.
  - Top fuel-potential 30%: IoU 0.068, Dice 0.127, area error -2.2%.

### Interpretation

The weak IoU values are expected: without observed ignition/progression, fuel and terrain
covariates alone cannot localize the final perimeter. This confirms the next scientific step is
progression/initial-state reconstruction rather than training a model on fake hourly labels.

## Phase 4E: FIRMS-Backed Label and Initial-State Artifacts ✅

**Status**: COMPLETE (2026-09-14)

**Purpose**: Decide what real time-resolved labels the current pilot fires can honestly support
before constructing ignition states, progression targets or ML training samples.

### Completed Tasks

- [x] Added reusable progression-source audit utilities for NIFC, MTBS and FIRMS.
- [x] Added historical FIRMS standard-processing source support for 2014-era MODIS/VIIRS queries.
- [x] Updated FIRMS API validation to the current 1-5 day area/country API window.
- [x] Added VIIRS standard-processing CSV parsing for `bright_ti4`/`bright_ti5` columns.
- [x] Added `scripts/audit_progression_labels.py`.
- [x] Generated `reports/progression_label_audit.md` with configured FIRMS credentials.
- [x] Added unit tests for chunking, historical source selection, source summaries and report
  rendering.
- [x] Added FIRMS label-artifact builder with cached detection records and FireTwin-grid
  rasterization.
- [x] Generated daily-binned FIRMS hotspot/progression label artifacts under ignored `data/labels/`.
- [x] Generated `reports/firms_label_artifacts.md`.
- [x] Added unit tests for confidence scoring, grid indexing, final-extent QC and label metadata.
- [x] Added shared pilot-fire definitions for repeatable Phase 4E artifact builders.
- [x] Added FIRMS-derived initial-state estimation from earliest active-fire detections.
- [x] Generated initial active-fire state artifacts under ignored `data/initial_states/`.
- [x] Generated `reports/firms_initial_state_artifacts.md`.
- [x] Added tests proving initial-state estimation does not use final burned extent as QC.
- [x] Added FIRMS artifact validation diagnostics and overlay figures.
- [x] Generated `reports/firms_artifact_validation.md` and figures under `reports/figures/`.

### Result-Wise Audit Findings

- Carlton Complex 2014: NIFC has 1 matching perimeter timestamp; MTBS not matched by current query;
  FIRMS has 7,588 detections across 170 unique timestamps and 27 dates.
- King 2014: NIFC has 1 matching perimeter timestamp; MTBS has 1 ignition/final record; FIRMS has
  5,584 detections across 88 unique timestamps and 21 dates.
- Big Cougar 2014: NIFC has 1 matching perimeter timestamp; MTBS has 1 ignition/final record; FIRMS
  has 3,002 detections across 126 unique timestamps and 28 dates.

### Interpretation

The current NIFC/MTBS evidence does not support hourly perimeter labels for any pilot fire. FIRMS
historical active-fire detections do support irregular hotspot/progression targets, but those targets
must be filtered, uncertainty-aware and clearly distinguished from exact burned perimeters.

### FIRMS Label Artifact Results

Generated artifacts are daily-binned companion Zarr products, not replacements for the final-extent
FireCase targets.

- Carlton Complex 2014: 7,588 input detections, 6,495 retained after QC, 25 daily slices,
  115,861 positive observation cells and 1,746,994 cumulative positive cells.
- King 2014: 5,584 input detections, 4,977 retained after QC, 14 daily slices,
  80,793 positive observation cells and 399,856 cumulative positive cells.
- Big Cougar 2014: 3,002 input detections, 1,441 retained after QC, 9 daily slices,
  26,056 positive observation cells and 123,901 cumulative positive cells.

All label artifacts record `label_type=irregular_firms_hotspot_progression`,
`target_type=active_fire_detection_probability`, `time_bin=date`,
`not_hourly_perimeter_truth=true` and
`non_detection_semantics=missing_or_unobserved_not_unburned`.

### FIRMS Initial-State Artifact Results

Generated initial-state artifacts are earliest-window companion Zarr products for initialization
experiments. They do not replace the canonical FireCase final-extent target.

- Carlton Complex 2014: 7,588 input detections, 6,723 retained after basic QC, 6 earliest-window
  detections, 213 active cells, reference 2014-07-14T19:12:00.
- King 2014: 5,584 input detections, 5,441 retained after basic QC, 264 earliest-window detections,
  4,351 active cells, reference 2014-09-14T10:41:00.
- Big Cougar 2014: 3,002 input detections, 1,491 retained after basic QC, 63 earliest-window
  detections, 1,641 active cells, reference 2014-08-03T08:45:00.

All initial-state artifacts record `label_type=firms_initial_state_estimate`,
`target_type=initial_active_fire_state`, `uses_final_extent_for_qc=false`,
`not_hourly_perimeter_truth=true` and
`non_detection_semantics=missing_or_unobserved_not_unburned`.

### FIRMS Artifact Validation Results

Generated validation overlays compare FIRMS companion artifacts with final extent for context only.
They do not turn FIRMS observations into perimeter truth.

- Carlton Complex 2014: cumulative FIRMS precision 1.000 vs final extent, recall 0.747; initial
  active-state precision 1.000, recall 0.002.
- King 2014: cumulative FIRMS precision 1.000 vs final extent, recall 0.952; initial active-state
  precision 0.895, recall 0.098, with 457 earliest-window cells outside final extent because
  initial-state construction avoids future final-extent QC.
- Big Cougar 2014: cumulative FIRMS precision 1.000 vs final extent, recall 0.776; initial
  active-state precision 1.000, recall 0.062.

### Completed Phase 4E Decision

- [x] Phase 5A will consume daily FIRMS active-fire observation labels directly.
- [x] Simulator-conditioned arrival-time fields are deferred until after direct FIRMS
  observation-learning baselines exist.

## Phase 5A: Next-Day FIRMS Active-Fire Learning ✅

**Status**: COMPLETE (2026-09-15)

**Purpose**: Turn the validated FIRMS companion artifacts into leakage-safe supervised-learning
samples for next-calendar-day active-fire probability modeling.

### Completed Tasks

- [x] Added `firms_next_day_active_fire_probability` sample dataset builder.
- [x] Added `scripts/build_firms_next_day_samples.py`.
- [x] Reindexed sparse FIRMS progression dates to a continuous daily calendar.
- [x] Included real terrain, LANDFIRE fuel classes/proxies, ERA5 scalar weather, FIRMS initial state
  and FIRMS history available at each reference day.
- [x] Excluded final burned extent from sample artifacts as a model input.
- [x] Added tests for continuous daily reindexing and no-leakage metadata.
- [x] Generated sample artifacts under ignored `data/training/firms_next_day/`.
- [x] Generated `reports/firms_next_day_samples.md`.
- [x] Added next-day active-fire baseline diagnostics: persistence, cumulative-history prior and
  fuel/terrain prior.
- [x] Added `scripts/evaluate_firms_next_day_baselines.py`.
- [x] Generated `reports/firms_next_day_baselines.md`.
- [x] Added first calibrated observed-label logistic model for next-day FIRMS active-fire
  probability.
- [x] Added leave-one-fire-out learned-model evaluation against persistence.
- [x] Added `scripts/train_firms_next_day_model.py`.
- [x] Generated `reports/firms_next_day_learned_model.md`.
- [x] Added leave-one-fire-out learned forecast artifact packaging for future Explorer/demo layers.
- [x] Added `scripts/build_firms_next_day_forecasts.py`.
- [x] Generated local forecast artifacts under ignored `data/forecasts/firms_next_day/`.
- [x] Generated `reports/firms_next_day_forecasts.md`.
- [x] Added forecast calibration, reliability-bin and threshold-sweep diagnostics.
- [x] Added `scripts/evaluate_firms_next_day_forecasts.py`.
- [x] Generated reliability figures under `reports/figures/`.
- [x] Generated `reports/firms_next_day_forecast_calibration.md`.
- [x] Added Explorer-ready forecast asset export for future public UI layers.
- [x] Added `scripts/export_firms_explorer_assets.py`.
- [x] Generated preview PNGs under `reports/figures/`.
- [x] Generated `data/manifests/firms_next_day_explorer_manifest.json`.
- [x] Generated `reports/firms_next_day_explorer_assets.md`.
- [x] Added first dependency-free local Explorer UI under `frontend/`.
- [x] Added allowlisted local preview server at `scripts/serve_explorer.py`.
- [x] Added static frontend and preview-server tests.
- [x] Added deployable static Explorer bundle builder at `scripts/build_explorer_site.py`.
- [x] Added deployable Explorer smoke test at `scripts/smoke_explorer_bundle.py`.

### Result-Wise Sample Artifacts

- Carlton Complex 2014: 28 samples on a 662x493 grid, 115,685 next-day positive target cells,
  target positive fraction 0.01266.
- King 2014: 23 samples on a 462x312 grid, 78,991 next-day positive target cells, target positive
  fraction 0.02383.
- Big Cougar 2014: 8 samples on a 349x239 grid, 24,455 next-day positive target cells, target
  positive fraction 0.03665.

All sample artifacts record `sample_type=firms_next_day_active_fire_probability`,
`target_type=active_fire_detection_probability`, `excludes_final_extent_as_input=true`,
`not_hourly_perimeter_truth=true` and
`positive_unlabeled_semantics=zeros_are_no_positive_firms_evidence_not_confirmed_unburned`.

### Result-Wise Baseline Diagnostics

These are observation-label diagnostics for next-day FIRMS active-fire evidence, not perimeter
forecast scores.

- Carlton Complex 2014: persistence Brier 0.00362, precision 0.232, recall 0.151; cumulative
  history Brier 0.04625; fuel/terrain prior Brier 0.10389.
- King 2014: persistence Brier 0.00462, precision 0.488, recall 0.307; cumulative history Brier
  0.05117; fuel/terrain prior Brier 0.16213.
- Big Cougar 2014: persistence Brier 0.01033, precision 0.172, recall 0.108; cumulative history
  Brier 0.03054; fuel/terrain prior Brier 0.08057.

Interpretation: persistence is the strongest first baseline by observed Brier/MAE. Static
fuel/terrain priors produce broad, high-recall maps but overpredict heavily, which confirms the
need for learned spatiotemporal models rather than covariates-only maps.

### Result-Wise Learned-Model Diagnostics

The first learned model is a calibrated observed-label logistic model trained on terrain, fuel,
weather, FIRMS initial-state, current-day FIRMS and cumulative-history features. It is evaluated
with leave-one-fire-out validation and does not use final burned extent as an input.

- Carlton Complex 2014 holdout: learned Brier 0.00278 vs persistence Brier 0.00362, improvement
  +0.00084; precision 0.225, recall 0.202 at threshold 0.05.
- King 2014 holdout: learned Brier 0.00382 vs persistence Brier 0.00462, improvement +0.00080;
  precision 0.492, recall 0.307 at threshold 0.05.
- Big Cougar 2014 holdout: learned Brier 0.00631 vs persistence Brier 0.01033, improvement
  +0.00402; precision 0.168, recall 0.144 at threshold 0.05.

Interpretation: the calibrated learned model now beats persistence on probabilistic Brier score
for every held-out pilot fire. The 0.05 diagnostic threshold gives predicted positive fractions in
the same range as observed FIRMS target fractions, but demo-facing thresholds still need separate
tuning. This is a credible first forecasting baseline, not yet a public-facing spread visualization
product.

### Result-Wise Forecast Artifacts

Generated artifacts are leave-one-fire-out learned forecasts, so each pilot fire is predicted by a
model trained on the other two pilot fires. They include `forecast_probability`,
`forecast_positive_mask`, target FIRMS observation evidence and reference-day FIRMS context for
future UI layers.

- Carlton Complex 2014: learned forecast Brier 0.00278 vs persistence Brier 0.00362, improvement
  +0.00084; forecast artifact `data/forecasts/firms_next_day/carlton_complex_2014_learned_forecast.zarr`.
- King 2014: learned forecast Brier 0.00382 vs persistence Brier 0.00462, improvement +0.00080;
  forecast artifact `data/forecasts/firms_next_day/king_2014_learned_forecast.zarr`.
- Big Cougar 2014: learned forecast Brier 0.00631 vs persistence Brier 0.01033, improvement
  +0.00402; forecast artifact `data/forecasts/firms_next_day/big_cougar_2014_learned_forecast.zarr`.

Interpretation: Phase 5A now has UI-ready probability layers that are still scientifically scoped as
satellite-visible active-fire evidence, not operational perimeter spread.

### Result-Wise Calibration and Threshold Diagnostics

Calibration diagnostics are computed against FIRMS observed-label probability targets. Recommended
thresholds are diagnostic display thresholds, not operational decision thresholds.

- Carlton Complex 2014: ECE 0.02462, recommended threshold 0.050, F1 0.213, precision 0.225,
  recall 0.202.
- King 2014: ECE 0.01871, recommended threshold 0.050, F1 0.378, precision 0.492, recall 0.307.
- Big Cougar 2014: ECE 0.01018, recommended threshold 0.025, F1 0.169, precision 0.149,
  recall 0.195.

Interpretation: a public Explorer should expose probability plus a threshold/opacity control rather
than hard-code one universal threshold. The default diagnostic thresholds are 0.05 for Carlton/King
and 0.025 for Big Cougar.

### Result-Wise Explorer Assets

The Explorer export selects the sample with the largest learned forecast probability mass for each
case and writes a compact preview PNG plus a JSON manifest that a future frontend can load without
understanding Zarr internals.

- Carlton Complex 2014: sample 4, reference 2014-07-18, target 2014-07-19, threshold 0.050,
  peak probability 0.470, preview `reports/figures/carlton_complex_2014_explorer_forecast_preview.png`.
- King 2014: sample 4, reference 2014-09-18, target 2014-09-19, threshold 0.050, peak probability
  0.216, preview `reports/figures/king_2014_explorer_forecast_preview.png`.
- Big Cougar 2014: sample 5, reference 2014-08-08, target 2014-08-09, threshold 0.025, peak
  probability 0.753, preview `reports/figures/big_cougar_2014_explorer_forecast_preview.png`.

Interpretation: the repository now has a browser-consumable manifest and visual preview assets for
the learned FIRMS forecasts. These assets are the bridge from model artifact to the local Explorer
and eventual public deployment.

### Local Explorer Preview

The first local Explorer UI now renders the committed FIRMS forecast manifest and preview figures.
It provides case switching, zoom controls, observed-label diagnostics, grid provenance and the
non-operational guardrails. Run it with:

```bash
python3 scripts/serve_explorer.py --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/frontend/`. The preview server is allowlisted to serve only
`frontend/`, `data/manifests/firms_next_day_explorer_manifest.json` and the Explorer preview PNGs,
so local secrets such as `.env` are not exposed.

The Explorer can also be packaged for static hosting with:

```bash
python3 scripts/build_explorer_site.py --output-dir dist/explorer
```

The build copies only the frontend, manifest and referenced preview PNGs into `dist/explorer/`.

Smoke-test the deployable bundle before sharing or deploying it:

```bash
python3 scripts/smoke_explorer_bundle.py --bundle-dir dist/explorer
```

### Phase 5A Exit Criteria

- [x] Leakage-safe supervised samples exist.
- [x] Baselines exist and persistence is explicitly reported.
- [x] A learned forecast model beats persistence by observed-label Brier score on all held-out pilot
  fires.
- [x] Forecast artifacts are packaged for future UI layers.
- [x] Calibration and threshold diagnostics exist with reliability figures.
- [x] Explorer-ready manifest and preview assets exist for the learned forecast layers.
- [x] A local Explorer UI can render the committed manifest and figures.
- [x] Guardrails distinguish FIRMS active-fire evidence from exact perimeter spread.

## Phase 5B: Simulation Corpus and Surrogate 🚧

**Status**: STARTED (2026-09-16)

**Purpose**: Build simulator-derived training data and a learned surrogate so future what-if
controls can produce real recomputed outputs rather than decorative UI changes.

### Completed Tasks

- [x] Added deterministic Phase 5B simulation-corpus utilities under `firetwin.simulation`.
- [x] Added `scripts/build_simulation_corpus.py`.
- [x] Added schema version `firetwin.simulation_corpus.v1`.
- [x] Added simulator-derived guardrails: synthetic corpus, not observed wildfire truth.
- [x] Added a small smoke corpus under `data/simulation/phase5b_synthetic_smoke/`.
- [x] Generated `reports/phase5b_simulation_corpus.md`.
- [x] Added unit tests for deterministic scenario sampling, NPZ array contract, reproducibility,
  config validation and report rendering.
- [x] Added `firetwin.models.surrogate` with a NumPy logistic simulation-surrogate baseline.
- [x] Added `scripts/train_simulation_surrogate.py`.
- [x] Trained `data/models/phase5b_surrogate_smoke.npz` on the smoke corpus.
- [x] Generated `reports/phase5b_simulation_surrogate.md` and
  `reports/phase5b_simulation_surrogate_metrics.json`.
- [x] Added unit tests for surrogate prediction shape, bounded probabilities, leave-one-out
  evaluation, save/load round-trip and report guardrails.
- [x] Added reusable latency benchmarking under `firetwin.models.surrogate.benchmark`.
- [x] Added `scripts/benchmark_simulation_surrogate.py`.
- [x] Generated `reports/phase5b_simulation_surrogate_latency.md` and
  `reports/phase5b_simulation_surrogate_latency_metrics.json`.
- [x] Added named corpus profiles in `configs/simulation_corpus_profiles.json`.
- [x] Updated `scripts/build_simulation_corpus.py` with `--profile` and `--list-profiles`.
- [x] Added ignore guardrails so larger generated corpora under `data/simulation/` are not
  accidentally committed.
- [x] Built a larger local development corpus report at
  `reports/phase5b_simulation_corpus_development.md`.

### Result-Wise Simulation Corpus Smoke Artifact

- Samples: 6 synthetic scenarios on a 40x40 grid.
- Forecast horizons: 3h, 6h and 12h.
- Generator: wind-driven `EllipticalBaseline` over synthetic terrain/fuel/weather scenarios.
- Total final burned cells across smoke corpus: 3,460.
- Example sample contract: `initial_burned`, terrain/fuel covariates, scalar weather,
  `forecast_burned`, `forecast_active_front`, `forecast_hours`, `resolution_m` and
  `base_spread_rate_m_h`.

Interpretation: Phase 5B now has a reproducible simulator-corpus data contract for surrogate-model
development.

### Result-Wise Simulation Surrogate Smoke Baseline

- Model: `phase5b_logistic_simulation_surrogate_v1`.
- Artifact: `data/models/phase5b_surrogate_smoke.npz`.
- Evaluation: leave-one-simulation-out over the 6-sample smoke corpus.
- Features: 23 terrain/fuel/weather/geometry features.
- Mean Brier score: 0.11628 vs 0.20062 initial-state persistence.
- Mean Brier improvement vs persistence: +0.08434.
- Mean IoU at threshold 0.40: 0.678.

Interpretation: the first surrogate baseline is real and result-checked against the smoke corpus.
It is still a simulator-trained baseline, not an observed-wildfire model.

### Result-Wise Simulation Surrogate Latency Smoke Benchmark

- Benchmark: trained surrogate artifact vs reconstructed `EllipticalBaseline` simulator path.
- Samples: 6 smoke-corpus scenarios, 1,600 cells each, 3 horizons each.
- Repetitions: 9 timed runs per sample after 2 warmup runs.
- Mean simulator median latency: 77.819 ms.
- Mean surrogate median latency: 4.848 ms.
- Mean median speedup: 16.31x.
- Median of sample speedups: 17.52x.

Interpretation: the first surrogate is already fast enough for interactive smoke-scale engineering
loops. These timings are directional and should be repeated on a larger corpus before claiming a
production SLA.

### Result-Wise Development Corpus Profile

- Profile command: `python scripts/build_simulation_corpus.py --profile development`.
- Output directory: `data/simulation/phase5b_synthetic_development`.
- Git policy: generated samples are ignored; the reproducible report is committed.
- Samples: 36 synthetic scenarios on a 64x64 grid.
- Forecast horizons: 3h, 6h, 12h and 24h.
- Total final burned cells: 61,795.

Interpretation: Phase 5B now has a larger local corpus path for stronger surrogate training and
scenario-control experiments, while keeping repository size controlled.

### Remaining Phase 5B Work

- [x] Train a first lightweight surrogate on the simulation corpus.
- [x] Evaluate surrogate accuracy against initial-state persistence on held-out simulations.
- [x] Benchmark surrogate latency against the simulator baseline.
- [x] Add larger configurable corpus generation after the smoke contract is stable.
- [ ] Train and evaluate the surrogate on the larger development corpus.
- [ ] Connect scenario controls only after backend/surrogate inference is real.

## Future Phases

- **Phase 5A**: Next-day FIRMS active-fire samples, baselines, learned model and Explorer assets
- **Phase 5B**: Simulation corpus and surrogate
- **Phase 6**: Hybrid model
- **Phase 7**: Assimilation and calibrated uncertainty
- **Phase 8**: Simulated intervention planner
- **Phase 9**: Production application
- **Phase 10**: Research-quality release

## Overall Progress

```
Phase 0: ████████████████████ 100% ✅
Phase 1: ████████████████████ 100% ✅
Phase 2: ████████████████████ 100% ✅
Phase 3: ████████████████████ 100% ✅
Phase 4A: ████████████████████ 100% ✅
Phase 4B: ████████████████████ 100% ✅
Phase 4C: ████████████████████ 100% ✅
Phase 4D: ████████████████████ 100% ✅
Phase 4E: ████████████████████ 100% ✅
Phase 5A: ████████████████████ 100% ✅
Phase 5B: ███████████░░░░░░░░░  55% 🚧
...
Overall: ████████████████░░░░  76%
```

## Known Issues

- Pilot FireCase Zarrs are still final-burned-extent artifacts. Real FIRMS-derived initial-state
  companion artifacts exist separately under `data/initial_states/`, but the canonical case schema
  has not yet been rewritten to embed them as time-zero forecast inputs.
- Fuel load and fuel moisture are class-based static proxies, not observed live/dead fuel moisture.
- Real-data baseline evaluation now rejects attempts to treat final masks as hourly progression
  labels.
- `python` on the local machine resolves to Python 2.7 outside conda; use `conda activate firetwin`
  or `python3` for scripts.

## Blockers

No credential blocker remains. Phase 5A plus the first local Explorer are complete. Phase 5B has
started with deterministic simulation-corpus profiles, a first trained surrogate baseline, a
smoke-corpus latency benchmark and a larger local development corpus. The next major unfinished task
is training/evaluating the surrogate on that larger corpus plus the first real backend inference
contract for interactive controls.

## Notes

- Using conda for dependency management (better for geospatial packages)
- GitHub username: rajat116
- Email: rajatgupta116@gmail.com
- M1 Mac with 8GB RAM - keeping development lightweight
