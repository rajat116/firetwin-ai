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

The committed `manifests/firms_next_day_explorer_manifest.json` file is intentionally lightweight.
It points to committed preview figures and ignored local learned-forecast Zarr artifacts so a future
Explorer UI can load demo metadata without committing large arrays.

## Data Sources

See `docs/DATA_SOURCES.md` for complete information about data providers, licenses, and access methods.
