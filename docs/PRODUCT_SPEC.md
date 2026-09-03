# Product Specification

**Last Updated**: 2026-09-03  
**Version**: 0.1.0

> FireTwin must finish as a polished, usable web product, not as a collection of notebooks or command-line scripts. A visitor must be able to understand and operate the public demonstration without installing Python, opening a terminal, editing a configuration file, or knowing the internal data schema.

## Product Vision

FireTwin is a research-grade wildfire digital twin that enables researchers, students, and engineers to:

1. Explore historical wildfire events with rich geospatial context
2. Understand fire spread through physics-based and ML models
3. Evaluate forecast accuracy against later observations
4. Interpret uncertainty and model limitations
5. Experiment with hypothetical scenarios (what-if analysis)
6. Learn from simulated containment strategies

The product demonstrates the **complete data-to-deployment lifecycle** for ML/MLOps portfolio evaluation.

## Core User Journey

### 1. Discover
- User arrives at public URL
- Sees prominent research prototype warning
- Views curated demonstration fires on 3D terrain map
- Understands project scope and capabilities

### 2. Select
- Browse historical fire catalogue
- Filter by location, date, size, data completeness
- Select a fire and forecast reference time
- System loads precomputed case or validates compute budget

### 3. Observe
- View terrain, fuels, weather, and observations at forecast origin
- Inspect layers: elevation, slope, aspect, fuel types, active fire detections
- Understand initial conditions and data quality

### 4. Forecast
- Run or view forecasts: persistence, physics, ML, hybrid
- Choose forecast horizon: 3h, 6h, 12h, 24h
- Animate probabilistic spread over time
- Compare models side-by-side

### 5. Evaluate
- Compare forecast to later observations
- View metrics: IoU, precision, recall, calibration
- Inspect uncertainty and model disagreement
- Explore failure modes

### 6. Experiment
- Modify hypothetical inputs: wind, fuel moisture
- Draw simulated containment lines
- Compare no-action, heuristic, and optimized strategies
- Evaluate across weather/state ensembles

### 7. Understand
- Read concise briefing with provenance
- Export metrics and screenshots
- Access technical documentation
- Cite methods and data sources

## Mandatory Product Requirements

### No-Code Operation

- ✅ **No terminal required**: All workflows operate through the browser
- ✅ **No credentials required**: Public demo uses precomputed data
- ✅ **No data downloads**: Demonstration cases bundled with deployment
- ✅ **No configuration files**: All settings exposed through UI controls
- ✅ **Guided demo**: Prominent "Run guided demo" button for first-time users

### 3D Geospatial Experience

- ✅ **Real DEM-based terrain**: Using USGS 3DEP data, not decorative scenery
- ✅ **Pitch, bearing, zoom controls**: Smooth camera navigation
- ✅ **Terrain-aligned overlays**: Fire layers draped correctly over elevation
- ✅ **Hillshade and contours**: Optional layers for terrain interpretation
- ✅ **2D/3D toggle**: Switch between perspective and orthographic views
- ✅ **Scale and coordinates**: Clear spatial reference
- ✅ **Level-of-detail**: Smooth performance while animating

### Uncertainty and Provenance

- ✅ **Probabilistic forecasts**: Not just deterministic perimeters
- ✅ **Calibration plots**: Reliability diagrams, expected calibration error
- ✅ **Ensemble spread**: Model disagreement visualization
- ✅ **Observation quality**: Confidence, sensor, timing displayed
- ✅ **Run provenance**: Model version, data versions, cutoff time, commit SHA
- ✅ **Reproducibility**: Link visible result to experiment record

### Safety Language

Every public screen and report must display:

> **Research prototype. Not for operational wildfire response, evacuation planning, or safety-critical decision-making.**

All simulated intervention language must use "simulated", "hypothetical", or "what-if" framing.

## User Interface Structure

### Desktop Layout (Primary)

```
┌─────────────────────────────────────────────────────────────────┐
│ FireTwin  │  Case: [Fire Name]  │  Status  │  Help  │  Warning │
├─────────┬───────────────────────────────────────────────┬───────┤
│         │                                               │       │
│  LEFT   │              CENTER MAP (3D)                  │ RIGHT │
│  PANEL  │                                               │ PANEL │
│         │                                               │       │
│  Fire   │     Terrain + Forecast Layers                │ Met-  │
│  Select │                                               │ rics  │
│  Model  │                                               │       │
│  Layers │                                               │ Prov- │
│  Scen-  │                                               │ enance│
│  ario   │                                               │       │
├─────────┴───────────────────────────────────────────────┴───────┤
│         TIMELINE + ANIMATION CONTROLS + OBSERVATION MARKERS     │
└─────────────────────────────────────────────────────────────────┘
```

