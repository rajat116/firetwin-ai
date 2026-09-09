"""USGS 3DEP elevation data client via The National Map API.

Official documentation:
- 3DEP: https://www.usgs.gov/3d-elevation-program
- The National Map: https://apps.nationalmap.gov/tnmaccess
- API Docs: https://apps.nationalmap.gov/tnmaccess/#/product

3DEP provides high-resolution elevation data:
- 1/3 arc-second (~10m) for CONUS
- 1 arc-second (~30m) for Alaska
- Various products: DEM, DSM, DTM, Hillshade

Data available as GeoTIFF files via The National Map API.
"""

import re
from datetime import date
from pathlib import Path

import numpy as np
import requests
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT

from firetwin.schemas.core import TerrainData


class USGS3DEPClient:
    """Client for USGS 3DEP elevation data via The National Map API."""

    # The National Map API endpoint
    BASE_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"
    DEFAULT_DATASET = "National Elevation Dataset (NED) 1 arc-second"
    HIGH_RES_DATASET = "National Elevation Dataset (NED) 1/3 arc-second"
    TILE_PATTERN = re.compile(r"n\d{2}[ew]\d{3}", re.IGNORECASE)

    def __init__(self, timeout: int = 300) -> None:
        """Initialize USGS 3DEP client.

        Args:
            timeout: HTTP request timeout in seconds (default: 300 for large files)
        """
        self.timeout = timeout

    def search_datasets(
        self,
        bbox: tuple[float, float, float, float],
        dataset: str = DEFAULT_DATASET,
        product_format: str = "GeoTIFF",
    ) -> list[dict]:
        """Search for available 3DEP datasets in bounding box.

        Args:
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            dataset: TNM dataset name
            product_format: Product file format

        Returns:
            List of dataset metadata dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        params = {
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "datasets": dataset,
            "prodFormats": product_format,
            "outputFormat": "JSON",
            "max": 500,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        items: list[dict] = data.get("items", [])
        return items

    @classmethod
    def _tile_key(cls, item: dict) -> str | None:
        """Extract the 1-degree DEM tile key from a TNM product."""
        text = " ".join(str(item.get(field, "")) for field in ("downloadURL", "title"))
        match = cls.TILE_PATTERN.search(text)
        if match is None:
            return None
        return match.group(0).lower()

    @staticmethod
    def _publication_date(item: dict) -> date:
        """Parse product publication date, falling back to the oldest valid date."""
        value = str(item.get("publicationDate") or "")
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return date.min

    @classmethod
    def select_latest_geotiff_tiles(cls, items: list[dict]) -> list[dict]:
        """Select the newest GeoTIFF product for each DEM tile.

        TNM often returns multiple historical versions for the same 1-degree
        tile. For reproducible current terrain builds, keep only the newest
        publication date per tile.
        """
        latest_by_tile: dict[str, dict] = {}

        for item in items:
            download_url = item.get("downloadURL")
            if not download_url:
                continue
            if item.get("format") and item.get("format") != "GeoTIFF":
                continue

            tile_key = cls._tile_key(item)
            if tile_key is None:
                continue

            current = latest_by_tile.get(tile_key)
            if current is None or cls._publication_date(item) > cls._publication_date(current):
                latest_by_tile[tile_key] = item

        return [latest_by_tile[key] for key in sorted(latest_by_tile)]

    def download_dataset(
        self,
        dataset_url: str,
        output_path: Path,
    ) -> Path:
        """Download a specific 3DEP dataset.

        Args:
            dataset_url: Direct download URL from search results
            output_path: Output file path for downloaded GeoTIFF

        Returns:
            Path to downloaded file

        Raises:
            requests.HTTPError: If download fails
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(dataset_url, stream=True, timeout=self.timeout)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def download_bbox(
        self,
        bbox: tuple[float, float, float, float],
        output_dir: Path,
        dataset: str = DEFAULT_DATASET,
    ) -> list[Path]:
        """Search and download all 3DEP tiles for a bounding box.

        Args:
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            output_dir: Output directory for downloaded files
            dataset: Dataset name

        Returns:
            List of downloaded file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Search for datasets
        try:
            datasets = self.select_latest_geotiff_tiles(
                self.search_datasets(bbox=bbox, dataset=dataset)
            )
        except requests.RequestException:
            cached_files = sorted(output_dir.glob("*.tif"))
            if cached_files:
                return cached_files
            raise

        downloaded_files: list[Path] = []

        # Download each dataset
        for ds in datasets:
            download_url = ds.get("downloadURL")
            if not download_url:
                continue

            # Generate output filename from dataset title
            title = ds.get("title", "dem")
            safe_title = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)
            output_path = output_dir / f"{safe_title}.tif"

            if output_path.exists() and output_path.stat().st_size > 0:
                downloaded_files.append(output_path)
                continue

            self.download_dataset(download_url, output_path)
            downloaded_files.append(output_path)

        return downloaded_files

    def load_aligned_dem(
        self,
        dem_paths: list[Path],
        grid_bounds: tuple[float, float, float, float],
        grid_shape: tuple[int, int],
        target_crs: str,
    ) -> np.ndarray:
        """Load DEM tiles and resample them onto a target model grid.

        Args:
            dem_paths: Source DEM GeoTIFF paths
            grid_bounds: Target bounds as (minx, miny, maxx, maxy)
            grid_shape: Target shape as (height, width)
            target_crs: Target CRS, for example EPSG:32610

        Returns:
            Float32 elevation grid in meters aligned to the target grid
        """
        if not dem_paths:
            raise ValueError("At least one DEM path is required")

        import rasterio

        height, width = grid_shape
        transform = from_bounds(*grid_bounds, width, height)
        mosaic = np.full((height, width), np.nan, dtype=np.float32)

        for dem_path in dem_paths:
            with rasterio.open(dem_path) as src:
                nodata = src.nodata
                with WarpedVRT(
                    src,
                    crs=target_crs,
                    transform=transform,
                    width=width,
                    height=height,
                    resampling=Resampling.bilinear,
                    src_nodata=nodata,
                    nodata=np.nan,
                    dtype="float32",
                ) as vrt:
                    data = vrt.read(1, masked=True).astype(np.float32)
                    aligned = data.filled(np.nan)
                    valid = np.isfinite(aligned)
                    mosaic[valid] = aligned[valid]

        if not np.isfinite(mosaic).all():
            missing = int(np.size(mosaic) - np.count_nonzero(np.isfinite(mosaic)))
            raise ValueError(f"DEM coverage incomplete for target grid ({missing} missing cells)")

        return mosaic.astype(np.float32)

    @staticmethod
    def derive_slope_aspect(
        elevation_m: np.ndarray,
        resolution_m: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Derive slope and downslope aspect from an elevation grid."""
        dz_drow, dz_dcol = np.gradient(elevation_m.astype(np.float32), resolution_m, resolution_m)
        slope_degrees = np.degrees(np.arctan(np.hypot(dz_dcol, dz_drow))).astype(np.float32)
        aspect_degrees = ((np.degrees(np.arctan2(-dz_dcol, dz_drow)) + 360.0) % 360.0).astype(
            np.float32
        )
        aspect_degrees[slope_degrees < 1e-6] = 0.0
        return slope_degrees, aspect_degrees

    def build_terrain_data(
        self,
        bbox: tuple[float, float, float, float],
        grid_bounds: tuple[float, float, float, float],
        grid_shape: tuple[int, int],
        target_crs: str,
        resolution_m: float,
        output_dir: Path,
        dataset: str = DEFAULT_DATASET,
    ) -> TerrainData:
        """Download, align, and derive terrain layers for a FireTwin grid."""
        from firetwin.schemas.core import BoundingBox, CoordinateSystem

        dem_paths = self.download_bbox(bbox=bbox, output_dir=output_dir, dataset=dataset)
        elevation_m = self.load_aligned_dem(
            dem_paths=dem_paths,
            grid_bounds=grid_bounds,
            grid_shape=grid_shape,
            target_crs=target_crs,
        )
        slope_degrees, aspect_degrees = self.derive_slope_aspect(elevation_m, resolution_m)

        minx, miny, maxx, maxy = grid_bounds
        return TerrainData(
            elevation_m=elevation_m,
            slope_degrees=slope_degrees,
            aspect_degrees=aspect_degrees,
            resolution_m=resolution_m,
            bbox=BoundingBox(
                min_x=minx,
                max_x=maxx,
                min_y=miny,
                max_y=maxy,
                crs=CoordinateSystem(target_crs),
            ),
        )

    @staticmethod
    def list_available_datasets() -> dict[str, str]:
        """Get dictionary of available 3DEP datasets.

        Returns:
            Dict mapping dataset names to descriptions
        """
        return {
            "National Elevation Dataset (NED) 1 arc-second": "~30m resolution DEM",
            "National Elevation Dataset (NED) 1/3 arc-second": "~10m resolution DEM for CONUS",
            "Digital Surface Model (DSM) 1 meter": "1m lidar-derived surface model",
            "Hillshade 1/3 arc-second": "Shaded relief visualization",
        }
