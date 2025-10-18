"""
ATS MAFIA Framework Scenario Engine

This module provides the comprehensive scenario management infrastructure for the
ATS MAFIA framework. It handles scenario definition, validation, adaptive difficulty,
and centralized scenario management.
"""

import os
import json
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from ..config.settings import FrameworkConfig
from .logging import AuditLogger, AuditEventType, SecurityLevel


class DifficultyLevel(Enum):
    """Difficulty levels for training scenarios."""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class ScenarioType(Enum):
    """Types of training scenarios."""
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    SOCIAL_ENGINEERING = "social_engineering"
    RED_VS_BLUE = "red_vs_blue"
    MULTI_STAGE = "multi_stage"


class ObjectiveStatus(Enum):
    """Status of scenario objectives."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PhaseStatus(Enum):
    """Status of scenario phases."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SuccessCriteria:
    """Success criteria for objectives."""
    type: str  # tool_execution, time_based, detection_based, score_based, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuccessCriteria':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Objective:
    """Individual objective within a scenario phase."""
    id: str
    description: str
    success_criteria: SuccessCriteria
    points: int = 100
    required: bool = True
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    completed_at: Optional[datetime] = None
    time_taken_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['success_criteria'] = self.success_criteria.to_dict()
        data['status'] = self.status.value
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Objective':
        """Create from dictionary."""
        data['success_criteria'] = SuccessCriteria.from_dict(data['success_criteria'])
        data['status'] = ObjectiveStatus(data.get('status', 'pending'))
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class Hint:
    """Hint for scenario assistance."""
    trigger_after_minutes: int
    hint: str
    penalty_points: int = 0
    revealed: bool = False
    revealed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.revealed_at:
            data['revealed_at'] = self.revealed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hint':
        """Create from dictionary."""
        if data.get('revealed_at'):
            data['revealed_at'] = datetime.fromisoformat(data['revealed_at'])
        return cls(**data)


@dataclass
class ScenarioPhase:
    """Individual phase/stage in a training scenario."""
    id: str
    name: str
    description: str
    objectives: List[Objective]
    hints: List[Hint] = field(default_factory=list)
    time_limit_minutes: Optional[int] = None
    required: bool = True
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'objectives': [obj.to_dict() for obj in self.objectives],
            'hints': [hint.to_dict() for hint in self.hints],
            'time_limit_minutes': self.time_limit_minutes,
            'required': self.required,
            'status': self.status.value
        }
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioPhase':
        """Create from dictionary."""
        data['objectives'] = [Objective.from_dict(obj) for obj in data.get('objectives', [])]
        data['hints'] = [Hint.from_dict(hint) for hint in data.get('hints', [])]
        data['status'] = PhaseStatus(data.get('status', 'pending'))
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)
    
    def get_completion_percentage(self) -> float:
        """Calculate completion percentage for this phase."""
        if not self.objectives:
            return 0.0
        completed = sum(1 for obj in self.objectives if obj.status == ObjectiveStatus.COMPLETED)
        return (completed / len(self.objectives)) * 100.0


