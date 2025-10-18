"""
ATS MAFIA API Module
Provides REST API endpoints for the framework
"""

# Flask blueprints (backward compatibility)
try:
    from .attack_api import attack_api, register_attack_api
    
    flask_exports = ['attack_api', 'register_attack_api']
except ImportError:
    # Flask not installed or other import issues
    # Gracefully handle for environments without API support
    flask_exports = []

# FastAPI routers
try:
    from .container_endpoints import router as container_router, get_container_orchestrator
    
    fastapi_exports = ['container_router', 'get_container_orchestrator']
except ImportError:
    # FastAPI not installed or other import issues
    fastapi_exports = []

__all__ = flask_exports + fastapi_exports