"""
ATS MAFIA Framework Command Line Interface

This file provides backward compatibility for imports that reference the old cli.py file.
The actual CLI implementation has been moved to the cli module.
"""

# Import the main functions from the new module structure
from .cli.main import main, cli_main, ATSMAFIACLI

# Re-export for backward compatibility
__all__ = ['main', 'cli_main', 'ATSMAFIACLI']