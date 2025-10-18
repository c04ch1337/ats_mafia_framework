"""
Sandbox API Endpoints
REST API for Kali sandbox management and tool execution.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

from ..sandbox.kali_connector import KaliConnector, KaliConnectorError
from ..sandbox.sandbox_manager import SandboxManager
from ..sandbox.security_monitor import SecurityMonitor
from ..sandbox.network_isolation import NetworkIsolation
from ..sandbox.tool_whitelist import validate_command, get_all_approved_tools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

# Initialize sandbox components
try:
    kali_connector = KaliConnector()
    sandbox_manager = SandboxManager()
    security_monitor = SecurityMonitor()
    network_isolation = NetworkIsolation()
    logger.info("Sandbox API components initialized")
except Exception as e:
    logger.error(f"Failed to initialize sandbox components: {e}")
    kali_connector = None
    sandbox_manager = None
    security_monitor = None
    network_isolation = None


# Pydantic models for request/response
class CommandRequest(BaseModel):
    command: str
    user_id: str
    timeout: Optional[int] = 300
    container_id: Optional[str] = None


class SessionCreateRequest(BaseModel):
    session_id: str
    cpu_limit: Optional[str] = '2.0'
    memory_limit: Optional[str] = '4g'


class ToolExecutionRequest(BaseModel):
    tool_name: str
    target: str
    user_id: str
    parameters: Optional[Dict[str, any]] = None


# Status endpoints
@router.get("/status")
async def get_sandbox_status():
    """Get Kali sandbox status and health information."""
    try:
        if not kali_connector:
            return {
                "available": False,
                "error": "Sandbox system not initialized"
            }
        
        status = kali_connector.get_container_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get sandbox status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for sandbox system."""
    try:
        if not kali_connector:
            return {"healthy": False, "reason": "Not initialized"}
        
        is_healthy = kali_connector.test_connectivity()
        return {
            "healthy": is_healthy,
            "components": {
                "kali_connector": kali_connector is not None,
                "sandbox_manager": sandbox_manager is not None,
                "security_monitor": security_monitor is not None,
                "network_isolation": network_isolation is not None
            }
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}


