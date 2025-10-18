"""
ATS MAFIA Framework Performance Metrics Engine

This module provides comprehensive performance tracking and analysis for operator
training, measuring effectiveness, skill progression, and system optimization.
"""

import logging
import threading
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
from enum import Enum
import statistics


class MetricType(Enum):
    """Types of performance metrics."""
    TIME_EFFICIENCY = "time_efficiency"
    COST_EFFICIENCY = "cost_efficiency"
    SUCCESS_RATE = "success_rate"
    SKILL_PROGRESSION = "skill_progression"
    STEALTH_RATING = "stealth_rating"
    TOOL_PROFICIENCY = "tool_proficiency"
    COMMUNICATION_EFFECTIVENESS = "communication_effectiveness"
    DECISION_QUALITY = "decision_quality"


class SkillLevel(Enum):
    """Skill proficiency levels."""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"
    
    def to_numeric(self) -> int:
        """Convert skill level to numeric value for calculations."""
        mapping = {
            self.NOVICE: 1,
            self.INTERMEDIATE: 2,
            self.ADVANCED: 3,
            self.EXPERT: 4,
            self.MASTER: 5
        }
        return mapping.get(self, 1)
    
    @classmethod
    def from_numeric(cls, value: int) -> 'SkillLevel':
        """Convert numeric value to skill level."""
        if value <= 1:
            return cls.NOVICE
        elif value == 2:
            return cls.INTERMEDIATE
        elif value == 3:
            return cls.ADVANCED
        elif value == 4:
            return cls.EXPERT
        else:
            return cls.MASTER


@dataclass
class PerformanceMetric:
    """
    Individual performance metric with value and context.
    
    Attributes:
        id: Unique identifier
        timestamp: When the metric was recorded
        metric_type: Type of metric
        value: Numeric value of the metric
        context: Additional context data
        operator_id: ID of the operator
        session_id: Associated training session
        scenario_id: Associated scenario
    """
    id: str
    timestamp: datetime
    metric_type: MetricType
    value: float
    operator_id: str
    session_id: str
    scenario_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metric_type'] = self.metric_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """Create metric from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['metric_type'] = MetricType(data['metric_type'])
        return cls(**data)


@dataclass
class SkillMetric:
    """
    Skill-specific performance metric.
    
    Attributes:
        skill_name: Name of the skill
        proficiency: Current proficiency level
        last_practiced: Last time skill was practiced
        practice_count: Number of times practiced
        success_rate: Success rate for this skill
        average_score: Average performance score
    """
    skill_name: str
    proficiency: SkillLevel
    last_practiced: datetime
    practice_count: int = 0
    success_rate: float = 0.0
    average_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['proficiency'] = self.proficiency.value
        data['last_practiced'] = self.last_practiced.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillMetric':
        """Create from dictionary."""
        data['proficiency'] = SkillLevel(data['proficiency'])
        data['last_practiced'] = datetime.fromisoformat(data['last_practiced'])
        return cls(**data)


@dataclass
class OperatorProfile:
    """
    Comprehensive operator performance profile.
    
    Tracks individual operator performance over time across multiple
    dimensions including skills, sessions, and achievements.
    """
    operator_id: str
    name: str
    created_at: datetime
    total_sessions: int = 0
    total_hours: float = 0.0
    skill_level: SkillLevel = SkillLevel.NOVICE
    skills: Dict[str, SkillMetric] = field(default_factory=dict)
    certifications: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['skill_level'] = self.skill_level.value
        data['skills'] = {k: v.to_dict() for k, v in self.skills.items()}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperatorProfile':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['skill_level'] = SkillLevel(data['skill_level'])
        data['skills'] = {
            k: SkillMetric.from_dict(v) 
            for k, v in data.get('skills', {}).items()
        }
        return cls(**data)
    
    def update_skill(self, skill_name: str, score: float, success: bool) -> None:
        """
        Update skill metrics based on performance.
        
        Args:
            skill_name: Name of the skill
            score: Performance score (0.0-1.0)
            success: Whether the attempt was successful
        """
        if skill_name not in self.skills:
            self.skills[skill_name] = SkillMetric(
                skill_name=skill_name,
                proficiency=SkillLevel.NOVICE,
                last_practiced=datetime.now(timezone.utc)
            )
        
        skill = self.skills[skill_name]
        skill.practice_count += 1
        skill.last_practiced = datetime.now(timezone.utc)
        
        # Update success rate
        total_attempts = skill.practice_count
        skill.success_rate = (
            (skill.success_rate * (total_attempts - 1) + (1.0 if success else 0.0)) 
            / total_attempts
        )
        
        # Update average score
        skill.average_score = (
            (skill.average_score * (total_attempts - 1) + score) / total_attempts
        )
        
        # Update proficiency based on performance
        if skill.practice_count >= 10:
            if skill.average_score >= 0.9 and skill.success_rate >= 0.9:
                skill.proficiency = SkillLevel.MASTER
            elif skill.average_score >= 0.8 and skill.success_rate >= 0.8:
                skill.proficiency = SkillLevel.EXPERT
            elif skill.average_score >= 0.7 and skill.success_rate >= 0.7:
                skill.proficiency = SkillLevel.ADVANCED
            elif skill.average_score >= 0.5 and skill.success_rate >= 0.6:
                skill.proficiency = SkillLevel.INTERMEDIATE


