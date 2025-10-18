"""
ATS MAFIA Framework Profiles Module

This module contains agent profile definitions for the ATS MAFIA framework.
Profiles define agent capabilities, personality traits, knowledge bases, and behavior settings.
"""

from .red_team import *
from .blue_team import *
from .social_engineer import *

__all__ = [
    "RedTeamOperatorProfile",
    "BlueTeamDefenderProfile", 
    "SocialEngineerProfile"
]