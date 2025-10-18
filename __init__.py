"""
ATS MAFIA Framework - Advanced Training System for Multi-Agent Interactive Framework

A comprehensive framework for creating, managing, and training specialized agent profiles
for various security scenarios including red team, blue team, and social engineering simulations.

Author: ATS MAFIA Team
Version: 1.0.0
License: Proprietary
"""

__version__ = "1.0.0"
__author__ = "ATS MAFIA Team"
__license__ = "Proprietary"
__description__ = "Advanced Training System for Multi-Agent Interactive Framework"

# Core imports
from .core.orchestrator import TrainingOrchestrator
from .core.profile_manager import ProfileManager
from .core.tool_system import ToolRegistry
from .core.communication import CommunicationProtocol
from .core.logging import AuditLogger

# Configuration
from .config.settings import FrameworkConfig

# Framework metadata
FRAMEWORK_INFO = {
    "name": "ATS MAFIA Framework",
    "version": __version__,
    "author": __author__,
    "license": __license__,
    "description": __description__,
    "components": {
        "orchestrator": TrainingOrchestrator,
        "profile_manager": ProfileManager,
        "tool_system": ToolRegistry,
        "communication": CommunicationProtocol,
        "logger": AuditLogger,
        "config": FrameworkConfig
    }
}

__all__ = [
    "TrainingOrchestrator",
    "ProfileManager",
    "ToolRegistry",
    "CommunicationProtocol",
    "AuditLogger",
    "FrameworkConfig",
    "FRAMEWORK_INFO"
]