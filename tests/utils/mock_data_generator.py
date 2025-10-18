"""
ATS MAFIA Mock Data Generator

This module provides utilities for generating mock data
for testing the ATS MAFIA framework.
"""

import json
import random
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path


class MockDataGenerator:
    """
    Generator for creating mock data for testing purposes.
    """
    
    def __init__(self):
        """Initialize mock data generator."""
        self.random = random.Random()
        self.agent_names = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon", 
            "Zeta", "Eta", "Theta", "Iota", "Kappa"
        ]
        self.scenario_names = [
            "Network Penetration", "Social Engineering", "Incident Response",
            "Threat Hunting", "Malware Analysis", "Vulnerability Assessment",
            "Red Team Exercise", "Blue Team Defense", "Security Audit"
        ]
        self.tool_names = [
            "nmap", "metasploit", "burp_suite", "wireshark", "splunk",
            "elastic", "nessus", "openvas", "nikto", "sqlmap"
        ]
        self.vulnerability_types = [
            "SQL Injection", "XSS", "RCE", "LFI", "Directory Traversal",
            "Buffer Overflow", "CSRF", "SSRF", "XXE", "Deserialization"
        ]
    
    def generate_agent_profile(self, 
                              profile_type: str = "red_team",
                              name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a mock agent profile.
        
        Args:
            profile_type: Type of profile (red_team, blue_team, social_engineer)
            name: Optional agent name
            
        Returns:
            Mock agent profile dictionary
        """
        if name is None:
            name = f"{profile_type.replace('_', ' ').title()} {self.random.choice(self.agent_names)}"
        
        base_profile = {
            "metadata": {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": f"Mock {profile_type} profile for testing",
                "version": "1.0.0",
                "author": "Test Generator",
                "profile_type": profile_type,
                "category": "test",
                "tags": ["test", "mock", profile_type],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "dependencies": [],
                "compatibility": ["test_environment"]
            },
            "capabilities": self._generate_capabilities(profile_type),
            "personality": self._generate_personality(profile_type),
            "knowledge_base": self._generate_knowledge_base(profile_type),
            "behavior_settings": self._generate_behavior_settings(),
            "communication_style": self._generate_communication_style(profile_type),
            "learning_parameters": self._generate_learning_parameters(),
            "security_settings": self._generate_security_settings(profile_type),
            "custom_data": self._generate_custom_data(profile_type)
        }
        
        return base_profile
    
    def _generate_capabilities(self, profile_type: str) -> List[Dict[str, Any]]:
        """Generate capabilities based on profile type."""
        if profile_type == "red_team":
            return [
                {
                    "name": "reconnaissance",
                    "description": "Perform network and application reconnaissance",
                    "skill_level": "expert",
                    "tools_required": ["nmap", "dirb"],
                    "prerequisites": [],
                    "metrics": {
                        "coverage_percentage": random.uniform(0.8, 0.95),
                        "stealth_score": random.uniform(0.7, 0.9)
                    }
                },
                {
                    "name": "exploitation",
                    "description": "Exploit identified vulnerabilities",
                    "skill_level": "advanced",
                    "tools_required": ["metasploit"],
                    "prerequisites": ["reconnaissance"],
                    "metrics": {
                        "success_rate": random.uniform(0.7, 0.9),
                        "stealth_score": random.uniform(0.6, 0.8)
                    }
                }
            ]
        elif profile_type == "blue_team":
            return [
                {
                    "name": "threat_detection",
                    "description": "Detect and identify security threats",
                    "skill_level": "expert",
                    "tools_required": ["splunk", "elastic"],
                    "prerequisites": [],
                    "metrics": {
                        "detection_rate": random.uniform(0.8, 0.95),
                        "false_positive_rate": random.uniform(0.05, 0.15)
                    }
                },
                {
                    "name": "incident_response",
                    "description": "Respond to security incidents",
                    "skill_level": "advanced",
                    "tools_required": ["siem", "soar"],
                    "prerequisites": ["threat_detection"],
                    "metrics": {
                        "response_time": random.uniform(300, 1800),
                        "containment_success": random.uniform(0.8, 0.95)
                    }
                }
            ]
        else:  # social_engineer
            return [
                {
                    "name": "psychological_profiling",
                    "description": "Analyze and profile targets",
                    "skill_level": "expert",
                    "tools_required": ["psychology_tools"],
                    "prerequisites": [],
                    "metrics": {
                        "accuracy": random.uniform(0.7, 0.9),
                        "speed": random.uniform(0.6, 0.8)
                    }
                }
            ]
    
    def _generate_personality(self, profile_type: str) -> List[Dict[str, Any]]:
        """Generate personality traits based on profile type."""
        if profile_type == "red_team":
            return [
                {"trait": "aggressiveness", "value": random.uniform(0.6, 0.9)},
                {"trait": "creativity", "value": random.uniform(0.7, 0.95)},
                {"trait": "risk_tolerance", "value": random.uniform(0.5, 0.8)},
                {"trait": "stealth_orientation", "value": random.uniform(0.7, 0.9)}
            ]
        elif profile_type == "blue_team":
            return [
                {"trait": "cautiousness", "value": random.uniform(0.7, 0.95)},
                {"trait": "analytical_thinking", "value": random.uniform(0.8, 1.0)},
                {"trait": "attention_to_detail", "value": random.uniform(0.7, 0.9)},
                {"trait": "collaboration", "value": random.uniform(0.6, 0.85)}
            ]
        else:  # social_engineer
            return [
                {"trait": "empathy_simulation", "value": random.uniform(0.8, 1.0)},
                {"trait": "adaptability", "value": random.uniform(0.7, 0.95)},
                {"trait": "patience", "value": random.uniform(0.6, 0.85)},
                {"trait": "ethical_awareness", "value": 1.0}
            ]
    
    def _generate_knowledge_base(self, profile_type: str) -> Dict[str, List[str]]:
        """Generate knowledge base based on profile type."""
        if profile_type == "red_team":
            return {
                "attack_frameworks": ["MITRE_ATT&CK", "Cyber_kill_chain"],
                "common_vulnerabilities": self.vulnerability_types[:5],
                "exploitation_techniques": ["buffer_overflow", "sql_injection", "xss"],
                "evasion_techniques": ["antivirus_evasion", "network_evasion"]
            }
        elif profile_type == "blue_team":
            return {
                "defense_frameworks": ["NIST_CSF", "ISO_27001"],
                "detection_methods": ["signature_based", "anomaly_based", "behavioral"],
                "response_procedures": ["isolation", "containment", "eradication"],
                "forensic_tools": ["wireshark", "volatility", "autopsy"]
            }
        else:  # social_engineer
            return {
                "social_engineering_techniques": ["pretexting", "phishing", "vishing"],
                "psychological_principles": ["authority", "scarcity", "social_proof"],
                "communication_patterns": ["rapport_building", "persuasion", "influence"],
                "ethical_guidelines": ["consent_required", "no_harm", "transparency"]
            }
    
    def _generate_behavior_settings(self) -> Dict[str, Any]:
        """Generate behavior settings."""
        return {
            "decision_making": {
                "risk_assessment": random.choice([True, False]),
                "collaborative_planning": random.choice([True, False]),
                "adaptation_threshold": random.uniform(0.5, 0.9),
                "exploration_vs_exploitation": random.uniform(0.3, 0.8)
            },
            "interaction_patterns": {
                "communication_frequency": random.choice(["low", "medium", "high"]),
                "information_sharing": random.choice(["selective", "open", "restricted"]),
                "team_coordination": random.choice(["active", "passive", "minimal"]),
                "independence_level": random.uniform(0.3, 0.9)
            },
            "learning_behavior": {
                "adaptation_rate": random.uniform(0.5, 0.9),
                "feedback_sensitivity": random.uniform(0.6, 0.85),
                "knowledge_retention": random.uniform(0.7, 0.95),
                "skill_improvement_rate": random.uniform(0.4, 0.8)
            }
        }
    
    def _generate_communication_style(self, profile_type: str) -> Dict[str, Any]:
        """Generate communication style based on profile type."""
        if profile_type == "red_team":
            return {
                "message_tone": "technical",
                "detail_level": "high",
                "urgency_level": "medium",
                "collaboration_style": "task_oriented",
                "reporting_frequency": "periodic"
            }
        elif profile_type == "blue_team":
            return {
                "message_tone": "formal",
                "detail_level": "comprehensive",
                "urgency_level": "high",
                "collaboration_style": "team_oriented",
                "reporting_frequency": "frequent"
            }
        else:  # social_engineer
            return {
                "message_tone": "adaptive",
                "detail_level": "moderate",
                "urgency_level": "situational",
                "collaboration_style": "relationship_oriented",
                "reporting_frequency": "as_needed"
            }
    
    def _generate_learning_parameters(self) -> Dict[str, Any]:
        """Generate learning parameters."""
        return {
            "learning_rate": random.uniform(0.01, 0.1),
            "exploration_rate": random.uniform(0.05, 0.2),
            "discount_factor": random.uniform(0.9, 0.99),
            "experience_replay_size": random.randint(5000, 20000),
            "target_network_update_frequency": random.randint(50, 200),
            "reward_shaping": {
                "success_bonus": random.uniform(5.0, 15.0),
                "failure_penalty": random.uniform(-10.0, -2.0),
                "stealth_bonus": random.uniform(1.0, 5.0),
                "speed_bonus": random.uniform(0.5, 2.0)
            }
        }
    
    def _generate_security_settings(self, profile_type: str) -> Dict[str, Any]:
        """Generate security settings based on profile type."""
        if profile_type == "red_team":
            return {
                "access_level": "high",
                "allowed_operations": ["reconnaissance", "exploitation", "post_exploitation"],
                "restricted_operations": ["data_destruction", "denial_of_service"],
                "auditing_level": "detailed",
                "encryption_required": True
            }
        elif profile_type == "blue_team":
            return {
                "access_level": "medium",
                "allowed_operations": ["monitoring", "analysis", "response"],
                "restricted_operations": ["system_modification", "data_access"],
                "auditing_level": "comprehensive",
                "encryption_required": True
            }
        else:  # social_engineer
            return {
                "access_level": "controlled",
                "allowed_operations": ["communication", "profiling", "simulation"],
                "restricted_operations": ["data_collection", "real_contact"],
                "auditing_level": "comprehensive",
                "encryption_required": True
            }
    
    def _generate_custom_data(self, profile_type: str) -> Dict[str, Any]:
        """Generate custom data based on profile type."""
        if profile_type == "red_team":
            return {
                "preferred_tools": random.sample(self.tool_names, 3),
                "specializations": ["pentesting", "adversary_simulation"],
                "certifications": ["OSCP", "OSEP"],
                "experience_years": random.randint(3, 10),
                "previous_exercises": [f"exercise_{i}" for i in range(random.randint(1, 5))]
            }
        elif profile_type == "blue_team":
            return {
                "preferred_tools": random.sample(["splunk", "elastic", "wireshark"], 2),
                "specializations": ["incident_response", "threat_hunting"],
                "certifications": ["GIAC", "CISSP"],
                "experience_years": random.randint(2, 8),
                "previous_incidents": [f"incident_{i}" for i in range(random.randint(1, 3))]
            }
        else:  # social_engineer
            return {
                "voice_capabilities": {
                    "supported_languages": ["en-US", "en-GB"],
                    "accent_variations": ["neutral", "american", "british"],
                    "emotion_range": ["happiness", "sadness", "neutral"]
                },
                "specializations": ["vishing", "pretexting", "psychological_profiling"],
                "certifications": ["Social_Engineering_Certified"],
                "experience_years": random.randint(2, 6)
            }
    
    def generate_training_scenario(self, 
                                  scenario_type: str = "red_team_exercise") -> Dict[str, Any]:
        """
        Generate a mock training scenario.
        
        Args:
            scenario_type: Type of scenario
            
        Returns:
            Mock training scenario dictionary
        """
        return {
            "id": str(uuid.uuid4()),
            "name": self.random.choice(self.scenario_names),
            "description": f"Mock {scenario_type} scenario for testing",
            "scenario_type": scenario_type,
            "duration": random.randint(1800, 7200),  # 30 minutes to 2 hours
            "max_agents": random.randint(2, 8),
            "required_profiles": self._get_required_profiles(scenario_type),
            "optional_profiles": self._get_optional_profiles(scenario_type),
            "environment_config": {
                "network": "test_network",
                "targets": [f"target_{i}" for i in range(random.randint(1, 5))],
                "tools": random.sample(self.tool_names, random.randint(2, 4))
            },
            "success_criteria": self._generate_success_criteria(scenario_type),
            "evaluation_metrics": self._generate_evaluation_metrics(scenario_type),
            "resources": {
                "documentation": ["test_docs"],
                "tools": random.sample(self.tool_names, 2),
                "time_limit": random.randint(1800, 7200)
            }
        }
    
    def _get_required_profiles(self, scenario_type: str) -> List[str]:
        """Get required profiles for scenario type."""
        if scenario_type in ["red_team_exercise", "penetration_testing"]:
            return ["red_team_operator"]
        elif scenario_type in ["blue_team_defense", "incident_response"]:
            return ["security_analyst"]
        elif scenario_type == "social_engineering":
            return ["social_engineer"]
        else:
            return ["red_team_operator", "security_analyst"]
    
    def _get_optional_profiles(self, scenario_type: str) -> List[str]:
        """Get optional profiles for scenario type."""
        profiles = ["red_team_operator", "security_analyst", "threat_hunter", 
                   "incident_responder", "social_engineer"]
        return random.sample(profiles, random.randint(0, 2))
    
    def _generate_success_criteria(self, scenario_type: str) -> Dict[str, Any]:
        """Generate success criteria based on scenario type."""
        if scenario_type in ["red_team_exercise", "penetration_testing"]:
            return {
                "compromise_targets": random.randint(1, 3),
                "exfiltrate_data": random.choice([True, False]),
                "maintain_access": random.choice([True, False]),
                "avoid_detection": random.choice([True, False])
            }
        elif scenario_type in ["blue_team_defense", "incident_response"]:
            return {
                "detect_intrusion": True,
                "contain_threat": True,
                "preserve_evidence": True,
                "minimal_downtime": True
            }
        else:
            return {
                "achieve_objectives": True,
                "maintain_ethics": True,
                "document_findings": True
            }
    
    def _generate_evaluation_metrics(self, scenario_type: str) -> List[str]:
        """Generate evaluation metrics based on scenario type."""
        if scenario_type in ["red_team_exercise", "penetration_testing"]:
            return ["time_to_compromise", "stealth_score", "coverage_score", "technique_diversity"]
        elif scenario_type in ["blue_team_defense", "incident_response"]:
            return ["detection_time", "response_time", "accuracy_score", "coordination_score"]
        else:
            return ["objective_completion", "ethical_compliance", "documentation_quality"]
    
    def generate_test_session(self, 
                             scenario_id: Optional[str] = None,
                             agent_profiles: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a mock training session.
        
        Args:
            scenario_id: Optional scenario ID
            agent_profiles: Optional list of agent profile IDs
            
        Returns:
            Mock training session dictionary
        """
        if scenario_id is None:
            scenario_id = str(uuid.uuid4())
        
        if agent_profiles is None:
            agent_profiles = [str(uuid.uuid4()) for _ in range(random.randint(2, 4))]
        
        return {
            "id": str(uuid.uuid4()),
            "name": f"Test Session {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "description": "Mock test session for testing",
            "scenario_id": scenario_id,
            "agent_profiles": agent_profiles,
            "status": "running",
            "start_time": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "end_time": None,
            "config": {
                "timeout": random.randint(1800, 7200),
                "checkpoint_interval": random.randint(300, 900),
                "auto_save": random.choice([True, False])
            },
            "metrics": {
                "progress": random.uniform(0.0, 1.0),
                "score": random.uniform(0.0, 100.0),
                "objective_completion": random.uniform(0.0, 1.0)
            },
            "logs": [f"Log entry {i}" for i in range(random.randint(5, 20))],
            "results": {
                "objectives_completed": random.randint(0, 5),
                "total_objectives": random.randint(5, 10),
                "final_score": random.uniform(0.0, 100.0)
            }
        }
    
    def generate_audit_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock audit logs.
        
        Args:
            count: Number of audit logs to generate
            
        Returns:
            List of mock audit log entries
        """
        event_types = ["agent_action", "system_event", "security_event", "training_event", "tool_execution"]
        actions = ["login", "logout", "execute_tool", "send_message", "receive_message", "start_scenario", "end_scenario"]
        
        logs = []
        for i in range(count):
            log = {
                "event_id": str(uuid.uuid4()),
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 1440))).isoformat(),
                "event_type": random.choice(event_types),
                "source": random.choice(["agent", "system", "user"]),
                "action": random.choice(actions),
                "details": {
                    "agent_id": str(uuid.uuid4()),
                    "session_id": str(uuid.uuid4()),
                    "additional_info": f"Additional info {i}"
                },
                "success": random.choice([True, False])
            }
            logs.append(log)
        
        return logs
    
    def save_mock_profile_to_file(self, 
                                 profile: Dict[str, Any], 
                                 file_path: str) -> None:
        """
        Save mock profile to a JSON file.
        
        Args:
            profile: Mock profile dictionary
            file_path: Path to save the profile
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, default=str)
    
    def create_mock_dataset(self, 
                           num_profiles: int = 5,
                           num_scenarios: int = 3,
                           num_sessions: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create a complete mock dataset for testing.
        
        Args:
            num_profiles: Number of agent profiles to generate
            num_scenarios: Number of scenarios to generate
            num_sessions: Number of sessions to generate
            
        Returns:
            Dictionary containing mock dataset
        """
        dataset = {
            "profiles": [],
            "scenarios": [],
            "sessions": [],
            "audit_logs": []
        }
        
        # Generate profiles
        profile_types = ["red_team", "blue_team", "social_engineer"]
        for i in range(num_profiles):
            profile_type = random.choice(profile_types)
            profile = self.generate_agent_profile(profile_type)
            dataset["profiles"].append(profile)
        
        # Generate scenarios
        scenario_types = ["red_team_exercise", "blue_team_defense", "social_engineering"]
        for i in range(num_scenarios):
            scenario_type = random.choice(scenario_types)
            scenario = self.generate_training_scenario(scenario_type)
            dataset["scenarios"].append(scenario)
        
        # Generate sessions
        for i in range(num_sessions):
            scenario = random.choice(dataset["scenarios"])
            agent_ids = [p["metadata"]["id"] for p in random.sample(dataset["profiles"], random.randint(2, 4))]
            session = self.generate_test_session(scenario["id"], agent_ids)
            dataset["sessions"].append(session)
        
        # Generate audit logs
        dataset["audit_logs"] = self.generate_audit_logs(50)
        
        return dataset