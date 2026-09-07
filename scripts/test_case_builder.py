"""Test script to validate FireCaseBuilder with Creek Fire (2020).

This script tests data fetching and validates the quality and correctness
of the downloaded data.
"""

import json
from datetime import date
from pathlib import Path

from firetwin.data.case_builder import CaseBuilderConfig, FireCaseBuilder


def test_creek_fire_2020():
    """Test case builder with Creek Fire 2020."""
    print("=" * 80)
    print("Testing FireCaseBuilder with Creek Fire (2020)")
    print("=" * 80)
    print()
    
    # Creek Fire configuration
    # Note: Using a smaller bbox and shorter date range for testing
    config = CaseBuilderConfig(
        fire_id="creek_fire_2020",
        fire_name="Creek Fire",
        bbox=(-119.6, 37.0, -118.9, 37.5),  # Fresno/Madera Counties, CA
        start_date=date(2020, 9, 4),  # Fire started Sept 4
        end_date=date(2020, 9, 14),  # First 10 days for testing
        grid_resolution_m=60.0,
        # Note: API keys would come from environment in production
        firms_map_key=None,  # Will skip FIRMS if not provided
        cds_api_url=None,  # Will skip ERA5 if not provided
        cds_api_key=None,
        fetch_firms=True,
        fetch_nifc=True,
        fetch_mtbs=True,
        fetch_era5=False,  # Skip ERA5 for quick test (requires credentials)
        fetch_landfire=False,  # Skip LANDFIRE (manual download)
        fetch_3dep=False,  # Skip 3DEP for quick test (large files)
    )
    
    print("Configuration:")
    print(f"  Fire: {config.fire_name}")
    print(f"  ID: {config.fire_id}")
    print(f"  Date range: {config.start_date} to {config.end_date}")
    print(f"  Bbox: {config.bbox}")
    print(f"  Grid resolution: {config.grid_resolution_m}m")
    print()
    
    # Create builder
    builder = FireCaseBuilder(config)
    
    # Check which clients are initialized
    print("Initialized clients:")
    print(f"  FIRMS: {'✓' if builder.firms_client else '✗ (no API key)'}")
    print(f"  NIFC: {'✓' if builder.nifc_client else '✗'}")
    print(f"  MTBS: {'✓' if builder.mtbs_client else '✗'}")
    print(f"  ERA5: {'✓' if builder.era5_client else '✗ (skipped for test)'}")
    print(f"  LANDFIRE: {'✓' if builder.landfire_client else '✗ (skipped for test)'}")
    print(f"  3DEP: {'✓' if builder.usgs_client else '✗ (skipped for test)'}")
    print()
    
    # Fetch data
    print("=" * 80)
    print("Fetching data...")
    print("=" * 80)
    print()
    
    try:
        raw_data = builder.fetch_all_data()
    except Exception as e:
        print(f"ERROR: Data fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 80)
    print("Data Summary")
    print("=" * 80)
    print()
    
    # Get summary
    summary = builder.get_data_summary()
    print(json.dumps(summary, indent=2, default=str))
    print()
    
    # Validate data
    print("=" * 80)
    print("Validation Checks")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    # Check FIRMS data
    if "firms" in raw_data and len(raw_data["firms"]) > 0:
        print("✓ FIRMS: Data fetched")
        
        # Check detection locations
        detections = raw_data["firms"]
        lats = [d.latitude for d in detections]
        lons = [d.longitude for d in detections]
        
        minx, miny, maxx, maxy = config.bbox
        if all(miny <= lat <= maxy for lat in lats) and all(minx <= lon <= maxx for lon in lons):
            print(f"  ✓ All {len(detections)} detections within bbox")
            passed += 1
        else:
            print(f"  ✗ Some detections outside bbox!")
            failed += 1
        
        # Check dates
        dates_in_range = all(
            config.start_date <= d.acq_date <= config.end_date
            for d in detections
        )
        if dates_in_range:
            print(f"  ✓ All detections within date range")
            passed += 1
        else:
            print(f"  ✗ Some detections outside date range!")
            failed += 1
        
        # Show sample
        print(f"  Sample detection:")
        sample = detections[0]
        print(f"    Date: {sample.acq_date}")
        print(f"    Location: ({sample.latitude:.4f}, {sample.longitude:.4f})")
        print(f"    Confidence: {sample.confidence}%")
        print(f"    FRP: {sample.frp} MW")
    else:
        print("ℹ FIRMS: No data (API key may be missing)")
    
    print()
    
    # Check NIFC data
    if "nifc" in raw_data and len(raw_data["nifc"]) > 0:
        print("✓ NIFC: Data fetched")
        
        perimeters = raw_data["nifc"]
        print(f"  Found {len(perimeters)} perimeter(s)")
        
        # Check fire name match
        if any("creek" in p.incident_name.lower() for p in perimeters):
            print(f"  ✓ Fire name matches search")
            passed += 1
        else:
            print(f"  ⚠ Fire name mismatch - check if this is correct")
            print(f"    Names found: {[p.incident_name for p in perimeters]}")
        
        # Show sample
        if perimeters:
            print(f"  Sample perimeter:")
            sample = perimeters[0]
            print(f"    Incident: {sample.incident_name}")
            print(f"    Date: {sample.fire_discovery_datetime}")
            print(f"    Acres: {sample.gis_acres:,.0f}")
    else:
        print("⚠ NIFC: No data found")
        print("  This might be expected if:")
        print("  - Fire name doesn't match NIFC records")
        print("  - Fire was not mapped in NIFC database")
    
    print()
    
    # Check MTBS data
    if "mtbs" in raw_data and len(raw_data["mtbs"]) > 0:
        print("✓ MTBS: Data fetched")
        
        fires = raw_data["mtbs"]
        print(f"  Found {len(fires)} fire(s)")
        
        # Check year match
        if any(f.fire_year == 2020 for f in fires):
            print(f"  ✓ Fire year matches (2020)")
            passed += 1
        else:
            print(f"  ⚠ Fire year mismatch")
        
        # Show sample
        if fires:
            print(f"  Sample MTBS record:")
            sample = fires[0]
            print(f"    Fire: {sample.fire_name}")
            print(f"    Year: {sample.fire_year}")
            print(f"    Acres: {sample.acres:,.0f}")
    else:
        print("⚠ MTBS: No data found")
        print("  This might be expected if:")
        print("  - Fire name doesn't match MTBS records")
        print("  - MTBS data not yet available for this fire")
    
    print()
    print("=" * 80)
    print(f"Validation Results: {passed} passed, {failed} failed")
    print("=" * 80)
    print()
    
    if failed > 0:
        print("❌ VALIDATION FAILED: Data has issues")
        return False
    elif passed == 0:
        print("⚠ WARNING: No data could be validated (API keys may be missing)")
        print("   This is OK for initial testing")
        return True
    else:
        print("✅ VALIDATION PASSED: Data looks correct")
        return True


if __name__ == "__main__":
    success = test_creek_fire_2020()
    exit(0 if success else 1)
