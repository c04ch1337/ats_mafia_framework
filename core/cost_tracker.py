"""
ATS MAFIA Framework Cost Tracking and Budget Management System

This module provides comprehensive cost tracking, budget management, and
optimization recommendations for LLM usage.
"""

import logging
import threading
import json
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

from .llm_models import ModelRegistry, LLMModel


@dataclass
class UsageMetrics:
    """
    Usage metrics for a single LLM request.
    
    Attributes:
        id: Unique identifier for this usage record
        timestamp: When the request was made
        model: Model identifier (provider/name)
        profile_id: Profile that made the request
        session_id: Training session ID
        task_type: Type of task (reconnaissance, exploitation, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Total cost in USD
        latency_ms: Response latency in milliseconds
        success: Whether the request was successful
        error_message: Error message if request failed
    """
    id: str
    timestamp: datetime
    model: str
    profile_id: str
    session_id: str
    task_type: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageMetrics':
        """Create metrics from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class BudgetAlert:
    """
    Budget alert configuration.
    
    Attributes:
        threshold: Percentage threshold (0.0-1.0)
        triggered: Whether alert has been triggered
        callback: Optional callback function when triggered
    """
    threshold: float
    triggered: bool = False
    callback: Optional[Callable[[str, float, float], None]] = None
    
    def __post_init__(self):
        """Validate threshold."""
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")


class CostTracker:
    """
    Comprehensive cost tracking and budget management system.
    
    Tracks LLM usage costs in real-time, enforces budget limits,
    generates analytics, and provides optimization recommendations.
    """
    
    def __init__(self, 
                 registry: ModelRegistry,
                 storage_path: Optional[str] = None):
        """
        Initialize the cost tracker.
        
        Args:
            registry: Model registry for cost calculations
            storage_path: Path to store usage data (optional)
        """
        self.registry = registry
        self.storage_path = storage_path
        self.logger = logging.getLogger("cost_tracker")
        
        # Usage storage
        self.usage_records: List[UsageMetrics] = []
        self.lock = threading.RLock()
        
        # Session tracking
        self.session_totals: Dict[str, float] = {}
        self.session_token_counts: Dict[str, Dict[str, int]] = {}
        
        # Profile tracking
        self.profile_totals: Dict[str, float] = {}
        
        # Model tracking
        self.model_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'avg_latency': 0.0,
            'success_count': 0,
            'error_count': 0
        })
        
        # Budget management
        self.session_budgets: Dict[str, float] = {}
        self.profile_budgets: Dict[str, float] = {}
        self.global_budget: Optional[float] = None
        self.budget_alerts: Dict[str, List[BudgetAlert]] = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'total_cost': 0.0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        
        # Load existing usage data if available
        self._load_usage_data()
    
    def _load_usage_data(self) -> None:
        """Load existing usage data from storage."""
        if not self.storage_path:
            return
        
        storage_file = Path(self.storage_path)
        if not storage_file.exists():
            return
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Load usage records
                for record_data in data.get('usage_records', []):
                    record = UsageMetrics.from_dict(record_data)
                    self.usage_records.append(record)
                
                # Rebuild aggregated data
                self._rebuild_aggregates()
                
                self.logger.info(f"Loaded {len(self.usage_records)} usage records from storage")
                
        except Exception as e:
            self.logger.error(f"Error loading usage data: {e}")
    
    def _save_usage_data(self) -> None:
        """Save usage data to storage."""
        if not self.storage_path:
            return
        
        try:
            storage_file = Path(self.storage_path)
            storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'usage_records': [record.to_dict() for record in self.usage_records],
                'stats': self.stats,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving usage data: {e}")
    
    def _rebuild_aggregates(self) -> None:
        """Rebuild aggregated statistics from usage records."""
        with self.lock:
            # Reset aggregates
            self.session_totals.clear()
            self.session_token_counts.clear()
            self.profile_totals.clear()
            self.model_usage.clear()
            
            # Rebuild from records
            for record in self.usage_records:
                self._update_aggregates(record)
    
    def _update_aggregates(self, metrics: UsageMetrics) -> None:
        """
        Update aggregated statistics with new metrics.
        
        Args:
            metrics: Usage metrics to aggregate
        """
        # Update session totals
        self.session_totals[metrics.session_id] = \
            self.session_totals.get(metrics.session_id, 0.0) + metrics.cost
        
        # Update session token counts
        if metrics.session_id not in self.session_token_counts:
            self.session_token_counts[metrics.session_id] = {
                'input': 0, 'output': 0
            }
        self.session_token_counts[metrics.session_id]['input'] += metrics.input_tokens
        self.session_token_counts[metrics.session_id]['output'] += metrics.output_tokens
        
        # Update profile totals
        self.profile_totals[metrics.profile_id] = \
            self.profile_totals.get(metrics.profile_id, 0.0) + metrics.cost
        
        # Update model usage
        model_stats = self.model_usage[metrics.model]
        model_stats['requests'] += 1
        model_stats['total_cost'] += metrics.cost
        model_stats['total_tokens'] += metrics.input_tokens + metrics.output_tokens
        
        # Update average latency
        prev_avg = model_stats['avg_latency']
        prev_count = model_stats['requests'] - 1
        model_stats['avg_latency'] = \
            (prev_avg * prev_count + metrics.latency_ms) / model_stats['requests']
        
        if metrics.success:
            model_stats['success_count'] += 1
        else:
            model_stats['error_count'] += 1
        
        # Update global stats
        self.stats['total_requests'] += 1
        self.stats['total_cost'] += metrics.cost
        self.stats['total_input_tokens'] += metrics.input_tokens
        self.stats['total_output_tokens'] += metrics.output_tokens
        
        if metrics.success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
    
    def record_usage(self,
                    usage_id: str,
                    model: str,
                    profile_id: str,
                    session_id: str,
                    task_type: str,
                    input_tokens: int,
                    output_tokens: int,
                    latency_ms: float,
                    success: bool = True,
                    error_message: Optional[str] = None) -> float:
        """
        Record LLM usage and calculate cost.
        
        Args:
            usage_id: Unique identifier for this usage
            model: Model identifier (provider/name)
            profile_id: Profile that made the request
            session_id: Training session ID
            task_type: Type of task
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Response latency in milliseconds
            success: Whether the request was successful
            error_message: Error message if request failed
            
        Returns:
            Total cost in USD
        """
        with self.lock:
            # Get model for cost calculation
            parts = model.split('/')
            if len(parts) == 2:
                provider, model_name = parts
                model_obj = self.registry.get_model(provider, model_name)
            else:
                model_obj = None
            
            if not model_obj:
                self.logger.warning(f"Model not found in registry: {model}")
                cost = 0.0
            else:
                cost = model_obj.calculate_cost(input_tokens, output_tokens)
            
            # Create usage record
            metrics = UsageMetrics(
                id=usage_id,
                timestamp=datetime.now(timezone.utc),
                model=model,
                profile_id=profile_id,
                session_id=session_id,
                task_type=task_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message
            )
            
            # Store record
            self.usage_records.append(metrics)
            
            # Update aggregates
            self._update_aggregates(metrics)
            
            # Check budget alerts
            self._check_budget_alerts(session_id, profile_id)
            
            # Persist to storage
            self._save_usage_data()
            
            self.logger.debug(
                f"Recorded usage: {model} - "
                f"{input_tokens}+{output_tokens} tokens - ${cost:.4f}"
            )
            
            return cost
    
    def get_session_cost(self, session_id: str) -> float:
        """
        Get total cost for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Total cost in USD
        """
        with self.lock:
            return self.session_totals.get(session_id, 0.0)
    
    def get_session_tokens(self, session_id: str) -> Dict[str, int]:
        """
        Get token counts for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with input and output token counts
        """
        with self.lock:
            return self.session_token_counts.get(
                session_id,
                {'input': 0, 'output': 0}
            )
    
    def get_profile_cost(self,
                        profile_id: str,
                        time_range: Optional[timedelta] = None) -> float:
        """
        Get total cost for a profile.
        
        Args:
            profile_id: Profile identifier
            time_range: Optional time range to filter by
            
        Returns:
            Total cost in USD
        """
        with self.lock:
            if time_range is None:
                return self.profile_totals.get(profile_id, 0.0)
            
            # Calculate from filtered records
            cutoff = datetime.now(timezone.utc) - time_range
            total = sum(
                record.cost
                for record in self.usage_records
                if record.profile_id == profile_id and record.timestamp >= cutoff
            )
            
            return total
    
    def get_cost_breakdown(self,
                          session_id: Optional[str] = None,
                          profile_id: Optional[str] = None,
                          time_range: Optional[timedelta] = None) -> Dict[str, float]:
        """
        Get cost breakdown by model.
        
        Args:
            session_id: Optional session filter
            profile_id: Optional profile filter
            time_range: Optional time range filter
            
        Returns:
            Dictionary mapping model names to costs
        """
        with self.lock:
            cutoff = datetime.now(timezone.utc) - time_range if time_range else None
            breakdown = {}
            
            for record in self.usage_records:
                # Apply filters
                if session_id and record.session_id != session_id:
                    continue
                if profile_id and record.profile_id != profile_id:
                    continue
                if cutoff and record.timestamp < cutoff:
                    continue
                
                # Aggregate by model
                breakdown[record.model] = breakdown.get(record.model, 0.0) + record.cost
            
            return breakdown
    
    def get_model_statistics(self, model: str) -> Dict[str, Any]:
        """
        Get statistics for a specific model.
        
        Args:
            model: Model identifier
            
        Returns:
            Dictionary with model statistics
        """
        with self.lock:
            stats = self.model_usage.get(model)
            if not stats:
                return {}
            
            return {
                'model': model,
                'total_requests': stats['requests'],
                'successful_requests': stats['success_count'],
                'failed_requests': stats['error_count'],
                'success_rate': stats['success_count'] / stats['requests'] if stats['requests'] > 0 else 0.0,
                'total_cost': stats['total_cost'],
                'total_tokens': stats['total_tokens'],
                'average_cost_per_request': stats['total_cost'] / stats['requests'] if stats['requests'] > 0 else 0.0,
                'average_latency_ms': stats['avg_latency']
            }
    
    def set_session_budget(self, session_id: str, budget: float) -> None:
        """
        Set budget limit for a session.
        
        Args:
            session_id: Session identifier
            budget: Budget limit in USD
        """
        with self.lock:
            self.session_budgets[session_id] = budget
            self.logger.info(f"Set budget for session {session_id}: ${budget:.2f}")
    
    def set_profile_budget(self, profile_id: str, budget: float) -> None:
        """
        Set budget limit for a profile.
        
        Args:
            profile_id: Profile identifier
            budget: Budget limit in USD
        """
        with self.lock:
            self.profile_budgets[profile_id] = budget
            self.logger.info(f"Set budget for profile {profile_id}: ${budget:.2f}")
    
    def set_global_budget(self, budget: float) -> None:
        """
        Set global budget limit.
        
        Args:
            budget: Budget limit in USD
        """
        with self.lock:
            self.global_budget = budget
            self.logger.info(f"Set global budget: ${budget:.2f}")
    
    def add_budget_alert(self,
                        entity_id: str,
                        threshold: float,
                        callback: Optional[Callable[[str, float, float], None]] = None) -> None:
        """
        Add a budget alert for an entity.
        
        Args:
            entity_id: Session or profile ID
            threshold: Alert threshold (0.0-1.0, e.g., 0.75 for 75%)
            callback: Optional callback function(entity_id, spent, budget)
        """
        with self.lock:
            if entity_id not in self.budget_alerts:
                self.budget_alerts[entity_id] = []
            
            alert = BudgetAlert(threshold=threshold, callback=callback)
            self.budget_alerts[entity_id].append(alert)
            
            self.logger.info(
                f"Added budget alert for {entity_id} at {threshold*100:.0f}% threshold"
            )
    
    def _check_budget_alerts(self, session_id: str, profile_id: str) -> None:
        """
        Check and trigger budget alerts if thresholds exceeded.
        
        Args:
            session_id: Session identifier
            profile_id: Profile identifier
        """
        entities_to_check = [
            (session_id, self.session_budgets.get(session_id), self.session_totals.get(session_id, 0.0)),
            (profile_id, self.profile_budgets.get(profile_id), self.profile_totals.get(profile_id, 0.0)),
            ('global', self.global_budget, self.stats['total_cost'])
        ]
        
        for entity_id, budget, spent in entities_to_check:
            if budget is None:
                continue
            
            if entity_id not in self.budget_alerts:
                continue
            
            percentage = spent / budget if budget > 0 else 0.0
            
            for alert in self.budget_alerts[entity_id]:
                if not alert.triggered and percentage >= alert.threshold:
                    alert.triggered = True
                    
                    self.logger.warning(
                        f"Budget alert triggered for {entity_id}: "
                        f"${spent:.2f} / ${budget:.2f} ({percentage*100:.1f}%)"
                    )
                    
                    if alert.callback:
                        try:
                            alert.callback(entity_id, spent, budget)
                        except Exception as e:
                            self.logger.error(f"Error in budget alert callback: {e}")
    
    def is_within_budget(self, session_id: str) -> bool:
        """
        Check if a session is within its budget.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if within budget or no budget set, False otherwise
        """
        with self.lock:
            budget = self.session_budgets.get(session_id)
            if budget is None:
                return True
            
            spent = self.session_totals.get(session_id, 0.0)
            return spent < budget
    
    def get_remaining_budget(self, session_id: str) -> Optional[float]:
        """
        Get remaining budget for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Remaining budget in USD or None if no budget set
        """
        with self.lock:
            budget = self.session_budgets.get(session_id)
            if budget is None:
                return None
            
            spent = self.session_totals.get(session_id, 0.0)
            return max(0.0, budget - spent)
    
    def get_optimization_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of recommendation dictionaries
        """
        with self.lock:
            recommendations = []
            
            # Get session records
            session_records = [
                r for r in self.usage_records
                if r.session_id == session_id
            ]
            
            if not session_records:
                return recommendations
            
            # Analyze model usage
            model_costs = {}
            for record in session_records:
                model_costs[record.model] = model_costs.get(record.model, 0.0) + record.cost
            
            # Check for expensive models
            for model, cost in model_costs.items():
                parts = model.split('/')
                if len(parts) != 2:
                    continue
                
                provider, model_name = parts
                current_model = self.registry.get_model(provider, model_name)
                
                if not current_model:
                    continue
                
                # Find cheaper alternatives
                cheaper_models = self.registry.list_models(
                    max_cost_per_1k=current_model.cost_per_1k_input_tokens * 0.5
                )
                
                if cheaper_models:
                    potential_savings = cost * 0.5  # Rough estimate
                    
                    recommendations.append({
                        'type': 'cheaper_model',
                        'current_model': model,
                        'current_cost': cost,
                        'alternatives': [m.get_full_name() for m in cheaper_models[:3]],
                        'potential_savings': potential_savings,
                        'message': f"Consider using cheaper models. Potential savings: ${potential_savings:.2f}"
                    })
            
            # Check for high token usage
            token_counts = self.get_session_tokens(session_id)
            if token_counts['input'] > 100000:
                recommendations.append({
                    'type': 'high_token_usage',
                    'input_tokens': token_counts['input'],
                    'message': "High input token usage detected. Consider optimizing prompts or using context compression."
                })
            
            return recommendations
    
    def export_usage_data(self,
                         session_id: Optional[str] = None,
                         profile_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         format: str = 'json') -> Union[List[Dict[str, Any]], str]:
        """
        Export usage data for reporting.
        
        Args:
            session_id: Optional session filter
            profile_id: Optional profile filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Export format ('json' or 'csv')
            
        Returns:
            List of usage records or CSV string
        """
        with self.lock:
            # Filter records
            filtered = self.usage_records
            
            if session_id:
                filtered = [r for r in filtered if r.session_id == session_id]
            
            if profile_id:
                filtered = [r for r in filtered if r.profile_id == profile_id]
            
            if start_date:
                filtered = [r for r in filtered if r.timestamp >= start_date]
            
            if end_date:
                filtered = [r for r in filtered if r.timestamp <= end_date]
            
            # Export
            if format == 'json':
                return [record.to_dict() for record in filtered]
            
            elif format == 'csv':
                if not filtered:
                    return ""
                
                # Build CSV
                lines = []
                header = "id,timestamp,model,profile_id,session_id,task_type,input_tokens,output_tokens,cost,latency_ms,success,error_message"
                lines.append(header)
                
                for record in filtered:
                    line = f"{record.id},{record.timestamp.isoformat()},{record.model},{record.profile_id},{record.session_id},{record.task_type},{record.input_tokens},{record.output_tokens},{record.cost},{record.latency_ms},{record.success},{record.error_message or ''}"
                    lines.append(line)
                
                return '\n'.join(lines)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cost tracking statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                'global_stats': self.stats.copy(),
                'active_sessions': len(self.session_totals),
                'active_profiles': len(self.profile_totals),
                'models_used': len(self.model_usage),
                'total_usage_records': len(self.usage_records),
                'average_cost_per_request': self.stats['total_cost'] / self.stats['total_requests'] if self.stats['total_requests'] > 0 else 0.0,
                'success_rate': self.stats['successful_requests'] / self.stats['total_requests'] if self.stats['total_requests'] > 0 else 0.0
            }
    
    def clear_session_data(self, session_id: str) -> None:
        """
        Clear tracking data for a session.
        
        Args:
            session_id: Session identifier
        """
        with self.lock:
            # Remove from aggregates
            self.session_totals.pop(session_id, None)
            self.session_token_counts.pop(session_id, None)
            self.session_budgets.pop(session_id, None)
            self.budget_alerts.pop(session_id, None)
            
            # Don't remove from usage_records to maintain historical data
            
            self.logger.info(f"Cleared session data for {session_id}")
    
    def reset(self) -> None:
        """Reset all tracking data."""
        with self.lock:
            self.usage_records.clear()
            self.session_totals.clear()
            self.session_token_counts.clear()
            self.profile_totals.clear()
            self.model_usage.clear()
            self.session_budgets.clear()
            self.profile_budgets.clear()
            self.global_budget = None
            self.budget_alerts.clear()
            
            self.stats = {
                'total_requests': 0,
                'total_cost': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'successful_requests': 0,
                'failed_requests': 0
            }
            
            self._save_usage_data()
            self.logger.info("Reset all cost tracking data")