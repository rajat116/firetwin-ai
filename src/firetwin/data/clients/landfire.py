"""LANDFIRE fuel and vegetation data client.

Official documentation:
- Portal: https://landfire.gov
- Data Access: https://landfire.gov/getdata.php
- Product Catalog: https://landfire.gov/version_comparison.php

LANDFIRE provides 30m resolution national fuel and vegetation datasets:
- Fuel Model (FBFM40, FBFM13)
- Canopy Cover, Height, Base Height, Bulk Density
- Vegetation Type, Height, Cover
- Topographic variables (Slope, Aspect, Elevation)

Data typically downloaded as GeoTIFF rasters for Areas of Interest (AOI).
"""

from pathlib import Path


class LANDFIREClient:
    """Client for LANDFIRE fuel and vegetation data downloads.

    LANDFIRE provides downloadable GeoTIFF datasets via their data portal.
    This client provides programmatic access to common fuel model layers.
    """

    # Base URL for LANDFIRE data downloads
    BASE_URL = "https://landfire.gov/bulk/downloadfile.php"

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
            "LANDFIRE requires manual AOI selection via web portal. "
            "Visit https://landfire.gov/getdata.php to: \n"
            "1. Draw or upload AOI boundary\n"
            "2. Select desired products and version\n"
            "3. Download GeoTIFF files\n"
            "For automation, use direct URLs from the download cart."
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
LANDFIRE Data Download Instructions:

1. Visit: https://landfire.gov/getdata.php

2. Define Area of Interest (AOI):
   - Draw on map, upload shapefile, or enter coordinates

3. Select Products:
   - Fuel Models: FBFM40, FBFM13
   - Canopy: Cover, Height, Base Height, Bulk Density
   - Topography: Aspect, Slope, Elevation

4. Select Version:
   - Current: 2.3.0 (2022 Update)
   - Previous: 2.2.0, 2.1.0, etc.

5. Download:
   - Add to cart and download GeoTIFF files
   - Files are 30m resolution, projected in Albers Equal Area

6. Automation:
   - For repeated downloads, save direct URLs from cart
   - Use requests library with saved URLs
        """.strip()
