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

**Current Phase**: Phase 5B In Progress - Simulation Corpus and First Surrogate Baseline

- ✅ **Phase 0**: Repository and engineering foundation
- ✅ **Phase 1**: Synthetic data pipeline, baseline models, evaluation metrics
- ✅ **Phase 2**: Real data source integration (all 6 clients + validation + inventory)
- ✅ **Phase 3**: Historical final-extent case builder (3 pilot fires with validated area/CRS metadata)
- ✅ **Phase 4A**: Real USGS 3DEP terrain enrichment with derived slope/aspect
- ✅ **Phase 4B**: Real LANDFIRE LF2022 FBFM40 fuel-model enrichment
- ✅ **Phase 4C**: ERA5-Land hourly weather enrichment
- ✅ **Phase 4D**: Final-extent baseline diagnostics and forecast-label guardrails
- ✅ **Phase 4E**: FIRMS-backed progression labels, initial-state artifacts and validation overlays
- ✅ **Phase 5A**: Leakage-safe next-day FIRMS active-fire samples, baselines, learned forecasts, calibration and Explorer assets
- 🚧 **Phase 5B**: Deterministic synthetic simulation corpus plus first trained surrogate baseline

Current pilot cases contain real NIFC/MTBS-derived final perimeter masks, real USGS 3DEP
terrain-derived elevation/slope/aspect, real LANDFIRE LF2022 FBFM40 fuel-model classes, and real
ERA5-Land hourly weather summarized at documented ignition/discovery reference times. Fuel load and
fuel moisture remain deterministic class-based proxies. The canonical FireCase initial-state arrays
remain placeholders, but FIRMS-derived initial active-fire companion artifacts now exist under
`data/initial_states/`. The cases are not valid 3/6/12/24-hour fire-progression labels yet.

Phase 4E is auditing timestamped observations before any label reconstruction. NIFC/MTBS checks show
the current 2014 pilots have only one perimeter timestamp each, so hourly perimeter labels are still
unsupported. FIRMS historical detections are available for all three pilots and support irregular
hotspot/progression targets after filtering. Daily-binned FIRMS label artifacts can now be built as
companion Zarr products under `data/labels/`, with earliest-window initial-state estimates under
`data/initial_states/` and Phase 5A next-day learning samples under `data/training/firms_next_day/`.
A first calibrated observed-label logistic model now beats persistence on held-out pilot fires by
Brier score, while remaining explicitly scoped to next-day FIRMS active-fire evidence rather than
exact burned-perimeter spread.
Leave-one-fire-out forecast artifacts, reliability diagnostics and Explorer-ready preview assets now
exist for future UI layers under ignored local forecast storage plus committed reports, figures and
a lightweight manifest.
Phase 5B has started with a reproducible synthetic simulation-corpus generator that writes
surrogate-ready NPZ samples and a guarded manifest. A first lightweight logistic surrogate now trains
against that corpus and beats initial-state persistence on leave-one-simulation-out smoke evaluation
(`0.11628` mean Brier vs `0.20062` persistence, `0.678` mean IoU). This corpus is
simulator-derived and is not real wildfire truth.

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

### Try the Demo

**Phase 1: Synthetic Fire Evolution**

Generate a synthetic fire case and run baseline forecasts:

```bash
# Generate synthetic fire evolution (50x50 grid, 12 hours)
firetwin generate-synthetic --case-id demo_001 --grid-size 50 --hours 12 --seed 42

# Run baseline forecast models
firetwin run-baselines data/processed/demo_001.zarr --horizons "3,6,12"

# Evaluate forecast accuracy
firetwin evaluate data/processed/demo_001.zarr data/forecasts/demo_001 --horizons "3,6,12"
```

**Phase 2: Real Data Access**

All 6 data source clients are implemented and tested:

```python
from firetwin.data.clients import FIRMSClient, NIFCHistoricalClient, MTBSClient
from firetwin.data.clients import ERA5LandClient, LANDFIREClient, USGS3DEPClient

# Example: Query NIFC Historical fire perimeters
nifc = NIFCHistoricalClient()
perimeters = nifc.get_fire_by_name("King", year=2014)
gdf = nifc.perimeters_to_geodataframe(perimeters)
```

**Phase 4C: Historical Final-Extent Fire Cases With Real Terrain + Fuels + Weather** ✨ NEW

Build canonical FireCase objects from real historical perimeter data plus USGS 3DEP terrain,
LANDFIRE LF2022 FBFM40 fuel models, and ERA5-Land hourly weather:

```bash
# Build all 3 pilot fires (Carlton Complex, King Fire, Big Cougar)
python3 scripts/build_all_pilot_fires.py

# Validate the generated fire cases
python3 scripts/validate_fire_cases.py
```

Generated local fire cases are written to ignored data storage under `data/fire_cases/`:
- Carlton Complex 2014 (WA): 275k acres, 21 LANDFIRE fuel classes, ERA5 weather 26.9C/RH 31%
- King Fire 2014 (CA): 98k acres, 26 LANDFIRE fuel classes, ERA5 weather 22.8C/RH 29%
- Big Cougar 2014 (OR/ID): 65k acres, 21 LANDFIRE fuel classes, ERA5 weather 26.3C/RH 32%

These artifacts are explicitly marked with `target_type=final_burned_extent` and
`covariate_status=partial_real_terrain_fuels_weather` so downstream evaluation can use real
covariates while still refusing to treat final extent as short-horizon progression.

Run non-temporal real-data diagnostics with:

```bash
firetwin evaluate-final-extent data/fire_cases/king_2014.zarr
```

