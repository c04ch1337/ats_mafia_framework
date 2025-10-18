"""
ATT&CK Framework API Endpoints
Provides REST API access to MITRE ATT&CK data for UI components
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any, List
import logging

from ats_mafia_framework.knowledge import ATTACKFramework
from ats_mafia_framework.analytics import ATTACKNavigatorExporter


# Create Blueprint
attack_api = Blueprint('attack_api', __name__, url_prefix='/api/v1/attack')

# Initialize framework and exporter (singletons)
_attack_framework = None
_navigator_exporter = None

def get_attack_framework() -> ATTACKFramework:
    """Get or initialize ATT&CK framework singleton"""
    global _attack_framework
    if _attack_framework is None:
        _attack_framework = ATTACKFramework()
    return _attack_framework

def get_navigator_exporter() -> ATTACKNavigatorExporter:
    """Get or initialize Navigator exporter singleton"""
    global _navigator_exporter
    if _navigator_exporter is None:
        attack = get_attack_framework()
        _navigator_exporter = ATTACKNavigatorExporter(attack)
    return _navigator_exporter


@attack_api.route('/tactics', methods=['GET'])
def get_tactics():
    """
    Get all ATT&CK tactics
    
    Returns:
        JSON with tactics list
    """
    try:
        attack = get_attack_framework()
        
        tactics = [
            {
                'id': tactic_id,
                'name': tactic_data['name'],
                'shortname': tactic_data['shortname'],
                'description': tactic_data.get('description', ''),
                'url': tactic_data.get('url', '')
            }
            for tactic_id, tactic_data in attack.tactics.items()
        ]
        
        return jsonify({
            'success': True,
            'tactics': tactics,
            'count': len(tactics)
        })
    
    except Exception as e:
        logging.error(f"Error getting tactics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/techniques', methods=['GET'])
def get_techniques():
    """
    Get all ATT&CK techniques (optionally filtered by tactic)
    
    Query params:
        tactic: Filter by tactic shortname (optional)
        include_subtechniques: Include sub-techniques (default: true)
    
    Returns:
        JSON with techniques list
    """
    try:
        attack = get_attack_framework()
        
        # Get query parameters
        tactic = request.args.get('tactic')
        include_subtechniques = request.args.get('include_subtechniques', 'true').lower() == 'true'
        
        # Get techniques
        if tactic:
            techniques_list = attack.get_techniques_by_tactic(tactic)
        else:
            techniques_list = list(attack.techniques.values())
            if include_subtechniques:
                techniques_list.extend(attack.subtechniques.values())
        
        # Filter out deprecated/revoked
        techniques_list = [
            t for t in techniques_list
            if not t.get('deprecated') and not t.get('revoked')
        ]
        
        return jsonify({
            'success': True,
            'techniques': techniques_list,
            'count': len(techniques_list),
            'filter': {
                'tactic': tactic,
                'include_subtechniques': include_subtechniques
            }
        })
    
    except Exception as e:
        logging.error(f"Error getting techniques: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/technique/<technique_id>', methods=['GET'])
def get_technique(technique_id: str):
    """
    Get a specific technique by ID
    
    Args:
        technique_id: ATT&CK technique ID (e.g., T1055 or T1055.001)
    
    Returns:
        JSON with technique data
    """
    try:
        attack = get_attack_framework()
        technique = attack.get_technique(technique_id)
        
        if not technique:
            return jsonify({
                'success': False,
                'error': f'Technique {technique_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'technique': technique
        })
    
    except Exception as e:
        logging.error(f"Error getting technique {technique_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/search', methods=['GET'])
def search_techniques():
    """
    Search techniques by query string
    
    Query params:
        q: Search query (required)
        tactic: Filter by tactic (optional)
        include_subtechniques: Include sub-techniques (default: true)
    
    Returns:
        JSON with matching techniques
    """
    try:
        attack = get_attack_framework()
        
        # Get query parameters
        query = request.args.get('q', '').strip()
        tactic = request.args.get('tactic')
        include_subtechniques = request.args.get('include_subtechniques', 'true').lower() == 'true'
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query (q) is required'
            }), 400
        
        # Search techniques
        results = attack.search_techniques(query, include_subtechniques=include_subtechniques)
        
        # Filter by tactic if specified
        if tactic:
            results = [
                t for t in results
                if tactic.lower() in [tac.lower() for tac in t.get('tactics', [])]
            ]
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query,
            'filter': {
                'tactic': tactic,
                'include_subtechniques': include_subtechniques
            }
        })
    
    except Exception as e:
        logging.error(f"Error searching techniques: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/coverage', methods=['POST'])
def validate_coverage():
    """
    Validate technique coverage for a set of techniques
    
    Request body:
        {
            "technique_ids": ["T1055", "T1059", ...]
        }
    
    Returns:
        JSON with coverage analysis
    """
    try:
        attack = get_attack_framework()
        
        # Get technique IDs from request
        data = request.get_json()
        if not data or 'technique_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'technique_ids array is required in request body'
            }), 400
        
        technique_ids = data['technique_ids']
        
        if not isinstance(technique_ids, list):
            return jsonify({
                'success': False,
                'error': 'technique_ids must be an array'
            }), 400
        
        # Validate coverage
        coverage = attack.validate_technique_coverage(technique_ids)
        
        return jsonify({
            'success': True,
            'coverage': coverage
        })
    
    except Exception as e:
        logging.error(f"Error validating coverage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get ATT&CK framework statistics
    
    Returns:
        JSON with framework statistics
    """
    try:
        attack = get_attack_framework()
        stats = attack.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        logging.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@attack_api.route('/tree', methods=['GET'])
