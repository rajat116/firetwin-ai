# Technical Decisions

This document records all material technical decisions made during FireTwin development.

## Format

Each decision includes:
- **Date**: When the decision was made
- **Context**: Why this decision was needed
- **Decision**: What was decided
- **Rationale**: Why this option was chosen
- **Alternatives**: What else was considered
- **Consequences**: Trade-offs and implications

---

## Decision 1: Dependency Management - conda over uv

**Date**: 2026-09-03  
**Phase**: 0 - Repository Setup

### Context

Need to choose a dependency management tool for a project with:
- Heavy geospatial dependencies (GDAL, rasterio, geopandas)
- PyTorch for deep learning
- Scientific computing stack (numpy, scipy, xarray)
- M1 Mac development environment with 8GB RAM

### Decision

Use **conda** (via environment.yml) for dependency management instead of uv or pip.

### Rationale

1. **Geospatial dependencies**: GDAL, rasterio, and geopandas have complex C/C++ dependencies that conda handles much better than pip
2. **M1 Mac optimization**: conda-forge provides excellent M1-optimized builds for PyTorch and scientific packages
3. **Portfolio credibility**: conda/mamba is industry standard for geospatial ML projects
4. **Proven reliability**: Well-tested for scientific computing workflows
5. **Reduced debugging time**: Focus on building the system, not fighting dependency issues

### Alternatives Considered

**uv**:
- Pros: Extremely fast (10-100x faster), lightweight, modern
- Cons: Geospatial packages are tricky, newer tool with smaller ecosystem for scientific computing

**venv + pip**:
- Pros: Standard Python approach, simple
- Cons: GDAL/rasterio installation is notoriously difficult, especially on M1 Macs

### Consequences

- Slower environment creation (acceptable trade-off)
- Larger disk footprint (~2-3 GB for full environment)
- Can still use pip for pure Python packages within conda environment
- Better compatibility with HPC clusters if needed later

---

## Decision 2: GitHub Username

**Date**: 2026-09-03  
**Phase**: 0 - Repository Setup

### Context

Need to create GitHub repository with correct user credentials.

### Decision

- **Username**: rajat116
- **Email**: rajatgupta116@gmail.com
- **Repository**: https://github.com/rajat116/firetwin-ai

### Rationale

Using user's existing GitHub profile for portfolio visibility.

---

## Decision 3: License - Apache 2.0

**Date**: 2026-09-03  
**Phase**: 0 - Repository Setup

### Context

Need to select an open-source license for the project.

### Decision

Use **Apache License 2.0**.

### Rationale

1. **Patent protection**: Explicit patent grant protects users and contributors
2. **Widely used in ML/data science**: Recognized and trusted in the community
3. **Permissive**: Allows commercial use while requiring attribution
4. **Professional**: Preferred by many organizations over MIT

### Alternatives Considered

**MIT License**:
- Simpler and more permissive
- No explicit patent protection

### Consequences

- Contributors must grant patent license
- Proper attribution required for derivative works
- Compatible with most other open-source projects

---

## Decision 4: MyPy Configuration - Skip Site Packages

**Date**: 2026-09-03  
**Phase**: 0 - Repository Setup

### Context

MyPy type checking fails on Python 3.12 with the following error:
```
/usr/share/miniconda/envs/firetwin/lib/python3.12/site-packages/numpy/__init__.pyi:737: error: Type statement is only supported in Python 3.12 and greater  [syntax]
```

This occurs because:
- NumPy 2.5.2 type stubs use Python 3.12+ `type` statement syntax
- MyPy 2.3.1 (latest available) has incomplete support for this new syntax
- The parsing error happens before mypy configuration can skip the module

### Decision

Use `--no-site-packages` flag in all mypy invocations to skip type checking of installed packages.

### Rationale

1. **Still checks our code**: Our source code is fully type-checked
2. **Avoids third-party stub issues**: Skips all site-packages, avoiding compatibility problems
3. **CI compatibility**: Works across Python 3.11 and 3.12
4. **Temporary workaround**: Can be removed when mypy/numpy compatibility improves
5. **Precedent**: Common practice for projects with complex dependencies