@dataclass
class SessionPerformance:
    """
    Detailed performance data for a completed training session.
    
    Attributes:
        session_id: Session identifier
        operator_id: Operator identifier
        scenario_id: Scenario identifier
        start_time: Session start time
        end_time: Session end time
        duration_seconds: Session duration
        success: Whether session was successful
        score: Overall performance score (0.0-1.0)
        cost: Total cost for session
        metrics: Individual performance metrics
        skills_practiced: Skills practiced in session
        objectives_completed: Number of objectives completed
        objectives_total: Total number of objectives
    """
    session_id: str
    operator_id: str
    scenario_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    score: float
    cost: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    skills_practiced: List[str] = field(default_factory=list)
    objectives_completed: int = 0
    objectives_total: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        data['metrics'] = [m.to_dict() for m in self.metrics]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionPerformance':
        """Create from dictionary."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['metrics'] = [
            PerformanceMetric.from_dict(m) 
            for m in data.get('metrics', [])
        ]
        return cls(**data)
    
    def get_completion_rate(self) -> float:
        """Get objective completion rate."""
        if self.objectives_total == 0:
            return 0.0
        return self.objectives_completed / self.objectives_total
    
    def get_time_efficiency(self) -> float:
        """
        Calculate time efficiency score.
        
        Returns value between 0.0 and 1.0 based on how quickly
        objectives were completed.
        """
        if self.objectives_total == 0 or self.duration_seconds == 0:
            return 0.0
        
        # Assume 5 minutes per objective as baseline
        expected_time = self.objectives_total * 300
        efficiency = min(1.0, expected_time / self.duration_seconds)
        return efficiency
    
    def get_cost_efficiency(self) -> float:
        """
        Calculate cost efficiency score.
        
        Returns value between 0.0 and 1.0 based on cost vs performance.
        """
        if self.cost == 0:
            return 1.0
        
        # Cost efficiency is performance per dollar spent
        # Assuming $1 per session as baseline
        efficiency = min(1.0, self.score / max(0.01, self.cost))
        return efficiency


class PerformanceAnalyzer:
    """
    Analyze performance trends and patterns.
    
    Provides analysis capabilities for identifying trends, patterns,
    and generating insights from performance data.
    """
    
    def __init__(self):
        """Initialize performance analyzer."""
        self.logger = logging.getLogger("performance_analyzer")
    
    def calculate_trend(self, 
                       metrics: List[PerformanceMetric],
                       window_days: int = 7) -> Dict[str, Any]:
        """
        Calculate performance trend over time.
        
        Args:
            metrics: List of performance metrics
            window_days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        if not metrics:
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'change_rate': 0.0
            }
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Filter to window
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        windowed = [m for m in sorted_metrics if m.timestamp >= cutoff]
        
        if len(windowed) < 2:
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'change_rate': 0.0
            }
        
        # Calculate simple linear trend
        values = [m.value for m in windowed]
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        change = second_half - first_half
        change_rate = change / max(0.01, first_half)
        
        if change_rate > 0.1:
            direction = 'improving'
            trend = 'positive'
        elif change_rate < -0.1:
            direction = 'declining'
            trend = 'negative'
        else:
            direction = 'stable'
            trend = 'neutral'
        
        return {
            'trend': trend,
            'direction': direction,
            'change_rate': change_rate,
            'current_avg': second_half,
            'previous_avg': first_half,
            'sample_size': len(windowed)
        }
    
    def identify_strengths(self,
                          operator_profile: OperatorProfile,
                          min_proficiency: SkillLevel = SkillLevel.ADVANCED) -> List[str]:
        """
        Identify operator's strong skills.
        
        Args:
            operator_profile: Operator profile
            min_proficiency: Minimum proficiency level
            
        Returns:
            List of skill names
        """
        strengths = []
        min_level = min_proficiency.to_numeric()
        
        for skill_name, skill in operator_profile.skills.items():
            if skill.proficiency.to_numeric() >= min_level:
                strengths.append(skill_name)
        
        return strengths
    
    def identify_weaknesses(self,
                           operator_profile: OperatorProfile,
                           max_proficiency: SkillLevel = SkillLevel.INTERMEDIATE) -> List[Tuple[str, SkillMetric]]:
        """
        Identify operator's weak skills needing improvement.
        
        Args:
            operator_profile: Operator profile
            max_proficiency: Maximum proficiency level
            
        Returns:
            List of (skill_name, skill_metric) tuples
        """
        weaknesses = []
        max_level = max_proficiency.to_numeric()
        
        for skill_name, skill in operator_profile.skills.items():
            if skill.proficiency.to_numeric() <= max_level:
                weaknesses.append((skill_name, skill))
        
        # Sort by performance (worst first)
        weaknesses.sort(key=lambda x: (x[1].average_score, x[1].success_rate))
        
        return weaknesses
    
    def calculate_learning_velocity(self,
                                    sessions: List[SessionPerformance]) -> float:
        """
        Calculate learning velocity (rate of improvement).
        
        Args:
            sessions: List of session performances
            
        Returns:
            Learning velocity score (higher is better)
        """
        if len(sessions) < 3:
            return 0.0
        
        # Sort by start time
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)
        
        # Calculate score progression
        scores = [s.score for s in sorted_sessions]
        
        # Simple linear regression
        n = len(scores)
        if n < 2:
            return 0.0
        
        # Calculate slope
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(scores)
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Normalize to 0-1 range (assume max velocity of 0.1 per session)
        velocity = max(0.0, min(1.0, slope / 0.1))
        
        return velocity
    
    def detect_plateau(self,
                      sessions: List[SessionPerformance],
                      window_size: int = 5) -> bool:
        """
        Detect if operator has hit a performance plateau.
        
        Args:
            sessions: List of session performances
            window_size: Number of sessions to analyze
            
        Returns:
            True if plateau detected, False otherwise
        """
        if len(sessions) < window_size:
            return False
        
        # Get recent sessions
        recent = sorted(sessions, key=lambda s: s.start_time)[-window_size:]
        scores = [s.score for s in recent]
        
        # Check for low variance
        if len(scores) < 2:
            return False
        
        variance = statistics.variance(scores)
        mean_score = statistics.mean(scores)
        
        # Plateau if variance is low and not at high performance
        if variance < 0.01 and mean_score < 0.9:
            return True
        
        return False


