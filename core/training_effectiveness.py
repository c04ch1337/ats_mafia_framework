"""
ATS MAFIA Framework Training Effectiveness Tracker

This module measures actual learning outcomes, skill retention, and provides
AI-driven training recommendations for optimal operator development.
"""

import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from .performance_metrics import (
    OperatorProfile, SessionPerformance, SkillLevel, SkillMetric
)


class LearningPhase(Enum):
    """Phases of learning progression."""
    INTRODUCTION = "introduction"
    PRACTICE = "practice"
    MASTERY = "mastery"
    MAINTENANCE = "maintenance"


class RecommendationType(Enum):
    """Types of training recommendations."""
    SKILL_DEVELOPMENT = "skill_development"
    KNOWLEDGE_RETENTION = "knowledge_retention"
    ADVANCED_CHALLENGE = "advanced_challenge"
    REMEDIAL_PRACTICE = "remedial_practice"
    BREAK_RECOMMENDED = "break_recommended"
    CERTIFICATION_READY = "certification_ready"


@dataclass
class LearningCurve:
    """
    Track improvement over time for specific skills.
    
    Attributes:
        skill_name: Name of the skill
        data_points: List of (timestamp, score) tuples
        initial_score: Starting proficiency score
        current_score: Current proficiency score
        learning_rate: Rate of improvement
        plateau_threshold: Score at which learning plateaus
    """
    skill_name: str
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)
    initial_score: float = 0.0
    current_score: float = 0.0
    learning_rate: float = 0.0
    plateau_threshold: float = 0.9
    
    def add_data_point(self, timestamp: datetime, score: float) -> None:
        """
        Add a new performance data point.
        
        Args:
            timestamp: When the score was achieved
            score: Performance score (0.0-1.0)
        """
        self.data_points.append((timestamp, score))
        
        if not self.initial_score:
            self.initial_score = score
        
        self.current_score = score
        self._calculate_learning_rate()
    
    def _calculate_learning_rate(self) -> None:
        """Calculate the learning rate from data points."""
        if len(self.data_points) < 2:
            self.learning_rate = 0.0
            return
        
        # Simple linear regression on recent data
        recent = self.data_points[-10:]  # Last 10 sessions
        if len(recent) < 2:
            recent = self.data_points
        
        # Convert to numeric x values (session index)
        x_values = list(range(len(recent)))
        y_values = [score for _, score in recent]
        
        n = len(recent)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            self.learning_rate = 0.0
        else:
            self.learning_rate = numerator / denominator
    
    def predict_time_to_mastery(self, mastery_score: float = 0.9) -> Optional[int]:
        """
        Predict number of sessions to reach mastery.
        
        Args:
            mastery_score: Score considered as mastery
            
        Returns:
            Estimated number of sessions, or None if not predictable
        """
        if self.learning_rate <= 0:
            return None
        
        if self.current_score >= mastery_score:
            return 0
        
        sessions_needed = (mastery_score - self.current_score) / self.learning_rate
        return int(sessions_needed) if sessions_needed > 0 else None
    
    def is_plateaued(self, window_size: int = 5) -> bool:
        """
        Detect if learning has plateaued.
        
        Args:
            window_size: Number of recent sessions to check
            
        Returns:
            True if plateaued, False otherwise
        """
        if len(self.data_points) < window_size:
            return False
        
        recent = self.data_points[-window_size:]
        scores = [score for _, score in recent]
        
        # Check for low variance
        if len(scores) < 2:
            return False
        
        variance = statistics.variance(scores)
        return variance < 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'skill_name': self.skill_name,
            'data_points': [(ts.isoformat(), score) for ts, score in self.data_points],
            'initial_score': self.initial_score,
            'current_score': self.current_score,
            'learning_rate': self.learning_rate,
            'plateau_threshold': self.plateau_threshold
        }


