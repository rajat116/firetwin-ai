"""Convert real data from API clients to canonical FireCase format.

This module orchestrates the transformation of raw data from multiple sources
(NIFC, MTBS, FIRMS, ERA5, USGS, LANDFIRE) into the canonical FireCase schema.
"""

from pathlib import Path

from firetwin.data.clients import (
    ERA5LandClient,
    FIRMSClient,
    LANDFIREClient,
    MTBSClient,
    NIFCHistoricalClient,
    USGS3DEPClient,
)
from firetwin.schemas.fire_case import FireCase


class RealFireCaseConverter:
    """Convert real wildfire data to canonical FireCase format.

    This class orchestrates:
    1. Spatial alignment (CRS, resolution, bbox)
    2. Temporal alignment (timestamps, time windows)
    3. Data reprojection and resampling
    4. Conversion to canonical schemas
    5. Quality validation
    """

    def __init__(
        self,
        fire_name: str,
        fire_year: int,
        bbox: tuple[float, float, float, float],
        target_resolution_m: float = 100.0,
        target_crs: str = "EPSG:32610",  # UTM Zone 10N for Western US
    ) -> None:
        """Initialize converter.

        Args:
            fire_name: Name of the fire incident
            fire_year: Fire year
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) in WGS84
            target_resolution_m: Target grid resolution in meters
            target_crs: Target CRS for modeling (should be projected, not geographic)
        """
        self.fire_name = fire_name
        self.fire_year = fire_year
        self.bbox = bbox
        self.target_resolution_m = target_resolution_m
        self.target_crs = target_crs

        # Initialize clients (some are optional)
        self.nifc_historical = NIFCHistoricalClient()
        self.mtbs = MTBSClient()

        # Optional clients (may require API keys/credentials)
        self.firms: FIRMSClient | None
        try:
            self.firms = FIRMSClient()
        except ValueError:
            self.firms = None  # No API key

        self.era5: ERA5LandClient | None
        try:
            self.era5 = ERA5LandClient()
        except Exception:
            self.era5 = None  # No CDS credentials

        self.usgs = USGS3DEPClient()
        self.landfire = LANDFIREClient()

        # Data storage
        self.raw_data: dict = {}
        self.aligned_data: dict = {}

    def fetch_all_data(self) -> None:
        """Fetch raw data from all sources."""
        print(f"🔥 Fetching data for {self.fire_name} ({self.fire_year})")
        print("=" * 70)

        # 1. Fire perimeters from NIFC Historical
        print("\n1️⃣  Fetching NIFC Historical perimeters...")
        try:
            perimeters = self.nifc_historical.get_fire_by_name(self.fire_name, year=self.fire_year)
            if perimeters:
                gdf = self.nifc_historical.perimeters_to_geodataframe(perimeters)
                self.raw_data["nifc_perimeters"] = gdf
                print(f"   ✅ Found {len(perimeters)} perimeter(s)")
            else:
                print("   ⚠️  No NIFC perimeters found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # 2. MTBS final perimeter (fallback if NIFC unavailable)
        print("\n2️⃣  Fetching MTBS final perimeter...")
        try:
            mtbs_fires = self.mtbs.get_fire_by_name(self.fire_name, year=self.fire_year)
            if mtbs_fires:
                gdf = self.mtbs.fires_to_geodataframe(mtbs_fires)
                self.raw_data["mtbs_fires"] = gdf
                print(f"   ✅ Found {len(mtbs_fires)} MTBS fire(s)")
            else:
                print("   ⚠️  No MTBS fires found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # 3. FIRMS active fire detections (skip if no key)
        print("\n3️⃣  Checking FIRMS detections...")
        if self.firms is None:
            print("   ℹ️  FIRMS requires API key (skipped)")
        else:
            print("   ℹ️  FIRMS client available but not fetched yet")

        # 4. ERA5-Land weather (skip if no credentials)
        print("\n4️⃣  Checking ERA5-Land weather...")
        if self.era5 is None:
            print("   ℹ️  ERA5 requires CDS credentials (skipped)")
        else:
            print("   ℹ️  ERA5 client available but not fetched yet")

        # 5. USGS 3DEP elevation
        print("\n5️⃣  Checking USGS 3DEP elevation...")
        print("   ℹ️  USGS elevation (to be implemented)")

        # 6. LANDFIRE fuels
        print("\n6️⃣  Checking LANDFIRE fuels...")
        print("   ℹ️  LANDFIRE requires manual download (skipped)")

        print("\n" + "=" * 70)
        print(f"📊 Data fetch complete: {len(self.raw_data)} sources available")

    def align_layers(self) -> None:
        """Align all layers to common grid, CRS, and resolution.

        This is the core spatial alignment step:
        - Reproject all layers to target_crs
        - Resample to target_resolution_m
        - Clip to common bbox
        - Ensure all arrays have same shape
        """
        print("\n🔧 Aligning layers to common grid...")
        print(f"   Target CRS: {self.target_crs}")
        print(f"   Target Resolution: {self.target_resolution_m}m")

        # Compute target grid bounds in projected CRS
        # (For now, just placeholder - will implement full reprojection)
        print("   ⚠️  Layer alignment not yet implemented")
        print("   TODO: Implement reprojection, resampling, clipping")

    def build_fire_case(self) -> FireCase | None:
        """Build canonical FireCase from aligned data.

        Returns:
            FireCase object if data is sufficient, None otherwise
        """
        print("\n🏗️  Building FireCase...")

        # Check minimum data requirements
        has_perimeter = "nifc_perimeters" in self.raw_data or "mtbs_fires" in self.raw_data

        if not has_perimeter:
            print("   ❌ Insufficient data: No fire perimeter available")
            return None

        print("   ⚠️  FireCase construction not yet implemented")
        print("   TODO: Convert raw data to TerrainData, FuelData, WeatherData, FireState")

        return None

    def save_fire_case(self, fire_case: FireCase, output_dir: Path) -> None:
        """Save FireCase to disk in Zarr format.

        Args:
            fire_case: FireCase to save
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        case_path = output_dir / f"{fire_case.metadata.case_id}.zarr"

        fire_case.save_to_zarr(case_path)
        print(f"\n💾 Saved FireCase to: {case_path}")

    def get_data_summary(self) -> dict:
        """Get summary of fetched data.

        Returns:
            Dictionary with data availability and statistics
        """
        data_sources: dict = {}

        if "nifc_perimeters" in self.raw_data:
            gdf = self.raw_data["nifc_perimeters"]
            data_sources["nifc_historical"] = {
                "available": True,
                "count": len(gdf),
                "total_acres": float(gdf["gis_acres"].sum()) if "gis_acres" in gdf.columns else 0,
            }

        if "mtbs_fires" in self.raw_data:
            gdf = self.raw_data["mtbs_fires"]
            data_sources["mtbs"] = {
                "available": True,
                "count": len(gdf),
                "total_acres": float(gdf["acres"].sum()) if "acres" in gdf.columns else 0,
            }

        return {
            "fire_name": self.fire_name,
            "fire_year": self.fire_year,
            "bbox": self.bbox,
            "data_sources": data_sources,
        }


def build_fire_case_from_real_data(
    fire_name: str,
    fire_year: int,
    bbox: tuple[float, float, float, float],
    output_dir: Path,
    target_resolution_m: float = 100.0,
) -> FireCase | None:
    """Convenience function to build a FireCase from real data.

    Args:
        fire_name: Name of the fire incident
        fire_year: Fire year
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) in WGS84
        output_dir: Directory to save the FireCase
        target_resolution_m: Target grid resolution in meters

    Returns:
        FireCase object if successful, None otherwise
    """
    converter = RealFireCaseConverter(
        fire_name=fire_name,
        fire_year=fire_year,
        bbox=bbox,
        target_resolution_m=target_resolution_m,
    )

    # Fetch data
    converter.fetch_all_data()

    # Align layers
    converter.align_layers()

    # Build FireCase
    fire_case = converter.build_fire_case()

    # Save if successful
    if fire_case:
        converter.save_fire_case(fire_case, output_dir)

    return fire_case
