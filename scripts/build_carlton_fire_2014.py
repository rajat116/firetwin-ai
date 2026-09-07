"""Build complete fire case for Carlton Complex 2014.

This script demonstrates building a historical fire case from multiple data sources:
- NIFC Historical: Fire perimeter progression
- MTBS: Final validated perimeter with burn severity
- FIRMS: Active fire detections (if available)
- ERA5-Land: Weather data (if credentials available)
- USGS 3DEP: Elevation data
- LANDFIRE: Fuel data (manual download required)

Carlton Complex Fire 2014:
- Location: Washington State
- Size: 251,965 acres (largest fire in WA state history at the time)
- Date: July 2014
- Multiple fires merged into complex
"""

import json
from datetime import date, datetime
from pathlib import Path

from firetwin.data.clients import (
    ERA5LandClient,
    FIRMSClient,
    MTBSClient,
    NIFCHistoricalClient,
    USGS3DEPClient,
)


def build_carlton_complex_case():
    """Build Carlton Complex 2014 fire case from real data sources."""
    print("🔥 Building Carlton Complex 2014 Fire Case\n")
    print("=" * 70)

    # Fire metadata
    fire_name = "Carlton Complex"
    fire_year = 2014
    # Approximate bbox for Carlton Complex in Washington
    bbox = (-120.5, 47.5, -119.5, 48.5)  # (min_lon, min_lat, max_lon, max_lat)

    data_summary = {
        "fire_name": fire_name,
        "fire_year": fire_year,
        "bbox": bbox,
        "data_sources": {},
    }

    # 1. NIFC Historical Perimeters
    print("\n1️⃣  Fetching NIFC Historical Perimeters...")
    try:
        nifc_client = NIFCHistoricalClient()
        nifc_perimeters = nifc_client.get_fire_by_name(fire_name, year=fire_year)

        if nifc_perimeters:
            print(f"   ✅ Found {len(nifc_perimeters)} NIFC perimeter(s)")
            for p in nifc_perimeters:
                date_obj = p.get_date()
                date_str = date_obj.strftime("%Y-%m-%d") if date_obj else "N/A"
                print(f"      - {p.incident_name}: {p.gis_acres:,.0f} acres ({date_str})")
                print(f"        Agency: {p.agency or 'N/A'}, Source: {p.source or 'N/A'}")

            data_summary["data_sources"]["nifc_historical"] = {
                "available": True,
                "count": len(nifc_perimeters),
                "largest_acres": max(p.gis_acres for p in nifc_perimeters),
            }
        else:
            print("   ⚠️  No NIFC historical perimeters found")
            data_summary["data_sources"]["nifc_historical"] = {
                "available": False,
                "reason": "No records found",
            }
    except Exception as e:
        print(f"   ❌ NIFC Historical error: {e}")
        data_summary["data_sources"]["nifc_historical"] = {
            "available": False,
            "error": str(e),
        }

    # 2. MTBS Final Perimeter
    print("\n2️⃣  Fetching MTBS Final Perimeter...")
    try:
        mtbs_client = MTBSClient()
        mtbs_fires = mtbs_client.get_fire_by_name(fire_name, year=fire_year)

        if mtbs_fires:
            print(f"   ✅ Found {len(mtbs_fires)} MTBS fire(s)")
            for f in mtbs_fires:
                ig_date = (
                    f.ignition_date.strftime("%Y-%m-%d") if f.ignition_date else "N/A"
                )
                print(f"      - {f.fire_name}: {f.acres:,.0f} acres")
                print(
                    f"        Year: {f.fire_year}, Ignition: {ig_date}, Type: {f.fire_type}"
                )

            data_summary["data_sources"]["mtbs"] = {
                "available": True,
                "count": len(mtbs_fires),
                "total_acres": sum(f.acres for f in mtbs_fires),
            }
        else:
            print("   ⚠️  No MTBS fires found")
            data_summary["data_sources"]["mtbs"] = {
                "available": False,
                "reason": "No records found",
            }
    except Exception as e:
        print(f"   ❌ MTBS error: {e}")
        data_summary["data_sources"]["mtbs"] = {
            "available": False,
            "error": str(e),
        }

    # 3. FIRMS Active Fire Detections
    print("\n3️⃣  Checking FIRMS Active Fire Detections...")
    print("   ℹ️  FIRMS requires MAP_KEY (skipping for now)")
    print("   Note: To enable, set FIRMS_MAP_KEY environment variable")
    data_summary["data_sources"]["firms"] = {
        "available": False,
        "reason": "API key required",
    }

    # 4. ERA5-Land Weather Data
    print("\n4️⃣  Checking ERA5-Land Weather Data...")
    print("   ℹ️  ERA5 requires CDS API credentials (skipping for now)")
    print("   Note: To enable, configure ~/.cdsapirc or set environment variables")
    data_summary["data_sources"]["era5"] = {
        "available": False,
        "reason": "CDS credentials required",
    }

    # 5. USGS 3DEP Elevation
    print("\n5️⃣  Checking USGS 3DEP Elevation Data...")
    try:
        usgs_client = USGS3DEPClient()
        datasets = usgs_client.search_datasets(bbox)

        if datasets:
            print(f"   ✅ Found {len(datasets)} elevation dataset(s) available")
            print(f"      Dataset: {datasets[0].get('title', 'Unknown')}")
            data_summary["data_sources"]["usgs_3dep"] = {
                "available": True,
                "count": len(datasets),
            }
        else:
            print("   ⚠️  No elevation datasets found")
            data_summary["data_sources"]["usgs_3dep"] = {
                "available": False,
                "reason": "No datasets found",
            }
    except Exception as e:
        print(f"   ❌ USGS 3DEP error: {e}")
        data_summary["data_sources"]["usgs_3dep"] = {
            "available": False,
            "error": str(e),
        }

    # 6. LANDFIRE Fuels
    print("\n6️⃣  LANDFIRE Fuel Data...")
    print("   ℹ️  LANDFIRE requires manual AOI selection and download")
    print("   Note: Visit https://landfire.gov/viewer/ to download")
    data_summary["data_sources"]["landfire"] = {
        "available": False,
        "reason": "Manual download required",
    }

    # Summary
    print("\n" + "=" * 70)
    print("📊 Data Availability Summary\n")

    available_sources = sum(
        1
        for src in data_summary["data_sources"].values()
        if src.get("available", False)
    )
    total_sources = len(data_summary["data_sources"])

    print(f"Available: {available_sources}/{total_sources} data sources")
    print(f"\nCore fire data:")
    print(
        f"  - NIFC Historical: {'✅' if data_summary['data_sources']['nifc_historical'].get('available') else '❌'}"
    )
    print(
        f"  - MTBS Final: {'✅' if data_summary['data_sources']['mtbs'].get('available') else '❌'}"
    )

    # Save summary
    output_dir = Path("data/fire_cases")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / "carlton_complex_2014_summary.json"
    with open(summary_file, "w") as f:
        json.dump(data_summary, f, indent=2)

    print(f"\n💾 Summary saved to: {summary_file}")

    # Validation
    has_core_data = (
        data_summary["data_sources"]["nifc_historical"].get("available", False)
        or data_summary["data_sources"]["mtbs"].get("available", False)
    )

    if has_core_data:
        print("\n✅ SUCCESS: Core fire perimeter data available!")
        print("   Ready to build complete FireCase")
        return True
    else:
        print("\n⚠️  WARNING: No core perimeter data available")
        print("   Cannot build complete FireCase without perimeter data")
        return False


if __name__ == "__main__":
    import sys

    success = build_carlton_complex_case()
    sys.exit(0 if success else 1)