@dataclass
class RetentionAnalysis:
    """
    Measure knowledge retention between sessions.
    
    Attributes:
        skill_name: Name of the skill
        last_practice_date: Last time skill was practiced
        retention_score: How well knowledge is retained
        decay_rate: Rate of knowledge decay
        optimal_practice_interval: Recommended time between practices
    """
    skill_name: str
    last_practice_date: datetime
    retention_score: float = 1.0
    decay_rate: float = 0.0
    optimal_practice_interval: timedelta = timedelta(days=7)
    
    def calculate_retention(self, 
                          current_date: datetime,
                          current_score: float,
                          previous_score: float) -> float:
        """
        Calculate retention score based on performance over time.
        
        Args:
            current_date: Current date
            current_score: Current performance score
            previous_score: Previous performance score
            
        Returns:
            Retention score (0.0-1.0)
        """
        days_elapsed = (current_date - self.last_practice_date).days
        
        if days_elapsed == 0:
            return 1.0
        
        # Calculate retention based on score change
        score_retention = current_score / previous_score if previous_score > 0 else 0.5
        
        # Factor in time elapsed (knowledge decays over time)
        time_factor = max(0.0, 1.0 - (days_elapsed / 30.0))  # 30-day decay period
        
        self.retention_score = score_retention * (0.5 + 0.5 * time_factor)
        self.decay_rate = (1.0 - score_retention) / max(1, days_elapsed)
        
        return self.retention_score
    
    def needs_review(self) -> bool:
        """
        Check if skill needs review based on time elapsed.
        
        Returns:
            True if review needed, False otherwise
        """
        time_since_practice = datetime.now(timezone.utc) - self.last_practice_date
        return time_since_practice > self.optimal_practice_interval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'skill_name': self.skill_name,
            'last_practice_date': self.last_practice_date.isoformat(),
            'retention_score': self.retention_score,
            'decay_rate': self.decay_rate,
            'optimal_practice_interval_days': self.optimal_practice_interval.days
        }


@dataclass
class SkillGap:
    """
    Identified skill gap needing improvement.
    
    Attributes:
        skill_name: Name of the skill
        current_level: Current proficiency level
        target_level: Target proficiency level
        gap_size: Size of the gap
        priority: Priority for addressing (1-5)
        recommended_actions: Suggested training actions
    """
    skill_name: str
    current_level: SkillLevel
    target_level: SkillLevel
    gap_size: int
    priority: int
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'skill_name': self.skill_name,
            'current_level': self.current_level.value,
            'target_level': self.target_level.value,
            'gap_size': self.gap_size,
            'priority': self.priority,
            'recommended_actions': self.recommended_actions
        }


