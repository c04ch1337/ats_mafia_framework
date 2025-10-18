"""
Container Orchestrator - Hybrid Three-Tier Pool Management
Production-grade container lifecycle management with hot/warm/cold pools.

SpaceX-level reliability with:
- Comprehensive error handling and recovery
- Async operations with proper timeout management
- Health checking and automatic retry logic
- Resource cleanup and leak prevention
- Detailed logging and monitoring
"""

import asyncio
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

import docker
from docker.errors import DockerException, NotFound, APIError

from ..sandbox.container_manager import ContainerManager
from ..config.container_pools import get_pool_config, ContainerPoolConfig

logger = logging.getLogger(__name__)


class PoolTier(Enum):
    """Container pool tiers with different startup/availability characteristics."""
    HOT = "hot"      # Always running, instant availability
    WARM = "warm"    # Started on-demand, kept alive with TTL
    COLD = "cold"    # Started only when explicitly needed


@dataclass
class ContainerState:
    """Tracks the state and metadata of a managed container."""
    name: str
    tier: PoolTier
    status: str = "stopped"
    last_used: Optional[datetime] = None
    start_time: Optional[datetime] = None
    health_check_count: int = 0
    failed_health_checks: int = 0
    restart_count: int = 0
    
    def mark_used(self) -> None:
        """Mark container as recently used."""
        self.last_used = datetime.utcnow()
    
    def is_idle(self, ttl_minutes: int) -> bool:
        """Check if container has been idle beyond TTL."""
        if not self.last_used:
            return False
        idle_time = datetime.utcnow() - self.last_used
        return idle_time > timedelta(minutes=ttl_minutes)
    
    def is_healthy(self) -> bool:
        """Check if container is in healthy state."""
        return self.status == "running" and self.failed_health_checks < 3


