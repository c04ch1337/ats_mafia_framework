"""
MITRE ATT&CK Navigator Layer Generation
Exports scenario and profile coverage as Navigator layers for visualization
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class ATTACKNavigatorExporter:
    """
    Generate ATT&CK Navigator layers for visualization
    
    Creates JSON layer files compatible with MITRE ATT&CK Navigator:
    https://mitre-attack.github.io/attack-navigator/
    """
    
    def __init__(self, attack_framework):
        """
        Initialize Navigator exporter
        
        Args:
            attack_framework: ATTACKFramework instance
        """
        self.attack = attack_framework
        self.logger = logging.getLogger("attack_navigator")
    
    def create_profile_layer(self, profile: Dict, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Navigator layer for profile technique coverage
        
        Args:
            profile: Profile dictionary with attack_knowledge
            name: Optional custom layer name
            
        Returns:
            Navigator layer JSON
        """
        profile_name = profile.get('metadata', {}).get('name', 'Unknown Profile')
        layer_name = name or f"Profile: {profile_name}"
        
        techniques = []
        
        # Extract techniques from profile
        attack_knowledge = profile.get('attack_knowledge', {})
        for technique_data in attack_knowledge.get('mastered_techniques', []):
            techniques.append({
                'techniqueID': technique_data['id'],
                'score': self._proficiency_to_score(technique_data.get('proficiency', 'intermediate')),
                'color': self._proficiency_to_color(technique_data.get('proficiency')),
                'comment': f"Proficiency: {technique_data.get('proficiency', 'N/A')}\nSuccess Rate: {technique_data.get('success_rate', 0) * 100:.1f}%",
                'enabled': True,
                'metadata': [
                    {'name': 'Success Rate', 'value': f"{technique_data.get('success_rate', 0) * 100:.1f}%"},
                    {'name': 'Proficiency', 'value': technique_data.get('proficiency', 'N/A')}
                ]
            })
        
        return {
            'name': layer_name,
            'versions': {
                'attack': '15',
                'navigator': '4.9.1',
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': f"ATT&CK coverage for {profile_name} profile in ATS MAFIA framework",
            'techniques': techniques,
            'gradient': {
                'colors': ['#ff6666', '#ffe766', '#8ec843'],
                'minValue': 0,
                'maxValue': 100
            },
            'legendItems': [
                {'label': 'Novice (20)', 'color': '#ff6666'},
                {'label': 'Beginner (40)', 'color': '#ffaa66'},
                {'label': 'Intermediate (60)', 'color': '#ffe766'},
                {'label': 'Advanced (80)', 'color': '#b3d966'},
                {'label': 'Expert (90)', 'color': '#9fcc66'},
                {'label': 'Master (100)', 'color': '#8ec843'}
            ],
            'showTacticRowBackground': True,
            'tacticRowBackground': '#1e1e1e',
            'selectTechniquesAcrossTactics': True,
            'metadata': [
                {'name': 'Profile ID', 'value': profile.get('metadata', {}).get('id', 'N/A')},
                {'name': 'Profile Type', 'value': profile.get('metadata', {}).get('profile_type', 'N/A')},
                {'name': 'Total Techniques', 'value': str(len(techniques))},
                {'name': 'Generated', 'value': datetime.now().isoformat()},
                {'name': 'Source', 'value': 'ATS MAFIA Framework'}
            ]
        }
    
    def create_scenario_layer(self, scenario: Dict, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Navigator layer for scenario technique requirements
        
        Args:
            scenario: Scenario dictionary with phases and objectives
            name: Optional custom layer name
            
        Returns:
            Navigator layer JSON
        """
        scenario_name = scenario.get('name', 'Unknown Scenario')
        layer_name = name or f"Scenario: {scenario_name}"
        
        techniques = []
        
        # Extract techniques from scenario phases
        for phase in scenario.get('phases', []):
            for objective in phase.get('objectives', []):
                if 'attack_mapping' in objective:
                    mapping = objective['attack_mapping']
                    techniques.append({
                        'techniqueID': mapping['technique_id'],
                        'score': 100 if objective.get('required', True) else 50,
                        'color': '#4361ee' if objective.get('required', True) else '#90caf9',
                        'comment': f"Phase: {phase['name']}\nObjective: {objective['description']}\nRequired: {objective.get('required', True)}",
                        'enabled': True,
                        'metadata': [
                            {'name': 'Phase', 'value': phase['name']},
                            {'name': 'Required', 'value': str(objective.get('required', True))}
                        ]
                    })
        
        return {
            'name': layer_name,
            'versions': {
                'attack': '15',
                'navigator': '4.9.1',
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': f"ATT&CK techniques for {scenario_name} training scenario",
            'techniques': techniques,
            'gradient': {
                'colors': ['#90caf9', '#4361ee'],
                'minValue': 0,
                'maxValue': 100
            },
            'legendItems': [
                {'label': 'Optional Technique', 'color': '#90caf9'},
                {'label': 'Required Technique', 'color': '#4361ee'}
            ],
            'showTacticRowBackground': True,
            'tacticRowBackground': '#1e1e1e',
            'selectTechniquesAcrossTactics': True,
            'metadata': [
                {'name': 'Scenario ID', 'value': scenario.get('id', 'N/A')},
                {'name': 'Difficulty', 'value': scenario.get('difficulty', 'N/A')},
                {'name': 'Type', 'value': scenario.get('type', 'N/A')},
                {'name': 'Total Techniques', 'value': str(len(techniques))},
                {'name': 'Generated', 'value': datetime.now().isoformat()},
                {'name': 'Source', 'value': 'ATS MAFIA Framework'}
            ]
        }
    
    def create_coverage_heatmap(self, sessions: List[Dict], name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create heatmap showing technique usage across multiple training sessions
        
        Args:
            sessions: List of session dictionaries with techniques_used
            name: Optional custom layer name
            
        Returns:
            Navigator heatmap layer JSON
        """
        layer_name = name or 'Training Coverage Heatmap'
        
        # Count technique usage across sessions
        technique_counts = {}
        
        for session in sessions:
            for technique_id in session.get('techniques_used', []):
                technique_counts[technique_id] = technique_counts.get(technique_id, 0) + 1
        
        # Find max count for normalization
        max_count = max(technique_counts.values()) if technique_counts else 1
        
        # Build technique list
        techniques = [
            {
                'techniqueID': tid,
                'score': (count / max_count) * 100,
                'color': '',  # Use gradient
                'comment': f"Used in {count} session(s)\nFrequency: {(count / len(sessions)) * 100:.1f}%",
                'enabled': True,
                'metadata': [
                    {'name': 'Usage Count', 'value': str(count)},
                    {'name': 'Frequency', 'value': f"{(count / len(sessions)) * 100:.1f}%"}
                ]
            }
            for tid, count in technique_counts.items()
        ]
        
        return {
            'name': layer_name,
            'versions': {
                'attack': '15',
                'navigator': '4.9.1',
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': f"Heatmap of ATT&CK techniques practiced across {len(sessions)} training sessions",
            'techniques': techniques,
            'gradient': {
                'colors': ['#ffffff', '#66b0ff', '#0066cc'],
                'minValue': 0,
                'maxValue': 100
            },
            'legendItems': [
                {'label': 'Rarely Used (< 25%)', 'color': '#ffffff'},
                {'label': 'Sometimes Used (25-75%)', 'color': '#66b0ff'},
                {'label': 'Frequently Used (> 75%)', 'color': '#0066cc'}
            ],
            'showTacticRowBackground': True,
            'tacticRowBackground': '#1e1e1e',
            'selectTechniquesAcrossTactics': True,
            'metadata': [
                {'name': 'Total Sessions', 'value': str(len(sessions))},
                {'name': 'Unique Techniques', 'value': str(len(technique_counts))},
                {'name': 'Generated', 'value': datetime.now().isoformat()},
                {'name': 'Source', 'value': 'ATS MAFIA Training Analytics'}
            ]
        }
    
    def create_custom_layer(self,
                           technique_ids: List[str],
                           name: str = "Custom Layer",
                           description: str = "",
                           scores: Optional[Dict[str, int]] = None,
                           colors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create custom Navigator layer from technique list
        
        Args:
            technique_ids: List of technique IDs to include
            name: Layer name
            description: Layer description
            scores: Optional dict mapping technique IDs to scores (0-100)
            colors: Optional dict mapping technique IDs to colors
            
        Returns:
            Navigator layer JSON
        """
        techniques = []
        
        for tech_id in technique_ids:
            technique = self.attack.get_technique(tech_id)
            if not technique:
                self.logger.warning(f"Technique {tech_id} not found, skipping")
                continue
            
            techniques.append({
                'techniqueID': tech_id,
                'score': scores.get(tech_id, 100) if scores else 100,
                'color': colors.get(tech_id, '') if colors else '',
                'comment': technique['name'],
                'enabled': True
            })
        
        return {
            'name': name,
            'versions': {
                'attack': '15',
                'navigator': '4.9.1',
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': description or f"Custom ATT&CK layer with {len(techniques)} techniques",
            'techniques': techniques,
            'gradient': {
                'colors': ['#66b0ff', '#0066cc'],
                'minValue': 0,
                'maxValue': 100
            },
            'showTacticRowBackground': True,
            'tacticRowBackground': '#1e1e1e',
            'selectTechniquesAcrossTactics': True,
            'metadata': [
                {'name': 'Total Techniques', 'value': str(len(techniques))},
                {'name': 'Generated', 'value': datetime.now().isoformat()},
                {'name': 'Source', 'value': 'ATS MAFIA Framework'}
            ]
        }
    
    def export_to_file(self, layer: Dict[str, Any], filepath: str) -> None:
        """
        Export Navigator layer to JSON file
        
        Args:
            layer: Navigator layer dictionary
            filepath: Output file path
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(layer, f, indent=2)
            
            self.logger.info(f"Exported Navigator layer to {filepath}")
        
        except Exception as e:
            self.logger.error(f"Error exporting layer: {e}")
            raise
    
    @staticmethod
    def _proficiency_to_score(proficiency: str) -> int:
        """
        Convert proficiency level to numeric score (0-100)
        
        Args:
            proficiency: Proficiency level string
            
        Returns:
            Numeric score
        """
        mapping = {
            'novice': 20,
            'beginner': 40,
            'intermediate': 60,
            'advanced': 80,
            'expert': 90,
            'master': 100
        }
        return mapping.get(proficiency.lower(), 50)
    
    @staticmethod
    def _proficiency_to_color(proficiency: str) -> str:
        """
        Convert proficiency level to color hex code
        
        Args:
            proficiency: Proficiency level string
            
        Returns:
            Hex color code
        """
        mapping = {
            'novice': '#ff6666',
            'beginner': '#ffaa66',
            'intermediate': '#ffe766',
            'advanced': '#b3d966',
            'expert': '#9fcc66',
            'master': '#8ec843'
        }
        return mapping.get(proficiency.lower(), '#dddddd')