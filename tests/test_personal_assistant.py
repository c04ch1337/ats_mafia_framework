"""
ATS MAFIA Framework Personal Assistant - Test Suite

Comprehensive tests for Personal Assistant functionality.
"""

import asyncio
import pytest
from typing import Dict, Any
from datetime import datetime

from ats_mafia_framework.config.settings import FrameworkConfig
from ats_mafia_framework.core.logging import AuditLogger
from ats_mafia_framework.voice.personal_assistant import (
    PersonalAssistantManager,
    PersonalTaskType,
    PersonalPersona,
    PersonalTaskStatus,
    PersonalTaskConfig,
    initialize_personal_assistant_manager,
    get_personal_assistant_manager,
    shutdown_personal_assistant_manager
)
from ats_mafia_framework.voice.personal_assistant_config import (
    PersonalAssistantConfig,
    PersonalAssistantInitializer,
    initialize_personal_assistant_feature
)
from ats_mafia_framework.voice.personal_assistant_tool import PersonalAssistantTool


class TestPersonalAssistantManager:
    """Test suite for PersonalAssistantManager."""
    
    @pytest.fixture
    async def pa_manager(self):
        """Create a test Personal Assistant Manager."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        config.set('voice.personal_assistant.phone_provider', 'mock')
        
        manager = PersonalAssistantManager(config)
        manager.enabled = True  # Force enable for testing
        
        yield manager
        
        # Cleanup
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_create_task(self, pa_manager):
        """Test task creation."""
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Test appointment booking",
            context={"service_type": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        assert task_id is not None
        assert task_id in pa_manager.active_tasks
        
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.status == PersonalTaskStatus.AWAITING_APPROVAL
        assert task.config.task_type == PersonalTaskType.APPOINTMENT_BOOKING
    
    @pytest.mark.asyncio
    async def test_approve_task(self, pa_manager):
        """Test task approval."""
        # Create task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test inquiry",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        # Approve task
        success = await pa_manager.approve_task(task_id, "test_user")
        
        assert success is True
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_execute_task(self, pa_manager):
        """Test task execution."""
        # Create and approve task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test inquiry",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        # Execute task
        success = await pa_manager.execute_task(task_id)
        
        assert success is True
        
        # Task should be in completed tasks
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.status == PersonalTaskStatus.COMPLETED
        assert task.result is not None
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, pa_manager):
        """Test task cancellation."""
        # Create task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Test appointment",
            context={"service_type": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        # Cancel task
        success = await pa_manager.cancel_task(task_id, "Testing cancellation")
        
        assert success is True
        assert task_id not in pa_manager.active_tasks
        
        # Task should be in completed tasks with cancelled status
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.status == PersonalTaskStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_script_generation(self, pa_manager):
        """Test script generation from templates."""
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Book appointment",
            context={
                "user_name": "Test User",
                "service_type": "dental cleaning",
                "preferred_timeframe": "next week"
            },
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.script is not None
        assert len(task.script) > 0
        assert "Test User" in task.script
        assert "dental cleaning" in task.script
    
    @pytest.mark.asyncio
    async def test_get_active_tasks(self, pa_manager):
        """Test retrieving active tasks."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await pa_manager.create_task(
                user_id="test_user",
                task_type=PersonalTaskType.INFORMATION_INQUIRY,
                phone_number=f"+1-555-TEST-{i}",
                intent_description=f"Test task {i}",
                context={"inquiry_topic": f"test {i}"},
                persona=PersonalPersona.PROFESSIONAL_ASSISTANT
            )
            task_ids.append(task_id)
        
        # Get active tasks
        active_tasks = pa_manager.get_active_tasks("test_user")
        
        assert len(active_tasks) == 3
        assert all(task.config.user_id == "test_user" for task in active_tasks)
    
    @pytest.mark.asyncio
    async def test_statistics(self, pa_manager):
        """Test statistics tracking."""
        initial_stats = pa_manager.get_statistics()
        initial_total = initial_stats['total_tasks']
        
        # Create and execute a task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        await pa_manager.execute_task(task_id)
        
        # Check statistics updated
        stats = pa_manager.get_statistics()
        assert stats['total_tasks'] == initial_total + 1
        assert stats['completed_tasks'] >= 1


