"""Physics-based fire spread simulation and surrogate-corpus utilities."""

from firetwin.simulation.corpus import (
    SIMULATION_CORPUS_SCHEMA_VERSION,
    SimulationCorpusConfig,
    SimulationCorpusSummary,
    SimulationSampleSummary,
    SimulationScenario,
    build_simulation_corpus,
    build_simulation_sample,
    render_simulation_corpus_report,
    sample_simulation_scenario,
)

__all__ = [
    "SIMULATION_CORPUS_SCHEMA_VERSION",
    "SimulationCorpusConfig",
    "SimulationCorpusSummary",
    "SimulationSampleSummary",
    "SimulationScenario",
    "build_simulation_corpus",
    "build_simulation_sample",
    "render_simulation_corpus_report",
    "sample_simulation_scenario",
]