class HybridContainerOrchestrator:
    """
    Production-grade hybrid container orchestrator with three-tier pool management.
    
    Architecture:
    - HOT Pool: Core services (framework, redis, postgres, kali) - always running
    - WARM Pool: Frequently used tools - started on demand, kept alive with TTL
    - COLD Pool: Rarely used services - started only when needed
    
    Features:
    - Async container lifecycle management
    - Health checking with automatic recovery
    - TTL-based cleanup for warm pool
    - Profile-to-container intelligent mapping
    - Parallel startup with concurrency limits
    - Comprehensive error handling and logging
    """
    
    # Default pool configurations (fallback if YAML fails to load)
    DEFAULT_HOT_POOL: List[str] = [
        'ats-mafia-framework',
        'redis',
        'postgres',
        'kali-sandbox'
    ]
    
    DEFAULT_WARM_POOL: List[str] = [
        'ats_network_nmap',
        'ats_recon_amass',
        'ats_web_zap',
        'ats_exploit_metasploit'
    ]
    
    DEFAULT_COLD_POOL: List[str] = [
        'ats_adversary_caldera',
        'ats_honeypot_cowrie',
        'ats_vuln_openvas'
    ]
    
    # Default profile to container mappings (fallback)
    DEFAULT_PROFILE_CONTAINERS: Dict[str, List[str]] = {
        "red_team_operator": [
            "ats_network_nmap",
            "ats_recon_amass",
            "ats_exploit_metasploit"
        ],
        "phantom": [
            "ats_adversary_atomic",
            "ats_lab_kali_base"
        ],
        "watcher": [
            "ats_monitoring_elk",
            "ats_network_nmap"
        ],
        "puppet_master": [
            "ats_phishing_gophish"
        ]
    }
    
    # Default configuration constants (fallback)
    DEFAULT_MAX_PARALLEL_STARTUP: int = 3
    DEFAULT_WARM_TTL_MINUTES: int = 30
    DEFAULT_HEALTH_CHECK_TIMEOUT: int = 30
    DEFAULT_CONTAINER_START_TIMEOUT: int = 120
    DEFAULT_MAX_RETRY_ATTEMPTS: int = 3
    DEFAULT_CLEANUP_INTERVAL_SECONDS: int = 300  # 5 minutes
    
    def __init__(
        self,
        warm_ttl_minutes: Optional[int] = None,
        enable_auto_cleanup: bool = True,
        config_path: Optional[str] = None
    ):
        """
        Initialize the container orchestrator.
        
        Args:
            warm_ttl_minutes: TTL for warm pool containers in minutes (overrides YAML)
            enable_auto_cleanup: Enable automatic cleanup of idle containers
            config_path: Path to container_pools.yaml (None uses default location)
        
        Raises:
            RuntimeError: If Docker is not available or initialization fails
        """
        # Load configuration from YAML
        self._load_pool_config(config_path)
        
        # Override TTL if provided
        if warm_ttl_minutes is not None:
            self.warm_ttl_minutes = warm_ttl_minutes
        else:
            # Use value from YAML warm pool config, or default
            if self.pool_config:
                warm_pool = self.pool_config.get_warm_pool()
                if warm_pool and warm_pool.ttl_seconds:
                    self.warm_ttl_minutes = warm_pool.ttl_seconds // 60
                else:
                    self.warm_ttl_minutes = self.DEFAULT_WARM_TTL_MINUTES
            else:
                self.warm_ttl_minutes = self.DEFAULT_WARM_TTL_MINUTES
        
        self.enable_auto_cleanup = enable_auto_cleanup
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(f"Docker not available: {e}")
        
        # Initialize container manager for routing
        try:
            self.container_manager = ContainerManager()
            logger.info("Container manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize container manager: {e}")
            raise RuntimeError(f"Container manager initialization failed: {e}")
        
        # State tracking
        self._container_states: Dict[str, ContainerState] = {}
        self._initialize_states()
        
        # Async task management
        self._cleanup_task: Optional[asyncio.Task] = None
        self._startup_semaphore = asyncio.Semaphore(self.MAX_PARALLEL_STARTUP)
        
        # Metrics
        self._total_starts = 0
        self._total_stops = 0
        self._failed_starts = 0
        self._failed_health_checks = 0
        
        logger.info(
            f"HybridContainerOrchestrator initialized: "
            f"Hot={len(self.HOT_POOL)}, Warm={len(self.WARM_POOL)}, "
            f"Cold={len(self.COLD_POOL)}, TTL={self.warm_ttl_minutes}m"
        )
    
    def _load_pool_config(self, config_path: Optional[str] = None) -> None:
        """
        Load pool configuration from YAML file.
        
        Args:
            config_path: Optional path to config file
        """
        try:
            # Load YAML configuration
            if config_path:
                from pathlib import Path
                self.pool_config = ContainerPoolConfig(Path(config_path))
                self.pool_config.load()
            else:
                self.pool_config = get_pool_config()
            
            # Extract pool containers from configuration
            hot_pool = self.pool_config.get_hot_pool()
            warm_pool = self.pool_config.get_warm_pool()
            cold_pool = self.pool_config.get_cold_pool()
            
            self.HOT_POOL = [c.name for c in hot_pool.containers] if hot_pool else self.DEFAULT_HOT_POOL
            self.WARM_POOL = [c.name for c in warm_pool.containers] if warm_pool else self.DEFAULT_WARM_POOL
            self.COLD_POOL = [c.name for c in cold_pool.containers] if cold_pool else self.DEFAULT_COLD_POOL
            
            # Extract profile mappings
            self.PROFILE_CONTAINERS = {}
            for profile_id, mapping in self.pool_config.profile_mappings.items():
                self.PROFILE_CONTAINERS[profile_id] = self.pool_config.get_containers_for_profile(profile_id)
            
            if not self.PROFILE_CONTAINERS:
                self.PROFILE_CONTAINERS = self.DEFAULT_PROFILE_CONTAINERS
            
            # Extract orchestration settings
            self.MAX_PARALLEL_STARTUP = self.pool_config.get_orchestration_setting(
                'max_parallel_starts', self.DEFAULT_MAX_PARALLEL_STARTUP
            )
            self.HEALTH_CHECK_TIMEOUT = self.pool_config.get_orchestration_setting(
                'health_check_timeout', self.DEFAULT_HEALTH_CHECK_TIMEOUT
            )
            self.CONTAINER_START_TIMEOUT = self.pool_config.get_orchestration_setting(
                'startup_timeout', self.DEFAULT_CONTAINER_START_TIMEOUT
            )
            self.MAX_RETRY_ATTEMPTS = self.pool_config.get_orchestration_setting(
                'retry_attempts', self.DEFAULT_MAX_RETRY_ATTEMPTS
            )
            self.CLEANUP_INTERVAL_SECONDS = self.pool_config.get_orchestration_setting(
                'shutdown_grace_period', self.DEFAULT_CLEANUP_INTERVAL_SECONDS
            )
            
            logger.info(
                f"Loaded pool configuration from YAML: "
                f"{len(self.HOT_POOL)} hot, {len(self.WARM_POOL)} warm, "
                f"{len(self.COLD_POOL)} cold containers"
            )
            
        except Exception as e:
            logger.warning(f"Failed to load YAML config, using defaults: {e}")
            # Use default hardcoded values as fallback
            self.pool_config = None
            self.HOT_POOL = self.DEFAULT_HOT_POOL
            self.WARM_POOL = self.DEFAULT_WARM_POOL
            self.COLD_POOL = self.DEFAULT_COLD_POOL
            self.PROFILE_CONTAINERS = self.DEFAULT_PROFILE_CONTAINERS
            self.MAX_PARALLEL_STARTUP = self.DEFAULT_MAX_PARALLEL_STARTUP
            self.HEALTH_CHECK_TIMEOUT = self.DEFAULT_HEALTH_CHECK_TIMEOUT
            self.CONTAINER_START_TIMEOUT = self.DEFAULT_CONTAINER_START_TIMEOUT
            self.MAX_RETRY_ATTEMPTS = self.DEFAULT_MAX_RETRY_ATTEMPTS
            self.CLEANUP_INTERVAL_SECONDS = self.DEFAULT_CLEANUP_INTERVAL_SECONDS
    
    def _initialize_states(self) -> None:
        """Initialize container state tracking for all pools."""
        for container in self.HOT_POOL:
            self._container_states[container] = ContainerState(
                name=container,
                tier=PoolTier.HOT
            )
        
        for container in self.WARM_POOL:
            self._container_states[container] = ContainerState(
                name=container,
                tier=PoolTier.WARM
            )
        
        for container in self.COLD_POOL:
            self._container_states[container] = ContainerState(
                name=container,
                tier=PoolTier.COLD
            )
        
        logger.debug(f"Initialized state tracking for {len(self._container_states)} containers")
    
    async def initialize(self) -> Dict[str, bool]:
        """
        Initialize the orchestrator by starting all hot pool containers.
        
        This should be called during application startup to ensure core
        services are available immediately.
        
        Returns:
            Dict mapping container names to startup success status
        
        Raises:
            RuntimeError: If critical hot pool containers fail to start
        """
        logger.info("Starting hot pool initialization...")
        start_time = time.time()
        
        results = {}
        tasks = []
        
        # Start hot pool containers in parallel
        for container_name in self.HOT_POOL:
            task = asyncio.create_task(
                self._start_container_with_retry(container_name)
            )
            tasks.append((container_name, task))
        
        # Wait for all to complete
        for container_name, task in tasks:
            try:
                success = await task
                results[container_name] = success
                if not success:
                    logger.error(f"Failed to start hot pool container: {container_name}")
            except Exception as e:
                logger.error(f"Exception starting {container_name}: {e}")
                results[container_name] = False
        
        # Check if any critical containers failed
        failed_critical = [name for name, success in results.items() if not success]
        if failed_critical:
            error_msg = f"Critical hot pool containers failed to start: {failed_critical}"
            logger.error(error_msg)
            # Don't raise - let the application decide how to handle
            # raise RuntimeError(error_msg)
        
        # Start background cleanup if enabled
        if self.enable_auto_cleanup:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started background cleanup task")
        
        elapsed = time.time() - start_time
        success_count = sum(1 for s in results.values() if s)
        logger.info(
            f"Hot pool initialization complete: {success_count}/{len(results)} "
            f"containers started in {elapsed:.2f}s"
        )
        
        return results
    
    async def prepare_for_profile(self, profile_id: str) -> Dict[str, bool]:
        """
        Prepare all required containers for a specific profile.
        
        This ensures that all containers needed by the profile are running
        and healthy before the profile starts executing tasks.
        
        Args:
            profile_id: The profile identifier (e.g., "red_team_operator")
        
        Returns:
            Dict mapping container names to preparation success status
        """
        logger.info(f"Preparing containers for profile: {profile_id}")
        
        # Get required containers for this profile
        required_containers = self._get_required_containers(profile_id)
        if not required_containers:
            logger.warning(f"No containers mapped for profile: {profile_id}")
            return {}
        
        logger.info(f"Profile {profile_id} requires: {required_containers}")
        
        # Start containers in parallel (respecting semaphore limit)
        results = {}
        tasks = []
        
        for container_name in required_containers:
            task = asyncio.create_task(
                self._ensure_container_running(container_name)
            )
            tasks.append((container_name, task))
        
        # Wait for all to complete
        for container_name, task in tasks:
            try:
                success = await task
                results[container_name] = success
                if success:
                    # Mark as used to prevent premature cleanup
                    if container_name in self._container_states:
                        self._container_states[container_name].mark_used()
            except Exception as e:
                logger.error(f"Exception preparing {container_name}: {e}")
                results[container_name] = False
        
        success_count = sum(1 for s in results.values() if s)
        logger.info(
            f"Profile preparation complete: {success_count}/{len(results)} "
            f"containers ready for {profile_id}"
        )
        
        return results
    
    async def _ensure_container_running(self, container_name: str) -> bool:
        """
        Ensure a container is running, starting it if necessary.
        
        Args:
            container_name: Name of the container
        
        Returns:
            True if container is running and healthy
        """
        # Check current state
        state = self._container_states.get(container_name)
        if state and state.is_healthy():
            logger.debug(f"Container {container_name} already running and healthy")
            return True
        
        # Need to start the container
        return await self._start_container_with_retry(container_name)
    
    async def _start_container_with_retry(
        self,
        container_name: str,
        max_retries: Optional[int] = None
    ) -> bool:
        """
        Start a container with automatic retry on failure.
        
        Args:
            container_name: Name of the container
            max_retries: Maximum number of retry attempts (None uses orchestrator default)
        
        Returns:
            True if container started successfully
        """
        # Use orchestrator default if not specified
        retry_count = max_retries if max_retries is not None else self.MAX_RETRY_ATTEMPTS
        
        for attempt in range(1, retry_count + 1):
            try:
                success = await self._start_container(container_name)
                if success:
                    return True
                
                if attempt < retry_count:
                    backoff = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    logger.warning(
                        f"Retry {attempt}/{retry_count} for {container_name} "
                        f"in {backoff}s..."
                    )
                    await asyncio.sleep(backoff)
            except Exception as e:
                logger.error(
                    f"Attempt {attempt}/{retry_count} failed for {container_name}: {e}"
                )
                if attempt < retry_count:
                    await asyncio.sleep(min(2 ** attempt, 30))
        
        self._failed_starts += 1
        logger.error(f"Failed to start {container_name} after {retry_count} attempts")
        return False
    
    async def _start_container(self, container_name: str) -> bool:
        """
        Start a single container with health checking.
        
        This is the core container startup method that:
        1. Acquires startup semaphore (limits parallel starts)
        2. Uses docker-compose to start the container
        3. Performs health check with timeout
        4. Updates container state
        
        Args:
            container_name: Name of the container to start
        
        Returns:
            True if container started and passed health check
        """
        async with self._startup_semaphore:
            logger.info(f"Starting container: {container_name}")
            start_time = time.time()
            
            try:
                # Update state
                if container_name in self._container_states:
                    state = self._container_states[container_name]
                    state.restart_count += 1
                    state.start_time = datetime.utcnow()
                
                # Use docker-compose to start the container
                result = await asyncio.create_subprocess_exec(
                    'docker-compose',
                    'up',
                    '-d',
                    container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(),
                    timeout=self.CONTAINER_START_TIMEOUT
                )
                
                if result.returncode != 0:
                    error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                    logger.error(f"Failed to start {container_name}: {error_msg}")
                    return False
                
                logger.debug(f"Docker-compose started {container_name}")
                
                # Perform health check
                is_healthy = await self._health_check(container_name)
                
                if is_healthy:
                    # Update state
                    if container_name in self._container_states:
                        state = self._container_states[container_name]
                        state.status = "running"
                        state.mark_used()
                        state.failed_health_checks = 0
                    
                    self._total_starts += 1
                    elapsed = time.time() - start_time
                    logger.info(f"Successfully started {container_name} in {elapsed:.2f}s")
                    return True
                else:
                    logger.error(f"Container {container_name} failed health check")
                    if container_name in self._container_states:
                        self._container_states[container_name].failed_health_checks += 1
                    return False
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout starting {container_name}")
                return False
            except Exception as e:
                logger.error(f"Exception starting {container_name}: {e}", exc_info=True)
                return False
    
    async def _health_check(self, container_name: str) -> bool:
        """
        Perform health check on a container.
        
        Checks that:
        1. Container exists
        2. Container is running
        3. Container responds to basic commands (optional)
        
        Args:
            container_name: Name of the container
        
        Returns:
            True if container is healthy
        """
        try:
            # Get container
            container = self.docker_client.containers.get(container_name)
            
            # Check status
            container.reload()
            if container.status != 'running':
                logger.debug(f"Health check failed: {container_name} status={container.status}")
                return False
            
            # Update health check count
            if container_name in self._container_states:
                self._container_states[container_name].health_check_count += 1
            
            logger.debug(f"Health check passed for {container_name}")
            return True
            
        except NotFound:
            logger.error(f"Health check failed: {container_name} not found")
            return False
        except Exception as e:
            logger.error(f"Health check exception for {container_name}: {e}")
            self._failed_health_checks += 1
            return False
    
    async def _stop_container(self, container_name: str, timeout: int = 30) -> bool:
        """
        Gracefully stop a container.
        
        Args:
            container_name: Name of the container
            timeout: Timeout in seconds for graceful shutdown
        
        Returns:
            True if container stopped successfully
        """
        logger.info(f"Stopping container: {container_name}")
        
        try:
            # Use docker-compose to stop gracefully
            result = await asyncio.create_subprocess_exec(
                'docker-compose',
                'stop',
                '-t', str(timeout),
                container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=timeout + 10  # Extra time for docker-compose itself
            )
            
            if result.returncode == 0:
                # Update state
                if container_name in self._container_states:
                    self._container_states[container_name].status = "stopped"
                
                self._total_stops += 1
                logger.info(f"Successfully stopped {container_name}")
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                logger.error(f"Failed to stop {container_name}: {error_msg}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout stopping {container_name}, forcing...")
            # Try force stop as fallback
            try:
                container = self.docker_client.containers.get(container_name)
                container.kill()
                logger.warning(f"Force stopped {container_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to force stop {container_name}: {e}")
                return False
        except Exception as e:
            logger.error(f"Exception stopping {container_name}: {e}", exc_info=True)
            return False
    
    def _get_required_containers(self, profile_id: str) -> List[str]:
        """
        Get list of containers required for a profile.
        
        Args:
            profile_id: The profile identifier
        
        Returns:
            List of container names needed by the profile
        """
        # Direct mapping
        if profile_id in self.PROFILE_CONTAINERS:
            return self.PROFILE_CONTAINERS[profile_id]
        
        # Normalize profile_id (handle case variations)
        normalized = profile_id.lower().replace('-', '_').replace(' ', '_')
        for key, containers in self.PROFILE_CONTAINERS.items():
            if key.lower().replace('-', '_') == normalized:
                return containers
        
        # Return empty list if no mapping found
        logger.warning(f"No container mapping found for profile: {profile_id}")
        return []
    
    async def _cleanup_loop(self) -> None:
        """
        Background task to cleanup idle warm pool containers.
        
        Runs periodically to check for containers that have exceeded their TTL
        and gracefully stops them to free resources.
        """
        logger.info("Starting cleanup loop")
        
        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
                await self._cleanup_idle_containers()
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                # Continue running despite errors
    
    async def _cleanup_idle_containers(self) -> None:
        """Check and stop idle warm pool containers."""
        logger.debug("Checking for idle warm pool containers...")
        
        stopped = []
        for container_name, state in self._container_states.items():
            # Only cleanup warm pool containers
            if state.tier != PoolTier.WARM:
                continue
            
            # Check if idle
            if state.status == "running" and state.is_idle(self.warm_ttl_minutes):
                idle_minutes = 0.0
                if state.last_used:
                    idle_minutes = (datetime.utcnow() - state.last_used).total_seconds() / 60
                logger.info(
                    f"Container {container_name} idle for {idle_minutes:.1f}m, stopping..."
                )
                success = await self._stop_container(container_name)
                if success:
                    stopped.append(container_name)
        
        if stopped:
            logger.info(f"Cleanup: stopped {len(stopped)} idle containers: {stopped}")
        else:
            logger.debug("Cleanup: no idle containers found")
    
    def get_orchestrator_stats(self) -> Dict:
        """
        Get current orchestrator statistics.
        
        Returns:
            Dict containing metrics and state information
        """
        running_count = sum(
            1 for state in self._container_states.values()
            if state.status == "running"
        )
        
        tier_stats = {
            "hot": sum(1 for s in self._container_states.values() 
                      if s.tier == PoolTier.HOT and s.status == "running"),
            "warm": sum(1 for s in self._container_states.values() 
                       if s.tier == PoolTier.WARM and s.status == "running"),
            "cold": sum(1 for s in self._container_states.values() 
                       if s.tier == PoolTier.COLD and s.status == "running"),
        }
        
        return {
            "total_containers": len(self._container_states),
            "running_containers": running_count,
            "tier_distribution": tier_stats,
            "total_starts": self._total_starts,
            "total_stops": self._total_stops,
            "failed_starts": self._failed_starts,
            "failed_health_checks": self._failed_health_checks,
            "warm_ttl_minutes": self.warm_ttl_minutes,
            "auto_cleanup_enabled": self.enable_auto_cleanup,
        }
    
    def get_container_status(self, container_name: str) -> Optional[Dict]:
        """
        Get detailed status of a specific container.
        
        Args:
            container_name: Name of the container
        
        Returns:
            Dict with container state or None if not tracked
        """
        state = self._container_states.get(container_name)
        if not state:
            return None
        
        return {
            "name": state.name,
            "tier": state.tier.value,
            "status": state.status,
            "last_used": state.last_used.isoformat() if state.last_used else None,
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "health_check_count": state.health_check_count,
            "failed_health_checks": state.failed_health_checks,
            "restart_count": state.restart_count,
            "is_healthy": state.is_healthy(),
        }
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the orchestrator.
        
        Stops all containers and cleanup tasks.
        """
        logger.info("Shutting down orchestrator...")
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Stop all running containers (except hot pool)
        stop_tasks = []
        for container_name, state in self._container_states.items():
            if state.status == "running" and state.tier != PoolTier.HOT:
                task = asyncio.create_task(self._stop_container(container_name))
                stop_tasks.append(task)
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Close Docker client
        if self.docker_client:
            self.docker_client.close()
        
        logger.info("Orchestrator shutdown complete")


__all__ = [
    'HybridContainerOrchestrator',
    'PoolTier',
    'ContainerState',
]