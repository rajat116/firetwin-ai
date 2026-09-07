"""Fire case inventory and candidate selection.

This module provides tools to build and query an inventory of fire cases
from available data sources, enabling selection of high-quality training
and evaluation datasets.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


@dataclass
class FireCaseCandidate:
    """Candidate fire case with metadata and quality metrics."""

    fire_id: str
    fire_name: str
    start_date: date
    end_date: date | None
    bbox: tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    area_hectares: float

    # Data availability flags
    has_firms_detections: bool = False
    has_nifc_perimeters: bool = False
    has_mtbs_perimeter: bool = False
    has_era5_weather: bool = False
    has_landfire_fuels: bool = False
    has_3dep_terrain: bool = False

    # Quality metrics
    firms_detection_count: int = 0
    nifc_perimeter_count: int = 0
    temporal_coverage_days: int = 0
    spatial_coverage_km2: float = 0.0

    # Quality score (0-100)
    quality_score: float = 0.0

    # Metadata
    region: str | None = None
    fire_type: str | None = None  # wildfire, prescribed, etc.
    data_sources: list[str] | None = None

    def __post_init__(self) -> None:
        """Calculate derived fields after initialization."""
        if self.data_sources is None:
            self.data_sources = []

        # Calculate quality score
        self.quality_score = self._calculate_quality_score()

    def _calculate_quality_score(self) -> float:
        """Calculate quality score based on data availability and completeness.

        Returns:
            Quality score from 0-100
        """
        score = 0.0

        # Data source availability (60 points total)
        if self.has_firms_detections:
            score += 15.0
        if self.has_nifc_perimeters:
            score += 15.0
        if self.has_mtbs_perimeter:
            score += 10.0
        if self.has_era5_weather:
            score += 10.0
        if self.has_landfire_fuels:
            score += 5.0
        if self.has_3dep_terrain:
            score += 5.0

        # Data richness (40 points total)
        # More detections = better temporal resolution
        if self.firms_detection_count > 100:
            score += 15.0
        elif self.firms_detection_count > 50:
            score += 10.0
        elif self.firms_detection_count > 10:
            score += 5.0

        # Multiple perimeters = fire progression data
        if self.nifc_perimeter_count > 5:
            score += 15.0
        elif self.nifc_perimeter_count > 2:
            score += 10.0
        elif self.nifc_perimeter_count > 0:
            score += 5.0

        # Temporal coverage (longer fires = more data)
        if self.temporal_coverage_days > 14:
            score += 10.0
        elif self.temporal_coverage_days > 7:
            score += 5.0

        return min(score, 100.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "fire_id": self.fire_id,
            "fire_name": self.fire_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "bbox": self.bbox,
            "area_hectares": self.area_hectares,
            "has_firms_detections": self.has_firms_detections,
            "has_nifc_perimeters": self.has_nifc_perimeters,
            "has_mtbs_perimeter": self.has_mtbs_perimeter,
            "has_era5_weather": self.has_era5_weather,
            "has_landfire_fuels": self.has_landfire_fuels,
            "has_3dep_terrain": self.has_3dep_terrain,
            "firms_detection_count": self.firms_detection_count,
            "nifc_perimeter_count": self.nifc_perimeter_count,
            "temporal_coverage_days": self.temporal_coverage_days,
            "spatial_coverage_km2": self.spatial_coverage_km2,
            "quality_score": self.quality_score,
            "region": self.region,
            "fire_type": self.fire_type,
            "data_sources": self.data_sources,
        }


class FireInventory:
    """Fire case inventory manager.

    Maintains a searchable database of available fire cases with
    metadata about data availability and quality.
    """

    def __init__(self, inventory_path: Path | None = None) -> None:
        """Initialize fire inventory.

        Args:
            inventory_path: Path to inventory CSV/Parquet file (optional)
        """
        self.inventory_path = inventory_path
        self.candidates: list[FireCaseCandidate] = []

        if inventory_path and inventory_path.exists():
            self.load()

    def add_candidate(self, candidate: FireCaseCandidate) -> None:
        """Add a fire case candidate to inventory."""
        self.candidates.append(candidate)

    def search(
        self,
        min_quality_score: float = 50.0,
        min_area_hectares: float = 100.0,
        start_date: date | None = None,
        end_date: date | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        require_firms: bool = False,
        require_nifc: bool = False,
        require_mtbs: bool = False,
    ) -> list[FireCaseCandidate]:
        """Search inventory for fire cases matching criteria.

        Args:
            min_quality_score: Minimum quality score (0-100)
            min_area_hectares: Minimum fire area in hectares
            start_date: Earliest start date
            end_date: Latest start date
            bbox: Bounding box (minx, miny, maxx, maxy) in WGS84
            require_firms: Require FIRMS detections
            require_nifc: Require NIFC perimeters
            require_mtbs: Require MTBS perimeter

        Returns:
            List of matching fire case candidates
        """
        results = []

        for candidate in self.candidates:
            # Quality filter
            if candidate.quality_score < min_quality_score:
                continue

            # Size filter
            if candidate.area_hectares < min_area_hectares:
                continue

            # Temporal filter
            if start_date and candidate.start_date < start_date:
                continue
            if end_date and candidate.start_date > end_date:
                continue

            # Spatial filter
            if bbox:
                cand_box = box(*candidate.bbox)
                search_box = box(*bbox)
                if not cand_box.intersects(search_box):
                    continue

            # Data requirement filters
            if require_firms and not candidate.has_firms_detections:
                continue
            if require_nifc and not candidate.has_nifc_perimeters:
                continue
            if require_mtbs and not candidate.has_mtbs_perimeter:
                continue

            results.append(candidate)

        # Sort by quality score (descending)
        results.sort(key=lambda c: c.quality_score, reverse=True)

        return results

    def to_dataframe(self) -> pd.DataFrame:
        """Convert inventory to pandas DataFrame."""
        return pd.DataFrame([c.to_dict() for c in self.candidates])

    def to_geodataframe(self) -> gpd.GeoDataFrame:
        """Convert inventory to GeoDataFrame with bbox geometries."""
        df = self.to_dataframe()

        # Create polygon geometries from bboxes
        geometries = [box(*bbox) for bbox in df["bbox"]]

        gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")
        return gdf

    def save(self, path: Path | None = None) -> None:
        """Save inventory to file.

        Args:
            path: Output path (CSV or Parquet). If None, uses self.inventory_path.
        """
        output_path = path or self.inventory_path

        if output_path is None:
            raise ValueError("No output path specified")

        df = self.to_dataframe()

        # Convert bbox tuples to strings for CSV
        df["bbox"] = df["bbox"].apply(str)
        df["data_sources"] = df["data_sources"].apply(str)

        if output_path.suffix == ".parquet":
            df.to_parquet(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)

    def load(self, path: Path | None = None) -> None:
        """Load inventory from file.

        Args:
            path: Input path. If None, uses self.inventory_path.
        """
        input_path = path or self.inventory_path

        if input_path is None:
            raise ValueError("No input path specified")

        if input_path.suffix == ".parquet":
            df = pd.read_parquet(input_path)
        else:
            df = pd.read_csv(input_path)

        # Reconstruct candidates
        self.candidates = []
        for _, row in df.iterrows():
            # Parse bbox from string
            bbox_str = row["bbox"].strip("()").split(",")
            bbox_tuple = tuple(float(x.strip()) for x in bbox_str)
            bbox: tuple[float, float, float, float] = (
                bbox_tuple[0],
                bbox_tuple[1],
                bbox_tuple[2],
                bbox_tuple[3],
            )

            # Parse data_sources from string
            sources_str = row["data_sources"].strip("[]").replace("'", "")
            data_sources = [s.strip() for s in sources_str.split(",")] if sources_str else []

            candidate = FireCaseCandidate(
                fire_id=row["fire_id"],
                fire_name=row["fire_name"],
                start_date=pd.to_datetime(row["start_date"]).date(),
                end_date=pd.to_datetime(row["end_date"]).date()
                if pd.notna(row["end_date"])
                else None,
                bbox=bbox,
                area_hectares=row["area_hectares"],
                has_firms_detections=row["has_firms_detections"],
                has_nifc_perimeters=row["has_nifc_perimeters"],
                has_mtbs_perimeter=row["has_mtbs_perimeter"],
                has_era5_weather=row["has_era5_weather"],
                has_landfire_fuels=row["has_landfire_fuels"],
                has_3dep_terrain=row["has_3dep_terrain"],
                firms_detection_count=row["firms_detection_count"],
                nifc_perimeter_count=row["nifc_perimeter_count"],
                temporal_coverage_days=row["temporal_coverage_days"],
                spatial_coverage_km2=row["spatial_coverage_km2"],
                quality_score=row["quality_score"],
                region=row["region"] if pd.notna(row["region"]) else None,
                fire_type=row["fire_type"] if pd.notna(row["fire_type"]) else None,
                data_sources=data_sources,
            )

            self.candidates.append(candidate)

    def get_statistics(self) -> dict[str, Any]:
        """Get inventory statistics.

        Returns:
            Dictionary with summary statistics
        """
        if not self.candidates:
            return {"total_fires": 0}

        df = self.to_dataframe()

        return {
            "total_fires": len(self.candidates),
            "mean_quality_score": df["quality_score"].mean(),
            "fires_with_firms": df["has_firms_detections"].sum(),
            "fires_with_nifc": df["has_nifc_perimeters"].sum(),
            "fires_with_mtbs": df["has_mtbs_perimeter"].sum(),
            "fires_with_era5": df["has_era5_weather"].sum(),
            "fires_with_landfire": df["has_landfire_fuels"].sum(),
            "fires_with_3dep": df["has_3dep_terrain"].sum(),
            "mean_area_hectares": df["area_hectares"].mean(),
            "total_area_hectares": df["area_hectares"].sum(),
            "date_range": (df["start_date"].min(), df["start_date"].max()),
        }
