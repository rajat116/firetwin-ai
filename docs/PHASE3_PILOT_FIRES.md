

# Phase 3 - Pilot Fire Selection

**Goal**: Select 3 historical fires to validate the end-to-end pipeline before scaling up.

## Selection Criteria

### Must-Have
1. **Time-resolved data**: Multiple perimeter observations (not just final)
2. **Geographic diversity**: Different regions within Western US
3. **Scale diversity**: Small (<5k acres), medium (5-20k acres), large (>20k acres)
4. **Data availability**: FIRMS detections + at least one perimeter source
5. **Recent enough**: 2018-2024 for best data coverage

### Nice-to-Have
- Well-documented fire with known progression
- Multiple NIFC perimeter snapshots
- Good weather coverage (minimal gaps in ERA5)
- Available LANDFIRE and 3DEP data
- Clear ignition point and spread pattern

## Candidate Fires (California Focus)

### Large Fire (>20,000 acres)
**Camp Fire (2018)**
- **Location**: Butte County, CA
- **Dates**: Nov 8-25, 2018
- **Size**: ~153,000 acres
- **Why**: Extremely well-documented, rapid spread, multiple data sources
- **Bbox**: ~(-121.7, 39.7, -121.3, 39.9)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅, ERA5 ✅

**Dixie Fire (2021)**
- **Location**: Plumas County, CA
- **Dates**: July 13 - Oct 25, 2021
- **Size**: ~963,000 acres
- **Why**: California's largest single-source fire, long duration
- **Bbox**: ~(-121.7, 39.7, -120.8, 40.5)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅, ERA5 ✅

**Creek Fire (2020)**
- **Location**: Fresno/Madera Counties, CA
- **Dates**: Sept 4 - Dec 24, 2020
- **Size**: ~379,000 acres
- **Why**: Sierra Nevada location, extreme fire behavior
- **Bbox**: ~(-119.6, 37.0, -118.9, 37.5)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅, ERA5 ✅

### Medium Fire (5,000-20,000 acres)
**Thomas Fire (2017)** - **Too early, may have limited data**

**River Fire (2021)**
- **Location**: Nevada/Placer Counties, CA
- **Dates**: Aug 11-21, 2021
- **Size**: ~2,600 acres
- **Why**: Recent, good progression data, accessible location
- **Bbox**: ~(-120.9, 39.3, -120.8, 39.4)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅, ERA5 ✅

**McKinney Fire (2022)**
- **Location**: Siskiyou County, CA
- **Dates**: July 29 - Sept 2, 2022
- **Size**: ~60,000 acres
- **Why**: Recent, Northern CA, diverse terrain
- **Bbox**: ~(-123.2, 41.7, -122.8, 41.9)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅ (pending), ERA5 ✅

### Small Fire (<5,000 acres)
**Caldor Fire (2021)** - Actually large (~221k acres)

**Mosquito Fire (2022)**
- **Location**: Placer/El Dorado Counties, CA
- **Dates**: Sept 6 - Oct 22, 2022
- **Size**: ~76,000 acres (actually medium-large)
- **Why**: Recent, Sierra Nevada, crossed major highway
- **Bbox**: ~(-120.8, 39.0, -120.4, 39.2)
- **Data**: FIRMS ✅, NIFC ✅, MTBS likely, ERA5 ✅

**Kincade Fire (2019)**
- **Location**: Sonoma County, CA
- **Dates**: Oct 23 - Nov 6, 2019
- **Size**: ~77,758 acres (medium-large)
- **Why**: Wine country, high-wind event, good documentation
- **Bbox**: ~(-123.0, 38.6, -122.6, 38.9)
- **Data**: FIRMS ✅, NIFC ✅, MTBS ✅, ERA5 ✅

## Recommended Initial Selection

### **FINAL SELECTION: 2014 Historical Fires** ✅

After discovering NIFC Historical archive (2000-2021+) and validating MTBS coverage for 2014, we selected 2014 fires for better data completeness:

> Phase 4E update (2026-09-10): these pilots are valid final-extent artifacts with real covariates,
> but the earlier assumption of strong perimeter progression was too optimistic. The current audit
> found only one matching NIFC perimeter timestamp per pilot. FIRMS historical detections still need
> to be audited with a configured `FIRMS_MAP_KEY`.

1. **Carlton Complex (2014)** - Washington State
   - **Size**: 251,965 acres (largest in WA state history at the time)
   - **Region**: Pacific Northwest
   - **Dates**: July 2014
   - **Data**: NIFC Historical ✅, MTBS ✅, FIRMS ✅
   - **Why**: Massive complex, multiple merged fires, geographically useful final-extent case

2. **King Fire (2014)** - California
   - **Size**: 97,685 acres
   - **Region**: Central California (Sierra Nevada)
   - **Dates**: September 2014
   - **Data**: NIFC Historical ✅, MTBS ✅, FIRMS ✅
   - **Why**: Well-documented Sierra Nevada fire, diverse terrain

3. **Big Cougar (2014)** - Northern Rockies (OR/ID)
   - **Size**: 65,305 acres
   - **Region**: Oregon/Idaho border
   - **Dates**: August 2014
   - **Data**: NIFC Historical ✅, MTBS ✅, FIRMS ✅
   - **Why**: Geographic diversity, different ecosystem

**Benefits of 2014 Selection:**
- Fully validated MTBS data (2-3 year lag means 2014 is complete)
- NIFC Historical perimeters available, but current audit does not show enough perimeter timestamps
  for hourly progression labels
- FIRMS daily detections available
- ERA5-Land weather reanalysis complete
- Geographic diversity: WA, CA, OR/ID
- Scale diversity: 65k - 252k acres

### Original Candidates (2018-2024)
*Kept for reference if needed for recent fire analysis*

### Option A: Diverse Scale
1. **Large**: Creek Fire (2020) - 379k acres, Sierra Nevada
2. **Medium**: McKinney Fire (2022) - 60k acres, Northern CA
3. **Small**: Find a well-documented fire <10k acres in 2020-2023

### Option B: Recent & Well-Documented
1. **Dixie Fire (2021)** - Largest, longest duration, excellent data
2. **Mosquito Fire (2022)** - Recent, good progression data
3. **River Fire (2021)** - Smaller, rapid spread, accessible

### Option C: Geographic Diversity
1. **Creek Fire (2020)** - Central Sierra Nevada
2. **McKinney Fire (2022)** - Northern California
3. **Kincade Fire (2019)** - North Bay/Wine Country

## Data Availability Check

Before finalizing selection, verify:
- [ ] FIRMS has detections for the date range
- [ ] NIFC has perimeter snapshots (not just final)
- [ ] MTBS has final perimeter and burn severity
- [ ] ERA5-Land covers the date range
- [ ] USGS 3DEP covers the bbox
- [ ] LANDFIRE has data for the fire year

## Next Steps

1. Run data availability queries for top 3 candidates
2. Select final 3 fires based on data completeness
3. Create CaseBuilderConfig for each fire
4. Fetch all data and validate quality
5. Build canonical FireCase objects
6. Document any data gaps or issues

## Notes

- **Perimeter progression**: NIFC may only have final perimeters for older fires
- **FIRMS temporal coverage**: 375m VIIRS preferred over 1km MODIS
- **Weather resolution**: ERA5-Land is 9km, much coarser than terrain/fuels
- **Bbox sizing**: Include ~10km buffer around fire for context

## References

- NIFC Fire Archive: https://data-nifc.opendata.arcgis.com/
- MTBS Fire List: https://www.mtbs.gov/direct-download
- Cal Fire Incidents: https://www.fire.ca.gov/incidents/
- InciWeb Archive: https://inciweb.wildfire.gov/
