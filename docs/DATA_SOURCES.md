# Data Sources

This document maintains a verified registry of all data sources used in FireTwin.

**Last Updated**: 2026-09-03

## Data Source Registry

### NASA FIRMS - Active Fire Observations

**Provider**: NASA Fire Information for Resource Management System  
**Products**: MODIS and VIIRS active fire/thermal anomaly detections  
**Official Links**:
- API Documentation: https://firms.modaps.eosdis.nasa.gov/api/
- Active Fire Downloads: https://firms.modaps.eosdis.nasa.gov/active_fire/
- Web Services: https://firms.modaps.eosdis.nasa.gov/web-services/

**Access Method**: REST API with MAP_KEY  
**Registration**: Free at https://firms.modaps.eosdis.nasa.gov/api/  
**Spatial Resolution**: MODIS ~1km, VIIRS ~375m nominal  
**Temporal Resolution**: Near real-time, multiple passes per day  
**License/Terms**: [NASA data policy](https://earthdata.nasa.gov/earth-observation-data/data-use-policy)

**Variables Used**:
- Detection coordinates (latitude, longitude)
- Acquisition date/time
- Sensor (MODIS/VIIRS)
- Confidence level
- Brightness temperature
- Fire radiative power (FRP)
- Day/night indicator

**Known Limitations**:
- Cloud, smoke, and orbit timing create gaps
- Detection points are not exact fire perimeters
- Non-detection does not prove absence of fire
- Resolution varies by sensor and viewing geometry

**Citation**: NASA FIRMS. (2026). Fire Information for Resource Management System. Retrieved from https://firms.modaps.eosdis.nasa.gov/

---

### NIFC/WFIGS - Fire Perimeters

**Provider**: National Interagency Fire Center / Wildland Fire Interagency Geospatial Services  
**Official Links**:
- Portal: https://data-nifc.opendata.arcgis.com/
- WFIGS Page: https://data-nifc.opendata.arcgis.com/pages/wfigs-page
- Current Perimeters: https://data-nifc.opendata.arcgis.com/datasets/nifc::wfigs-current-interagency-fire-perimeters/
- Historical Catalogue: https://data-nifc.opendata.arcgis.com/search?tags=Category%2Chistoric_wildlandfire_opendata

**Access Method**: ArcGIS REST API / GeoJSON downloads  
**Spatial Resolution**: Varies by mapping method  
**Temporal Resolution**: Variable update frequency per incident  
**License/Terms**: Public domain (U.S. government work)

**Variables Used**:
- Fire perimeter geometry (polygon)
- Incident identifier
- Fire name
- Perimeter timestamp
- Modified timestamp
- Acres
- Containment percentage

**Known Limitations**:
- Coverage and update frequency differ by incident
- Historical archives may contain only final perimeter, not progression
- Timestamp interpretation requires care (may not represent exact fire extent at that time)

**Citation**: NIFC. (2026). Wildland Fire Interagency Geospatial Services. Retrieved from https://data-nifc.opendata.arcgis.com/

---

### MTBS - Burn Severity

**Provider**: Monitoring Trends in Burn Severity (USGS/USFS)  
**Official Links**:
- Homepage: https://www.mtbs.gov/
- Direct Download: https://www.mtbs.gov/direct-download
- Burn Severity Portal: https://burnseverity.cr.usgs.gov/direct-download

**Access Method**: FTP/HTTPS download  
**Spatial Resolution**: 30m  
**Temporal Coverage**: 1984-present (annual updates)  
**License/Terms**: Public domain (U.S. government work)

**Variables Used**:
- Fire perimeter (final)
- Burn severity classification (dNBR-based)
- Ignition date
- Fire type

**Known Limitations**:
- Final perimeters only, not suitable for hourly progression modeling
- Annual update cycle, not near-real-time
- Minimum fire size thresholds (varies by region)

**Citation**: MTBS. (2026). Monitoring Trends in Burn Severity. Retrieved from https://www.mtbs.gov/

---

### ERA5-Land - Weather Reanalysis

**Provider**: Copernicus Climate Data Store (ECMWF)  
**Official Links**:
- Dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- CDS Portal: https://cds.climate.copernicus.eu/

**Access Method**: `cdsapi` Python package  
**Registration**: Free at https://cds.climate.copernicus.eu/  
**Spatial Resolution**: ~9km  
**Temporal Resolution**: Hourly  
**License/Terms**: [Copernicus license](https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf)

**Variables Used**:
- 10m u- and v-components of wind
- 2m temperature
- 2m dewpoint temperature
- Total precipitation
- Surface pressure
- Soil moisture (multiple layers)
- Surface solar radiation

**Known Limitations**:
- Coarser than 30m terrain/fuel data (resampling does not create fine-scale weather)
- Reanalysis, not real-time forecasts
- Uncertainty in complex terrain

**Citation**: Muñoz Sabater, J. (2021). ERA5-Land hourly data from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS).