- **Top bar**: Project identity, case status, research warning, help
- **Left panel**: Fire catalogue, model selector, layer controls, scenario inputs
- **Center**: Largest area for 3D geospatial view
- **Right panel**: Metrics, uncertainty, cell inspection, provenance, briefing
- **Bottom**: Forecast timeline, play/pause, speed, horizon selectors

Panels are **collapsible** to maximize map area.

### Tablet Layout

- Responsive reflow with collapsible sidebars
- Single-column for settings, metrics below map
- Touch-friendly controls

### Mobile Layout

- Read-only or reduced-control experience
- Fire catalogue browsing
- View precomputed forecasts
- Informative, not broken

## Technology Stack

### Backend

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Server**: Uvicorn
- **Validation**: Pydantic schemas
- **Task Queue**: (TBD based on compute requirements)

### Frontend

- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Map Rendering**: MapLibre GL JS
- **3D Terrain**: MapLibre terrain-dem with USGS DEM tiles
- **Scientific Overlays**: deck.gl
- **Charts**: Plotly
- **State Management**: (TBD - Context API or lightweight state library)
- **Styling**: CSS Modules or Tailwind

### Data & Compute

- **Data Storage**: Zarr, Xarray, GeoParquet
- **Caching**: Redis or simple file-based for precomputed results
- **Compute**: Bounded background jobs with progress feedback

## Prepared Demonstration Cases

Minimum **3 curated fires**, geographically held-out, with:

1. **Case A**: California fire with good VIIRS coverage, moderate wind
2. **Case B**: Different state/terrain (e.g., Pacific Northwest steep terrain)
3. **Case C**: High-wind extreme fire

Each case includes:
- Precomputed physics, ML, hybrid, assimilated forecasts
- Later observations for comparison
- Reproducible manifest
- Data completeness note

## Visual Design Requirements

### Design Principles

- **Scientific command center**: Clear, restrained, information-dense
- **Excellent typography and spacing**: Readable legends, units, labels
- **Stable animations**: Time communicates progression, not decoration
- **Accessible**: Keyboard navigation, screen reader support, color-blind safe palettes

### Color Palettes

- **Fire probability**: Sequential scale (e.g., YlOrRd) with clear zero
- **Terrain**: Hillshade grayscale or subtle earth tones
- **Uncertainty**: Diverging scale or opacity-based
- **Observation confidence**: Green (high) → Yellow (medium) → Red (low)

Palettes must work over:
- Satellite base maps
- Dark and light backgrounds
- Common color-vision deficiencies

### Required UI States

- Initial loading
- Terrain/data streaming
- Job queued / running
- Partial results
- Success
- Stale data warning
- Invalid scenario input
- Network failure
- Empty selection

Never show blank map or unexplained spinner.

## Performance Budgets

| Metric | Target | Maximum |
|--------|--------|---------|
| Initial load | <3s | 5s |
| Map interaction FPS | 60fps | 30fps |
| Animation smoothness | 60fps | 30fps |
| API latency (cached) | <500ms | 1s |
| API latency (compute) | <30s | 60s |
| Browser memory | <500MB | 1GB |

Measure on representative MacBook Pro (2020+).

## Acceptance Criteria

Before calling the product complete:

1. ✅ A first-time visitor can complete the guided demo without instructions
2. ✅ No workflow requires code, terminal, credentials, or local data
3. ✅ Terrain uses real DEM with smooth 3D navigation
4. ✅ At least 3 prepared fires load reliably
5. ✅ Every layer has stable legend, units, timestamp, provenance
6. ✅ Scenario inputs are validated
7. ✅ Hypothetical actions are visibly labelled
8. ✅ All product states are understandable and tested
9. ✅ Usability tested with 5+ participants
10. ✅ Performance budgets met or exceptions documented

## Future Enhancements (Post-v1)

- Live/recent fire demonstration mode
- Mobile app (native or PWA)
- Multi-fire comparison view
- Advanced uncertainty quantification
- Optional LLM briefing assistant

Record additions in `DECISIONS.md`.
