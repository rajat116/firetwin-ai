"""Validate generated fire cases for Phase 3 completion.

This script validates that the generated fire cases:
1. Have correct metadata
2. Match expected fire sizes (within reasonable tolerance)
3. Have valid spatial properties
4. Are properly formatted
"""

from pathlib import Path

import numpy as np
import xarray as xr


def validate_fire_case(zarr_path: Path, expected_acres: float) -> dict:
    """Validate a single fire case.

    Args:
        zarr_path: Path to the zarr file
        expected_acres: Expected fire size in acres

    Returns:
        Dictionary with validation results
    """
    results = {"name": zarr_path.stem, "passed": [], "failed": [], "warnings": []}

    try:
        # Load the fire case
        ds = xr.open_zarr(zarr_path)

        # 1. Check metadata exists
        required_attrs = ["case_id", "name", "source", "is_synthetic", "resolution_m"]
        for attr in required_attrs:
            if attr in ds.attrs:
                results["passed"].append(f"✅ Metadata '{attr}' present")
            else:
                results["failed"].append(f"❌ Missing metadata '{attr}'")

        # 2. Check grid properties
        resolution_m = ds.attrs.get("resolution_m", 100)
        if "x" in ds.dims and "y" in ds.dims:
            results["passed"].append(f"✅ Grid dimensions: {ds.dims['y']} x {ds.dims['x']}")
        else:
            results["failed"].append("❌ Missing x/y dimensions")

        # 3. Check burned area
        try:
            # Access via xarray directly - the zarr structure should be readable
            if "target_states" in ds:
                burned = ds["target_states"].sel(time=0)["burned"].values
            else:
                burned = None
                results["failed"].append("❌ No target_states found in dataset")

            if burned is not None:
                # Count burned pixels
                burned_pixels = int(np.sum(burned))
                total_pixels = burned.size
                burned_fraction = burned_pixels / total_pixels * 100

            # Calculate burned area
            pixel_area_m2 = resolution_m**2
            burned_area_m2 = burned_pixels * pixel_area_m2
            burned_area_acres = burned_area_m2 / 4046.86  # m² to acres
            burned_area_km2 = burned_area_m2 / 1e6

            results["burned_pixels"] = burned_pixels
            results["burned_fraction"] = burned_fraction
            results["burned_area_acres"] = burned_area_acres
            results["burned_area_km2"] = burned_area_km2

            # Compare to expected size
            error_percent = abs(burned_area_acres - expected_acres) / expected_acres * 100

            if error_percent < 10:
                results["passed"].append(
                    f"✅ Burned area: {burned_area_acres:,.0f} acres "
                    f"(expected {expected_acres:,.0f}, {error_percent:.1f}% error)"
                )
            elif error_percent < 30:
                results["warnings"].append(
                    f"⚠️  Burned area: {burned_area_acres:,.0f} acres "
                    f"(expected {expected_acres:,.0f}, {error_percent:.1f}% error)"
                )
            else:
                results["failed"].append(
                    f"❌ Burned area: {burned_area_acres:,.0f} acres "
                    f"(expected {expected_acres:,.0f}, {error_percent:.1f}% error)"
                )

            # Check if burned area is reasonable
            if burned_pixels > 0:
                results["passed"].append(
                    f"✅ Burned pixels: {burned_pixels:,} / {total_pixels:,} "
                    f"({burned_fraction:.1f}%)"
                )
            else:
                results["failed"].append("❌ No burned pixels found")

        except Exception as e:
            results["failed"].append(f"❌ Error reading target_states: {e}")

        # 4. Check terrain data
        if "elevation_m" in ds:
            elev = ds["elevation_m"].values
            if np.all(elev == 1000.0):
                results["warnings"].append("⚠️  Terrain is placeholder (flat at 1000m)")
            else:
                results["passed"].append("✅ Terrain has variation")
        else:
            results["failed"].append("❌ Missing elevation data")

        # 5. Check fuel data
        if "fuel_model" in ds:
            fuels = ds["fuel_model"].values
            if np.all(fuels == 10):
                results["warnings"].append("⚠️  Fuels are placeholder (uniform FBFM 10)")
            else:
                results["passed"].append("✅ Fuels have variation")
        else:
            results["failed"].append("❌ Missing fuel data")

        # 6. Check initial state
        try:
            if "initial_state" in ds:
                initial = ds["initial_state"].sel(time=0)["burned"].values
                if np.sum(initial) == 0:
                    results["passed"].append("✅ Initial state is empty (no fire)")
                else:
                    results["warnings"].append(
                        f"⚠️  Initial state has {np.sum(initial)} burned pixels"
                    )
            else:
                results["failed"].append("❌ No initial_state found in dataset")
        except Exception as e:
            results["failed"].append(f"❌ Error reading initial_state: {e}")

    except Exception as e:
        results["failed"].append(f"❌ Error loading fire case: {e}")

    return results


def main():
    """Validate all fire cases."""
    print("🔥 Phase 3 Fire Case Validation")
    print("=" * 80)

    # Expected sizes (from PHASE3_PILOT_FIRES.md)
    fire_cases = [
        ("carlton_complex_2014", 251965),  # acres
        ("king_2014", 97685),
        ("big_cougar_2014", 65305),
    ]

    fire_cases_dir = Path("data/fire_cases")
    all_passed = True

    for case_id, expected_acres in fire_cases:
        zarr_path = fire_cases_dir / f"{case_id}.zarr"

        if not zarr_path.exists():
            print(f"\n❌ {case_id}: File not found")
            all_passed = False
            continue

        print(f"\n{'=' * 80}")
        print(f"🔥 {case_id.replace('_', ' ').title()}")
        print(f"{'=' * 80}")

        results = validate_fire_case(zarr_path, expected_acres)

        # Print passed checks
        for msg in results["passed"]:
            print(msg)

        # Print warnings
        for msg in results["warnings"]:
            print(msg)

        # Print failures
        for msg in results["failed"]:
            print(msg)
            all_passed = False

        # Summary for this fire
        if "burned_area_km2" in results:
            print("\n📊 Summary:")
            print(f"   Burned Area: {results['burned_area_km2']:.1f} km²")
            print(f"   Grid Coverage: {results['burned_fraction']:.1f}%")

    # Overall summary
    print(f"\n{'=' * 80}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'=' * 80}")

    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("   Phase 3 fire cases are ready")
        return True
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("   Review issues above before completing Phase 3")
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
