"""Physics-based fire spread simulation and surrogate-corpus utilities."""

from firetwin.simulation.corpus import (
    SIMULATION_CORPUS_SCHEMA_VERSION,
    SimulationCorpusConfig,
    SimulationCorpusProfile,
    SimulationCorpusSummary,
    SimulationSampleSummary,
    SimulationScenario,
    build_simulation_corpus,
    build_simulation_sample,
    load_simulation_corpus_profiles,
    render_simulation_corpus_report,
    sample_simulation_scenario,
    simulation_corpus_profile_report,
)

__all__ = [
    "SIMULATION_CORPUS_SCHEMA_VERSION",
    "SimulationCorpusConfig",
    "SimulationCorpusProfile",
    "SimulationCorpusSummary",
    "SimulationSampleSummary",
    "SimulationScenario",
    "build_simulation_corpus",
    "build_simulation_sample",
    "load_simulation_corpus_profiles",
    "render_simulation_corpus_report",
    "sample_simulation_scenario",
    "simulation_corpus_profile_report",
]
