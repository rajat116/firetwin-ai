# Data Source Validation

This document details the validation performed on all FireTwin data sources to ensure consistency, quality, and interoperability.

**Last Updated**: 2026-09-07

## Coordinate Reference Systems (CRS)

All data sources must be transformed to a common CRS for analysis. FireTwin uses:
- **Standard CRS**: WGS84 (EPSG:4326) for all geospatial data
- **Analysis CRS**: Local projected CRS (e.g., UTM) for distance calculations

### Source CRS Summary

| Data Source | Native CRS | Notes |
|------------|-----------|-------|
| **FIRMS** | WGS84 (EPSG:4326) | Point data (lat/lon) |
| **NIFC/WFIGS** | WGS84 (EPSG:4326) | GeoJSON polygons |
| **MTBS** | WGS84 (EPSG:4326) | GeoJSON polygons |
| **ERA5-Land** | WGS84 (EPSG:4326) | NetCDF with lat/lon coordinates |
| **LANDFIRE** | Albers Equal Area (ESRI:102039) | 30m GeoTIFF rasters |
| **USGS 3DEP** | Variable (typically UTM or NAD83) | GeoTIFF rasters with metadata |

**Validation Steps**:
1. Check CRS metadata in all downloaded files
2. Verify geometries are valid (no self-intersections, proper topology)
3. Transform all data to WGS84 for storage
4. Validate spatial extent overlaps with AOI

## Temporal Data Validation

### Timestamp Standards

All timestamps in FireTwin follow ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

| Data Source | Temporal Resolution | Timezone | Format |
|------------|-------------------|----------|--------|
| **FIRMS** | Individual detections | UTC | ISO 8601 datetime |
| **NIFC/WFIGS** | Daily updates | UTC | ISO 8601 date |
| **MTBS** | Fire year | Local | Year (YYYY) |
| **ERA5-Land** | Hourly | UTC | NetCDF time dimension |
| **LANDFIRE** | Static (version year) | N/A | Version string (e.g., "2.3.0") |
| **USGS 3DEP** | Static | N/A | Acquisition date in metadata |

**Validation Steps**:
1. Parse all timestamps to Python `datetime` objects
2. Convert all to UTC timezone
3. Check for temporal gaps and overlaps
4. Validate temporal ordering (start < end)

## Geometry Validation

### Point Data (FIRMS)

- Validate latitude range: [-90, 90]
- Validate longitude range: [-180, 180]
- Check for duplicate points (same location + timestamp)
- Confidence threshold filtering (>50%)

### Polygon Data (NIFC, MTBS)

- Validate polygon topology (no self-intersections)
- Check minimum area threshold (>1 hectare)
- Verify clockwise/counter-clockwise orientation
- Simplify geometries if necessary (Douglas-Peucker)
- Handle multi-polygon features

### Raster Data (ERA5, LANDFIRE, USGS)

- Validate pixel alignment and resolution
- Check for NoData values and masking
- Verify spatial extent matches metadata
- Confirm consistent grid spacing

## Unit Validation

### FIRMS (Active Fire Detections)

| Field | Unit | Range/Format |
|-------|------|-------------|
| `latitude` | degrees | [-90, 90] |
| `longitude` | degrees | [-180, 180] |
| `brightness` | Kelvin (K) | [0, 500] typical |
| `frp` | MW (Megawatts) | [0, 10000+] |
| `confidence` | percentage | [0, 100] |

### ERA5-Land (Weather)

| Variable | Unit | Conversion Notes |
|----------|------|------------------|
| `2m_temperature` | Kelvin (K) | Convert to Celsius: T(°C) = T(K) - 273.15 |
| `10m_u_component_of_wind` | m/s | No conversion needed |
| `10m_v_component_of_wind` | m/s | No conversion needed |
| `total_precipitation` | meters | Convert to mm: P(mm) = P(m) × 1000 |
| `surface_pressure` | Pascals (Pa) | Convert to hPa: P(hPa) = P(Pa) / 100 |

### LANDFIRE (Fuels)

