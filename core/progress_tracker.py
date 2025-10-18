"""
ATS MAFIA Framework Progress Tracking System

This module provides comprehensive operator progress monitoring including
achievements, milestones, certifications, and structured learning paths.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from .performance_metrics import SkillLevel, OperatorProfile


class MilestoneType(Enum):
    """Types of milestones."""
    FIRST_SESSION = "first_session"
    SKILL_MILESTONE = "skill_milestone"
    SESSION_COUNT = "session_count"
    HOURS_TRAINED = "hours_trained"
    CERTIFICATION = "certification"
    MASTERY = "mastery"
    SPECIAL_EVENT = "special_event"


class AchievementCategory(Enum):
    """Categories for achievements."""
    SKILL_BASED = "skill_based"
    PERFORMANCE_BASED = "performance_based"
    DEDICATION = "dedication"
    SOCIAL = "social"
    SPECIAL = "special"


class CertificationLevel(Enum):
    """Certification levels."""
    FOUNDATION = "foundation"
    PRACTITIONER = "practitioner"
    PROFESSIONAL = "professional"
    EXPERT = "expert"
    MASTER = "master"


@dataclass
class Milestone:
    """
    Define achievement milestones.
    
    Attributes:
        id: Unique identifier
        name: Milestone name
        description: Milestone description
        milestone_type: Type of milestone
        requirements: Dictionary of requirements
        xp_reward: Experience points awarded
        badge_icon: Optional badge icon identifier
    """
    id: str
    name: str
    description: str
    milestone_type: MilestoneType
    requirements: Dict[str, Any]
    xp_reward: int
    badge_icon: Optional[str] = None
    
    def check_completion(self, operator_data: Dict[str, Any]) -> bool:
        """
        Check if milestone is completed based on operator data.
        
        Args:
            operator_data: Current operator data
            
        Returns:
            True if completed, False otherwise
        """
        if self.milestone_type == MilestoneType.FIRST_SESSION:
            return operator_data.get('total_sessions', 0) >= 1
        
        elif self.milestone_type == MilestoneType.SESSION_COUNT:
            required = self.requirements.get('sessions', 0)
            return operator_data.get('total_sessions', 0) >= required
        
        elif self.milestone_type == MilestoneType.HOURS_TRAINED:
            required = self.requirements.get('hours', 0)
            return operator_data.get('total_hours', 0) >= required
        
        elif self.milestone_type == MilestoneType.SKILL_MILESTONE:
            skill_name = self.requirements.get('skill_name')
            required_level = self.requirements.get('level', 'intermediate')
            
            if not skill_name:
                return False
            
            skills = operator_data.get('skills', {})
            skill = skills.get(skill_name)
            
            if not skill:
                return False
            
            required_skill_level = SkillLevel(required_level)
            current_level = SkillLevel(skill.get('proficiency', 'novice'))
            
            return current_level.to_numeric() >= required_skill_level.to_numeric()
        
        elif self.milestone_type == MilestoneType.CERTIFICATION:
            cert_name = self.requirements.get('certification_name')
            certifications = operator_data.get('certifications', [])
            return cert_name in certifications
        
        elif self.milestone_type == MilestoneType.MASTERY:
            # Check if operator has mastered required number of skills
            required_count = self.requirements.get('skill_count', 1)
            skills = operator_data.get('skills', {})
            
            master_count = sum(
                1 for skill in skills.values()
                if SkillLevel(skill.get('proficiency', 'novice')) == SkillLevel.MASTER
            )
            
            return master_count >= required_count
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['milestone_type'] = self.milestone_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Milestone':
        """Create from dictionary."""
        data['milestone_type'] = MilestoneType(data['milestone_type'])
        return cls(**data)


@dataclass
class Achievement:
    """
    Track unlocked achievements.
    
    Attributes:
        id: Unique identifier
        operator_id: Operator who earned it
        milestone_id: Associated milestone
        name: Achievement name
        description: Achievement description
        category: Achievement category
        unlocked_at: When it was unlocked
        xp_earned: Experience points earned
    """
    id: str
    operator_id: str
    milestone_id: str
    name: str
    description: str
    category: AchievementCategory
    unlocked_at: datetime
    xp_earned: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['category'] = self.category.value
        data['unlocked_at'] = self.unlocked_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        """Create from dictionary."""
        data['category'] = AchievementCategory(data['category'])
        data['unlocked_at'] = datetime.fromisoformat(data['unlocked_at'])
        return cls(**data)


@dataclass
class ProgressPath:
    """
    Structured learning paths (beginner → expert).
    
    Attributes:
        id: Unique identifier
        name: Path name
        description: Path description
        stages: Ordered list of stage names
        stage_requirements: Requirements for each stage
        total_xp: Total XP to complete path
    """
    id: str
    name: str
    description: str
    stages: List[str]
    stage_requirements: Dict[str, Dict[str, Any]]
    total_xp: int
    
    def get_current_stage(self, operator_data: Dict[str, Any]) -> str:
        """
        Determine operator's current stage in the path.
        
        Args:
            operator_data: Operator data
            
        Returns:
            Current stage name
        """
        for stage in self.stages:
            requirements = self.stage_requirements.get(stage, {})
            
            # Check if stage is completed
            if not self._check_stage_completion(requirements, operator_data):
                return stage
        
        # All stages complete
        return self.stages[-1] if self.stages else "unknown"
    
    def _check_stage_completion(self,
                                requirements: Dict[str, Any],
                                operator_data: Dict[str, Any]) -> bool:
        """Check if a stage is completed."""
        # Check session requirements
        if 'min_sessions' in requirements:
            if operator_data.get('total_sessions', 0) < requirements['min_sessions']:
                return False
        
        # Check skill requirements
        if 'required_skills' in requirements:
            skills = operator_data.get('skills', {})
            for skill_req in requirements['required_skills']:
                skill_name = skill_req.get('name')
                required_level = SkillLevel(skill_req.get('level', 'intermediate'))
                
                skill = skills.get(skill_name, {})
                current_level = SkillLevel(skill.get('proficiency', 'novice'))
                
                if current_level.to_numeric() < required_level.to_numeric():
                    return False
        
        # Check XP requirements
        if 'min_xp' in requirements:
            if operator_data.get('total_xp', 0) < requirements['min_xp']:
                return False
        
        return True
    
    def get_next_requirements(self, operator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get requirements for the next stage.
        
        Args:
            operator_data: Operator data
            
        Returns:
            Dictionary with next stage requirements
        """
        current_stage = self.get_current_stage(operator_data)
        current_index = self.stages.index(current_stage) if current_stage in self.stages else 0
        
        if current_index < len(self.stages) - 1:
            next_stage = self.stages[current_index + 1]
            return {
                'next_stage': next_stage,
                'requirements': self.stage_requirements.get(next_stage, {})
            }
        
        return {'next_stage': None, 'requirements': {}}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressPath':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Goal:
    """
    Trackable goal for an operator.
    
    Attributes:
        id: Unique identifier
        operator_id: Operator identifier
        name: Goal name
        description: Goal description
        target_value: Target value to achieve
        current_value: Current progress value
        unit: Unit of measurement
        deadline: Optional deadline
        created_at: When goal was created
        completed_at: When goal was completed
    """
    id: str
    operator_id: str
    name: str
    description: str
    target_value: float
    current_value: float = 0.0
    unit: str = "units"
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)
    
    def is_completed(self) -> bool:
        """Check if goal is completed."""
        return self.current_value >= self.target_value
    
    def update_progress(self, value: float) -> bool:
        """
        Update progress towards goal.
        
        Args:
            value: New progress value
            
        Returns:
            True if goal was completed by this update
        """
        was_complete = self.is_completed()
        self.current_value = value
        
        if self.is_completed() and not was_complete:
            self.completed_at = datetime.now(timezone.utc)
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.deadline:
            data['deadline'] = self.deadline.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('deadline'):
            data['deadline'] = datetime.fromisoformat(data['deadline'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class Certification:
    """
    Operator certification/badge.
    
    Attributes:
        id: Unique identifier
        name: Certification name
        description: Certification description
        level: Certification level
        requirements: Requirements to earn
        badge_icon: Badge icon identifier
        valid_for_days: Days certification is valid (None = permanent)
    """
    id: str
    name: str
    description: str
    level: CertificationLevel
    requirements: Dict[str, Any]
    badge_icon: str
    valid_for_days: Optional[int] = None
    
    def check_eligibility(self, operator_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if operator is eligible for certification.
        
        Args:
            operator_data: Operator data
            
        Returns:
            Tuple of (is_eligible, missing_requirements)
        """
        missing = []
        
        # Check skill requirements
        if 'required_skills' in self.requirements:
            skills = operator_data.get('skills', {})
            
            for skill_req in self.requirements['required_skills']:
                skill_name = skill_req.get('name')
                required_level = SkillLevel(skill_req.get('level', 'advanced'))
                
                skill = skills.get(skill_name)
                if not skill:
                    missing.append(f"Missing skill: {skill_name}")
                else:
                    current_level = SkillLevel(skill.get('proficiency', 'novice'))
                    if current_level.to_numeric() < required_level.to_numeric():
                        missing.append(
                            f"{skill_name} level {current_level.value} "
                            f"(need {required_level.value})"
                        )
        
        # Check session requirements
        if 'min_sessions' in self.requirements:
            min_sessions = self.requirements['min_sessions']
            if operator_data.get('total_sessions', 0) < min_sessions:
                missing.append(f"Need {min_sessions} total sessions")
        
        # Check XP requirements
        if 'min_xp' in self.requirements:
            min_xp = self.requirements['min_xp']
            if operator_data.get('total_xp', 0) < min_xp:
                missing.append(f"Need {min_xp} total XP")
        
        # Check certification prerequisites
        if 'prerequisite_certifications' in self.requirements:
            current_certs = operator_data.get('certifications', [])
            for prereq in self.requirements['prerequisite_certifications']:
                if prereq not in current_certs:
                    missing.append(f"Missing prerequisite certification: {prereq}")
        
        return (len(missing) == 0, missing)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['level'] = self.level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Certification':
        """Create from dictionary."""
        data['level'] = CertificationLevel(data['level'])
        return cls(**data)


@dataclass
class EarnedCertification:
    """
    Track earned certifications.
    
    Attributes:
        operator_id: Operator identifier
        certification_id: Certification identifier
        earned_at: When certification was earned
        expires_at: When certification expires (if applicable)
    """
    operator_id: str
    certification_id: str
    earned_at: datetime
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if certification is still valid."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'operator_id': self.operator_id,
            'certification_id': self.certification_id,
            'earned_at': self.earned_at.isoformat()
        }
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EarnedCertification':
        """Create from dictionary."""
        data['earned_at'] = datetime.fromisoformat(data['earned_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class GoalTracker:
    """Track progress toward specific goals."""
    
    def __init__(self):
        """Initialize goal tracker."""
        self.logger = logging.getLogger("goal_tracker")
        self.goals: Dict[str, Goal] = {}
    
    def create_goal(self,
                   operator_id: str,
                   name: str,
                   description: str,
                   target_value: float,
                   unit: str = "units",
                   deadline: Optional[datetime] = None) -> Goal:
        """
        Create a new goal.
        
        Args:
            operator_id: Operator identifier
            name: Goal name
            description: Goal description
            target_value: Target value
            unit: Unit of measurement
            deadline: Optional deadline
            
        Returns:
            Created goal
        """
        goal = Goal(
            id=str(uuid.uuid4()),
            operator_id=operator_id,
            name=name,
            description=description,
            target_value=target_value,
            unit=unit,
            deadline=deadline
        )
        
        self.goals[goal.id] = goal
        self.logger.info(f"Created goal for operator {operator_id}: {name}")
        
        return goal
    
    def update_goal_progress(self, goal_id: str, value: float) -> bool:
        """
        Update progress for a goal.
        
        Args:
            goal_id: Goal identifier
            value: New progress value
            
        Returns:
            True if goal was completed, False otherwise
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return False
        
        completed = goal.update_progress(value)
        
        if completed:
            self.logger.info(f"Goal {goal.name} completed for operator {goal.operator_id}")
        
        return completed
    
    def get_operator_goals(self,
                          operator_id: str,
                          include_completed: bool = True) -> List[Goal]:
        """
        Get goals for an operator.
        
        Args:
            operator_id: Operator identifier
            include_completed: Whether to include completed goals
            
        Returns:
            List of goals
        """
        goals = [
            g for g in self.goals.values()
            if g.operator_id == operator_id
        ]
        
        if not include_completed:
            goals = [g for g in goals if not g.is_completed()]
        
        return goals


class CertificationManager:
    """Manage operator certifications and badges."""
    
    def __init__(self):
        """Initialize certification manager."""
        self.logger = logging.getLogger("certification_manager")
        self.certifications: Dict[str, Certification] = {}
        self.earned_certifications: List[EarnedCertification] = []
        
        # Initialize default certifications
        self._create_default_certifications()
    
    def _create_default_certifications(self) -> None:
        """Create default certification tracks."""
        # Red Team certifications
        self.register_certification(Certification(
            id="cert_red_team_foundation",
            name="Red Team Foundation",
            description="Foundation level red team operations",
            level=CertificationLevel.FOUNDATION,
            requirements={
                'required_skills': [
                    {'name': 'reconnaissance', 'level': 'intermediate'},
                    {'name': 'exploitation', 'level': 'intermediate'}
                ],
                'min_sessions': 5,
                'min_xp': 500
            },
            badge_icon="red_team_foundation_badge"
        ))
        
        self.register_certification(Certification(
            id="cert_red_team_professional",
            name="Red Team Professional",
            description="Professional level red team operations",
            level=CertificationLevel.PROFESSIONAL,
            requirements={
                'required_skills': [
                    {'name': 'reconnaissance', 'level': 'advanced'},
                    {'name': 'exploitation', 'level': 'advanced'},
                    {'name': 'post_exploitation', 'level': 'advanced'}
                ],
                'min_sessions': 20,
                'min_xp': 5000,
                'prerequisite_certifications': ['cert_red_team_foundation']
            },
            badge_icon="red_team_professional_badge"
        ))
        
        # Blue Team certifications
        self.register_certification(Certification(
            id="cert_blue_team_foundation",
            name="Blue Team Foundation",
            description="Foundation level defensive operations",
            level=CertificationLevel.FOUNDATION,
            requirements={
                'required_skills': [
                    {'name': 'threat_detection', 'level': 'intermediate'},
                    {'name': 'incident_response', 'level': 'intermediate'}
                ],
                'min_sessions': 5,
                'min_xp': 500
            },
            badge_icon="blue_team_foundation_badge"
        ))
        
        # Social Engineering certification
        self.register_certification(Certification(
            id="cert_social_engineering",
            name="Social Engineering Specialist",
            description="Advanced social engineering techniques",
            level=CertificationLevel.PROFESSIONAL,
            requirements={
                'required_skills': [
                    {'name': 'social_engineering', 'level': 'expert'},
                    {'name': 'pretexting', 'level': 'advanced'}
                ],
                'min_sessions': 15,
                'min_xp': 3000
            },
            badge_icon="social_engineering_badge"
        ))
    
    def register_certification(self, certification: Certification) -> None:
        """
        Register a certification.
        
        Args:
            certification: Certification to register
        """
        self.certifications[certification.id] = certification
        self.logger.info(f"Registered certification: {certification.name}")
    
    def award_certification(self,
                          operator_id: str,
                          certification_id: str) -> Optional[EarnedCertification]:
        """
        Award a certification to an operator.
        
        Args:
            operator_id: Operator identifier
            certification_id: Certification identifier
            
        Returns:
            Earned certification or None if not eligible
        """
        certification = self.certifications.get(certification_id)
        if not certification:
            self.logger.error(f"Certification not found: {certification_id}")
            return None
        
        # Create earned certification
        earned = EarnedCertification(
            operator_id=operator_id,
            certification_id=certification_id,
            earned_at=datetime.now(timezone.utc)
        )
        
        # Set expiration if applicable
        if certification.valid_for_days:
            earned.expires_at = (
                datetime.now(timezone.utc) + 
                timedelta(days=certification.valid_for_days)
            )
        
        self.earned_certifications.append(earned)
        self.logger.info(
            f"Awarded certification {certification.name} to operator {operator_id}"
        )
        
        return earned
    
    def get_operator_certifications(self,
                                   operator_id: str,
                                   include_expired: bool = False) -> List[EarnedCertification]:
        """
        Get certifications for an operator.
        
        Args:
            operator_id: Operator identifier
            include_expired: Whether to include expired certifications
            
        Returns:
            List of earned certifications
        """
        certs = [
            c for c in self.earned_certifications
            if c.operator_id == operator_id
        ]
        
        if not include_expired:
            certs = [c for c in certs if c.is_valid()]
        
        return certs
    
    def check_certification_eligibility(self,
                                       operator_id: str,
                                       certification_id: str,
                                       operator_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if operator is eligible for a certification.
        
        Args:
            operator_id: Operator identifier
            certification_id: Certification identifier
            operator_data: Operator data for checking requirements
            
        Returns:
            Tuple of (is_eligible, missing_requirements)
        """
        certification = self.certifications.get(certification_id)
        if not certification:
            return (False, ["Certification not found"])
        
        return certification.check_eligibility(operator_data)


class ProgressTracker:
    """
    Main progress tracking system.
    
    Coordinates milestone tracking, achievements, goals, and certifications
    for comprehensive operator progress monitoring.
    """
    
    def __init__(self):
        """Initialize progress tracker."""
        self.logger = logging.getLogger("progress_tracker")
        
        # Components
        self.milestones: Dict[str, Milestone] = {}
        self.achievements: Dict[str, List[Achievement]] = {}  # By operator_id
        self.progress_paths: Dict[str, ProgressPath] = {}
        self.goal_tracker = GoalTracker()
        self.certification_manager = CertificationManager()
        
        # XP tracking
        self.operator_xp: Dict[str, int] = {}
        
        # Leaderboard data
        self.leaderboard_scores: Dict[str, Dict[str, float]] = {}
        
        # Initialize default content
        self._create_default_milestones()
        self._create_default_progress_paths()
    
    def _create_default_milestones(self) -> None:
        """Create default milestones."""
        # First session milestone
        self.register_milestone(Milestone(
            id="milestone_first_session",
            name="First Steps",
            description="Complete your first training session",
            milestone_type=MilestoneType.FIRST_SESSION,
            requirements={},
            xp_reward=100,
            badge_icon="first_session_badge"
        ))
        
        # Session count milestones
        for count in [10, 25, 50, 100]:
            self.register_milestone(Milestone(
                id=f"milestone_{count}_sessions",
                name=f"{count} Session Veteran",
                description=f"Complete {count} training sessions",
                milestone_type=MilestoneType.SESSION_COUNT,
                requirements={'sessions': count},
                xp_reward=count * 10,
                badge_icon=f"sessions_{count}_badge"
            ))
        
        # Hours trained milestones
        for hours in [10, 50, 100, 250]:
            self.register_milestone(Milestone(
                id=f"milestone_{hours}_hours",
                name=f"{hours} Hour Dedication",
                description=f"Train for {hours} total hours",
                milestone_type=MilestoneType.HOURS_TRAINED,
                requirements={'hours': hours},
                xp_reward=hours * 5,
                badge_icon=f"hours_{hours}_badge"
            ))
    
    def _create_default_progress_paths(self) -> None:
        """Create default learning paths."""
        # Red Team path
        red_team_path = ProgressPath(
            id="path_red_team",
            name="Red Team Operator",
            description="Comprehensive red team training path",
            stages=["beginner", "intermediate", "advanced", "expert"],
            stage_requirements={
                'beginner': {
                    'min_sessions': 0,
                    'required_skills': [],
                    'min_xp': 0
                },
                'intermediate': {
                    'min_sessions': 5,
                    'required_skills': [
                        {'name': 'reconnaissance', 'level': 'intermediate'}
                    ],
                    'min_xp': 500
                },
                'advanced': {
                    'min_sessions': 20,
                    'required_skills': [
                        {'name': 'reconnaissance', 'level': 'advanced'},
                        {'name': 'exploitation', 'level': 'advanced'}
                    ],
                    'min_xp': 2500
                },
                'expert': {
                    'min_sessions': 50,
                    'required_skills': [
                        {'name': 'reconnaissance', 'level': 'expert'},
                        {'name': 'exploitation', 'level': 'expert'},
                        {'name': 'post_exploitation', 'level': 'expert'}
                    ],
                    'min_xp': 10000
                }
            },
            total_xp=10000
        )
        
        self.progress_paths[red_team_path.id] = red_team_path
    
    def register_milestone(self, milestone: Milestone) -> None:
        """
        Register a milestone.
        
        Args:
            milestone: Milestone to register
        """
        self.milestones[milestone.id] = milestone
        self.logger.info(f"Registered milestone: {milestone.name}")
    
    def check_and_award_milestones(self,
                                   operator_id: str,
                                   operator_data: Dict[str, Any]) -> List[Achievement]:
        """
        Check and award any newly completed milestones.
        
        Args:
            operator_id: Operator identifier
            operator_data: Current operator data
            
        Returns:
            List of newly awarded achievements
        """
        newly_awarded = []
        
        # Get existing achievements
        existing_milestone_ids = set(
            a.milestone_id 
            for a in self.achievements.get(operator_id, [])
        )
        
        # Check each milestone
        for milestone in self.milestones.values():
            if milestone.id in existing_milestone_ids:
                continue  # Already awarded
            
            if milestone.check_completion(operator_data):
                # Award achievement
                achievement = Achievement(
                    id=str(uuid.uuid4()),
                    operator_id=operator_id,
                    milestone_id=milestone.id,
                    name=milestone.name,
                    description=milestone.description,
                    category=AchievementCategory.SKILL_BASED,
                    unlocked_at=datetime.now(timezone.utc),
                    xp_earned=milestone.xp_reward
                )
                
                if operator_id not in self.achievements:
                    self.achievements[operator_id] = []
                
                self.achievements[operator_id].append(achievement)
                newly_awarded.append(achievement)
                
                # Award XP
                self.operator_xp[operator_id] = (
                    self.operator_xp.get(operator_id, 0) + milestone.xp_reward
                )
                
                self.logger.info(
                    f"Awarded achievement {milestone.name} to operator {operator_id}"
                )
        
        return newly_awarded
    
    def get_operator_achievements(self, operator_id: str) -> List[Achievement]:
        """Get all achievements for an operator."""
        return self.achievements.get(operator_id, [])
    
    def get_operator_xp(self, operator_id: str) -> int:
        """Get total XP for an operator."""
        return self.operator_xp.get(operator_id, 0)
    
    def get_operator_level(self, operator_id: str) -> int:
        """
        Calculate operator level based on XP.
        
        Args:
            operator_id: Operator identifier
            
        Returns:
            Operator level
        """
        xp = self.get_operator_xp(operator_id)
        
        # Simple level formula: level = sqrt(xp / 100)
        level = int((xp / 100) ** 0.5) + 1
        return level
    
    def get_progress_path_status(self,
                                 operator_id: str,
                                 path_id: str,
                                 operator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get operator's progress on a learning path.
        
        Args:
            operator_id: Operator identifier
            path_id: Progress path identifier
            operator_data: Current operator data
            
        Returns:
            Progress status dictionary
        """
        path = self.progress_paths.get(path_id)
        if not path:
            return {'error': 'path_not_found'}
        
        current_stage = path.get_current_stage(operator_data)
        next_reqs = path.get_next_requirements(operator_data)
        
        return {
            'path_id': path_id,
            'path_name': path.name,
            'current_stage': current_stage,
            'total_stages': len(path.stages),
            'next_stage': next_reqs.get('next_stage'),
            'next_requirements': next_reqs.get('requirements', {}),
            'completion_percentage': (
                (path.stages.index(current_stage) + 1) / len(path.stages) * 100
                if current_stage in path.stages else 0
            )
        }
    
    def update_leaderboard(self,
                          category: str,
                          operator_id: str,
                          score: float) -> None:
        """
        Update leaderboard scores.
        
        Args:
            category: Leaderboard category
            operator_id: Operator identifier
            score: Score value
        """
        if category not in self.leaderboard_scores:
            self.leaderboard_scores[category] = {}
        
        self.leaderboard_scores[category][operator_id] = score
    
    def get_leaderboard(self,
                       category: str,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get leaderboard rankings for a category.
        
        Args:
            category: Leaderboard category
            limit: Number of top entries to return
            
        Returns:
            List of leaderboard entries
        """
        scores = self.leaderboard_scores.get(category, {})
        
        # Sort by score (descending)
        sorted_scores = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {
                'rank': idx + 1,
                'operator_id': operator_id,
                'score': score
            }
            for idx, (operator_id, score) in enumerate(sorted_scores)
        ]
    
    def get_operator_summary(self,
                            operator_id: str,
                            operator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for an operator.
        
        Args:
            operator_id: Operator identifier
            operator_data: Current operator data
            
        Returns:
            Progress summary
        """
        return {
            'operator_id': operator_id,
            'level': self.get_operator_level(operator_id),
            'total_xp': self.get_operator_xp(operator_id),
            'achievements_count': len(self.get_operator_achievements(operator_id)),
            'certifications': [
                c.certification_id 
                for c in self.certification_manager.get_operator_certifications(operator_id)
            ],
            'active_goals': len(self.goal_tracker.get_operator_goals(operator_id, False)),
            'total_sessions': operator_data.get('total_sessions', 0),
            'total_hours': operator_data.get('total_hours', 0)
        }