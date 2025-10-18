"""
ATS MAFIA Framework Scenario CLI Commands

Command-line interface commands for scenario management including listing,
viewing, validating, and managing scenarios.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List
from tabulate import tabulate

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ats_mafia_framework.core.scenario_engine import (
    ScenarioLibrary, ScenarioValidator, Scenario,
    DifficultyLevel, ScenarioType
)


class ScenarioCommands:
    """CLI commands for scenario management."""
    
    def __init__(self):
        """Initialize scenario commands."""
        self.library = ScenarioLibrary()
        self.validator = ScenarioValidator()
    
    def list_scenarios(self, 
                      scenario_type: Optional[str] = None,
                      difficulty: Optional[str] = None,
                      tags: Optional[List[str]] = None):
        """
        List available scenarios with optional filtering.
        
        Args:
            scenario_type: Filter by scenario type
            difficulty: Filter by difficulty level
            tags: Filter by tags
        """
        # Convert string filters to enums
        type_filter = ScenarioType(scenario_type) if scenario_type else None
        difficulty_filter = DifficultyLevel(difficulty) if difficulty else None
        
        # Get scenarios
        scenarios = self.library.list_scenarios(
            scenario_type=type_filter,
            difficulty=difficulty_filter,
            tags=tags
        )
        
        if not scenarios:
            print("No scenarios found matching the criteria.")
            return
        
        # Prepare table data
        table_data = []
        for scenario in scenarios:
            table_data.append([
                scenario['id'],
                scenario['name'],
                scenario['type'],
                scenario['difficulty'],
                f"{scenario['estimated_duration_minutes']} min",
                len(scenario['phases']),
                ', '.join(scenario['tags'][:3])
            ])
        
        # Print table
        headers = ['ID', 'Name', 'Type', 'Difficulty', 'Duration', 'Phases', 'Tags']
        print(f"\n📋 Available Scenarios ({len(scenarios)} found)\n")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()
    
    def show_scenario(self, scenario_id: str):
        """
        Display detailed information about a scenario.
        
        Args:
            scenario_id: ID of the scenario to display
        """
        scenario = self.library.get_scenario(scenario_id)
        
        if not scenario:
            print(f"❌ Scenario not found: {scenario_id}")
            return
        
        # Display scenario details
        print("\n" + "=" * 80)
        print(f"📄 SCENARIO: {scenario.name}")
        print("=" * 80)
        
        print(f"\n🆔 ID: {scenario.id}")
        print(f"📝 Description: {scenario.description}")
        print(f"🎯 Type: {scenario.type.value}")
        print(f"⚡ Difficulty: {scenario.difficulty.value}")
        print(f"⏱️  Duration: {scenario.estimated_duration_minutes} minutes")
        print(f"📊 Version: {scenario.version}")
        print(f"✍️  Author: {scenario.author}")
        
        # Required resources
        print(f"\n📋 Required Profiles: {', '.join(scenario.required_profiles)}")
        print(f"🔧 Required Tools: {', '.join(scenario.required_tools)}")
        
        if scenario.optional_profiles:
            print(f"📋 Optional Profiles: {', '.join(scenario.optional_profiles)}")
        if scenario.optional_tools:
            print(f"🔧 Optional Tools: {', '.join(scenario.optional_tools)}")
        
        # Prerequisites
        if scenario.prerequisites:
            print(f"\n⚠️  Prerequisites: {', '.join(scenario.prerequisites)}")
        
        # Tags
        if scenario.tags:
            print(f"\n🏷️  Tags: {', '.join(scenario.tags)}")
        
        # Learning objectives
        if scenario.learning_objectives:
            print(f"\n🎓 Learning Objectives:")
            for i, obj in enumerate(scenario.learning_objectives, 1):
                print(f"  {i}. {obj}")
        
        # Phases
        print(f"\n📑 Phases ({len(scenario.phases)}):")
        for i, phase in enumerate(scenario.phases, 1):
            time_info = f" ({phase.time_limit_minutes} min)" if phase.time_limit_minutes else ""
            print(f"\n  Phase {i}: {phase.name}{time_info}")
            print(f"  {phase.description}")
            print(f"  Objectives: {len(phase.objectives)}")
            if phase.hints:
                print(f"  Hints: {len(phase.hints)}")
        
        # Scoring
        print(f"\n🏆 Scoring:")
        print(f"  Max Points: {scenario.scoring.max_points}")
        print(f"  Time Bonus Multiplier: {scenario.scoring.time_bonus_multiplier}x")
        print(f"  Stealth Bonus: {scenario.scoring.stealth_bonus}")
        print(f"  Completion Bonus: {scenario.scoring.completion_bonus}")
        
        # Statistics
        total_objectives = scenario.get_total_objectives()
        print(f"\n📊 Statistics:")
        print(f"  Total Objectives: {total_objectives}")
        print(f"  Total Phases: {len(scenario.phases)}")
        
        print("\n" + "=" * 80 + "\n")
    
    def validate_scenario(self, file_path: str):
        """
        Validate a scenario JSON file.
        
        Args:
            file_path: Path to the scenario file
        """
        print(f"\n🔍 Validating scenario: {file_path}")
        
        try:
            # Load scenario
            with open(file_path, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            # Create scenario object
            scenario = Scenario.from_dict(scenario_data)
            
            # Validate
            errors = self.validator.validate(scenario)
            
            if errors:
                print(f"\n❌ Validation Failed ({len(errors)} errors):\n")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
                return False
            else:
                print("\n✅ Validation Passed!")
                print(f"\nScenario: {scenario.name}")
                print(f"Type: {scenario.type.value}")
                print(f"Difficulty: {scenario.difficulty.value}")
                print(f"Phases: {len(scenario.phases)}")
                print(f"Total Objectives: {scenario.get_total_objectives()}")
                return True
                
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def scenario_stats(self):
        """Display statistics about available scenarios."""
        stats = self.library.get_statistics()
        
        print("\n" + "=" * 80)
        print("📊 SCENARIO STATISTICS")
        print("=" * 80)
        
        print(f"\n📋 Total Scenarios: {stats['total_scenarios']}")
        print(f"✅ Validated: {stats['scenarios_validated']}")
        print(f"📥 Loaded: {stats['scenarios_loaded']}")
        
        if stats.get('validation_errors'):
            print(f"❌ Validation Errors: {stats['validation_errors']}")
        
        # By type
        if stats.get('scenarios_by_type'):
            print(f"\n🎯 By Type:")
            for scenario_type, count in stats['scenarios_by_type'].items():
                print(f"  {scenario_type}: {count}")
        
        # By difficulty
        if stats.get('scenarios_by_difficulty'):
            print(f"\n⚡ By Difficulty:")
            for difficulty, count in stats['scenarios_by_difficulty'].items():
                print(f"  {difficulty}: {count}")
        
        print("\n" + "=" * 80 + "\n")
    
    def start_scenario(self, scenario_id: str):
        """
        Display instructions for starting a scenario.
        
        Args:
            scenario_id: ID of the scenario to start
        """
        scenario = self.library.get_scenario(scenario_id)
        
        if not scenario:
            print(f"❌ Scenario not found: {scenario_id}")
            return
        
        print("\n" + "=" * 80)
        print(f"🚀 STARTING SCENARIO: {scenario.name}")
        print("=" * 80)
        
        print(f"\n📋 Required Profiles: {', '.join(scenario.required_profiles)}")
        print(f"🔧 Required Tools: {', '.join(scenario.required_tools)}")
        print(f"⏱️  Estimated Duration: {scenario.estimated_duration_minutes} minutes")
        
        if scenario.prerequisites:
            print(f"\n⚠️  Prerequisites:")
            for prereq in scenario.prerequisites:
                print(f"  - {prereq}")
        
        print(f"\n📝 Description:")
        print(f"  {scenario.description}")
        
        print(f"\n🎓 Learning Objectives:")
        for i, obj in enumerate(scenario.learning_objectives, 1):
            print(f"  {i}. {obj}")
        
        print(f"\n📑 Phases:")
        for i, phase in enumerate(scenario.phases, 1):
            print(f"  Phase {i}: {phase.name}")
        
        print("\n" + "-" * 80)
        print("To start this scenario programmatically, use the TrainingOrchestrator:")
        print(f"  orchestrator.create_session(")
        print(f"      name='{scenario.name}',")
        print(f"      description='{scenario.description}',")
        print(f"      scenario_id='{scenario.id}',")
        print(f"      agent_configs=[...],")
        print(f"  )")
        print("=" * 80 + "\n")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ATS MAFIA Scenario Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list-scenarios command
    list_parser = subparsers.add_parser('list-scenarios', help='List available scenarios')
    list_parser.add_argument('--type', help='Filter by scenario type')
    list_parser.add_argument('--difficulty', help='Filter by difficulty level')
    list_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    
    # show-scenario command
    show_parser = subparsers.add_parser('show-scenario', help='Show scenario details')
    show_parser.add_argument('scenario_id', help='Scenario ID')
    
    # validate-scenario command
    validate_parser = subparsers.add_parser('validate-scenario', help='Validate scenario file')
    validate_parser.add_argument('file', help='Path to scenario JSON file')
    
    # start-scenario command
    start_parser = subparsers.add_parser('start-scenario', help='Start a scenario')
    start_parser.add_argument('scenario_id', help='Scenario ID')
    
    # scenario-stats command
    subparsers.add_parser('scenario-stats', help='Show scenario statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = ScenarioCommands()
    
    try:
        if args.command == 'list-scenarios':
            commands.list_scenarios(
                scenario_type=args.type,
                difficulty=args.difficulty,
                tags=args.tags
            )
        elif args.command == 'show-scenario':
            commands.show_scenario(args.scenario_id)
        elif args.command == 'validate-scenario':
            success = commands.validate_scenario(args.file)
            sys.exit(0 if success else 1)
        elif args.command == 'start-scenario':
            commands.start_scenario(args.scenario_id)
        elif args.command == 'scenario-stats':
            commands.scenario_stats()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()