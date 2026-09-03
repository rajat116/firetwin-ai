"""Global settings and configuration for FireTwin."""

import platform
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FireTwinSettings(BaseSettings):
    """Global FireTwin settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    firms_map_key: str | None = Field(
        default=None,
        description="NASA FIRMS MAP_KEY for active fire data",
    )
    cds_api_url: str | None = Field(
        default="https://cds.climate.copernicus.eu/api/v2",
        description="Copernicus Climate Data Store API URL",
    )
    cds_api_key: str | None = Field(
        default=None,
        description="Copernicus Climate Data Store API key",
    )

    # Data paths
    data_root: Path = Field(
        default=Path("./data"),
        description="Root directory for all data",
    )

    # MLflow
    mlflow_tracking_uri: str = Field(
        default="./mlruns",
        description="MLflow tracking URI",
    )

    @property
    def data_raw(self) -> Path:
        """Path to raw data directory."""
        return self.data_root / "raw"

    @property
    def data_interim(self) -> Path:
        """Path to interim data directory."""
        return self.data_root / "interim"

    @property
    def data_processed(self) -> Path:
        """Path to processed data directory."""
        return self.data_root / "processed"

    @property
    def data_manifests(self) -> Path:
        """Path to data manifests directory."""
        return self.data_root / "manifests"


def get_system_info() -> dict:
    """Get system information for diagnostics."""
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def check_optional_dependencies() -> dict:
    """Check availability of optional dependencies."""
    dependencies = {}

    # Check PyTorch
    try:
        import torch

        dependencies["torch"] = {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        }
    except ImportError:
        dependencies["torch"] = {"available": False}

    # Check geospatial libraries
    for lib in ["geopandas", "rasterio", "xarray", "mlflow"]:
        try:
            module = __import__(lib)
            dependencies[lib] = {
                "available": True,
                "version": getattr(module, "__version__", "unknown"),
            }
        except ImportError:
            dependencies[lib] = {"available": False}

    return dependencies


# Global settings instance
settings = FireTwinSettings()
