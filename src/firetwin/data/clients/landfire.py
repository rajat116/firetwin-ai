"""LANDFIRE fuel and vegetation data client.

Official documentation:
- Portal: https://landfire.gov
- FBFM40: https://landfire.gov/fuel/fbfm40
- WCS/WMS: https://www.landfire.gov/data/lf_wcs_wms

LANDFIRE provides 30m resolution national fuel and vegetation datasets:
- Fuel Model (FBFM40, FBFM13)
- Canopy Cover, Height, Base Height, Bulk Density
- Vegetation Type, Height, Cover
- Topographic variables (Slope, Aspect, Elevation)

This client uses the public LF Product Service ArcGIS ImageServer export API
for grid-aligned FBFM40 GeoTIFF rasters.
"""

from pathlib import Path

import numpy as np
import requests
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT

from firetwin.schemas.core import FuelData


class LANDFIREClient:
    """Client for LANDFIRE fuel and vegetation data downloads.

    LANDFIRE exposes products through streaming services and LF Product Service
    REST endpoints. FireTwin currently uses the LF2022 CONUS FBFM40 ImageServer
    because it returns compact AOI GeoTIFFs directly aligned to model grids.
    """

    FBFM40_IMAGE_SERVER = (
        "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/LF2022_FBFM40_CONUS/ImageServer"
    )
    FUEL_MODEL_SOURCE = "LANDFIRE LF2022 FBFM40 CONUS ImageServer"
    NODATA_VALUE = -9999
    NON_BURNABLE_CODES = frozenset({NODATA_VALUE, 91, 92, 93, 98, 99})

    # Common LANDFIRE products for fire modeling
    FUEL_PRODUCTS = {
        "fbfm40": "40 Fire Behavior Fuel Models",
        "fbfm13": "13 Fire Behavior Fuel Models",
        "cc": "Canopy Cover",
        "ch": "Canopy Height",
        "cbh": "Canopy Base Height",
        "cbd": "Canopy Bulk Density",
        "asp": "Aspect",
        "slp": "Slope Degrees",
        "elev": "Elevation",
    }

    def __init__(self, timeout: int = 300) -> None:
        """Initialize LANDFIRE client.

        Args:
            timeout: HTTP request timeout in seconds (default: 300 for large files)
        """
        self.timeout = timeout

    def download_product(
        self,
        product: str,
        _version: str,
        _output_path: Path,
    ) -> Path:
        """Download a LANDFIRE product.

        Note: This is a simplified interface. For actual downloads, users should:
        1. Visit https://landfire.gov/getdata.php
        2. Define Area of Interest (AOI)
        3. Select products and version
        4. Download via web interface or direct links

        Args:
            product: Product code (e.g., 'fbfm40', 'cc', 'ch')
            version: LANDFIRE version (e.g., '2.3.0', '2.2.0')
            output_path: Output file path for downloaded GeoTIFF

        Returns:
            Path to downloaded file

        Raises:
            ValueError: If product is not recognized
            NotImplementedError: This is a placeholder for bulk download logic
        """
        if product not in self.FUEL_PRODUCTS:
            raise ValueError(
                f"Unknown product: {product}. Available: {list(self.FUEL_PRODUCTS.keys())}"
            )

        raise NotImplementedError(
            "Generic LANDFIRE product downloads are not implemented. "
            "Use export_fbfm40() for grid-aligned LF2022 FBFM40 GeoTIFF exports."
        )

    @staticmethod
    def _spatial_reference_id(crs: str) -> str:
        """Convert CRS strings such as EPSG:32610 to ArcGIS spatial reference IDs."""
        if crs.upper().startswith("EPSG:"):
            return crs.split(":", maxsplit=1)[1]
        return crs

    def export_fbfm40(
        self,
        grid_bounds: tuple[float, float, float, float],
        grid_shape: tuple[int, int],
        target_crs: str,
        output_path: Path,
    ) -> Path:
        """Export LF2022 FBFM40 for a target model grid as a GeoTIFF.

        Args:
            grid_bounds: Target bounds as (minx, miny, maxx, maxy)
            grid_shape: Target shape as (height, width)
            target_crs: Target CRS, for example EPSG:32610
            output_path: Output GeoTIFF path

        Returns:
            Path to the cached or downloaded GeoTIFF

        Raises:
            requests.HTTPError: If an HTTP request fails
            ValueError: If the export service returns no image URL
        """
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        height, width = grid_shape
        spatial_ref = self._spatial_reference_id(target_crs)
        minx, miny, maxx, maxy = grid_bounds

        params = {
            "f": "json",
            "bbox": f"{minx},{miny},{maxx},{maxy}",
            "bboxSR": spatial_ref,
            "imageSR": spatial_ref,
            "size": f"{width},{height}",
            "format": "tiff",
            "interpolation": "RSP_NearestNeighbor",
            "noData": str(self.NODATA_VALUE),
        }

        response = requests.get(
            f"{self.FBFM40_IMAGE_SERVER}/exportImage",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise ValueError(f"LANDFIRE export failed: {payload['error']}")

        href = payload.get("href")
        if not href:
            raise ValueError(f"LANDFIRE export response did not include an image URL: {payload}")

        image_response = requests.get(href, stream=True, timeout=self.timeout)
        image_response.raise_for_status()
        with open(output_path, "wb") as output_file:
            for chunk in image_response.iter_content(chunk_size=8192):
                output_file.write(chunk)

        return output_path

    @classmethod
    def normalize_fbfm40(cls, fbfm40: np.ndarray) -> np.ndarray:
        """Normalize raw FBFM40 codes for FireTwin burnability semantics.

        LANDFIRE non-burnable classes are valid categorical values, but many
        FireTwin baselines currently treat fuel_model > 0 as burnable. Convert
        those classes to 0 while preserving burnable FBFM40 class codes.
        """
        fuel_model = fbfm40.astype(np.int32, copy=True)
        fuel_model[np.isin(fuel_model, list(cls.NON_BURNABLE_CODES))] = 0
        fuel_model[fuel_model < 0] = 0
        return fuel_model

    def load_aligned_fbfm40(
        self,
        raster_path: Path,
        grid_bounds: tuple[float, float, float, float],
        grid_shape: tuple[int, int],
        target_crs: str,
    ) -> np.ndarray:
        """Load and nearest-neighbor align an FBFM40 raster to the model grid."""
        import rasterio

        height, width = grid_shape
        transform = from_bounds(*grid_bounds, width, height)

        with rasterio.open(raster_path) as src:
            nodata = src.nodata if src.nodata is not None else self.NODATA_VALUE
            with WarpedVRT(
                src,
                crs=target_crs,
                transform=transform,
                width=width,
                height=height,
                resampling=Resampling.nearest,
                src_nodata=nodata,
                nodata=self.NODATA_VALUE,
                dtype="int32",
            ) as vrt:
                data = vrt.read(1, masked=True)

        raw = data.filled(self.NODATA_VALUE).astype(np.int32)
        return self.normalize_fbfm40(raw)

    @staticmethod
    def derive_fuel_properties(
        fuel_model: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Derive simple static fuel-load and moisture proxy grids from FBFM40 codes.

        The fuel model layer is real LANDFIRE data. These two companion layers
        remain deterministic proxies until FireTwin adds live/dead fuel moisture
        and full fuelbed attributes.
        """
        codes = fuel_model.astype(np.int32)
        load = np.zeros(codes.shape, dtype=np.float32)
        moisture = np.zeros(codes.shape, dtype=np.float32)

        grass = (codes >= 101) & (codes <= 109)
        grass_shrub = (codes >= 121) & (codes <= 124)
        shrub = (codes >= 141) & (codes <= 149)
        timber_understory = (codes >= 161) & (codes <= 165)
        timber_litter = (codes >= 181) & (codes <= 189)
        slash_blowdown = (codes >= 201) & (codes <= 204)

        load[grass] = 0.25 + 0.08 * (codes[grass] - 101)
        load[grass_shrub] = 0.75 + 0.15 * (codes[grass_shrub] - 121)
        load[shrub] = 1.00 + 0.18 * (codes[shrub] - 141)
        load[timber_understory] = 1.35 + 0.25 * (codes[timber_understory] - 161)
        load[timber_litter] = 1.60 + 0.18 * (codes[timber_litter] - 181)
        load[slash_blowdown] = 2.25 + 0.30 * (codes[slash_blowdown] - 201)

        moisture[grass] = 6.0
        moisture[grass_shrub] = 7.0
        moisture[shrub] = 8.0
        moisture[timber_understory] = 9.0
        moisture[timber_litter] = 10.0
        moisture[slash_blowdown] = 8.0

        other_burnable = (codes > 0) & (load == 0.0)
        load[other_burnable] = 1.0
        moisture[other_burnable] = 8.0

        return load.astype(np.float32), moisture.astype(np.float32)

    def build_fuel_data(
        self,
        grid_bounds: tuple[float, float, float, float],
        grid_shape: tuple[int, int],
        target_crs: str,
        resolution_m: float,
        output_dir: Path,
    ) -> FuelData:
        """Export, align, and derive FireTwin fuel layers for a model grid."""
        raster_path = self.export_fbfm40(
            grid_bounds=grid_bounds,
            grid_shape=grid_shape,
            target_crs=target_crs,
            output_path=output_dir / "lf2022_fbfm40.tif",
        )
        fuel_model = self.load_aligned_fbfm40(
            raster_path=raster_path,
            grid_bounds=grid_bounds,
            grid_shape=grid_shape,
            target_crs=target_crs,
        )
        if np.count_nonzero(fuel_model) == 0:
            raise ValueError("LANDFIRE FBFM40 export contains no burnable fuel cells")

        fuel_load_kg_m2, fuel_moisture_percent = self.derive_fuel_properties(fuel_model)
        return FuelData(
            fuel_model=fuel_model,
            fuel_load_kg_m2=fuel_load_kg_m2,
            fuel_moisture_percent=fuel_moisture_percent,
            resolution_m=resolution_m,
        )

    @staticmethod
    def list_available_products() -> dict[str, str]:
        """Get dictionary of available LANDFIRE products.

        Returns:
            Dict mapping product codes to descriptions
        """
        return LANDFIREClient.FUEL_PRODUCTS.copy()

    @staticmethod
    def get_download_instructions() -> str:
        """Get instructions for downloading LANDFIRE data.

        Returns:
            Formatted instructions string
        """
        return """
LANDFIRE Data Access Instructions:

1. FireTwin uses the public LF Product Service ImageServer export API for
   LF2022 CONUS FBFM40 AOI GeoTIFFs.

2. Use LANDFIREClient.export_fbfm40(...) to export a grid-aligned categorical
   fuel raster with nearest-neighbor resampling.

3. For manual inspection or other products, visit https://landfire.gov/fuel/fbfm40
   and the LANDFIRE WCS/WMS service page.
        """.strip()
