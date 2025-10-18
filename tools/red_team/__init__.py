"""
ATS MAFIA Framework - Red Team Tools

This module contains offensive security tools for red team operations,
including reconnaissance, exploitation, post-exploitation, and evasion tools.

All tools operate in SIMULATION MODE ONLY for training purposes.
"""

from .stealth_scanner import StealthScanner
from .osint_collector import OSINTCollector
from .vulnerability_exploiter import VulnerabilityExploiter
from .persistence_installer import PersistenceInstaller
from .data_exfiltrator import DataExfiltrator
from .privilege_escalator import PrivilegeEscalator
from .anti_forensics import AntiForensics
from .payload_obfuscator import PayloadObfuscator

__all__ = [
    'StealthScanner',
    'OSINTCollector',
    'VulnerabilityExploiter',
    'PersistenceInstaller',
    'DataExfiltrator',
    'PrivilegeEscalator',
    'AntiForensics',
    'PayloadObfuscator'
]