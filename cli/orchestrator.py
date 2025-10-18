#!/usr/bin/env python3
"""
ATS MAFIA Framework Orchestrator CLI

Provides command-line interface for training orchestration functionality.
"""

import argparse
import asyncio
import sys
from typing import Optional
from pathlib import Path

from ..core.orchestrator import TrainingOrchestrator, initialize_training_orchestrator
from ..core.profile_manager import initialize_profile_manager
from ..core.logging import initialize_audit_logger
from ..core.tool_system import ToolRegistry
from ..core.communication import CommunicationProtocol
from ..config.settings import load_config, FrameworkConfig


async def start_orchestrator(config_file: Optional[str] = None, 
                           host: str = "0.0.0.0", 
                           port: int = 8080) -> None:
    """
    Start the training orchestrator server.
    
    Args:
        config_file: Path to configuration file
        host: Host to bind to
        port: Port to bind to
    """
    try:
        # Load configuration
        if config_file:
            config = load_config(Path(config_file))
        else:
            # Use default configuration
            config = FrameworkConfig()
        
        # Initialize components
        audit_logger = initialize_audit_logger(config)
        profile_manager = initialize_profile_manager(config, audit_logger)
        tool_registry = ToolRegistry(config)
        communication = CommunicationProtocol("orchestrator", config, audit_logger)
        
        # Initialize orchestrator
        orchestrator = initialize_training_orchestrator(
            config, profile_manager, tool_registry, communication, audit_logger
        )
        
        print(f"🚀 Starting ATS MAFIA Orchestrator on {host}:{port}")
        
        # Start the orchestrator (this would typically start a web server)
        # For now, we'll just keep it running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down orchestrator...")
            await orchestrator.shutdown()
            print("✅ Orchestrator shutdown complete")
            
    except Exception as e:
        print(f"❌ Failed to start orchestrator: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for orchestrator CLI."""
    parser = argparse.ArgumentParser(
        description="ATS MAFIA Framework Training Orchestrator"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port to bind to (default: 8080)'
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(start_orchestrator(args.config, args.host, args.port))
    except KeyboardInterrupt:
        print("\n⚠️  Orchestrator stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()