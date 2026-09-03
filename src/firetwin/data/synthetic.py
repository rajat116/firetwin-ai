"""Generate synthetic fire cases for testing and validation."""

from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

from firetwin.schemas import (
    BoundingBox,
    CoordinateSystem,
    FireCase,
    FireCaseMetadata,
    FireState,
    FuelData,
    TerrainData,
    WeatherData,
)


def generate_synthetic_terrain(
    grid_size: tuple[int, int],
    resolution_m: float,
    base_elevation_m: float = 1000.0,
    elevation_range_m: float = 500.0,
    roughness: float = 0.3,
    seed: int | None = None,
) -> TerrainData:
    """Generate synthetic terrain with realistic elevation, slope, and aspect.

    Args:
        grid_size: (height, width) in cells
        resolution_m: Cell size in meters
        base_elevation_m: Base elevation
        elevation_range_m: Range of elevation variation
        roughness: Terrain roughness (0-1, higher = more variation)
        seed: Random seed for reproducibility

    Returns:
        TerrainData with elevation, slope, and aspect
    """
    rng = np.random.default_rng(seed)
    h, w = grid_size

    # Generate fractal-like elevation using multiple octaves of noise
    elevation = np.zeros((h, w))
    frequency = 1.0
    amplitude = 1.0

    for _ in range(5):  # 5 octaves
        noise = rng.random((h, w))
        # Smooth at this frequency
        smoothed = ndimage.gaussian_filter(noise, sigma=10.0 / frequency)
        elevation += amplitude * smoothed
        frequency *= 2.0
        amplitude *= roughness

    # Normalize and scale
    elevation = (elevation - elevation.min()) / (elevation.max() - elevation.min())
    elevation = base_elevation_m + elevation * elevation_range_m

    # Calculate slope (degrees)
    dy, dx = np.gradient(elevation, resolution_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_degrees = np.rad2deg(slope_rad)

    # Calculate aspect (degrees from north, 0-360)
    aspect_rad = np.arctan2(-dx, dy)  # Mathematical convention
    aspect_degrees = (np.rad2deg(aspect_rad) + 360) % 360

    # Create bounding box (synthetic lat/lon-like coordinates)
    width_deg = (w * resolution_m) / 111000  # Rough conversion at mid-latitudes
    height_deg = (h * resolution_m) / 111000
    bbox = BoundingBox(
        min_x=-120.0,
        max_x=-120.0 + width_deg,
        min_y=40.0,
        max_y=40.0 + height_deg,
        crs=CoordinateSystem.WGS84,
    )

    return TerrainData(
        elevation_m=elevation,
        slope_degrees=slope_degrees,
        aspect_degrees=aspect_degrees,
        resolution_m=resolution_m,
        bbox=bbox,
    )


def generate_synthetic_fuels(
    grid_size: tuple[int, int],
    resolution_m: float,
    fuel_continuity: float = 0.9,
    seed: int | None = None,
) -> FuelData:
    """Generate synthetic fuel distribution.

    Args:
        grid_size: (height, width) in cells
        resolution_m: Cell size in meters
        fuel_continuity: How connected fuels are (0-1)
        seed: Random seed

    Returns:
        FuelData with fuel model, load, and moisture
    """
    rng = np.random.default_rng(seed)
    h, w = grid_size

    # Generate fuel type patches
    # 0 = non-burnable, 1 = grass, 2 = shrub, 3 = timber
    noise = rng.random((h, w))
    smoothed = ndimage.gaussian_filter(noise, sigma=5.0)

    fuel_model = np.zeros((h, w), dtype=np.int32)
    fuel_model[smoothed > 0.7] = 3  # Timber
    fuel_model[(smoothed > 0.4) & (smoothed <= 0.7)] = 2  # Shrub
    fuel_model[(smoothed > 0.2) & (smoothed <= 0.4)] = 1  # Grass
    # Rest stays 0 (non-burnable)

    # Fuel load varies by type
    fuel_load = np.zeros((h, w))
    fuel_load[fuel_model == 1] = rng.uniform(0.3, 0.6, np.sum(fuel_model == 1))  # Grass
    fuel_load[fuel_model == 2] = rng.uniform(0.8, 1.5, np.sum(fuel_model == 2))  # Shrub
    fuel_load[fuel_model == 3] = rng.uniform(2.0, 4.0, np.sum(fuel_model == 3))  # Timber

    # Fuel moisture (%)
    base_moisture = 12.0  # Dry conditions
    fuel_moisture = base_moisture + rng.normal(0, 2, (h, w))
    fuel_moisture = np.clip(fuel_moisture, 5, 30)

    return FuelData(
        fuel_model=fuel_model,
        fuel_load_kg_m2=fuel_load,
        fuel_moisture_percent=fuel_moisture,
        resolution_m=resolution_m,
    )


def generate_synthetic_weather(
    timestamp: datetime,
    wind_speed_m_s: float = 10.0,
    wind_direction_degrees: float = 270.0,  # From west
    temperature_c: float = 32.0,
    relative_humidity_percent: float = 20.0,
) -> WeatherData:
    """Generate synthetic weather conditions.

    Args:
        timestamp: Time of weather observation
        wind_speed_m_s: Wind speed
        wind_direction_degrees: Wind direction (0 = from north, clockwise)
        temperature_c: Temperature
        relative_humidity_percent: Relative humidity

    Returns:
        WeatherData
    """
    return WeatherData(
        wind_speed_m_s=wind_speed_m_s,
        wind_direction_degrees=wind_direction_degrees,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        timestamp=timestamp,
    )


def generate_fire_evolution(
    terrain: TerrainData,
    fuels: FuelData,
    weather: WeatherData,
    ignition_point: tuple[int, int],
    n_steps: int = 24,
    dt_hours: float = 1.0,
    base_spread_rate_m_h: float = 100.0,
    seed: int | None = None,
) -> list[FireState]:
    """Generate realistic fire evolution using simple spread model.

    Args:
        terrain: Terrain data
        fuels: Fuel data
        weather: Weather conditions
        ignition_point: (row, col) ignition location
        n_steps: Number of time steps
        dt_hours: Time step in hours
        base_spread_rate_m_h: Base spread rate in m/h
        seed: Random seed

    Returns:
        List of FireState objects showing evolution
    """
    rng = np.random.default_rng(seed)
    h, w = terrain.elevation_m.shape
    resolution_m = terrain.resolution_m

    # Initialize burned area
    burned = np.zeros((h, w), dtype=np.int32)
    ig_r, ig_c = ignition_point
    burned[ig_r, ig_c] = 1

    states = []
    t0 = weather.timestamp

    for step in range(n_steps):
        # Find active front (cells adjacent to burned)
        active_front = np.zeros((h, w), dtype=np.int32)
        kernel = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        dilated = ndimage.binary_dilation(burned, structure=kernel)
        active_front = (dilated & ~burned).astype(np.int32)

        # Calculate spread probability for each active cell
        # Factors: fuel type, slope, wind alignment
        for i in range(h):
            for j in range(w):
                if not active_front[i, j]:
                    continue

                # Base spread rate modified by fuel
                fuel_type = fuels.fuel_model[i, j]
                if fuel_type == 0:  # Non-burnable
                    continue

                spread_rate = base_spread_rate_m_h
                if fuel_type == 1:  # Grass
                    spread_rate *= 1.5
                elif fuel_type == 2:  # Shrub
                    spread_rate *= 1.0
                elif fuel_type == 3:  # Timber
                    spread_rate *= 0.7

                # Simple wind effect (elliptical spread)
                # Calculate direction from nearest burned cell
                # For simplicity, use stochastic spread with wind bias
                spread_prob = (spread_rate * dt_hours) / resolution_m

                # Wind alignment bonus (simplified)
                # If wind is from west (270°), fire spreads faster east
                wind_factor = 1.0 + 0.5 * rng.random()  # Simplified

                spread_prob *= wind_factor
                spread_prob = min(spread_prob, 0.95)  # Cap at 95%

                if rng.random() < spread_prob:
                    burned[i, j] = 1

        # Save state
        timestamp = t0 + timedelta(hours=step * dt_hours)
        state = FireState(
            burned=burned.copy(),
            active_front=active_front.copy(),
            timestamp=timestamp,
            resolution_m=resolution_m,
            bbox=terrain.bbox,
        )
        states.append(state)

    return states


def generate_synthetic_fire_case(
    case_id: str = "synthetic_001",
    name: str = "Synthetic Fire Case",
    grid_size: tuple[int, int] = (100, 100),
    resolution_m: float = 30.0,
    ignition_center: bool = True,
    n_forecast_hours: int = 24,
    seed: int | None = None,
) -> FireCase:
    """Generate a complete synthetic fire case.

    Args:
        case_id: Unique identifier
        name: Human-readable name
        grid_size: (height, width) grid dimensions
        resolution_m: Cell size in meters
        ignition_center: If True, ignite at center; else random
        n_forecast_hours: Hours of evolution to generate
        seed: Random seed for reproducibility

    Returns:
        Complete FireCase with terrain, fuels, weather, and evolution
    """
    rng = np.random.default_rng(seed)

    # Generate components
    terrain = generate_synthetic_terrain(grid_size, resolution_m, seed=seed)
    fuels = generate_synthetic_fuels(grid_size, resolution_m, seed=seed)

    t0 = datetime(2024, 8, 15, 12, 0, 0)  # Arbitrary start time
    weather = generate_synthetic_weather(t0)

    # Ignition point
    h, w = grid_size
    if ignition_center:
        ig_point = (h // 2, w // 2)
    else:
        ig_point = (rng.integers(h // 4, 3 * h // 4), rng.integers(w // 4, 3 * w // 4))

    # Generate evolution
    states = generate_fire_evolution(
        terrain, fuels, weather, ig_point, n_steps=n_forecast_hours, seed=seed
    )

    # Initial state is just the ignition
    initial_state = states[0]

    # Target states are the rest
    target_states = states[1:]

    metadata = FireCaseMetadata(
        case_id=case_id,
        name=name,
        description=f"Synthetic fire case with {n_forecast_hours}h evolution",
        is_synthetic=True,
        source="synthetic_generator",
        tags=["synthetic", "testing"],
    )

    return FireCase(
        metadata=metadata,
        terrain=terrain,
        fuels=fuels,
        weather=weather,
        initial_state=initial_state,
        target_states=target_states,
    )
