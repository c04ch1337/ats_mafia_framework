"""
ATS MAFIA Framework Personal Assistant Configuration

This module provides configuration and initialization helpers for the Personal Assistant feature.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .personal_assistant import (
    initialize_personal_assistant_manager,
    get_personal_assistant_manager,
    shutdown_personal_assistant_manager,
    PersonalPersona
)
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger


@dataclass
class PersonalAssistantConfig:
    """Configuration for Personal Assistant feature."""
    
    # Feature enablement
    enabled: bool = False
    
    # Default settings
    default_persona: str = "professional_assistant"
    default_requires_approval: bool = True
    auto_record_calls: bool = True
    max_call_duration_minutes: int = 10
    
    # Phone provider settings
    phone_provider: str = "mock"  # mock, twilio, plivo, etc.
    from_number: Optional[str] = None
    
    # Twilio settings (if using Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Plivo settings (if using Plivo)
    plivo_auth_id: Optional[str] = None
    plivo_auth_token: Optional[str] = None
    plivo_phone_number: Optional[str] = None
    
    # Storage settings
    recording_path: str = "recordings/personal_assistant/"
    transcript_path: str = "transcripts/personal_assistant/"
    task_history_path: str = "data/personal_assistant/tasks/"
    
    # Rate limiting
    max_tasks_per_day: int = 50
    max_active_tasks: int = 5
    
    # Notification settings
    notify_on_task_created: bool = False
    notify_on_task_awaiting_approval: bool = True
    notify_on_call_started: bool = True
    notify_on_call_completed: bool = True
    notify_on_task_failed: bool = True
    
    # Ethical safeguards
    always_identify_as_assistant: bool = True
    disclose_ai_when_asked: bool = True
    no_impersonation: bool = True
    require_approval_for_sensitive: bool = True
    
    # Advanced settings
    enable_learning: bool = False
    enable_adaptation: bool = True
    conversation_timeout_seconds: int = 600  # 10 minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'default_persona': self.default_persona,
            'default_requires_approval': self.default_requires_approval,
            'auto_record_calls': self.auto_record_calls,
            'max_call_duration_minutes': self.max_call_duration_minutes,
            'phone_provider': self.phone_provider,
            'from_number': self.from_number,
            'twilio_account_sid': self.twilio_account_sid,
            'twilio_auth_token': '***' if self.twilio_auth_token else None,
            'twilio_phone_number': self.twilio_phone_number,
            'plivo_auth_id': self.plivo_auth_id,
            'plivo_auth_token': '***' if self.plivo_auth_token else None,
            'plivo_phone_number': self.plivo_phone_number,
            'recording_path': self.recording_path,
            'transcript_path': self.transcript_path,
            'task_history_path': self.task_history_path,
            'max_tasks_per_day': self.max_tasks_per_day,
            'max_active_tasks': self.max_active_tasks,
            'notify_on_task_created': self.notify_on_task_created,
            'notify_on_task_awaiting_approval': self.notify_on_task_awaiting_approval,
            'notify_on_call_started': self.notify_on_call_started,
            'notify_on_call_completed': self.notify_on_call_completed,
            'notify_on_task_failed': self.notify_on_task_failed,
            'always_identify_as_assistant': self.always_identify_as_assistant,
            'disclose_ai_when_asked': self.disclose_ai_when_asked,
            'no_impersonation': self.no_impersonation,
            'require_approval_for_sensitive': self.require_approval_for_sensitive,
            'enable_learning': self.enable_learning,
            'enable_adaptation': self.enable_adaptation,
            'conversation_timeout_seconds': self.conversation_timeout_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalAssistantConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_framework_config(cls, config: FrameworkConfig) -> 'PersonalAssistantConfig':
        """
        Create from framework configuration.
        
        Args:
            config: Framework configuration
            
        Returns:
            PersonalAssistantConfig instance
        """
        return cls(
            enabled=config.get('voice.personal_assistant.enabled', False),
            default_persona=config.get('voice.personal_assistant.default_persona', 'professional_assistant'),
            default_requires_approval=config.get('voice.personal_assistant.default_requires_approval', True),
            auto_record_calls=config.get('voice.personal_assistant.auto_record_calls', True),
            max_call_duration_minutes=config.get('voice.personal_assistant.max_call_duration_minutes', 10),
            phone_provider=config.get('voice.personal_assistant.phone_provider', 'mock'),
            from_number=config.get('voice.personal_assistant.from_number'),
            twilio_account_sid=config.get('voice.personal_assistant.twilio.account_sid'),
            twilio_auth_token=config.get('voice.personal_assistant.twilio.auth_token'),
            twilio_phone_number=config.get('voice.personal_assistant.twilio.phone_number'),
            plivo_auth_id=config.get('voice.personal_assistant.plivo.auth_id'),
            plivo_auth_token=config.get('voice.personal_assistant.plivo.auth_token'),
            plivo_phone_number=config.get('voice.personal_assistant.plivo.phone_number'),
            recording_path=config.get('voice.personal_assistant.recording_path', 'recordings/personal_assistant/'),
            transcript_path=config.get('voice.personal_assistant.transcript_path', 'transcripts/personal_assistant/'),
            task_history_path=config.get('voice.personal_assistant.task_history_path', 'data/personal_assistant/tasks/'),
            max_tasks_per_day=config.get('voice.personal_assistant.max_tasks_per_day', 50),
            max_active_tasks=config.get('voice.personal_assistant.max_active_tasks', 5),
            notify_on_task_created=config.get('voice.personal_assistant.notify_on_task_created', False),
            notify_on_task_awaiting_approval=config.get('voice.personal_assistant.notify_on_task_awaiting_approval', True),
            notify_on_call_started=config.get('voice.personal_assistant.notify_on_call_started', True),
            notify_on_call_completed=config.get('voice.personal_assistant.notify_on_call_completed', True),
            notify_on_task_failed=config.get('voice.personal_assistant.notify_on_task_failed', True),
            always_identify_as_assistant=config.get('voice.personal_assistant.ethics.always_identify', True),
            disclose_ai_when_asked=config.get('voice.personal_assistant.ethics.disclose_ai', True),
            no_impersonation=config.get('voice.personal_assistant.ethics.no_impersonation', True),
            require_approval_for_sensitive=config.get('voice.personal_assistant.ethics.require_approval_sensitive', True),
            enable_learning=config.get('voice.personal_assistant.enable_learning', False),
            enable_adaptation=config.get('voice.personal_assistant.enable_adaptation', True),
            conversation_timeout_seconds=config.get('voice.personal_assistant.conversation_timeout_seconds', 600)
        )


class PersonalAssistantInitializer:
    """Helper class for initializing Personal Assistant feature."""
    
    def __init__(self, 
                 framework_config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Personal Assistant initializer.
        
        Args:
            framework_config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.framework_config = framework_config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("personal_assistant_initializer")
        
        # Load personal assistant configuration
        self.pa_config = PersonalAssistantConfig.from_framework_config(framework_config)
    
    def initialize(self) -> bool:
        """
        Initialize the Personal Assistant feature.
        
        Returns:
            True if initialized successfully
        """
        try:
            if not self.pa_config.enabled:
                self.logger.info("Personal Assistant feature is disabled")
                return False
            
            self.logger.info("Initializing Personal Assistant feature...")
            
            # Create necessary directories
            self._create_directories()
            
            # Initialize personal assistant manager
            manager = initialize_personal_assistant_manager(
                self.framework_config,
                self.audit_logger
            )
            
            if manager:
                self.logger.info("Personal Assistant Manager initialized successfully")
                
                # Log initialization
                if self.audit_logger:
                    from ..core.logging import AuditEventType, SecurityLevel
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="personal_assistant_initialized",
                        details=self.pa_config.to_dict(),
                        security_level=SecurityLevel.MEDIUM
                    )
                
                return True
            else:
                self.logger.error("Failed to initialize Personal Assistant Manager")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing Personal Assistant: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Create necessary directories for Personal Assistant."""
        directories = [
            self.pa_config.recording_path,
            self.pa_config.transcript_path,
            self.pa_config.task_history_path
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.logger.debug(f"Created directory: {directory}")
    
    def shutdown(self) -> None:
        """Shutdown Personal Assistant feature."""
        try:
            self.logger.info("Shutting down Personal Assistant feature...")
            shutdown_personal_assistant_manager()
            self.logger.info("Personal Assistant feature shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down Personal Assistant: {e}")
    
    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate Personal Assistant configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.pa_config.enabled:
            return True, None
        
        # Validate phone provider configuration
        if self.pa_config.phone_provider == "twilio":
            if not all([
                self.pa_config.twilio_account_sid,
                self.pa_config.twilio_auth_token,
                self.pa_config.twilio_phone_number
            ]):
                return False, "Twilio configuration incomplete: account_sid, auth_token, and phone_number required"
        
        elif self.pa_config.phone_provider == "plivo":
            if not all([
                self.pa_config.plivo_auth_id,
                self.pa_config.plivo_auth_token,
                self.pa_config.plivo_phone_number
            ]):
                return False, "Plivo configuration incomplete: auth_id, auth_token, and phone_number required"
        
        elif self.pa_config.phone_provider not in ["mock", "twilio", "plivo"]:
            return False, f"Unknown phone provider: {self.pa_config.phone_provider}"
        
        # Validate paths are writable
        for path in [self.pa_config.recording_path, self.pa_config.transcript_path, self.pa_config.task_history_path]:
            parent_dir = os.path.dirname(path) or '.'
            if not os.access(parent_dir, os.W_OK):
                return False, f"Directory not writable: {path}"
        
        # Validate limits
        if self.pa_config.max_tasks_per_day < 1:
            return False, "max_tasks_per_day must be at least 1"
        
        if self.pa_config.max_active_tasks < 1:
            return False, "max_active_tasks must be at least 1"
        
        if self.pa_config.max_call_duration_minutes < 1 or self.pa_config.max_call_duration_minutes > 60:
            return False, "max_call_duration_minutes must be between 1 and 60"
        
        return True, None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Personal Assistant status.
        
        Returns:
            Status dictionary
        """
        manager = get_personal_assistant_manager()
        
        status = {
            'enabled': self.pa_config.enabled,
            'initialized': manager is not None,
            'phone_provider': self.pa_config.phone_provider,
            'configuration': self.pa_config.to_dict()
        }
        
        if manager:
            status['statistics'] = manager.get_statistics()
            status['active_tasks_count'] = len(manager.get_active_tasks())
        
        return status


def create_default_config_yaml() -> str:
    """
    Create default YAML configuration for Personal Assistant.
    
    Returns:
        YAML configuration string
    """
    return """
# Personal Assistant Configuration
voice:
  personal_assistant:
    # Enable/disable Personal Assistant feature
    enabled: false
    
    # Default settings
    default_persona: professional_assistant
    default_requires_approval: true
    auto_record_calls: true
    max_call_duration_minutes: 10
    
    # Phone provider (mock, twilio, plivo)
    phone_provider: mock
    from_number: null
    
    # Twilio configuration (uncomment and configure if using Twilio)
    # twilio:
    #   account_sid: "your_account_sid_here"
    #   auth_token: "your_auth_token_here"
    #   phone_number: "+1234567890"
    
    # Plivo configuration (uncomment and configure if using Plivo)
    # plivo:
    #   auth_id: "your_auth_id_here"
    #   auth_token: "your_auth_token_here"
    #   phone_number: "+1234567890"
    
    # Storage paths
    recording_path: "recordings/personal_assistant/"
    transcript_path: "transcripts/personal_assistant/"
    task_history_path: "data/personal_assistant/tasks/"
    
    # Rate limiting
    max_tasks_per_day: 50
    max_active_tasks: 5
    
    # Notifications
    notify_on_task_created: false
    notify_on_task_awaiting_approval: true
    notify_on_call_started: true
    notify_on_call_completed: true
    notify_on_task_failed: true
    
    # Ethical safeguards
    ethics:
      always_identify: true
      disclose_ai: true
      no_impersonation: true
      require_approval_sensitive: true
    
    # Advanced settings
    enable_learning: false
    enable_adaptation: true
    conversation_timeout_seconds: 600
""".strip()


def create_example_env_config() -> str:
    """
    Create example .env configuration for Personal Assistant.
    
    Returns:
        .env configuration string
    """
    return """
# Personal Assistant Phone Provider Configuration

# Enable Personal Assistant feature
PERSONAL_ASSISTANT_ENABLED=false

# Phone provider (mock, twilio, plivo)
PERSONAL_ASSISTANT_PHONE_PROVIDER=mock

# Twilio Configuration (if using Twilio)
# TWILIO_ACCOUNT_SID=your_account_sid_here
# TWILIO_AUTH_TOKEN=your_auth_token_here
# TWILIO_PHONE_NUMBER=+1234567890

# Plivo Configuration (if using Plivo)
# PLIVO_AUTH_ID=your_auth_id_here
# PLIVO_AUTH_TOKEN=your_auth_token_here
# PLIVO_PHONE_NUMBER=+1234567890

# Default settings
PERSONAL_ASSISTANT_DEFAULT_PERSONA=professional_assistant
PERSONAL_ASSISTANT_AUTO_RECORD=true
PERSONAL_ASSISTANT_MAX_CALL_DURATION=10
""".strip()


def initialize_personal_assistant_feature(
    framework_config: FrameworkConfig,
    audit_logger: Optional[AuditLogger] = None
) -> bool:
    """
    Initialize the Personal Assistant feature with all dependencies.
    
    Args:
        framework_config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        True if initialization successful
    """
    initializer = PersonalAssistantInitializer(framework_config, audit_logger)
    
    # Validate configuration
    is_valid, error_msg = initializer.validate_configuration()
    if not is_valid:
        logging.error(f"Personal Assistant configuration invalid: {error_msg}")
        return False
    
    # Initialize feature
    return initializer.initialize()


def get_personal_assistant_config(framework_config: FrameworkConfig) -> PersonalAssistantConfig:
    """
    Get Personal Assistant configuration from framework config.
    
    Args:
        framework_config: Framework configuration
        
    Returns:
        PersonalAssistantConfig instance
    """
    return PersonalAssistantConfig.from_framework_config(framework_config)