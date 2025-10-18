"""
ATS MAFIA Framework Analytics Aggregator

This module provides pre-computed metrics for fast dashboard loading,
including cached metrics, trend calculations, leaderboards, and alerts.
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from enum import Enum

from .performance_metrics import PerformanceMetricsEngine, MetricType
from .training_effectiveness import TrainingEffectivenessTracker
from .progress_tracker import ProgressTracker
from .cost_tracker import CostTracker


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    BUDGET_WARNING = "budget_warning"
    PERFORMANCE_ISSUE = "performance_issue"
    GOAL_DEADLINE = "goal_deadline"
    CERTIFICATION_EXPIRING = "certification_expiring"
    SKILL_PLATEAU = "skill_plateau"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_HEALTH = "system_health"


@dataclass
class Alert:
    """
    Performance or system alert.
    
    Attributes:
        id: Unique identifier
        alert_type: Type of alert
        priority: Priority level
        title: Alert title
        message: Alert message
        details: Additional details
        created_at: When alert was created
        acknowledged: Whether alert has been acknowledged
        operator_id: Optional related operator
    """
    id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    details: Dict[str, Any]
    created_at: datetime
    acknowledged: bool = False
    operator_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class CachedMetric:
    """
    Cached metric for fast retrieval.
    
    Attributes:
        key: Metric key
        value: Metric value
        timestamp: When metric was calculated
        ttl_seconds: Time to live in seconds
    """
    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if cached metric has expired."""
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'expired': self.is_expired()
        }


