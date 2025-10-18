"""
ATS MAFIA Framework - Kali Linux Sandbox Integration
Phase 7: Real Security Tools in Controlled Environment

This module provides secure access to Kali Linux tools running in isolated Docker containers.
Agents can execute real security tools (nmap, metasploit, sqlmap, etc.) with proper safety controls.
"""

from typing import Dict, List, Optional
import logging

# Version and metadata
__version__ = "1.0.0"
__author__ = "ATS MAFIA Team"
__description__ = "Kali Linux Sandbox Integration for Real Security Tools"

# Setup logging
logger = logging.getLogger(__name__)

# Import main components
try:
    from .kali_connector import KaliConnector
    from .tool_whitelist import (
        APPROVED_TOOLS,
        validate_command,
        is_tool_approved
    )
    from .sandbox_manager import SandboxManager
    from .security_monitor import SecurityMonitor
    from .network_isolation import NetworkIsolation
    
    __all__ = [
        'KaliConnector',
        'SandboxManager',
        'SecurityMonitor',
        'NetworkIsolation',
        'APPROVED_TOOLS',
        'validate_command',
        'is_tool_approved',
    ]
    
except ImportError as e:
    logger.warning(f"Failed to import sandbox components: {e}")
    logger.warning("Docker may not be available. Sandbox features will be disabled.")
    
    # Provide stub classes if imports fail
    class KaliConnector:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docker not available. Cannot create KaliConnector.")
    
    class SandboxManager:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docker not available. Cannot create SandboxManager.")
    
    class SecurityMonitor:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docker not available. Cannot create SecurityMonitor.")
    
    class NetworkIsolation:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docker not available. Cannot create NetworkIsolation.")
    
    APPROVED_TOOLS = {}
    
    def validate_command(command: str):
        raise RuntimeError("Docker not available. Cannot validate commands.")
    
    def is_tool_approved(tool: str) -> bool:
        return False
    
    __all__ = [
        'KaliConnector',
        'SandboxManager',
        'SecurityMonitor',
        'NetworkIsolation',
        'APPROVED_TOOLS',
        'validate_command',
        'is_tool_approved',
    ]


# Sandbox configuration
SANDBOX_CONFIG = {
    'container_name': 'ats_kali_sandbox',
    'max_execution_time': 300,  # 5 minutes
    'max_cpu_percent': 200,  # 2 cores
    'max_memory_mb': 4096,  # 4GB
    'network_isolated': True,
    'auto_cleanup': True,
    'audit_logging': True,
}


def get_sandbox_status() -> Dict[str, any]:
    """
    Get current status of sandbox system.
    
    Returns:
        Dict containing sandbox status information
    """
    try:
        connector = KaliConnector()
        return connector.get_container_status()
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'message': 'Sandbox system not available'
        }


def check_sandbox_requirements() -> bool:
    """
    Check if all requirements for sandbox system are met.
    
    Returns:
        True if requirements are met, False otherwise
    """
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


logger.info(f"ATS MAFIA Sandbox module initialized (v{__version__})")
if check_sandbox_requirements():
    logger.info("Docker available - Sandbox features enabled")
else:
    logger.warning("Docker not available - Sandbox features disabled")