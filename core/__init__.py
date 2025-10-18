"""
ATS MAFIA Framework Core Module

This module contains the core components of the ATS MAFIA framework:
- Training Orchestrator: Manages training sessions and scenarios
- Profile Manager: Handles agent profile creation and management
- Tool System: Manages tool extensions and integrations
- Communication Protocol: Handles agent-to-agent communication
- Logging System: Provides comprehensive logging and audit trails
"""

from .orchestrator import TrainingOrchestrator
from .profile_manager import ProfileManager
from .tool_system import ToolRegistry
from .communication import CommunicationProtocol
from .logging import AuditLogger

__all__ = [
    "TrainingOrchestrator",
    "ProfileManager",
    "ToolRegistry",
    "CommunicationProtocol",
    "AuditLogger"
]

# Core module version
__version__ = "1.0.0"