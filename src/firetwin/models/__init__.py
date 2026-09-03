"""Fire spread forecast models and baselines."""

from firetwin.models.baselines import EllipticalBaseline, PersistenceBaseline, RadialBaseline

__all__ = ["PersistenceBaseline", "RadialBaseline", "EllipticalBaseline"]