@dataclass
class ScoringConfig:
    """Scoring configuration for scenarios."""
    max_points: int = 1000
    time_bonus_multiplier: float = 1.5
    stealth_bonus: int = 200
    deductions_per_mistake: int = 50
    deductions_per_hint: int = 25
    completion_bonus: int = 500
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Scenario:
    """Complete scenario definition."""
    id: str
    name: str
    description: str
    type: ScenarioType
    difficulty: DifficultyLevel
    estimated_duration_minutes: int
    required_profiles: List[str]
    required_tools: List[str]
    phases: List[ScenarioPhase]
    scoring: ScoringConfig
    optional_profiles: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "ATS MAFIA Framework"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'difficulty': self.difficulty.value,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'required_profiles': self.required_profiles,
            'required_tools': self.required_tools,
            'optional_profiles': self.optional_profiles,
            'optional_tools': self.optional_tools,
            'phases': [phase.to_dict() for phase in self.phases],
            'scoring': self.scoring.to_dict(),
            'prerequisites': self.prerequisites,
            'learning_objectives': self.learning_objectives,
            'tags': self.tags,
            'version': self.version,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scenario':
        """Create from dictionary."""
        data['type'] = ScenarioType(data['type'])
        data['difficulty'] = DifficultyLevel(data['difficulty'])
        data['phases'] = [ScenarioPhase.from_dict(phase) for phase in data.get('phases', [])]
        data['scoring'] = ScoringConfig.from_dict(data.get('scoring', {}))
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for the scenario."""
        scenario_data = self.to_dict()
        scenario_json = json.dumps(scenario_data, sort_keys=True)
        return hashlib.sha256(scenario_json.encode()).hexdigest()
    
    def get_total_objectives(self) -> int:
        """Get total number of objectives across all phases."""
        return sum(len(phase.objectives) for phase in self.phases)
    
    def get_completed_objectives(self) -> int:
        """Get number of completed objectives."""
        return sum(
            sum(1 for obj in phase.objectives if obj.status == ObjectiveStatus.COMPLETED)
            for phase in self.phases
        )
    
    def get_completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        total = self.get_total_objectives()
        if total == 0:
            return 0.0
        completed = self.get_completed_objectives()
        return (completed / total) * 100.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for adaptive difficulty."""
    objectives_completed: int = 0
    objectives_failed: int = 0
    hints_used: int = 0
    mistakes_made: int = 0
    time_efficiency: float = 1.0  # 1.0 = on pace, <1.0 = slow, >1.0 = fast
    stealth_score: float = 1.0  # 0.0-1.0
    technique_diversity: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create from dictionary."""
        return cls(**data)


class AdaptiveDifficulty:
    """Dynamic difficulty adjustment system based on performance."""
    
    def __init__(self, initial_difficulty: DifficultyLevel):
        """
        Initialize adaptive difficulty system.
        
        Args:
            initial_difficulty: Starting difficulty level
        """
        self.current_difficulty = initial_difficulty
        self.performance_history: List[PerformanceMetrics] = []
        self.adjustment_threshold = 0.7  # Adjust if performance consistently above/below this
        self.logger = logging.getLogger("adaptive_difficulty")
    
    def record_performance(self, metrics: PerformanceMetrics) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics: Performance metrics to record
        """
        self.performance_history.append(metrics)
        
        # Keep only last 5 performance snapshots
        if len(self.performance_history) > 5:
            self.performance_history = self.performance_history[-5:]
    
    def calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate overall performance score (0.0-1.0).
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Performance score between 0.0 and 1.0
        """
        # Calculate success rate
        total_objectives = metrics.objectives_completed + metrics.objectives_failed
        success_rate = metrics.objectives_completed / total_objectives if total_objectives > 0 else 0.5
        
        # Factor in time efficiency
        time_factor = min(metrics.time_efficiency, 1.5) / 1.5
        
        # Factor in stealth
        stealth_factor = metrics.stealth_score
        
        # Penalize hints and mistakes
        hint_penalty = min(metrics.hints_used * 0.05, 0.3)
        mistake_penalty = min(metrics.mistakes_made * 0.03, 0.2)
        
        # Combined score
        score = (success_rate * 0.4 + time_factor * 0.2 + stealth_factor * 0.2 +
                (metrics.technique_diversity / 10) * 0.2 - hint_penalty - mistake_penalty)
        
        return max(0.0, min(1.0, score))
    
    def should_adjust_difficulty(self) -> Tuple[bool, Optional[DifficultyLevel]]:
        """
        Determine if difficulty should be adjusted.
        
        Returns:
            Tuple of (should_adjust, new_difficulty_level)
        """
        if len(self.performance_history) < 3:
            return False, None
        
        # Calculate average performance
        recent_scores = [self.calculate_performance_score(m) for m in self.performance_history[-3:]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        # Determine adjustment
        difficulty_levels = list(DifficultyLevel)
        current_index = difficulty_levels.index(self.current_difficulty)
        
        # Performing very well - increase difficulty
        if avg_score > 0.85 and current_index < len(difficulty_levels) - 1:
            new_difficulty = difficulty_levels[current_index + 1]
            return True, new_difficulty
        
        # Struggling - decrease difficulty
        elif avg_score < 0.4 and current_index > 0:
            new_difficulty = difficulty_levels[current_index - 1]
            return True, new_difficulty
        
        return False, None
    
    def get_hint_trigger_modifier(self) -> float:
        """
        Get modifier for hint trigger times based on performance.
        
        Returns:
            Multiplier for hint trigger times (e.g., 0.8 = show hints 20% earlier)
        """
        if not self.performance_history:
            return 1.0
        
        recent_score = self.calculate_performance_score(self.performance_history[-1])
        
        # Struggling players get hints earlier
        if recent_score < 0.4:
            return 0.7
        elif recent_score < 0.6:
            return 0.85
        else:
            return 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current_difficulty': self.current_difficulty.value,
            'performance_history': [m.to_dict() for m in self.performance_history],
            'adjustment_threshold': self.adjustment_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptiveDifficulty':
        """Create from dictionary."""
        instance = cls(DifficultyLevel(data['current_difficulty']))
        instance.performance_history = [
            PerformanceMetrics.from_dict(m) for m in data.get('performance_history', [])
        ]
        instance.adjustment_threshold = data.get('adjustment_threshold', 0.7)
        return instance


class ScenarioValidator:
    """Validator for scenario completeness and logical consistency."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logging.getLogger("scenario_validator")
    
    def validate(self, scenario: Scenario) -> List[str]:
        """
        Validate a scenario.
        
        Args:
            scenario: Scenario to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation
        errors.extend(self._validate_basic_fields(scenario))
        
        # Validate phases
        errors.extend(self._validate_phases(scenario.phases))
        
        # Validate dependencies
        errors.extend(self._validate_dependencies(scenario))
        
        # Validate scoring configuration
        errors.extend(self._validate_scoring(scenario.scoring))
        
        # Validate logical consistency
        errors.extend(self._validate_logical_consistency(scenario))
        
        return errors
    
    def _validate_basic_fields(self, scenario: Scenario) -> List[str]:
        """Validate basic required fields."""
        errors = []
        
        if not scenario.id or not scenario.id.strip():
            errors.append("Scenario ID is required")
        
        if not scenario.name or not scenario.name.strip():
            errors.append("Scenario name is required")
        
        if not scenario.description or not scenario.description.strip():
            errors.append("Scenario description is required")
        
        if not isinstance(scenario.type, ScenarioType):
            errors.append("Invalid scenario type")
        
        if not isinstance(scenario.difficulty, DifficultyLevel):
            errors.append("Invalid difficulty level")
        
        if scenario.estimated_duration_minutes <= 0:
            errors.append("Estimated duration must be positive")
        
        if not scenario.required_profiles:
            errors.append("At least one required profile must be specified")
        
        if not scenario.phases:
            errors.append("Scenario must have at least one phase")
        
        return errors
    
    def _validate_phases(self, phases: List[ScenarioPhase]) -> List[str]:
        """Validate scenario phases."""
        errors = []
        
        phase_ids = set()
        
        for i, phase in enumerate(phases):
            if not phase.id or not phase.id.strip():
                errors.append(f"Phase {i}: ID is required")
                continue
            
            if phase.id in phase_ids:
                errors.append(f"Duplicate phase ID: {phase.id}")
            else:
                phase_ids.add(phase.id)
            
            if not phase.name or not phase.name.strip():
                errors.append(f"Phase {phase.id}: Name is required")
            
            if not phase.objectives:
                errors.append(f"Phase {phase.id}: Must have at least one objective")
            
            # Validate objectives
            errors.extend(self._validate_objectives(phase.id, phase.objectives))
        
        return errors
    
    def _validate_objectives(self, phase_id: str, objectives: List[Objective]) -> List[str]:
        """Validate phase objectives."""
        errors = []
        
        objective_ids = set()
        
        for obj in objectives:
            if not obj.id or not obj.id.strip():
                errors.append(f"Phase {phase_id}: Objective ID is required")
                continue
            
            if obj.id in objective_ids:
                errors.append(f"Phase {phase_id}: Duplicate objective ID: {obj.id}")
            else:
                objective_ids.add(obj.id)
            
            if not obj.description or not obj.description.strip():
                errors.append(f"Phase {phase_id}, Objective {obj.id}: Description is required")
            
            if obj.points < 0:
                errors.append(f"Phase {phase_id}, Objective {obj.id}: Points cannot be negative")
            
            if not obj.success_criteria.type:
                errors.append(f"Phase {phase_id}, Objective {obj.id}: Success criteria type is required")
        
        return errors
    
    def _validate_dependencies(self, scenario: Scenario) -> List[str]:
        """Validate scenario dependencies."""
        errors = []
        
        # Check for circular dependencies
        if scenario.id in scenario.prerequisites:
            errors.append("Scenario cannot be a prerequisite of itself")
        
        return errors
    
    def _validate_scoring(self, scoring: ScoringConfig) -> List[str]:
        """Validate scoring configuration."""
        errors = []
        
        if scoring.max_points <= 0:
            errors.append("Max points must be positive")
        
        if scoring.time_bonus_multiplier < 1.0:
            errors.append("Time bonus multiplier should be >= 1.0")
        
        if scoring.deductions_per_mistake < 0:
            errors.append("Deductions per mistake cannot be negative")
        
        if scoring.deductions_per_hint < 0:
            errors.append("Deductions per hint cannot be negative")
        
        return errors
    
    def _validate_logical_consistency(self, scenario: Scenario) -> List[str]:
        """Validate logical consistency of the scenario."""
        errors = []
        
        # Check if estimated duration is reasonable for phases
        total_phase_time = sum(
            phase.time_limit_minutes for phase in scenario.phases
            if phase.time_limit_minutes
        )
        
        if total_phase_time > 0 and total_phase_time > scenario.estimated_duration_minutes * 1.5:
            errors.append(
                f"Total phase time limits ({total_phase_time} min) significantly exceed "
                f"estimated duration ({scenario.estimated_duration_minutes} min)"
            )
        
        # Check if scenario type matches phase requirements
        if scenario.type == ScenarioType.RED_VS_BLUE:
            red_team_found = any('red' in prof.lower() for prof in scenario.required_profiles)
            blue_team_found = any('blue' in prof.lower() for prof in scenario.required_profiles)
            
            if not (red_team_found and blue_team_found):
                errors.append("RED_VS_BLUE scenarios should require both red and blue team profiles")
        
        return errors


class ScenarioLibrary:
    """Centralized scenario registry and management system."""
    
    def __init__(self, 
                 config: Optional[FrameworkConfig] = None,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the scenario library.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("scenario_library")
        
        # Scenario storage
        self.scenarios: Dict[str, Scenario] = {}
        self.scenario_files: Dict[str, str] = {}  # scenario_id -> file_path
        
        # Components
        self.validator = ScenarioValidator()
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'scenarios_loaded': 0,
            'scenarios_validated': 0,
            'validation_errors': 0,
            'scenarios_by_type': {},
            'scenarios_by_difficulty': {}
        }
        
        # Load scenarios from default directory
        if config:
            # Use the default profile path as base or current directory
            base_dir = getattr(config, 'default_profile_path', 'ats_mafia_framework/profiles')
            base_dir = str(Path(base_dir).parent.parent)
            scenarios_dir = os.path.join(base_dir, 'ats_mafia_framework/scenarios')
            self.load_scenarios_from_directory(scenarios_dir)
    
    def load_scenarios_from_directory(self, directory: str) -> None:
        """
        Load scenarios from a directory.
        
        Args:
            directory: Directory to load scenarios from
        """
        scenario_dir = Path(directory)
        
        if not scenario_dir.exists():
            self.logger.warning(f"Scenario directory does not exist: {directory}")
            return
        
        # Look for JSON scenario files
        for scenario_file in scenario_dir.glob("**/*.json"):
            try:
                self.load_scenario_from_file(str(scenario_file))
            except Exception as e:
                self.logger.error(f"Error loading scenario from {scenario_file}: {e}")
        
        self.logger.info(f"Loaded {len(self.scenarios)} scenarios from {directory}")
    
    def load_scenario_from_file(self, file_path: str) -> bool:
        """
        Load a scenario from a file.
        
        Args:
            file_path: Path to scenario JSON file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            scenario_path = Path(file_path)
            
            if not scenario_path.exists():
                self.logger.error(f"Scenario file not found: {file_path}")
                return False
            
            # Load scenario data
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            # Create scenario
            scenario = Scenario.from_dict(scenario_data)
            
            # Validate scenario
            errors = self.validator.validate(scenario)
            if errors:
                self.logger.error(f"Scenario validation failed for {scenario.id}: {errors}")
                self.stats['validation_errors'] += len(errors)
                
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="scenario_validation_failed",
                        details={
                            'scenario_id': scenario.id,
                            'file_path': file_path,
                            'errors': errors
                        },
                        security_level=SecurityLevel.MEDIUM
                    )
                
                return False
            
            self.stats['scenarios_validated'] += 1
            
            # Register scenario
            self.register_scenario(scenario, file_path)
            
            self.stats['scenarios_loaded'] += 1
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="scenario_loaded",
                    details={
                        'scenario_id': scenario.id,
                        'file_path': file_path,
                        'type': scenario.type.value,
                        'difficulty': scenario.difficulty.value
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Loaded scenario: {scenario.id} from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading scenario from {file_path}: {e}")
            return False
    
    def register_scenario(self, scenario: Scenario, file_path: Optional[str] = None) -> None:
        """
        Register a scenario in the library.
        
        Args:
            scenario: Scenario to register
            file_path: Optional file path for the scenario
        """
        with self.lock:
            self.scenarios[scenario.id] = scenario
            
            if file_path:
                self.scenario_files[scenario.id] = file_path
            
            # Update statistics
            scenario_type = scenario.type.value
            self.stats['scenarios_by_type'][scenario_type] = \
                self.stats['scenarios_by_type'].get(scenario_type, 0) + 1
            
            difficulty = scenario.difficulty.value
            self.stats['scenarios_by_difficulty'][difficulty] = \
                self.stats['scenarios_by_difficulty'].get(difficulty, 0) + 1
    
    def unregister_scenario(self, scenario_id: str) -> bool:
        """
        Unregister a scenario.
        
        Args:
            scenario_id: ID of scenario to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        with self.lock:
            if scenario_id in self.scenarios:
                scenario = self.scenarios[scenario_id]
                
                # Update statistics
                scenario_type = scenario.type.value
                self.stats['scenarios_by_type'][scenario_type] -= 1
                
                difficulty = scenario.difficulty.value
                self.stats['scenarios_by_difficulty'][difficulty] -= 1
                
                del self.scenarios[scenario_id]
                self.scenario_files.pop(scenario_id, None)
                
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="scenario_unregistered",
                        details={'scenario_id': scenario_id},
                        security_level=SecurityLevel.LOW
                    )
                
                self.logger.info(f"Unregistered scenario: {scenario_id}")
                return True
            
            return False
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        Get a scenario by ID.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Scenario or None if not found
        """
        with self.lock:
            return self.scenarios.get(scenario_id)
    
    def list_scenarios(self,
                      scenario_type: Optional[ScenarioType] = None,
                      difficulty: Optional[DifficultyLevel] = None,
                      tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List scenarios with optional filtering.
        
        Args:
            scenario_type: Filter by scenario type
            difficulty: Filter by difficulty level
            tags: Filter by tags (scenario must have at least one)
            
        Returns:
            List of scenario dictionaries
        """
        with self.lock:
            results = []
            
            for scenario in self.scenarios.values():
                # Apply filters
                if scenario_type and scenario.type != scenario_type:
                    continue
                
                if difficulty and scenario.difficulty != difficulty:
                    continue
                
                if tags and not any(tag in scenario.tags for tag in tags):
                    continue
                
                results.append(scenario.to_dict())
            
            return results
    
    def search_scenarios(self, query: str) -> List[Dict[str, Any]]:
        """
        Search scenarios by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching scenario dictionaries
        """
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for scenario in self.scenarios.values():
                # Search in name, description, and tags
                searchable = [
                    scenario.name.lower(),
                    scenario.description.lower(),
                    *[tag.lower() for tag in scenario.tags]
                ]
                
                if any(query_lower in text for text in searchable):
                    results.append(scenario.to_dict())
            
            return results
    
    def get_recommended_scenarios(self,
                                 skill_level: DifficultyLevel,
                                 completed_scenarios: List[str],
                                 max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get recommended scenarios based on skill level and progress.
        
        Args:
            skill_level: User's skill level
            completed_scenarios: List of completed scenario IDs
            max_results: Maximum number of recommendations
            
        Returns:
            List of recommended scenario dictionaries
        """
        with self.lock:
            recommendations = []
            
            # Map difficulty to numeric value
            difficulty_order = {
                DifficultyLevel.NOVICE: 0,
                DifficultyLevel.INTERMEDIATE: 1,
                DifficultyLevel.ADVANCED: 2,
                DifficultyLevel.EXPERT: 3,
                DifficultyLevel.MASTER: 4
            }
            
            user_level = difficulty_order[skill_level]
            
            for scenario in self.scenarios.values():
                # Skip completed scenarios
                if scenario.id in completed_scenarios:
                    continue
                
                scenario_level = difficulty_order[scenario.difficulty]
                
                # Check prerequisites
                prerequisites_met = all(
                    prereq in completed_scenarios
                    for prereq in scenario.prerequisites
                )
                
                if not prerequisites_met:
                    continue
                
                # Recommend scenarios at or slightly above user level
                if user_level <= scenario_level <= user_level + 1:
                    recommendations.append({
                        'scenario': scenario.to_dict(),
                        'match_score': 1.0 - abs(scenario_level - user_level) * 0.3
                    })
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Return top recommendations
            return [r['scenario'] for r in recommendations[:max_results]]
    
    def validate_scenario(self, scenario: Scenario) -> List[str]:
        """
        Validate a scenario.
        
        Args:
            scenario: Scenario to validate
            
        Returns:
            List of validation errors
        """
        return self.validator.validate(scenario)
    
    def save_scenario(self, scenario: Scenario, file_path: Optional[str] = None) -> bool:
        """
        Save a scenario to file.
        
        Args:
            scenario: Scenario to save
            file_path: Path to save to (defaults to registered path)
            
        Returns:
            True if saved successfully
        """
        try:
            save_path = file_path or self.scenario_files.get(scenario.id)
            
            if not save_path:
                self.logger.error(f"No file path for scenario {scenario.id}")
                return False
            
            # Update timestamp
            scenario.updated_at = datetime.now(timezone.utc)
            
            # Save to file
            scenario_path = Path(save_path)
            scenario_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(scenario_path, 'w', encoding='utf-8') as f:
                json.dump(scenario.to_dict(), f, indent=2)
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="scenario_saved",
                    details={
                        'scenario_id': scenario.id,
                        'file_path': save_path
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Saved scenario: {scenario.id} to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving scenario {scenario.id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get library statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self.lock:
            return {
                'total_scenarios': len(self.scenarios),
                **self.stats
            }
    
    def shutdown(self) -> None:
        """Shutdown the scenario library."""
        with self.lock:
            self.scenarios.clear()
            self.scenario_files.clear()
            self.logger.info("Scenario library shutdown complete")


# Global scenario library instance
_global_scenario_library: Optional[ScenarioLibrary] = None


def get_scenario_library() -> Optional[ScenarioLibrary]:
    """
    Get the global scenario library instance.
    
    Returns:
        Global ScenarioLibrary instance or None if not initialized
    """
    return _global_scenario_library


def initialize_scenario_library(config: Optional[FrameworkConfig] = None,
                               audit_logger: Optional[AuditLogger] = None) -> ScenarioLibrary:
    """
    Initialize the global scenario library.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized ScenarioLibrary instance
    """
    global _global_scenario_library
    _global_scenario_library = ScenarioLibrary(config, audit_logger)
    return _global_scenario_library


def shutdown_scenario_library() -> None:
    """Shutdown the global scenario library."""
    global _global_scenario_library
    if _global_scenario_library:
        _global_scenario_library.shutdown()
        _global_scenario_library = None