"""
SQLMap Remote Tool
Execute real SQLMap via Kali container for SQL injection testing.
"""

import re
from typing import Dict, List, Optional
import logging

from ...sandbox.kali_connector import KaliConnector

logger = logging.getLogger(__name__)


class SqlmapRemoteTool:
    """Execute real SQLMap SQL injection testing in Kali sandbox."""
    
    def __init__(self):
        self.name = "sqlmap_remote"
        self.description = "Real SQLMap SQL injection scanner via Kali container"
        self.category = "web_testing"
        self.risk_level = "HIGH_RISK"
        self.requires_sandbox = True
        self.kali = None
    
    def _ensure_connector(self):
        """Ensure Kali connector is initialized."""
        if self.kali is None:
            self.kali = KaliConnector()
    
    def execute(
        self,
        url: str,
        data: Optional[str] = None,
        cookie: Optional[str] = None,
        level: int = 1,
        risk: int = 1,
        **kwargs
    ) -> Dict[str, any]:
        """
        Execute SQLMap scan against target URL.
        
        Args:
            url: Target URL
            data: POST data (optional)
            cookie: Cookie data (optional)
            level: Test level (1-5)
            risk: Risk level (1-3)
            
        Returns:
            Dict containing scan results
        """
        self._ensure_connector()
        
        # Build sqlmap command
        cmd_parts = ['sqlmap']
        
        # Add URL
        cmd_parts.append(f'-u "{url}"')
        
        # Add POST data if provided
        if data:
            cmd_parts.append(f'--data="{data}"')
        
        # Add cookie if provided
        if cookie:
            cmd_parts.append(f'--cookie="{cookie}"')
        
        # Add level and risk
        cmd_parts.append(f'--level={min(level, 5)}')
        cmd_parts.append(f'--risk={min(risk, 3)}')
        
        # Add batch mode (no user interaction)
        cmd_parts.append('--batch')
        
        # Add output to /tmp
        cmd_parts.append('--output-dir=/tmp/sqlmap')
        
        command = ' '.join(cmd_parts)
        
        logger.info(f"Executing SQLMap: {command}")
        
        try:
            result = self.kali.execute_command(command, timeout=900)
            
            if result['success']:
                parsed = self._parse_sqlmap_output(result['stdout'])
                return {
                    'success': True,
                    'tool': 'sqlmap',
                    'url': url,
                    'command': command,
                    'raw_output': result['stdout'],
                    'parsed': parsed,
                    'execution_time': result['execution_time']
                }
            else:
                return {
                    'success': False,
                    'tool': 'sqlmap',
                    'error': result['stderr'],
                    'command': command
                }
                
        except Exception as e:
            logger.error(f"SQLMap execution failed: {e}")
            return {
                'success': False,
                'tool': 'sqlmap',
                'error': str(e),
                'command': command
            }
    
    def _parse_sqlmap_output(self, output: str) -> Dict[str, any]:
        """Parse SQLMap output."""
        parsed = {
            'vulnerable': False,
            'injection_points': [],
            'databases': [],
            'tables': [],
            'findings': []
        }
        
        # Check if vulnerable
        if 'vulnerable' in output.lower():
            parsed['vulnerable'] = True
        
        # Extract injection points
        injection_pattern = r'Parameter: (\w+) \((\w+)\)'
        for match in re.finditer(injection_pattern, output):
            param, type_inj = match.groups()
            parsed['injection_points'].append({
                'parameter': param,
                'type': type_inj
            })
        
        return parsed


__all__ = ['SqlmapRemoteTool']