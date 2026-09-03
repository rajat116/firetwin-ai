# 🔥 FireTwin

> **⚠️ Research Prototype**: Not for operational wildfire response, evacuation planning, or safety-critical decision-making.

A research-grade wildfire digital twin that combines satellite observations, weather, terrain, and vegetation with physics-guided machine learning to produce probabilistic fire-spread forecasts and evaluate simulated containment strategies.

[![CI](https://github.com/rajat116/firetwin-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/rajat116/firetwin-ai/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

## Overview

FireTwin implements a closed-loop wildfire digital twin:

```
observation → state estimation → physics-based simulation → 
fast learned surrogate → uncertainty → new observation assimilation → 
simulated intervention analysis
```

This project answers **measurable research questions** about hybrid physics-ML forecasting, data assimilation, uncertainty calibration, and simulated intervention planning—while maintaining a production-grade codebase suitable for portfolio demonstration.

## Key Features

- 🛰️ **Multi-source data integration**: NASA FIRMS, NIFC/WFIGS, MTBS, ERA5-Land, LANDFIRE, USGS 3DEP
- 🔬 **Physics-guided ML**: Hybrid models combining interpretable fire simulators with learned components
- 📊 **Probabilistic forecasting**: Calibrated uncertainty with ensemble methods
- 🔄 **Data assimilation**: Real-time state updates as new observations arrive
- 🎯 **Intervention planning**: Simulated containment strategy optimization and evaluation
- 🌐 **Interactive 3D visualization**: MapLibre GL + deck.gl for geospatial rendering
- 📈 **MLOps pipeline**: MLflow tracking, DVC data versioning, automated CI/CD

## Project Status

**Current Phase**: Phase 0 - Repository and Engineering Foundation ✅

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for detailed progress tracking.

## Quick Start

### Prerequisites

- Python 3.11+
- conda or mamba
- Git

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/rajat116/firetwin-ai.git
cd firetwin-ai
```

2. **Create conda environment**:
```bash
conda env create -f environment.yml
conda activate firetwin
```

3. **Install the package**:
```bash
pip install -e .
```

4. **Run diagnostics**:
```bash
firetwin doctor
```

### Configuration

Copy `.env.example` to `.env` and add your API credentials:

```bash
cp .env.example .env
```

Required credentials:
- **NASA FIRMS**: Get your MAP_KEY from [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)
- **Copernicus CDS**: Register at [https://cds.climate.copernicus.eu/](https://cds.climate.copernicus.eu/)

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -m "not data" -v
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Install pre-commit hooks
make pre-commit
```

## Architecture

```
firetwin-ai/
├── src/firetwin/          # Core Python package
│   ├── data/              # Data acquisition and processing
│   ├── geo/               # Geospatial utilities
│   ├── simulation/        # Physics-based simulators
│   ├── models/            # ML models (baselines, surrogate, hybrid)
│   ├── assimilation/      # Data assimilation
│   ├── interventions/     # Simulated intervention planning
│   ├── evaluation/        # Metrics and evaluation protocols
│   ├── tracking/          # Experiment tracking
│   └── api/               # FastAPI backend
├── frontend/              # React + MapLibre GL + deck.gl
├── notebooks/             # Jupyter notebooks for exploration
├── tests/                 # Comprehensive test suite
├── docs/                  # Detailed documentation
└── data/                  # Data directory (gitignored)
```

## Data Sources

FireTwin integrates multiple authoritative data sources:

| Source | Purpose | Official Link |
|--------|---------|---------------|
| NASA FIRMS | Active fire observations | [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/) |
| NIFC/WFIGS | Fire perimeters | [data-nifc.opendata.arcgis.com](https://data-nifc.opendata.arcgis.com/) |
| MTBS | Burn severity | [mtbs.gov](https://www.mtbs.gov/) |
| ERA5-Land | Weather reanalysis | [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/) |
| LANDFIRE | Fuels & vegetation | [landfire.gov](https://www.landfire.gov/) |
| USGS 3DEP | Terrain elevation | [usgs.gov/3dep](https://www.usgs.gov/3d-elevation-program) |

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for detailed information about licenses, access methods, and limitations.

## Research Questions

FireTwin is designed to answer measurable questions:

1. **RQ1 - Forecasting**: Can hybrid physics-ML models outperform both pure physics and pure ML baselines?
2. **RQ2 - Speed**: Can learned surrogates maintain accuracy while reducing latency?
3. **RQ3 - Assimilation**: Does incorporating new observations improve forecast accuracy?
4. **RQ4 - Generalization**: How does performance degrade on unseen regions or extreme conditions?
5. **RQ5 - Uncertainty**: Are probabilistic forecasts calibrated?
6. **RQ6 - Counterfactual robustness**: Do simulated interventions remain effective under uncertainty?

## Roadmap

- [x] **Phase 0**: Repository and engineering foundation
- [ ] **Phase 1**: Synthetic end-to-end vertical slice
- [ ] **Phase 2**: Data-source smoke tests and audit
- [ ] **Phase 3**: Historical case builder
- [ ] **Phase 4**: Real-data baselines
- [ ] **Phase 5**: Simulation corpus and surrogate
- [ ] **Phase 6**: Hybrid model
- [ ] **Phase 7**: Assimilation and calibrated uncertainty
- [ ] **Phase 8**: Simulated intervention planner
- [ ] **Phase 9**: Production application
- [ ] **Phase 10**: Research-quality release

## Documentation

- [Project Status](docs/PROJECT_STATUS.md)
- [Technical Decisions](docs/DECISIONS.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [Product Specification](docs/PRODUCT_SPEC.md)
- [UI/UX Specification](docs/UI_UX_SPEC.md)
- [Demo Script](docs/DEMO_SCRIPT.md)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines.

## Safety and Limitations

FireTwin is a **research prototype** with important limitations:

- ❌ Not validated for operational emergency response
- ❌ Not certified for evacuation planning
- ❌ Not suitable for safety-critical decisions
- ❌ Simulated interventions are hypothetical only
- ⚠️ Models may fail on extreme, rare, or out-of-distribution fires
- ⚠️ Data quality varies by source, region, and time period
- ⚠️ Uncertainty estimates are model-dependent

See [`docs/SAFETY_AND_LIMITATIONS.md`](docs/SAFETY_AND_LIMITATIONS.md) for complete discussion.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use FireTwin in your research, please cite:

```bibtex
@software{gupta2026firetwin,
  author = {Gupta, Rajat},
  title = {FireTwin: A Research-Grade Wildfire Digital Twin},
  year = {2026},
  url = {https://github.com/rajat116/firetwin-ai}
}
```

## Acknowledgments

This project builds upon open-source geospatial and ML tools, authoritative wildfire and weather data sources, and physics-based fire modeling research. See individual data source documentation for attribution requirements.

---

**Author**: Rajat Gupta ([rajatgupta116@gmail.com](mailto:rajatgupta116@gmail.com))  
**Repository**: [https://github.com/rajat116/firetwin-ai](https://github.com/rajat116/firetwin-ai)
