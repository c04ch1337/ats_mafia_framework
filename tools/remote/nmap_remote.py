"""
Nmap Remote Tool
Execute real nmap scanning via Kali container.
"""

import re
import json
from typing import Dict, List, Optional
import logging

from ...sandbox.kali_connector import KaliConnector
from ...core.tool_system import Tool, ToolCategory, ToolRiskLevel

logger = logging.getLogger(__name__)


class NmapRemoteTool(Tool):
    """Execute real nmap scanning in Kali sandbox."""
    
    def __init__(self):
        super().__init__(
            name="nmap_remote",
            description="Real nmap port scanner via Kali container - performs actual network reconnaissance",
            category=ToolCategory.RECONNAISSANCE,
            risk_level=ToolRiskLevel.MEDIUM_RISK,
            requires_approval=True
        )
        self.kali = None
        self.requires_sandbox = True
    
    def _ensure_connector(self):
        """Ensure Kali connector is initialized."""
        if self.kali is None:
            self.kali = KaliConnector()
    
    def execute(
        self,
        target: str,
        scan_type: str = 'syn',
        ports: Optional[str] = None,
        options: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Execute nmap scan against target.
        
        Args:
            target: Target IP address or hostname
            scan_type: Type of scan (syn, tcp, udp, ping, etc.)
            ports: Port specification (e.g., "80,443" or "1-1000")
            options: Additional nmap options
            
        Returns:
            Dict containing scan results
        """
        self._ensure_connector()
        
        # Build nmap command
        cmd_parts = ['nmap']
        
        # Add scan type
        scan_flags = {
            'syn': '-sS',
            'tcp': '-sT',
            'udp': '-sU',
            'ping': '-sn',
            'version': '-sV',
            'os': '-O',
            'aggressive': '-A',
            'fast': '-F'
        }
        
        if scan_type in scan_flags:
            cmd_parts.append(scan_flags[scan_type])
        
        # Add port specification
        if ports:
            cmd_parts.append(f'-p {ports}')
        
        # Add additional options
        if options:
            for opt in options:
                # Sanitize each option
                safe_opt = re.sub(r'[;&|`$()]', '', opt)
                cmd_parts.append(safe_opt)
        
        # Add output format
        cmd_parts.append('-oX -')  # XML output to stdout
        
        # Add target
        cmd_parts.append(target)
        
        command = ' '.join(cmd_parts)
        
        logger.info(f"Executing nmap: {command}")
        
        try:
            result = self.kali.execute_command(command, timeout=600)
            
            if result['success']:
                parsed_results = self._parse_nmap_output(result['stdout'])
                return {
                    'success': True,
                    'tool': 'nmap',
                    'target': target,
                    'scan_type': scan_type,
                    'command': command,
                    'raw_output': result['stdout'],
                    'parsed': parsed_results,
                    'execution_time': result['execution_time']
                }
            else:
                return {
                    'success': False,
                    'tool': 'nmap',
                    'error': result['stderr'],
                    'command': command
                }
                
        except Exception as e:
            logger.error(f"Nmap execution failed: {e}")
            return {
                'success': False,
                'tool': 'nmap',
                'error': str(e),
                'command': command
            }
    
    def _parse_nmap_output(self, output: str) -> Dict[str, any]:
        """
        Parse nmap output for key information.
        
        Args:
            output: Raw nmap output
            
        Returns:
            Dict with parsed scan results
        """
        parsed = {
            'open_ports': [],
            'filtered_ports': [],
            'closed_ports': [],
            'host_status': 'unknown',
            'os_detection': None,
            'services': []
        }
        
        # Extract open ports
        port_pattern = r'(\d+)/(\w+)\s+open\s+(\w+)'
        for match in re.finditer(port_pattern, output):
            port_num, protocol, service = match.groups()
            parsed['open_ports'].append({
                'port': int(port_num),
                'protocol': protocol,
                'service': service
            })
        
        # Extract host status
        if 'Host is up' in output:
            parsed['host_status'] = 'up'
        elif 'Host seems down' in output:
            parsed['host_status'] = 'down'
        
        # Extract OS detection if present
        os_match = re.search(r'OS details: (.+)', output)
        if os_match:
            parsed['os_detection'] = os_match.group(1).strip()
        
        return parsed
    
    def quick_scan(self, target: str) -> Dict[str, any]:
        """Perform quick TCP SYN scan of common ports."""
        return self.execute(
            target=target,
            scan_type='syn',
            ports='21,22,23,25,80,110,139,143,443,445,3306,3389,8080',
            options=['-T4']
        )
    
    def full_scan(self, target: str) -> Dict[str, any]:
        """Perform comprehensive scan of all ports."""
        return self.execute(
            target=target,
            scan_type='syn',
            ports='1-65535',
            options=['-T4', '-A', '-v']
        )
    
    def version_scan(self, target: str, ports: str = None) -> Dict[str, any]:
        """Perform service version detection scan."""
        return self.execute(
            target=target,
            scan_type='version',
            ports=ports or '1-1000',
            options=['-T4']
        )


__all__ = ['NmapRemoteTool']