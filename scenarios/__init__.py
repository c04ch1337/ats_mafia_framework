"""
ATS MAFIA Framework Scenarios Module

This module contains training scenario definitions for the ATS MAFIA framework.
Scenarios define training exercises, environments, objectives, and evaluation criteria.
"""

from .red_team_exercises import *
from .blue_team_exercises import *
from .combined_exercises import *

__all__ = [
    "BasicPenetrationTest",
    "NetworkDefenseExercise",
    "RedVsBlueExercise"
]