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

from pathlib import Path

import requests


class USGS3DEPClient:
    """Client for USGS 3DEP elevation data via The National Map API."""

    # The National Map API endpoint
    BASE_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"

    def __init__(self, timeout: int = 300) -> None:
        """Initialize USGS 3DEP client.

        Args:
            timeout: HTTP request timeout in seconds (default: 300 for large files)
        """
        self.timeout = timeout

    def search_datasets(
        self,
        bbox: tuple[float, float, float, float],
        dataset: str = "Digital Elevation Model (DEM) 1/3 arc-second",
    ) -> list[dict]:
        """Search for available 3DEP datasets in bounding box.

        Args:
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat) in WGS84
            dataset: Dataset name (default: 1/3 arc-second DEM)

        Returns:
            List of dataset metadata dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        params = {
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "datasets": dataset,
            "outputFormat": "JSON",
        }

        response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        items: list[dict] = data.get("items", [])
        return items

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
        dataset: str = "Digital Elevation Model (DEM) 1/3 arc-second",
    ) -> list[Path]:
        """Search and download all 3DEP tiles for a bounding box.

        Args:
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            output_dir: Output directory for downloaded files
            dataset: Dataset name

        Returns:
            List of downloaded file paths
        """
        # Search for datasets
        datasets = self.search_datasets(bbox=bbox, dataset=dataset)

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

            try:
                self.download_dataset(download_url, output_path)
                downloaded_files.append(output_path)
            except Exception:
                # Continue with other downloads if one fails
                continue

        return downloaded_files

    @staticmethod
    def list_available_datasets() -> dict[str, str]:
        """Get dictionary of available 3DEP datasets.

        Returns:
            Dict mapping dataset names to descriptions
        """
        return {
            "Digital Elevation Model (DEM) 1/3 arc-second": "~10m resolution DEM for CONUS",
            "Digital Elevation Model (DEM) 1 arc-second": "~30m resolution DEM",
            "Digital Surface Model (DSM) 1 meter": "1m lidar-derived surface model",
            "Hillshade 1/3 arc-second": "Shaded relief visualization",
        }