class BenchmarkEngine:
    """
    Compare performance against historical data and peers.
    
    Provides benchmarking capabilities to compare operator performance
    against historical baselines and peer groups.
    """
    
    def __init__(self):
        """Initialize benchmark engine."""
        self.logger = logging.getLogger("benchmark_engine")
        self.benchmarks: Dict[str, Dict[str, Any]] = {}
    
    def set_benchmark(self,
                     benchmark_id: str,
                     metric_type: MetricType,
                     value: float,
                     context: Optional[Dict[str, Any]] = None) -> None:
        """
        Set a benchmark value.
        
        Args:
            benchmark_id: Benchmark identifier
            metric_type: Type of metric
            value: Benchmark value
            context: Additional context
        """
        self.benchmarks[benchmark_id] = {
            'metric_type': metric_type,
            'value': value,
            'context': context or {},
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
    def compare_to_benchmark(self,
                           metric: PerformanceMetric,
                           benchmark_id: str) -> Dict[str, Any]:
        """
        Compare a metric to a benchmark.
        
        Args:
            metric: Performance metric
            benchmark_id: Benchmark to compare against
            
        Returns:
            Comparison results
        """
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {
                'comparison': 'no_benchmark',
                'difference': 0.0,
                'percentage': 0.0
            }
        
        if benchmark['metric_type'] != metric.metric_type:
            return {
                'comparison': 'type_mismatch',
                'difference': 0.0,
                'percentage': 0.0
            }
        
        benchmark_value = benchmark['value']
        difference = metric.value - benchmark_value
        percentage = (difference / benchmark_value * 100) if benchmark_value != 0 else 0
        
        if difference > 0:
            comparison = 'above_benchmark'
        elif difference < 0:
            comparison = 'below_benchmark'
        else:
            comparison = 'at_benchmark'
        
        return {
            'comparison': comparison,
            'difference': difference,
            'percentage': percentage,
            'metric_value': metric.value,
            'benchmark_value': benchmark_value
        }
    
    def calculate_percentile_rank(self,
                                  value: float,
                                  population: List[float]) -> float:
        """
        Calculate percentile rank within population.
        
        Args:
            value: Value to rank
            population: Population values
            
        Returns:
            Percentile rank (0-100)
        """
        if not population:
            return 50.0
        
        sorted_pop = sorted(population)
        rank = sum(1 for v in sorted_pop if v <= value)
        percentile = (rank / len(sorted_pop)) * 100
        
        return percentile


class PerformanceMetricsEngine:
    """
    Main performance metrics engine.
    
    Coordinates all performance tracking, analysis, and reporting
    for the ATS MAFIA framework.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize performance metrics engine.
        
        Args:
            storage_path: Path to store performance data
        """
        self.storage_path = storage_path
        self.logger = logging.getLogger("performance_metrics")
        
        # Data storage
        self.metrics: List[PerformanceMetric] = []
        self.operator_profiles: Dict[str, OperatorProfile] = {}
        self.session_performances: Dict[str, SessionPerformance] = {}
        self.lock = threading.RLock()
        
        # Analyzers
        self.analyzer = PerformanceAnalyzer()
        self.benchmark_engine = BenchmarkEngine()
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load performance data from storage."""
        if not self.storage_path:
            return
        
        storage_file = Path(self.storage_path)
        if not storage_file.exists():
            return
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Load operator profiles
                for profile_data in data.get('operator_profiles', []):
                    profile = OperatorProfile.from_dict(profile_data)
                    self.operator_profiles[profile.operator_id] = profile
                
                # Load session performances
                for session_data in data.get('session_performances', []):
                    session = SessionPerformance.from_dict(session_data)
                    self.session_performances[session.session_id] = session
                
                # Load metrics
                for metric_data in data.get('metrics', []):
                    metric = PerformanceMetric.from_dict(metric_data)
                    self.metrics.append(metric)
                
                self.logger.info(
                    f"Loaded {len(self.operator_profiles)} profiles, "
                    f"{len(self.session_performances)} sessions, "
                    f"{len(self.metrics)} metrics"
                )
                
        except Exception as e:
            self.logger.error(f"Error loading performance data: {e}")
    
    def _save_data(self) -> None:
        """Save performance data to storage."""
        if not self.storage_path:
            return
        
        try:
            storage_file = Path(self.storage_path)
            storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'operator_profiles': [
                    p.to_dict() for p in self.operator_profiles.values()
                ],
                'session_performances': [
                    s.to_dict() for s in self.session_performances.values()
                ],
                'metrics': [m.to_dict() for m in self.metrics[-10000:]],  # Keep last 10k
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving performance data: {e}")
    
    def create_operator_profile(self,
                               operator_id: str,
                               name: str,
                               metadata: Optional[Dict[str, Any]] = None) -> OperatorProfile:
        """
        Create a new operator profile.
        
        Args:
            operator_id: Unique operator identifier
            name: Operator name
            metadata: Additional metadata
            
        Returns:
            Created operator profile
        """
        with self.lock:
            profile = OperatorProfile(
                operator_id=operator_id,
                name=name,
                created_at=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            self.operator_profiles[operator_id] = profile
            self._save_data()
            
            self.logger.info(f"Created operator profile: {operator_id}")
            return profile
    
    def get_operator_profile(self, operator_id: str) -> Optional[OperatorProfile]:
        """Get operator profile by ID."""
        return self.operator_profiles.get(operator_id)
    
    def record_metric(self,
                     operator_id: str,
                     session_id: str,
                     metric_type: MetricType,
                     value: float,
                     scenario_id: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """
        Record a performance metric.
        
        Args:
            operator_id: Operator identifier
            session_id: Session identifier
            metric_type: Type of metric
            value: Metric value
            scenario_id: Optional scenario identifier
            context: Additional context
            
        Returns:
            Created performance metric
        """
        with self.lock:
            metric = PerformanceMetric(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                metric_type=metric_type,
                value=value,
                operator_id=operator_id,
                session_id=session_id,
                scenario_id=scenario_id,
                context=context or {}
            )
            
            self.metrics.append(metric)
            self._save_data()
            
            return metric
    
    def record_session_performance(self, session_perf: SessionPerformance) -> None:
        """
        Record session performance data.
        
        Args:
            session_perf: Session performance object
        """
        with self.lock:
            self.session_performances[session_perf.session_id] = session_perf
            
            # Update operator profile
            profile = self.operator_profiles.get(session_perf.operator_id)
            if profile:
                profile.total_sessions += 1
                profile.total_hours += session_perf.duration_seconds / 3600
                
                # Update skills
                for skill in session_perf.skills_practiced:
                    profile.update_skill(
                        skill,
                        session_perf.score,
                        session_perf.success
                    )
            
            self._save_data()
            
            self.logger.info(
                f"Recorded session performance: {session_perf.session_id}"
            )
    
    def get_operator_metrics(self,
                           operator_id: str,
                           metric_type: Optional[MetricType] = None,
                           time_range: Optional[timedelta] = None) -> List[PerformanceMetric]:
        """
        Get metrics for an operator.
        
        Args:
            operator_id: Operator identifier
            metric_type: Optional metric type filter
            time_range: Optional time range filter
            
        Returns:
            List of performance metrics
        """
        with self.lock:
            cutoff = None
            if time_range:
                cutoff = datetime.now(timezone.utc) - time_range
            
            filtered = []
            for metric in self.metrics:
                if metric.operator_id != operator_id:
                    continue
                if metric_type and metric.metric_type != metric_type:
                    continue
                if cutoff and metric.timestamp < cutoff:
                    continue
                filtered.append(metric)
            
            return filtered
    
    def get_operator_sessions(self,
                            operator_id: str,
                            limit: Optional[int] = None) -> List[SessionPerformance]:
        """
        Get session performances for an operator.
        
        Args:
            operator_id: Operator identifier
            limit: Optional limit on number of sessions
            
        Returns:
            List of session performances
        """
        with self.lock:
            sessions = [
                s for s in self.session_performances.values()
                if s.operator_id == operator_id
            ]
            
            # Sort by start time (most recent first)
            sessions.sort(key=lambda s: s.start_time, reverse=True)
            
            if limit:
                sessions = sessions[:limit]
            
            return sessions
    
    def analyze_operator_performance(self, operator_id: str) -> Dict[str, Any]:
        """
        Comprehensive performance analysis for an operator.
        
        Args:
            operator_id: Operator identifier
            
        Returns:
            Analysis results
        """
        profile = self.get_operator_profile(operator_id)
        if not profile:
            return {'error': 'operator_not_found'}
        
        sessions = self.get_operator_sessions(operator_id)
        metrics = self.get_operator_metrics(operator_id)
        
        analysis = {
            'operator_id': operator_id,
            'profile': profile.to_dict(),
            'total_sessions': len(sessions),
            'total_metrics': len(metrics),
            'strengths': self.analyzer.identify_strengths(profile),
            'weaknesses': [
                {'skill': s[0], 'proficiency': s[1].proficiency.value}
                for s in self.analyzer.identify_weaknesses(profile)[:5]
            ],
            'learning_velocity': self.analyzer.calculate_learning_velocity(sessions),
            'plateau_detected': self.analyzer.detect_plateau(sessions)
        }
        
        # Add trend analysis for each metric type
        trends = {}
        for metric_type in MetricType:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                trends[metric_type.value] = self.analyzer.calculate_trend(type_metrics)
        
        analysis['trends'] = trends
        
        return analysis