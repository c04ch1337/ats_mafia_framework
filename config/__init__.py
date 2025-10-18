"""
ATS MAFIA Framework Configuration Module

This module handles all configuration management for the ATS MAFIA framework,
including default settings, environment-specific configurations, and runtime
parameter management.
"""

from .settings import FrameworkConfig
from .loader import ConfigLoader
from .validator import ConfigValidator

__all__ = [
    "FrameworkConfig",
    "ConfigLoader", 
    "ConfigValidator"
]

# Config module version
__version__ = "1.0.0"