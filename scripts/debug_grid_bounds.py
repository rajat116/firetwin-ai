"""Debug grid bounds calculation for fire cases.

This script traces through the grid bounds calculation to identify
why some grids (especially King fire) are way too large.
"""

import numpy as np

from firetwin.data.clients import NIFCHistoricalClient


def debug_fire_bounds(fire_name: str, fire_year: int, target_crs: str = "EPSG:32610"):
    """Debug the bounds calculation for a specific fire.

    Args:
        fire_name: Name of the fire
        fire_year: Year of the fire
        target_crs: Target CRS for projection
    """
    print(f"\n{'=' * 70}")
    print(f"🔥 Debugging: {fire_name} ({fire_year})")
    print(f"{'=' * 70}")

    # Fetch fire perimeter
    client = NIFCHistoricalClient()
    perimeters = client.get_fire_by_name(fire_name, year=fire_year)

    if not perimeters:
        print("❌ No perimeters found")
        return

    print(f"✅ Found {len(perimeters)} perimeter(s)")

    # Convert to GeoDataFrame
    gdf = client.perimeters_to_geodataframe(perimeters)
    print("\n📍 Original Data:")
    print(f"   CRS: {gdf.crs}")
    print(f"   Bounds (WGS84): {gdf.total_bounds}")

    minx, miny, maxx, maxy = gdf.total_bounds
    width_deg = maxx - minx
    height_deg = maxy - miny
    print(f"   Size: {width_deg:.4f}° × {height_deg:.4f}°")

    # Reproject to target CRS
    print(f"\n🔄 Reprojecting to {target_crs}...")
    gdf_proj = gdf.to_crs(target_crs)

    proj_bounds = gdf_proj.total_bounds
    print(f"   Projected CRS: {gdf_proj.crs}")
    print(f"   Projected bounds: {proj_bounds}")

    minx, miny, maxx, maxy = proj_bounds
    width_m = maxx - minx
    height_m = maxy - miny
    area_km2 = (width_m * height_m) / 1e6

    print(f"   Size: {width_m:,.0f}m × {height_m:,.0f}m")
    print(f"   Size: {width_m / 1000:.1f}km × {height_m / 1000:.1f}km")
    print(f"   Bounding box area: {area_km2:.1f} km²")

    # Current implementation: 10% buffer based on max dimension
    print("\n📐 Current Buffer Calculation (10% of max dimension):")
    buffer_m = max(width_m, height_m) * 0.1
    print(f"   Buffer: {buffer_m:,.0f}m = {buffer_m / 1000:.1f}km")

    buffered_minx = minx - buffer_m
    buffered_miny = miny - buffer_m
    buffered_maxx = maxx + buffer_m
    buffered_maxy = maxy + buffer_m

    buffered_width = buffered_maxx - buffered_minx
    buffered_height = buffered_maxy - buffered_miny
    buffered_area_km2 = (buffered_width * buffered_height) / 1e6

    print(f"   Buffered size: {buffered_width:,.0f}m × {buffered_height:,.0f}m")
    print(f"   Buffered area: {buffered_area_km2:.1f} km²")

    # Calculate grid at 100m resolution
    resolution_m = 100.0
    grid_width = int(np.ceil(buffered_width / resolution_m))
    grid_height = int(np.ceil(buffered_height / resolution_m))
    total_pixels = grid_width * grid_height

    print("\n🔢 Grid Calculation (100m resolution):")
    print(f"   Grid dimensions: {grid_height} × {grid_width}")
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Memory (float32): {(total_pixels * 4) / 1024 / 1024:.1f} MB per layer")

    # Better buffer: Fixed 5km or 10% of actual fire size, whichever is smaller
    print("\n💡 Proposed Fix: Smarter Buffer")

    # Calculate actual fire area from geometry
    fire_area_m2 = gdf_proj.geometry.area.sum()
    fire_area_km2 = fire_area_m2 / 1e6
    fire_area_acres = fire_area_km2 * 247.105

    print(f"   Actual fire area: {fire_area_km2:.1f} km² = {fire_area_acres:,.0f} acres")

    # Proposed: 10% buffer of actual fire dimension, max 5km
    fire_dimension = np.sqrt(fire_area_m2)  # Approximate side length
    smart_buffer = min(fire_dimension * 0.1, 5000)  # Max 5km buffer

    print(f"   Fire dimension (approx): {fire_dimension:,.0f}m")
    print(f"   Smart buffer: {smart_buffer:,.0f}m = {smart_buffer / 1000:.1f}km")

    smart_minx = minx - smart_buffer
    smart_miny = miny - smart_buffer
    smart_maxx = maxx + smart_buffer
    smart_maxy = maxy + smart_buffer

    smart_width = smart_maxx - smart_minx
    smart_height = smart_maxy - smart_miny

    smart_grid_width = int(np.ceil(smart_width / resolution_m))
    smart_grid_height = int(np.ceil(smart_height / resolution_m))
    smart_total_pixels = smart_grid_width * smart_grid_height

    print(f"   Smart grid: {smart_grid_height} × {smart_grid_width}")
    print(f"   Smart total pixels: {smart_total_pixels:,}")
    print(f"   Reduction: {100 * (1 - smart_total_pixels / total_pixels):.1f}%")


def main():
    """Debug all three pilot fires."""
    print("🔍 Grid Bounds Debug Analysis")
    print("=" * 70)

    fires = [
        ("Carlton Complex", 2014, "EPSG:32610"),  # UTM 10N
        ("KING", 2014, "EPSG:32610"),  # UTM 10N
        ("Big Cougar", 2014, "EPSG:32611"),  # UTM 11N
    ]

    for fire_name, fire_year, target_crs in fires:
        try:
            debug_fire_bounds(fire_name, fire_year, target_crs)
        except Exception as e:
            print(f"\n❌ Error debugging {fire_name}: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("📊 ANALYSIS COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
