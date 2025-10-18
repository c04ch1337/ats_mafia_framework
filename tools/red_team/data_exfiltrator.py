"""
ATS MAFIA Framework - Data Exfiltrator Tool

Simulates data extraction and exfiltration techniques.
Demonstrates various covert channels and data staging for training.

SIMULATION ONLY - No actual data exfiltration performed.
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
class ExfiltrationResult:
    """Result of data exfiltration simulation."""
    target: str
    data_type: str
    data_size_mb: float
    channel: str
    compression_ratio: float
    encryption_used: bool
    estimated_time: float
    detection_probability: float
    staging_locations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'target': self.target,
            'data_type': self.data_type,
            'data_size_mb': self.data_size_mb,
            'exfiltration_channel': self.channel,
            'compression_ratio': self.compression_ratio,
            'encryption_used': self.encryption_used,
            'estimated_time_seconds': self.estimated_time,
            'detection_probability': self.detection_probability,
            'staging_locations': self.staging_locations
        }


class DataExfiltrator(Tool):
    """
    Simulated data exfiltration tool.
    
    Features:
    - File discovery and classification
    - Data compression and encryption
    - Covert channel selection (DNS, HTTPS, ICMP)
    - Bandwidth throttling to avoid detection
    
    IMPORTANT: This tool operates in SIMULATION MODE ONLY.
    """
    
    def __init__(self):
        """Initialize the data exfiltrator tool."""
        metadata = ToolMetadata(
            id="data_exfiltrator",
            name="Data Exfiltrator",
            description="Data extraction and exfiltration simulation",
            version="1.0.0",
            author="ATS MAFIA Team",
            tool_type=ToolType.PYTHON,
            category=ToolCategory.POST_EXPLOITATION,
            risk_level=ToolRiskLevel.HIGH_RISK,
            tags=["exfiltration", "data-theft", "covert-channel"],
            permissions_required=[PermissionLevel.ADMIN],
            dependencies=[],
            simulation_only=True,
            config_schema={
                "target": {
                    "type": "string",
                    "required": True
                },
                "data_type": {
                    "type": "string",
                    "enum": ["documents", "credentials", "database", "emails", "source_code"],
                    "default": "documents"
                },
                "channel": {
                    "type": "string",
                    "enum": ["https", "dns", "icmp", "ftp", "smb"],
                    "default": "https"
                },
                "compress": {
                    "type": "boolean",
                    "default": True
                },
                "encrypt": {
                    "type": "boolean",
                    "default": True
                },
                "throttle_mbps": {
                    "type": "number",
                    "default": 1.0,
                    "description": "Bandwidth limit in Mbps"
                }
            }
        )
        
        super().__init__(metadata)
        self.logger = logging.getLogger("tool.data_exfiltrator")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters."""
        return 'target' in parameters
    
    async def execute(self,
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """Execute data exfiltration simulation."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            if not self.validate_parameters(parameters):
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Invalid parameters"
                )
            
            target = parameters['target']
            data_type = parameters.get('data_type', 'documents')
            channel = parameters.get('channel', 'https')
            compress = parameters.get('compress', True)
            encrypt = parameters.get('encrypt', True)
            throttle = parameters.get('throttle_mbps', 1.0)
            
            self.logger.warning("⚠️  SIMULATION MODE - No actual data exfiltration")
            self.logger.info(f"[SIMULATION] Exfiltrating {data_type} from {target} via {channel}")
            
            result = await self._simulate_exfiltration(
                target, data_type, channel, compress, encrypt, throttle
            )
            
            execution_time = time.time() - start_time
            
            result_data = result.to_dict()
            result_data['simulation_mode'] = True
            result_data['disclaimer'] = 'SIMULATION ONLY - No actual data transferred'
            
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
    
    async def _simulate_exfiltration(self, target: str, data_type: str, channel: str,
                                    compress: bool, encrypt: bool, throttle: float) -> ExfiltrationResult:
        """Simulate data exfiltration."""
        await asyncio.sleep(random.uniform(1.5, 2.5))
        
        # Simulate data sizes by type (in MB)
        data_sizes = {
            'documents': random.uniform(50, 500),
            'credentials': random.uniform(1, 10),
            'database': random.uniform(100, 2000),
            'emails': random.uniform(200, 1000),
            'source_code': random.uniform(50, 300)
        }
        
        data_size = data_sizes[data_type]
        
        # Apply compression
        compression_ratio = random.uniform(0.4, 0.7) if compress else 1.0
        compressed_size = data_size * compression_ratio
        
        # Estimate transfer time based on throttle
        estimated_time = (compressed_size * 8) / throttle  # Convert MB to Mb and divide by Mbps
        
        # Calculate detection probability
        detection_prob = {
            'https': 0.2,
            'dns': 0.4,
            'icmp': 0.5,
            'ftp': 0.6,
            'smb': 0.3
        }[channel]
        
        if not encrypt:
            detection_prob += 0.3
        if throttle < 0.5:
            detection_prob -= 0.1
        
        detection_prob = max(0.1, min(0.9, detection_prob))
        
        staging_locations = [
            f"/tmp/staged_{data_type}_{i}.dat" for i in range(1, random.randint(2, 5))
        ]
        
        return ExfiltrationResult(
            target=target,
            data_type=data_type,
            data_size_mb=data_size,
            channel=channel,
            compression_ratio=compression_ratio,
            encryption_used=encrypt,
            estimated_time=estimated_time,
            detection_probability=detection_prob,
            staging_locations=staging_locations
        )


def create_tool() -> DataExfiltrator:
    """Create an instance of the DataExfiltrator tool."""
    return DataExfiltrator()