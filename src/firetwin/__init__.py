"""
FireTwin: A research-grade wildfire digital twin.

FireTwin combines satellite observations, weather, terrain and vegetation
with physics-guided machine learning to produce probabilistic fire-spread
forecasts and evaluate simulated containment strategies.
"""

__version__ = "0.1.0"
__author__ = "Rajat Gupta"
__email__ = "rajatgupta116@gmail.com"

from firetwin import settings

__all__ = ["settings", "__version__"]
