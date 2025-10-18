"""
ATS MAFIA Framework - Phishing Crafter Tool

Email/message creation for phishing simulations.
SIMULATION ONLY - For training purposes.
"""

import asyncio
import random
import time
import logging
from typing import Dict, Any
from dataclasses import dataclass
import uuid

from ...core.tool_system import (
    Tool, ToolMetadata, ToolExecutionResult, ToolType,
    PermissionLevel, ToolCategory, ToolRiskLevel
)


@dataclass
class PhishingCampaign:
    """Phishing campaign materials."""
    subject: str
    body: str
    sender: str
    urgency_score: float
    personalization_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'email_subject': self.subject,
            'email_body': self.body,
            'sender_address': self.sender,
            'urgency_score': self.urgency_score,
            'personalization': self.personalization_level,
            'simulation_mode': True
        }


class PhishingCrafter(Tool):
    """Phishing campaign creation tool."""
    
    def __init__(self):
        metadata = ToolMetadata(
            id="phishing_crafter",
            name="Phishing Crafter",
            description="Create phishing campaign materials for training",
            version="1.0.0",
            author="ATS MAFIA Team",
            tool_type=ToolType.PYTHON,
            category=ToolCategory.SOCIAL_ENGINEERING,
            risk_level=ToolRiskLevel.MEDIUM_RISK,
            tags=["phishing", "social-engineering", "email"],
            permissions_required=[PermissionLevel.EXECUTE],
            dependencies=[],
            simulation_only=True,
            config_schema={
                "template": {
                    "type": "string",
                    "enum": ["urgent_security", "invoice", "password_reset"],
                    "required": True
                }
            }
        )
        super().__init__(metadata)
        self.logger = logging.getLogger("tool.phishing_crafter")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return 'template' in parameters
    
    async def execute(self, parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            template = parameters['template']
            self.logger.info(f"[SIMULATION] Creating {template} phishing campaign")
            result = await self._simulate_campaign(template)
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=result.to_dict(),
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
    
    async def _simulate_campaign(self, template: str) -> PhishingCampaign:
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        templates = {
            'urgent_security': {
                'subject': 'URGENT: Security Alert - Action Required',
                'body': 'Your account shows suspicious activity. Click here to verify.',
                'sender': 'security@company-alert.com',
                'urgency': 0.9
            },
            'invoice': {
                'subject': 'Invoice #12345 - Payment Overdue',
                'body': 'Your invoice is past due. Please review the attached document.',
                'sender': 'billing@vendor-inc.com',
                'urgency': 0.7
            }
        }
        
        data = templates.get(template, templates['urgent_security'])
        
        return PhishingCampaign(
            subject=data['subject'],
            body=data['body'],
            sender=data['sender'],
            urgency_score=data['urgency'],
            personalization_level='medium'
        )


def create_tool() -> PhishingCrafter:
    return PhishingCrafter()