"""
Example FastAPI Application with Container Endpoints

This example shows how to integrate the container lifecycle management endpoints
into a FastAPI application.

Usage:
    uvicorn ats_mafia_framework.api.container_app_example:app --reload --host 0.0.0.0 --port 8000

Then visit:
    - http://localhost:8000/docs - Interactive API documentation
    - http://localhost:8000/redoc - Alternative API documentation
    - http://localhost:8000/api/v1/containers/health - Health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .container_endpoints import router as container_router, get_container_orchestrator
from .profile_endpoints import router as profiles_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="ATS MAFIA Container Management API",
    description="REST API for container lifecycle management and orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
# Note: allow_credentials is False for local file:// origins and broad dev support.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include container endpoints
app.include_router(container_router)
# Include profiles endpoints
app.include_router(profiles_router)

@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator and start hot pool on application startup."""
    logger.info("Starting ATS MAFIA Container Management API...")
    
    try:
        # Get orchestrator instance (initializes if needed)
        orchestrator = get_container_orchestrator()
        
        # Initialize hot pool containers
        logger.info("Initializing hot pool containers...")
        results = await orchestrator.initialize()
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Hot pool initialization complete: {success_count}/{len(results)} containers started")
        
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        # Don't prevent app startup, but log the error
        

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown orchestrator on application shutdown."""
    logger.info("Shutting down ATS MAFIA Container Management API...")
    
    try:
        orchestrator = get_container_orchestrator()
        await orchestrator.shutdown()
        logger.info("Orchestrator shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ATS MAFIA Container Management API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/containers/health",
            "metrics": "/api/v1/containers/metrics"
        }
    }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "ats_mafia_framework.api.container_app_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )