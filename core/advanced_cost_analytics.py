"""
ATS MAFIA Framework Advanced Cost Analytics

This module provides enhanced cost optimization, ROI calculation, and predictive
cost forecasting beyond the basic cost tracking capabilities.
"""

import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from enum import Enum

from .cost_tracker import CostTracker, UsageMetrics


class CostCategory(Enum):
    """Categories for cost analysis."""
    MODEL_USAGE = "model_usage"
    PROFILE = "profile"
    SCENARIO = "scenario"
    PHASE = "phase"
    TIME_PERIOD = "time_period"


class OptimizationType(Enum):
    """Types of cost optimization opportunities."""
    MODEL_SUBSTITUTION = "model_substitution"
    BATCH_PROCESSING = "batch_processing"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    CACHING = "caching"
    SCHEDULING = "scheduling"
    BUDGET_REALLOCATION = "budget_reallocation"


@dataclass
class CostBreakdown:
    """
    Detailed cost analysis breakdown.
    
    Attributes:
        category: Category of breakdown
        items: Dictionary mapping items to costs
        total_cost: Total cost for this category
        percentage_of_total: Percentage of overall costs
        time_range: Time range for analysis
    """
    category: CostCategory
    items: Dict[str, float]
    total_cost: float
    percentage_of_total: float
    time_range: Optional[Tuple[datetime, datetime]] = None
    
    def get_top_items(self, n: int = 5) -> List[Tuple[str, float]]:
        """
        Get top N items by cost.
        
        Args:
            n: Number of items to return
            
        Returns:
            List of (item_name, cost) tuples
        """
        sorted_items = sorted(self.items.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'category': self.category.value,
            'items': self.items,
            'total_cost': self.total_cost,
            'percentage_of_total': self.percentage_of_total
        }
        
        if self.time_range:
            data['time_range'] = {
                'start': self.time_range[0].isoformat(),
                'end': self.time_range[1].isoformat()
            }
        
        return data


@dataclass
class OptimizationOpportunity:
    """
    Identified cost optimization opportunity.
    
    Attributes:
        id: Unique identifier
        optimization_type: Type of optimization
        priority: Priority level (1-5)
        title: Opportunity title
        description: Detailed description
        current_cost: Current cost
        potential_savings: Estimated savings
        implementation_difficulty: Difficulty to implement (1-5)
        recommendations: Specific recommendations
    """
    id: str
    optimization_type: OptimizationType
    priority: int
    title: str
    description: str
    current_cost: float
    potential_savings: float
    implementation_difficulty: int
    recommendations: List[str] = field(default_factory=list)
    
    def get_roi_score(self) -> float:
        """
        Calculate ROI score for this opportunity.
        
        Higher score means better return on investment.
        
        Returns:
            ROI score
        """
        if self.implementation_difficulty == 0:
            return 0.0
        
        # ROI = savings / difficulty
        return self.potential_savings / self.implementation_difficulty
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'optimization_type': self.optimization_type.value,
            'priority': self.priority,
            'title': self.title,
            'description': self.description,
            'current_cost': self.current_cost,
            'potential_savings': self.potential_savings,
            'implementation_difficulty': self.implementation_difficulty,
            'recommendations': self.recommendations,
            'roi_score': self.get_roi_score()
        }


