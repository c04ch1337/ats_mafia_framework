"""
Metasploit Remote Tool
Execute Metasploit Framework via Kali container.
"""

import re
from typing import Dict, List, Optional
import logging

from ...sandbox.kali_connector import KaliConnector

logger = logging.getLogger(__name__)


class MetasploitRemoteTool:
    """Execute Metasploit Framework in Kali sandbox."""
    
    def __init__(self):
        self.name = "metasploit_remote"
        self.description = "Real Metasploit Framework via Kali container - exploitation platform"
        self.category = "exploitation"
        self.risk_level = "CRITICAL_RISK"
        self.requires_sandbox = True
        self.kali = None
    
    def _ensure_connector(self):
        """Ensure Kali connector is initialized."""
        if self.kali is None:
            self.kali = KaliConnector()
    
    def search_exploit(self, search_term: str) -> Dict[str, any]:
        """
        Search for exploits in Metasploit database.
        
        Args:
            search_term: Search term for exploits
            
        Returns:
            Dict containing search results
        """
        self._ensure_connector()
        
        command = f'msfconsole -q -x "search {search_term}; exit"'
        
        logger.info(f"Searching Metasploit: {search_term}")
        
        try:
            result = self.kali.execute_command(command, timeout=120)
            
            if result['success']:
                exploits = self._parse_search_results(result['stdout'])
                return {
                    'success': True,
                    'tool': 'metasploit',
                    'action': 'search',
                    'search_term': search_term,
                    'exploits': exploits,
                    'raw_output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'tool': 'metasploit',
                    'error': result['stderr']
                }
                
        except Exception as e:
            logger.error(f"Metasploit search failed: {e}")
            return {
                'success': False,
                'tool': 'metasploit',
                'error': str(e)
            }
    
    def get_exploit_info(self, exploit_path: str) -> Dict[str, any]:
        """
        Get detailed information about an exploit.
        
        Args:
            exploit_path: Path to exploit module
            
        Returns:
            Dict containing exploit information
        """
        self._ensure_connector()
        
        command = f'msfconsole -q -x "use {exploit_path}; info; exit"'
        
        logger.info(f"Getting info for: {exploit_path}")
        
        try:
            result = self.kali.execute_command(command, timeout=60)
            
            if result['success']:
                return {
                    'success': True,
                    'tool': 'metasploit',
                    'action': 'info',
                    'exploit': exploit_path,
                    'info': result['stdout'],
                    'raw_output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'tool': 'metasploit',
                    'error': result['stderr']
                }
                
        except Exception as e:
            logger.error(f"Metasploit info failed: {e}")
            return {
                'success': False,
                'tool': 'metasploit',
                'error': str(e)
            }
    
    def _parse_search_results(self, output: str) -> List[Dict[str, str]]:
        """Parse msfconsole search results."""
        exploits = []
        
        # Pattern: exploit/platform/name  date  Rank  Description
        pattern = r'(exploit/[\w/]+)\s+(\d{4}-\d{2}-\d{2})\s+(\w+)\s+(.+)'
        
        for match in re.finditer(pattern, output):
            path, date, rank, description = match.groups()
            exploits.append({
                'path': path.strip(),
                'date': date,
                'rank': rank,
                'description': description.strip()
            })
        
        return exploits


__all__ = ['MetasploitRemoteTool']