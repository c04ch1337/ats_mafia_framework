"""
ATS MAFIA Framework Network Scanner Tool

This module implements a network scanning tool for reconnaissance activities
in training scenarios. It provides comprehensive network discovery and
service enumeration capabilities.
"""

import asyncio
import socket
import subprocess
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import ipaddress
import logging

from ..core.tool_system import Tool, ToolMetadata, ToolExecutionResult, ToolType, PermissionLevel
from ..core.profile_manager import SkillLevel


@dataclass
class ScanResult:
    """Result of a network scan."""
    target: str
    is_alive: bool
    open_ports: List[int] = None
    services: Dict[int, str] = None
    os_fingerprint: Optional[str] = None
    scan_time: float = 0.0
    
    def __post_init__(self):
        """Initialize result after dataclass creation."""
        if self.open_ports is None:
            self.open_ports = []
        if self.services is None:
            self.services = {}


class NetworkScanner(Tool):
    """
    Network scanning tool for reconnaissance and enumeration.
    
    Provides comprehensive network discovery capabilities including host discovery,
    port scanning, service enumeration, and OS fingerprinting.
    """
    
    def __init__(self):
        """Initialize the network scanner tool."""
        metadata = ToolMetadata(
            id="network_scanner",
            name="Network Scanner",
            description="Comprehensive network scanning and reconnaissance tool",
            version="1.0.0",
            author="ATS MAFIA Team",
            tool_type=ToolType.PYTHON,
            category="reconnaissance",
            tags=["network", "scanning", "reconnaissance", "enumeration"],
            permissions_required=[PermissionLevel.READ, PermissionLevel.EXECUTE],
            dependencies=["python-nmap", "scapy"],
            config_schema={
                "scan_type": {
                    "type": "string",
                    "enum": ["ping", "port", "service", "comprehensive"],
                    "default": "comprehensive"
                },
                "target_range": {
                    "type": "string",
                    "description": "Target IP range (e.g., 192.168.1.0/24)"
                },
                "ports": {
                    "type": "array",
                    "description": "Ports to scan (default: common ports)",
                    "default": [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306]
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout per port in seconds",
                    "default": 3.0
                },
                "max_threads": {
                    "type": "number",
                    "description": "Maximum concurrent threads",
                    "default": 50
                },
                "stealth_mode": {
                    "type": "boolean",
                    "description": "Enable stealth scanning techniques",
                    "default": False
                }
            },
            documentation="Network scanner for host discovery, port scanning, and service enumeration",
            examples=[
                {
                    "name": "Basic Network Scan",
                    "parameters": {
                        "target_range": "192.168.1.0/24",
                        "scan_type": "comprehensive"
                    }
                },
                {
                    "name": "Quick Ping Sweep",
                    "parameters": {
                        "target_range": "10.0.0.1-254",
                        "scan_type": "ping"
                    }
                }
            ]
        )
        
        super().__init__(metadata)
        self.logger = logging.getLogger("tool.network_scanner")
        
        # Common ports for scanning
        self.common_ports = [
            21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
            1433, 3306, 3389, 5432, 5900, 8080, 8443
        ]
        
        # Service mapping
        self.service_map = {
            21: "ftp",
            22: "ssh",
            23: "telnet",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            143: "imap",
            443: "https",
            993: "imaps",
            995: "pop3s",
            1433: "mssql",
            3306: "mysql",
            3389: "rdp",
            5432: "postgresql",
            5900: "vnc",
            8080: "http-alt",
            8443: "https-alt"
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate scan parameters.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        required_params = ['target_range']
        
        for param in required_params:
            if param not in parameters:
                self.logger.error(f"Missing required parameter: {param}")
                return False
        
        # Validate target range
        try:
            ipaddress.ip_network(parameters['target_range'], strict=False)
        except ValueError:
            self.logger.error(f"Invalid target range: {parameters['target_range']}")
            return False
        
        # Validate scan type
        valid_scan_types = ['ping', 'port', 'service', 'comprehensive']
        scan_type = parameters.get('scan_type', 'comprehensive')
        if scan_type not in valid_scan_types:
            self.logger.error(f"Invalid scan type: {scan_type}")
            return False
        
        return True
    
    async def execute(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the network scan.
        
        Args:
            parameters: Scan parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        execution_id = context.get('execution_id', 'unknown')
        start_time = time.time()
        
        try:
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Invalid parameters"
                )
            
            # Extract parameters
            target_range = parameters['target_range']
            scan_type = parameters.get('scan_type', 'comprehensive')
            ports = parameters.get('ports', self.common_ports)
            timeout = parameters.get('timeout', 3.0)
            max_threads = parameters.get('max_threads', 50)
            stealth_mode = parameters.get('stealth_mode', False)
            
            self.logger.info(f"Starting {scan_type} scan of {target_range}")
            
            # Perform scan based on type
            if scan_type == 'ping':
                results = await self._ping_sweep(target_range, max_threads)
            elif scan_type == 'port':
                results = await self._port_scan(target_range, ports, timeout, max_threads)
            elif scan_type == 'service':
                results = await self._service_scan(target_range, ports, timeout, max_threads)
            else:  # comprehensive
                results = await self._comprehensive_scan(
                    target_range, ports, timeout, max_threads, stealth_mode
                )
            
            execution_time = time.time() - start_time
            
            # Format results
            formatted_results = {
                'scan_type': scan_type,
                'target_range': target_range,
                'scan_time': execution_time,
                'targets_scanned': len(results),
                'live_hosts': len([r for r in results if r.is_alive]),
                'results': [self._format_scan_result(r) for r in results],
                'summary': self._generate_summary(results)
            }
            
            self.logger.info(f"Scan completed in {execution_time:.2f} seconds")
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=formatted_results,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Network scan failed: {e}")
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _ping_sweep(self, target_range: str, max_threads: int) -> List[ScanResult]:
        """
        Perform ping sweep to discover live hosts.
        
        Args:
            target_range: Target IP range
            max_threads: Maximum concurrent threads
            
        Returns:
            List of scan results
        """
        network = ipaddress.ip_network(target_range, strict=False)
        results = []
        
        # Create semaphore to limit concurrent threads
        semaphore = asyncio.Semaphore(max_threads)
        
        async def ping_host(ip: str) -> ScanResult:
            """Ping a single host."""
            async with semaphore:
                result = ScanResult(target=str(ip), is_alive=False)
                
                try:
                    # Use ping command (platform-specific)
                    if os.name == 'nt':  # Windows
                        cmd = ['ping', '-n', '1', '-w', '1000', str(ip)]
                    else:  # Unix/Linux
                        cmd = ['ping', '-c', '1', '-W', '1', str(ip)]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await process.wait()
                    
                    if process.returncode == 0:
                        result.is_alive = True
                        
                except Exception as e:
                    self.logger.debug(f"Error pinging {ip}: {e}")
                
                return result
        
        # Create tasks for all hosts
        tasks = [ping_host(str(ip)) for ip in network.hosts()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, ScanResult):
                valid_results.append(result)
            else:
                self.logger.error(f"Ping scan error: {result}")
        
        return valid_results
    
    async def _port_scan(self, target_range: str, ports: List[int], 
                        timeout: float, max_threads: int) -> List[ScanResult]:
        """
        Perform port scan on target range.
        
        Args:
            target_range: Target IP range
            ports: Ports to scan
            timeout: Connection timeout
            max_threads: Maximum concurrent threads
            
        Returns:
            List of scan results
        """
        network = ipaddress.ip_network(target_range, strict=False)
        results = []
        
        # First do ping sweep to find live hosts
        live_hosts = await self._ping_sweep(target_range, max_threads)
        live_ips = [r.target for r in live_hosts if r.is_alive]
        
        if not live_ips:
            return live_hosts
        
        # Create semaphore to limit concurrent threads
        semaphore = asyncio.Semaphore(max_threads)
        
        async def scan_port(ip: str, port: int) -> Optional[tuple]:
            """Scan a single port on a single host."""
            async with semaphore:
                try:
                    future = asyncio.open_connection(ip, port)
                    reader, writer = await asyncio.wait_for(future, timeout=timeout)
                    writer.close()
                    await writer.wait_closed()
                    return (ip, port)
                except:
                    return None
        
        # Create tasks for all host/port combinations
        tasks = []
        for ip in live_ips:
            for port in ports:
                tasks.append(scan_port(ip, port))
        
        scan_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        host_results = {ip: ScanResult(target=ip, is_alive=True) for ip in live_ips}
        
        for result in scan_results:
            if isinstance(result, tuple):
                ip, port = result
                host_results[ip].open_ports.append(port)
                host_results[ip].services[port] = self.service_map.get(port, "unknown")
        
        return list(host_results.values())
    
    async def _service_scan(self, target_range: str, ports: List[int],
                           timeout: float, max_threads: int) -> List[ScanResult]:
        """
        Perform detailed service detection.
        
        Args:
            target_range: Target IP range
            ports: Ports to scan
            timeout: Connection timeout
            max_threads: Maximum concurrent threads
            
        Returns:
            List of scan results
        """
        # Start with port scan
        port_results = await self._port_scan(target_range, ports, timeout, max_threads)
        
        # Enhance with service detection
        for result in port_results:
            if result.is_alive and result.open_ports:
                await self._detect_services(result, timeout)
        
        return port_results
    
    async def _detect_services(self, result: ScanResult, timeout: float) -> None:
        """
        Detect services on open ports.
        
        Args:
            result: Scan result to enhance
            timeout: Connection timeout
        """
        for port in result.open_ports:
            try:
                # Connect to the service
                future = asyncio.open_connection(result.target, port)
                reader, writer = await asyncio.wait_for(future, timeout=timeout)
                
                # Send service-specific probes
                service_info = await self._probe_service(reader, writer, port)
                if service_info:
                    result.services[port] = service_info
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                self.logger.debug(f"Service detection failed for {result.target}:{port} - {e}")
    
    async def _probe_service(self, reader: asyncio.StreamReader, 
                           writer: asyncio.StreamWriter, port: int) -> Optional[str]:
        """
        Probe a service to identify it.
        
        Args:
            reader: Stream reader
            writer: Stream writer
            port: Port number
            
        Returns:
            Service identification string
        """
        try:
            # Service-specific probes
            if port == 80 or port == 8080:
                writer.write(b"GET / HTTP/1.0\r\n\r\n")
                await writer.drain()
                response = await reader.read(1024)
                if b"Server:" in response:
                    server_line = response.split(b"Server:")[1].split(b"\r\n")[0]
                    return f"http/{server_line.decode().strip()}"
                return "http"
            
            elif port == 443 or port == 8443:
                return "https"
            
            elif port == 22:
                return "ssh"
            
            elif port == 21:
                writer.write(b"HELP\r\n")
                await writer.drain()
                response = await reader.read(1024)
                if b"FTP" in response:
                    return "ftp"
            
            elif port == 25:
                writer.write(b"EHLO test\r\n")
                await writer.drain()
                response = await reader.read(1024)
                if b"SMTP" in response:
                    return "smtp"
            
            elif port == 53:
                return "dns"
            
            return self.service_map.get(port, "unknown")
            
        except Exception:
            return self.service_map.get(port, "unknown")
    
    async def _comprehensive_scan(self, target_range: str, ports: List[int],
                                 timeout: float, max_threads: int, stealth_mode: bool) -> List[ScanResult]:
        """
        Perform comprehensive network scan.
        
        Args:
            target_range: Target IP range
            ports: Ports to scan
            timeout: Connection timeout
            max_threads: Maximum concurrent threads
            stealth_mode: Enable stealth techniques
            
        Returns:
            List of scan results
        """
        self.logger.info(f"Starting comprehensive scan of {target_range}")
        
        # Start with service scan
        results = await self._service_scan(target_range, ports, timeout, max_threads)
        
        # Add OS fingerprinting for live hosts
        for result in results:
            if result.is_alive and result.open_ports:
                result.os_fingerprint = await self._os_fingerprint(result.target, timeout)
        
        return results
    
    async def _os_fingerprint(self, ip: str, timeout: float) -> Optional[str]:
        """
        Perform basic OS fingerprinting.
        
        Args:
            ip: Target IP address
            timeout: Connection timeout
            
        Returns:
            OS fingerprint string
        """
        try:
            # Try TTL-based OS detection
            future = asyncio.create_subprocess_exec(
                'ping', '-c', '1', str(ip),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            process = await future
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode()
                if "ttl=" in output.lower():
                    ttl_line = [line for line in output.split('\n') if 'ttl=' in line.lower()]
                    if ttl_line:
                        ttl_str = ttl_line[0].split('ttl=')[1].split()[0]
                        ttl = int(ttl_str)
                        
                        # Basic TTL-based OS detection
                        if ttl <= 64:
                            return "Linux/Unix"
                        elif ttl <= 128:
                            return "Windows"
                        else:
                            return "Cisco/Network Device"
            
            return "Unknown"
            
        except Exception as e:
            self.logger.debug(f"OS fingerprinting failed for {ip}: {e}")
            return "Unknown"
    
    def _format_scan_result(self, result: ScanResult) -> Dict[str, Any]:
        """
        Format scan result for output.
        
        Args:
            result: Scan result to format
            
        Returns:
            Formatted result dictionary
        """
        return {
            'target': result.target,
            'is_alive': result.is_alive,
            'open_ports': result.open_ports,
            'services': result.services,
            'os_fingerprint': result.os_fingerprint,
            'scan_time': result.scan_time
        }
    
    def _generate_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """
        Generate scan summary statistics.
        
        Args:
            results: List of scan results
            
        Returns:
            Summary statistics dictionary
        """
        total_hosts = len(results)
        live_hosts = len([r for r in results if r.is_alive])
        total_ports = sum(len(r.open_ports) for r in results)
        
        service_counts = {}
        for result in results:
            for service in result.services.values():
                service_counts[service] = service_counts.get(service, 0) + 1
        
        os_counts = {}
        for result in results:
            if result.os_fingerprint:
                os_counts[result.os_fingerprint] = os_counts.get(result.os_fingerprint, 0) + 1
        
        return {
            'total_hosts_scanned': total_hosts,
            'live_hosts_found': live_hosts,
            'dead_hosts': total_hosts - live_hosts,
            'total_open_ports': total_ports,
            'most_common_services': sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'operating_systems': os_counts,
            'scan_efficiency': (live_hosts / total_hosts * 100) if total_hosts > 0 else 0
        }


# Tool factory function
def create_tool() -> NetworkScanner:
    """
    Create an instance of the NetworkScanner tool.
    
    Returns:
        NetworkScanner instance
    """
    return NetworkScanner()


# Tool execution function for compatibility
def execute(parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolExecutionResult:
    """
    Execute the network scanner tool.
    
    Args:
        parameters: Tool parameters
        context: Execution context
        
    Returns:
        Tool execution result
    """
    tool = NetworkScanner()
    return asyncio.run(tool.execute(parameters, context))