@dataclass
class ROIMetrics:
    """
    Return on Investment metrics for training.
    
    Attributes:
        total_investment: Total cost invested
        skill_gains: Number of skill levels gained
        certifications_earned: Number of certifications earned
        proficiency_increase: Average proficiency increase
        time_to_proficiency: Time taken to reach proficiency
        cost_per_skill_level: Cost per skill level gained
        overall_roi: Overall ROI score
    """
    total_investment: float
    skill_gains: int
    certifications_earned: int
    proficiency_increase: float
    time_to_proficiency: float
    cost_per_skill_level: float
    overall_roi: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CostOptimizer:
    """
    Identify cost-saving opportunities and optimization strategies.
    """
    
    def __init__(self, cost_tracker: CostTracker):
        """
        Initialize cost optimizer.
        
        Args:
            cost_tracker: Cost tracker instance
        """
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger("cost_optimizer")
    
    def identify_opportunities(self,
                             session_id: Optional[str] = None,
                             time_range: Optional[timedelta] = None) -> List[OptimizationOpportunity]:
        """
        Identify cost optimization opportunities.
        
        Args:
            session_id: Optional session filter
            time_range: Optional time range filter
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        # Get usage records
        with self.cost_tracker.lock:
            records = self.cost_tracker.usage_records
            
            if session_id:
                records = [r for r in records if r.session_id == session_id]
            
            if time_range:
                cutoff = datetime.now(timezone.utc) - time_range
                records = [r for r in records if r.timestamp >= cutoff]
        
        if not records:
            return opportunities
        
        # Analyze for expensive model usage
        model_costs = defaultdict(float)
        model_tokens = defaultdict(int)
        
        for record in records:
            model_costs[record.model] += record.cost
            model_tokens[record.model] += record.input_tokens + record.output_tokens
        
        # Find expensive models that could be replaced
        for model, cost in model_costs.items():
            if cost > 1.0:  # Threshold for optimization
                # Get model info
                parts = model.split('/')
                if len(parts) == 2:
                    provider, model_name = parts
                    current_model = self.cost_tracker.registry.get_model(provider, model_name)
                    
                    if current_model:
                        # Find cheaper alternatives
                        cheaper_models = self.cost_tracker.registry.list_models(
                            max_cost_per_1k=current_model.cost_per_1k_input_tokens * 0.6
                        )
                        
                        if cheaper_models:
                            # Estimate savings
                            potential_savings = cost * 0.4  # Assume 40% savings
                            
                            opp = OptimizationOpportunity(
                                id=f"opt_model_{model}_{int(datetime.now(timezone.utc).timestamp())}",
                                optimization_type=OptimizationType.MODEL_SUBSTITUTION,
                                priority=4 if potential_savings > 5.0 else 3,
                                title=f"Replace expensive model {model}",
                                description=f"Current cost: ${cost:.2f}. Consider cheaper alternatives.",
                                current_cost=cost,
                                potential_savings=potential_savings,
                                implementation_difficulty=2,
                                recommendations=[
                                    f"Test alternative: {m.get_full_name()}"
                                    for m in cheaper_models[:3]
                                ]
                            )
                            opportunities.append(opp)
        
        # Analyze for high token usage (prompt optimization opportunity)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in records)
        avg_tokens_per_request = total_tokens / len(records) if records else 0
        
        if avg_tokens_per_request > 2000:
            opp = OptimizationOpportunity(
                id=f"opt_prompt_{int(datetime.now(timezone.utc).timestamp())}",
                optimization_type=OptimizationType.PROMPT_OPTIMIZATION,
                priority=4,
                title="Optimize prompt length",
                description=f"Average {avg_tokens_per_request:.0f} tokens per request",
                current_cost=sum(r.cost for r in records),
                potential_savings=sum(r.cost for r in records) * 0.2,
                implementation_difficulty=3,
                recommendations=[
                    "Review and compress prompts",
                    "Remove redundant context",
                    "Use more efficient prompt templates"
                ]
            )
            opportunities.append(opp)
        
        # Analyze for repeated similar requests (caching opportunity)
        task_types = defaultdict(int)
        for record in records:
            task_types[record.task_type] += 1
        
        repeated_tasks = {k: v for k, v in task_types.items() if v > 10}
        if repeated_tasks:
            total_repeated_cost = sum(
                r.cost for r in records
                if r.task_type in repeated_tasks
            )
            
            opp = OptimizationOpportunity(
                id=f"opt_cache_{int(datetime.now(timezone.utc).timestamp())}",
                optimization_type=OptimizationType.CACHING,
                priority=3,
                title="Implement response caching",
                description=f"Detected {sum(repeated_tasks.values())} repeated task patterns",
                current_cost=total_repeated_cost,
                potential_savings=total_repeated_cost * 0.3,
                implementation_difficulty=4,
                recommendations=[
                    "Cache responses for common queries",
                    "Implement semantic caching for similar requests",
                    f"Focus on task types: {', '.join(list(repeated_tasks.keys())[:3])}"
                ]
            )
            opportunities.append(opp)
        
        # Sort by ROI score
        opportunities.sort(key=lambda o: o.get_roi_score(), reverse=True)
        
        return opportunities
    
    def calculate_optimization_impact(self,
                                    opportunities: List[OptimizationOpportunity]) -> Dict[str, Any]:
        """
        Calculate total impact of implementing optimizations.
        
        Args:
            opportunities: List of optimization opportunities
            
        Returns:
            Dictionary with impact analysis
        """
        total_current_cost = sum(o.current_cost for o in opportunities)
        total_potential_savings = sum(o.potential_savings for o in opportunities)
        
        if total_current_cost == 0:
            savings_percentage = 0.0
        else:
            savings_percentage = (total_potential_savings / total_current_cost) * 100
        
        return {
            'total_opportunities': len(opportunities),
            'total_current_cost': total_current_cost,
            'total_potential_savings': total_potential_savings,
            'savings_percentage': savings_percentage,
            'avg_implementation_difficulty': statistics.mean(
                [o.implementation_difficulty for o in opportunities]
            ) if opportunities else 0,
            'high_priority_count': sum(1 for o in opportunities if o.priority >= 4),
            'quick_wins': [
                o.to_dict() for o in opportunities
                if o.implementation_difficulty <= 2 and o.potential_savings > 1.0
            ]
        }


class ROICalculator:
    """
    Calculate return on investment for training activities.
    """
    
    def __init__(self):
        """Initialize ROI calculator."""
        self.logger = logging.getLogger("roi_calculator")
    
    def calculate_training_roi(self,
                              total_cost: float,
                              initial_skill_level: float,
                              final_skill_level: float,
                              training_hours: float,
                              certifications: int = 0) -> ROIMetrics:
        """
        Calculate ROI for training investment.
        
        Args:
            total_cost: Total cost invested
            initial_skill_level: Starting skill level (0-5)
            final_skill_level: Ending skill level (0-5)
            training_hours: Total training hours
            certifications: Number of certifications earned
            
        Returns:
            ROI metrics
        """
        skill_gains = int(final_skill_level - initial_skill_level)
        proficiency_increase = (final_skill_level - initial_skill_level) / 5.0
        
        if skill_gains == 0:
            cost_per_skill_level = 0.0
        else:
            cost_per_skill_level = total_cost / skill_gains
        
        # Calculate time to proficiency
        if training_hours == 0:
            time_to_proficiency = 0.0
        else:
            time_to_proficiency = training_hours / max(1, skill_gains)
        
        # Calculate overall ROI score
        # Higher proficiency increase and certifications = better ROI
        # Lower cost and time = better ROI
        roi_score = 0.0
        
        if total_cost > 0:
            # ROI based on value gained vs cost
            value_gained = (skill_gains * 100) + (certifications * 200)  # Arbitrary value points
            roi_score = (value_gained / total_cost) - 1.0  # -1 to make it relative to investment
        
        return ROIMetrics(
            total_investment=total_cost,
            skill_gains=skill_gains,
            certifications_earned=certifications,
            proficiency_increase=proficiency_increase,
            time_to_proficiency=time_to_proficiency,
            cost_per_skill_level=cost_per_skill_level,
            overall_roi=roi_score
        )
    
    def compare_training_methods(self,
                                methods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare ROI across different training methods.
        
        Args:
            methods: List of training method data
            
        Returns:
            Comparison analysis
        """
        if not methods:
            return {'error': 'no_methods_provided'}
        
        roi_metrics = []
        for method in methods:
            metrics = self.calculate_training_roi(
                total_cost=method.get('cost', 0),
                initial_skill_level=method.get('initial_level', 0),
                final_skill_level=method.get('final_level', 0),
                training_hours=method.get('hours', 0),
                certifications=method.get('certifications', 0)
            )
            roi_metrics.append({
                'method_name': method.get('name', 'Unknown'),
                'metrics': metrics.to_dict()
            })
        
        # Find best method
        best_roi = max(roi_metrics, key=lambda m: m['metrics']['overall_roi'])
        most_efficient = min(
            roi_metrics,
            key=lambda m: m['metrics']['cost_per_skill_level']
            if m['metrics']['cost_per_skill_level'] > 0 else float('inf')
        )
        
        return {
            'methods': roi_metrics,
            'best_roi': best_roi,
            'most_cost_efficient': most_efficient,
            'average_roi': statistics.mean(
                [m['metrics']['overall_roi'] for m in roi_metrics]
            )
        }


