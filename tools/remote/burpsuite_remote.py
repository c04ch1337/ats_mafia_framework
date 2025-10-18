"""
BurpSuite Remote Tool
Execute BurpSuite web security scanner via Kali container.
"""

import re
from typing import Dict, List, Optional
import logging

from ...sandbox.kali_connector import KaliConnector

logger = logging.getLogger(__name__)


class BurpSuiteRemoteTool:
    """Execute BurpSuite web security testing in Kali sandbox."""
    
    def __init__(self):
        self.name = "burpsuite_remote"
        self.description = "Real BurpSuite web security scanner via Kali container"
        self.category = "web_testing"
        self.risk_level = "MEDIUM_RISK"
        self.requires_sandbox = True
        self.kali = None
    
    def _ensure_connector(self):
        """Ensure Kali connector is initialized."""
        if self.kali is None:
            self.kali = KaliConnector()
    
    def scan_url(
        self,
        url: str,
        scan_type: str = 'passive',
        **kwargs
    ) -> Dict[str, any]:
        """
        Execute BurpSuite scan against target URL.
        
        Note: This is a simplified implementation. Full BurpSuite typically
        requires GUI or professional edition with API access.
        
        Args:
            url: Target URL to scan
            scan_type: Type of scan (passive, active)
            
        Returns:
            Dict containing scan results
        """
        self._ensure_connector()
        
        # For demo purposes, we'll use nikto as a proxy for web scanning
        # since BurpSuite Pro is needed for CLI automation
        logger.info(f"Running web security scan on: {url}")
        
        command = f'nikto -h {url} -Format txt'
        
        try:
            result = self.kali.execute_command(command, timeout=600)
            
            if result['success']:
                parsed = self._parse_scan_output(result['stdout'])
                return {
                    'success': True,
                    'tool': 'burpsuite_proxy',
                    'url': url,
                    'scan_type': scan_type,
                    'command': command,
                    'raw_output': result['stdout'],
                    'parsed': parsed,
                    'execution_time': result['execution_time'],
                    'note': 'Using nikto as BurpSuite CLI alternative'
                }
            else:
                return {
                    'success': False,
                    'tool': 'burpsuite_proxy',
                    'error': result['stderr'],
                    'command': command
                }
                
        except Exception as e:
            logger.error(f"Web scan execution failed: {e}")
            return {
                'success': False,
                'tool': 'burpsuite_proxy',
                'error': str(e),
                'command': command
            }
    
    def _parse_scan_output(self, output: str) -> Dict[str, any]:
        """Parse web scanner output."""
        parsed = {
            'vulnerabilities': [],
            'total_tests': 0,
            'findings_count': 0
        }
        
        # Extract vulnerabilities from nikto output
        vuln_pattern = r'\+ (OSVDB-\d+): (.+)'
        for match in re.finditer(vuln_pattern, output):
            osvdb_id, description = match.groups()
            parsed['vulnerabilities'].append({
                'id': osvdb_id,
                'description': description.strip()
            })
        
        parsed['findings_count'] = len(parsed['vulnerabilities'])
        
        # Extract test count
        test_match = re.search(r'(\d+) items checked', output)
        if test_match:
            parsed['total_tests'] = int(test_match.group(1))
        
        return parsed
    
    def proxy_request(
        self,
        url: str,
        method: str = 'GET',
        data: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Send HTTP request through analysis.
        
        Args:
            url: Target URL
            method: HTTP method
            data: Request data
            headers: Custom headers
            
        Returns:
            Dict containing response
        """
        self._ensure_connector()
        
        # Use curl for HTTP requests
        cmd_parts = ['curl', '-i', '-X', method]
        
        if data:
            cmd_parts.append(f'-d "{data}"')
        
        if headers:
            for key, value in headers.items():
                cmd_parts.append(f'-H "{key}: {value}"')
        
        cmd_parts.append(f'"{url}"')
        command = ' '.join(cmd_parts)
        
        try:
            result = self.kali.execute_command(command, timeout=60)
            
            return {
                'success': result['success'],
                'tool': 'burpsuite_proxy',
                'action': 'proxy_request',
                'url': url,
                'method': method,
                'response': result['stdout'],
                'execution_time': result['execution_time']
            }
                
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            return {
                'success': False,
                'tool': 'burpsuite_proxy',
                'error': str(e)
            }


__all__ = ['BurpSuiteRemoteTool']