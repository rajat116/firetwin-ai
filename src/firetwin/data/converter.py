"""Convert real data from API clients to canonical FireCase format.

This module orchestrates the transformation of raw data from multiple sources
(NIFC, MTBS, FIRMS, ERA5, USGS, LANDFIRE) into the canonical FireCase schema.
"""

from datetime import datetime, timedelta
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
from firetwin.settings import settings

PLACEHOLDER_COVARIATE_LIMITATIONS = [
    "Terrain is placeholder flat elevation, not USGS 3DEP.",
    "Fuel grids are placeholder uniform FBFM 10, not LANDFIRE.",
    "Weather is a placeholder scalar condition, not ERA5-Land.",
    "Target state is final burned extent, not time-resolved fire progression.",
]

REAL_TERRAIN_LIMITATIONS = [
    "Terrain is real USGS 3DEP elevation resampled to the FireTwin grid.",
    "Fuel grids are placeholder uniform FBFM 10, not LANDFIRE.",
    "Weather is a placeholder scalar condition, not ERA5-Land.",
    "Target state is final burned extent, not time-resolved fire progression.",
]

REAL_FUELS_LIMITATIONS = [
    "Terrain is placeholder flat elevation, not USGS 3DEP.",
    "Fuel model is real LANDFIRE LF2022 FBFM40 resampled to the FireTwin grid.",
    "Fuel load and moisture are deterministic proxies derived from FBFM40 classes, not live fuel observations.",
    "Weather is a placeholder scalar condition, not ERA5-Land.",
    "Target state is final burned extent, not time-resolved fire progression.",
]

REAL_TERRAIN_FUELS_LIMITATIONS = [
    "Terrain is real USGS 3DEP elevation resampled to the FireTwin grid.",
    "Fuel model is real LANDFIRE LF2022 FBFM40 resampled to the FireTwin grid.",
    "Fuel load and moisture are deterministic proxies derived from FBFM40 classes, not live fuel observations.",
    "Weather is a placeholder scalar condition, not ERA5-Land.",
    "Target state is final burned extent, not time-resolved fire progression.",
]