class BudgetPlanner:
    """
    Predictive budget planning based on training goals.
    """
    
    def __init__(self, cost_tracker: CostTracker):
        """
        Initialize budget planner.
        
        Args:
            cost_tracker: Cost tracker instance
        """
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger("budget_planner")
    
    def predict_training_cost(self,
                            target_skill_gains: int,
                            training_hours: float,
                            model_tier: str = "standard") -> Dict[str, Any]:
        """
        Predict cost for achieving training goals.
        
        Args:
            target_skill_gains: Number of skill levels to gain
            training_hours: Expected training hours
            model_tier: Model tier to use (economy/standard/premium)
            
        Returns:
            Cost prediction
        """
        # Get historical cost data
        stats = self.cost_tracker.get_statistics()
        avg_cost_per_request = stats.get('average_cost_per_request', 0.01)
        
        # Estimate requests needed
        # Assume 10 requests per hour of training
        estimated_requests = int(training_hours * 10)
        
        # Apply model tier multiplier
        tier_multipliers = {
            'economy': 0.5,
            'standard': 1.0,
            'premium': 2.0
        }
        multiplier = tier_multipliers.get(model_tier, 1.0)
        
        # Calculate prediction
        predicted_cost = estimated_requests * avg_cost_per_request * multiplier
        
        # Add confidence intervals
        variance = predicted_cost * 0.2  # 20% variance
        
        return {
            'predicted_cost': predicted_cost,
            'confidence_range': {
                'low': predicted_cost - variance,
                'high': predicted_cost + variance
            },
            'estimated_requests': estimated_requests,
            'model_tier': model_tier,
            'assumptions': {
                'avg_cost_per_request': avg_cost_per_request,
                'requests_per_hour': 10,
                'tier_multiplier': multiplier
            }
        }
    
    def create_budget_plan(self,
                          total_budget: float,
                          time_period_days: int,
                          priority_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a budget allocation plan.
        
        Args:
            total_budget: Total budget available
            time_period_days: Planning period in days
            priority_areas: Optional priority training areas
            
        Returns:
            Budget plan
        """
        # Allocate budget
        daily_budget = total_budget / time_period_days
        
        # Default allocation percentages
        allocation = {
            'core_training': 0.5,  # 50%
            'advanced_scenarios': 0.3,  # 30%
            'certification_prep': 0.15,  # 15%
            'contingency': 0.05  # 5%
        }
        
        # Adjust for priority areas
        if priority_areas:
            for area in priority_areas:
                if area in allocation:
                    allocation[area] *= 1.2  # Boost priority areas
        
        # Normalize to 100%
        total_allocation = sum(allocation.values())
        allocation = {k: v / total_allocation for k, v in allocation.items()}
        
        # Calculate allocations
        budget_breakdown = {
            area: total_budget * percentage
            for area, percentage in allocation.items()
        }
        
        return {
            'total_budget': total_budget,
            'time_period_days': time_period_days,
            'daily_budget': daily_budget,
            'allocation_percentages': allocation,
            'budget_breakdown': budget_breakdown,
            'weekly_budget': daily_budget * 7,
            'recommendations': [
                f"Allocate ${budget_breakdown['core_training']:.2f} to core training",
                f"Reserve ${budget_breakdown['contingency']:.2f} for contingency",
                "Monitor spending weekly to stay on track"
            ]
        }


class CostAnomalyDetector:
    """
    Identify unusual spending patterns and potential issues.
    """
    
    def __init__(self, cost_tracker: CostTracker):
        """
        Initialize anomaly detector.
        
        Args:
            cost_tracker: Cost tracker instance
        """
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger("cost_anomaly_detector")
    
    def detect_anomalies(self,
                        time_window: timedelta = timedelta(days=7)) -> List[Dict[str, Any]]:
        """
        Detect cost anomalies in recent usage.
        
        Args:
            time_window: Time window to analyze
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        cutoff = datetime.now(timezone.utc) - time_window
        
        with self.cost_tracker.lock:
            recent_records = [
                r for r in self.cost_tracker.usage_records
                if r.timestamp >= cutoff
            ]
        
        if len(recent_records) < 10:
            return anomalies  # Not enough data
        
        # Analyze cost per request
        costs = [r.cost for r in recent_records]
        mean_cost = statistics.mean(costs)
        stdev_cost = statistics.stdev(costs) if len(costs) > 1 else 0
        
        # Detect unusually expensive requests
        threshold = mean_cost + (2 * stdev_cost)
        expensive_requests = [
            r for r in recent_records
            if r.cost > threshold
        ]
        
        if expensive_requests:
            anomalies.append({
                'type': 'expensive_requests',
                'severity': 'medium',
                'count': len(expensive_requests),
                'description': f"Found {len(expensive_requests)} requests exceeding ${threshold:.4f}",
                'examples': [
                    {
                        'id': r.id,
                        'cost': r.cost,
                        'model': r.model,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in expensive_requests[:3]
                ]
            })
        
        # Detect sudden cost spikes
        daily_costs = defaultdict(float)
        for record in recent_records:
            date = record.timestamp.date()
            daily_costs[date] += record.cost
        
        if len(daily_costs) > 1:
            daily_values = list(daily_costs.values())
            mean_daily = statistics.mean(daily_values)
            max_daily = max(daily_values)
            
            if max_daily > mean_daily * 2:
                anomalies.append({
                    'type': 'cost_spike',
                    'severity': 'high',
                    'description': f"Daily cost spike detected: ${max_daily:.2f} vs avg ${mean_daily:.2f}",
                    'max_daily_cost': max_daily,
                    'average_daily_cost': mean_daily
                })
        
        # Detect high error rates (wasteful spending)
        error_rate = sum(1 for r in recent_records if not r.success) / len(recent_records)
        if error_rate > 0.1:  # More than 10% errors
            wasted_cost = sum(r.cost for r in recent_records if not r.success)
            anomalies.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'error_rate': error_rate,
                'wasted_cost': wasted_cost,
                'description': f"High error rate: {error_rate*100:.1f}% (${wasted_cost:.2f} wasted)"
            })
        
        return anomalies