class TestPersonalAssistantConfig:
    """Test suite for PersonalAssistantConfig."""
    
    def test_config_creation(self):
        """Test configuration creation."""
        config = PersonalAssistantConfig(
            enabled=True,
            default_persona="professional_assistant",
            phone_provider="mock"
        )
        
        assert config.enabled is True
        assert config.default_persona == "professional_assistant"
        assert config.phone_provider == "mock"
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = PersonalAssistantConfig(enabled=True)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'enabled' in config_dict
        assert config_dict['enabled'] is True
    
    def test_config_from_dict(self):
        """Test configuration deserialization."""
        config_dict = {
            'enabled': True,
            'default_persona': 'friendly_representative',
            'phone_provider': 'twilio'
        }
        
        config = PersonalAssistantConfig.from_dict(config_dict)
        
        assert config.enabled is True
        assert config.default_persona == 'friendly_representative'
        assert config.phone_provider == 'twilio'
    
    def test_config_from_framework_config(self):
        """Test creating from framework configuration."""
        framework_config = FrameworkConfig()
        framework_config.set('voice.personal_assistant.enabled', True)
        framework_config.set('voice.personal_assistant.default_persona', 'formal_business')
        
        pa_config = PersonalAssistantConfig.from_framework_config(framework_config)
        
        assert pa_config.enabled is True
        assert pa_config.default_persona == 'formal_business'


class TestPersonalAssistantInitializer:
    """Test suite for PersonalAssistantInitializer."""
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        config.set('voice.personal_assistant.phone_provider', 'mock')
        
        initializer = PersonalAssistantInitializer(config)
        is_valid, error = initializer.validate_configuration()
        
        assert is_valid is True
        assert error is None
    
    def test_validate_configuration_twilio_incomplete(self):
        """Test configuration validation with incomplete Twilio config."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        config.set('voice.personal_assistant.phone_provider', 'twilio')
        # Missing Twilio credentials
        
        initializer = PersonalAssistantInitializer(config)
        is_valid, error = initializer.validate_configuration()
        
        assert is_valid is False
        assert error is not None
        assert 'twilio' in error.lower()
    
    def test_validate_configuration_invalid_limits(self):
        """Test configuration validation with invalid limits."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        config.set('voice.personal_assistant.phone_provider', 'mock')
        config.set('voice.personal_assistant.max_tasks_per_day', 0)  # Invalid
        
        initializer = PersonalAssistantInitializer(config)
        is_valid, error = initializer.validate_configuration()
        
        assert is_valid is False
        assert error is not None


class TestPersonalAssistantTool:
    """Test suite for PersonalAssistantTool."""
    
    @pytest.fixture
    def pa_tool(self):
        """Create test tool instance."""
        return PersonalAssistantTool()
    
    def test_tool_initialization(self, pa_tool):
        """Test tool initialization."""
        assert pa_tool.metadata.id == "personal_assistant"
        assert pa_tool.metadata.name == "Personal Assistant Tool"
        assert pa_tool.metadata.tool_type.value == "builtin"
    
    def test_validate_parameters_valid(self, pa_tool):
        """Test parameter validation with valid parameters."""
        parameters = {'action': 'create_task'}
        assert pa_tool.validate_parameters(parameters) is True
    
    def test_validate_parameters_invalid(self, pa_tool):
        """Test parameter validation with invalid parameters."""
        parameters = {}  # Missing action
        assert pa_tool.validate_parameters(parameters) is False
        
        parameters = {'action': 'invalid_action'}
        assert pa_tool.validate_parameters(parameters) is True  # Action exists
    
    @pytest.mark.asyncio
    async def test_execute_create_task(self, pa_tool):
        """Test executing create_task action."""
        # Initialize manager first
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        manager = PersonalAssistantManager(config)
        manager.enabled = True
        
        # Set manager (normally done by initialization)
        pa_tool.manager = manager
        
        parameters = {
            'action': 'create_task',
            'user_id': 'test_user',
            'task_type': 'information_inquiry',
            'phone_number': '+1-555-TEST',
            'intent_description': 'Test inquiry',
            'context': {'inquiry_topic': 'test'}
        }
        
        context = {'user_id': 'test_user'}
        
        result = await pa_tool.execute(parameters, context)
        
        assert result.success is True
        assert result.result is not None
        assert 'task_id' in result.result


class TestTaskTemplates:
    """Test suite for task templates."""
    
    @pytest.fixture
    async def pa_manager(self):
        """Create test manager."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        manager = PersonalAssistantManager(config)
        manager.enabled = True
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_appointment_booking_template(self, pa_manager):
        """Test appointment booking template."""
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Book appointment",
            context={
                "user_name": "Test User",
                "service_type": "dental checkup",
                "preferred_timeframe": "next week"
            },
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.script is not None
        
        # Verify script contains context
        assert "Test User" in task.script
        assert "dental checkup" in task.script
    
    @pytest.mark.asyncio
    async def test_information_inquiry_template(self, pa_manager):
        """Test information inquiry template."""
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Get information",
            context={
                "inquiry_topic": "store hours",
                "specific_questions": "What are your hours today?"
            },
            persona=PersonalPersona.FRIENDLY_REPRESENTATIVE
        )
        
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.script is not None
        assert "store hours" in task.script


class TestTaskWorkflow:
    """Test suite for complete task workflows."""
    
    @pytest.fixture
    async def pa_manager(self):
        """Create test manager."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        manager = PersonalAssistantManager(config)
        manager.enabled = True
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_complete_approval_workflow(self, pa_manager):
        """Test complete workflow: create → approve → execute."""
        # Create task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=True
        )
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.AWAITING_APPROVAL
        
        # Approve
        success = await pa_manager.approve_task(task_id, "test_user")
        assert success is True
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.APPROVED
        
        # Execute
        success = await pa_manager.execute_task(task_id)
        assert success is True
        
        task = pa_manager.get_task(task_id)
        assert task is not None
        assert task.status == PersonalTaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_no_approval_workflow(self, pa_manager):
        """Test workflow without approval: create → execute."""
        # Create task without approval requirement
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.PENDING
        
        # Execute directly
        success = await pa_manager.execute_task(task_id)
        assert success is True
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_cancellation_workflow(self, pa_manager):
        """Test workflow: create → cancel."""
        # Create task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"service_type": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT
        )
        
        # Cancel
        success = await pa_manager.cancel_task(task_id, "Changed mind")
        assert success is True
        
        task = pa_manager.get_task(task_id)
        assert task.status == PersonalTaskStatus.CANCELLED


