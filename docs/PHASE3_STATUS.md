# Phase 3 Status - Historical Fire Case Builder

**Last Updated**: 2026-09-08
**Status**: COMPLETE ✅ - Final-extent pilot cases built and validated with explicit limitations

**Scientific Scope**: These cases are valid final-burned-extent artifacts. They are not yet
time-resolved fire-progression labels and are not forecast-ready real-data samples.

## Completed ✅

### 1. RealFireCaseConverter Implementation
   - ✅ Multi-source data fetching (NIFC Historical, MTBS)
   - ✅ **Bbox filtering** to prevent multiple fires with similar names
   - ✅ **Smart buffer calculation** (10% of fire size, max 5km)
   - ✅ Spatial alignment and CRS reprojection
   - ✅ Target CRS preserved in FireCase bbox metadata
   - ✅ Fire perimeter rasterization
   - ✅ FireCase construction with canonical schemas
   - ✅ Final-extent and placeholder-covariate limitations stored in metadata
   - ✅ Zarr format export with compression

### 2. All 3 Pilot Fires Generated & Validated

| Fire | Grid Size | Burned Pixels | Efficiency | Burned Area | Accuracy |
|------|-----------|---------------|------------|-------------|----------|
| Carlton Complex | 662×493 (326k) | 111k (34.2%) | Excellent | 275k acres | 9.3% error ✅ |
| King Fire | 462×312 (144k) | 40k (27.5%) | Excellent | 98k acres | 0.2% error ✅ |
| Big Cougar | 349×239 (83k) | 26k (31.7%) | Excellent | 65k acres | 0.0% error ✅ |

**All grids have 27-34% burn efficiency** - much better than the broken version!

### 3. Bugs Fixed
   - ✅ **King fire bbox filtering**: Was returning 7 fires across the US, now filters to California fire only
   - ✅ **Smart buffer calculation**: Changed from "10% of max dimension" to "10% of fire dimension, max 5km"
   - ✅ **Big Cougar bbox corrected**: Updated bbox to match actual fire location
   - ✅ **Big Cougar CRS metadata**: FireCase bbox now records EPSG:32611 when requested instead of hard-coded EPSG:32610
   - ✅ **Validation script storage layout**: Validator now reads the actual `burned(time, y, x)` Zarr layout
   - ✅ **Grid efficiency**: All fires now have reasonable grid sizes (~30% burned vs 0.01%)

## Critical Findings 🔍

### NIFC API Limitation
**Issue**: NIFC "Current Perimeters" service only contains ACTIVE fires
- Service: `WFIGS_Interagency_Perimeters_Current`
- Contains recent/ongoing fires only
- Historical fires (like Creek 2020) NOT available
- **Impact**: Cannot use NIFC for historical fire progression data

**Solution Options**:
1. Use NIFC historical archive (separate service, needs investigation)
2. Rely on MTBS for historical perimeters (final only, no progression)
3. Use FIRMS detections to infer progression (lower quality)

### MTBS API Field Names
**Issue**: Actual field names don't match initial implementation
- Fields are lowercase: `fire_name` not `Fire_Name`
- No direct `Fire_Year` field
- Year embedded in `fire_id` (last 8 digits: YYYYMMDD)
- `ig_date` is Unix timestamp (milliseconds)

**Status**: Corrections identified, implementation pending

### Data Availability for Test Cases
**Creek Fire 2020**:
- NIFC Current: ❌ Not available (too old)
- MTBS: ⚠️ Need to test with corrected client
- FIRMS: ⚠️ Requires API key (not tested)

## Known Limitations

1. **Placeholder Data**
   - ⚠️ Terrain: Using flat 1000m elevation (real USGS 3DEP integration pending)
   - ⚠️ Fuels: Using uniform FBFM 10 (real LANDFIRE integration pending)
   - ⚠️ Weather: Using moderate conditions (real ERA5 integration pending)

2. **Static Perimeters Only**
   - Fire progression data not yet implemented
   - Only final perimeter captured (no time-resolved evolution)
   - Temporal alignment deferred to future phase
   - Final extent must not be used as hourly forecast labels

3. **Data Source Coverage**
   - NIFC Historical: ✅ Working for 2014 fires
   - MTBS: ⚠️ Limited data for Carlton Complex
   - FIRMS: ❌ Requires API key
   - ERA5: ❌ Requires CDS credentials
   - USGS/LANDFIRE: ❌ Not yet integrated

## Next Steps (Phase 4+)

1. **Phase 4: Real Data Enrichment**
   - Integrate USGS 3DEP for real terrain
   - Integrate LANDFIRE for real fuels
   - Integrate ERA5-Land for real weather
   - Add FIRMS active fire detections

2. **Phase 4: Real-Data Baselines**
   - Run baseline models on real fire cases
   - Evaluate forecast accuracy against real outcomes
   - Compare to synthetic case performance

3. **Future Phases**
   - Time-resolved fire progression (multiple perimeters)
   - Data assimilation with observations
   - Hybrid physics-ML models

## Lessons Learned

1. **NIFC Historical Archive is gold** - Discovered separate historical archive (2000-2021+) with progression data
2. **2014 fires are ideal** - Complete MTBS data, NIFC historical perimeters, geographic diversity
3. **Start simple, iterate** - Built with placeholder terrain/fuels/weather, can enrich later
4. **Real perimeters work** - Successfully rasterized real fire polygons to 100m grid
5. **Zarr format is excellent** - Fast saves, efficient storage, good compression

## Final Implementation

**Core Pipeline**:
```
RealFireCaseConverter
  └─ fetch_all_data()     → NIFC Historical, MTBS
  └─ align_layers()       → CRS, grid, rasterization  
  └─ build_fire_case()    → TerrainData, FuelData, WeatherData, FireState
  └─ save_fire_case()     → Zarr export
```

**Output**:
- 3 canonical FireCase objects in `data/fire_cases/`
- Each with real fire perimeter rasterized to 100m grid
- Geographic diversity: Washington, California, Oregon/Idaho
- Scale diversity: 65k - 252k acres
- Ready for final-extent validation; not yet ready for hourly real-data forecast evaluation

## Phase 3 Exit Gate

Completed before Phase 4:

- ✅ Regenerated the three local pilot Zarr artifacts after the metadata/CRS fixes.
- ✅ Ran `scripts/validate_fire_cases.py` successfully with the project Python environment.
- ✅ Ran unit tests, lint/format checks, and type checks.
- ✅ Documented that Phase 4 baseline code must respect `target_type=final_burned_extent`.
