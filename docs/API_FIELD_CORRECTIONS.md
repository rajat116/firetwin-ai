# API Field Name Corrections

**Date**: 2026-09-07

## Issue Discovery

During Phase 3 testing, we discovered that the actual field names from NIFC and MTBS APIs differ from what was initially implemented in the data clients.

## NIFC/WFIGS API

**Service**: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0

**Issue**: Field names have prefixes (`attr_` and `poly_`) that were not included in the client implementation.

**Actual Field Names**:
- `attr_IncidentName` (not `IncidentName`)
- `attr_FireDiscoveryDateTime` (not `FireDiscoveryDateTime`)
- `poly_GISAcres` (not `GISAcres`)  
- `attr_PercentContained` (not `PercentContained`)
- `poly_DateCurrent` (not `DateCurrent`)
- `poly_IRWINID` (not `IRWINID`)

**Fix Required**: Update `src/firetwin/data/clients/nifc.py` to use prefixed field names.

## MTBS API

**Service**: https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/0

**Issue 1**: Field names are lowercase (not PascalCase as implemented).

**Actual Field Names**:
- `fire_name` (not `Fire_Name`)
- `fire_id` (not `Fire_ID`)
- `acres` (not `Acres`)
- `ig_date` (not `Ig_Date` or `IgnitionDate`)
- `fire_type` (not `Fire_Type`)

**Issue 2**: No direct `Fire_Year` field exists.

**Year Extraction Options**:
1. Extract from `fire_id` (format: `[STATE][COORDS][YYYYMMDD]`, e.g., `AZ3630511215520141023` → 2014-10-23)
2. Convert `ig_date` Unix timestamp (milliseconds) to year

**Fix Required**: 
1. Update `src/firetwin/data/clients/mtbs.py` to use lowercase field names
2. Implement year extraction from `fire_id` or `ig_date`
3. Update query logic to not filter by non-existent `Fire_Year` field

## Sample API Responses

### NIFC Sample
```json
{
  "attr_IncidentName": "Creek Fire",
  "attr_FireDiscoveryDateTime": 1599192000000,
  "poly_GISAcres": 379895,
  "attr_PercentContained": 100
}
```

### MTBS Sample
```json
{
  "fire_id": "AZ3630511215520141023",
  "fire_name": "SLOPES RX",
  "acres": 2999.0,
  "ig_date": 1414022400000,
  "fire_type": "Wildfire"
}
```

## Testing Validation

**Status**: Field name corrections identified but not yet implemented in clients.

**Next Steps**:
1. Update NIFC client with correct field names
2. Update MTBS client with lowercase fields and year extraction
3. Re-run test_case_builder.py to validate data fetching
4. Verify data correctness (dates, locations, fire names)

## Impact

**Current**: Data clients return empty results due to field name mismatches
**After Fix**: Clients should successfully fetch and parse real fire data
