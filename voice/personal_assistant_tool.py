"""
ATS MAFIA Framework Personal Assistant Tool

This module provides a tool interface for personal assistant capabilities.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from enum import Enum

from .personal_assistant import (
    get_personal_assistant_manager,
    PersonalTaskType,
    PersonalPersona,
    PersonalTaskStatus,
    PersonalAssistantManager
)
from ..core.tool_system import (
    Tool,
    ToolMetadata,
    ToolExecutionResult,
    ToolType,
    ToolCategory,
    ToolRiskLevel,
    PermissionLevel
)


class PersonalAssistantTool(Tool):
    """Tool for personal assistant operations."""
    
    def __init__(self):
        """Initialize the personal assistant tool."""
        metadata = ToolMetadata(
            id="personal_assistant",
            name="Personal Assistant Tool",
            description="Handle personal tasks like making appointments, gathering information, and making calls on behalf of users",
            version="1.0.0",
            author="ATS MAFIA Framework",
            tool_type=ToolType.BUILTIN,
            category=ToolCategory.UTILITIES,
            tags=["personal", "assistant", "phone", "appointments", "voice"],
            permissions_required=[PermissionLevel.EXECUTE],
            dependencies=["voice_system", "phone_integration"],
            risk_level=ToolRiskLevel.MEDIUM_RISK,
            simulation_only=False
        )
        super().__init__(metadata)
        
        self.logger = logging.getLogger("personal_assistant_tool")
        self.manager: Optional[PersonalAssistantManager] = None
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate execution parameters."""
        action = parameters.get('action')
        if not action:
            return False
        
        valid_actions = [
            'create_task', 'approve_task', 'execute_task', 'cancel_task',
            'get_task', 'get_active_tasks', 'get_completed_tasks',
            'get_statistics', 'get_templates'
        ]
        
        return action in valid_actions
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the personal assistant tool.
        
        Args:
            parameters: Tool parameters
            context: Tool execution context
            
        Returns:
            Tool execution result
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Get personal assistant manager
            if not self.manager:
                self.manager = get_personal_assistant_manager()
            
            if not self.manager:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Personal assistant manager not initialized"
                )
            
            if not self.manager.enabled:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Personal assistant feature is not enabled"
                )
            
            action = parameters.get('action')
            
            if action == 'create_task':
                return await self._create_task(parameters, context, execution_id)
            elif action == 'approve_task':
                return await self._approve_task(parameters, context, execution_id)
            elif action == 'execute_task':
                return await self._execute_task(parameters, context, execution_id)
            elif action == 'cancel_task':
                return await self._cancel_task(parameters, context, execution_id)
            elif action == 'get_task':
                return await self._get_task(parameters, context, execution_id)
            elif action == 'get_active_tasks':
                return await self._get_active_tasks(parameters, context, execution_id)
            elif action == 'get_completed_tasks':
                return await self._get_completed_tasks(parameters, context, execution_id)
            elif action == 'get_statistics':
                return await self._get_statistics(parameters, context, execution_id)
            elif action == 'get_templates':
                return await self._get_templates(parameters, context, execution_id)
            else:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            self.logger.error(f"Error executing personal assistant tool: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _create_task(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Create a new personal assistant task."""
        try:
            assert self.manager is not None
            
            user_id = parameters.get('user_id') or context.get('user_id', 'unknown')
            task_type_str = parameters.get('task_type')
            phone_number = parameters.get('phone_number', '')
            intent_description = parameters.get('intent_description', '')
            task_context = parameters.get('context', {})
            persona_str = parameters.get('persona', 'professional_assistant')
            requires_approval = parameters.get('requires_approval', True)
            
            # Validate required parameters
            if not all([user_id, task_type_str, phone_number, intent_description]):
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Missing required parameters: user_id, task_type, phone_number, intent_description"
                )
            
            # Convert enums
            try:
                task_type = PersonalTaskType(task_type_str)
            except ValueError:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error=f"Invalid task_type: {task_type_str}. Valid types: {[t.value for t in PersonalTaskType]}"
                )
            
            try:
                persona = PersonalPersona(persona_str)
            except ValueError:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error=f"Invalid persona: {persona_str}. Valid personas: {[p.value for p in PersonalPersona]}"
                )
            
            # Create task
            task_id = await self.manager.create_task(
                user_id=user_id,
                task_type=task_type,
                phone_number=phone_number,
                intent_description=intent_description,
                context=task_context,
                persona=persona,
                requires_approval=requires_approval
            )
            
            # Get task details
            task = self.manager.get_task(task_id)
            
            result_data = {
                'task_id': task_id,
                'status': task.status.value if task else 'unknown',
                'script': task.script if task else None,
                'requires_approval': requires_approval,
                'message': f"Task created successfully. {'Awaiting approval.' if requires_approval else 'Ready to execute.'}"
            }
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=result_data
            )
                
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _approve_task(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Approve a task for execution."""
        try:
            assert self.manager is not None
            
            task_id = parameters.get('task_id')
            approved_by = parameters.get('approved_by') or context.get('user_id', 'unknown')
            
            if not task_id:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="task_id is required"
                )
            
            success = await self.manager.approve_task(task_id, approved_by)
            
            if success:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=True,
                    result={
                        'task_id': task_id,
                        'status': 'approved',
                        'message': 'Task approved. Ready to execute.'
                    }
                )
            else:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Failed to approve task"
                )
                
        except Exception as e:
            self.logger.error(f"Error approving task: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _execute_task(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Execute a personal assistant task."""
        try:
            assert self.manager is not None
            
            task_id = parameters.get('task_id')
            
            if not task_id:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="task_id is required"
                )
            
            success = await self.manager.execute_task(task_id)
            
            task = self.manager.get_task(task_id)
            
            if success and task:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=True,
                    result={
                        'task_id': task_id,
                        'status': task.status.value,
                        'result': task.result,
                        'recording_file': task.recording_file,
                        'transcript': task.transcript,
                        'duration': task.get_duration(),
                        'message': 'Task executed successfully.'
                    }
                )
            else:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result={'task_id': task_id, 'status': task.status.value if task else 'unknown'},
                    error=task.error_message if task else "Task execution failed"
                )
                
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _cancel_task(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Cancel a pending task."""
        try:
            assert self.manager is not None
            
            task_id = parameters.get('task_id')
            reason = parameters.get('reason')
            
            if not task_id:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="task_id is required"
                )
            
            success = await self.manager.cancel_task(task_id, reason)
            
            if success:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=True,
                    result={
                        'task_id': task_id,
                        'status': 'cancelled',
                        'message': 'Task cancelled successfully.'
                    }
                )
            else:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Failed to cancel task"
                )
                
        except Exception as e:
            self.logger.error(f"Error cancelling task: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _get_task(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Get task details."""
        try:
            assert self.manager is not None
            
            task_id = parameters.get('task_id')
            
            if not task_id:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="task_id is required"
                )
            
            task = self.manager.get_task(task_id)
            
            if task:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=True,
                    result=task.to_dict()
                )
            else:
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error=f"Task not found: {task_id}"
                )
                
        except Exception as e:
            self.logger.error(f"Error getting task: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _get_active_tasks(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Get active tasks."""
        try:
            assert self.manager is not None
            
            user_id = parameters.get('user_id') or context.get('user_id')
            
            tasks = self.manager.get_active_tasks(user_id)
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result={
                    'tasks': [task.to_dict() for task in tasks],
                    'count': len(tasks)
                }
            )
                
        except Exception as e:
            self.logger.error(f"Error getting active tasks: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _get_completed_tasks(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Get completed tasks."""
        try:
            assert self.manager is not None
            
            user_id = parameters.get('user_id') or context.get('user_id')
            limit = parameters.get('limit', 100)
            
            tasks = self.manager.get_completed_tasks(user_id, limit)
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result={
                    'tasks': [task.to_dict() for task in tasks],
                    'count': len(tasks)
                }
            )
                
        except Exception as e:
            self.logger.error(f"Error getting completed tasks: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _get_statistics(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Get personal assistant statistics."""
        try:
            assert self.manager is not None
            
            stats = self.manager.get_statistics()
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=stats
            )
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _get_templates(self, parameters: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> ToolExecutionResult:
        """Get task templates."""
        try:
            assert self.manager is not None
            
            templates = self.manager.get_task_templates()
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result={
                    'templates': templates,
                    'count': len(templates)
                }
            )
                
        except Exception as e:
            self.logger.error(f"Error getting templates: {e}")
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )