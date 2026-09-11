# FireTwin Data Strategy

**Last Updated**: 2026-09-10
**Status**: Data clients implemented; progression labels still under audit

## Overview

This document outlines the comprehensive data strategy for FireTwin, addressing the limitations discovered during Phase 3 and providing production-ready solutions for accessing historical wildfire data.

## Data Sources Summary

| Source | Type | Coverage | Best Use Case | Status |
|--------|------|----------|---------------|--------|
| **NIFC Historical** | Perimeters | 2000-2021+ | Historical fire perimeters | ✅ Implemented |
| **NIFC Current** | Perimeters | Active fires only | Real-time monitoring | ✅ Implemented |
| **MTBS** | Perimeters + Severity | 1984-2020 (2-3yr lag) | Final validated perimeters | ✅ Implemented |
| **FIRMS** | Active Fire Points | 2000-present | Fire progression/hotspots | ✅ Implemented |
| **ERA5-Land** | Weather | 1950-present | Meteorological data | ✅ Implemented |
| **USGS 3DEP** | Elevation | Current | Terrain data | ✅ Implemented |
| **LANDFIRE** | Fuels/Vegetation | Current | Fuel models | ✅ Implemented |

## Addressing Key Limitations

### 1. NIFC Current Perimeters Limitation

**Problem**: NIFC "Current Perimeters" only contains active fires, not historical data.

**Solution**: ✅ **SOLVED** - Implemented `NIFCHistoricalClient`

```python
from firetwin.data.clients import NIFCHistoricalClient

# Access historical perimeters (2000-2021+)
client = NIFCHistoricalClient()
fires_2014 = client.get_fires_by_year(2014, min_acres=50000)

# Result: 11 large fires including Carlton Complex (251,965 acres)
```

**Benefits**:
- Access to 20+ years of historical fire perimeters
- Multi-agency data (USFS, BLM, NPS, CALFIRE, etc.)
- Temporal progression for large fires
- IRWIN IDs for cross-referencing

### 2. MTBS Data Lag (2-3 Years)

**Problem**: MTBS processes fires 2-3 years after containment, so recent fires unavailable.

**Solution**: ✅ **Accepted as Feature, Not Bug**

**Rationale**:
- **For Portfolio/Research**: 2014-2020 data is **better** - fully validated, complete
- **For Production**: Hybrid approach (see below)

**Hybrid Strategy**:
```python
def get_fire_data(fire_id: str, year: int):
    if year < current_year - 2:
        # Use MTBS for complete, validated data with burn severity
        return mtbs_client.get_fire(fire_id)
    else:
        # Use NIFC Historical + FIRMS for recent fires
        perimeters = nifc_hist_client.get_fire_by_name(fire_id, year)
        hotspots = firms_client.get_detections(...)
        return combine_sources(perimeters, hotspots)
```

### 3. MTBS Temporal Query Limitation

**Problem**: MTBS API doesn't support timestamp range queries.

**Solution**: ✅ **Solved with Spatial Filtering**

- Made `bbox` parameter required
- Prevents hitting 2000-record ESRI API limit
- Filters by year in Python after fetch
- **Design Decision**: Wildfire data is inherently spatial - requiring bbox is good practice

### 4. Fire Progression Data Gap

**Problem**: Need time-resolved fire spread for modeling.

**Status**: 🔎 **Under Audit Before Reconstruction**

```python
# Approach 1: NIFC Historical (when available)
# - Multiple perimeters for same fire at different dates
perimeters = nifc_hist_client.get_fire_by_name("Carlton Complex", 2014)
# May return multiple timestamps, but current 2014 pilots only have one each

# Approach 2: FIRMS Active Fire Detections
# - Daily hotspots can support irregular hotspot/progression labels after filtering
firms_detections = firms_client.get_area_detections(
    bbox=fire_bbox,
    start_date=fire_start,
    end_date=fire_end
)
# Cluster detections by date to infer uncertain progression observations
```

Phase 4E audit results show the current 2014 pilot fires have only one matching NIFC perimeter
timestamp each. That is not enough for hourly perimeter labels. FIRMS historical detections are
available for all three pilots and can support irregular hotspot/progression targets after sensor,
confidence, FRP and spatial filtering.

The first FireTwin progression artifacts are daily-binned FIRMS hotspot/progression Zarr products
under `data/labels/`. They store positive active-fire evidence, cumulative detection probability and
FRP summaries on the same grid as the final-extent FireCase. Non-detection is explicitly treated as
missing/unobserved, not unburned.

## Recommended Data Pipeline

### For Historical Case Building (2000-2020)

```python
def build_historical_fire_case(fire_name: str, year: int, bbox: tuple):
    # 1. Get final validated perimeter from MTBS
    mtbs_fire = mtbs_client.get_fire_by_name(fire_name, year)
    
    # 2. Get historical progression from NIFC
    nifc_perimeters = nifc_hist_client.get_fire_by_name(fire_name, year)
    
    # 3. Get daily hotspots from FIRMS (if needed)
    firms_detections = firms_client.get_area_detections(
        bbox=bbox,
        start_date=fire_start,
        end_date=fire_end
    )
    
    # 4. Get weather data from ERA5
    weather = era5_client.download_area(bbox, fire_start, fire_end)
    
    # 5. Get terrain from USGS 3DEP
    elevation = usgs_client.download_bbox(bbox)
    
    # 6. Get fuels from LANDFIRE
    fuels = landfire_client.build_fuel_data(grid_bounds, grid_shape, target_crs, resolution_m, output_dir)
    
    return FireCase(
        perimeter=mtbs_fire,
        progression=reconstruct_from_sources(nifc_perimeters, firms_detections),
        weather=weather,
        terrain=elevation,
        fuels=fuels
    )
```

### For Recent Fires (2021+)

```python
def build_recent_fire_case(fire_name: str, bbox: tuple):
    # 1. Get perimeters from NIFC Historical
    nifc_perimeters = nifc_hist_client.get_fire_by_name(fire_name)
    
    # 2. Supplement with NIFC Current if still active
    current_perimeters = nifc_client.get_fire_by_name(fire_name)
    
    # 3. Get daily hotspots from FIRMS
    firms_detections = firms_client.get_area_detections(...)
    
    # ... rest same as historical
```

## Data Quality Validation

### Checklist for Each Fire Case

- [ ] Perimeter data available (MTBS or NIFC Historical)
- [ ] Fire progression data (NIFC multiple dates or FIRMS)
- [ ] Weather data coverage (ERA5-Land for bbox/dates)
- [ ] Terrain data available (USGS 3DEP for bbox)
- [ ] Fuel data available (LANDFIRE for bbox)
- [ ] Temporal alignment (all data covers fire duration)
- [ ] Spatial alignment (all data covers fire bbox)
- [ ] CRS consistency (all data in WGS84/EPSG:4326)

### Known Data Gaps

| Issue | Affected Years | Workaround |
|-------|----------------|------------|
| NIFC Historical incomplete | Varies | Use MTBS as fallback |
| MTBS burn severity delay | Recent fires | Accept or use proxy |
| FIRMS requires API key | All | User must provide key |
| LANDFIRE canopy/vegetation products not integrated | All | FBFM40 fuel model is automated; add other products when needed |

## Production Deployment Considerations

### 1. API Rate Limiting

- **ESRI Services (NIFC, MTBS)**: 2000 records/query max
- **FIRMS**: 5-day Area API window limit, requires MAP_KEY
- **ERA5 CDS**: Account required, queue system

### 2. Data Caching Strategy

```python
# Cache MTBS/NIFC data (changes infrequently)
cache_duration = {
    "mtbs": "permanent",  # Historical data doesn't change
    "nifc_historical": "1 week",  # Updated occasionally
    "nifc_current": "5 minutes",  # Near real-time
    "firms": "1 hour",  # Daily updates
}
```

### 3. Fallback Chain

```
Primary: NIFC Historical
    ↓ (if unavailable)
Fallback 1: MTBS
    ↓ (if unavailable)
Fallback 2: FIRMS reconstruction
    ↓ (if unavailable)
Error: Insufficient data
```

## Validation Results

### NIFC Historical Testing (2014 Data)

```
✅ Found 11 large fires (>50k acres)
✅ Carlton Complex: 251,965 acres
⚠️ Current pilot-fire audit found only one matching NIFC perimeter timestamp per 2014 pilot
✅ Agency attribution working
✅ Date parsing functional
✅ GeoDataFrame conversion successful
```

### MTBS Testing (2014 Data)

```
✅ Found 12 large fires (>50k acres)
✅ Year extraction from fire_id working
✅ Spatial filtering via bbox working
✅ Python-side year filtering effective
```

## Conclusion

**All major data clients are implemented, but progression-label construction is not solved yet.**

The FireTwin project now has:
- ✅ Access to 20+ years of historical fire perimeters
- ✅ Multiple data sources for validation/cross-referencing
- ✅ Strategies for recent vs. historical fires
- 🔎 A Phase 4E audit gate before progression labels or ML forecast training
- ✅ Validated clients for all 6 core data sources

**Status**: Phase 3 historical case building, Phase 4A terrain enrichment, Phase 4B LANDFIRE
FBFM40 fuel-model enrichment, Phase 4C ERA5-Land weather enrichment and Phase 4D final-extent
diagnostics are complete. Phase 4E now has daily-binned FIRMS progression label artifacts and is
moving to initial-state reconstruction.
