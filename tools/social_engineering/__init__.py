"""
ATS MAFIA Framework - Social Engineering Tools

This module contains social engineering tools for training scenarios,
including pretext generation, phishing campaigns, and vishing simulations.

All tools operate in SIMULATION MODE ONLY for training purposes.
"""

from .pretext_generator import PretextGenerator
from .phishing_crafter import PhishingCrafter
from .voice_modulator import VoiceModulator

__all__ = [
    'PretextGenerator',
    'PhishingCrafter',
    'VoiceModulator'
]