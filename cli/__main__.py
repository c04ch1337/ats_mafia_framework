"""
Entry point for running the ATS MAFIA Framework CLI as a module.

This allows the CLI to be executed with:
python -m ats_mafia_framework.cli
"""

from .main import cli_main

if __name__ == '__main__':
    cli_main()