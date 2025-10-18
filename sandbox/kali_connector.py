"""
Kali Linux Connector
Secure connection and command execution in Kali sandbox container.
"""

import docker
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from .tool_whitelist import validate_command, is_tool_approved

logger = logging.getLogger(__name__)


class KaliConnectorError(Exception):
    """Base exception for KaliConnector errors."""
    pass


class ContainerNotFoundError(KaliConnectorError):
    """Raised when Kali container is not found."""
    pass


class CommandValidationError(KaliConnectorError):
    """Raised when command fails validation."""
    pass


class CommandExecutionError(KaliConnectorError):
    """Raised when command execution fails."""
    pass


class KaliConnector:
    """
    Secure connector to Kali Linux sandbox container.
    Handles command execution, output capture, and resource management.
    """
    
    def __init__(self, container_name: str = 'ats_kali_sandbox'):
        """
        Initialize Kali connector.
        
        Args:
            container_name: Name of the Kali Docker container
        """
        self.container_name = container_name
        self.docker_client = None
        self.container = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Docker and Kali container."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise KaliConnectorError(f"Docker connection failed: {e}")
        
        try:
            self.container = self.docker_client.containers.get(self.container_name)
            logger.info(f"Connected to Kali container: {self.container_name}")
        except docker.errors.NotFound:
            logger.error(f"Kali container '{self.container_name}' not found")
            raise ContainerNotFoundError(
                f"Container '{self.container_name}' not found. "
                "Please ensure docker-compose is running."
            )
        except Exception as e:
            logger.error(f"Failed to get container: {e}")
            raise KaliConnectorError(f"Container access failed: {e}")
    
    def execute_command(
        self,
        command: str,
        timeout: int = 300,
        working_dir: str = '/root/workspace',
        environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Execute command in Kali container with safety checks.
        
        Args:
            command: Command to execute
            timeout: Maximum execution time in seconds (default: 300)
            working_dir: Working directory for command execution
            environment: Additional environment variables
            
        Returns:
            Dict with keys:
                - success: bool
                - stdout: str
                - stderr: str
                - exit_code: int
                - execution_time: float
                - command: str (executed command)
                - timestamp: str
        """
        # Validate command
        is_valid, reason = validate_command(command)
        if not is_valid:
            logger.warning(f"Command validation failed: {reason}")
            raise CommandValidationError(f"Command rejected: {reason}")
        
        # Check container status
        self.container.reload()
        if self.container.status != 'running':
            raise KaliConnectorError(
                f"Container is not running (status: {self.container.status})"
            )
        
        logger.info(f"Executing command: {command}")
        start_time = time.time()
        
        try:
            # Prepare environment
            env = environment or {}
            
            # Execute command
            exec_result = self.container.exec_run(
                cmd=['bash', '-c', command],
                workdir=working_dir,
                environment=env,
                demux=True,
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                privileged=False,
                user='root'
            )
            
            execution_time = time.time() - start_time
            
            # Decode output
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ''
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ''
            exit_code = exec_result.exit_code
            
            result = {
                'success': exit_code == 0,
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'execution_time': round(execution_time, 2),
                'command': command,
                'timestamp': datetime.utcnow().isoformat(),
                'container': self.container_name
            }
            
            if exit_code == 0:
                logger.info(f"Command executed successfully in {execution_time:.2f}s")
            else:
                logger.warning(f"Command failed with exit code {exit_code}")
            
            return result
            
        except docker.errors.APIError as e:
            logger.error(f"Docker API error during execution: {e}")
            raise CommandExecutionError(f"Docker API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during execution: {e}")
            raise CommandExecutionError(f"Execution failed: {e}")
    
    def install_tool(self, tool_name: str) -> bool:
        """
        Install specific Kali tool if not present.
        
        Args:
            tool_name: Name of the tool to install
            
        Returns:
            True if installation successful
        """
        if not is_tool_approved(tool_name):
            logger.warning(f"Tool '{tool_name}' is not in approved list")
            return False
        
        # Check if tool is already installed
        check_cmd = f"which {tool_name}"
        result = self.execute_command(check_cmd, timeout=10)
        
        if result['success']:
            logger.info(f"Tool '{tool_name}' is already installed")
            return True
        
        # Install tool
        logger.info(f"Installing tool: {tool_name}")
        install_cmd = f"apt-get update && apt-get install -y {tool_name}"
        
        try:
            result = self.execute_command(install_cmd, timeout=600)
            if result['success']:
                logger.info(f"Tool '{tool_name}' installed successfully")
                return True
            else:
                logger.error(f"Failed to install '{tool_name}': {result['stderr']}")
                return False
        except Exception as e:
            logger.error(f"Error installing tool: {e}")
            return False
    
    def list_available_tools(self) -> List[str]:
        """
        List all available security tools in container.
        
        Returns:
            List of installed tool names
        """
        from .tool_whitelist import get_all_approved_tools
        
        approved_tools = get_all_approved_tools()
        available_tools = []
        
        for tool in approved_tools:
            try:
                result = self.execute_command(f"which {tool}", timeout=5)
                if result['success']:
                    available_tools.append(tool)
            except Exception:
                continue
        
        logger.info(f"Found {len(available_tools)} available tools")
        return sorted(available_tools)
    
    def get_container_status(self) -> Dict[str, any]:
        """
        Get comprehensive container status and health.
        
        Returns:
            Dict containing status information
        """
        try:
            self.container.reload()
            
            # Get container stats
            stats = self.container.stats(stream=False)
            
            # Calculate resource usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'available': True,
                'status': self.container.status,
                'name': self.container.name,
                'id': self.container.short_id,
                'image': self.container.image.tags[0] if self.container.image.tags else 'unknown',
                'created': self.container.attrs['Created'],
                'started': self.container.attrs['State']['StartedAt'],
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
                'memory_percent': round(memory_percent, 2),
                'network': self.container.attrs['NetworkSettings']['Networks'],
                'health': self.container.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return {
                'available': False,
                'error': str(e),
                'message': 'Failed to retrieve container status'
            }
    
    def get_tool_info(self, tool_name: str) -> Dict[str, str]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dict with tool information
        """
        if not is_tool_approved(tool_name):
            return {'error': 'Tool not approved'}
        
        try:
            # Check if installed
            which_result = self.execute_command(f"which {tool_name}", timeout=5)
            if not which_result['success']:
                return {'installed': False, 'tool': tool_name}
            
            path = which_result['stdout'].strip()
            
            # Get version
            version_result = self.execute_command(f"{tool_name} --version", timeout=10)
            version = version_result['stdout'].strip() if version_result['success'] else 'unknown'
            
            # Get help text (first 20 lines)
            help_result = self.execute_command(f"{tool_name} --help | head -20", timeout=10)
            help_text = help_result['stdout'] if help_result['success'] else ''
            
            return {
                'installed': True,
                'tool': tool_name,
                'path': path,
                'version': version,
                'help': help_text
            }
        except Exception as e:
            logger.error(f"Error getting tool info: {e}")
            return {'error': str(e), 'tool': tool_name}
    
    def test_connectivity(self) -> bool:
        """
        Test connectivity to Kali container.
        
        Returns:
            True if container is reachable and responsive
        """
        try:
            result = self.execute_command('echo "test"', timeout=5)
            return result['success'] and 'test' in result['stdout']
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def cleanup_workspace(self) -> bool:
        """
        Clean up temporary files in workspace.
        
        Returns:
            True if cleanup successful
        """
        try:
            # Only clean files in /tmp and /root/workspace
            cleanup_cmd = "rm -rf /tmp/* /root/workspace/*"
            result = self.execute_command(cleanup_cmd, timeout=30)
            
            if result['success']:
                logger.info("Workspace cleaned successfully")
                return True
            else:
                logger.warning(f"Workspace cleanup had issues: {result['stderr']}")
                return False
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
    
    def get_network_info(self) -> Dict[str, any]:
        """
        Get network configuration of container.
        
        Returns:
            Dict with network information
        """
        try:
            self.container.reload()
            networks = self.container.attrs['NetworkSettings']['Networks']
            
            network_info = {}
            for net_name, net_config in networks.items():
                network_info[net_name] = {
                    'ip_address': net_config.get('IPAddress'),
                    'gateway': net_config.get('Gateway'),
                    'mac_address': net_config.get('MacAddress'),
                    'network_id': net_config.get('NetworkID')
                }
            
            return network_info
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close connection to Docker client."""
        if self.docker_client:
            self.docker_client.close()
            logger.info("Docker client connection closed")


# Export public API
__all__ = [
    'KaliConnector',
    'KaliConnectorError',
    'ContainerNotFoundError',
    'CommandValidationError',
    'CommandExecutionError',
]