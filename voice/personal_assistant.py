"""
ATS MAFIA Framework Personal Assistant Manager

This module provides personal assistant capabilities for Puppet Master,
enabling it to make calls and handle tasks on behalf of users.
"""

import os
import asyncio
import logging
import time
import uuid
import json
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from .core import VoicePersonaConfig, AudioSegment, AudioFormat
from .integration import get_voice_system_manager
from .conversation import DialogueStrategy, ScenarioType, ConversationObjective
from .puppet_master_integration import get_puppet_master_integration
from .phone import CallType, ScenarioType as PhoneScenarioType
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class PersonalTaskType(Enum):
    """Types of personal assistant tasks."""
    APPOINTMENT_BOOKING = "appointment_booking"
    APPOINTMENT_CANCEL = "appointment_cancel"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    INFORMATION_INQUIRY = "information_inquiry"
    SERVICE_ISSUE = "service_issue"
    BILL_NEGOTIATION = "bill_negotiation"
    SOCIAL_CALL = "social_call"
    CUSTOM = "custom"


class PersonalTaskStatus(Enum):
    """Status of personal tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    CALLING = "calling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PersonalPersona(Enum):
    """Voice personas for personal assistant."""
    PROFESSIONAL_ASSISTANT = "professional_assistant"
    FRIENDLY_REPRESENTATIVE = "friendly_representative"
    FORMAL_BUSINESS = "formal_business"
    CASUAL_HELPER = "casual_helper"
    CUSTOM = "custom"


@dataclass
class PersonalTaskConfig:
    """Configuration for a personal assistant task."""
    task_id: str
    task_type: PersonalTaskType
    user_id: str
    phone_number: str
    intent_description: str
    context: Dict[str, Any]
    persona: PersonalPersona
    requires_approval: bool = True
    auto_record: bool = True
    max_duration_minutes: int = 10
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'intent_description': self.intent_description,
            'context': self.context,
            'persona': self.persona.value,
            'requires_approval': self.requires_approval,
            'auto_record': self.auto_record,
            'max_duration_minutes': self.max_duration_minutes,
            'priority': self.priority,
            'metadata': self.metadata
        }


@dataclass
class PersonalTask:
    """A personal assistant task."""
    task_id: str
    config: PersonalTaskConfig
    status: PersonalTaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    call_id: Optional[str] = None
    conversation_id: Optional[str] = None
    script: Optional[str] = None
    recording_file: Optional[str] = None
    transcript: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'config': self.config.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'call_id': self.call_id,
            'conversation_id': self.conversation_id,
            'script': self.script,
            'recording_file': self.recording_file,
            'transcript': self.transcript,
            'result': self.result,
            'error_message': self.error_message
        }
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class PersonalAssistantManager:
    """
    Manager for personal assistant capabilities.
    
    Handles task creation, execution, and tracking for personal calls.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the personal assistant manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("personal_assistant_manager")
        
        # Voice system manager
        self.voice_system_manager = get_voice_system_manager()
        
        # Puppet Master integration
        self.puppet_master = get_puppet_master_integration()
        
        # Task tracking
        self.active_tasks: Dict[str, PersonalTask] = {}
        self.completed_tasks: List[PersonalTask] = []
        
        # Task templates
        self.task_templates: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.statistics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_call_duration': 0.0,
            'success_rate': 0.0
        }
        
        # Load task templates
        self._load_task_templates()
        
        # Personal assistant enabled
        self.enabled = config.get('voice.personal_assistant.enabled', False)
        
        if self.enabled:
            self.logger.info("Personal Assistant Manager initialized")
        else:
            self.logger.info("Personal Assistant Manager initialized (disabled)")
    
    def _load_task_templates(self) -> None:
        """Load task templates for different task types."""
        
        # Appointment Booking Template
        self.task_templates[PersonalTaskType.APPOINTMENT_BOOKING.value] = {
            'name': 'Appointment Booking',
            'description': 'Schedule a new appointment',
            'required_context': ['service_type', 'preferred_timeframe'],
            'optional_context': ['specific_date', 'specific_time', 'provider_name'],
            'script_template': '''
Hello, I'm calling on behalf of {user_name}.
I'd like to schedule an appointment for {service_type}.
{timeframe_request}
{additional_context}
            '''.strip(),
            'objectives': [
                'Identify as calling on behalf of user',
                'Request appointment for service',
                'Negotiate suitable time',
                'Confirm appointment details',
                'Get confirmation number if available'
            ],
            'fallback_strategies': [
                'If no availability, ask for next available slot',
                'If specific time not available, ask for alternatives',
                'If uncertain about requirements, offer to have user call back'
            ]
        }
        
        # Information Inquiry Template
        self.task_templates[PersonalTaskType.INFORMATION_INQUIRY.value] = {
            'name': 'Information Inquiry',
            'description': 'Get information about products, services, or hours',
            'required_context': ['inquiry_topic'],
            'optional_context': ['specific_questions', 'urgency'],
            'script_template': '''
Hello, I'm calling to inquire about {inquiry_topic}.
{specific_questions}
{additional_context}
            '''.strip(),
            'objectives': [
                'State purpose of call clearly',
                'Ask specific questions',
                'Clarify any unclear responses',
                'Confirm information accuracy',
                'Thank for assistance'
            ],
            'fallback_strategies': [
                'If information not available, ask who to contact',
                'If complex question, request callback',
                'If automated system, navigate to operator'
            ]
        }
        
        # Service Issue Template
        self.task_templates[PersonalTaskType.SERVICE_ISSUE.value] = {
            'name': 'Service Issue Report',
            'description': 'Report and resolve service problems',
            'required_context': ['issue_description', 'account_info'],
            'optional_context': ['duration_of_issue', 'attempted_solutions', 'urgency_level'],
            'script_template': '''
Hello, I'm calling regarding a service issue for account {account_info}.
{issue_description}
{duration_context}
We need this resolved as soon as possible.
            '''.strip(),
            'objectives': [
                'Identify account and issue clearly',
                'Explain problem in detail',
                'Request resolution timeline',
                'Get ticket or reference number',
                'Confirm next steps'
            ],
            'fallback_strategies': [
                'If first-level cannot help, request supervisor',
                'If wait time excessive, request callback',
                'If no immediate solution, get timeline for follow-up'
            ]
        }
        
        # Social Call Template
        self.task_templates[PersonalTaskType.SOCIAL_CALL.value] = {
            'name': 'Social Call',
            'description': 'RSVP, relay messages, or coordinate',
            'required_context': ['message_or_purpose'],
            'optional_context': ['recipient_name', 'urgency', 'requires_response'],
            'script_template': '''
Hello {recipient_greeting}, this is {user_name}'s assistant calling.
{message_or_purpose}
{requires_response_text}
            '''.strip(),
            'objectives': [
                'Identify clearly as assistant',
                'Deliver message accurately',
                'Get response if needed',
                'Confirm understanding',
                'End call politely'
            ],
            'fallback_strategies': [
                'If voicemail, leave detailed message',
                'If recipient unavailable, ask for callback',
                'If message complex, offer to have user call directly'
            ]
        }
    
    async def create_task(self,
                         user_id: str,
                         task_type: PersonalTaskType,
                         phone_number: str,
                         intent_description: str,
                         context: Dict[str, Any],
                         persona: PersonalPersona = PersonalPersona.PROFESSIONAL_ASSISTANT,
                         requires_approval: bool = True) -> str:
        """
        Create a new personal assistant task.
        
        Args:
            user_id: ID of the user requesting the task
            task_type: Type of task to perform
            phone_number: Phone number to call
            intent_description: Brief description of what to accomplish
            context: Additional context for the task
            persona: Voice persona to use
            requires_approval: Whether task requires user approval before execution
            
        Returns:
            Task ID
        """
        try:
            if not self.enabled:
                raise ValueError("Personal Assistant feature is not enabled")
            
            # Validate phone number
            if not self._validate_phone_number(phone_number):
                raise ValueError(f"Invalid phone number: {phone_number}")
            
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Create task config
            task_config = PersonalTaskConfig(
                task_id=task_id,
                task_type=task_type,
                user_id=user_id,
                phone_number=phone_number,
                intent_description=intent_description,
                context=context,
                persona=persona,
                requires_approval=requires_approval
            )
            
            # Generate script
            script = await self._generate_script(task_config)
            
            # Create task
            task = PersonalTask(
                task_id=task_id,
                config=task_config,
                status=PersonalTaskStatus.AWAITING_APPROVAL if requires_approval else PersonalTaskStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                script=script
            )
            
            # Store task
            self.active_tasks[task_id] = task
            
            # Update statistics
            self.statistics['total_tasks'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="personal_task_created",
                    details={
                        'task_id': task_id,
                        'user_id': user_id,
                        'task_type': task_type.value,
                        'phone_number': phone_number,
                        'requires_approval': requires_approval
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Created personal task {task_id} for user {user_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Error creating personal task: {e}")
            raise
    
    async def _generate_script(self, config: PersonalTaskConfig) -> str:
        """Generate call script from task configuration."""
        try:
            template = self.task_templates.get(config.task_type.value)
            if not template:
                return f"Purpose: {config.intent_description}"
            
            # Fill template with context
            script = template['script_template']
            
            # Replace placeholders
            for key, value in config.context.items():
                placeholder = f"{{{key}}}"
                if placeholder in script:
                    script = script.replace(placeholder, str(value))
            
            # Add user name if available
            user_name = config.context.get('user_name', '[User Name]')
            script = script.replace('{user_name}', user_name)
            
            return script
            
        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            return f"Purpose: {config.intent_description}"
    
    async def approve_task(self, task_id: str, approved_by: str) -> bool:
        """
        Approve a task for execution.
        
        Args:
            task_id: ID of the task to approve
            approved_by: ID of user approving the task
            
        Returns:
            True if approved successfully
        """
        try:
            if task_id not in self.active_tasks:
                raise ValueError(f"Task not found: {task_id}")
            
            task = self.active_tasks[task_id]
            
            if task.status != PersonalTaskStatus.AWAITING_APPROVAL:
                raise ValueError(f"Task {task_id} is not awaiting approval (status: {task.status.value})")
            
            # Update status
            task.status = PersonalTaskStatus.APPROVED
            task.config.metadata['approved_by'] = approved_by
            task.config.metadata['approved_at'] = datetime.now(timezone.utc).isoformat()
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="personal_task_approved",
                    details={
                        'task_id': task_id,
                        'approved_by': approved_by
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Task {task_id} approved by {approved_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error approving task {task_id}: {e}")
            return False
    
    async def execute_task(self, task_id: str) -> bool:
        """
        Execute a personal assistant task.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            True if execution started successfully
        """
        try:
            if task_id not in self.active_tasks:
                raise ValueError(f"Task not found: {task_id}")
            
            task = self.active_tasks[task_id]
            
            # Check if task can be executed
            if task.config.requires_approval and task.status != PersonalTaskStatus.APPROVED:
                raise ValueError(f"Task {task_id} requires approval before execution")
            
            if task.status not in [PersonalTaskStatus.PENDING, PersonalTaskStatus.APPROVED]:
                raise ValueError(f"Task {task_id} cannot be executed (status: {task.status.value})")
            
            # Update status
            task.status = PersonalTaskStatus.CALLING
            task.started_at = datetime.now(timezone.utc)
            
            # Make the call
            success = await self._execute_call(task)
            
            if success:
                task.status = PersonalTaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                self.statistics['completed_tasks'] += 1
                
                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
            else:
                task.status = PersonalTaskStatus.FAILED
                task.completed_at = datetime.now(timezone.utc)
                self.statistics['failed_tasks'] += 1
            
            # Update success rate
            total_finished = self.statistics['completed_tasks'] + self.statistics['failed_tasks']
            if total_finished > 0:
                self.statistics['success_rate'] = self.statistics['completed_tasks'] / total_finished
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="personal_task_executed",
                    details={
                        'task_id': task_id,
                        'success': success,
                        'duration': task.get_duration()
                    },
                    security_level=SecurityLevel.HIGH
                )
            
            self.logger.info(f"Task {task_id} execution {'completed' if success else 'failed'}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = PersonalTaskStatus.FAILED
                self.active_tasks[task_id].error_message = str(e)
            return False
    
    async def _execute_call(self, task: PersonalTask) -> bool:
        """Execute the actual phone call for a task."""
        try:
            # This would integrate with the actual phone system
            # For now, we'll create a placeholder implementation
            
            self.logger.info(f"Executing call for task {task.task_id} to {task.config.phone_number}")
            
            # In real implementation, this would:
            # 1. Use phone_call_manager to initiate call
            # 2. Use puppet_master_integration for conversation
            # 3. Handle real-time conversation flow
            # 4. Record call if enabled
            # 5. Generate transcript
            # 6. Extract key information
            
            # Placeholder result
            task.result = {
                'call_completed': True,
                'objective_achieved': True,
                'key_information': {},
                'next_steps': []
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing call for task {task.task_id}: {e}")
            task.error_message = str(e)
            return False
    
    async def cancel_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a pending task.
        
        Args:
            task_id: ID of the task to cancel
            reason: Optional reason for cancellation
            
        Returns:
            True if cancelled successfully
        """
        try:
            if task_id not in self.active_tasks:
                raise ValueError(f"Task not found: {task_id}")
            
            task = self.active_tasks[task_id]
            
            if task.status == PersonalTaskStatus.CALLING:
                raise ValueError(f"Cannot cancel task {task_id} while call is in progress")
            
            # Update status
            task.status = PersonalTaskStatus.CANCELLED
            task.completed_at = datetime.now(timezone.utc)
            if reason:
                task.config.metadata['cancellation_reason'] = reason
            
            # Update statistics
            self.statistics['cancelled_tasks'] += 1
            
            # Move to completed tasks
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="personal_task_cancelled",
                    details={
                        'task_id': task_id,
                        'reason': reason
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Task {task_id} cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[PersonalTask]:
        """Get a task by ID."""
        task = self.active_tasks.get(task_id)
        if not task:
            # Check completed tasks
            for completed_task in self.completed_tasks:
                if completed_task.task_id == task_id:
                    return completed_task
        return task
    
    def get_active_tasks(self, user_id: Optional[str] = None) -> List[PersonalTask]:
        """Get all active tasks, optionally filtered by user."""
        tasks = list(self.active_tasks.values())
        if user_id:
            tasks = [t for t in tasks if t.config.user_id == user_id]
        return tasks
    
    def get_completed_tasks(self, user_id: Optional[str] = None, limit: int = 100) -> List[PersonalTask]:
        """Get completed tasks, optionally filtered by user."""
        tasks = self.completed_tasks[-limit:]
        if user_id:
            tasks = [t for t in tasks if t.config.user_id == user_id]
        return tasks
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get personal assistant statistics."""
        return {
            **self.statistics,
            'active_tasks': len(self.active_tasks),
            'total_completed': len(self.completed_tasks)
        }
    
    def get_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all task templates."""
        return self.task_templates.copy()
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format."""
        try:
            # Remove non-digit characters
            digits = ''.join(c for c in phone_number if c.isdigit())
            
            # Check length (10-15 digits for international numbers)
            if len(digits) < 10 or len(digits) > 15:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Cancel all active tasks
            task_ids = list(self.active_tasks.keys())
            for task_id in task_ids:
                await self.cancel_task(task_id, reason="System cleanup")
            
            self.logger.info("Personal Assistant Manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global personal assistant manager instance
_global_personal_assistant_manager: Optional[PersonalAssistantManager] = None


def get_personal_assistant_manager() -> Optional[PersonalAssistantManager]:
    """
    Get the global personal assistant manager instance.
    
    Returns:
        Global PersonalAssistantManager instance or None if not initialized
    """
    return _global_personal_assistant_manager


def initialize_personal_assistant_manager(config: FrameworkConfig,
                                         audit_logger: Optional[AuditLogger] = None) -> PersonalAssistantManager:
    """
    Initialize the global personal assistant manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized PersonalAssistantManager instance
    """
    global _global_personal_assistant_manager
    _global_personal_assistant_manager = PersonalAssistantManager(config, audit_logger)
    return _global_personal_assistant_manager


def shutdown_personal_assistant_manager() -> None:
    """Shutdown the global personal assistant manager."""
    global _global_personal_assistant_manager
    if _global_personal_assistant_manager:
        asyncio.create_task(_global_personal_assistant_manager.cleanup())
        _global_personal_assistant_manager = None