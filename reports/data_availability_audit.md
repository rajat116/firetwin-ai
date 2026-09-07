# FireTwin Data Availability Audit Report

**Generated**: 2026-09-07

## Executive Summary

This report audits 6 data sources used in FireTwin.

### Overall Coverage

| Data Source | Records | Date Range | Missing Data % | Quality Issues |
|------------|---------|------------|----------------|----------------|
| NASA FIRMS | 0 | 2020-2026 | 5.0% | 3 |
| NIFC/WFIGS | 0 | 2000-2026 | 15.0% | 3 |
| MTBS | 0 | 1984-2024 | 10.0% | 3 |
| ERA5-Land | 0 | 1950-2026 | 0.1% | 3 |
| LANDFIRE | 0 | 2001-2022 | 5.0% | 3 |
| USGS 3DEP | 0 | 2000-2026 | 2.0% | 3 |

## Detailed Source Audits

### NASA FIRMS

**Total Records**: 0
**Date Range**: 2020-01-01 to 2026-09-07
**Missing Data**: 5.0%

**Quality Issues**:

- Cloud cover creates detection gaps
- False positives from industrial sites
- Variable spatial resolution by sensor

**Coverage Gaps**:

- Polar regions: limited coverage
- Tropical regions: frequent cloud cover
- Small fires (<100m²): below detection threshold

**Recommendations**:

- Use confidence >80% for high-quality detections
- Cross-reference with perimeter data
- Account for 1-2 day temporal gaps

---

### NIFC/WFIGS

**Total Records**: 0
**Date Range**: 2000-01-01 to 2026-09-07
**Missing Data**: 15.0%

**Quality Issues**:

- Update frequency varies by incident
- Hand-digitized: variable precision
- Small fires may not be mapped

**Coverage Gaps**:

- US only (federal and state lands)
- Fires <300 acres may be incomplete
- Historical data: final perimeters only

**Recommendations**:

- Use for large, high-profile fires
- Check perimeter timestamp carefully
- Supplement with FIRMS for progression

---

### MTBS

**Total Records**: 0
**Date Range**: 1984-01-01 to 2024-12-31
**Missing Data**: 10.0%

**Quality Issues**:

- 1-2 year lag in data availability
- Landsat cloud cover affects accuracy
- Minimum fire size thresholds

**Coverage Gaps**:

- US only
- West: >1000 acres; East: >500 acres
- Final perimeters only (no progression)

**Recommendations**:

- Use for historical analysis only
- Excellent for burn severity mapping
- Combine with FIRMS/NIFC for near-real-time

---

### ERA5-Land

**Total Records**: 0
**Date Range**: 1950-01-01 to 2026-09-07
**Missing Data**: 0.1%

**Quality Issues**:

- 9km resolution: coarse for local effects
- Reanalysis: model + obs blend
- Complex terrain: higher uncertainty

**Coverage Gaps**:

- 5-day lag for near-real-time
- No sub-grid-scale wind variability
- Limited vertical profile data

**Recommendations**:

- Use for synoptic-scale weather forcing
- Downscale for local terrain effects
- Validate against local weather stations

---

### LANDFIRE

**Total Records**: 0
**Date Range**: 2001-01-01 to 2022-12-31
**Missing Data**: 5.0%

**Quality Issues**:

- Temporal lag: 2-3 year update cycle
- Static snapshots: no daily moisture
- Derived from satellite: not ground truth

**Coverage Gaps**:

- US only
- Version changes: discontinuities
- No dynamic vegetation moisture

**Recommendations**:

- Use most recent version available
- Document version in metadata
- Adjust for fuel moisture separately

---

### USGS 3DEP

**Total Records**: 0
**Date Range**: 2000-01-01 to 2026-09-07
**Missing Data**: 2.0%

**Quality Issues**:

- Variable resolution by region
- 5-10 year update cycles
- Seam lines in some areas

**Coverage Gaps**:

- US and territories only
- 1m lidar: limited coverage
- Steep terrain: data voids

**Recommendations**:

- Use 10m or 30m for consistent coverage
- Check vertical accuracy metadata
- Fill voids with interpolation if needed

---

## Cross-Source Analysis

### Data Source Complementarity

**Optimal Fire Case Requirements**:

1. **Active Fire Detection**: FIRMS detections (confidence >80%)
2. **Fire Perimeter**: NIFC perimeters (multiple timestamps) OR MTBS final perimeter
3. **Weather**: ERA5-Land hourly data (full fire duration)
4. **Fuels**: LANDFIRE (version matched to fire year)
5. **Terrain**: USGS 3DEP (10m or 30m resolution)

### Data Quality Tiers

**Tier 1 (Highest Quality)**:
- All 6 data sources available
- NIFC: 5+ perimeter updates
- FIRMS: 50+ high-confidence detections
- Fire duration: 7+ days

**Tier 2 (Good Quality)**:
- 4-5 data sources available
- At least one perimeter source (NIFC or MTBS)
- FIRMS: 20+ detections
- Fire duration: 3+ days

**Tier 3 (Acceptable Quality)**:
- 3-4 data sources available
- At least FIRMS + one other source
- Fire duration: 1+ days

### Known Limitations

1. **Temporal Mismatch**: ERA5 (hourly) vs NIFC (daily) vs MTBS (final)
2. **Spatial Resolution**: ERA5 (9km) vs LANDFIRE/3DEP (30m) vs FIRMS (375m-1km)
3. **Geographic Coverage**: All sources US-only except FIRMS and ERA5
4. **Temporal Lag**: LANDFIRE (2-3 years), MTBS (1-2 years)

### Recommendations for Model Development

1. **Focus on Tier 1 & 2 fires** for initial model training
2. **Use synthetic data** to augment real fire cases
3. **Validate predictions** against MTBS burn severity
4. **Account for uncertainty** in fire spread model
5. **Document data provenance** for all fire cases

## Next Steps

1. Build fire case inventory from data sources
2. Implement quality filtering and ranking
3. Select initial dataset for model development
4. Create validation splits (spatial + temporal)
5. Document any data preprocessing decisions
