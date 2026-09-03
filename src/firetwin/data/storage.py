"""Storage and serialization for fire cases using Xarray and Zarr."""

from pathlib import Path

import numpy as np
import xarray as xr

from firetwin.schemas import FireCase, FireCaseMetadata, FireState


def fire_case_to_xarray(case: FireCase) -> xr.Dataset:
    """Convert FireCase to Xarray Dataset for storage.

    Args:
        case: FireCase to convert

    Returns:
        Xarray Dataset with all case data and metadata
    """
    h, w = case.grid_shape

    # Create coordinate arrays
    # Use grid indices for now; real cases will have lat/lon
    y = np.arange(h)
    x = np.arange(w)

    # Time coordinates for fire evolution
    times = [case.initial_state.timestamp] + [s.timestamp for s in case.target_states]

    # Build time-varying burned/active masks
    burned_stack = np.stack(
        [case.initial_state.burned] + [s.burned for s in case.target_states]
    )
    active_stack = np.stack(
        [case.initial_state.active_front] + [s.active_front for s in case.target_states]
    )

    # Create dataset
    ds = xr.Dataset(
        data_vars={
            # Terrain (static)
            "elevation_m": (["y", "x"], case.terrain.elevation_m),
            "slope_degrees": (["y", "x"], case.terrain.slope_degrees),
            "aspect_degrees": (["y", "x"], case.terrain.aspect_degrees),
            # Fuels (static)
            "fuel_model": (["y", "x"], case.fuels.fuel_model),
            "fuel_load_kg_m2": (["y", "x"], case.fuels.fuel_load_kg_m2),
            "fuel_moisture_percent": (["y", "x"], case.fuels.fuel_moisture_percent),
            # Fire evolution (time-varying)
            "burned": (["time", "y", "x"], burned_stack),
            "active_front": (["time", "y", "x"], active_stack),
        },
        coords={
            "y": y,
            "x": x,
            "time": times,
        },
        attrs={
            # Metadata
            "case_id": case.metadata.case_id,
            "name": case.metadata.name,
            "description": case.metadata.description,
            "is_synthetic": case.metadata.is_synthetic,
            "creation_timestamp": case.metadata.creation_timestamp.isoformat(),
            "source": case.metadata.source,
            "tags": ",".join(case.metadata.tags),
            # Grid info
            "resolution_m": case.resolution_m,
            "bbox_min_x": case.terrain.bbox.min_x,
            "bbox_max_x": case.terrain.bbox.max_x,
            "bbox_min_y": case.terrain.bbox.min_y,
            "bbox_max_y": case.terrain.bbox.max_y,
            "bbox_crs": case.terrain.bbox.crs.value,
            # Weather (stored as attrs for now; could be separate dataset)
            "wind_speed_m_s": case.weather.wind_speed_m_s,
            "wind_direction_degrees": case.weather.wind_direction_degrees,
            "temperature_c": case.weather.temperature_c,
            "relative_humidity_percent": case.weather.relative_humidity_percent,
            "weather_timestamp": case.weather.timestamp.isoformat(),
        },
    )

    # Add units and descriptions
    ds["elevation_m"].attrs = {"units": "meters", "long_name": "Elevation"}
    ds["slope_degrees"].attrs = {"units": "degrees", "long_name": "Slope angle"}
    ds["aspect_degrees"].attrs = {
        "units": "degrees",
        "long_name": "Aspect (degrees from north)",
    }
    ds["fuel_model"].attrs = {
        "long_name": "Fuel type",
        "description": "0=non-burnable, 1=grass, 2=shrub, 3=timber",
    }
    ds["fuel_load_kg_m2"].attrs = {"units": "kg/m^2", "long_name": "Fuel load"}
    ds["fuel_moisture_percent"].attrs = {"units": "percent", "long_name": "Fuel moisture"}
    ds["burned"].attrs = {"long_name": "Burned area mask", "description": "0=unburned, 1=burned"}
    ds["active_front"].attrs = {
        "long_name": "Active fire front",
        "description": "0=inactive, 1=active",
    }

    return ds


