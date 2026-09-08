"""Convert real data from API clients to canonical FireCase format.

This module orchestrates the transformation of raw data from multiple sources
(NIFC, MTBS, FIRMS, ERA5, USGS, LANDFIRE) into the canonical FireCase schema.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_bounds

from firetwin.data.clients import (
    ERA5LandClient,
    FIRMSClient,
    LANDFIREClient,
    MTBSClient,
    NIFCHistoricalClient,
    USGS3DEPClient,
)
from firetwin.schemas.core import FireState, FuelData, TerrainData, WeatherData
from firetwin.schemas.fire_case import FireCase, FireCaseMetadata

PLACEHOLDER_COVARIATE_LIMITATIONS = [
    "Terrain is placeholder flat elevation, not USGS 3DEP.",
    "Fuel grids are placeholder uniform FBFM 10, not LANDFIRE.",
    "Weather is a placeholder scalar condition, not ERA5-Land.",
    "Target state is final burned extent, not time-resolved fire progression.",
]


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
                # Filter perimeters to those within the target bbox
                # This prevents getting fires with similar names from other regions
                min_lon, min_lat, max_lon, max_lat = self.bbox

                gdf = self.nifc_historical.perimeters_to_geodataframe(perimeters)

                # Filter by bbox
                gdf_filtered = gdf.cx[min_lon:max_lon, min_lat:max_lat]

                if len(gdf_filtered) > 0:
                    self.raw_data["nifc_perimeters"] = gdf_filtered
                    if len(gdf_filtered) < len(gdf):
                        print(
                            f"   ✅ Found {len(gdf_filtered)} perimeter(s) in bbox (filtered from {len(gdf)})"
                        )
                    else:
                        print(f"   ✅ Found {len(gdf_filtered)} perimeter(s)")
                else:
                    print(f"   ⚠️  Found {len(gdf)} perimeter(s) but none in target bbox")
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

                # Filter by bbox
                min_lon, min_lat, max_lon, max_lat = self.bbox
                gdf_filtered = gdf.cx[min_lon:max_lon, min_lat:max_lat]

                if len(gdf_filtered) > 0:
                    self.raw_data["mtbs_fires"] = gdf_filtered
                    if len(gdf_filtered) < len(gdf):
                        print(
                            f"   ✅ Found {len(gdf_filtered)} MTBS fire(s) in bbox (filtered from {len(gdf)})"
                        )
                    else:
                        print(f"   ✅ Found {len(gdf_filtered)} MTBS fire(s)")
                else:
                    print(f"   ⚠️  Found {len(gdf)} MTBS fire(s) but none in target bbox")
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

        if not self.raw_data:
            print("   ⚠️  No data to align")
            return

        # 1. Reproject fire perimeter to target CRS
        if "nifc_perimeters" in self.raw_data:
            gdf = self.raw_data["nifc_perimeters"]
            gdf_proj = gdf.to_crs(self.target_crs)
            self.aligned_data["fire_perimeter"] = gdf_proj
            print(f"   ✅ Reprojected NIFC perimeter to {self.target_crs}")
        elif "mtbs_fires" in self.raw_data:
            gdf = self.raw_data["mtbs_fires"]
            gdf_proj = gdf.to_crs(self.target_crs)
            self.aligned_data["fire_perimeter"] = gdf_proj
            print(f"   ✅ Reprojected MTBS perimeter to {self.target_crs}")

        # 2. Compute target grid bounds in projected CRS
        if "fire_perimeter" in self.aligned_data:
            gdf_proj = self.aligned_data["fire_perimeter"]
            bounds = gdf_proj.total_bounds  # (minx, miny, maxx, maxy)

            # Smart buffer: 10% of fire dimension, max 5km
            # This prevents huge buffers for large fires
            fire_area_m2 = gdf_proj.geometry.area.sum()
            fire_dimension = np.sqrt(fire_area_m2)  # Approximate side length
            buffer_m = min(fire_dimension * 0.1, 5000)  # Max 5km buffer

            print(f"   📏 Fire area: {fire_area_m2 / 1e6:.1f} km²")
            print(f"   📏 Buffer: {buffer_m:,.0f}m ({buffer_m / 1000:.1f}km)")

            minx = bounds[0] - buffer_m
            miny = bounds[1] - buffer_m
            maxx = bounds[2] + buffer_m
            maxy = bounds[3] + buffer_m

            # Compute grid dimensions
            width = int(np.ceil((maxx - minx) / self.target_resolution_m))
            height = int(np.ceil((maxy - miny) / self.target_resolution_m))

            # Adjust bounds to align with grid
            maxx = minx + width * self.target_resolution_m
            maxy = miny + height * self.target_resolution_m

            self.aligned_data["grid_bounds"] = (minx, miny, maxx, maxy)
            self.aligned_data["grid_shape"] = (height, width)
            self.aligned_data["transform"] = from_bounds(minx, miny, maxx, maxy, width, height)

            print(f"   ✅ Grid: {width}x{height} cells ({self.target_resolution_m}m resolution)")
            print(f"   📐 Bounds: {minx:.0f}, {miny:.0f} → {maxx:.0f}, {maxy:.0f}")

        # 3. Rasterize fire perimeter onto target grid
        if "fire_perimeter" in self.aligned_data and "grid_shape" in self.aligned_data:
            gdf_proj = self.aligned_data["fire_perimeter"]
            height, width = self.aligned_data["grid_shape"]
            transform = self.aligned_data["transform"]

            # Rasterize: 1 inside fire perimeter, 0 outside
            shapes = [(geom, 1) for geom in gdf_proj.geometry]
            burned_mask = rasterize(
                shapes,
                out_shape=(height, width),
                transform=transform,
                fill=0,
                dtype=np.uint8,
            )

            self.aligned_data["burned_mask"] = burned_mask
            burned_pixels = np.sum(burned_mask)
            total_pixels = height * width
            burned_fraction = burned_pixels / total_pixels * 100

            print(
                f"   ✅ Rasterized fire perimeter: {burned_pixels}/{total_pixels} pixels burned ({burned_fraction:.1f}%)"
            )

        print("   ✅ Layer alignment complete")

    def build_fire_case(self) -> FireCase | None:
        """Build canonical FireCase from aligned data.

        Returns:
            FireCase object if data is sufficient, None otherwise
        """
        print("\n🏗️  Building FireCase...")

        # Check minimum data requirements
        if "burned_mask" not in self.aligned_data:
            print("   ❌ Insufficient data: No aligned fire perimeter")
            return None

        height, width = self.aligned_data["grid_shape"]
        burned_mask = self.aligned_data["burned_mask"]

        # 1. Create metadata
        case_id = f"{self.fire_name.lower().replace(' ', '_')}_{self.fire_year}"
        metadata = FireCaseMetadata(
            case_id=case_id,
            name=f"{self.fire_name} ({self.fire_year})",
            description=(
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; terrain, fuels, and weather are placeholders."
            ),
            is_synthetic=False,
            creation_timestamp=datetime.utcnow(),
            source="NIFC/MTBS",
            tags=[
                "real_data",
                "final_extent_only",
                "placeholder_covariates",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ],
            target_type="final_burned_extent",
            data_quality="phase3_final_extent_only",
            covariate_status="placeholder",
            limitations=PLACEHOLDER_COVARIATE_LIMITATIONS,
        )

        # Create BoundingBox from aligned grid bounds
        from firetwin.schemas.core import BoundingBox, CoordinateSystem

        minx, miny, maxx, maxy = self.aligned_data["grid_bounds"]
        bbox_obj = BoundingBox(
            min_x=minx,
            max_x=maxx,
            min_y=miny,
            max_y=maxy,
            crs=CoordinateSystem(self.target_crs),
        )

        # 2. Create TerrainData (placeholder with flat terrain for now)
        print("   ⚠️  Using placeholder terrain (flat at 1000m elevation)")
        terrain = TerrainData(
            elevation_m=np.full((height, width), 1000.0, dtype=np.float32),
            slope_degrees=np.zeros((height, width), dtype=np.float32),
            aspect_degrees=np.zeros((height, width), dtype=np.float32),
            resolution_m=self.target_resolution_m,
            bbox=bbox_obj,
        )

        # 3. Create FuelData (placeholder with moderate fuel load)
        print("   ⚠️  Using placeholder fuels (uniform FBFM 10)")
        fuels = FuelData(
            fuel_model=np.full((height, width), 10, dtype=np.int32),  # FBFM 10: Timber
            fuel_load_kg_m2=np.full((height, width), 2.0, dtype=np.float32),
            fuel_moisture_percent=np.full((height, width), 8.0, dtype=np.float32),
            resolution_m=self.target_resolution_m,
        )

        # 4. Create WeatherData (placeholder with moderate conditions)
        print("   ⚠️  Using placeholder weather (moderate wind/temp)")
        weather = WeatherData(
            temperature_c=25.0,  # Scalar, not array
            relative_humidity_percent=30.0,
            wind_speed_m_s=5.0,
            wind_direction_degrees=270.0,  # West
            timestamp=datetime(self.fire_year, 7, 1),  # Placeholder date
        )

        # 5. Create initial FireState (no fire initially)
        print("   ✅ Creating initial state (no fire)")
        initial_state = FireState(
            timestamp=datetime(self.fire_year, 1, 1),  # Placeholder date
            burned=np.zeros((height, width), dtype=np.uint8),
            active_front=np.zeros((height, width), dtype=np.uint8),
            resolution_m=self.target_resolution_m,
            bbox=bbox_obj,
        )

        # 6. Create target state (final fire perimeter)
        print("   ✅ Creating target state (final perimeter)")
        target_state = FireState(
            timestamp=datetime(self.fire_year, 12, 31),  # Placeholder date
            burned=burned_mask.astype(np.uint8),
            active_front=np.zeros((height, width), dtype=np.uint8),  # No active front at end
            resolution_m=self.target_resolution_m,
            bbox=bbox_obj,
        )

        # 7. Build FireCase
        fire_case = FireCase(
            metadata=metadata,
            terrain=terrain,
            fuels=fuels,
            weather=weather,
            initial_state=initial_state,
            target_states=[target_state],
        )

        print(f"   ✅ Built FireCase: {case_id}")
        print(f"      Grid: {width}x{height} @ {self.target_resolution_m}m")
        print(f"      Burned area: {np.sum(burned_mask)} pixels")

        return fire_case

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