class AdvancedCostAnalytics:
    """
    Main advanced cost analytics system.
    
    Provides comprehensive cost analysis, optimization, and forecasting
    capabilities beyond basic cost tracking.
    """
    
    def __init__(self, cost_tracker: CostTracker):
        """
        Initialize advanced cost analytics.
        
        Args:
            cost_tracker: Cost tracker instance
        """
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger("advanced_cost_analytics")
        
        # Sub-systems
        self.optimizer = CostOptimizer(cost_tracker)
        self.roi_calculator = ROICalculator()
        self.budget_planner = BudgetPlanner(cost_tracker)
        self.anomaly_detector = CostAnomalyDetector(cost_tracker)
    
    def get_detailed_breakdown(self,
                              category: CostCategory,
                              time_range: Optional[timedelta] = None) -> CostBreakdown:
        """
        Get detailed cost breakdown for a category.
        
        Args:
            category: Category to break down
            time_range: Optional time range filter
            
        Returns:
            Cost breakdown
        """
        cutoff = None
        if time_range:
            cutoff = datetime.now(timezone.utc) - time_range
        
        with self.cost_tracker.lock:
            records = self.cost_tracker.usage_records
            
            if cutoff:
                records = [r for r in records if r.timestamp >= cutoff]
            
            total_cost = sum(r.cost for r in records)
            items = defaultdict(float)
            
            # Group by category
            if category == CostCategory.MODEL_USAGE:
                for r in records:
                    items[r.model] += r.cost
            elif category == CostCategory.PROFILE:
                for r in records:
                    items[r.profile_id] += r.cost
            elif category == CostCategory.SCENARIO:
                for r in records:
                    scenario = r.session_id  # Simplified
                    items[scenario] += r.cost
            elif category == CostCategory.PHASE:
                for r in records:
                    items[r.task_type] += r.cost
            elif category == CostCategory.TIME_PERIOD:
                for r in records:
                    date = r.timestamp.date().isoformat()
                    items[date] += r.cost
            
            category_total = sum(items.values())
            percentage = (category_total / total_cost * 100) if total_cost > 0 else 0
            
            time_range_tuple = None
            if records:
                time_range_tuple = (
                    min(r.timestamp for r in records),
                    max(r.timestamp for r in records)
                )
            
            return CostBreakdown(
                category=category,
                items=dict(items),
                total_cost=category_total,
                percentage_of_total=percentage,
                time_range=time_range_tuple
            )
    
    def generate_comprehensive_report(self,
                                     session_id: Optional[str] = None,
                                     time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Generate comprehensive cost analysis report.
        
        Args:
            session_id: Optional session filter
            time_range: Optional time range filter
            
        Returns:
            Comprehensive cost report
        """
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'session_id': session_id,
            'time_range_days': time_range.days if time_range else None
        }
        
        # Basic statistics
        if session_id:
            report['total_cost'] = self.cost_tracker.get_session_cost(session_id)
            report['tokens'] = self.cost_tracker.get_session_tokens(session_id)
        else:
            stats = self.cost_tracker.get_statistics()
            report['global_stats'] = stats
        
        # Breakdowns
        report['breakdowns'] = {}
        for category in CostCategory:
            breakdown = self.get_detailed_breakdown(category, time_range)
            report['breakdowns'][category.value] = breakdown.to_dict()
        
        # Optimization opportunities
        report['optimization_opportunities'] = [
            o.to_dict() for o in self.optimizer.identify_opportunities(session_id, time_range)
        ]
        
        # Anomalies
        if not session_id:  # Only for global analysis
            report['anomalies'] = self.anomaly_detector.detect_anomalies(
                time_range or timedelta(days=7)
            )
        
        return report