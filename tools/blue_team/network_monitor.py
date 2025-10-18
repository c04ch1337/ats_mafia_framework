"""
ATS MAFIA Framework - Network Monitor Tool

Real-time network surveillance and anomaly detection for blue team operations.
Monitors traffic, detects intrusions, and analyzes network health.

SIMULATION ONLY - Provides simulated monitoring data.
"""

import asyncio
import random
import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass, field
import uuid

from ...core.tool_system import (
    Tool, ToolMetadata, ToolExecutionResult, ToolType,
    PermissionLevel, ToolCategory, ToolRiskLevel
)


@dataclass
class NetworkMonitorResult:
    """Result of network monitoring."""
    duration_seconds: float
    packets_analyzed: int
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    bandwidth_stats: Dict[str, float] = field(default_factory=dict)
    protocol_distribution: Dict[str, int] = field(default_factory=dict)
    suspicious_ips: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'monitoring_duration': self.duration_seconds,
            'packets_analyzed': self.packets_analyzed,
            'anomalies_detected': self.anomalies_detected,
            'bandwidth_statistics': self.bandwidth_stats,
            'protocol_distribution': self.protocol_distribution,
            'suspicious_ips': self.suspicious_ips,
            'security_alerts': self.alerts
        }


class NetworkMonitor(Tool):
    """
    Real-time network monitoring and analysis tool.
    
    Features:
    - Traffic analysis and anomaly detection
    - Protocol analysis
    - Intrusion detection
    - Bandwidth monitoring
    
    IMPORTANT: This tool operates in SIMULATION MODE ONLY.
    """
    
    def __init__(self):
        """Initialize the network monitor tool."""
        metadata = ToolMetadata(
            id="network_monitor",
            name="Network Monitor",
            description="Real-time network surveillance and anomaly detection",
            version="1.0.0",
            author="ATS MAFIA Team",
            tool_type=ToolType.PYTHON,
            category=ToolCategory.MONITORING,
            risk_level=ToolRiskLevel.SAFE,
            tags=["monitoring", "network", "ids", "traffic-analysis"],
            permissions_required=[PermissionLevel.READ],
            dependencies=[],
            simulation_only=True,
            config_schema={
                "interface": {
                    "type": "string",
                    "default": "eth0",
                    "description": "Network interface to monitor"
                },
                "duration": {
                    "type": "number",
                    "default": 60,
                    "description": "Monitoring duration in seconds"
                },
                "alert_threshold": {
                    "type": "number",
                    "default": 0.8,
                    "description": "Anomaly detection threshold (0-1)"
                },
                "protocols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["tcp", "udp", "icmp"],
                    "description": "Protocols to monitor"
                }
            }
        )
        
        super().__init__(metadata)
        self.logger = logging.getLogger("tool.network_monitor")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters."""
        return True  # All parameters are optional
    
    async def execute(self,
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """Execute network monitoring simulation."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            interface = parameters.get('interface', 'eth0')
            duration = parameters.get('duration', 60)
            threshold = parameters.get('alert_threshold', 0.8)
            protocols = parameters.get('protocols', ['tcp', 'udp', 'icmp'])
            
            self.logger.info(f"[SIMULATION] Starting network monitoring on {interface}")
            self.logger.info(f"Monitoring for {duration} seconds")
            
            result = await self._simulate_monitoring(interface, duration, threshold, protocols)
            
            execution_time = time.time() - start_time
            
            result_data = result.to_dict()
            result_data['simulation_mode'] = True
            result_data['disclaimer'] = 'SIMULATION - Simulated network data'
            
            self.logger.info(f"[SIMULATION] Monitoring complete - {len(result.anomalies_detected)} anomalies detected")
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=result_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _simulate_monitoring(self, interface: str, duration: float,
                                   threshold: float, protocols: List[str]) -> NetworkMonitorResult:
        """Simulate network monitoring."""
        await asyncio.sleep(min(duration / 30, 2.0))  # Shortened simulation time
        
        # Simulate packet analysis
        packets_analyzed = int(random.uniform(10000, 50000) * (duration / 60))
        
        # Simulate bandwidth stats
        bandwidth_stats = {
            'average_mbps': random.uniform(50, 500),
            'peak_mbps': random.uniform(500, 1000),
            'total_mb': random.uniform(3000, 15000)
        }
        
        # Simulate protocol distribution
        protocol_dist = {}
        for proto in protocols:
            protocol_dist[proto] = random.randint(1000, 10000)
        
        # Simulate anomalies
        num_anomalies = random.randint(0, 5)
        anomalies = []
        for i in range(num_anomalies):
            anomalies.append({
                'type': random.choice(['port_scan', 'dos_attempt', 'unusual_traffic', 'protocol_violation']),
                'severity': random.choice(['low', 'medium', 'high']),
                'source_ip': f"192.168.1.{random.randint(1, 254)}",
                'timestamp': time.time() - random.uniform(0, duration)
            })
        
        # Simulate suspicious IPs
        suspicious_ips = [f"10.0.0.{random.randint(1, 254)}" for _ in range(random.randint(0, 3))]
        
        # Simulate alerts
        alerts = []
        for anomaly in anomalies:
            if anomaly['severity'] in ['high', 'medium']:
                alerts.append({
                    'alert_type': anomaly['type'],
                    'severity': anomaly['severity'],
                    'message': f"Detected {anomaly['type']} from {anomaly['source_ip']}",
                    'recommended_action': 'Investigate and block if confirmed malicious'
                })
        
        return NetworkMonitorResult(
            duration_seconds=duration,
            packets_analyzed=packets_analyzed,
            anomalies_detected=anomalies,
            bandwidth_stats=bandwidth_stats,
            protocol_distribution=protocol_dist,
            suspicious_ips=suspicious_ips,
            alerts=alerts
        )


def create_tool() -> NetworkMonitor:
    """Create an instance of the NetworkMonitor tool."""
    return NetworkMonitor()