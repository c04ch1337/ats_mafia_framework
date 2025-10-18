"""
Remote Tool Adapters
Execute real security tools via Kali Linux sandbox container.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

# Import remote tool adapters
try:
    from .nmap_remote import NmapRemoteTool
    from .metasploit_remote import MetasploitRemoteTool
    from .sqlmap_remote import SqlmapRemoteTool
    from .burpsuite_remote import BurpSuiteRemoteTool
    from .hydra_remote import HydraRemoteTool
    
    __all__ = [
        'NmapRemoteTool',
        'MetasploitRemoteTool',
        'SqlmapRemoteTool',
        'BurpSuiteRemoteTool',
        'HydraRemoteTool',
        'get_all_remote_tools',
    ]
    
    logger.info("Remote tool adapters loaded successfully")
    
except ImportError as e:
    logger.warning(f"Failed to import some remote tools: {e}")
    
    # Provide stub classes if imports fail
    class NmapRemoteTool:
        def __init__(self):
            raise RuntimeError("NmapRemoteTool not available")
    
    class MetasploitRemoteTool:
        def __init__(self):
            raise RuntimeError("MetasploitRemoteTool not available")
    
    class SqlmapRemoteTool:
        def __init__(self):
            raise RuntimeError("SqlmapRemoteTool not available")
    
    class BurpSuiteRemoteTool:
        def __init__(self):
            raise RuntimeError("BurpSuiteRemoteTool not available")
    
    class HydraRemoteTool:
        def __init__(self):
            raise RuntimeError("HydraRemoteTool not available")
    
    __all__ = [
        'NmapRemoteTool',
        'MetasploitRemoteTool',
        'SqlmapRemoteTool',
        'BurpSuiteRemoteTool',
        'HydraRemoteTool',
        'get_all_remote_tools',
    ]


def get_all_remote_tools() -> List[any]:
    """
    Get list of all available remote tool classes.
    
    Returns:
        List of remote tool classes
    """
    return [
        NmapRemoteTool,
        MetasploitRemoteTool,
        SqlmapRemoteTool,
        BurpSuiteRemoteTool,
        HydraRemoteTool,
    ]