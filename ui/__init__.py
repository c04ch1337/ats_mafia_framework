"""
ATS MAFIA Framework UI Module

This module contains user interface components for the ATS MAFIA framework.
Includes web-based dashboards, monitoring interfaces, and training scenario controls.
"""

from .dashboard import *
from .controls import *

__all__ = [
    "TrainingDashboard",
    "ScenarioControls"
]