def get_technique_tree():
    """
    Get techniques organized by tactic
    
    Returns:
        JSON with technique tree structure
    """
    try:
        attack = get_attack_framework()
        tree = attack.get_technique_tree()
        
        # Convert to API-friendly format
        formatted_tree = {}
        for tactic_name, techniques in tree.items():
            # Filter out deprecated/revoked
            active_techniques = [
                t for t in techniques
                if not t.get('deprecated') and not t.get('revoked')
            ]
            formatted_tree[tactic_name] = {
                'techniques': active_techniques,
                'count': len(active_techniques)
            }
        
        return jsonify({
            'success': True,
            'tree': formatted_tree
        })
    
    except Exception as e:
        logging.error(f"Error getting technique tree: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Health check endpoint
@attack_api.route('/health', methods=['GET'])
def health_check():
    """Health check for ATT&CK API"""
    try:
        attack = get_attack_framework()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'version': attack.version,
            'techniques_loaded': len(attack.techniques),
            'tactics_loaded': len(attack.tactics)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@attack_api.route('/navigator/export', methods=['POST'])
def export_navigator_layer():
    """
    Export ATT&CK Navigator layer
    
    Request body:
        {
            "type": "profile|scenario|custom",
            "name": "Layer Name",
            "description": "Layer description",
            "technique_ids": ["T1055", ...],  // For custom
            "profile": {...},  // For profile
            "scenario": {...}  // For scenario
        }
    
    Returns:
        Navigator layer JSON file
    """
    try:
        exporter = get_navigator_exporter()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        layer_type = data.get('type', 'custom')
        
        if layer_type == 'profile':
            if 'profile' not in data:
                return jsonify({
                    'success': False,
                    'error': 'profile data is required for profile layer'
                }), 400
            
            layer = exporter.create_profile_layer(
                profile=data['profile'],
                name=data.get('name')
            )
        
        elif layer_type == 'scenario':
            if 'scenario' not in data:
                return jsonify({
                    'success': False,
                    'error': 'scenario data is required for scenario layer'
                }), 400
            
            layer = exporter.create_scenario_layer(
                scenario=data['scenario'],
                name=data.get('name')
            )
        
        elif layer_type == 'custom':
            if 'technique_ids' not in data:
                return jsonify({
                    'success': False,
                    'error': 'technique_ids array is required for custom layer'
                }), 400
            
            layer = exporter.create_custom_layer(
                technique_ids=data['technique_ids'],
                name=data.get('name', 'Custom Layer'),
                description=data.get('description', ''),
                scores=data.get('scores'),
                colors=data.get('colors')
            )
        
        else:
            return jsonify({
                'success': False,
                'error': f'Invalid layer type: {layer_type}'
            }), 400
        
        # Return layer as downloadable JSON
        from flask import Response
        import json as json_lib
        
        return Response(
            json_lib.dumps(layer, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=navigator_layer_{layer_type}.json'
            }
        )
    
    except Exception as e:
        logging.error(f"Error exporting Navigator layer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



def register_attack_api(app):
    """
    Register ATT&CK API blueprint with Flask app
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(attack_api)
    logging.info("Registered ATT&CK API endpoints at /api/v1/attack")