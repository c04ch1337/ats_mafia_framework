"""
ATS MAFIA Framework - Pretext Generator Tool

Creates believable pretexts for social engineering scenarios.
SIMULATION ONLY - For training purposes.
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
class PretextProfile:
    """Generated pretext profile."""
    role: str
    organization: str
    backstory: str
    credentials: Dict[str, str] = field(default_factory=dict)
    talking_points: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'assumed_role': self.role,
            'organization': self.organization,
            'backstory': self.backstory,
            'fabricated_credentials': self.credentials,
            'key_talking_points': self.talking_points
        }


class PretextGenerator(Tool):
    """Pretext generation tool for social engineering."""
    
    def __init__(self):
        metadata = ToolMetadata(
            id="pretext_generator",
            name="Pretext Generator",
            description="Create believable pretexts for social engineering",
            version="1.0.0",
            author="ATS MAFIA Team",
            tool_type=ToolType.PYTHON,
            category=ToolCategory.SOCIAL_ENGINEERING,
            risk_level=ToolRiskLevel.MEDIUM_RISK,
            tags=["social-engineering", "pretext", "persona"],
            permissions_required=[PermissionLevel.EXECUTE],
            dependencies=[],
            simulation_only=True,
            config_schema={
                "scenario": {
                    "type": "string",
                    "enum": ["it_support", "vendor", "executive", "auditor"],
                    "required": True
                }
            }
        )
        super().__init__(metadata)
        self.logger = logging.getLogger("tool.pretext_generator")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return 'scenario' in parameters
    
    async def execute(self, parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            scenario = parameters['scenario']
            self.logger.info(f"[SIMULATION] Generating {scenario} pretext")
            result = await self._simulate_pretext(scenario)
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result={**result.to_dict(), 'simulation_mode': True,
                       'disclaimer': 'For training purposes only'},
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _simulate_pretext(self, scenario: str) -> PretextProfile:
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        pretexts = {
            'it_support': {
                'role': 'IT Support Technician',
                'org': 'IT Help Desk',
                'story': 'Calling to verify security update installation',
                'creds': {'employee_id': 'IT-12345', 'dept': 'IT Operations'},
                'points': ['Security update urgent', 'Need to verify credentials',
                          'Company policy requirement']
            },
            'vendor': {
                'role': 'Software Vendor Representative',
                'org': 'TechVendor Inc.',
                'story': 'Following up on license renewal',
                'creds': {'company': 'TechVendor', 'account_num': 'V-98765'},
                'points': ['License expiring soon', 'Special discount available',
                          'Need billing contact']
            }
        }
        
        pretext_data = pretexts.get(scenario, pretexts['it_support'])
        
        return PretextProfile(
            role=pretext_data['role'],
            organization=pretext_data['org'],
            backstory=pretext_data['story'],
            credentials=pretext_data['creds'],
            talking_points=pretext_data['points']
        )


def create_tool() -> PretextGenerator:
    return PretextGenerator()