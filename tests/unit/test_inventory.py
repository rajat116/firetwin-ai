"""Unit tests for fire inventory system."""

from datetime import date
from pathlib import Path

import pytest

from firetwin.data.inventory import FireCaseCandidate, FireInventory


@pytest.fixture
def sample_candidate() -> FireCaseCandidate:
    """Create a sample fire case candidate."""
    return FireCaseCandidate(
        fire_id="TEST001",
        fire_name="Test Fire",
        start_date=date(2024, 8, 1),
        end_date=date(2024, 8, 10),
        bbox=(-121.0, 38.0, -120.0, 39.0),
        area_hectares=5000.0,
        has_firms_detections=True,
        has_nifc_perimeters=True,
        has_mtbs_perimeter=True,
        has_era5_weather=True,
        has_landfire_fuels=True,
        has_3dep_terrain=True,
        firms_detection_count=150,
        nifc_perimeter_count=8,
        temporal_coverage_days=9,
    )


def test_fire_case_candidate_quality_score(sample_candidate: FireCaseCandidate) -> None:
    """Test quality score calculation."""
    # High-quality fire with all data sources
    assert sample_candidate.quality_score > 80.0

    # Low-quality fire
    low_quality = FireCaseCandidate(
        fire_id="LOW001",
        fire_name="Low Quality Fire",
        start_date=date(2024, 8, 1),
        end_date=None,
        bbox=(-121.0, 38.0, -120.0, 39.0),
        area_hectares=100.0,
        firms_detection_count=5,
    )
    assert low_quality.quality_score < 30.0


def test_fire_case_candidate_to_dict(sample_candidate: FireCaseCandidate) -> None:
    """Test conversion to dictionary."""
    data = sample_candidate.to_dict()

    assert data["fire_id"] == "TEST001"
    assert data["fire_name"] == "Test Fire"
    assert data["area_hectares"] == 5000.0
    assert data["has_firms_detections"] is True


def test_fire_inventory_add_candidate(sample_candidate: FireCaseCandidate) -> None:
    """Test adding candidates to inventory."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    assert len(inventory.candidates) == 1
    assert inventory.candidates[0].fire_id == "TEST001"


def test_fire_inventory_search_quality(sample_candidate: FireCaseCandidate) -> None:
    """Test searching by quality score."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Should find with low threshold
    results = inventory.search(min_quality_score=50.0)
    assert len(results) == 1

    # Should not find with high threshold
    results = inventory.search(min_quality_score=99.0)
    assert len(results) == 0


def test_fire_inventory_search_area(sample_candidate: FireCaseCandidate) -> None:
    """Test searching by area."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Should find with low threshold
    results = inventory.search(min_area_hectares=1000.0)
    assert len(results) == 1

    # Should not find with high threshold
    results = inventory.search(min_area_hectares=10000.0)
    assert len(results) == 0


def test_fire_inventory_search_temporal(sample_candidate: FireCaseCandidate) -> None:
    """Test searching by temporal range."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Should find within range
    results = inventory.search(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    assert len(results) == 1

    # Should not find outside range
    results = inventory.search(start_date=date(2025, 1, 1))
    assert len(results) == 0


def test_fire_inventory_search_spatial(sample_candidate: FireCaseCandidate) -> None:
    """Test searching by bbox."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Should find with overlapping bbox
    results = inventory.search(bbox=(-122.0, 37.0, -119.0, 40.0))
    assert len(results) == 1

    # Should not find with non-overlapping bbox
    results = inventory.search(bbox=(-100.0, 30.0, -99.0, 31.0))
    assert len(results) == 0


def test_fire_inventory_search_data_requirements(
    sample_candidate: FireCaseCandidate,
) -> None:
    """Test searching with data requirement filters."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Should find with matching requirements
    results = inventory.search(require_firms=True, require_nifc=True)
    assert len(results) == 1

    # Should not find with unmet requirement
    results = inventory.search(require_mtbs=False)
    assert len(results) == 1

    # Add candidate without MTBS
    no_mtbs = FireCaseCandidate(
        fire_id="NO_MTBS",
        fire_name="No MTBS Fire",
        start_date=date(2024, 8, 1),
        end_date=None,
        bbox=(-121.0, 38.0, -120.0, 39.0),
        area_hectares=1000.0,
        has_firms_detections=True,
    )
    inventory.add_candidate(no_mtbs)

    # Should only find the one with MTBS
    results = inventory.search(require_mtbs=True)
    assert len(results) == 1
    assert results[0].fire_id == "TEST001"


def test_fire_inventory_to_dataframe(sample_candidate: FireCaseCandidate) -> None:
    """Test conversion to DataFrame."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    df = inventory.to_dataframe()

    assert len(df) == 1
    assert df["fire_id"].iloc[0] == "TEST001"
    assert df["quality_score"].iloc[0] > 80.0


def test_fire_inventory_to_geodataframe(sample_candidate: FireCaseCandidate) -> None:
    """Test conversion to GeoDataFrame."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    gdf = inventory.to_geodataframe()

    assert len(gdf) == 1
    assert gdf.crs.to_epsg() == 4326
    assert gdf.geometry.iloc[0].is_valid


def test_fire_inventory_save_load(sample_candidate: FireCaseCandidate, tmp_path: Path) -> None:
    """Test saving and loading inventory."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    # Save to CSV
    csv_path = tmp_path / "inventory.csv"
    inventory.save(csv_path)
    assert csv_path.exists()

    # Load from CSV
    loaded_inventory = FireInventory(csv_path)
    assert len(loaded_inventory.candidates) == 1
    assert loaded_inventory.candidates[0].fire_id == "TEST001"


def test_fire_inventory_statistics(sample_candidate: FireCaseCandidate) -> None:
    """Test inventory statistics."""
    inventory = FireInventory()
    inventory.add_candidate(sample_candidate)

    stats = inventory.get_statistics()

    assert stats["total_fires"] == 1
    assert stats["fires_with_firms"] == 1
    assert stats["fires_with_nifc"] == 1
    assert stats["mean_area_hectares"] == 5000.0
