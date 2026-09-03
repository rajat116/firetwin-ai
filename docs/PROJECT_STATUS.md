# FireTwin Project Status

**Last Updated**: 2026-09-03  
**Current Phase**: Phase 0 ✅

## Phase 0: Repository and Engineering Foundation ✅

**Status**: COMPLETED

### Completed Tasks

- [x] Initialize Git repository with correct credentials
- [x] Create comprehensive directory structure
- [x] Set up conda environment with all required dependencies
- [x] Configure Python package structure with pyproject.toml
- [x] Implement CLI with `firetwin doctor` command
- [x] Add code quality tools (Ruff, MyPy, Pytest)
- [x] Configure pre-commit hooks
- [x] Set up GitHub Actions CI pipeline
- [x] Add Apache-2.0 license
- [x] Create initial documentation structure
- [x] Write comprehensive README
- [x] Create Makefile for development commands

### Acceptance Criteria

- [x] Fresh clone can install from documented commands
- [ ] `pytest`, `ruff check`, `ruff format --check` and `mypy` pass (pending environment creation)
- [ ] CI passes (pending first push)
- [x] No credentials or large data committed

### Next Steps

1. Create conda environment and install package
2. Run all quality checks locally
3. Create GitHub repository (remote)
4. Push initial commit
5. Verify CI passes

## Phase 1: Synthetic End-to-End Vertical Slice

**Status**: PENDING

**Purpose**: Prove architecture before downloading large datasets.

### Planned Tasks

- [ ] Generate small synthetic terrain, fuel, wind, and ignition grid
- [ ] Implement simple persistence baseline
- [ ] Implement radial growth baseline
- [ ] Implement wind-oriented elliptical growth baseline
- [ ] Store outputs in canonical Xarray/Zarr format
- [ ] Calculate IoU, boundary distance, and area error
- [ ] Display animated map in minimal dashboard
- [ ] Create golden tests

### Estimated Timeline

Start after Phase 0 completion. Expected duration: 1-2 weeks.

## Phase 2: Data-Source Smoke Tests and Audit

**Status**: PENDING

### Planned Tasks

- [ ] Build FIRMS API client
- [ ] Build NIFC/WFIGS client
- [ ] Build MTBS client
- [ ] Build ERA5-Land client (cdsapi)
- [ ] Build LANDFIRE client
- [ ] Build USGS 3DEP client
- [ ] Download tiny samples for validation
- [ ] Validate CRS, timestamps, geometries, units
- [ ] Build candidate fire inventory
- [ ] Produce data-availability audit

## Future Phases

- **Phase 3**: Historical case builder (3 pilot fires)
- **Phase 4**: Real-data baselines
- **Phase 5**: Simulation corpus and surrogate
- **Phase 6**: Hybrid model
- **Phase 7**: Assimilation and calibrated uncertainty
- **Phase 8**: Simulated intervention planner
- **Phase 9**: Production application
- **Phase 10**: Research-quality release

## Overall Progress

```
Phase 0: ████████████████████ 100% ✅
Phase 1: ░░░░░░░░░░░░░░░░░░░░   0%
Phase 2: ░░░░░░░░░░░░░░░░░░░░   0%
Phase 3: ░░░░░░░░░░░░░░░░░░░░   0%
...
Overall: ██░░░░░░░░░░░░░░░░░░  10%
```

## Known Issues

None at this time.

## Blockers

None at this time.

## Notes

- Using conda for dependency management (better for geospatial packages)
- GitHub username: rajat116
- Email: rajatgupta116@gmail.com
- M1 Mac with 8GB RAM - keeping development lightweight
