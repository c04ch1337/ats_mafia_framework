"""
ATS MAFIA Framework Command Line Interface

Provides command-line access to framework functionality for training management,
profile administration, and system operations.
"""

import argparse
import asyncio
import json
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from ..config.settings import FrameworkConfig, load_config
from ..core.logging import AuditLogger, initialize_audit_logger
from ..core.profile_manager import ProfileManager, initialize_profile_manager
from ..core.tool_system import ToolRegistry
from ..core.communication import CommunicationProtocol
from ..core.orchestrator import TrainingOrchestrator, initialize_training_orchestrator


class ATSMAFIACLI:
    """Command line interface for ATS MAFIA Framework."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config: Optional[FrameworkConfig] = None
        self.audit_logger: Optional[AuditLogger] = None
        self.profile_manager: Optional[ProfileManager] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.communication: Optional[CommunicationProtocol] = None
        self.orchestrator: Optional[TrainingOrchestrator] = None
    
    async def initialize(self, config_file: Optional[str] = None) -> bool:
        """
        Initialize framework components.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load configuration
            if config_file:
                self.config = FrameworkConfig.from_file(config_file)
            else:
                # Use default configuration
                self.config = FrameworkConfig()
            
            # Initialize components
            self.audit_logger = initialize_audit_logger(self.config)
            self.profile_manager = initialize_profile_manager(self.config, self.audit_logger)
            self.tool_registry = ToolRegistry(self.config)
            self.communication = CommunicationProtocol(
                "cli_agent", self.config, self.audit_logger
            )
            self.orchestrator = initialize_training_orchestrator(
                self.config, self.profile_manager, self.tool_registry, 
                self.communication, self.audit_logger
            )
            
            print("✅ ATS MAFIA Framework initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize framework: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup framework components."""
        try:
            if self.communication:
                await self.communication.stop_server()
            
            if self.orchestrator:
                await self.orchestrator.shutdown()
            
            print("✅ Framework cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Warning during cleanup: {e}")
    
    async def list_profiles(self, profile_type: Optional[str] = None) -> None:
        """
        List available profiles.
        
        Args:
            profile_type: Filter by profile type
        """
        if not self.profile_manager:
            print("❌ Profile manager not initialized")
            return
        
        try:
            profiles = self.profile_manager.list_profiles()
            
            if profile_type:
                profiles = [p for p in profiles if p['profile_type'] == profile_type]
            
            if not profiles:
                print("No profiles found")
                return
            
            print(f"\n📋 Available Profiles ({len(profiles)}):")
            print("-" * 80)
            
            for profile in profiles:
                print(f"🏷️  {profile['name']} ({profile['id']})")
                print(f"   Type: {profile['profile_type']}")
                print(f"   Category: {profile['category']}")
                print(f"   Description: {profile['description'][:80]}...")
                print(f"   Version: {profile['version']}")
                print(f"   Author: {profile['author']}")
                print(f"   Tags: {', '.join(profile['tags'])}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing profiles: {e}")
    
    async def list_scenarios(self, scenario_type: Optional[str] = None) -> None:
        """
        List available scenarios.
        
        Args:
            scenario_type: Filter by scenario type
        """
        if not self.orchestrator:
            print("❌ Training orchestrator not initialized")
            return
        
        try:
            scenarios = self.orchestrator.list_scenarios()
            
            if scenario_type:
                scenarios = [s for s in scenarios if s['scenario_type'] == scenario_type]
            
            if not scenarios:
                print("No scenarios found")
                return
            
            print(f"\n🎭 Available Scenarios ({len(scenarios)}):")
            print("-" * 80)
            
            for scenario in scenarios:
                print(f"🎯 {scenario['name']} ({scenario['id']})")
                print(f"   Type: {scenario['scenario_type']}")
                print(f"   Duration: {scenario['duration']} seconds")
                print(f"   Max Agents: {scenario['max_agents']}")
                print(f"   Description: {scenario['description'][:80]}...")
                print(f"   Required Profiles: {', '.join(scenario['required_profiles'])}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing scenarios: {e}")
    
    async def create_session(self, 
                           name: str,
                           description: str,
                           scenario_id: str,
                           profile_ids: list) -> None:
        """
        Create a training session.
        
        Args:
            name: Session name
            description: Session description
            scenario_id: Scenario ID
            profile_ids: List of profile IDs
        """
        if not self.orchestrator:
            print("❌ Training orchestrator not initialized")
            return
        
        try:
            # Create agent configurations
            agent_configs = []
            for i, profile_id in enumerate(profile_ids):
                agent_configs.append({
                    "profile_id": profile_id,
                    "role": f"agent_{i+1}"
                })
            
            # Create session
            session_id = await self.orchestrator.create_session(
                name=name,
                description=description,
                scenario_id=scenario_id,
                agent_configs=agent_configs
            )
            
            if session_id:
                print(f"✅ Training session created: {session_id}")
                print(f"   Name: {name}")
                print(f"   Scenario: {scenario_id}")
                print(f"   Agents: {len(agent_configs)}")
                
                # Ask if user wants to start the session
                response = input("\n🚀 Start this session now? (y/n): ").lower().strip()
                if response == 'y':
                    success = await self.orchestrator.start_session(session_id)
                    if success:
                        print(f"✅ Session {session_id} started successfully")
                    else:
                        print(f"❌ Failed to start session {session_id}")
            else:
                print("❌ Failed to create training session")
                
        except Exception as e:
            print(f"❌ Error creating session: {e}")
    
    async def list_sessions(self, status: Optional[str] = None) -> None:
        """
        List training sessions.
        
        Args:
            status: Filter by session status
        """
        if not self.orchestrator:
            print("❌ Training orchestrator not initialized")
            return
        
        try:
            sessions = self.orchestrator.list_sessions()
            
            if status:
                sessions = [s for s in sessions if s['status'] == status]
            
            if not sessions:
                print("No sessions found")
                return
            
            print(f"\n📊 Training Sessions ({len(sessions)}):")
            print("-" * 80)
            
            for session in sessions:
                print(f"🎯 {session['name']} ({session['id'][:8]}...)")
                print(f"   Status: {session['status']}")
                print(f"   Scenario: {session['scenario']['name']}")
                print(f"   Agents: {len(session['agents'])}")
                
                if session['start_time']:
                    print(f"   Started: {session['start_time']}")
                if session['end_time']:
                    print(f"   Ended: {session['end_time']}")
                    duration = session['metrics'].get('execution_time', 0)
                    print(f"   Duration: {duration:.1f} seconds")
                
                print()
                
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")
    
    async def get_session_status(self, session_id: str) -> None:
        """
        Get detailed status of a training session.
        
        Args:
            session_id: Session ID
        """
        if not self.orchestrator:
            print("❌ Training orchestrator not initialized")
            return
        
        try:
            session = self.orchestrator.get_session(session_id)
            
            if not session:
                print(f"❌ Session {session_id} not found")
                return
            
            print(f"\n📊 Session Status: {session.name}")
            print("-" * 80)
            print(f"ID: {session.id}")
            print(f"Status: {session.status.value}")
            print(f"Description: {session.description}")
            print(f"Scenario: {session.scenario.name}")
            print(f"Agents: {len(session.agents)}")
            
            if session.start_time:
                print(f"Started: {session.start_time}")
            if session.end_time:
                print(f"Ended: {session.end_time}")
            
            # Agent status
            print(f"\n🤖 Agent Status:")
            for agent in session.agents:
                print(f"   {agent.id[:8]}... ({agent.profile_id}) - {agent.status}")
            
            # Metrics
            if session.metrics:
                print(f"\n📈 Session Metrics:")
                for key, value in session.metrics.items():
                    print(f"   {key}: {value}")
            
            # Recent logs
            if session.logs:
                print(f"\n📝 Recent Logs (last 5):")
                for log in session.logs[-5:]:
                    print(f"   {log.get('timestamp', 'N/A')} - {log.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Error getting session status: {e}")
    
    async def show_statistics(self) -> None:
        """Show framework statistics."""
        if not self.orchestrator:
            print("❌ Training orchestrator not initialized")
            return
        
        try:
            # Orchestrator stats
            orch_stats = self.orchestrator.get_statistics()
            
            print("\n📊 Framework Statistics")
            print("-" * 80)
            
            print(f"🎯 Training Sessions:")
            print(f"   Total: {orch_stats['total_sessions']}")
            print(f"   Active: {orch_stats['active_sessions']}")
            print(f"   Completed: {orch_stats['sessions_completed']}")
            print(f"   Failed: {orch_stats['sessions_failed']}")
            
            print(f"\n📋 Scenarios:")
            print(f"   Available: {orch_stats['available_scenarios']}")
            
            if orch_stats.get('sessions_by_status'):
                print(f"\n📈 Sessions by Status:")
                for status, count in orch_stats['sessions_by_status'].items():
                    print(f"   {status}: {count}")
            
            if orch_stats.get('sessions_by_scenario'):
                print(f"\n🎭 Sessions by Scenario:")
                for scenario, count in orch_stats['sessions_by_scenario'].items():
                    print(f"   {scenario}: {count}")
            
            # Profile manager stats
            if self.profile_manager:
                profile_stats = self.profile_manager.get_statistics()
                
                print(f"\n👥 Agent Profiles:")
                print(f"   Total: {profile_stats['total_profiles']}")
                
                if profile_stats.get('profiles_by_type'):
                    print(f"   By Type:")
                    for profile_type, count in profile_stats['profiles_by_type'].items():
                        print(f"     {profile_type}: {count}")
                
                if profile_stats.get('cache'):
                    cache_stats = profile_stats['cache']
                    print(f"\n💾 Cache Statistics:")
                    print(f"   Size: {cache_stats['size']}/{cache_stats['max_size']}")
                    print(f"   Hit Rate: {cache_stats.get('hit_rate', 0):.1%}")
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="ATS MAFIA Framework - Advanced Training System for Multi-Agent Interactive Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s profile list
  %(prog)s scenario list
  %(prog)s session create --name "Test Session" --scenario basic_penetration_test --profiles red_team_operator
  %(prog)s session list
  %(prog)s session status <session_id>
  %(prog)s stats
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Profile commands
    profile_parser = subparsers.add_parser('profile', help='Profile management')
    profile_subparsers = profile_parser.add_subparsers(dest='profile_command')
    
    profile_list_parser = profile_subparsers.add_parser('list', help='List profiles')
    profile_list_parser.add_argument(
        '--type',
        type=str,
        help='Filter by profile type'
    )
    
    # Scenario commands
    scenario_parser = subparsers.add_parser('scenario', help='Scenario management')
    scenario_subparsers = scenario_parser.add_subparsers(dest='scenario_command')
    
    scenario_list_parser = scenario_subparsers.add_parser('list', help='List scenarios')
    scenario_list_parser.add_argument(
        '--type',
        type=str,
        help='Filter by scenario type'
    )
    
    # Session commands
    session_parser = subparsers.add_parser('session', help='Session management')
    session_subparsers = session_parser.add_subparsers(dest='session_command')
    
    session_create_parser = session_subparsers.add_parser('create', help='Create session')
    session_create_parser.add_argument('--name', required=True, help='Session name')
    session_create_parser.add_argument('--description', required=True, help='Session description')
    session_create_parser.add_argument('--scenario', required=True, help='Scenario ID')
    session_create_parser.add_argument('--profiles', nargs='+', required=True, help='Profile IDs')
    
    session_list_parser = session_subparsers.add_parser('list', help='List sessions')
    session_list_parser.add_argument('--status', help='Filter by status')
    
    session_status_parser = session_subparsers.add_parser('status', help='Get session status')
    session_status_parser.add_argument('session_id', help='Session ID')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show framework statistics')
    
    return parser


async def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        # No command provided, start the framework in server mode
        print("🚀 Starting ATS MAFIA Framework in server mode...")
        cli = ATSMAFIACLI()
        
        try:
            # Initialize framework
            if await cli.initialize(args.config):
                print("✅ Framework started successfully. Press Ctrl+C to stop.")
                # Keep the server running
                while True:
                    await asyncio.sleep(1)
            else:
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down framework...")
        finally:
            await cli.cleanup()
        return
    
    # Initialize CLI
    cli = ATSMAFIACLI()
    
    try:
        # Initialize framework
        if not await cli.initialize(args.config):
            sys.exit(1)
        
        # Execute command
        if args.command == 'profile':
            if args.profile_command == 'list':
                await cli.list_profiles(args.type)
            else:
                print("❌ Unknown profile command")
        
        elif args.command == 'scenario':
            if args.scenario_command == 'list':
                await cli.list_scenarios(args.type)
            else:
                print("❌ Unknown scenario command")
        
        elif args.command == 'session':
            if args.session_command == 'create':
                await cli.create_session(
                    args.name, args.description, args.scenario, args.profiles
                )
            elif args.session_command == 'list':
                await cli.list_sessions(args.status)
            elif args.session_command == 'status':
                await cli.get_session_status(args.session_id)
            else:
                print("❌ Unknown session command")
        
        elif args.command == 'stats':
            await cli.show_statistics()
        
        else:
            print(f"❌ Unknown command: {args.command}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        # Cleanup
        await cli.cleanup()


def cli_main() -> None:
    """CLI entry point for setup.py."""
    asyncio.run(main())


if __name__ == '__main__':
    cli_main()