---

### LANDFIRE - Fuels and Vegetation

**Provider**: LANDFIRE (USGS/USFS)  
**Official Links**:
- Homepage: https://www.landfire.gov/
- Data: https://www.landfire.gov/data
- Fuel Vegetation Type: https://www.landfire.gov/fuel/fvt

**Access Method**: Area-of-interest download / REST services  
**Spatial Resolution**: 30m  
**Temporal Coverage**: Periodic updates (check version)  
**License/Terms**: Public domain (U.S. government work)

**Variables Used**:
- Fire Behavior Fuel Model (FBFM)
- Existing Vegetation Type (EVT)
- Existing Vegetation Cover (EVC)
- Existing Vegetation Height (EVH)
- Canopy cover, height, base height, bulk density
- Disturbance layers

**Known Limitations**:
- May not represent conditions at fire date (temporal lag)
- Product version and year must be recorded
- Static snapshots, not daily vegetation moisture

**Citation**: LANDFIRE. (2026). LANDFIRE Product Data. Retrieved from https://www.landfire.gov/

---

### USGS 3DEP - Terrain Elevation

**Provider**: U.S. Geological Survey 3D Elevation Program  
**Official Links**:
- Homepage: https://www.usgs.gov/3d-elevation-program
- Data Download: https://www.usgs.gov/the-national-map-data-delivery/gis-data-download

**Access Method**: The National Map download / API  
**Spatial Resolution**: 10m, 30m (resolution varies by area)  
**License/Terms**: Public domain (U.S. government work)

**Derived Variables**:
- Elevation
- Slope
- Aspect

**Known Limitations**:
- Select resolution consistent with model grid and computational budget
- Very high resolution (1m) may not be justified given coarser weather/fuel inputs

**Citation**: USGS. (2026). USGS 3D Elevation Program. Retrieved from https://www.usgs.gov/3d-elevation-program

---

## Data Attribution Requirements

When using FireTwin data or derivatives:

1. **NASA FIRMS**: Acknowledge NASA/LANCE/EOSDIS
2. **NIFC/WFIGS**: Acknowledge National Interagency Fire Center
3. **MTBS**: Acknowledge USGS/USFS MTBS program
4. **ERA5-Land**: Cite Copernicus Climate Data Store and dataset DOI
5. **LANDFIRE**: Acknowledge LANDFIRE program
6. **USGS 3DEP**: Acknowledge USGS 3D Elevation Program

## Data Access Setup

### Required API Keys

Store in `.env` (never commit):

```bash
# NASA FIRMS
FIRMS_MAP_KEY=your_key_here

# Copernicus CDS
CDS_API_URL=https://cds.climate.copernicus.eu/api/v2
CDS_API_KEY=your_uid:your_api_key
```

### Data Directory Structure

```
data/
├── raw/              # Immutable downloads
│   ├── firms/
│   ├── nifc/
│   ├── mtbs/
│   ├── era5/
│   ├── landfire/
│   └── 3dep/
├── interim/          # Processing intermediates
├── processed/        # Canonical Zarr/Xarray datasets
└── manifests/        # Metadata and version tracking
```

## Data Quality and Validation

Each data client must:
- Validate CRS and reproject if needed
- Verify timestamps and time zones
- Check for missing values and document handling
- Record exact product version and access date
- Compute checksums where practical

See `src/firetwin/data/validation/` for validation schemas.

## Future Data Sources (Not Yet Implemented)

- Sentinel-2 / Landsat imagery
- NOAA/NWS high-resolution forecasts
- National Fuel Moisture Database
- OpenStreetMap (roads, buildings, water)
- InciWeb incident reports

Add these only after explicit decision record in `DECISIONS.md`.
