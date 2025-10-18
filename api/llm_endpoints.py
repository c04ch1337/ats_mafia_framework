"""
ATS MAFIA Framework LLM API Endpoints

This module provides REST API endpoints for LLM model management,
cost tracking, and budget control.
"""

import logging
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify
from datetime import timedelta

from ..core.llm_models import ModelRegistry, ModelSelector, ModelTier, ModelCapability
from ..core.cost_tracker import CostTracker
from ..core.orchestrator import TrainingOrchestrator


# Create Blueprint
llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')
logger = logging.getLogger("llm_api")

# Global references (will be set during initialization)
_model_registry: Optional[ModelRegistry] = None
_model_selector: Optional[ModelSelector] = None
_cost_tracker: Optional[CostTracker] = None
_orchestrator: Optional[TrainingOrchestrator] = None


def initialize_llm_api(orchestrator: TrainingOrchestrator) -> None:
    """
    Initialize the LLM API with required components.
    
    Args:
        orchestrator: Training orchestrator instance
    """
    global _model_registry, _model_selector, _cost_tracker, _orchestrator
    
    _orchestrator = orchestrator
    _model_registry = orchestrator.get_model_registry()
    _model_selector = orchestrator.model_selector
    _cost_tracker = orchestrator.get_cost_tracker()
    
    logger.info("LLM API initialized")


def _check_initialized() -> bool:
    """Check if API components are initialized."""
    return all([_model_registry, _model_selector, _cost_tracker, _orchestrator])


