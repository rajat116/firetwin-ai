# FireTwin Project Status

**Last Updated**: 2026-09-10
**Current Phase**: Phase 4E 🔎 - Progression/Initial-State Label Audit

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

## Phase 4E: Progression/Initial-State Label Audit 🔎

**Status**: IN PROGRESS (2026-09-10)

**Purpose**: Decide what real time-resolved labels the current pilot fires can honestly support
before constructing ignition states, progression targets or ML training samples.

### Completed Tasks

- [x] Added reusable progression-source audit utilities for NIFC, MTBS and FIRMS.
- [x] Added historical FIRMS standard-processing source support for 2014-era MODIS/VIIRS queries.
- [x] Updated FIRMS API validation to the current 1-5 day area/country API window.
- [x] Added VIIRS standard-processing CSV parsing for `bright_ti4`/`bright_ti5` columns.
- [x] Added `scripts/audit_progression_labels.py`.
- [x] Generated `reports/progression_label_audit.md`.
- [x] Added unit tests for chunking, historical source selection, source summaries and report
  rendering.

### Result-Wise Audit Findings

- Carlton Complex 2014: NIFC has 1 matching perimeter timestamp; MTBS not matched by current query;
  FIRMS skipped locally because `FIRMS_MAP_KEY` was not visible to settings.
- King 2014: NIFC has 1 matching perimeter timestamp; MTBS has 1 ignition/final record; FIRMS
  skipped locally because `FIRMS_MAP_KEY` was not visible to settings.
- Big Cougar 2014: NIFC has 1 matching perimeter timestamp; MTBS has 1 ignition/final record; FIRMS
  skipped locally because `FIRMS_MAP_KEY` was not visible to settings.

### Interpretation

The current NIFC/MTBS evidence does not support hourly perimeter labels for any pilot fire. FIRMS
historical active-fire detections are the next required data source for irregular hotspot/progression
labels. Until that audit passes, the pilot artifacts remain valid final-extent cases, not
short-horizon forecast samples.

### Remaining Phase 4E Work

- [ ] Put `FIRMS_MAP_KEY` in `.env` or export it in the active shell and rerun
  `python3 scripts/audit_progression_labels.py`.
- [ ] If FIRMS has enough detections, design uncertainty-aware irregular hotspot/progression labels.
- [ ] If FIRMS is too sparse/noisy for these 2014 pilots, select newer pilot fires with denser
  timestamped observations before Phase 5.

## Future Phases

- **Phase 5**: Simulation corpus and surrogate
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
Phase 4E: ████████░░░░░░░░░░░░  40% 🔎
...
Overall: ████████████░░░░░░░░  60%
```

## Known Issues

- Pilot cases are final-burned-extent artifacts with real terrain, real fuel-model classes and real
  ERA5-Land scalar weather, but placeholder empty initial fire states.
- Fuel load and fuel moisture are class-based static proxies, not observed live/dead fuel moisture.
- Real-data baseline evaluation now rejects attempts to treat final masks as hourly progression
  labels.
- `python` on the local machine resolves to Python 2.7 outside conda; use `conda activate firetwin`
  or `python3` for scripts.

## Blockers

Phase 4E needs `FIRMS_MAP_KEY` visible to FireTwin settings so historical MODIS/VIIRS detections can
be audited for the current pilot fire windows.

## Notes

- Using conda for dependency management (better for geospatial packages)
- GitHub username: rajat116
- Email: rajatgupta116@gmail.com
- M1 Mac with 8GB RAM - keeping development lightweight
