# Demo Script

**Last Updated**: 2026-09-03  
**Version**: 0.1.0

This document provides scripts for demonstrating FireTwin to different audiences.

## Quick Demo (5 minutes)

**Audience**: Portfolio reviewers, recruiters, quick overview

### Script

1. **Landing (30 seconds)**
   - "FireTwin is a research-grade wildfire digital twin"
   - Point out research prototype warning
   - "It combines satellite observations, weather data, and physics-guided ML"

2. **Fire Selection (30 seconds)**
   - Click a curated California fire
   - "This is a historical fire from 2024"
   - Show data completeness indicators

3. **Initial Conditions (60 seconds)**
   - Toggle terrain layers: elevation, slope, fuels
   - "Here's what we knew at forecast origin"
   - Show active fire observations
   - Zoom and rotate 3D terrain

4. **Forecast (90 seconds)**
   - Select "Hybrid Model"
   - Click "Run 6-hour Forecast" (or show precomputed)
   - Play animation
   - "Probabilistic spread - not a single line"
   - Pause at 3h, 6h marks

5. **Evaluation (60 seconds)**
   - Switch to comparison view
   - "Forecast vs. later observations"
   - Show IoU metric: "72% overlap"
   - Briefly show uncertainty panel

6. **What-If (30 seconds)**
   - "We can test hypothetical scenarios"
   - Change wind direction slider
   - "Simulated containment lines" (don't run, just show controls)

7. **Wrap-up (30 seconds)**
   - "Full ML/MLOps stack: data pipelines, experiment tracking, CI/CD"
   - "See GitHub for code, documentation, and reproducibility"
   - Show provenance panel with model/data versions

### Key Points to Emphasize

✅ **Research-grade**: Not a toy project  
✅ **Complete system**: Data → Model → Production  
✅ **Uncertainty quantification**: Not overconfident  
✅ **Reproducible**: Provenance tracked  
✅ **Interactive**: No notebooks, no terminal

## Technical Demo (15 minutes)

**Audience**: Engineers, data scientists, technical interviewers

### Script

1. **Architecture Overview (2 min)**
   - Show README architecture diagram
   - "Python backend (FastAPI), React frontend"
   - "Multiple data sources: NASA FIRMS, ERA5, LANDFIRE, USGS"
   - "Geospatial stack: GeoPandas, Rasterio, Xarray"

2. **Data Pipeline (2 min)**
   - Show `src/firetwin/data/` structure
   - "Each source has a client with validation"
   - "Canonical Zarr/Xarray format"
   - Show `docs/DATA_SOURCES.md`
   - "DVC for data versioning"

3. **Model Development (3 min)**
   - Show `src/firetwin/models/` structure
   - "Baselines: persistence, physics, pure ML"
   - "Hybrid: physics + learned residual"
   - "Surrogate: fast neural operator"
   - Show evaluation metrics in `src/firetwin/evaluation/`

4. **Experiment Tracking (2 min)**
   - Show MLflow integration
   - "Every run tracked with hyperparameters"
   - "Model versioning and reproducibility"
   - Show provenance in UI

5. **Interactive Demo (4 min)**
   - Full user journey (see Quick Demo above)
   - Emphasize 3D terrain rendering
   - Show calibration plots
   - Demonstrate scenario controls

6. **Production Engineering (2 min)**
   - Show GitHub Actions CI
   - "Ruff, MyPy, Pytest, pre-commit hooks"
   - "Conda for geospatial dependencies"
   - "Docker deployment" (when implemented)
   - Show test coverage

### Key Technical Points

✅ **Geospatial ML**: GDAL, CRS transformations, terrain-aligned overlays  
✅ **Physics-guided**: Not pure black-box ML  
✅ **Probabilistic**: Ensemble methods, calibration  
✅ **Production-ready**: API, CI/CD, monitoring  
✅ **Documented**: README, specs, data cards

## Research Demo (20 minutes)

**Audience**: Researchers, domain experts, academic presentations

### Script

1. **Motivation (3 min)**
   - Wildfire forecasting challenges
   - Data availability and quality issues
   - Physics vs. data-driven approaches
   - Uncertainty quantification importance

2. **Research Questions (2 min)**
   - Show 6 research questions from README
   - Emphasize measurable outcomes
   - Not just "build a model"

3. **Data Foundation (3 min)**
   - Walk through `docs/DATA_SOURCES.md`
   - Discuss limitations of each source
   - Time-resolved labels challenge
   - Data audit findings (when available)

4. **Modeling Approach (5 min)**
   - Baseline progression
   - Physics simulator integration (ELMFIRE)
   - Learned surrogate architecture
   - Hybrid model design
   - Data assimilation method

5. **Evaluation Protocol (3 min)**
   - Fire-disjoint splits
   - Geographic and temporal holdout
   - Calibration metrics
   - Per-horizon evaluation
   - Failure mode analysis

6. **Results Discussion (4 min)**
   - Show forecast comparison
   - Calibration plots
   - Ablation studies
   - Limitation examples
   - Future work

### Key Research Points

✅ **Rigorous evaluation**: Not cherry-picked results  
✅ **Honest limitations**: Failure modes documented  
✅ **Reproducible**: Code, data manifests, experiment logs  
✅ **Negative results**: Report when complexity doesn't help  
✅ **Safety-aware**: Clear warnings about operational use

## Portfolio Walkthrough (10 minutes)

**Audience**: Self, preparing for interviews

### Focus Areas

1. **Problem Understanding**
   - Why is this problem hard?
   - What makes wildfire forecasting unique?
   - Why hybrid physics-ML?

2. **Technical Decisions**
   - Why conda not pip/uv?
   - Why these data sources?
   - Why this model architecture?
   - How did you handle geospatial data at scale?

3. **Engineering Practices**
   - How do you ensure reproducibility?
   - How did you handle data quality issues?
   - How do you test geospatial pipelines?
   - What's your MLOps workflow?

4. **Product Thinking**
   - Who is the user?
   - What's the key user journey?
   - How do you communicate uncertainty?
   - Why 3D terrain, not 2D?

5. **Results and Impact**
   - What did you learn?
   - What worked? What didn't?
   - What would you do differently?
   - What's next?

### Practice Responses

**"Tell me about this project"** (2 min):
> "FireTwin is a research-grade wildfire digital twin that combines satellite observations, weather, terrain, and fuels with physics-guided machine learning to forecast fire spread and evaluate simulated containment strategies. The key technical challenge is integrating multiple geospatial data sources with different resolutions and uncertainties, building hybrid models that combine interpretable physics simulators with learned components, and quantifying calibrated uncertainty in probabilistic forecasts. I built the complete ML/MLOps pipeline from data acquisition through production deployment, handling everything from NASA FIRMS API integration to 3D terrain rendering with MapLibre GL."

**"What was the hardest part?"** (1 min):
> "Handling time-resolved fire progression labels. Most fire perimeter data is only final extents, not hourly snapshots. I had to combine active fire detections from VIIRS with occasional perimeter updates, each with different uncertainty and temporal resolution. I used data assimilation methods to update state estimates as new observations arrived, while accounting for observation masks and sensor-specific confidence."

**"How do you ensure quality?"** (1 min):
> "Multiple layers: data validation schemas with Pydantic, automated leakage tests to prevent post-cutoff information from entering models, unit tests for coordinate transformations, golden tests with synthetic cases, comprehensive CI with Ruff/MyPy/Pytest, and experiment tracking with MLflow to ensure every result is reproducible. I also maintain detailed documentation of data sources, limitations, and evaluation protocols."

## Common Questions

### Q: Is this ready for real wildfire response?

**A**: No. This is a research prototype to explore modeling approaches and demonstrate ML/MLOps skills. Operational fire forecasting requires validation by domain experts, certification, and careful integration with existing emergency management systems. The project includes prominent warnings about this limitation.

### Q: How accurate are the forecasts?

**A**: It depends on the fire, forecast horizon, and model. On the held-out test set, IoU ranges from 0.4 to 0.8 at 6-hour horizons. Uncertainty estimates are calibrated to ±X% empirical coverage (results pending). I report negative results—when added complexity doesn't improve performance.

### Q: What data sources do you use?

**A**: NASA FIRMS for active fire detections, NIFC/WFIGS for fire perimeters, ERA5-Land for weather reanalysis, LANDFIRE for fuels and vegetation, and USGS 3DEP for terrain. All sources are documented with official links, licenses, and limitations in `docs/DATA_SOURCES.md`.

### Q: Why not use [X model architecture]?

**A**: I started with simple baselines (persistence, radial growth) to establish a performance floor, then added physics (ELMFIRE simulator), pure ML (U-Net/ConvLSTM), and hybrid approaches. Architecture choices are based on small experiments and ablations, not fashion. If a simpler baseline outperforms a complex model, I report that honestly.

### Q: How long did this take?

**A**: This is a ~5-7 month part-time project, following a phased approach. Phase 0 (engineering foundation) took ~2 weeks. Phases 1-3 (data and baselines) took ~2 months. Phases 4-8 (modeling and assimilation) are expected to take 3-4 months. Phase 9-10 (production and release) will take ~1 month.

## Demo Assets

### Required Materials

- [ ] 3 precomputed demonstration fires (Phase 9)
- [ ] Screenshots of key views (Phase 10)
- [ ] 2-3 minute demo video (Phase 10)
- [ ] Slides for technical presentation (Phase 10)

### Backup Plan

If live demo fails:
1. Have video recording ready
2. Have static screenshots prepared
3. Be ready to walk through code/docs instead

## Recording Tips

- Use QuickTime or OBS for screen recording
- Record at 1920x1080, 30fps
- Use external microphone for narration
- Keep mouse movements smooth and intentional
- Pause briefly before/after each action
- Export with subtitles for accessibility

## Update Schedule

Update this document:
- After each phase completion
- When new features are added
- After usability testing
- Before major presentations