### Alternatives Considered

**Downgrade NumPy**:
- Lose latest features, bug fixes, and Python 3.12 optimizations
- Not future-proof

**Skip MyPy on Python 3.12**:
- Would miss type errors in our code
- Defeats purpose of type checking

**Disable MyPy entirely**:
- Lose valuable type safety
- Against best practices

### Consequences

- We don't get type checking against third-party API signatures
- Our own code still gets full type checking
- Must rely on runtime checks and tests for third-party API usage
- Can re-enable site-packages checking when tooling matures

---

## Decision 5: Phase 3 Real Cases Are Final-Extent Artifacts

**Date**: 2026-09-09
**Phase**: 3 - Historical Fire Case Builder

### Context

The first real pilot fire cases successfully rasterize NIFC/MTBS-derived perimeters, but the
canonical cases still use placeholder terrain, fuels, weather, and initial-state fields. The master
project brief explicitly says not to treat final perimeters as time-resolved progression labels.

### Decision

Mark Phase 3 pilot cases as `target_type=final_burned_extent` and
`covariate_status=placeholder` in FireCase metadata and Zarr attributes. Keep hourly real-data
forecast evaluation out of scope until time-stamped observations and real covariates are added.

### Rationale

This preserves the value of the Phase 3 artifacts while preventing leakage or inflated claims. The
cases are valid for final-extent validation and pipeline testing, but not yet for 3/6/12/24-hour
forecast benchmarking.

### Alternatives Considered

**Treat generated masks as forecast targets**:
- Rejected because final extent would leak future information into short-horizon evaluation.

**Delay all real-case artifacts until every covariate is integrated**:
- Rejected because the perimeter-to-grid pipeline is independently valuable and now carries clear
  limitations.

### Consequences

- Baseline/model code must inspect target metadata before reporting horizon-specific real-data
  metrics.
- Phase 4 should enrich or reconstruct time-stamped states before claiming real-data forecasting
  performance.

---

## Decision 6: Machine-Readable Data Source Registry

**Date**: 2026-09-09
**Phase**: 3 - Data Foundation Cleanup

### Context

The master project brief requires a machine-readable registry at `configs/data_sources.yaml` in
addition to human documentation in `docs/DATA_SOURCES.md`.

### Decision

Add `configs/data_sources.yaml` with provider, products, variables, resolution, access method,
official URLs, access date, version notes, checksums where available, and known limitations for
the current FireTwin data sources.

### Rationale

The YAML registry gives later builders a structured source of truth for provenance, audits and
dataset manifests.

### Consequences

- Future downloads should update source versions/checksums at case-build time.
- Docs and config must be kept in sync when source behavior changes.

---

## Decision 7: Use USGS 3DEP 1 Arc-Second DEM for Phase 4A Terrain

**Date**: 2026-09-09
**Phase**: 4A - Real Terrain Enrichment

### Context

The pilot fire cases use a 100m model grid. USGS 3DEP 1/3 arc-second tiles are available but are
hundreds of megabytes per 1-degree tile, while 1 arc-second GeoTIFF tiles are still real 3DEP DEM
data and finer than the current model grid.

### Decision

Use `National Elevation Dataset (NED) 1 arc-second` as the default USGS 3DEP product for Phase 4A.
Select the latest GeoTIFF product per 1-degree tile, cache the source DEMs under ignored
`data/raw/3dep/`, resample them onto the FireTwin grid, and derive slope/aspect from the aligned
elevation.

Generated cases are marked as `target_type=final_burned_extent` and
`covariate_status=partial_real_terrain`.

### Rationale

This replaces dummy terrain with physically meaningful covariates while keeping download size and
local processing practical. It also keeps the metadata honest: terrain is real, while fuel, weather
and time-resolved progression remain unfinished.

### Consequences