class TestStatistics:
    """Test suite for statistics and metrics."""
    
    @pytest.fixture
    async def pa_manager(self):
        """Create test manager."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        manager = PersonalAssistantManager(config)
        manager.enabled = True
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, pa_manager):
        """Test that statistics are tracked correctly."""
        initial_stats = pa_manager.get_statistics()
        
        # Create and complete a task
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        await pa_manager.execute_task(task_id)
        
        final_stats = pa_manager.get_statistics()
        
        assert final_stats['total_tasks'] == initial_stats['total_tasks'] + 1
        assert final_stats['completed_tasks'] == initial_stats['completed_tasks'] + 1
    
    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, pa_manager):
        """Test success rate calculation."""
        # Create and execute successful task
        task_id1 = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        await pa_manager.execute_task(task_id1)
        
        stats = pa_manager.get_statistics()
        
        # Should have a success rate
        if stats['completed_tasks'] + stats['failed_tasks'] > 0:
            assert 0.0 <= stats['success_rate'] <= 1.0


class TestErrorHandling:
    """Test suite for error handling."""
    
    @pytest.fixture
    async def pa_manager(self):
        """Create test manager."""
        config = FrameworkConfig()
        config.set('voice.personal_assistant.enabled', True)
        manager = PersonalAssistantManager(config)
        manager.enabled = True
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_invalid_phone_number(self, pa_manager):
        """Test handling of invalid phone number."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            await pa_manager.create_task(
                user_id="test_user",
                task_type=PersonalTaskType.INFORMATION_INQUIRY,
                phone_number="invalid",  # Invalid format
                intent_description="Test",
                context={"inquiry_topic": "test"},
                persona=PersonalPersona.PROFESSIONAL_ASSISTANT
            )
    
    @pytest.mark.asyncio
    async def test_approve_nonexistent_task(self, pa_manager):
        """Test approving a task that doesn't exist."""
        with pytest.raises(ValueError, match="Task not found"):
            await pa_manager.approve_task("nonexistent_task_id", "test_user")
    
    @pytest.mark.asyncio
    async def test_execute_unapproved_task(self, pa_manager):
        """Test executing a task that requires but hasn't received approval."""
        # Create task requiring approval
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.APPOINTMENT_BOOKING,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"service_type": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=True  # Requires approval
        )
        
        # Try to execute without approval
        with pytest.raises(ValueError, match="requires approval"):
            await pa_manager.execute_task(task_id)
    
    @pytest.mark.asyncio
    async def test_cancel_calling_task(self, pa_manager):
        """Test that we cannot cancel a task while call is in progress."""
        task_id = await pa_manager.create_task(
            user_id="test_user",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        # Manually set status to CALLING
        task = pa_manager.get_task(task_id)
        task.status = PersonalTaskStatus.CALLING
        
        # Try to cancel
        with pytest.raises(ValueError, match="call is in progress"):
            await pa_manager.cancel_task(task_id)


# Integration test
@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration from config to execution."""
    # Create configuration
    config = FrameworkConfig()
    config.set('voice.personal_assistant.enabled', True)
    config.set('voice.personal_assistant.phone_provider', 'mock')
    
    # Initialize
    initialized = initialize_personal_assistant_feature(config)
    
    if initialized:
        # Get manager
        pa_manager = get_personal_assistant_manager()
        assert pa_manager is not None
        
        # Create task
        task_id = await pa_manager.create_task(
            user_id="integration_test",
            task_type=PersonalTaskType.INFORMATION_INQUIRY,
            phone_number="+1-555-TEST",
            intent_description="Integration test",
            context={"inquiry_topic": "test"},
            persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
            requires_approval=False
        )
        
        # Execute
        success = await pa_manager.execute_task(task_id)
        assert success is True
        
        # Cleanup
        shutdown_personal_assistant_manager()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])