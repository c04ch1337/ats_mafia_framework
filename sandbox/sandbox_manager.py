"""
Sandbox Manager
Manage Kali sandbox container lifecycle - creation, destruction, snapshots.
"""

import docker
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SandboxManager:
    """Manage Kali sandbox containers for training sessions."""
    
    def __init__(self):
        """Initialize sandbox manager."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.base_image = 'kalilinux/kali-rolling:latest'
            self.base_container_name = 'ats_kali_sandbox'
            logger.info("SandboxManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SandboxManager: {e}")
            raise RuntimeError(f"Docker not available: {e}")
    
    def create_ephemeral_sandbox(
        self,
        session_id: str,
        cpu_limit: str = '2.0',
        memory_limit: str = '4g'
    ) -> str:
        """
        Create isolated sandbox container for specific session.
        
        Args:
            session_id: Unique session identifier
            cpu_limit: CPU limit (e.g., '2.0' for 2 cores)
            memory_limit: Memory limit (e.g., '4g')
            
        Returns:
            Container ID of created sandbox
        """
        container_name = f"ats_kali_session_{session_id}"
        
        try:
            # Check if container already exists
            try:
                existing = self.docker_client.containers.get(container_name)
                logger.warning(f"Container {container_name} already exists, removing it")
                existing.remove(force=True)
            except docker.errors.NotFound:
                pass
            
            # Create new container
            logger.info(f"Creating ephemeral sandbox: {container_name}")
            
            container = self.docker_client.containers.create(
                image=self.base_image,
                name=container_name,
                command='/bin/bash -c "tail -f /dev/null"',
                detach=True,
                network='ats-training-network',
                volumes={
                    '/tmp': {'bind': '/root/workspace', 'mode': 'rw'}
                },
                environment={
                    'SESSION_ID': session_id,
                    'CREATED_AT': datetime.utcnow().isoformat()
                },
                cpu_period=100000,
                cpu_quota=int(float(cpu_limit) * 100000),
                mem_limit=memory_limit,
                security_opt=['no-new-privileges:true'],
                cap_drop=['ALL'],
                cap_add=['NET_ADMIN', 'NET_RAW', 'NET_BIND_SERVICE'],
                labels={
                    'ats.mafia.session': session_id,
                    'ats.mafia.type': 'ephemeral_sandbox',
                    'ats.mafia.created': datetime.utcnow().isoformat()
                }
            )
            
            # Start container
            container.start()
            
            logger.info(f"Ephemeral sandbox created: {container.id[:12]}")
            
            return container.id
            
        except Exception as e:
            logger.error(f"Failed to create ephemeral sandbox: {e}")
            raise RuntimeError(f"Sandbox creation failed: {e}")
    
    def destroy_sandbox(self, container_id: str, force: bool = True) -> bool:
        """
        Destroy sandbox container.
        
        Args:
            container_id: Container ID or name
            force: Force removal even if running
            
        Returns:
            True if destroyed successfully
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Stop if running
            if container.status == 'running':
                logger.info(f"Stopping container: {container_id[:12]}")
                container.stop(timeout=10)
            
            # Remove container
            logger.info(f"Removing container: {container_id[:12]}")
            container.remove(force=force)
            
            logger.info(f"Sandbox destroyed: {container_id[:12]}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to destroy sandbox: {e}")
            return False
    
    def get_sandbox_metrics(self, container_id: str) -> Dict[str, any]:
        """
        Get resource usage metrics for sandbox.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Dict with resource metrics
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            if container.status != 'running':
                return {
                    'available': False,
                    'status': container.status,
                    'message': 'Container not running'
                }
            
            # Get stats
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            # Network I/O
            network_rx = 0
            network_tx = 0
            if 'networks' in stats:
                for net_data in stats['networks'].values():
                    network_rx += net_data.get('rx_bytes', 0)
                    network_tx += net_data.get('tx_bytes', 0)
            
            return {
                'available': True,
                'container_id': container.id[:12],
                'name': container.name,
                'status': container.status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
                'memory_percent': round(memory_percent, 2),
                'network_rx_mb': round(network_rx / (1024 * 1024), 2),
                'network_tx_mb': round(network_tx / (1024 * 1024), 2),
                'uptime_seconds': time.time() - datetime.fromisoformat(
                    container.attrs['State']['StartedAt'].replace('Z', '+00:00')
                ).timestamp()
            }
            
        except docker.errors.NotFound:
            return {
                'available': False,
                'error': 'Container not found'
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def snapshot_sandbox(self, container_id: str, snapshot_name: Optional[str] = None) -> str:
        """
        Create snapshot/checkpoint of sandbox state.
        
        Args:
            container_id: Container ID or name
            snapshot_name: Optional name for snapshot
            
        Returns:
            Image ID of snapshot
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            if not snapshot_name:
                snapshot_name = f"ats_kali_snapshot_{int(time.time())}"
            
            logger.info(f"Creating snapshot: {snapshot_name}")
            
            # Commit container to image
            image = container.commit(
                repository='ats-mafia/kali-snapshot',
                tag=snapshot_name,
                message=f"Snapshot of {container.name}"
            )
            
            logger.info(f"Snapshot created: {image.id[:12]}")
            return image.id
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise RuntimeError(f"Snapshot creation failed: {e}")
    
    def restore_sandbox(
        self,
        snapshot_id: str,
        session_id: str
    ) -> str:
        """
        Restore sandbox from snapshot.
        
        Args:
            snapshot_id: Image ID of snapshot
            session_id: Session ID for restored container
            
        Returns:
            Container ID of restored sandbox
        """
        container_name = f"ats_kali_session_{session_id}_restored"
        
        try:
            logger.info(f"Restoring sandbox from snapshot: {snapshot_id[:12]}")
            
            # Create container from snapshot image
            container = self.docker_client.containers.create(
                image=snapshot_id,
                name=container_name,
                command='/bin/bash -c "tail -f /dev/null"',
                detach=True,
                network='ats-training-network',
                labels={
                    'ats.mafia.session': session_id,
                    'ats.mafia.type': 'restored_sandbox',
                    'ats.mafia.restored_from': snapshot_id,
                    'ats.mafia.created': datetime.utcnow().isoformat()
                }
            )
            
            container.start()
            
            logger.info(f"Sandbox restored: {container.id[:12]}")
            return container.id
            
        except Exception as e:
            logger.error(f"Failed to restore sandbox: {e}")
            raise RuntimeError(f"Sandbox restoration failed: {e}")
    
    def list_sandboxes(self) -> List[Dict[str, any]]:
        """
        List all ATS MAFIA sandbox containers.
        
        Returns:
            List of sandbox container info
        """
        try:
            filters = {'label': 'ats.mafia.type'}
            containers = self.docker_client.containers.list(all=True, filters=filters)
            
            sandboxes = []
            for container in containers:
                sandboxes.append({
                    'id': container.id[:12],
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'],
                    'session_id': container.labels.get('ats.mafia.session', 'unknown'),
                    'type': container.labels.get('ats.mafia.type', 'unknown')
                })
            
            return sandboxes
            
        except Exception as e:
            logger.error(f"Failed to list sandboxes: {e}")
            return []
    
    def cleanup_old_sandboxes(self, max_age_hours: int = 24) -> int:
        """
        Clean up old ephemeral sandboxes.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of sandboxes cleaned up
        """
        try:
            filters = {'label': 'ats.mafia.type=ephemeral_sandbox'}
            containers = self.docker_client.containers.list(all=True, filters=filters)
            
            cleanup_count = 0
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            for container in containers:
                created_str = container.labels.get('ats.mafia.created')
                if created_str:
                    created_time = datetime.fromisoformat(created_str).timestamp()
                    if created_time < cutoff_time:
                        logger.info(f"Cleaning up old sandbox: {container.name}")
                        self.destroy_sandbox(container.id)
                        cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} old sandboxes")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup sandboxes: {e}")
            return 0
    
    def get_base_container_status(self) -> Dict[str, any]:
        """
        Get status of base Kali container.
        
        Returns:
            Dict with base container status
        """
        try:
            container = self.docker_client.containers.get(self.base_container_name)
            
            return {
                'available': True,
                'name': container.name,
                'status': container.status,
                'id': container.id[:12],
                'image': container.image.tags[0] if container.image.tags else 'unknown'
            }
        except docker.errors.NotFound:
            return {
                'available': False,
                'error': 'Base container not found',
                'message': 'Please start docker-compose'
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def close(self):
        """Close Docker client connection."""
        if self.docker_client:
            self.docker_client.close()
            logger.info("SandboxManager connection closed")


__all__ = ['SandboxManager']