class SkillGapAnalyzer:
    """
    Analyze skill gaps and identify areas needing focus.
    """
    
    def __init__(self):
        """Initialize skill gap analyzer."""
        self.logger = logging.getLogger("skill_gap_analyzer")
    
    def analyze_gaps(self,
                    operator_profile: OperatorProfile,
                    target_role: Optional[str] = None) -> List[SkillGap]:
        """
        Identify skill gaps for an operator.
        
        Args:
            operator_profile: Operator profile
            target_role: Optional target role (e.g., "red_team_expert")
            
        Returns:
            List of identified skill gaps
        """
        gaps = []
        
        # Define expected skills for different roles
        role_requirements = self._get_role_requirements(target_role)
        
        for skill_name, required_level in role_requirements.items():
            current_skill = operator_profile.skills.get(skill_name)
            
            if not current_skill:
                # Skill not practiced yet
                gap = SkillGap(
                    skill_name=skill_name,
                    current_level=SkillLevel.NOVICE,
                    target_level=required_level,
                    gap_size=required_level.to_numeric() - 1,
                    priority=5,
                    recommended_actions=[
                        f"Complete introductory training for {skill_name}",
                        f"Practice {skill_name} in guided scenarios"
                    ]
                )
                gaps.append(gap)
            else:
                current_numeric = current_skill.proficiency.to_numeric()
                required_numeric = required_level.to_numeric()
                
                if current_numeric < required_numeric:
                    gap_size = required_numeric - current_numeric
                    
                    gap = SkillGap(
                        skill_name=skill_name,
                        current_level=current_skill.proficiency,
                        target_level=required_level,
                        gap_size=gap_size,
                        priority=min(5, gap_size + 1),
                        recommended_actions=self._generate_recommendations(
                            skill_name,
                            current_skill,
                            required_level
                        )
                    )
                    gaps.append(gap)
        
        # Sort by priority
        gaps.sort(key=lambda g: g.priority, reverse=True)
        
        return gaps
    
    def _get_role_requirements(self, role: Optional[str]) -> Dict[str, SkillLevel]:
        """
        Get skill requirements for a role.
        
        Args:
            role: Target role
            
        Returns:
            Dictionary mapping skill names to required levels
        """
        # Default requirements
        default = {
            'reconnaissance': SkillLevel.INTERMEDIATE,
            'exploitation': SkillLevel.INTERMEDIATE,
            'post_exploitation': SkillLevel.INTERMEDIATE,
            'social_engineering': SkillLevel.NOVICE,
            'stealth_operations': SkillLevel.INTERMEDIATE
        }
        
        # Role-specific requirements
        role_requirements = {
            'red_team_expert': {
                'reconnaissance': SkillLevel.EXPERT,
                'exploitation': SkillLevel.EXPERT,
                'post_exploitation': SkillLevel.EXPERT,
                'lateral_movement': SkillLevel.ADVANCED,
                'privilege_escalation': SkillLevel.ADVANCED,
                'stealth_operations': SkillLevel.EXPERT
            },
            'blue_team_expert': {
                'threat_detection': SkillLevel.EXPERT,
                'incident_response': SkillLevel.EXPERT,
                'log_analysis': SkillLevel.EXPERT,
                'threat_hunting': SkillLevel.ADVANCED,
                'forensics': SkillLevel.ADVANCED
            },
            'social_engineer_expert': {
                'social_engineering': SkillLevel.EXPERT,
                'pretexting': SkillLevel.EXPERT,
                'phishing': SkillLevel.EXPERT,
                'vishing': SkillLevel.ADVANCED,
                'elicitation': SkillLevel.ADVANCED
            }
        }
        
        if role is None:
            return default
        return role_requirements.get(role, default)
    
    def _generate_recommendations(self,
                                 skill_name: str,
                                 current_skill: SkillMetric,
                                 target_level: SkillLevel) -> List[str]:
        """
        Generate training recommendations for a skill gap.
        
        Args:
            skill_name: Name of the skill
            current_skill: Current skill metrics
            target_level: Target proficiency level
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        gap = target_level.to_numeric() - current_skill.proficiency.to_numeric()
        
        if gap >= 3:
            recommendations.append(f"Complete advanced {skill_name} certification")
            recommendations.append(f"Practice {skill_name} in complex scenarios")
        elif gap >= 2:
            recommendations.append(f"Take intermediate {skill_name} course")
            recommendations.append(f"Apply {skill_name} in real-world simulations")
        else:
            recommendations.append(f"Refine {skill_name} through repeated practice")
            recommendations.append(f"Mentor others in {skill_name}")
        
        # Add specific recommendations based on current performance
        if current_skill.success_rate < 0.7:
            recommendations.append(f"Focus on success rate improvement for {skill_name}")
        
        if current_skill.practice_count < 10:
            recommendations.append(f"Increase practice frequency for {skill_name}")
        
        return recommendations


@dataclass
class TrainingRecommendation:
    """
    AI-driven training recommendation.
    
    Attributes:
        id: Unique identifier
        operator_id: Target operator
        recommendation_type: Type of recommendation
        priority: Priority level (1-5)
        title: Recommendation title
        description: Detailed description
        suggested_scenarios: Recommended training scenarios
        estimated_time: Estimated time to complete
        expected_outcome: Expected improvement
        created_at: When recommendation was generated
    """
    id: str
    operator_id: str
    recommendation_type: RecommendationType
    priority: int
    title: str
    description: str
    suggested_scenarios: List[str] = field(default_factory=list)
    estimated_time: timedelta = timedelta(hours=1)
    expected_outcome: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'recommendation_type': self.recommendation_type.value,
            'priority': self.priority,
            'title': self.title,
            'description': self.description,
            'suggested_scenarios': self.suggested_scenarios,
            'estimated_time_hours': self.estimated_time.total_seconds() / 3600,
            'expected_outcome': self.expected_outcome,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class CompetencyMatrix:
    """
    Track proficiency across multiple domains.
    
    Attributes:
        operator_id: Operator identifier
        domains: Dictionary mapping domains to skill levels
        last_updated: Last update timestamp
    """
    operator_id: str
    domains: Dict[str, Dict[str, SkillLevel]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_domain(self, domain: str, skills: Dict[str, SkillLevel]) -> None:
        """
        Add or update a domain.
        
        Args:
            domain: Domain name (e.g., "red_team", "blue_team")
            skills: Dictionary mapping skill names to levels
        """
        self.domains[domain] = skills
        self.last_updated = datetime.now(timezone.utc)
    
    def get_domain_proficiency(self, domain: str) -> float:
        """
        Calculate overall proficiency for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Average proficiency (0.0-1.0)
        """
        if domain not in self.domains:
            return 0.0
        
        skills = self.domains[domain]
        if not skills:
            return 0.0
        
        total = sum(level.to_numeric() for level in skills.values())
        avg = total / len(skills)
        
        # Normalize to 0-1 scale (max level is 5)
        return avg / 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operator_id': self.operator_id,
            'domains': {
                domain: {skill: level.value for skill, level in skills.items()}
                for domain, skills in self.domains.items()
            },
            'last_updated': self.last_updated.isoformat()
        }


class TrainingEffectivenessTracker:
    """
    Main training effectiveness tracking system.
    
    Measures actual learning outcomes, retention, and provides
    intelligent recommendations for optimal training paths.
    """
    
    def __init__(self):
        """Initialize training effectiveness tracker."""
        self.logger = logging.getLogger("training_effectiveness")
        
        # Learning curves by operator and skill
        self.learning_curves: Dict[str, Dict[str, LearningCurve]] = {}
        
        # Retention analysis
        self.retention_data: Dict[str, Dict[str, RetentionAnalysis]] = {}
        
        # Competency matrices
        self.competency_matrices: Dict[str, CompetencyMatrix] = {}
        
        # Analyzers
        self.gap_analyzer = SkillGapAnalyzer()
    
    def track_learning_progress(self,
                               operator_id: str,
                               skill_name: str,
                               timestamp: datetime,
                               score: float) -> LearningCurve:
        """
        Track learning progress for a skill.
        
        Args:
            operator_id: Operator identifier
            skill_name: Skill being practiced
            timestamp: When the score was achieved
            score: Performance score (0.0-1.0)
            
        Returns:
            Updated learning curve
        """
        if operator_id not in self.learning_curves:
            self.learning_curves[operator_id] = {}
        
        if skill_name not in self.learning_curves[operator_id]:
            self.learning_curves[operator_id][skill_name] = LearningCurve(
                skill_name=skill_name
            )
        
        curve = self.learning_curves[operator_id][skill_name]
        curve.add_data_point(timestamp, score)
        
        return curve
    
    def analyze_retention(self,
                         operator_id: str,
                         skill_name: str,
                         current_score: float,
                         previous_score: float) -> RetentionAnalysis:
        """
        Analyze knowledge retention for a skill.
        
        Args:
            operator_id: Operator identifier
            skill_name: Skill being analyzed
            current_score: Current performance score
            previous_score: Previous performance score
            
        Returns:
            Retention analysis
        """
        if operator_id not in self.retention_data:
            self.retention_data[operator_id] = {}
        
        if skill_name not in self.retention_data[operator_id]:
            self.retention_data[operator_id][skill_name] = RetentionAnalysis(
                skill_name=skill_name,
                last_practice_date=datetime.now(timezone.utc)
            )
        
        analysis = self.retention_data[operator_id][skill_name]
        analysis.calculate_retention(
            datetime.now(timezone.utc),
            current_score,
            previous_score
        )
        analysis.last_practice_date = datetime.now(timezone.utc)
        
        return analysis
    
    def get_skill_gaps(self,
                      operator_profile: OperatorProfile,
                      target_role: Optional[str] = None) -> List[SkillGap]:
        """
        Identify skill gaps for an operator.
        
        Args:
            operator_profile: Operator profile
            target_role: Optional target role
            
        Returns:
            List of skill gaps
        """
        return self.gap_analyzer.analyze_gaps(operator_profile, target_role)
    
    def generate_recommendations(self,
                               operator_id: str,
                               operator_profile: OperatorProfile,
                               recent_sessions: List[SessionPerformance],
                               target_role: Optional[str] = None) -> List[TrainingRecommendation]:
        """
        Generate AI-driven training recommendations.
        
        Args:
            operator_id: Operator identifier
            operator_profile: Operator profile
            recent_sessions: Recent training sessions
            target_role: Optional target role
            
        Returns:
            List of training recommendations
        """
        recommendations = []
        
        # Analyze skill gaps
        gaps = self.get_skill_gaps(operator_profile, target_role)
        
        # Generate gap-based recommendations
        for gap in gaps[:3]:  # Top 3 gaps
            rec = TrainingRecommendation(
                id=f"rec_{operator_id}_{gap.skill_name}_{int(datetime.now(timezone.utc).timestamp())}",
                operator_id=operator_id,
                recommendation_type=RecommendationType.SKILL_DEVELOPMENT,
                priority=gap.priority,
                title=f"Improve {gap.skill_name}",
                description=f"Current level: {gap.current_level.value}. Target: {gap.target_level.value}",
                suggested_scenarios=[f"{gap.skill_name}_training_scenario"],
                estimated_time=timedelta(hours=gap.gap_size * 2),
                expected_outcome=f"Advance from {gap.current_level.value} to {gap.target_level.value}"
            )
            recommendations.append(rec)
        
        # Check for skills needing retention practice
        if operator_id in self.retention_data:
            for skill_name, retention in self.retention_data[operator_id].items():
                if retention.needs_review():
                    rec = TrainingRecommendation(
                        id=f"rec_{operator_id}_retention_{skill_name}_{int(datetime.now(timezone.utc).timestamp())}",
                        operator_id=operator_id,
                        recommendation_type=RecommendationType.KNOWLEDGE_RETENTION,
                        priority=3,
                        title=f"Review {skill_name}",
                        description=f"Last practiced {(datetime.now(timezone.utc) - retention.last_practice_date).days} days ago",
                        suggested_scenarios=[f"{skill_name}_review_scenario"],
                        estimated_time=timedelta(hours=1),
                        expected_outcome="Maintain proficiency and prevent skill decay"
                    )
                    recommendations.append(rec)
        
        # Check for plateau situations
        if operator_id in self.learning_curves:
            for skill_name, curve in self.learning_curves[operator_id].items():
                if curve.is_plateaued() and curve.current_score < 0.9:
                    rec = TrainingRecommendation(
                        id=f"rec_{operator_id}_plateau_{skill_name}_{int(datetime.now(timezone.utc).timestamp())}",
                        operator_id=operator_id,
                        recommendation_type=RecommendationType.ADVANCED_CHALLENGE,
                        priority=4,
                        title=f"Break through {skill_name} plateau",
                        description=f"Performance has plateaued at {curve.current_score:.2f}",
                        suggested_scenarios=[f"{skill_name}_advanced_scenario"],
                        estimated_time=timedelta(hours=3),
                        expected_outcome="Overcome learning plateau and advance to next level"
                    )
                    recommendations.append(rec)
        
        # Check for burnout risk (too many sessions recently)
        if len(recent_sessions) > 10:
            recent_window = [s for s in recent_sessions 
                           if (datetime.now(timezone.utc) - s.start_time).days <= 7]
            if len(recent_window) > 7:
                rec = TrainingRecommendation(
                    id=f"rec_{operator_id}_break_{int(datetime.now(timezone.utc).timestamp())}",
                    operator_id=operator_id,
                    recommendation_type=RecommendationType.BREAK_RECOMMENDED,
                    priority=5,
                    title="Take a break",
                    description="High training frequency detected. Rest is important for retention.",
                    suggested_scenarios=[],
                    estimated_time=timedelta(days=2),
                    expected_outcome="Improved focus and knowledge consolidation"
                )
                recommendations.append(rec)
        
        # Check for certification readiness
        high_skill_count = sum(
            1 for skill in operator_profile.skills.values()
            if skill.proficiency.to_numeric() >= 4
        )
        
        if high_skill_count >= 5:
            rec = TrainingRecommendation(
                id=f"rec_{operator_id}_cert_{int(datetime.now(timezone.utc).timestamp())}",
                operator_id=operator_id,
                recommendation_type=RecommendationType.CERTIFICATION_READY,
                priority=4,
                title="Consider certification",
                description=f"You have achieved expert level in {high_skill_count} skills",
                suggested_scenarios=["certification_preparation_scenario"],
                estimated_time=timedelta(hours=8),
                expected_outcome="Obtain professional certification"
            )
            recommendations.append(rec)
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        return recommendations
    
    def calculate_time_to_proficiency(self,
                                     operator_id: str,
                                     skill_name: str,
                                     target_level: SkillLevel) -> Optional[Dict[str, Any]]:
        """
        Calculate estimated time to reach target proficiency.
        
        Args:
            operator_id: Operator identifier
            skill_name: Skill name
            target_level: Target proficiency level
            
        Returns:
            Dictionary with time estimate, or None if not calculable
        """
        if operator_id not in self.learning_curves:
            return None
        
        curve = self.learning_curves[operator_id].get(skill_name)
        if not curve:
            return None
        
        target_score = target_level.to_numeric() / 5.0  # Normalize to 0-1
        sessions_needed = curve.predict_time_to_mastery(target_score)
        
        if sessions_needed is None:
            return None
        
        # Assume 2 hours per session
        hours_needed = sessions_needed * 2
        
        return {
            'skill_name': skill_name,
            'target_level': target_level.value,
            'sessions_needed': sessions_needed,
            'estimated_hours': hours_needed,
            'estimated_days': hours_needed / 8,  # 8 hours per day
            'current_score': curve.current_score,
            'learning_rate': curve.learning_rate
        }
    
    def update_competency_matrix(self,
                                operator_id: str,
                                operator_profile: OperatorProfile) -> CompetencyMatrix:
        """
        Update competency matrix for an operator.
        
        Args:
            operator_id: Operator identifier
            operator_profile: Operator profile
            
        Returns:
            Updated competency matrix
        """
        if operator_id not in self.competency_matrices:
            self.competency_matrices[operator_id] = CompetencyMatrix(
                operator_id=operator_id
            )
        
        matrix = self.competency_matrices[operator_id]
        
        # Group skills by domain
        domains: Dict[str, Dict[str, SkillLevel]] = {}
        
        for skill_name, skill_metric in operator_profile.skills.items():
            # Categorize skill into domain (simplified)
            if any(x in skill_name.lower() for x in ['reconnaissance', 'exploitation', 'post_exploitation']):
                domain = 'red_team'
            elif any(x in skill_name.lower() for x in ['detection', 'response', 'forensics']):
                domain = 'blue_team'
            elif any(x in skill_name.lower() for x in ['social', 'phishing', 'pretexting']):
                domain = 'social_engineering'
            else:
                domain = 'general'
            
            if domain not in domains:
                domains[domain] = {}
            
            domains[domain][skill_name] = skill_metric.proficiency
        
        # Update matrix
        for domain, skills in domains.items():
            matrix.add_domain(domain, skills)
        
        return matrix
    
    def get_training_statistics(self, operator_id: str) -> Dict[str, Any]:
        """
        Get comprehensive training effectiveness statistics.
        
        Args:
            operator_id: Operator identifier
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'operator_id': operator_id,
            'learning_curves': {},
            'retention_data': {},
            'competency_matrix': None
        }
        
        # Learning curves
        if operator_id in self.learning_curves:
            stats['learning_curves'] = {
                skill: curve.to_dict()
                for skill, curve in self.learning_curves[operator_id].items()
            }
        
        # Retention data
        if operator_id in self.retention_data:
            stats['retention_data'] = {
                skill: retention.to_dict()
                for skill, retention in self.retention_data[operator_id].items()
            }
        
        # Competency matrix
        if operator_id in self.competency_matrices:
            stats['competency_matrix'] = self.competency_matrices[operator_id].to_dict()
        
        return stats