REAL_TERRAIN_FUELS_WEATHER_LIMITATIONS = [
    "Terrain is real USGS 3DEP elevation resampled to the FireTwin grid.",
    "Fuel model is real LANDFIRE LF2022 FBFM40 resampled to the FireTwin grid.",
    "Fuel load and moisture are deterministic proxies derived from FBFM40 classes, not live fuel observations.",
    "Weather is real ERA5-Land hourly reanalysis summarized to a scalar AOI mean.",
    "Target state is final burned extent, not time-resolved fire progression.",
    "Initial state is still an empty placeholder until ignition/progression observations are reconstructed.",
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
        weather_start: datetime | None = None,
        weather_end: datetime | None = None,
    ) -> None:
        """Initialize converter.

        Args:
            fire_name: Name of the fire incident
            fire_year: Fire year
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) in WGS84
            target_resolution_m: Target grid resolution in meters
            target_crs: Target CRS for modeling (should be projected, not geographic)
            weather_start: Optional weather reference/window start time
            weather_end: Optional weather window end time (default: start + 23 hours)
        """
        self.fire_name = fire_name
        self.fire_year = fire_year
        self.bbox = bbox
        self.target_resolution_m = target_resolution_m
        self.target_crs = target_crs
        self.weather_start = weather_start
        self.weather_end = weather_end

        # Initialize clients (some are optional)
        self.nifc_historical = NIFCHistoricalClient()
        self.mtbs = MTBSClient()

        # Optional clients (may require API keys/credentials)
        self.firms: FIRMSClient | None
        try:
            self.firms = FIRMSClient()
        except ValueError:
            self.firms = None  # No API key

        self.era5: ERA5LandClient | None = None

        self.usgs = USGS3DEPClient()
        self.landfire = LANDFIREClient()

        # Data storage
        self.raw_data: dict = {}
        self.aligned_data: dict = {}

    def _get_era5_client(self) -> ERA5LandClient | None:
        """Create the ERA5 client only when weather data is actually fetched."""
        if self.era5 is not None:
            return self.era5

        try:
            if settings.cds_api_key:
                self.era5 = ERA5LandClient(url=settings.cds_api_url, key=settings.cds_api_key)
            else:
                self.era5 = ERA5LandClient()
        except Exception:
            self.era5 = None

        return self.era5

    def _weather_window(self) -> tuple[datetime, datetime] | None:
        """Return the weather download/summarization window if one can be inferred."""
        if self.weather_start is not None:
            weather_end = self.weather_end or (self.weather_start + timedelta(hours=23))
            return self.weather_start, weather_end

        mtbs = self.raw_data.get("mtbs_fires")
        if mtbs is not None and "ignition_date" in mtbs:
            ignition_dates = mtbs["ignition_date"].dropna()
            if len(ignition_dates) > 0:
                earliest = min(ignition_dates)
                start = earliest.to_pydatetime() if hasattr(earliest, "to_pydatetime") else earliest
                return start, start + timedelta(hours=23)

        return None

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
        era5 = self._get_era5_client()
        if era5 is None:
            print("   ℹ️  ERA5 requires CDS credentials (skipped)")
        else:
            weather_window = self._weather_window()
            if weather_window is None:
                print("   ℹ️  No defensible weather reference time available (skipped)")
            else:
                start, end = weather_window
                case_id = f"{self.fire_name.lower().replace(' ', '_')}_{self.fire_year}"
                output_path = (
                    Path("data/raw/era5") / case_id / f"era5land_{start:%Y%m%d%H}_{end:%Y%m%d%H}.nc"
                )
                try:
                    weather = era5.build_weather_data(
                        bbox=self.bbox,
                        start_datetime=start,
                        end_datetime=end,
                        output_path=output_path,
                    )
                    self.aligned_data["weather"] = weather
                    print(
                        "   ✅ Real ERA5-Land weather summarized: "
                        f"{weather.temperature_c:.1f}°C, RH {weather.relative_humidity_percent:.0f}%, "
                        f"wind {weather.wind_speed_m_s:.1f} m/s from {weather.wind_direction_degrees:.0f}°"
                    )
                except Exception as e:
                    print(
                        f"   ⚠️  ERA5 weather unavailable; falling back to placeholder weather: {e}"
                    )

        # 5. USGS 3DEP elevation
        print("\n5️⃣  Checking USGS 3DEP elevation...")
        print("   ℹ️  USGS DEM tiles are downloaded, cached, and aligned after grid creation")

        # 6. LANDFIRE fuels
        print("\n6️⃣  Checking LANDFIRE fuels...")
        print("   ℹ️  LANDFIRE FBFM40 is exported, cached, and aligned after grid creation")

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

        # 4. Align real USGS terrain to the target grid. This happens after
        # grid creation because DEMs must be resampled onto the exact model grid.
        if "grid_shape" in self.aligned_data and "grid_bounds" in self.aligned_data:
            print("\n🏔️  Aligning USGS 3DEP terrain...")
            case_id = f"{self.fire_name.lower().replace(' ', '_')}_{self.fire_year}"
            output_dir = Path("data/raw/3dep") / case_id
            try:
                terrain = self.usgs.build_terrain_data(
                    bbox=self.bbox,
                    grid_bounds=self.aligned_data["grid_bounds"],
                    grid_shape=self.aligned_data["grid_shape"],
                    target_crs=self.target_crs,
                    resolution_m=self.target_resolution_m,
                    output_dir=output_dir,
                )
                self.aligned_data["terrain"] = terrain
                elev = terrain.elevation_m
                slope = terrain.slope_degrees
                print(
                    "   ✅ Real terrain aligned: "
                    f"elevation {float(np.nanmin(elev)):.0f}-{float(np.nanmax(elev)):.0f}m, "
                    f"slope mean {float(np.nanmean(slope)):.1f}°"
                )
            except Exception as e:
                print(f"   ⚠️  USGS terrain unavailable; falling back to placeholder terrain: {e}")

            print("\n🌲 Aligning LANDFIRE LF2022 FBFM40 fuels...")
            landfire_output_dir = Path("data/raw/landfire") / case_id
            try:
                fuels = self.landfire.build_fuel_data(
                    grid_bounds=self.aligned_data["grid_bounds"],
                    grid_shape=self.aligned_data["grid_shape"],
                    target_crs=self.target_crs,
                    resolution_m=self.target_resolution_m,
                    output_dir=landfire_output_dir,
                )
                self.aligned_data["fuels"] = fuels
                fuel_codes = fuels.fuel_model
                burnable_fraction = np.count_nonzero(fuel_codes) / fuel_codes.size * 100
                unique_codes = np.unique(fuel_codes)
                print(
                    "   ✅ Real LANDFIRE fuels aligned: "
                    f"{len(unique_codes)} classes, {burnable_fraction:.1f}% burnable cells"
                )
            except Exception as e:
                print(f"   ⚠️  LANDFIRE fuels unavailable; falling back to placeholder fuels: {e}")

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
        has_real_terrain = "terrain" in self.aligned_data
        has_real_fuels = "fuels" in self.aligned_data
        has_real_weather = "weather" in self.aligned_data
        if has_real_terrain and has_real_fuels and has_real_weather:
            description = (
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; terrain is USGS 3DEP; fuel model is LANDFIRE LF2022 FBFM40; "
                "weather is ERA5-Land; initial fire state is a placeholder."
            )
            data_quality = "phase4c_real_terrain_fuels_weather_final_extent"
            source = "NIFC/MTBS/USGS 3DEP/LANDFIRE/ERA5-Land"
            tags = [
                "real_data",
                "final_extent_only",
                "real_terrain",
                "real_fbfm40",
                "real_weather",
                "proxy_fuel_properties",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ]
            covariate_status = "partial_real_terrain_fuels_weather"
            limitations = REAL_TERRAIN_FUELS_WEATHER_LIMITATIONS
            covariate_sources = {
                "terrain": "USGS 3DEP National Elevation Dataset (NED) 1 arc-second GeoTIFF via TNM",
                "fuel_model": LANDFIREClient.FUEL_MODEL_SOURCE,
                "fuel_load_kg_m2": "derived_proxy_from_landfire_fbfm40_class",
                "fuel_moisture_percent": "static_proxy_from_landfire_fbfm40_class",
                "weather": ERA5LandClient.WEATHER_SOURCE,
                "weather_spatial_resolution": "0.1 degree grid; native resolution about 9 km",
                "weather_summary": "AOI mean at nearest requested hourly timestamp",
                "initial_state": "placeholder_empty_no_ignition_time",
            }
        elif has_real_terrain and has_real_fuels:
            description = (
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; terrain is USGS 3DEP; fuel model is LANDFIRE LF2022 FBFM40; "
                "weather and initial fire state are placeholders."
            )
            data_quality = "phase4b_real_terrain_fuels_final_extent"
            source = "NIFC/MTBS/USGS 3DEP/LANDFIRE"
            tags = [
                "real_data",
                "final_extent_only",
                "real_terrain",
                "real_fbfm40",
                "proxy_fuel_properties",
                "placeholder_weather",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ]
            covariate_status = "partial_real_terrain_fuels"
            limitations = REAL_TERRAIN_FUELS_LIMITATIONS
            covariate_sources = {
                "terrain": "USGS 3DEP National Elevation Dataset (NED) 1 arc-second GeoTIFF via TNM",
                "fuel_model": LANDFIREClient.FUEL_MODEL_SOURCE,
                "fuel_load_kg_m2": "derived_proxy_from_landfire_fbfm40_class",
                "fuel_moisture_percent": "static_proxy_from_landfire_fbfm40_class",
                "weather": "placeholder_scalar_moderate_conditions",
                "initial_state": "placeholder_empty_no_ignition_time",
            }
        elif has_real_terrain:
            description = (
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; terrain is USGS 3DEP; fuels and weather are placeholders."
            )
            data_quality = "phase4a_real_terrain_final_extent"
            source = "NIFC/MTBS/USGS 3DEP"
            tags = [
                "real_data",
                "final_extent_only",
                "real_terrain",
                "placeholder_fuels",
                "placeholder_weather",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ]
            covariate_status = "partial_real_terrain"
            limitations = REAL_TERRAIN_LIMITATIONS
            covariate_sources = {
                "terrain": "USGS 3DEP National Elevation Dataset (NED) 1 arc-second GeoTIFF via TNM",
                "fuels": "placeholder_uniform_fbfm_10",
                "weather": "placeholder_scalar_moderate_conditions",
                "initial_state": "placeholder_empty_no_ignition_time",
            }
        elif has_real_fuels:
            description = (
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; fuel model is LANDFIRE LF2022 FBFM40; "
                "terrain, weather and initial fire state are placeholders."
            )
            data_quality = "phase4b_real_fuels_final_extent"
            source = "NIFC/MTBS/LANDFIRE"
            tags = [
                "real_data",
                "final_extent_only",
                "placeholder_terrain",
                "real_fbfm40",
                "proxy_fuel_properties",
                "placeholder_weather",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ]
            covariate_status = "partial_real_fuels"
            limitations = REAL_FUELS_LIMITATIONS
            covariate_sources = {
                "terrain": "placeholder_flat_1000m",
                "fuel_model": LANDFIREClient.FUEL_MODEL_SOURCE,
                "fuel_load_kg_m2": "derived_proxy_from_landfire_fbfm40_class",
                "fuel_moisture_percent": "static_proxy_from_landfire_fbfm40_class",
                "weather": "placeholder_scalar_moderate_conditions",
                "initial_state": "placeholder_empty_no_ignition_time",
            }
        else:
            description = (
                f"Real final-extent fire case from {self.fire_name} fire in {self.fire_year}. "
                "Perimeter is real; terrain, fuels, and weather are placeholders."
            )
            data_quality = "phase3_final_extent_only"
            source = "NIFC/MTBS"
            tags = [
                "real_data",
                "final_extent_only",
                "placeholder_covariates",
                "placeholder_fuels",
                "placeholder_weather",
                f"year_{self.fire_year}",
                self.fire_name.lower().replace(" ", "_"),
            ]
            covariate_status = "placeholder"
            limitations = PLACEHOLDER_COVARIATE_LIMITATIONS
            covariate_sources = {
                "terrain": "placeholder_flat_1000m",
                "fuels": "placeholder_uniform_fbfm_10",
                "weather": "placeholder_scalar_moderate_conditions",
                "initial_state": "placeholder_empty_no_ignition_time",
            }

        metadata = FireCaseMetadata(
            case_id=case_id,
            name=f"{self.fire_name} ({self.fire_year})",
            description=description,
            is_synthetic=False,
            creation_timestamp=datetime.utcnow(),
            source=source,
            tags=tags,
            target_type="final_burned_extent",
            data_quality=data_quality,
            covariate_status=covariate_status,
            limitations=limitations,
            covariate_sources=covariate_sources,
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

        # 2. Create TerrainData
        if has_real_terrain:
            print("   ✅ Using real USGS 3DEP terrain")
            terrain = self.aligned_data["terrain"]
        else:
            print("   ⚠️  Using placeholder terrain (flat at 1000m elevation)")
            terrain = TerrainData(
                elevation_m=np.full((height, width), 1000.0, dtype=np.float32),
                slope_degrees=np.zeros((height, width), dtype=np.float32),
                aspect_degrees=np.zeros((height, width), dtype=np.float32),
                resolution_m=self.target_resolution_m,
                bbox=bbox_obj,
            )

        # 3. Create FuelData
        if has_real_fuels:
            print("   ✅ Using real LANDFIRE LF2022 FBFM40 fuel model")
            fuels = self.aligned_data["fuels"]
        else:
            print("   ⚠️  Using placeholder fuels (uniform FBFM 10)")
            fuels = FuelData(
                fuel_model=np.full((height, width), 10, dtype=np.int32),  # FBFM 10: Timber
                fuel_load_kg_m2=np.full((height, width), 2.0, dtype=np.float32),
                fuel_moisture_percent=np.full((height, width), 8.0, dtype=np.float32),
                resolution_m=self.target_resolution_m,
            )

        # 4. Create WeatherData
        if has_real_weather:
            print("   ✅ Using real ERA5-Land weather")
            weather = self.aligned_data["weather"]
        else:
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
