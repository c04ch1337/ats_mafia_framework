"""
ATS MAFIA Framework Analytics System Integration

This module provides a unified interface for initializing and accessing all
Phase 4 analytics components. Use this as the main entry point for analytics.
"""

import logging
from typing import Optional
from pathlib import Path

from .performance_metrics import PerformanceMetricsEngine
from .training_effectiveness import TrainingEffectivenessTracker
from .advanced_cost_analytics import AdvancedCostAnalytics
from .progress_tracker import ProgressTracker
from .reporting_engine import ReportingEngine
from .analytics_aggregator import AnalyticsAggregator
from .cost_tracker import CostTracker
from .llm_models import ModelRegistry


class AnalyticsSystem:
    """
    Unified analytics system for ATS MAFIA Framework.
    
    Provides a single initialization point and unified access to all
    Phase 4 analytics components.
    """
    
    def __init__(self,
                 storage_path: Optional[str] = "data/analytics",
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize complete analytics system.
        
        Args:
            storage_path: Base path for analytics data storage
            cost_tracker: Optional existing cost tracker instance
        """
        self.logger = logging.getLogger("analytics_system")
        self.storage_path = Path(storage_path) if storage_path else None
        
        # Ensure storage directory exists
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize core components
        self.logger.info("Initializing analytics system...")
        
        # Performance tracking
        perf_storage = str(self.storage_path / "performance.json") if self.storage_path else None
        self.performance_engine = PerformanceMetricsEngine(storage_path=perf_storage)
        
        # Training effectiveness
        self.effectiveness_tracker = TrainingEffectivenessTracker()
        
        # Cost tracking and analytics
        if cost_tracker:
            self.cost_tracker = cost_tracker
        else:
            registry = ModelRegistry()
            cost_storage = str(self.storage_path / "costs.json") if self.storage_path else None
            self.cost_tracker = CostTracker(registry, storage_path=cost_storage)
        
        self.cost_analytics = AdvancedCostAnalytics(self.cost_tracker)
        
        # Progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Reporting
        self.reporting_engine = ReportingEngine(
            self.performance_engine,
            self.effectiveness_tracker,
            self.cost_analytics,
            self.progress_tracker
        )
        
        # Analytics aggregation
        self.analytics_aggregator = AnalyticsAggregator(
            self.performance_engine,
            self.effectiveness_tracker,
            self.cost_tracker,
            self.progress_tracker
        )
        
        self.logger.info("✓ Analytics system initialized successfully")
    
    def get_all_components(self) -> dict:
        """
        Get all analytics components.
        
        Returns:
            Dictionary with all component instances
        """
        return {
            'performance_engine': self.performance_engine,
            'effectiveness_tracker': self.effectiveness_tracker,
            'cost_tracker': self.cost_tracker,
            'cost_analytics': self.cost_analytics,
            'progress_tracker': self.progress_tracker,
            'reporting_engine': self.reporting_engine,
            'analytics_aggregator': self.analytics_aggregator
        }
    
    def create_api_app(self):
        """
        Create Flask API app for analytics.
        
        Returns:
            Flask app with analytics endpoints
        """
        try:
            from ..api.analytics_endpoints import create_analytics_api
            
            return create_analytics_api(
                self.performance_engine,
                self.effectiveness_tracker,
                self.cost_analytics,
                self.progress_tracker,
                self.reporting_engine,
                self.analytics_aggregator
            )
        except ImportError:
            self.logger.error("Flask not available. Install with: pip install flask")
            return None
    
    def get_cli_context(self) -> dict:
        """
        Get context object for CLI commands.
        
        Returns:
            Dictionary suitable for Click context
        """
        return {
            'performance_engine': self.performance_engine,
            'effectiveness_tracker': self.effectiveness_tracker,
            'cost_analytics': self.cost_analytics,
            'progress_tracker': self.progress_tracker,
            'reporting_engine': self.reporting_engine,
            'analytics_aggregator': self.analytics_aggregator
        }
    
    def health_check(self) -> dict:
        """
        Perform health check on all components.
        
        Returns:
            Dictionary with health status
        """
        health = {
            'overall_status': 'healthy',
            'components': {},
            'stats': {}
        }
        
        # Check each component
        try:
            health['components']['performance_engine'] = {
                'status': 'operational',
                'operators': len(self.performance_engine.operator_profiles),
                'sessions': len(self.performance_engine.session_performances),
                'metrics': len(self.performance_engine.metrics)
            }
        except Exception as e:
            health['components']['performance_engine'] = {
                'status': 'error',
                'error': str(e)
            }
            health['overall_status'] = 'degraded'
        
        try:
            health['components']['cost_tracker'] = {
                'status': 'operational',
                'total_cost': self.cost_tracker.stats['total_cost'],
                'requests': self.cost_tracker.stats['total_requests']
            }
        except Exception as e:
            health['components']['cost_tracker'] = {
                'status': 'error',
                'error': str(e)
            }
            health['overall_status'] = 'degraded'
        
        try:
            health['components']['progress_tracker'] = {
                'status': 'operational',
                'milestones': len(self.progress_tracker.milestones),
                'certifications': len(self.progress_tracker.certification_manager.certifications)
            }
        except Exception as e:
            health['components']['progress_tracker'] = {
                'status': 'error',
                'error': str(e)
            }
            health['overall_status'] = 'degraded'
        
        try:
            health['components']['reporting_engine'] = {
                'status': 'operational',
                'reports': len(self.reporting_engine.reports)
            }
        except Exception as e:
            health['components']['reporting_engine'] = {
                'status': 'error',
                'error': str(e)
            }
            health['overall_status'] = 'degraded'
        
        return health


# Global analytics system instance
_global_analytics_system: Optional[AnalyticsSystem] = None


def initialize_analytics_system(
    storage_path: str = "data/analytics",
    cost_tracker: Optional[CostTracker] = None
) -> AnalyticsSystem:
    """
    Initialize the global analytics system.
    
    Args:
        storage_path: Base path for analytics data storage
        cost_tracker: Optional existing cost tracker instance
        
    Returns:
        Initialized AnalyticsSystem instance
    """
    global _global_analytics_system
    _global_analytics_system = AnalyticsSystem(storage_path, cost_tracker)
    return _global_analytics_system


def get_analytics_system() -> Optional[AnalyticsSystem]:
    """
    Get the global analytics system instance.
    
    Returns:
        Global AnalyticsSystem instance or None if not initialized
    """
    return _global_analytics_system


def shutdown_analytics_system() -> None:
    """Shutdown the global analytics system."""
    global _global_analytics_system
    if _global_analytics_system:
        # Perform any cleanup needed
        _global_analytics_system.logger.info("Analytics system shutdown")
        _global_analytics_system = None