"""Validate generated pilot fire cases.

This script validates that the generated fire cases:
1. Have correct metadata
2. Match expected fire sizes (within reasonable tolerance)
3. Have valid spatial properties and real terrain covariates
4. Are properly formatted
"""

from pathlib import Path

import numpy as np
import xarray as xr


def validate_fire_case(
    zarr_path: Path,
    expected_acres: float,
    expected_crs: str,
    require_real_terrain: bool = False,
    require_real_fuels: bool = False,
) -> dict:
    """Validate a single fire case.

    Args:
        zarr_path: Path to the zarr file
        expected_acres: Expected fire size in acres
        expected_crs: Expected target CRS
        require_real_terrain: If True, fail flat placeholder terrain
        require_real_fuels: If True, fail uniform placeholder fuels

    Returns:
        Dictionary with validation results
    """
    results = {"name": zarr_path.stem, "passed": [], "failed": [], "warnings": []}

    try:
        # Load the fire case
        ds = xr.open_zarr(zarr_path)

        # 1. Check metadata exists
        required_attrs = [
            "case_id",
            "name",
            "source",
            "is_synthetic",
            "resolution_m",
            "bbox_crs",
            "target_type",
            "covariate_status",
            "limitations",
            "covariate_sources",
        ]
        for attr in required_attrs:
            if attr in ds.attrs:
                results["passed"].append(f"✅ Metadata '{attr}' present")
            else:
                results["failed"].append(f"❌ Missing metadata '{attr}'")

        if ds.attrs.get("target_type") == "final_burned_extent":
            results["passed"].append("✅ Target type explicitly marked as final burned extent")
        else:
            results["failed"].append("❌ Target type is not marked as final_burned_extent")

        covariate_status = ds.attrs.get("covariate_status")
        if covariate_status == "placeholder":
            results["passed"].append("✅ Placeholder covariates explicitly marked")
        elif covariate_status == "partial_real_terrain":
            results["passed"].append("✅ Partial real covariates explicitly marked")
        elif covariate_status == "partial_real_fuels":
            results["passed"].append("✅ Partial real fuel covariates explicitly marked")
        elif covariate_status == "partial_real_terrain_fuels":
            results["passed"].append("✅ Partial real terrain/fuel covariates explicitly marked")
        else:
            results["failed"].append("❌ Covariate status is not explicit")

        if require_real_terrain and covariate_status not in (
            "partial_real_terrain",
            "partial_real_terrain_fuels",
        ):
            results["failed"].append(
                "❌ Real terrain is required but covariate status does not record real terrain"
            )
        if require_real_fuels and covariate_status != "partial_real_terrain_fuels":
            results["failed"].append(
                "❌ Real fuels are required but covariate status is not partial_real_terrain_fuels"
            )

        covariate_sources = ds.attrs.get("covariate_sources", "")
        if require_real_terrain and "USGS 3DEP" in covariate_sources:
            results["passed"].append("✅ Terrain source provenance records USGS 3DEP")
        elif require_real_terrain:
            results["failed"].append("❌ Terrain source provenance does not record USGS 3DEP")

        if require_real_fuels and "LANDFIRE LF2022 FBFM40" in covariate_sources:
            results["passed"].append("✅ Fuel source provenance records LANDFIRE LF2022 FBFM40")
        elif require_real_fuels:
            results["failed"].append("❌ Fuel source provenance does not record LANDFIRE FBFM40")

        if ds.attrs.get("bbox_crs") == expected_crs:
            results["passed"].append(f"✅ CRS matches expected {expected_crs}")
        else:
            results["failed"].append(
                f"❌ CRS mismatch: got {ds.attrs.get('bbox_crs')}, expected {expected_crs}"
            )

        # 2. Check grid properties
        resolution_m = ds.attrs.get("resolution_m", 100)
        if "x" in ds.sizes and "y" in ds.sizes:
            results["passed"].append(f"✅ Grid dimensions: {ds.sizes['y']} x {ds.sizes['x']}")
        else:
            results["failed"].append("❌ Missing x/y dimensions")

        if "time" in ds.sizes and ds.sizes["time"] >= 2:
            results["passed"].append(f"✅ Fire-state time axis has {ds.sizes['time']} states")
        else:
            results["failed"].append(
                "❌ Fire-state time axis must contain initial and target state"
            )

        # 3. Check burned area
        try:
            if "burned" in ds:
                initial = ds["burned"].isel(time=0).values
                burned = ds["burned"].isel(time=-1).values
            else:
                burned = None
                initial = None
                results["failed"].append("❌ No burned fire-state array found in dataset")

            if burned is not None:
                if initial is not None and np.sum(initial) == 0:
                    results["passed"].append("✅ Initial state is empty placeholder")
                elif initial is not None:
                    results["warnings"].append(
                        f"⚠️  Initial state has {int(np.sum(initial))} burned pixels"
                    )

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
            results["failed"].append(f"❌ Error reading burned states: {e}")

        # 4. Check terrain data
        if "elevation_m" in ds:
            elev = ds["elevation_m"].values
            if np.all(elev == 1000.0):
                message = "Terrain is placeholder (flat at 1000m)"
                if require_real_terrain:
                    results["failed"].append(f"❌ {message}")
                else:
                    results["warnings"].append(f"⚠️  {message}")
            else:
                elev_range = float(np.nanmax(elev) - np.nanmin(elev))
                if np.isfinite(elev).all() and elev_range > 1.0:
                    results["passed"].append(
                        f"✅ Terrain has real elevation variation ({elev_range:.0f}m range)"
                    )
                else:
                    results["failed"].append("❌ Terrain elevation is missing or nearly flat")

            if require_real_terrain:
                if "slope_degrees" in ds:
                    slope = ds["slope_degrees"].values
                    if np.isfinite(slope).all() and float(np.nanmax(slope)) > 0.1:
                        results["passed"].append(
                            f"✅ Slope is derived and non-flat (max {float(np.nanmax(slope)):.1f}°)"
                        )
                    else:
                        results["failed"].append("❌ Slope is missing, invalid, or flat")
                else:
                    results["failed"].append("❌ Missing slope data")

                if "aspect_degrees" in ds:
                    aspect = ds["aspect_degrees"].values
                    if np.isfinite(aspect).all() and np.all((aspect >= 0.0) & (aspect < 360.0)):
                        results["passed"].append("✅ Aspect is finite and within [0, 360)")
                    else:
                        results["failed"].append("❌ Aspect contains invalid values")
                else:
                    results["failed"].append("❌ Missing aspect data")
        else:
            results["failed"].append("❌ Missing elevation data")

        # 5. Check fuel data
        if "fuel_model" in ds:
            fuels = ds["fuel_model"].values.astype(np.int32)
            if np.all(fuels == 10):
                message = "Fuels are placeholder (uniform FBFM 10)"
                if require_real_fuels:
                    results["failed"].append(f"❌ {message}")
                else:
                    results["warnings"].append(f"⚠️  {message}")
            else:
                unique_fuels = np.unique(fuels)
                burnable = fuels > 0
                if require_real_fuels:
                    if unique_fuels.size > 1 and np.count_nonzero(burnable) > 0:
                        results["passed"].append(
                            f"✅ Fuels have real class variation ({unique_fuels.size} classes)"
                        )
                    else:
                        results["failed"].append("❌ Real fuels are missing class variation")

                    if "fuel_load_kg_m2" in ds and "fuel_moisture_percent" in ds:
                        load = ds["fuel_load_kg_m2"].values
                        moisture = ds["fuel_moisture_percent"].values
                        if (
                            np.isfinite(load).all()
                            and np.isfinite(moisture).all()
                            and np.all(load[burnable] > 0.0)
                            and np.all(moisture[burnable] > 0.0)
                            and np.all(load[~burnable] == 0.0)
                            and np.all(moisture[~burnable] == 0.0)
                        ):
                            results["passed"].append(
                                "✅ Fuel load/moisture proxies match burnable mask"
                            )
                        else:
                            results["failed"].append(
                                "❌ Fuel load/moisture proxies are inconsistent with fuel_model"
                            )
                    else:
                        results["failed"].append("❌ Missing fuel load/moisture grids")
                else:
                    results["passed"].append("✅ Fuels have variation")
        else:
            results["failed"].append("❌ Missing fuel data")

    except Exception as e:
        results["failed"].append(f"❌ Error loading fire case: {e}")

    return results


def main():
    """Validate all fire cases."""
    print("🔥 Pilot Fire Case Validation (Phase 4B terrain/fuels gate)")
    print("=" * 80)

    # Expected sizes (from PHASE3_PILOT_FIRES.md)
    fire_cases = [
        ("carlton_complex_2014", 251965, "EPSG:32610"),  # acres, CRS
        ("king_2014", 97685, "EPSG:32610"),
        ("big_cougar_2014", 65305, "EPSG:32611"),
    ]

    fire_cases_dir = Path("data/fire_cases")
    all_passed = True

    for case_id, expected_acres, expected_crs in fire_cases:
        zarr_path = fire_cases_dir / f"{case_id}.zarr"

        if not zarr_path.exists():
            print(f"\n❌ {case_id}: File not found")
            all_passed = False
            continue

        print(f"\n{'=' * 80}")
        print(f"🔥 {case_id.replace('_', ' ').title()}")
        print(f"{'=' * 80}")

        results = validate_fire_case(
            zarr_path,
            expected_acres,
            expected_crs,
            require_real_terrain=True,
            require_real_fuels=True,
        )

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
        print("   Phase 4B fire cases have real terrain and real LANDFIRE fuel models")
        return True
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("   Review issues above before completing the current phase")
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
