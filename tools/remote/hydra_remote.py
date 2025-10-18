"""
Hydra Remote Tool
Execute Hydra password cracking via Kali container.
"""

import re
from typing import Dict, List, Optional
import logging

from ...sandbox.kali_connector import KaliConnector

logger = logging.getLogger(__name__)


class HydraRemoteTool:
    """Execute Hydra password attacks in Kali sandbox."""
    
    def __init__(self):
        self.name = "hydra_remote"
        self.description = "Real Hydra password cracker via Kali container"
        self.category = "password"
        self.risk_level = "HIGH_RISK"
        self.requires_sandbox = True
        self.kali = None
    
    def _ensure_connector(self):
        """Ensure Kali connector is initialized."""
        if self.kali is None:
            self.kali = KaliConnector()
    
    def execute(
        self,
        target: str,
        service: str,
        username: Optional[str] = None,
        username_list: Optional[str] = None,
        password: Optional[str] = None,
        password_list: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Execute Hydra password attack.
        
        Args:
            target: Target IP or hostname
            service: Service to attack (ssh, ftp, http, etc.)
            username: Single username to test
            username_list: Path to username list
            password: Single password to test
            password_list: Path to password list
            port: Target port (optional)
            
        Returns:
            Dict containing attack results
        """
        self._ensure_connector()
        
        # Build hydra command
        cmd_parts = ['hydra']
        
        # Add username(s)
        if username:
            cmd_parts.append(f'-l {username}')
        elif username_list:
            cmd_parts.append(f'-L {username_list}')
        else:
            return {
                'success': False,
                'tool': 'hydra',
                'error': 'Either username or username_list is required'
            }
        
        # Add password(s)
        if password:
            cmd_parts.append(f'-p {password}')
        elif password_list:
            cmd_parts.append(f'-P {password_list}')
        else:
            return {
                'success': False,
                'tool': 'hydra',
                'error': 'Either password or password_list is required'
            }
        
        # Add port if specified
        if port:
            cmd_parts.append(f'-s {port}')
        
        # Add verbosity
        cmd_parts.append('-V')
        
        # Add target and service
        cmd_parts.append(f'{target} {service}')
        
        command = ' '.join(cmd_parts)
        
        logger.info(f"Executing Hydra: {command}")
        
        try:
            result = self.kali.execute_command(command, timeout=600)
            
            parsed = self._parse_hydra_output(result['stdout'])
            
            return {
                'success': result['success'],
                'tool': 'hydra',
                'target': target,
                'service': service,
                'command': command,
                'raw_output': result['stdout'],
                'parsed': parsed,
                'execution_time': result['execution_time']
            }
                
        except Exception as e:
            logger.error(f"Hydra execution failed: {e}")
            return {
                'success': False,
                'tool': 'hydra',
                'error': str(e),
                'command': command
            }
    
    def _parse_hydra_output(self, output: str) -> Dict[str, any]:
        """Parse Hydra output for credentials."""
        parsed = {
            'credentials_found': [],
            'attempts': 0,
            'status': 'unknown'
        }
        
        # Extract found credentials
        cred_pattern = r'\[(\w+)\]\[(\w+)\]\s+host:\s+([\d\.]+)\s+login:\s+(\w+)\s+password:\s+(\S+)'
        for match in re.finditer(cred_pattern, output):
            port, service, host, login, password = match.groups()
            parsed['credentials_found'].append({
                'host': host,
                'port': port,
                'service': service,
                'username': login,
                'password': password
            })
        
        # Extract attempts count
        attempt_match = re.search(r'(\d+)\s+of\s+(\d+)\s+target', output)
        if attempt_match:
            parsed['attempts'] = int(attempt_match.group(1))
        
        # Determine status
        if parsed['credentials_found']:
            parsed['status'] = 'credentials_found'
        elif 'completed' in output.lower():
            parsed['status'] = 'completed_no_credentials'
        else:
            parsed['status'] = 'running'
        
        return parsed


__all__ = ['HydraRemoteTool']