"""
ATS MAFIA Framework Scenario Builder CLI Tool

Interactive command-line tool for creating custom training scenarios.
Provides templates, validation, and guided scenario creation.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ats_mafia_framework.core.scenario_engine import (
    DifficultyLevel, ScenarioType, ScenarioPhase, Scenario,
    Objective, SuccessCriteria, Hint, ScoringConfig, ScenarioValidator
)


class ScenarioBuilder:
    """Interactive scenario builder for creating custom training scenarios."""
    
    def __init__(self):
        """Initialize the scenario builder."""
        self.validator = ScenarioValidator()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load scenario templates."""
        return {
            'red_team': {
                'type': ScenarioType.RED_TEAM,
                'difficulty': DifficultyLevel.INTERMEDIATE,
                'required_profiles': ['phantom', 'red_team_operator'],
                'required_tools': ['network_scanner', 'exploitation_framework']
            },
            'blue_team': {
                'type': ScenarioType.BLUE_TEAM,
                'difficulty': DifficultyLevel.INTERMEDIATE,
                'required_profiles': ['watcher', 'incident_responder'],
                'required_tools': ['siem', 'network_monitor']
            },
            'social_engineering': {
                'type': ScenarioType.SOCIAL_ENGINEERING,
                'difficulty': DifficultyLevel.INTERMEDIATE,
                'required_profiles': ['puppet_master'],
                'required_tools': ['pretext_generator', 'osint_tools']
            }
        }
    
    def run(self):
        """Run the interactive scenario builder."""
        print("\n" + "=" * 70)
        print("ATS MAFIA FRAMEWORK - SCENARIO BUILDER")
        print("=" * 70)
        print("\nCreate custom training scenarios for the ATS MAFIA framework.")
        print("This wizard will guide you through the process.\n")
        
        # Select template or start from scratch
        template_choice = self._select_template()
        
        # Build scenario
        scenario_data = self._build_scenario(template_choice)
        
        # Validate scenario
        if not self._validate_scenario(scenario_data):
            print("\n❌ Scenario validation failed. Please review errors and try again.")
            return
        
        # Save scenario
        self._save_scenario(scenario_data)
        
        print("\n✅ Scenario created successfully!")
    
    def _select_template(self) -> Optional[str]:
        """Select a scenario template."""
        print("\n📋 STEP 1: Select Template")
        print("-" * 70)
        print("1. Red Team Scenario")
        print("2. Blue Team Scenario")
        print("3. Social Engineering Scenario")
        print("4. Start from Scratch")
        
        while True:
            choice = input("\nSelect option (1-4): ").strip()
            if choice == '1':
                return 'red_team'
            elif choice == '2':
                return 'blue_team'
            elif choice == '3':
                return 'social_engineering'
            elif choice == '4':
                return None
            else:
                print("Invalid choice. Please select 1-4.")
    
    def _build_scenario(self, template: Optional[str]) -> Dict[str, Any]:
        """Build scenario interactively."""
        scenario_data = {}
        
        # Load template if selected
        if template:
            scenario_data.update(self.templates[template])
            print(f"\n✓ Using {template.replace('_', ' ').title()} template")
        
        # Basic information
        scenario_data.update(self._get_basic_info(scenario_data))
        
        # Scenario type and difficulty
        if 'type' not in scenario_data:
            scenario_data['type'] = self._select_scenario_type()
        if 'difficulty' not in scenario_data:
            scenario_data['difficulty'] = self._select_difficulty()
        
        # Duration and requirements
        scenario_data.update(self._get_requirements(scenario_data))
        
        # Learning objectives
        scenario_data['learning_objectives'] = self._get_learning_objectives()
        
        # Tags
        scenario_data['tags'] = self._get_tags()
        
        # Phases
        scenario_data['phases'] = self._build_phases()
        
        # Scoring
        scenario_data['scoring'] = self._configure_scoring()
        
        # Metadata
        scenario_data['metadata'] = self._get_metadata()
        
        # Auto-generated fields
        scenario_data['version'] = '1.0.0'
        scenario_data['author'] = input("\nAuthor name: ").strip() or "ATS MAFIA User"
        
        return scenario_data
    
    def _get_basic_info(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic scenario information."""
        print("\n📝 STEP 2: Basic Information")
        print("-" * 70)
        
        data = {}
        data['id'] = input("Scenario ID (lowercase with underscores): ").strip()
        data['name'] = input("Scenario Name: ").strip()
        data['description'] = input("Description: ").strip()
        
        return data
    
    def _select_scenario_type(self) -> str:
        """Select scenario type."""
        print("\n🎯 Scenario Type:")
        print("1. Red Team")
        print("2. Blue Team")
        print("3. Social Engineering")
        print("4. Red vs Blue")
        print("5. Multi-Stage")
        
        type_map = {
            '1': 'red_team',
            '2': 'blue_team',
            '3': 'social_engineering',
            '4': 'red_vs_blue',
            '5': 'multi_stage'
        }
        
        while True:
            choice = input("Select type (1-5): ").strip()
            if choice in type_map:
                return type_map[choice]
            print("Invalid choice. Please select 1-5.")
    
    def _select_difficulty(self) -> str:
        """Select difficulty level."""
        print("\n⚡ Difficulty Level:")
        print("1. Novice")
        print("2. Intermediate")
        print("3. Advanced")
        print("4. Expert")
        print("5. Master")
        
        difficulty_map = {
            '1': 'novice',
            '2': 'intermediate',
            '3': 'advanced',
            '4': 'expert',
            '5': 'master'
        }
        
        while True:
            choice = input("Select difficulty (1-5): ").strip()
            if choice in difficulty_map:
                return difficulty_map[choice]
            print("Invalid choice. Please select 1-5.")
    
    def _get_requirements(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get scenario requirements."""
        print("\n⚙️  STEP 3: Requirements")
        print("-" * 70)
        
        data = {}
        
        # Duration
        duration = input("Estimated duration (minutes) [60]: ").strip()
        data['estimated_duration_minutes'] = int(duration) if duration else 60
        
        # Required profiles
        if 'required_profiles' not in current_data:
            print("\nRequired Profiles (comma-separated):")
            print("Examples: phantom, watcher, puppet_master")
            profiles = input("Profiles: ").strip()
            data['required_profiles'] = [p.strip() for p in profiles.split(',') if p.strip()]
        
        # Required tools
        if 'required_tools' not in current_data:
            print("\nRequired Tools (comma-separated):")
            print("Examples: network_scanner, siem, exploitation_framework")
            tools = input("Tools: ").strip()
            data['required_tools'] = [t.strip() for t in tools.split(',') if t.strip()]
        
        # Optional profiles
        print("\nOptional Profiles (comma-separated, or press Enter to skip):")
        opt_profiles = input("Profiles: ").strip()
        data['optional_profiles'] = [p.strip() for p in opt_profiles.split(',') if p.strip()]
        
        # Optional tools
        print("\nOptional Tools (comma-separated, or press Enter to skip):")
        opt_tools = input("Tools: ").strip()
        data['optional_tools'] = [t.strip() for t in opt_tools.split(',') if t.strip()]
        
        # Prerequisites
        print("\nPrerequisite Scenarios (comma-separated IDs, or press Enter to skip):")
        prereqs = input("Prerequisites: ").strip()
        data['prerequisites'] = [p.strip() for p in prereqs.split(',') if p.strip()]
        
        return data
    
    def _get_learning_objectives(self) -> List[str]:
        """Get learning objectives."""
        print("\n🎓 STEP 4: Learning Objectives")
        print("-" * 70)
        print("Enter learning objectives (one per line, empty line to finish):")
        
        objectives = []
        while True:
            obj = input(f"Objective {len(objectives) + 1}: ").strip()
            if not obj:
                break
            objectives.append(obj)
        
        return objectives or ["Complete scenario objectives"]
    
    def _get_tags(self) -> List[str]:
        """Get scenario tags."""
        print("\n🏷️  Tags (comma-separated):")
        print("Examples: red_team, network_penetration, advanced")
        tags = input("Tags: ").strip()
        return [t.strip() for t in tags.split(',') if t.strip()]
    
    def _build_phases(self) -> List[Dict[str, Any]]:
        """Build scenario phases."""
        print("\n📑 STEP 5: Scenario Phases")
        print("-" * 70)
        
        num_phases = int(input("Number of phases: ").strip() or "1")
        phases = []
        
        for i in range(num_phases):
            print(f"\n--- Phase {i + 1} ---")
            phase = self._build_phase(i + 1)
            phases.append(phase)
        
        return phases
    
    def _build_phase(self, phase_num: int) -> Dict[str, Any]:
        """Build a single phase."""
        phase = {}
        phase['id'] = input(f"Phase ID [phase-{phase_num}]: ").strip() or f"phase-{phase_num}"
        phase['name'] = input("Phase Name: ").strip()
        phase['description'] = input("Description: ").strip()
        
        # Time limit
        time_limit = input("Time limit (minutes, or press Enter for none): ").strip()
        if time_limit:
            phase['time_limit_minutes'] = int(time_limit)
        
        # Objectives
        num_objectives = int(input("Number of objectives [2]: ").strip() or "2")
        phase['objectives'] = [self._build_objective(i + 1) for i in range(num_objectives)]
        
        # Hints
        add_hints = input("Add hints? (y/n) [n]: ").strip().lower()
        if add_hints == 'y':
            num_hints = int(input("Number of hints [1]: ").strip() or "1")
            phase['hints'] = [self._build_hint(i + 1) for i in range(num_hints)]
        else:
            phase['hints'] = []
        
        return phase
    
    def _build_objective(self, obj_num: int) -> Dict[str, Any]:
        """Build a single objective."""
        print(f"\n  Objective {obj_num}:")
        obj = {}
        obj['id'] = input(f"  ID [obj-{obj_num}]: ").strip() or f"obj-{obj_num}"
        obj['description'] = input("  Description: ").strip()
        
        # Success criteria
        obj['success_criteria'] = {
            'type': input("  Success criteria type [manual_verification]: ").strip() or 'manual_verification',
            'parameters': {}
        }
        
        # Points
        points = input("  Points [100]: ").strip()
        obj['points'] = int(points) if points else 100
        
        # Required
        required = input("  Required? (y/n) [y]: ").strip().lower()
        obj['required'] = required != 'n'
        
        return obj
    
    def _build_hint(self, hint_num: int) -> Dict[str, Any]:
        """Build a single hint."""
        print(f"\n  Hint {hint_num}:")
        hint = {}
        
        trigger = input("  Trigger after minutes [10]: ").strip()
        hint['trigger_after_minutes'] = int(trigger) if trigger else 10
        
        hint['hint'] = input("  Hint text: ").strip()
        
        penalty = input("  Penalty points [25]: ").strip()
        hint['penalty_points'] = int(penalty) if penalty else 25
        
        return hint
    
    def _configure_scoring(self) -> Dict[str, Any]:
        """Configure scoring system."""
        print("\n🏆 STEP 6: Scoring Configuration")
        print("-" * 70)
        
        scoring = {}
        
        max_points = input("Maximum points [1000]: ").strip()
        scoring['max_points'] = int(max_points) if max_points else 1000
        
        time_bonus = input("Time bonus multiplier [1.5]: ").strip()
        scoring['time_bonus_multiplier'] = float(time_bonus) if time_bonus else 1.5
        
        stealth_bonus = input("Stealth bonus points [200]: ").strip()
        scoring['stealth_bonus'] = int(stealth_bonus) if stealth_bonus else 200
        
        mistake_deduction = input("Deduction per mistake [50]: ").strip()
        scoring['deductions_per_mistake'] = int(mistake_deduction) if mistake_deduction else 50
        
        hint_deduction = input("Deduction per hint [25]: ").strip()
        scoring['deductions_per_hint'] = int(hint_deduction) if hint_deduction else 25
        
        completion_bonus = input("Completion bonus [500]: ").strip()
        scoring['completion_bonus'] = int(completion_bonus) if completion_bonus else 500
        
        return scoring
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get scenario metadata."""
        print("\n📊 STEP 7: Metadata (Optional)")
        print("-" * 70)
        print("Add any custom metadata (press Enter to skip)")
        
        metadata = {}
        
        while True:
            key = input("\nMetadata key (or press Enter to finish): ").strip()
            if not key:
                break
            value = input(f"Value for '{key}': ").strip()
            metadata[key] = value
        
        return metadata
    
    def _validate_scenario(self, scenario_data: Dict[str, Any]) -> bool:
        """Validate scenario data."""
        print("\n🔍 Validating scenario...")
        
        try:
            # Create scenario object
            scenario = Scenario.from_dict(scenario_data)
            
            # Validate
            errors = self.validator.validate(scenario)
            
            if errors:
                print("\n❌ Validation errors found:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
                return False
            
            print("✓ Scenario validation passed")
            return True
            
        except Exception as e:
            print(f"\n❌ Validation error: {e}")
            return False
    
    def _save_scenario(self, scenario_data: Dict[str, Any]):
        """Save scenario to file."""
        print("\n💾 STEP 8: Save Scenario")
        print("-" * 70)
        
        # Default path
        default_path = f"ats_mafia_framework/scenarios/{scenario_data['id']}.json"
        
        save_path = input(f"Save path [{default_path}]: ").strip() or default_path
        
        # Create directory if needed
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(scenario_data, f, indent=2)
        
        print(f"\n✅ Scenario saved to: {save_path}")


def main():
    """Main entry point for scenario builder."""
    try:
        builder = ScenarioBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n\n❌ Scenario creation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()