# Session management endpoints
@router.post("/session/{session_id}/create")
async def create_session_sandbox(session_id: str, request: SessionCreateRequest):
    """Create ephemeral sandbox for specific session."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        container_id = sandbox_manager.create_ephemeral_sandbox(
            session_id=session_id,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "container_id": container_id,
            "message": "Ephemeral sandbox created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create session sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def destroy_session_sandbox(session_id: str):
    """Destroy session sandbox."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        # Find container by session ID label
        sandboxes = sandbox_manager.list_sandboxes()
        container_id = None
        
        for sandbox in sandboxes:
            if sandbox.get('session_id') == session_id:
                container_id = sandbox['id']
                break
        
        if not container_id:
            raise HTTPException(status_code=404, detail="Session sandbox not found")
        
        success = sandbox_manager.destroy_sandbox(container_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "Sandbox destroyed" if success else "Failed to destroy sandbox"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to destroy session sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Command execution endpoints
@router.post("/execute")
async def execute_command(request: CommandRequest):
    """Execute validated command in sandbox."""
    try:
        if not kali_connector or not security_monitor:
            raise HTTPException(status_code=503, detail="Sandbox system not available")
        
        # Security monitoring
        monitor_result = security_monitor.monitor_command(
            user_id=request.user_id,
            command=request.command,
            container_id=request.container_id or 'default'
        )
        
        if not monitor_result['allowed']:
            raise HTTPException(
                status_code=403,
                detail=f"Command blocked: {monitor_result['reason']}"
            )
        
        # Validate command
        is_valid, reason = validate_command(request.command)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid command: {reason}")
        
        # Execute command
        result = kali_connector.execute_command(
            command=request.command,
            timeout=request.timeout
        )
        
        return {
            "success": result['success'],
            "stdout": result['stdout'],
            "stderr": result['stderr'],
            "exit_code": result['exit_code'],
            "execution_time": result['execution_time'],
            "warnings": monitor_result.get('warnings', []),
            "threat_level": monitor_result.get('threat_level', 'LOW')
        }
        
    except HTTPException:
        raise
    except KaliConnectorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Tool listing endpoints
@router.get("/tools")
async def list_available_tools():
    """List all approved security tools."""
    try:
        approved_tools = get_all_approved_tools()
        
        if kali_connector:
            # Get actually installed tools
            available_tools = kali_connector.list_available_tools()
        else:
            available_tools = []
        
        return {
            "approved_tools": approved_tools,
            "available_tools": available_tools,
            "total_approved": len(approved_tools),
            "total_available": len(available_tools)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get information about specific tool."""
    try:
        if not kali_connector:
            raise HTTPException(status_code=503, detail="Sandbox not available")
        
        tool_info = kali_connector.get_tool_info(tool_name)
        return tool_info
        
    except Exception as e:
        logger.error(f"Failed to get tool info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Container metrics endpoints
@router.get("/metrics/{container_id}")
async def get_container_metrics(container_id: str):
    """Get resource usage metrics for container."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        metrics = sandbox_manager.get_sandbox_metrics(container_id)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_sandboxes():
    """List all sandbox containers."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        sandboxes = sandbox_manager.list_sandboxes()
        return {
            "sandboxes": sandboxes,
            "total": len(sandboxes)
        }
        
    except Exception as e:
        logger.error(f"Failed to list sandboxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Snapshot endpoints
@router.post("/snapshot/{container_id}")
async def create_snapshot(container_id: str, snapshot_name: Optional[str] = None):
    """Create snapshot of sandbox state."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        snapshot_id = sandbox_manager.snapshot_sandbox(container_id, snapshot_name)
        
        return {
            "success": True,
            "container_id": container_id,
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name
        }
        
    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{snapshot_id}")
async def restore_from_snapshot(snapshot_id: str, session_id: str):
    """Restore sandbox from snapshot."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        container_id = sandbox_manager.restore_sandbox(snapshot_id, session_id)
        
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "container_id": container_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to restore snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security endpoints
@router.get("/security/audit-log")
async def get_audit_log(user_id: Optional[str] = None, limit: int = 100):
    """Get security audit log."""
    try:
        if not security_monitor:
            raise HTTPException(status_code=503, detail="Security monitor not available")
        
        logs = security_monitor.get_audit_log(user_id=user_id, limit=limit)
        
        return {
            "logs": logs,
            "total": len(logs),
            "user_filter": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/report")
async def get_security_report():
    """Get security statistics and report."""
    try:
        if not security_monitor:
            raise HTTPException(status_code=503, detail="Security monitor not available")
        
        report = security_monitor.get_security_report()
        return report
        
    except Exception as e:
        logger.error(f"Failed to get security report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/unblock/{user_id}")
async def unblock_user(user_id: str):
    """Unblock a previously blocked user."""
    try:
        if not security_monitor:
            raise HTTPException(status_code=503, detail="Security monitor not available")
        
        success = security_monitor.unblock_user(user_id)
        
        return {
            "success": success,
            "user_id": user_id,
            "message": "User unblocked" if success else "User was not blocked"
        }
        
    except Exception as e:
        logger.error(f"Failed to unblock user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Network endpoints
@router.get("/network/info/{network_name}")
async def get_network_info(network_name: str):
    """Get information about a network."""
    try:
        if not network_isolation:
            raise HTTPException(status_code=503, detail="Network isolation not available")
        
        info = network_isolation.get_network_info(network_name)
        return info
        
    except Exception as e:
        logger.error(f"Failed to get network info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/list")
async def list_networks():
    """List all ATS MAFIA networks."""
    try:
        if not network_isolation:
            raise HTTPException(status_code=503, detail="Network isolation not available")
        
        networks = network_isolation.list_networks()
        
        return {
            "networks": networks,
            "total": len(networks)
        }
        
    except Exception as e:
        logger.error(f"Failed to list networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Maintenance endpoints
@router.post("/cleanup")
async def cleanup_old_sandboxes(max_age_hours: int = 24):
    """Clean up old ephemeral sandboxes."""
    try:
        if not sandbox_manager:
            raise HTTPException(status_code=503, detail="Sandbox manager not available")
        
        count = sandbox_manager.cleanup_old_sandboxes(max_age_hours=max_age_hours)
        
        return {
            "success": True,
            "cleaned_up": count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup sandboxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']