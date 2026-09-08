"""Test RealFireCaseConverter with Carlton Complex 2014.

This script tests the converter's ability to:
1. Fetch data from multiple sources
2. Display data availability
3. Begin layer alignment (currently placeholder)
"""

import json
from pathlib import Path

from firetwin.data.converter import RealFireCaseConverter


def test_carlton_complex_converter():
    """Test converter with Carlton Complex 2014."""
    print("🔥 Testing RealFireCaseConverter: Carlton Complex 2014\n")
    print("=" * 70)

    # Carlton Complex bbox (WA State)
    fire_name = "Carlton Complex"
    fire_year = 2014
    bbox = (-120.5, 47.5, -119.5, 48.5)  # (min_lon, min_lat, max_lon, max_lat)
    target_resolution_m = 100.0  # 100m grid

    # Initialize converter
    converter = RealFireCaseConverter(
        fire_name=fire_name,
        fire_year=fire_year,
        bbox=bbox,
        target_resolution_m=target_resolution_m,
        target_crs="EPSG:32610",  # UTM Zone 10N for Western US
    )

    # Fetch data
    converter.fetch_all_data()

    # Get summary
    summary = converter.get_data_summary()

    # Display summary
    print("\n" + "=" * 70)
    print("📊 Data Summary\n")
    print(json.dumps(summary, indent=2))

    # Test layer alignment (placeholder for now)
    converter.align_layers()

    # Test FireCase building
    fire_case = converter.build_fire_case()

    # Save FireCase if successful
    if fire_case:
        output_dir = Path("data/fire_cases")
        converter.save_fire_case(fire_case, output_dir)
        print("\n✅ SUCCESS: FireCase built and saved!")
        print("   Converter working end-to-end")
        return True
    else:
        print("\n⚠️  WARNING: Failed to build FireCase")
        return False


if __name__ == "__main__":
    import sys

    success = test_carlton_complex_converter()
    sys.exit(0 if success else 1)
