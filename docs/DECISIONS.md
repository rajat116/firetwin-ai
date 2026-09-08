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

**Date**: 2026-09-08  
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

**Date**: 2026-09-08  
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

## Future Decisions

Document all future material decisions here, including:
- Data source selection and access methods
- Model architectures
- Evaluation protocols
- Infrastructure choices
- API design
- Frontend framework selection
- Deployment strategy