def xarray_to_fire_case(ds: xr.Dataset) -> FireCase:
    """Convert Xarray Dataset back to FireCase.

    Args:
        ds: Xarray Dataset

    Returns:
        Reconstructed FireCase
    """
    from datetime import datetime

    from firetwin.schemas import (
        BoundingBox,
        CoordinateSystem,
        FuelData,
        TerrainData,
        WeatherData,
    )

    # Extract metadata
    metadata = FireCaseMetadata(
        case_id=ds.attrs["case_id"],
        name=ds.attrs["name"],
        description=ds.attrs.get("description", ""),
        is_synthetic=ds.attrs["is_synthetic"],
        creation_timestamp=datetime.fromisoformat(ds.attrs["creation_timestamp"]),
        source=ds.attrs["source"],
        tags=ds.attrs.get("tags", "").split(",") if ds.attrs.get("tags") else [],
    )

    # Extract bbox
    bbox = BoundingBox(
        min_x=ds.attrs["bbox_min_x"],
        max_x=ds.attrs["bbox_max_x"],
        min_y=ds.attrs["bbox_min_y"],
        max_y=ds.attrs["bbox_max_y"],
        crs=CoordinateSystem(ds.attrs["bbox_crs"]),
    )

    resolution_m = ds.attrs["resolution_m"]

    # Terrain
    terrain = TerrainData(
        elevation_m=ds["elevation_m"].values,
        slope_degrees=ds["slope_degrees"].values,
        aspect_degrees=ds["aspect_degrees"].values,
        resolution_m=resolution_m,
        bbox=bbox,
    )

    # Fuels
    fuels = FuelData(
        fuel_model=ds["fuel_model"].values,
        fuel_load_kg_m2=ds["fuel_load_kg_m2"].values,
        fuel_moisture_percent=ds["fuel_moisture_percent"].values,
        resolution_m=resolution_m,
    )

    # Weather
    weather = WeatherData(
        wind_speed_m_s=ds.attrs["wind_speed_m_s"],
        wind_direction_degrees=ds.attrs["wind_direction_degrees"],
        temperature_c=ds.attrs["temperature_c"],
        relative_humidity_percent=ds.attrs["relative_humidity_percent"],
        timestamp=datetime.fromisoformat(ds.attrs["weather_timestamp"]),
    )

    # Fire states
    times = ds.coords["time"].values
    burned_stack = ds["burned"].values
    active_stack = ds["active_front"].values

    # Convert numpy datetime64 to Python datetime
    import pandas as pd

    def to_datetime(np_datetime: np.datetime64) -> datetime:
        """Convert numpy datetime64 to Python datetime."""
        return pd.Timestamp(np_datetime).to_pydatetime()

    initial_state = FireState(
        burned=burned_stack[0].astype(np.int32),
        active_front=active_stack[0].astype(np.int32),
        timestamp=to_datetime(times[0]),
        resolution_m=resolution_m,
        bbox=bbox,
    )

    target_states = [
        FireState(
            burned=burned_stack[i].astype(np.int32),
            active_front=active_stack[i].astype(np.int32),
            timestamp=to_datetime(times[i]),
            resolution_m=resolution_m,
            bbox=bbox,
        )
        for i in range(1, len(times))
    ]

    return FireCase(
        metadata=metadata,
        terrain=terrain,
        fuels=fuels,
        weather=weather,
        initial_state=initial_state,
        target_states=target_states,
    )


def save_fire_case_zarr(case: FireCase, path: Path) -> None:
    """Save FireCase to Zarr format for efficient storage and access.

    Args:
        case: FireCase to save
        path: Output path (will create directory)
    """
    ds = fire_case_to_xarray(case)
    path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(path, mode="w")
    print(f"Saved fire case to {path}")


def load_fire_case_zarr(path: Path) -> FireCase:
    """Load FireCase from Zarr format.

    Args:
        path: Path to Zarr directory

    Returns:
        Loaded FireCase
    """
    ds = xr.open_zarr(path)
    case = xarray_to_fire_case(ds)
    print(f"Loaded fire case {case.metadata.case_id} from {path}")
    return case
