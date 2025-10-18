"""
ATS MAFIA Framework Analytics API Endpoints

This module provides REST API endpoints for accessing all analytics functionality
including performance metrics, cost analysis, progress tracking, and reporting.
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from flask import Flask, request, jsonify, Response
from functools import wraps

from ..core.performance_metrics import PerformanceMetricsEngine, MetricType
from ..core.training_effectiveness import TrainingEffectivenessTracker
from ..core.advanced_cost_analytics import AdvancedCostAnalytics, CostCategory
from ..core.progress_tracker import ProgressTracker
from ..core.reporting_engine import ReportingEngine, ReportType, ReportFormat
from ..core.analytics_aggregator import AnalyticsAggregator


# Initialize logger
logger = logging.getLogger("analytics_api")


def create_analytics_api(
    performance_engine: PerformanceMetricsEngine,
    effectiveness_tracker: TrainingEffectivenessTracker,
    cost_analytics: AdvancedCostAnalytics,
    progress_tracker: ProgressTracker,
    reporting_engine: ReportingEngine,
    analytics_aggregator: AnalyticsAggregator
) -> Flask:
    """
    Create Flask app with analytics API endpoints.
    
    Args:
        performance_engine: Performance metrics engine
        effectiveness_tracker: Training effectiveness tracker
        cost_analytics: Advanced cost analytics
        progress_tracker: Progress tracker
        reporting_engine: Reporting engine
        analytics_aggregator: Analytics aggregator
        
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    
    # Error handler decorator
    def handle_errors(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"API error: {e}", exc_info=True)
                return jsonify({'error': 'Internal server error'}), 500
        return decorated_function
    
    # ========== Operator Performance Endpoints ==========
    
    @app.route('/api/analytics/operator/<operator_id>/performance', methods=['GET'])
    @handle_errors
    def get_operator_performance(operator_id: str):
        """Get comprehensive performance metrics for an operator."""
        time_range_days = request.args.get('time_range_days', type=int)
        time_range = timedelta(days=time_range_days) if time_range_days else None
        
        profile = performance_engine.get_operator_profile(operator_id)
        if not profile:
            return jsonify({'error': 'Operator not found'}), 404
        
        analysis = performance_engine.analyze_operator_performance(operator_id)
        
        return jsonify({
            'operator_id': operator_id,
            'profile': profile.to_dict(),
            'analysis': analysis
        })
    
    @app.route('/api/analytics/operator/<operator_id>/progress', methods=['GET'])
    @handle_errors
    def get_operator_progress(operator_id: str):
        """Get progress and achievements for an operator."""
        profile = performance_engine.get_operator_profile(operator_id)
        if not profile:
            return jsonify({'error': 'Operator not found'}), 404
        
        operator_data = {
            'total_sessions': profile.total_sessions,
            'total_hours': profile.total_hours,
            'skills': {k: v.to_dict() for k, v in profile.skills.items()},
            'certifications': profile.certifications,
            'total_xp': progress_tracker.get_operator_xp(operator_id)
        }
        
        summary = progress_tracker.get_operator_summary(operator_id, operator_data)
        achievements = [a.to_dict() for a in progress_tracker.get_operator_achievements(operator_id)]
        
        # Get progress path status
        path_statuses = {}
        for path_id in progress_tracker.progress_paths.keys():
            path_statuses[path_id] = progress_tracker.get_progress_path_status(
                operator_id, path_id, operator_data
            )
        
        return jsonify({
            'operator_id': operator_id,
            'summary': summary,
            'achievements': achievements,
            'progress_paths': path_statuses
        })
    
    @app.route('/api/analytics/operator/<operator_id>/recommendations', methods=['GET'])
    @handle_errors
    def get_operator_recommendations(operator_id: str):
        """Get AI-driven training recommendations for an operator."""
        profile = performance_engine.get_operator_profile(operator_id)
        if not profile:
            return jsonify({'error': 'Operator not found'}), 404
        
        recent_sessions = performance_engine.get_operator_sessions(operator_id, limit=20)
        target_role = request.args.get('target_role')
        
        recommendations = effectiveness_tracker.generate_recommendations(
            operator_id, profile, recent_sessions, target_role
        )
        
        return jsonify({
            'operator_id': operator_id,
            'recommendations': [r.to_dict() for r in recommendations]
        })
    
    @app.route('/api/analytics/operator/<operator_id>/skill-gaps', methods=['GET'])
    @handle_errors
    def get_operator_skill_gaps(operator_id: str):
        """Get identified skill gaps for an operator."""
        profile = performance_engine.get_operator_profile(operator_id)
        if not profile:
            return jsonify({'error': 'Operator not found'}), 404
        
        target_role = request.args.get('target_role')
        gaps = effectiveness_tracker.get_skill_gaps(profile, target_role)
        
        return jsonify({
            'operator_id': operator_id,
            'target_role': target_role,
            'skill_gaps': [g.to_dict() for g in gaps]
        })
    
    # ========== Session Analysis Endpoints ==========
    
    @app.route('/api/analytics/session/<session_id>/analysis', methods=['GET'])
    @handle_errors
    def get_session_analysis(session_id: str):
        """Get detailed analysis for a training session."""
        session = performance_engine.session_performances.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'session_data': session.to_dict(),
            'metrics': {
                'completion_rate': session.get_completion_rate(),
                'time_efficiency': session.get_time_efficiency(),
                'cost_efficiency': session.get_cost_efficiency()
            }
        })
    
    # ========== Cost Analysis Endpoints ==========
    
    @app.route('/api/analytics/cost/breakdown', methods=['GET'])
    @handle_errors
    def get_cost_breakdown():
        """Get detailed cost breakdown."""
        category = request.args.get('category', 'model_usage')
        time_range_days = request.args.get('time_range_days', type=int)
        
        time_range = timedelta(days=time_range_days) if time_range_days else None
        cost_category = CostCategory(category)
        
        breakdown = cost_analytics.get_detailed_breakdown(cost_category, time_range)
        
        return jsonify(breakdown.to_dict())
    
    @app.route('/api/analytics/cost/optimization', methods=['GET'])
    @handle_errors
    def get_cost_optimization():
        """Get cost optimization recommendations."""
        session_id = request.args.get('session_id')
        time_range_days = request.args.get('time_range_days', type=int)
        
        time_range = timedelta(days=time_range_days) if time_range_days else None
        
        opportunities = cost_analytics.optimizer.identify_opportunities(
            session_id=session_id,
            time_range=time_range
        )
        
        impact = cost_analytics.optimizer.calculate_optimization_impact(opportunities)
        
        return jsonify({
            'opportunities': [o.to_dict() for o in opportunities],
            'impact_analysis': impact
        })
    
    @app.route('/api/analytics/cost/summary', methods=['GET'])
    @handle_errors
    def get_cost_summary():
        """Get cost summary report."""
        session_id = request.args.get('session_id')
        time_range_days = request.args.get('time_range_days', type=int)
        
        time_range = timedelta(days=time_range_days) if time_range_days else None
        
        report = cost_analytics.generate_comprehensive_report(
            session_id=session_id,
            time_range=time_range
        )
        
        return jsonify(report)
    
    # ========== Trend Analysis Endpoints ==========
    
    @app.route('/api/analytics/trends', methods=['GET'])
    @handle_errors
    def get_trends():
        """Get performance and cost trends."""
        operator_id = request.args.get('operator_id')
        period_days = request.args.get('period_days', 30, type=int)
        
        performance_trend = analytics_aggregator.trend_calculator.calculate_performance_trend(
            operator_id=operator_id,
            period_days=period_days
        )
        
        cost_trend = analytics_aggregator.trend_calculator.calculate_cost_trend(
            period_days=period_days
        )
        
        return jsonify({
            'performance_trend': performance_trend,
            'cost_trend': cost_trend,
            'period_days': period_days
        })
    
    # ========== Leaderboard Endpoints ==========
    
    @app.route('/api/analytics/leaderboard', methods=['GET'])
    @handle_errors
    def get_leaderboard():
        """Get leaderboards."""
        board_type = request.args.get('type', 'xp')
        limit = request.args.get('limit', 10, type=int)
        
        if board_type == 'xp':
            leaderboard = analytics_aggregator.leaderboard_manager.get_xp_leaderboard(limit)
        elif board_type == 'activity':
            leaderboard = analytics_aggregator.leaderboard_manager.get_activity_leaderboard(limit)
        elif board_type == 'skill':
            skill_name = request.args.get('skill_name')
            if not skill_name:
                return jsonify({'error': 'skill_name required for skill leaderboard'}), 400
            leaderboard = analytics_aggregator.leaderboard_manager.get_skill_leaderboard(
                skill_name, limit
            )
        else:
            return jsonify({'error': f'Invalid leaderboard type: {board_type}'}), 400
        
        return jsonify({
            'type': board_type,
            'entries': leaderboard
        })
    
    # ========== Team Performance Endpoints ==========
    
    @app.route('/api/analytics/team/performance', methods=['GET'])
    @handle_errors
    def get_team_performance():
        """Get aggregate team performance metrics."""
        # Get all operator IDs or filter by team
        operator_ids = list(performance_engine.operator_profiles.keys())
        
        if not operator_ids:
            return jsonify({'error': 'No operators found'}), 404
        
        # Generate team report
        report = reporting_engine.generate_report(
            ReportType.TEAM_PERFORMANCE,
            operator_ids=operator_ids
        )
        
        return jsonify(report.data)
    
    # ========== Report Generation Endpoints ==========
    
    @app.route('/api/analytics/reports/generate', methods=['POST'])
    @handle_errors
    def generate_report():
        """Generate a custom report."""
        data = request.get_json()
        
        if not data or 'report_type' not in data:
            return jsonify({'error': 'report_type required'}), 400
        
        report_type = ReportType(data['report_type'])
        params = data.get('parameters', {})
        
        report = reporting_engine.generate_report(report_type, **params)
        
        return jsonify({
            'report_id': report.id,
            'report_type': report.report_type.value,
            'title': report.title,
            'generated_at': report.generated_at.isoformat()
        })
    
    @app.route('/api/analytics/reports/<report_id>', methods=['GET'])
    @handle_errors
    def get_report(report_id: str):
        """Get a generated report."""
        report = reporting_engine.get_report(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify(report.to_dict())
    
    @app.route('/api/analytics/reports/<report_id>/download', methods=['GET'])
    @handle_errors
    def download_report(report_id: str):
        """Download a report in specified format."""
        format_str = request.args.get('format', 'json')
        
        try:
            report_format = ReportFormat(format_str)
        except ValueError:
            return jsonify({'error': f'Invalid format: {format_str}'}), 400
        
        content = reporting_engine.export_report(report_id, report_format)
        
        # Set appropriate content type
        content_types = {
            ReportFormat.JSON: 'application/json',
            ReportFormat.CSV: 'text/csv',
            ReportFormat.HTML: 'text/html',
            ReportFormat.MARKDOWN: 'text/markdown'
        }
        
        content_type = content_types.get(report_format, 'text/plain')
        
        return Response(
            content,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename=report_{report_id}.{format_str}'
            }
        )
    
    @app.route('/api/analytics/reports', methods=['GET'])
    @handle_errors
    def list_reports():
        """List all generated reports."""
        report_type = request.args.get('report_type')
        
        filter_type = ReportType(report_type) if report_type else None
        reports = reporting_engine.list_reports(filter_type)
        
        return jsonify({
            'reports': reports,
            'count': len(reports)
        })
    
    # ========== Dashboard Endpoints ==========
    
    @app.route('/api/analytics/dashboard', methods=['GET'])
    @handle_errors
    def get_dashboard():
        """Get complete dashboard data."""
        dashboard_data = analytics_aggregator.get_dashboard_data()
        return jsonify(dashboard_data)
    
    @app.route('/api/analytics/dashboard/refresh', methods=['POST'])
    @handle_errors
    def refresh_dashboard():
        """Refresh dashboard cache."""
        analytics_aggregator.refresh_cache()
        return jsonify({'status': 'success', 'message': 'Dashboard cache refreshed'})
    
    # ========== Alert Endpoints ==========
    
    @app.route('/api/analytics/alerts', methods=['GET'])
    @handle_errors
    def get_alerts():
        """Get active alerts."""
        priority = request.args.get('priority')
        operator_id = request.args.get('operator_id')
        
        from ..core.analytics_aggregator import AlertPriority
        priority_filter = AlertPriority(priority) if priority else None
        
        alerts = analytics_aggregator.alert_manager.get_active_alerts(
            priority=priority_filter,
            operator_id=operator_id
        )
        
        return jsonify({
            'alerts': [a.to_dict() for a in alerts],
            'count': len(alerts)
        })
    
    @app.route('/api/analytics/alerts/<alert_id>/acknowledge', methods=['POST'])
    @handle_errors
    def acknowledge_alert(alert_id: str):
        """Acknowledge an alert."""
        success = analytics_aggregator.alert_manager.acknowledge_alert(alert_id)
        
        if success:
            return jsonify({'status': 'success', 'alert_id': alert_id})
        else:
            return jsonify({'error': 'Alert not found'}), 404
    
    # ========== Goals Endpoints ==========
    
    @app.route('/api/analytics/operator/<operator_id>/goals', methods=['GET'])
    @handle_errors
    def get_operator_goals(operator_id: str):
        """Get goals for an operator."""
        include_completed = request.args.get('include_completed', 'true').lower() == 'true'
        
        goals = progress_tracker.goal_tracker.get_operator_goals(
            operator_id,
            include_completed=include_completed
        )
        
        return jsonify({
            'operator_id': operator_id,
            'goals': [g.to_dict() for g in goals],
            'count': len(goals)
        })
    
    @app.route('/api/analytics/operator/<operator_id>/goals', methods=['POST'])
    @handle_errors
    def create_operator_goal(operator_id: str):
        """Create a new goal for an operator."""
        data = request.get_json()
        
        if not data or 'name' not in data or 'target_value' not in data:
            return jsonify({'error': 'name and target_value required'}), 400
        
        goal = progress_tracker.goal_tracker.create_goal(
            operator_id=operator_id,
            name=data['name'],
            description=data.get('description', ''),
            target_value=data['target_value'],
            unit=data.get('unit', 'units'),
            deadline=None  # Could parse from data if provided
        )
        
        return jsonify(goal.to_dict()), 201
    
    # ========== Certifications Endpoints ==========
    
    @app.route('/api/analytics/certifications', methods=['GET'])
    @handle_errors
    def list_certifications():
        """List all available certifications."""
        certifications = [
            cert.to_dict()
            for cert in progress_tracker.certification_manager.certifications.values()
        ]
        
        return jsonify({
            'certifications': certifications,
            'count': len(certifications)
        })
    
    @app.route('/api/analytics/operator/<operator_id>/certifications', methods=['GET'])
    @handle_errors
    def get_operator_certifications(operator_id: str):
        """Get certifications for an operator."""
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'
        
        earned_certs = progress_tracker.certification_manager.get_operator_certifications(
            operator_id,
            include_expired=include_expired
        )
        
        return jsonify({
            'operator_id': operator_id,
            'certifications': [c.to_dict() for c in earned_certs],
            'count': len(earned_certs)
        })
    
    @app.route('/api/analytics/operator/<operator_id>/certifications/<cert_id>/eligibility', methods=['GET'])
    @handle_errors
    def check_certification_eligibility(operator_id: str, cert_id: str):
        """Check if operator is eligible for a certification."""
        profile = performance_engine.get_operator_profile(operator_id)
        if not profile:
            return jsonify({'error': 'Operator not found'}), 404
        
        operator_data = {
            'total_sessions': profile.total_sessions,
            'total_hours': profile.total_hours,
            'skills': {k: v.to_dict() for k, v in profile.skills.items()},
            'certifications': profile.certifications,
            'total_xp': progress_tracker.get_operator_xp(operator_id)
        }
        
        is_eligible, missing = progress_tracker.certification_manager.check_certification_eligibility(
            operator_id, cert_id, operator_data
        )
        
        return jsonify({
            'operator_id': operator_id,
            'certification_id': cert_id,
            'eligible': is_eligible,
            'missing_requirements': missing
        })
    
    # ========== System Health Endpoint ==========
    
    @app.route('/api/analytics/health', methods=['GET'])
    @handle_errors
    def get_system_health():
        """Get system health status."""
        return jsonify({
            'status': 'healthy',
            'components': {
                'performance_engine': 'operational',
                'cost_tracker': 'operational',
                'progress_tracker': 'operational',
                'reporting_engine': 'operational',
                'analytics_aggregator': 'operational'
            },
            'stats': {
                'total_operators': len(performance_engine.operator_profiles),
                'total_sessions': len(performance_engine.session_performances),
                'total_metrics': len(performance_engine.metrics),
                'cached_reports': len(reporting_engine.reports),
                'active_alerts': len(analytics_aggregator.alert_manager.get_active_alerts())
            }
        })
    
    return app


class AnalyticsAPI:
    """
    Wrapper class for analytics API.
    
    Provides easy initialization and management of the analytics API server.
    """
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 effectiveness_tracker: TrainingEffectivenessTracker,
                 cost_analytics: AdvancedCostAnalytics,
                 progress_tracker: ProgressTracker,
                 reporting_engine: ReportingEngine,
                 analytics_aggregator: AnalyticsAggregator):
        """
        Initialize analytics API.
        
        Args:
            performance_engine: Performance metrics engine
            effectiveness_tracker: Training effectiveness tracker
            cost_analytics: Advanced cost analytics
            progress_tracker: Progress tracker
            reporting_engine: Reporting engine
            analytics_aggregator: Analytics aggregator
        """
        self.app = create_analytics_api(
            performance_engine,
            effectiveness_tracker,
            cost_analytics,
            progress_tracker,
            reporting_engine,
            analytics_aggregator
        )
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        self.app.run(host=host, port=port, debug=debug)