| Product | Unit | Value Range |
|---------|------|-------------|
| FBFM40 | categorical | [0, 40] fuel model codes |
| Canopy Cover | percent | [0, 100] |
| Canopy Height | meters × 10 | Divide by 10 for actual meters |
| Canopy Bulk Density | kg/m³ × 100 | Divide by 100 for actual kg/m³ |

### USGS 3DEP (Elevation)

| Variable | Unit | NoData Value |
|----------|------|--------------|
| Elevation | meters | -9999 or NaN |
| Slope | degrees | [0, 90] |
| Aspect | degrees | [0, 360] (0 = North) |

## Data Quality Checks

### Completeness

- **Spatial Coverage**: Check for gaps in raster data
- **Temporal Coverage**: Identify missing time steps
- **Attribute Completeness**: No null/missing required fields

### Accuracy

- **Positional Accuracy**: Compare overlapping datasets (e.g., FIRMS vs NIFC)
- **Temporal Accuracy**: Cross-reference fire dates across sources
- **Attribute Accuracy**: Validate field ranges and distributions

### Consistency

- **Cross-Source Validation**: Fire detections should align with perimeters
- **Temporal Consistency**: Weather data should match fire dates
- **Spatial Consistency**: Terrain should match known topography

## Validation Workflow

```python
from firetwin.data.clients import (
    FIRMSClient,
    NIFCClient,
    MTBSClient,
    ERA5LandClient,
    USGS3DEPClient,
)
import geopandas as gpd

# 1. Validate CRS
def validate_crs(gdf: gpd.GeoDataFrame) -> bool:
    """Ensure GeoDataFrame has valid CRS."""
    if gdf.crs is None:
        raise ValueError("No CRS defined")
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return True

# 2. Validate geometries
def validate_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Check and fix invalid geometries."""
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid].buffer(0)
    return gdf

# 3. Validate temporal range
def validate_temporal_range(start, end):
    """Ensure temporal ordering."""
    if start >= end:
        raise ValueError("Start date must be before end date")
    return True
```

## Known Issues and Limitations

### FIRMS
- **Coverage**: Only detects active burning, not full perimeter
- **Temporal Resolution**: 1-2 passes per day (depends on satellite)
- **False Positives**: Industrial sites, gas flares can trigger detections
- **Minimum Fire Size**: ~100m² for VIIRS, ~1000m² for MODIS

### NIFC/WFIGS
- **Update Frequency**: Daily, but may lag 24-48 hours
- **Coverage**: US only (federal and state lands)
- **Accuracy**: Hand-digitized, variable precision (±50-100m)
- **Completeness**: Small fires (<300 acres) may not be mapped

### MTBS
- **Temporal Lag**: 1-2 years after fire season
- **Coverage**: US only, fires >1000 acres (West) or >500 acres (East)
- **Burn Severity**: Derived from Landsat, 30m resolution
- **Quality**: Cloud cover can affect accuracy

### ERA5-Land
- **Spatial Resolution**: 9km grid (coarse for local fire modeling)
- **Temporal Resolution**: Hourly (historical), 5-day lag (near-real-time)
- **Variables**: Limited atmospheric profile (surface only)
- **Accuracy**: Reanalysis (model + observations), not ground truth

### LANDFIRE
- **Update Cycle**: Every 2-3 years (not real-time)
- **Coverage**: US only
- **Accuracy**: Derived from satellite imagery, 30m resolution
- **Consistency**: Version changes can introduce discontinuities

### USGS 3DEP
- **Coverage**: Variable resolution (1m lidar in some areas, 30m elsewhere)
- **Temporal Currency**: Updates vary by region (5-10 year cycles)
- **Vertical Accuracy**: ±0.5m (lidar) to ±3m (photogrammetry)
- **Artifacts**: Seam lines, data voids in steep terrain

## Recommended Best Practices

1. **Always validate CRS** before spatial operations
2. **Buffer geometries** by uncertainty when intersecting sources
3. **Use confidence thresholds** for FIRMS detections (>80% recommended)
4. **Cross-reference sources** to identify high-quality fire cases
5. **Document data versions** and acquisition dates in metadata
6. **Apply temporal buffers** (±1 day) when matching sources
7. **Quality flag bad data** rather than discarding (preserves provenance)

## Validation Test Suite

See `tests/integration/test_data_validation.py` for automated validation tests across all data sources.
