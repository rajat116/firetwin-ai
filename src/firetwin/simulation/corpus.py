"""Phase 5B simulation-corpus generation utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from firetwin.data.synthetic import generate_synthetic_fire_case, generate_synthetic_weather
from firetwin.models.baselines import EllipticalBaseline

SIMULATION_CORPUS_SCHEMA_VERSION = "firetwin.simulation_corpus.v1"


@dataclass(frozen=True)
class SimulationCorpusConfig:
    """Configuration for a lightweight deterministic simulation corpus."""

    case_count: int = 24
    grid_height: int = 64
    grid_width: int = 64
    resolution_m: float = 60.0
    forecast_hours: tuple[float, ...] = (3.0, 6.0, 12.0, 24.0)
    seed: int = 1729
    base_spread_rate_min_m_h: float = 35.0
    base_spread_rate_max_m_h: float = 145.0

    def validate(self) -> None:
        """Validate corpus-generation settings."""
        if self.case_count <= 0:
            raise ValueError("case_count must be positive")
        if self.grid_height <= 8 or self.grid_width <= 8:
            raise ValueError("grid dimensions must be greater than 8 cells")
        if self.resolution_m <= 0:
            raise ValueError("resolution_m must be positive")
        if not self.forecast_hours:
            raise ValueError("forecast_hours must not be empty")
        if any(hour <= 0 for hour in self.forecast_hours):
            raise ValueError("forecast_hours must be positive")
        if tuple(sorted(self.forecast_hours)) != self.forecast_hours:
            raise ValueError("forecast_hours must be sorted ascending")
        if self.base_spread_rate_min_m_h <= 0:
            raise ValueError("base_spread_rate_min_m_h must be positive")
        if self.base_spread_rate_max_m_h < self.base_spread_rate_min_m_h:
            raise ValueError("base spread max must be >= min")


@dataclass(frozen=True)
class SimulationScenario:
    """Sampled scenario parameters for one simulated case."""

    case_id: str
    seed: int
    wind_speed_m_s: float
    wind_direction_degrees: float
    temperature_c: float
    relative_humidity_percent: float
    base_spread_rate_m_h: float


@dataclass(frozen=True)
class SimulationSampleSummary:
    """Manifest entry for one simulation-corpus sample."""

    case_id: str
    artifact: str
    grid_shape: dict[str, int]
    resolution_m: float
    forecast_hours: list[float]
    initial_burned_cells: int
    final_burned_cells: int
    final_active_cells: int
    wind_speed_m_s: float
    wind_direction_degrees: float
    temperature_c: float
    relative_humidity_percent: float
    base_spread_rate_m_h: float


@dataclass(frozen=True)
class SimulationCorpusSummary:
    """Summary returned after writing a simulation corpus."""

    schema_version: str
    output_dir: str
    manifest_path: str
    sample_count: int
    forecast_hours: list[float]
    total_final_burned_cells: int


@dataclass(frozen=True)
class SimulationCorpusProfile:
    """Named corpus-generation profile loaded from project configuration."""

    name: str
    description: str
    output_dir: Path
    report_path: Path
    config: SimulationCorpusConfig
    commit_outputs: bool


def sample_simulation_scenario(index: int, *, seed: int) -> SimulationScenario:
    """Sample deterministic weather and spread parameters for one scenario."""
    rng = np.random.default_rng(seed + index * 7919)
    return SimulationScenario(
        case_id=f"phase5b_sim_{index:04d}",
        seed=int(rng.integers(1, 2**31 - 1)),
        wind_speed_m_s=float(rng.uniform(0.5, 14.0)),
        wind_direction_degrees=float(rng.uniform(0.0, 360.0)),
        temperature_c=float(rng.uniform(18.0, 38.0)),
        relative_humidity_percent=float(rng.uniform(12.0, 55.0)),
        base_spread_rate_m_h=float(rng.uniform(35.0, 145.0)),
    )


def build_simulation_sample(
    scenario: SimulationScenario,
    *,
    config: SimulationCorpusConfig,
) -> tuple[dict[str, np.ndarray], SimulationSampleSummary]:
    """Build one simulated sample artifact and its manifest entry."""
    case = generate_synthetic_fire_case(
        case_id=scenario.case_id,
        name=f"Phase 5B simulated case {scenario.case_id}",
        grid_size=(config.grid_height, config.grid_width),
        resolution_m=config.resolution_m,
        ignition_center=False,
        n_forecast_hours=int(max(config.forecast_hours)) + 1,
        seed=scenario.seed,
    )
    case.weather = generate_synthetic_weather(
        case.initial_state.timestamp,
        wind_speed_m_s=scenario.wind_speed_m_s,
        wind_direction_degrees=scenario.wind_direction_degrees,
        temperature_c=scenario.temperature_c,
        relative_humidity_percent=scenario.relative_humidity_percent,
    )

    forecasts = EllipticalBaseline(base_spread_rate_m_h=scenario.base_spread_rate_m_h).forecast(
        case, list(config.forecast_hours)
    )
    burned_stack = np.stack(
        [forecasts[hour].burned.astype(np.uint8) for hour in config.forecast_hours]
    )
    active_stack = np.stack(
        [forecasts[hour].active_front.astype(np.uint8) for hour in config.forecast_hours]
    )

    artifact = {
        "initial_burned": case.initial_state.burned.astype(np.uint8),
        "fuel_model": case.fuels.fuel_model.astype(np.int16),
        "fuel_load_kg_m2": case.fuels.fuel_load_kg_m2.astype(np.float32),
        "fuel_moisture_percent": case.fuels.fuel_moisture_percent.astype(np.float32),
        "elevation_m": case.terrain.elevation_m.astype(np.float32),
        "slope_degrees": case.terrain.slope_degrees.astype(np.float32),
        "aspect_degrees": case.terrain.aspect_degrees.astype(np.float32),
        "forecast_hours": np.asarray(config.forecast_hours, dtype=np.float32),
        "forecast_burned": burned_stack,
        "forecast_active_front": active_stack,
        "resolution_m": np.asarray([config.resolution_m], dtype=np.float32),
        "weather": np.asarray(
            [
                scenario.wind_speed_m_s,
                scenario.wind_direction_degrees,
                scenario.temperature_c,
                scenario.relative_humidity_percent,
            ],
            dtype=np.float32,
        ),
        "base_spread_rate_m_h": np.asarray([scenario.base_spread_rate_m_h], dtype=np.float32),
    }
    summary = SimulationSampleSummary(
        case_id=scenario.case_id,
        artifact=f"samples/{scenario.case_id}.npz",
        grid_shape={"height": config.grid_height, "width": config.grid_width},
        resolution_m=config.resolution_m,
        forecast_hours=list(config.forecast_hours),
        initial_burned_cells=int(np.sum(case.initial_state.burned)),
        final_burned_cells=int(np.sum(burned_stack[-1])),
        final_active_cells=int(np.sum(active_stack[-1])),
        wind_speed_m_s=scenario.wind_speed_m_s,
        wind_direction_degrees=scenario.wind_direction_degrees,
        temperature_c=scenario.temperature_c,
        relative_humidity_percent=scenario.relative_humidity_percent,
        base_spread_rate_m_h=scenario.base_spread_rate_m_h,
    )
    return artifact, summary


def build_simulation_corpus(
    *,
    output_dir: Path,
    config: SimulationCorpusConfig | None = None,
) -> SimulationCorpusSummary:
    """Write a deterministic Phase 5B simulation corpus to disk."""
    config = config or SimulationCorpusConfig()
    config.validate()
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)

    samples: list[SimulationSampleSummary] = []
    for index in range(config.case_count):
        scenario = sample_simulation_scenario(index, seed=config.seed)
        artifact, summary = build_simulation_sample(scenario, config=config)
        np.savez_compressed(output_dir / summary.artifact, **artifact)
        samples.append(summary)

    manifest = _manifest(config=config, samples=samples)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return SimulationCorpusSummary(
        schema_version=SIMULATION_CORPUS_SCHEMA_VERSION,
        output_dir=output_dir.as_posix(),
        manifest_path=manifest_path.as_posix(),
        sample_count=len(samples),
        forecast_hours=list(config.forecast_hours),
        total_final_burned_cells=int(sum(sample.final_burned_cells for sample in samples)),
    )


def load_simulation_corpus_profiles(path: Path) -> dict[str, SimulationCorpusProfile]:
    """Load named Phase 5B simulation-corpus profiles from a JSON config file."""
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    raw_profiles = raw.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ValueError("Simulation corpus profiles file must contain a non-empty profiles object")

    profiles: dict[str, SimulationCorpusProfile] = {}
    for name, raw_profile in raw_profiles.items():
        if not isinstance(raw_profile, dict):
            raise ValueError(f"Profile {name!r} must be an object")
        raw_config = raw_profile.get("config")
        if not isinstance(raw_config, dict):
            raise ValueError(f"Profile {name!r} must contain a config object")
        forecast_hours = tuple(float(hour) for hour in raw_config.get("forecast_hours", ()))
        config = SimulationCorpusConfig(
            case_count=int(raw_config["case_count"]),
            grid_height=int(raw_config["grid_height"]),
            grid_width=int(raw_config["grid_width"]),
            resolution_m=float(raw_config.get("resolution_m", 60.0)),
            forecast_hours=forecast_hours,
            seed=int(raw_config.get("seed", 1729)),
            base_spread_rate_min_m_h=float(raw_config.get("base_spread_rate_min_m_h", 35.0)),
            base_spread_rate_max_m_h=float(raw_config.get("base_spread_rate_max_m_h", 145.0)),
        )
        config.validate()
        profiles[str(name)] = SimulationCorpusProfile(
            name=str(name),
            description=str(raw_profile.get("description", "")),
            output_dir=Path(str(raw_profile["output_dir"])),
            report_path=Path(str(raw_profile["report_path"])),
            config=config,
            commit_outputs=bool(raw_profile.get("commit_outputs", False)),
        )
    return profiles


def simulation_corpus_profile_report(profile: SimulationCorpusProfile) -> str:
    """Render a short Markdown description of a configured corpus profile."""
    sample_cells = profile.config.grid_height * profile.config.grid_width
    total_masks = profile.config.case_count * len(profile.config.forecast_hours)
    return "\n".join(
        [
            f"## `{profile.name}`",
            "",
            profile.description,
            "",
            f"- Output directory: `{profile.output_dir.as_posix()}`",
            f"- Report path: `{profile.report_path.as_posix()}`",
            f"- Cases: {profile.config.case_count}",
            f"- Grid: {profile.config.grid_height}x{profile.config.grid_width}",
            f"- Forecast horizons: {', '.join(f'{hour:g}h' for hour in profile.config.forecast_hours)}",
            f"- Total forecast masks: {total_masks}",
            f"- Cells per mask: {sample_cells:,}",
            f"- Commit generated samples: `{str(profile.commit_outputs).lower()}`",
            "",
        ]
    )


def render_simulation_corpus_report(summary: SimulationCorpusSummary) -> str:
    """Render a concise Markdown report for a generated simulation corpus."""
    return "\n".join(
        [
            "# FireTwin Phase 5B Simulation Corpus",
            "",
            f"- Schema: `{summary.schema_version}`",
            f"- Output: `{summary.output_dir}`",
            f"- Manifest: `{summary.manifest_path}`",
            f"- Samples: {summary.sample_count}",
            f"- Forecast horizons: {', '.join(f'{hour:g}h' for hour in summary.forecast_hours)}",
            f"- Total final burned cells: {summary.total_final_burned_cells:,}",
            "",
            "This corpus is simulator-derived and intended for surrogate-model development, not as real",
            "wildfire truth.",
            "",
        ]
    )


def _manifest(
    *,
    config: SimulationCorpusConfig,
    samples: list[SimulationSampleSummary],
) -> dict[str, Any]:
    return {
        "schema_version": SIMULATION_CORPUS_SCHEMA_VERSION,
        "target": "simulated_fire_spread_masks",
        "not_real_wildfire_truth": True,
        "generator": "EllipticalBaseline over synthetic terrain/fuel/weather scenarios",
        "config": asdict(config),
        "sample_count": len(samples),
        "samples": [asdict(sample) for sample in samples],
        "guardrails": [
            "Synthetic simulator corpus; not observed fire perimeter truth.",
            "Uses simplified wind-driven elliptical spread for first surrogate scaffolding.",
            "Designed to test surrogate data contracts before hybrid modeling.",
        ],
    }
