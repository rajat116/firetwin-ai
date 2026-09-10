"""Build all 3 pilot fire cases with real terrain, fuels, and ERA5 weather.

This script builds complete FireCase objects for:
1. Carlton Complex 2014 (WA, 252k acres) - Pacific NW
2. King Fire 2014 (CA, 98k acres) - Sierra Nevada
3. Big Cougar 2014 (OR/ID, 65k acres) - Northern Rockies

Each fire demonstrates the end-to-end Phase 4C pipeline:
- Multi-source data fetching (NIFC, MTBS, FIRMS, ERA5, USGS, LANDFIRE)
- Spatial alignment and reprojection
- USGS 3DEP DEM resampling to the FireTwin grid
- LANDFIRE LF2022 FBFM40 resampling to the FireTwin grid
- ERA5-Land weather summarization when CDS credentials are configured
- Rasterization to canonical grid
- FireCase construction with real perimeters, real terrain, real fuel models, and real weather
"""

from datetime import datetime, timedelta
from pathlib import Path

from firetwin.data.converter import RealFireCaseConverter


def build_pilot_fire(
    fire_name: str,
    fire_year: int,
    bbox: tuple[float, float, float, float],
    target_crs: str = "EPSG:32610",
    weather_start: datetime | None = None,
) -> bool:
    """Build a single pilot fire case.

    Args:
        fire_name: Name of the fire incident
        fire_year: Fire year
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) in WGS84
        target_crs: Target CRS for modeling
        weather_start: Optional ignition/discovery weather reference time

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"🔥 Building: {fire_name} ({fire_year})")
    print(f"{'=' * 70}")

    converter = RealFireCaseConverter(
        fire_name=fire_name,
        fire_year=fire_year,
        bbox=bbox,
        target_resolution_m=100.0,
        target_crs=target_crs,
        weather_start=weather_start,
        weather_end=weather_start + timedelta(hours=23) if weather_start else None,
    )

    # Fetch data
    converter.fetch_all_data()

    # Align layers
    converter.align_layers()

    # Build FireCase
    fire_case = converter.build_fire_case()

    # Save if successful
    if fire_case:
        output_dir = Path("data/fire_cases")
        converter.save_fire_case(fire_case, output_dir)
        return True
    else:
        print(f"\n❌ Failed to build FireCase for {fire_name}")
        return False


def main():
    """Build all 3 pilot fire cases."""
    print("🚀 Building All Pilot Fire Cases (Phase 4C real terrain/fuels/weather)")
    print("=" * 70)

    # Define pilot fires (from PHASE3_PILOT_FIRES.md)
    pilot_fires = [
        {
            "name": "Carlton Complex",
            "year": 2014,
            "bbox": (-120.5, 47.5, -119.5, 48.5),  # Washington
            "crs": "EPSG:32610",  # UTM 10N
            "weather_start": datetime(2014, 7, 14, 12),
        },
        {
            "name": "KING",  # Must use uppercase for API
            "year": 2014,
            "bbox": (-121.5, 38.5, -120.0, 39.5),  # California Sierra Nevada
            "crs": "EPSG:32610",  # UTM 10N
            "weather_start": datetime(2014, 9, 13, 23),
        },
        {
            "name": "Big Cougar",
            "year": 2014,
            "bbox": (-117.5, 45.4, -116.2, 46.6),  # Oregon/Idaho (corrected bounds)
            "crs": "EPSG:32611",  # UTM 11N (further east)
            "weather_start": datetime(2014, 8, 2, 12),
        },
    ]

    results = []
    for fire in pilot_fires:
        success = build_pilot_fire(
            fire_name=fire["name"],
            fire_year=fire["year"],
            bbox=fire["bbox"],
            target_crs=fire["crs"],
            weather_start=fire["weather_start"],
        )
        results.append((fire["name"], success))

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    successful = sum(1 for _, success in results if success)
    total = len(results)

    for fire_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {fire_name}")

    print(f"\n🎯 Built {successful}/{total} pilot fire cases")

    if successful == total:
        print("\n✅ ALL PILOT FIRES COMPLETE!")
        print("   Pilot case building successful")
        print("   FireCases saved to: data/fire_cases/")
        return True
    else:
        print(f"\n⚠️  {total - successful} fire(s) failed")
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
