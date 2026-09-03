# Data Directory

This directory contains FireTwin's geospatial and temporal data at different processing stages.

## Structure

- `raw/` - Immutable raw downloads from data sources (never committed to git)
- `interim/` - Intermediate processing steps and geospatial transformations
- `processed/` - Canonical analysis-ready datasets in Zarr/Xarray format
- `manifests/` - Dataset manifests, metadata, and version information (committed to git)

## Storage

Large data files are excluded from version control via `.gitignore`. 

Use DVC (Data Version Control) for tracking large datasets when needed.

## Data Sources

See `docs/DATA_SOURCES.md` for complete information about data providers, licenses, and access methods.
