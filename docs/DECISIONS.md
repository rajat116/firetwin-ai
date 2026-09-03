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

## Future Decisions

Document all future material decisions here, including:
- Data source selection and access methods
- Model architectures
- Evaluation protocols
- Infrastructure choices
- API design
- Frontend framework selection
- Deployment strategy