Audit whether the current pilots can support progression labels:

```bash
python3 scripts/audit_progression_labels.py
```

Build FIRMS hotspot/progression label artifacts:

```bash
python3 scripts/build_firms_progression_labels.py
```

Build FIRMS-derived initial active-fire state artifacts:

```bash
python3 scripts/build_firms_initial_states.py
```

Validate FIRMS companion artifacts and generate overlay figures:

```bash
python3 scripts/validate_firms_artifacts.py
```

Build leakage-safe next-day FIRMS active-fire sample artifacts:

```bash
python3 scripts/build_firms_next_day_samples.py
```

Evaluate next-day FIRMS baseline diagnostics:

```bash
python3 scripts/evaluate_firms_next_day_baselines.py
```

Train and evaluate the first learned next-day FIRMS active-fire model:

```bash
python3 scripts/train_firms_next_day_model.py
```

Build leave-one-fire-out learned forecast artifacts for future Explorer layers:

```bash
python3 scripts/build_firms_next_day_forecasts.py
```

Evaluate learned forecast calibration and diagnostic thresholds:

```bash
python3 scripts/evaluate_firms_next_day_forecasts.py
```

Export lightweight Explorer-ready preview assets and manifest:

```bash
python3 scripts/export_firms_explorer_assets.py
```

Serve the first local FireTwin Explorer UI:

```bash
python3 scripts/serve_explorer.py --host 127.0.0.1 --port 8000
```

Then open [`http://127.0.0.1:8000/frontend/`](http://127.0.0.1:8000/frontend/). The preview server
is allowlisted so it serves the Explorer, manifest and preview figures without exposing `.env` or
arbitrary repository files.

Open the globe-oriented public demo at
[`http://127.0.0.1:8000/frontend/globe.html`](http://127.0.0.1:8000/frontend/globe.html).

Build a deployable static Explorer bundle:

```bash
python3 scripts/build_explorer_site.py --output-dir dist/explorer
```

The bundle contains only the Explorer, manifest and referenced preview PNGs.

Smoke-test the deployable bundle, including manifest integrity and preview-image visual checks,
before sharing it:

```bash
python3 scripts/smoke_explorer_bundle.py --bundle-dir dist/explorer
```

Run the FireTwin API backend for the same forecast catalog:

```bash
uvicorn firetwin.api.main:app --reload
```

Key endpoints include `/health`, `/api/explorer/cases` and
`/api/forecast/firms-next-day/{case_id}`. The current forecast endpoint is artifact-backed: it
serves validated leave-one-fire-out FIRMS forecast products through a live API contract, ready for a
globe frontend and later on-demand inference.

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for complete API documentation.

### Configuration

Copy `.env.example` to `.env` and add your API credentials:

```bash
cp .env.example .env
```

Required credentials:
- **NASA FIRMS**: Get your MAP_KEY from [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)
- **Copernicus CDS**: Register at [https://cds.climate.copernicus.eu/](https://cds.climate.copernicus.eu/) and accept ERA5-Land terms before rebuilding real-weather cases

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
├── frontend/              # Dependency-free static Explorer UI
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
- [x] **Phase 1**: Synthetic end-to-end vertical slice
- [x] **Phase 2**: Data-source clients, validation, inventory, and audit
- [x] **Phase 3**: Historical case builder (3 validated pilot fires with real perimeters)
- [x] **Phase 4A**: Real USGS 3DEP terrain covariates
- [x] **Phase 4B**: Real LANDFIRE FBFM40 fuel-model covariates
- [x] **Phase 4C**: Real ERA5-Land weather artifacts
- [x] **Phase 4D**: Final-extent baseline diagnostics and guardrails
- [x] **Phase 4E**: FIRMS-backed progression labels and initial-state artifacts
- [x] **Phase 5A**: Next-day FIRMS active-fire sample artifacts, baselines, learned forecasts, calibration and Explorer assets
- [ ] **Phase 5B**: Simulation corpus and first surrogate baseline (in progress)
- [ ] **Phase 6**: Hybrid model
- [ ] **Phase 7**: Assimilation and calibrated uncertainty
- [ ] **Phase 8**: Simulated intervention planner
- [ ] **Phase 9**: Production application
- [ ] **Phase 10**: Research-quality release

## Documentation

- [Project Status](docs/PROJECT_STATUS.md)
- [Technical Decisions](docs/DECISIONS.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [Machine-Readable Data Source Registry](configs/data_sources.yaml)
- [Data Validation](docs/DATA_VALIDATION.md)
- [Evaluation Protocol](docs/EVALUATION_PROTOCOL.md)
- [Data Availability Audit](reports/data_availability_audit.md)
- [FIRMS Label Artifact Report](reports/firms_label_artifacts.md)
- [FIRMS Initial-State Artifact Report](reports/firms_initial_state_artifacts.md)
- [FIRMS Artifact Validation Report](reports/firms_artifact_validation.md)
- [FIRMS Next-Day Sample Report](reports/firms_next_day_samples.md)
- [FIRMS Next-Day Baseline Report](reports/firms_next_day_baselines.md)
- [FIRMS Next-Day Learned Model Report](reports/firms_next_day_learned_model.md)
- [FIRMS Next-Day Learned Forecast Artifact Report](reports/firms_next_day_forecasts.md)
- [FIRMS Next-Day Forecast Calibration Report](reports/firms_next_day_forecast_calibration.md)
- [FIRMS Next-Day Explorer Asset Report](reports/firms_next_day_explorer_assets.md)
- [FIRMS Next-Day Explorer Manifest](data/manifests/firms_next_day_explorer_manifest.json)
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
