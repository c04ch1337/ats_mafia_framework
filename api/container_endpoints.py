"""
Container Lifecycle Management API Endpoints

Provides REST API for managing container orchestration, health monitoring,
and profile-based container preparation.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from datetime import datetime

from ..core.container_orchestrator import HybridContainerOrchestrator, PoolTier, ContainerState
from ..config.container_pools import get_pool_config, reload_pool_config

logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator: Optional[HybridContainerOrchestrator] = None

def get_container_orchestrator() -> HybridContainerOrchestrator:
    """Get or initialize container orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = HybridContainerOrchestrator()
            logger.info("Container orchestrator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    return _orchestrator

# Pydantic models for request/response
class ContainerStatus(str, Enum):
    """Container status enum."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class PoolType(str, Enum):
    """Container pool types."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

class PrepareContainersRequest(BaseModel):
    """Request to prepare containers for profile."""
    profile_id: str = Field(..., description="Profile identifier")
    force_restart: bool = Field(False, description="Force restart if already running")

class PrepareContainersResponse(BaseModel):
    """Response from container preparation."""
    profile_id: str
    containers: Dict[str, Dict[str, Any]]
    all_ready: bool
    estimated_wait_seconds: int
    timestamp: datetime

class ContainerStatusResponse(BaseModel):
    """Container status information."""
    container_name: str
    status: ContainerStatus
    pool: PoolType
    healthy: bool
    uptime_seconds: Optional[float] = None
    last_used: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None

class ProfileContainersResponse(BaseModel):
    """Containers status for profile."""
    profile_id: str
    containers: Dict[str, ContainerStatusResponse]
    ready: bool
    timestamp: datetime

class PoolStatusResponse(BaseModel):
    """Pool status information."""
    pool_type: PoolType
    description: str
    containers: List[str]
    active_count: int
    total_count: int
    health_check_interval: int
    ttl_seconds: Optional[int] = None

class OrchestratorMetricsResponse(BaseModel):
    """Orchestrator performance metrics."""
    total_starts: int
    total_stops: int
    total_failures: int
    average_startup_time: float
    active_containers: int
    pool_distribution: Dict[str, int]
    timestamp: datetime

class StartContainerRequest(BaseModel):
    """Request to start container."""
    container_name: str
    wait_for_health: bool = True
    timeout: int = 120

class StopContainerRequest(BaseModel):
    """Request to stop container."""
    container_name: str
    force: bool = False
    timeout: int = 30

# Create router
router = APIRouter(prefix="/api/v1/containers", tags=["containers"])

# Dependency to get orchestrator
async def get_orchestrator() -> HybridContainerOrchestrator:
    """Get container orchestrator instance."""
    orchestrator = get_container_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Container orchestrator not initialized")
    return orchestrator


@router.post("/prepare", response_model=PrepareContainersResponse)
async def prepare_containers_for_profile(
    request: PrepareContainersRequest,
    background_tasks: BackgroundTasks,
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Prepare containers needed for a profile.
    
    Starts required containers in background if not already running.
    Returns immediately with status and estimated wait time.
    """
    try:
        # Get profile containers - returns Dict[str, bool]
        results = await orchestrator.prepare_for_profile(
            profile_id=request.profile_id
        )
        
        # Convert results to detailed status
        containers_status = {}
        for container_name, success in results.items():
            state = orchestrator._container_states.get(container_name)
            containers_status[container_name] = {
                'status': 'ready' if success else 'failed',
                'healthy': success,
                'estimated_time': 10 if not success else 0  # Estimate 10s startup
            }
        
        return PrepareContainersResponse(
            profile_id=request.profile_id,
            containers=containers_status,
            all_ready=all(results.values()),
            estimated_wait_seconds=max(
                (c.get('estimated_time', 0) for c in containers_status.values()),
                default=0
            ),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to prepare containers for profile {request.profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Container preparation failed: {str(e)}")


@router.get("/status/{profile_id}", response_model=ProfileContainersResponse)
async def get_profile_container_status(
    profile_id: str,
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Get status of all containers for a profile.
    
    Use this endpoint to poll for container readiness after calling /prepare.
    """
    try:
        # Get required containers for profile
        pool_config = get_pool_config()
        container_names = pool_config.get_containers_for_profile(profile_id)
        
        if not container_names:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        # Get status for each container
        containers_status = {}
        for container_name in container_names:
            state = orchestrator._container_states.get(container_name)
            
            if state:
                containers_status[container_name] = ContainerStatusResponse(
                    container_name=container_name,
                    status=ContainerStatus(state.status),
                    pool=PoolType(state.tier.value),
                    healthy=state.is_healthy(),
                    uptime_seconds=(datetime.utcnow() - state.start_time).total_seconds() if state.start_time else None,
                    last_used=state.last_used,
                    metrics=None  # Can be extended
                )
            else:
                # Determine pool from orchestrator
                pool = PoolType.COLD
                if container_name in orchestrator.HOT_POOL:
                    pool = PoolType.HOT
                elif container_name in orchestrator.WARM_POOL:
                    pool = PoolType.WARM
                
                containers_status[container_name] = ContainerStatusResponse(
                    container_name=container_name,
                    status=ContainerStatus.UNKNOWN,
                    pool=pool,
                    healthy=False
                )
        
        all_ready = all(
            c.status == ContainerStatus.RUNNING and c.healthy 
            for c in containers_status.values()
        )
        
        return ProfileContainersResponse(
            profile_id=profile_id,
            containers=containers_status,
            ready=all_ready,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get container status for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status query failed: {str(e)}")


@router.post("/start", status_code=202)
async def start_container(
    request: StartContainerRequest,
    background_tasks: BackgroundTasks,
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Start a specific container.
    
    Returns 202 Accepted and starts container in background.
    Use /status endpoint to monitor progress.
    """
    try:
        # Start in background
        background_tasks.add_task(
            orchestrator._start_container_with_retry,
            request.container_name
        )
        
        # Estimate startup time
        estimated_time = 30  # Default estimate
        pool_config = get_pool_config()
        for pool_name in ['hot', 'warm', 'cold']:
            pool = pool_config.get_pool(pool_name)
            if pool:
                for container in pool.containers:
                    if container.name == request.container_name:
                        estimated_time = container.estimated_startup_time
                        break
        
        return {
            "message": f"Container {request.container_name} is starting",
            "container_name": request.container_name,
            "wait_for_health": request.wait_for_health,
            "estimated_time": estimated_time
        }
        
    except Exception as e:
        logger.error(f"Failed to start container {request.container_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Container start failed: {str(e)}")


@router.post("/stop")
async def stop_container(
    request: StopContainerRequest,
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Stop a specific container.
    
    Gracefully stops container with configurable timeout and force option.
    """
    try:
        success = await orchestrator._stop_container(
            container_name=request.container_name,
            timeout=request.timeout
        )
        
        if success:
            return {
                "message": f"Container {request.container_name} stopped successfully",
                "container_name": request.container_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop container {request.container_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop container {request.container_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Container stop failed: {str(e)}")


@router.get("/pools/{pool_type}", response_model=PoolStatusResponse)
async def get_pool_status(
    pool_type: PoolType,
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Get status of a specific container pool (hot/warm/cold).
    """
    try:
        pool_config = get_pool_config()
        
        # Get pool configuration
        if pool_type == PoolType.HOT:
            pool = pool_config.get_hot_pool()
        elif pool_type == PoolType.WARM:
            pool = pool_config.get_warm_pool()
        else:
            pool = pool_config.get_cold_pool()
        
        if not pool:
            raise HTTPException(status_code=404, detail=f"Pool {pool_type} not found")
        
        # Get container names in pool
        container_names = [c.name for c in pool.containers]
        
        # Count active containers
        active_count = 0
        for name in container_names:
            state = orchestrator._container_states.get(name)
            if state and state.status == "running":
                active_count += 1
        
        return PoolStatusResponse(
            pool_type=pool_type,
            description=pool.description,
            containers=container_names,
            active_count=active_count,
            total_count=len(container_names),
            health_check_interval=pool.health_check_interval,
            ttl_seconds=pool.ttl_seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pool status for {pool_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Pool status query failed: {str(e)}")


@router.get("/metrics", response_model=OrchestratorMetricsResponse)
async def get_orchestrator_metrics(
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Get orchestrator performance metrics.
    
    Returns statistics about container lifecycle operations.
    """
    try:
        stats = orchestrator.get_orchestrator_stats()
        
        # Calculate pool distribution
        pool_distribution = stats.get('tier_distribution', {"hot": 0, "warm": 0, "cold": 0})
        
        return OrchestratorMetricsResponse(
            total_starts=stats['total_starts'],
            total_stops=stats['total_stops'],
            total_failures=stats['failed_starts'],
            average_startup_time=0.0,  # Can be extended with timing metrics
            active_containers=stats['running_containers'],
            pool_distribution=pool_distribution,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get orchestrator metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics query failed: {str(e)}")


@router.get("/health")
async def health_check(
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Health check endpoint for orchestrator.
    
    Returns 200 if orchestrator is operational.
    """
    try:
        # Check if orchestrator is initialized
        if not orchestrator.docker_client:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Check if cleanup task is running
        cleanup_running = orchestrator._cleanup_task and not orchestrator._cleanup_task.done()
        
        # Count active containers
        active_count = sum(
            1 for s in orchestrator._container_states.values()
            if s.status == "running"
        )
        
        return {
            "status": "healthy",
            "initialized": True,
            "cleanup_task_running": cleanup_running,
            "active_containers": active_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Orchestrator unhealthy")


@router.post("/reload-config")
async def reload_configuration(
    orchestrator: HybridContainerOrchestrator = Depends(get_orchestrator)
):
    """
    Reload container pool configuration from YAML.
    
    Use this after updating container_pools.yaml to apply changes without restart.
    """
    try:
        # Reload configuration
        reload_pool_config()
        
        # Reload in orchestrator
        orchestrator._load_pool_config()
        
        logger.info("Container pool configuration reloaded successfully")
        
        return {
            "message": "Configuration reloaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")


# Export router
__all__ = ['router', 'get_container_orchestrator']