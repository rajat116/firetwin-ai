# Phase 3 Status - Historical Fire Case Builder

**Last Updated**: 2026-09-07
**Status**: IN PROGRESS - Infrastructure built, API corrections identified

## What's Working ✅

1. **Case Builder Infrastructure**
   - `FireCaseBuilder` class with multi-source orchestration
   - `CaseBuilderConfig` for fire specifications
   - Data fetching framework operational
   - Test scripts created and functional

2. **API Connectivity**
   - All 6 data source APIs are reachable
   - Client initialization working
   - Request/response cycle functional

3. **Testing Framework**
   - Test scripts for validation
   - Debug scripts for API exploration
   - Comprehensive error checking

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

## Next Steps (Priority Order)

### Immediate (Get CI Passing)
1. ✅ Fix lint/format issues in case_builder.py
2. ⏳ Ensure all existing tests still pass
3. ⏳ Commit clean state

### Short-term (This Week)
4. Fix MTBS client field name issues
5. Test MTBS with actual 2020 fires
6. Research NIFC historical archive access
7. Obtain FIRMS API key for testing

### Medium-term (Phase 3 Completion)
8. Select 1-2 fires with confirmed MTBS data
9. Implement spatial/temporal alignment
10. Convert to canonical FireCase format
11. Build first complete real fire case

## Lessons Learned

1. **Test with real data early** - Caught field name mismatches that unit tests missed
2. **Understand data source limitations** - "Current" vs "Historical" is critical
3. **API documentation != API reality** - Always verify actual responses
4. **Run all checks before committing** - Avoid CI failures

## Revised Approach

**Old Plan**: Build 3 diverse pilot fires from different sources
**New Plan**: 
1. Start with ONE fire that we can fully validate
2. Use MTBS (most reliable for historical data)
3. Supplement with FIRMS if available
4. Accept that we may not have time-resolved progression initially
5. Document limitations clearly

## Code Status

**Passing**:
- FireCaseBuilder infrastructure
- Test framework
- Client initialization

**Needs Fix**:
- MTBS field name parsing
- Lint issues (SIM105 in case_builder)
- MTBS client tests (will fail with corrections)

**Not Yet Implemented**:
- Spatial alignment
- Temporal interpolation  
- FireCase conversion
- Visualization tools
