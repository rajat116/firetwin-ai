"""Fire case schema bundling all data for a modeling scenario."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from firetwin.schemas.core import FireState, FuelData, TerrainData, WeatherData


class FireCaseMetadata(BaseModel):
    """Metadata about a fire case for provenance and reproducibility."""

    case_id: str = Field(..., description="Unique case identifier")
    name: str = Field(..., description="Human-readable case name")
    description: str = Field(default="", description="Case description")
    is_synthetic: bool = Field(..., description="Whether this is synthetic or real data")
    creation_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When this case was created"
    )
    source: str = Field(default="unknown", description="Data source (synthetic, FIRMS, etc.)")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")


class FireCase(BaseModel):
    """Complete fire modeling case with terrain, fuels, weather, and fire states."""

    metadata: FireCaseMetadata
    terrain: TerrainData
    fuels: FuelData
    weather: WeatherData
    initial_state: FireState = Field(..., description="Fire state at t=0")
    target_states: list[FireState] = Field(
        default_factory=list, description="Ground truth states at future times"
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    @property
    def grid_shape(self) -> tuple[int, int]:
        """Get (height, width) of the modeling grid."""
        shape = self.terrain.elevation_m.shape
        return (int(shape[0]), int(shape[1]))

    @property
    def resolution_m(self) -> float:
        """Get grid resolution in meters."""
        return self.terrain.resolution_m

    def save_to_zarr(self, path: Path) -> None:
        """Save case to Zarr format (implemented in storage module)."""
        from firetwin.data.storage import save_fire_case_zarr

        save_fire_case_zarr(self, path)

    @classmethod
    def load_from_zarr(cls, path: Path) -> "FireCase":
        """Load case from Zarr format (implemented in storage module)."""
        from firetwin.data.storage import load_fire_case_zarr

        return load_fire_case_zarr(path)