@llm_bp.route('/models', methods=['GET'])
def list_models():
    """
    List available LLM models with optional filtering.
    
    Query Parameters:
        provider (str, optional): Filter by provider
        tier (str, optional): Filter by tier (ENTRY, STANDARD, ADVANCED, PREMIUM)
        capability (str, optional): Filter by capability
        max_cost (float, optional): Maximum cost per 1k input tokens
    
    Returns:
        JSON response with list of models
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        # Get query parameters
        provider = request.args.get('provider')
        tier_str = request.args.get('tier')
        capability_str = request.args.get('capability')
        max_cost = request.args.get('max_cost', type=float)
        
        # Parse tier and capability
        tier = ModelTier(tier_str) if tier_str else None
        capability = ModelCapability(capability_str) if capability_str else None
        
        # Get models
        models = _model_registry.list_models(
            provider=provider,
            tier=tier,
            capability=capability,
            max_cost_per_1k=max_cost
        )
        
        return jsonify({
            'success': True,
            'count': len(models),
            'models': [model.to_dict() for model in models]
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/models/<provider>/<model_name>', methods=['GET'])
def get_model(provider: str, model_name: str):
    """
    Get detailed information about a specific model.
    
    Args:
        provider: Model provider
        model_name: Model name
    
    Returns:
        JSON response with model details
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        model = _model_registry.get_model(provider, model_name)
        
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        # Get usage statistics if available
        model_stats = _cost_tracker.get_model_statistics(model.get_full_name())
        
        return jsonify({
            'success': True,
            'model': model.to_dict(),
            'usage_statistics': model_stats if model_stats else None
        })
        
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/models/recommend', methods=['POST'])
def recommend_models():
    """
    Get model recommendations for a task.
    
    Request Body:
        {
            "task_type": str (required) - Type of task
            "max_cost_per_request": float (optional) - Maximum cost per request
            "preferred_tier": str (optional) - Preferred tier
            "required_capabilities": list (optional) - Required capabilities
        }
    
    Returns:
        JSON response with recommended models
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        data = request.get_json()
        
        if not data or 'task_type' not in data:
            return jsonify({'error': 'task_type is required'}), 400
        
        task_type = data['task_type']
        max_cost = data.get('max_cost_per_request')
        tier_str = data.get('preferred_tier')
        capabilities_str = data.get('required_capabilities', [])
        
        # Parse tier and capabilities
        tier = ModelTier(tier_str) if tier_str else None
        capabilities = [ModelCapability(cap) for cap in capabilities_str] if capabilities_str else None
        
        # Get recommended models
        recommended = _model_registry.get_recommended_models(
            task_type=task_type,
            tier=tier,
            max_cost_per_request=max_cost
        )
        
        # Filter by capabilities if specified
        if capabilities:
            recommended = [
                m for m in recommended
                if all(cap in m.capabilities for cap in capabilities)
            ]
        
        return jsonify({
            'success': True,
            'task_type': task_type,
            'count': len(recommended),
            'recommendations': [model.to_dict() for model in recommended]
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error recommending models: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/costs/session/<session_id>', methods=['GET'])
def get_session_costs(session_id: str):
    """
    Get cost information for a specific session.
    
    Args:
        session_id: Training session ID
    
    Returns:
        JSON response with session cost details
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        cost_info = _orchestrator.get_session_llm_costs(session_id)
        
        # Get optimization recommendations
        recommendations = _cost_tracker.get_optimization_recommendations(session_id)
        cost_info['optimization_recommendations'] = recommendations
        
        return jsonify({
            'success': True,
            **cost_info
        })
        
    except Exception as e:
        logger.error(f"Error getting session costs: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/costs/profile/<profile_id>', methods=['GET'])
def get_profile_costs(profile_id: str):
    """
    Get cost information for a specific profile.
    
    Query Parameters:
        days (int, optional): Number of days to look back (default: 30)
    
    Args:
        profile_id: Profile ID
    
    Returns:
        JSON response with profile cost details
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        days = request.args.get('days', default=30, type=int)
        time_range = timedelta(days=days)
        
        total_cost = _cost_tracker.get_profile_cost(profile_id, time_range)
        breakdown = _cost_tracker.get_cost_breakdown(
            profile_id=profile_id,
            time_range=time_range
        )
        
        return jsonify({
            'success': True,
            'profile_id': profile_id,
            'time_range_days': days,
            'total_cost': total_cost,
            'breakdown_by_model': breakdown
        })
        
    except Exception as e:
        logger.error(f"Error getting profile costs: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/costs/total', methods=['GET'])
def get_total_costs():
    """
    Get total cost information and analytics.
    
    Query Parameters:
        days (int, optional): Number of days to look back for breakdown
    
    Returns:
        JSON response with total costs and analytics
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        days = request.args.get('days', type=int)
        time_range = timedelta(days=days) if days else None
        
        # Get overall statistics
        stats = _cost_tracker.get_statistics()
        
        # Get cost breakdown
        breakdown = _cost_tracker.get_cost_breakdown(time_range=time_range)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'breakdown_by_model': breakdown,
            'time_range_days': days if days else 'all_time'
        })
        
    except Exception as e:
        logger.error(f"Error getting total costs: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/costs/model/<provider>/<model_name>', methods=['GET'])
def get_model_costs(provider: str, model_name: str):
    """
    Get cost and usage statistics for a specific model.
    
    Args:
        provider: Model provider
        model_name: Model name
    
    Returns:
        JSON response with model statistics
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        full_name = f"{provider}/{model_name}"
        stats = _cost_tracker.get_model_statistics(full_name)
        
        if not stats:
            return jsonify({'error': 'No usage data for this model'}), 404
        
        return jsonify({
            'success': True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Error getting model costs: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/budget/session/<session_id>', methods=['POST'])
def set_session_budget(session_id: str):
    """
    Set or update budget limit for a session.
    
    Request Body:
        {
            "budget": float (required) - Budget limit in USD
            "alert_thresholds": list (optional) - Alert thresholds (e.g., [0.75, 0.90, 1.0])
        }
    
    Args:
        session_id: Training session ID
    
    Returns:
        JSON response with confirmation
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        data = request.get_json()
        
        if not data or 'budget' not in data:
            return jsonify({'error': 'budget is required'}), 400
        
        budget = float(data['budget'])
        if budget <= 0:
            return jsonify({'error': 'budget must be positive'}), 400
        
        # Set budget
        _cost_tracker.set_session_budget(session_id, budget)
        
        # Add alert thresholds if provided
        alert_thresholds = data.get('alert_thresholds', [0.75, 0.90, 1.0])
        for threshold in alert_thresholds:
            _cost_tracker.add_budget_alert(
                session_id,
                threshold,
                _orchestrator.budget_alert_callback
            )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'budget': budget,
            'alert_thresholds': alert_thresholds
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid budget value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error setting session budget: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/budget/profile/<profile_id>', methods=['POST'])
def set_profile_budget(profile_id: str):
    """
    Set or update budget limit for a profile.
    
    Request Body:
        {
            "budget": float (required) - Budget limit in USD
        }
    
    Args:
        profile_id: Profile ID
    
    Returns:
        JSON response with confirmation
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        data = request.get_json()
        
        if not data or 'budget' not in data:
            return jsonify({'error': 'budget is required'}), 400
        
        budget = float(data['budget'])
        if budget <= 0:
            return jsonify({'error': 'budget must be positive'}), 400
        
        # Set budget
        _cost_tracker.set_profile_budget(profile_id, budget)
        
        return jsonify({
            'success': True,
            'profile_id': profile_id,
            'budget': budget
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid budget value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error setting profile budget: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/budget/global', methods=['POST'])
def set_global_budget():
    """
    Set or update global budget limit.
    
    Request Body:
        {
            "budget": float (required) - Budget limit in USD
        }
    
    Returns:
        JSON response with confirmation
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        data = request.get_json()
        
        if not data or 'budget' not in data:
            return jsonify({'error': 'budget is required'}), 400
        
        budget = float(data['budget'])
        if budget <= 0:
            return jsonify({'error': 'budget must be positive'}), 400
        
        # Set budget
        _cost_tracker.set_global_budget(budget)
        
        return jsonify({
            'success': True,
            'global_budget': budget
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid budget value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error setting global budget: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get comprehensive LLM system statistics.
    
    Returns:
        JSON response with system statistics
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        model_stats = _model_registry.get_statistics()
        cost_stats = _cost_tracker.get_statistics()
        
        return jsonify({
            'success': True,
            'model_registry': model_stats,
            'cost_tracking': cost_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@llm_bp.route('/export/usage', methods=['GET'])
def export_usage_data():
    """
    Export usage data for reporting.
    
    Query Parameters:
        session_id (str, optional): Filter by session
        profile_id (str, optional): Filter by profile
        format (str, optional): Export format ('json' or 'csv', default: 'json')
        days (int, optional): Number of days to look back
    
    Returns:
        JSON or CSV response with usage data
    """
    if not _check_initialized():
        return jsonify({'error': 'LLM API not initialized'}), 500
    
    try:
        session_id = request.args.get('session_id')
        profile_id = request.args.get('profile_id')
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', type=int)
        
        from datetime import datetime, timezone
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days) if days else None
        
        # Export data
        data = _cost_tracker.export_usage_data(
            session_id=session_id,
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )
        
        if format_type == 'csv':
            from flask import Response
            return Response(
                data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=llm_usage.csv'}
            )
        else:
            return jsonify({
                'success': True,
                'count': len(data),
                'data': data
            })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error exporting usage data: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Error handlers
@llm_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@llm_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500