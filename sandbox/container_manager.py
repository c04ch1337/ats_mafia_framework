"""
Container Manager - Modular Container Architecture
Routes agent tasks to specialized containers based on task requirements.
"""

import docker
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ContainerCategory(Enum):
    """Categories of specialized containers."""
    RECONNAISSANCE = "reconnaissance"
    WEB_TESTING = "web_testing"
    ADVERSARY_EMULATION = "adversary_emulation"
    PHISHING = "phishing"
    HONEYPOT = "honeypot"
    NETWORK_SCANNING = "network_scanning"
    EXPLOITATION = "exploitation"
    LAB = "lab"
    VULNERABILITY_SCANNING = "vulnerability_scanning"
    MONITORING = "monitoring"


class ContainerManager:
    """
    Manage routing of tasks to specialized containers.
    
    Implements intelligent routing based on:
    - Task type (reconnaissance, web testing, etc.)
    - Required tools
    - Resource requirements
    - Network requirements
    """
    
    # Container mappings
    CONTAINER_MAPPINGS = {
        # Reconnaissance tools
        'amass': 'ats_recon_amass',
        'theharvester': 'ats_recon_harvester',
        'nuclei': 'ats_recon_nuclei',
        'subfinder': 'ats_recon_subfinder',
        
        # Web testing tools
        'zap': 'ats_web_zap',
        'zap-cli': 'ats_web_zap',
        'nikto': 'ats_web_nikto',
        
        # Network scanning
        'nmap': 'ats_network_nmap',
        'masscan': 'ats_network_masscan',
        
        # Exploitation
        'metasploit': 'ats_exploit_metasploit',
        'msfconsole': 'ats_exploit_metasploit',
        'msfvenom': 'ats_exploit_metasploit',
        
        # Adversary emulation
        'caldera': 'ats_adversary_caldera',
        'atomic': 'ats_adversary_atomic',
        
        # Phishing
        'gophish': 'ats_phishing_gophish',
        
        # Honeypots
        'cowrie': 'ats_honeypot_cowrie',
        'dionaea': 'ats_honeypot_dionaea',
        
        # Vulnerability scanning
        'openvas': 'ats_vuln_openvas',
    }
    
    # Category patterns for task routing
    TASK_PATTERNS = {
        ContainerCategory.RECONNAISSANCE: [
            r'\b(subdomain|dns|domain|email|osint|harvest|enumerate)\b',
            r'\b(amass|theharvester|subfinder|nuclei)\b',
        ],
        ContainerCategory.WEB_TESTING: [
            r'\b(web|http|https|api|xss|sqli|csrf|injection)\b',
            r'\b(zap|nikto|burp|proxy)\b',
        ],
        ContainerCategory.NETWORK_SCANNING: [
            r'\b(scan|port|network|host|ping|traceroute)\b',
            r'\b(nmap|masscan|netcat|nc)\b',
        ],
        ContainerCategory.EXPLOITATION: [
            r'\b(exploit|payload|reverse|shell|meterpreter)\b',
            r'\b(metasploit|msf|msfvenom|msfconsole)\b',
        ],
        ContainerCategory.ADVERSARY_EMULATION: [
            r'\b(mitre|att&ck|technique|tactic|adversary)\b',
            r'\b(caldera|atomic|red team|emulation)\b',
        ],
        ContainerCategory.PHISHING: [
            r'\b(phish|social|engineering|email campaign)\b',
            r'\b(gophish|setoolkit)\b',
        ],
        ContainerCategory.VULNERABILITY_SCANNING: [
            r'\b(vulnerability|vuln|cve|patch|assessment)\b',
            r'\b(openvas|nessus|qualys)\b',
        ],
    }
    
    def __init__(self):
        """Initialize container manager."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("ContainerManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ContainerManager: {e}")
            raise RuntimeError(f"Docker not available: {e}")
    
    def route_task(
        self,
        task_description: str,
        tool_name: Optional[str] = None,
        category: Optional[ContainerCategory] = None
    ) -> str:
        """
        Route task to appropriate container.
        
        Args:
            task_description: Natural language description of task
            tool_name: Specific tool required (optional)
            category: Force specific category (optional)
        
        Returns:
            Container name to execute task in
        """
        # 1. Check if specific tool is requested
        if tool_name:
            container = self._route_by_tool(tool_name)
            if container:
                logger.info(f"Routed to {container} based on tool: {tool_name}")
                return container
        
        # 2. Check if category is specified
        if category:
            container = self._get_default_container_for_category(category)
            logger.info(f"Routed to {container} based on category: {category.value}")
            return container
        
        # 3. Analyze task description and route based on patterns
        detected_category = self._detect_category(task_description)
        if detected_category:
            container = self._get_default_container_for_category(detected_category)
            logger.info(f"Routed to {container} based on task analysis: {detected_category.value}")
            return container
        
        # 4. Default to general-purpose lab container
        default_container = 'ats_lab_kali_base'
        logger.info(f"Using default container: {default_container}")
        return default_container
    
    def _route_by_tool(self, tool_name: str) -> Optional[str]:
        """Route based on specific tool name."""
        # Normalize tool name
        tool_lower = tool_name.lower().strip()
        
        # Check direct mapping
        if tool_lower in self.CONTAINER_MAPPINGS:
            return self.CONTAINER_MAPPINGS[tool_lower]
        
        # Check partial matches
        for tool_pattern, container in self.CONTAINER_MAPPINGS.items():
            if tool_pattern in tool_lower or tool_lower in tool_pattern:
                return container
        
        return None
    
    def _detect_category(self, task_description: str) -> Optional[ContainerCategory]:
        """Detect task category from description."""
        task_lower = task_description.lower()
        
        # Score each category
        category_scores = {}
        for category, patterns in self.TASK_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, task_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Detected category: {best_category.value} (score: {category_scores[best_category]})")
            return best_category
        
        return None
    
    def _get_default_container_for_category(self, category: ContainerCategory) -> str:
        """Get default container for a category."""
        defaults = {
            ContainerCategory.RECONNAISSANCE: 'ats_recon_amass',
            ContainerCategory.WEB_TESTING: 'ats_web_zap',
            ContainerCategory.NETWORK_SCANNING: 'ats_network_nmap',
            ContainerCategory.EXPLOITATION: 'ats_exploit_metasploit',
            ContainerCategory.ADVERSARY_EMULATION: 'ats_adversary_caldera',
            ContainerCategory.PHISHING: 'ats_phishing_gophish',
            ContainerCategory.HONEYPOT: 'ats_honeypot_cowrie',
            ContainerCategory.VULNERABILITY_SCANNING: 'ats_vuln_openvas',
            ContainerCategory.LAB: 'ats_lab_kali_base',
            ContainerCategory.MONITORING: 'ats_monitoring_elk',
        }
        
        return defaults.get(category, 'ats_lab_kali_base')
    
    def execute_in_container(
        self,
        container_name: str,
        command: str,
        timeout: int = 300,
        working_dir: str = '/root'
    ) -> Dict:
        """
        Execute command in specified container.
        
        Args:
            container_name: Name of container
            command: Command to execute
            timeout: Timeout in seconds
            working_dir: Working directory
        
        Returns:
            Dict with execution results
        """
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Check if container is running
            if container.status != 'running':
                return {
                    'success': False,
                    'error': f'Container {container_name} is not running (status: {container.status})',
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1
                }
            
            # Execute command
            logger.info(f"Executing in {container_name}: {command}")
            
            exec_result = container.exec_run(
                cmd=['bash', '-c', command],
                workdir=working_dir,
                demux=True,
                stdout=True,
                stderr=True
            )
            
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ''
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ''
            
            return {
                'success': exec_result.exit_code == 0,
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exec_result.exit_code,
                'container': container_name
            }
            
        except Exception as e:
            if 'NotFound' in str(type(e)):
                logger.error(f"Container not found: {container_name}")
                return {
                    'success': False,
                    'error': f'Container {container_name} not found',
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1
                }
            else:
                logger.error(f"Execution failed: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'stdout': '',
                    'stderr': '',
                    'exit_code': -1
                }
    
    def get_container_info(self, container_name: str) -> Dict:
        """Get information about a specific container."""
        try:
            container = self.docker_client.containers.get(container_name)
            container.reload()
            
            # Get labels
            labels = container.labels
            
            return {
                'available': True,
                'name': container.name,
                'id': container.id[:12],
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'category': labels.get('ats.mafia.category', 'unknown'),
                'tool': labels.get('ats.mafia.tool', 'unknown'),
                'created': container.attrs['Created'],
                'networks': list(container.attrs['NetworkSettings']['Networks'].keys())
            }
        except Exception as e:
            if 'NotFound' in str(type(e)):
                return {
                    'available': False,
                    'error': f'Container {container_name} not found'
                }
            return {
                'available': False,
                'error': str(e)
            }
    
    def list_containers_by_category(self, category: ContainerCategory) -> List[Dict]:
        """List all containers in a specific category."""
        try:
            filters = {'label': f'ats.mafia.category={category.value}'}
            containers = self.docker_client.containers.list(all=True, filters=filters)
            
            container_list = []
            for container in containers:
                container_list.append({
                    'name': container.name,
                    'id': container.id[:12] if container.id else 'unknown',
                    'status': container.status,
                    'tool': container.labels.get('ats.mafia.tool', 'unknown')
                })
            
            return container_list
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def list_all_specialized_containers(self) -> Dict[str, List[Dict]]:
        """List all specialized containers grouped by category."""
        result = {}
        
        for category in ContainerCategory:
            containers = self.list_containers_by_category(category)
            if containers:
                result[category.value] = containers
        
        return result
    
    def get_container_health(self, container_name: str) -> Dict:
        """Get health and resource usage of container."""
        try:
            container = self.docker_client.containers.get(container_name)
            
            if container.status != 'running':
                return {
                    'healthy': False,
                    'status': container.status,
                    'message': 'Container not running'
                }
            
            # Get stats
            stats = container.stats(stream=False)
            
            # CPU usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'healthy': True,
                'status': container.status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
                'memory_percent': round(memory_percent, 2)
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def recommend_container(
        self,
        task_keywords: List[str],
        preferred_tool: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Recommend best container for task based on keywords.
        
        Args:
            task_keywords: List of keywords describing the task
            preferred_tool: Preferred tool if any
        
        Returns:
            Tuple of (container_name, confidence_score)
        """
        # Build task description from keywords
        task_desc = ' '.join(task_keywords)
        
        # Route using existing logic
        container = self.route_task(
            task_description=task_desc,
            tool_name=preferred_tool
        )
        
        # Calculate confidence score
        confidence = 0.5  # Base confidence
        
        # Increase confidence if tool match
        if preferred_tool and preferred_tool.lower() in self.CONTAINER_MAPPINGS:
            confidence = 0.9
        
        # Increase confidence if strong category match
        category = self._detect_category(task_desc)
        if category:
            # Count pattern matches
            matches = sum(
                1 for pattern in self.TASK_PATTERNS.get(category, [])
                if re.search(pattern, task_desc, re.IGNORECASE)
            )
            confidence = min(0.5 + (matches * 0.15), 0.95)
        
        return container, confidence
    
    def get_available_tools_in_container(self, container_name: str) -> List[str]:
        """
        Get list of available tools in a container.
        
        Args:
            container_name: Name of container
        
        Returns:
            List of tool names
        """
        # Get container category from labels
        info = self.get_container_info(container_name)
        if not info.get('available'):
            return []
        
        category = info.get('category', 'unknown')
        tool = info.get('tool', 'unknown')
        
        # Return known tools for this container
        # This could be enhanced to actually query the container
        return [tool] if tool != 'unknown' else []
    
    def close(self):
        """Close Docker client connection."""
        if self.docker_client:
            self.docker_client.close()
            logger.info("ContainerManager connection closed")


# Convenience functions for common routing scenarios

def route_reconnaissance_task(subdomain: bool = False, email: bool = False) -> str:
    """Route reconnaissance task to appropriate container."""
    manager = ContainerManager()
    
    if subdomain:
        return 'ats_recon_amass'
    elif email:
        return 'ats_recon_harvester'
    else:
        return 'ats_recon_nuclei'


def route_web_testing_task(proxy: bool = False) -> str:
    """Route web testing task to appropriate container."""
    if proxy:
        return 'ats_web_zap'
    else:
        return 'ats_web_nikto'


def route_network_scan_task(fast: bool = False) -> str:
    """Route network scanning task to appropriate container."""
    if fast:
        return 'ats_network_masscan'
    else:
        return 'ats_network_nmap'


__all__ = [
    'ContainerManager',
    'ContainerCategory',
    'route_reconnaissance_task',
    'route_web_testing_task',
    'route_network_scan_task',
]