class MetricAggregator:
    """Pre-calculate common dashboard metrics for fast loading."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 cost_tracker: CostTracker,
                 progress_tracker: ProgressTracker):
        """
        Initialize metric aggregator.
        
        Args:
            performance_engine: Performance metrics engine
            cost_tracker: Cost tracker
            progress_tracker: Progress tracker
        """
        self.logger = logging.getLogger("metric_aggregator")
        self.performance_engine = performance_engine
        self.cost_tracker = cost_tracker
        self.progress_tracker = progress_tracker
        
        # Metric cache
        self.cache: Dict[str, CachedMetric] = {}
        self.lock = threading.RLock()
    
    def get_metric(self, key: str, force_refresh: bool = False) -> Any:
        """
        Get a cached metric value.
        
        Args:
            key: Metric key
            force_refresh: Force recalculation
            
        Returns:
            Metric value
        """
        with self.lock:
            cached = self.cache.get(key)
            
            if cached and not cached.is_expired() and not force_refresh:
                return cached.value
            
            # Recalculate metric
            value = self._calculate_metric(key)
            
            # Cache the result
            self.cache[key] = CachedMetric(
                key=key,
                value=value,
                timestamp=datetime.now(timezone.utc)
            )
            
            return value
    
    def _calculate_metric(self, key: str) -> Any:
        """Calculate a specific metric."""
        if key == "active_sessions_count":
            return self._count_active_sessions()
        elif key == "today_training_hours":
            return self._calculate_today_training_hours()
        elif key == "week_cost":
            return self._calculate_week_cost()
        elif key == "total_operators":
            return len(self.performance_engine.operator_profiles)
        elif key == "total_achievements":
            return sum(len(a) for a in self.progress_tracker.achievements.values())
        elif key == "average_operator_level":
            return self._calculate_average_operator_level()
        elif key == "success_rate_7d":
            return self._calculate_success_rate(days=7)
        elif key == "cost_efficiency_trend":
            return self._calculate_cost_efficiency_trend()
        else:
            return None
    
    def _count_active_sessions(self) -> int:
        """Count currently active sessions."""
        # Would need orchestrator reference for real implementation
        return 0
    
    def _calculate_today_training_hours(self) -> float:
        """Calculate total training hours for today."""
        today = datetime.now(timezone.utc).date()
        total_hours = 0.0
        
        for session in self.performance_engine.session_performances.values():
            if session.start_time.date() == today:
                total_hours += session.duration_seconds / 3600
        
        return round(total_hours, 2)
    
    def _calculate_week_cost(self) -> float:
        """Calculate total cost for the current week."""
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        with self.cost_tracker.lock:
            week_cost = sum(
                r.cost for r in self.cost_tracker.usage_records
                if r.timestamp >= week_ago
            )
        
        return round(week_cost, 2)
    
    def _calculate_average_operator_level(self) -> float:
        """Calculate average operator level."""
        if not self.performance_engine.operator_profiles:
            return 0.0
        
        total_level = sum(
            self.progress_tracker.get_operator_level(op_id)
            for op_id in self.performance_engine.operator_profiles.keys()
        )
        
        avg = total_level / len(self.performance_engine.operator_profiles)
        return round(avg, 1)
    
    def _calculate_success_rate(self, days: int) -> float:
        """Calculate success rate over specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        total_sessions = 0
        successful_sessions = 0
        
        for session in self.performance_engine.session_performances.values():
            if session.start_time >= cutoff:
                total_sessions += 1
                if session.success:
                    successful_sessions += 1
        
        if total_sessions == 0:
            return 0.0
        
        return round((successful_sessions / total_sessions) * 100, 1)
    
    def _calculate_cost_efficiency_trend(self) -> str:
        """Calculate cost efficiency trend."""
        # Simple implementation - would need more sophisticated analysis
        week_cost = self._calculate_week_cost()
        week_sessions = len([
            s for s in self.performance_engine.session_performances.values()
            if (datetime.now(timezone.utc) - s.start_time).days <= 7
        ])
        
        if week_sessions == 0:
            return "neutral"
        
        cost_per_session = week_cost / week_sessions
        
        if cost_per_session < 1.0:
            return "improving"
        elif cost_per_session > 2.0:
            return "declining"
        else:
            return "stable"
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary with all key metrics.
        
        Returns:
            Dictionary with dashboard metrics
        """
        return {
            'active_sessions': self.get_metric('active_sessions_count'),
            'today_training_hours': self.get_metric('today_training_hours'),
            'week_cost': self.get_metric('week_cost'),
            'total_operators': self.get_metric('total_operators'),
            'total_achievements': self.get_metric('total_achievements'),
            'average_operator_level': self.get_metric('average_operator_level'),
            'success_rate_7d': self.get_metric('success_rate_7d'),
            'cost_efficiency_trend': self.get_metric('cost_efficiency_trend'),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    
    def refresh_all_metrics(self) -> None:
        """Refresh all cached metrics."""
        with self.lock:
            for key in list(self.cache.keys()):
                self.get_metric(key, force_refresh=True)
        
        self.logger.info("Refreshed all cached metrics")


class TrendCalculator:
    """Calculate trend data for various time periods."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 cost_tracker: CostTracker):
        """
        Initialize trend calculator.
        
        Args:
            performance_engine: Performance metrics engine
            cost_tracker: Cost tracker
        """
        self.logger = logging.getLogger("trend_calculator")
        self.performance_engine = performance_engine
        self.cost_tracker = cost_tracker
    
    def calculate_performance_trend(self,
                                   operator_id: Optional[str] = None,
                                   period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate performance trend over time period.
        
        Args:
            operator_id: Optional operator filter
            period_days: Number of days to analyze
            
        Returns:
            Trend data
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        
        # Get sessions in period
        if operator_id:
            sessions = [
                s for s in self.performance_engine.session_performances.values()
                if s.operator_id == operator_id and s.start_time >= cutoff
            ]
        else:
            sessions = [
                s for s in self.performance_engine.session_performances.values()
                if s.start_time >= cutoff
            ]
        
        if not sessions:
            return {
                'trend': 'insufficient_data',
                'data_points': []
            }
        
        # Group by day
        daily_scores = defaultdict(list)
        for session in sessions:
            date_key = session.start_time.date().isoformat()
            daily_scores[date_key].append(session.score)
        
        # Calculate daily averages
        data_points = []
        for date_key in sorted(daily_scores.keys()):
            scores = daily_scores[date_key]
            avg_score = sum(scores) / len(scores)
            data_points.append({
                'date': date_key,
                'average_score': round(avg_score, 3),
                'session_count': len(scores)
            })
        
        # Determine trend direction
        if len(data_points) >= 2:
            first_half_avg = sum(dp['average_score'] for dp in data_points[:len(data_points)//2]) / (len(data_points)//2)
            second_half_avg = sum(dp['average_score'] for dp in data_points[len(data_points)//2:]) / (len(data_points) - len(data_points)//2)
            
            if second_half_avg > first_half_avg * 1.1:
                trend = 'improving'
            elif second_half_avg < first_half_avg * 0.9:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'data_points': data_points,
            'period_days': period_days
        }
    
    def calculate_cost_trend(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate cost trend over time period.
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Cost trend data
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        
        with self.cost_tracker.lock:
            records = [
                r for r in self.cost_tracker.usage_records
                if r.timestamp >= cutoff
            ]
        
        if not records:
            return {
                'trend': 'insufficient_data',
                'data_points': []
            }
        
        # Group by day
        daily_costs = defaultdict(float)
        for record in records:
            date_key = record.timestamp.date().isoformat()
            daily_costs[date_key] += record.cost
        
        # Create data points
        data_points = [
            {
                'date': date_key,
                'cost': round(cost, 2)
            }
            for date_key, cost in sorted(daily_costs.items())
        ]
        
        # Determine trend
        if len(data_points) >= 2:
            first_half_avg = sum(dp['cost'] for dp in data_points[:len(data_points)//2]) / (len(data_points)//2)
            second_half_avg = sum(dp['cost'] for dp in data_points[len(data_points)//2:]) / (len(data_points) - len(data_points)//2)
            
            if second_half_avg > first_half_avg * 1.2:
                trend = 'increasing'
            elif second_half_avg < first_half_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'data_points': data_points,
            'total_cost': round(sum(daily_costs.values()), 2),
            'period_days': period_days
        }


class LeaderboardManager:
    """Maintain competitive rankings and leaderboards."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 progress_tracker: ProgressTracker):
        """
        Initialize leaderboard manager.
        
        Args:
            performance_engine: Performance metrics engine
            progress_tracker: Progress tracker
        """
        self.logger = logging.getLogger("leaderboard_manager")
        self.performance_engine = performance_engine
        self.progress_tracker = progress_tracker
    
    def get_xp_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get XP leaderboard.
        
        Args:
            limit: Number of entries to return
            
        Returns:
            List of leaderboard entries
        """
        entries = []
        
        for operator_id, profile in self.performance_engine.operator_profiles.items():
            xp = self.progress_tracker.get_operator_xp(operator_id)
            level = self.progress_tracker.get_operator_level(operator_id)
            
            entries.append({
                'operator_id': operator_id,
                'name': profile.name,
                'xp': xp,
                'level': level
            })
        
        # Sort by XP (descending)
        entries.sort(key=lambda e: e['xp'], reverse=True)
        
        # Add ranks
        for idx, entry in enumerate(entries[:limit]):
            entry['rank'] = idx + 1
        
        return entries[:limit]
    
    def get_skill_leaderboard(self,
                             skill_name: str,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get leaderboard for a specific skill.
        
        Args:
            skill_name: Skill to rank by
            limit: Number of entries to return
            
        Returns:
            List of leaderboard entries
        """
        entries = []
        
        for operator_id, profile in self.performance_engine.operator_profiles.items():
            if skill_name in profile.skills:
                skill = profile.skills[skill_name]
                
                entries.append({
                    'operator_id': operator_id,
                    'name': profile.name,
                    'skill_name': skill_name,
                    'proficiency': skill.proficiency.value,
                    'proficiency_score': skill.proficiency.to_numeric(),
                    'average_score': skill.average_score,
                    'success_rate': skill.success_rate
                })
        
        # Sort by proficiency and average score
        entries.sort(
            key=lambda e: (e['proficiency_score'], e['average_score']),
            reverse=True
        )
        
        # Add ranks
        for idx, entry in enumerate(entries[:limit]):
            entry['rank'] = idx + 1
        
        return entries[:limit]
    
    def get_activity_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get leaderboard by training activity.
        
        Args:
            limit: Number of entries to return
            
        Returns:
            List of leaderboard entries
        """
        entries = []
        
        for operator_id, profile in self.performance_engine.operator_profiles.items():
            entries.append({
                'operator_id': operator_id,
                'name': profile.name,
                'total_sessions': profile.total_sessions,
                'total_hours': round(profile.total_hours, 1)
            })
        
        # Sort by total hours
        entries.sort(key=lambda e: e['total_hours'], reverse=True)
        
        # Add ranks
        for idx, entry in enumerate(entries[:limit]):
            entry['rank'] = idx + 1
        
        return entries[:limit]


class AlertManager:
    """Track and prioritize performance alerts."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.logger = logging.getLogger("alert_manager")
        self.alerts: List[Alert] = []
        self.lock = threading.RLock()
    
    def create_alert(self,
                    alert_type: AlertType,
                    priority: AlertPriority,
                    title: str,
                    message: str,
                    details: Optional[Dict[str, Any]] = None,
                    operator_id: Optional[str] = None) -> Alert:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of alert
            priority: Priority level
            title: Alert title
            message: Alert message
            details: Additional details
            operator_id: Optional related operator
            
        Returns:
            Created alert
        """
        import uuid
        
        with self.lock:
            alert = Alert(
                id=str(uuid.uuid4()),
                alert_type=alert_type,
                priority=priority,
                title=title,
                message=message,
                details=details or {},
                created_at=datetime.now(timezone.utc),
                operator_id=operator_id
            )
            
            self.alerts.append(alert)
            self.logger.info(f"Created alert: {title} ({priority.value})")
            
            return alert
    
    def get_active_alerts(self,
                         priority: Optional[AlertPriority] = None,
                         operator_id: Optional[str] = None) -> List[Alert]:
        """
        Get active (unacknowledged) alerts.
        
        Args:
            priority: Optional priority filter
            operator_id: Optional operator filter
            
        Returns:
            List of alerts
        """
        with self.lock:
            alerts = [a for a in self.alerts if not a.acknowledged]
            
            if priority:
                alerts = [a for a in alerts if a.priority == priority]
            
            if operator_id:
                alerts = [a for a in alerts if a.operator_id == operator_id]
            
            # Sort by priority and creation time
            priority_order = {
                AlertPriority.CRITICAL: 0,
                AlertPriority.HIGH: 1,
                AlertPriority.MEDIUM: 2,
                AlertPriority.LOW: 3
            }
            
            alerts.sort(key=lambda a: (priority_order[a.priority], a.created_at))
            
            return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            True if acknowledged, False if not found
        """
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    self.logger.info(f"Acknowledged alert: {alert_id}")
                    return True
        
        return False
    
    def clear_old_alerts(self, days: int = 7) -> int:
        """
        Clear old acknowledged alerts.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of alerts cleared
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        with self.lock:
            initial_count = len(self.alerts)
            
            self.alerts = [
                a for a in self.alerts
                if not a.acknowledged or a.created_at >= cutoff
            ]
            
            cleared = initial_count - len(self.alerts)
            
            if cleared > 0:
                self.logger.info(f"Cleared {cleared} old alerts")
            
            return cleared


class AnalyticsAggregator:
    """
    Main analytics aggregator system.
    
    Provides pre-computed metrics, trends, leaderboards, and alerts
    for fast dashboard loading and real-time monitoring.
    """
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 effectiveness_tracker: TrainingEffectivenessTracker,
                 cost_tracker: CostTracker,
                 progress_tracker: ProgressTracker):
        """
        Initialize analytics aggregator.
        
        Args:
            performance_engine: Performance metrics engine
            effectiveness_tracker: Training effectiveness tracker
            cost_tracker: Cost tracker
            progress_tracker: Progress tracker
        """
        self.logger = logging.getLogger("analytics_aggregator")
        
        # Components
        self.metric_aggregator = MetricAggregator(
            performance_engine, cost_tracker, progress_tracker
        )
        self.trend_calculator = TrendCalculator(performance_engine, cost_tracker)
        self.leaderboard_manager = LeaderboardManager(performance_engine, progress_tracker)
        self.alert_manager = AlertManager()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all dashboard data in one call.
        
        Returns:
            Complete dashboard data
        """
        return {
            'summary': self.metric_aggregator.get_dashboard_summary(),
            'performance_trend_7d': self.trend_calculator.calculate_performance_trend(period_days=7),
            'performance_trend_30d': self.trend_calculator.calculate_performance_trend(period_days=30),
            'cost_trend_7d': self.trend_calculator.calculate_cost_trend(period_days=7),
            'cost_trend_30d': self.trend_calculator.calculate_cost_trend(period_days=30),
            'xp_leaderboard': self.leaderboard_manager.get_xp_leaderboard(),
            'activity_leaderboard': self.leaderboard_manager.get_activity_leaderboard(),
            'active_alerts': [a.to_dict() for a in self.alert_manager.get_active_alerts()],
            'critical_alerts': [
                a.to_dict() for a in self.alert_manager.get_active_alerts(
                    priority=AlertPriority.CRITICAL
                )
            ]
        }
    
    def refresh_cache(self) -> None:
        """Refresh all cached data."""
        self.metric_aggregator.refresh_all_metrics()
        self.logger.info("Refreshed analytics cache")