- Pilot Zarrs should now fail validation if terrain is flat or missing.
- Future LANDFIRE and weather work can build on an already-aligned terrain grid.
- 1/3 arc-second DEM can be enabled later for cases where storage and compute budgets justify it.

---

## Decision 8: Use LANDFIRE LF2022 FBFM40 ImageServer for Phase 4B Fuels

**Date**: 2026-09-09
**Phase**: 4B - Real Fuel Enrichment

### Context

The pilot fire cases need real fuel-model covariates on the same 100m model grid as the perimeter
and terrain layers. LANDFIRE provides full extent downloads, product services, image services, and
WCS/WMS access. Bulk national downloads would add unnecessary storage pressure for the current
pilot AOIs.

### Decision

Use the public LANDFIRE LF2022 CONUS FBFM40 ArcGIS ImageServer export endpoint for Phase 4B. Export
each pilot AOI directly to a GeoTIFF in the target CRS, target bounds and target raster dimensions.
Use nearest-neighbor resampling so categorical FBFM40 class values are preserved.

LANDFIRE non-burnable codes (`91`, `92`, `93`, `98`, `99`) are converted to `0` in FireTwin's
canonical `fuel_model` grid because existing baselines treat `fuel_model > 0` as burnable. Burnable
FBFM40 class codes are preserved. Fuel load and moisture companion arrays are deterministic
class-based proxies until FireTwin adds source-derived fuelbed attributes or live/dead fuel
moisture.

Generated cases are marked as `target_type=final_burned_extent` and
`covariate_status=partial_real_terrain_fuels`.

### Rationale

The ImageServer path is reproducible, compact and aligned with FireTwin's current grid-based case
builder. It avoids manual AOI downloads while keeping categorical fuel semantics intact.

### Consequences

- Pilot Zarrs should now fail validation if fuels remain uniform FBFM 10.
- Fuel-model provenance records LANDFIRE LF2022 FBFM40.
- Weather and ignition/progression labels remain unfinished; Phase 4B cases are still not
  short-horizon forecast samples.
- Fuel load and moisture proxy limitations must be visible in metadata and reporting.

---

## Decision 9: Use ERA5-Land Hourly AOI Mean Weather for Phase 4C

**Date**: 2026-09-10
**Phase**: 4C - Real Weather Enrichment

### Context

The current FireTwin schema stores `WeatherData` as scalar forcing values, while ERA5-Land is an
hourly gridded reanalysis product on a coarse 0.1 degree grid. The pilot cases are still
final-burned-extent artifacts, not time-resolved forecast samples, so weather should be treated as
an initialization/conditioning covariate rather than a progression label.

### Decision

Use ERA5-Land hourly data from the Copernicus Climate Data Store API. For the current schema,
download/cache a small NetCDF window around a documented ignition or discovery reference time,
select the nearest hourly timestamp, and summarize the AOI by spatial mean. Store temperature in
Celsius, relative humidity derived from 2m temperature and dewpoint, wind speed from 10m u/v
components, and meteorological wind direction degrees from north.

Generated real-weather cases will be marked as `target_type=final_burned_extent` and
`covariate_status=partial_real_terrain_fuels_weather`.

### Rationale

This replaces placeholder weather without inventing fine-scale meteorology. It also keeps the code
compatible with the current scalar schema while leaving room for a future time-varying weather cube
when the model/label design justifies it.

### Consequences

- Phase 4C artifact rebuilding requires local CDS account setup and accepted ERA5-Land terms.
- The pilot Zarrs rebuilt on 2026-09-10 now store real ERA5-Land scalar weather.
- Resampling or summarizing ERA5-Land does not create 30m/100m weather truth.
- Forecast experiments must still refuse to use final burned extent as an hourly progression label.
- A later schema revision should add time-varying weather arrays for real forecast windows.

---

## Future Decisions

Document all future material decisions here, including:
- Data source selection and access methods
- Model architectures
- Evaluation protocols
- Infrastructure choices
- API design
- Frontend framework selection
- Deployment strategy
