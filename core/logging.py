"""
ATS MAFIA Framework Logging and Audit Trail System

This module provides comprehensive logging and audit trail functionality for the ATS MAFIA framework.
It includes structured logging, security event tracking, performance monitoring, and compliance reporting.
"""

import logging
import logging.handlers
import json
import time
import uuid
import threading
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import atexit
from contextlib import contextmanager
import sys
import traceback

try:
    from ..config.settings import FrameworkConfig as ConfigFrameworkConfig
    FrameworkConfig = ConfigFrameworkConfig
except ImportError as e:
    print(f"Error importing FrameworkConfig: {e}")
    # Create a minimal fallback config
    class FrameworkConfig:
        def __init__(self):
            self.log_level = "INFO"
            self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            self.log_file_path = "logs/ats_mafia.log"
            self.max_file_size = "10MB"
            self.backup_count = 5
            self.audit_enabled = True
            self.audit_file_path = "logs/audit.log"


class LogLevel(Enum):
    """Log levels for the framework."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEventType(Enum):
    """Types of audit events."""
    AGENT_ACTION = "agent_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    TRAINING_EVENT = "training_event"
    COMMUNICATION_EVENT = "communication_event"
    TOOL_EXECUTION = "tool_execution"
    CONFIG_CHANGE = "config_change"
    ERROR_EVENT = "error_event"
    PERFORMANCE_METRIC = "performance_metric"


class SecurityLevel(Enum):
    """Security levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    security_level: SecurityLevel
    source: str
    action: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['security_level'] = self.security_level.value
        return data


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


class AuditLogger:
    """
    Comprehensive audit logging system for ATS MAFIA framework.
    
    Provides structured logging, security event tracking, and compliance reporting
    with support for multiple output formats and destinations.
    """
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the audit logger.
        
        Args:
            config: Framework configuration instance
        """
        self.config = config
        self.logger = self._setup_logger()
        self.audit_queue = queue.Queue()
        self.audit_thread = None
        self.shutdown_event = threading.Event()
        self.session_id = str(uuid.uuid4())
        
        # Start audit processing thread
        self._start_audit_thread()
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the main framework logger."""
        logger = logging.getLogger('ats_mafia')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create logs directory if it doesn't exist
        log_path = Path(self.config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.config.log_file_path,
            maxBytes=self._parse_size(self.config.max_file_size),
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.config.log_format))
        logger.addHandler(console_handler)
        
        return logger
    
    def _start_audit_thread(self) -> None:
        """Start the audit processing thread."""
        if self.config.audit_enabled:
            self.audit_thread = threading.Thread(
                target=self._audit_worker,
                name="AuditLogger",
                daemon=True
            )
            self.audit_thread.start()
    
    def _audit_worker(self) -> None:
        """Audit event processing worker thread."""
        # Create audit log directory
        audit_path = Path(self.config.audit_file_path)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        
        while not self.shutdown_event.is_set():
            try:
                # Get audit event with timeout
                event = self.audit_queue.get(timeout=1.0)
                self._write_audit_event(event)
                self.audit_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audit event: {e}")
    
    def _write_audit_event(self, event: AuditEvent) -> None:
        """
        Write audit event to audit log.
        
        Args:
            event: Audit event to write
        """
        try:
            with open(self.config.audit_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write audit event: {e}")
    
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields to include in structured log
        """
        extra_fields = {
            'session_id': self.session_id,
            **kwargs
        }
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.value),
            '',  # pathname
            0,   # lineno
            message,
            (),  # args
            None  # exc_info
        )
        log_record.extra_fields = extra_fields
        
        self.logger.handle(log_record)
    
    def audit(self,
              event_type: AuditEventType,
              action: str,
              details: Dict[str, Any],
              security_level: SecurityLevel = SecurityLevel.LOW,
              source: str = "system",
              user_id: Optional[str] = None,
              agent_id: Optional[str] = None,
              ip_address: Optional[str] = None,
              user_agent: Optional[str] = None,
              success: bool = True,
              error_message: Optional[str] = None) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            action: Action being performed
            details: Additional event details
            security_level: Security level of the event
            source: Source of the event
            user_id: User ID if applicable
            agent_id: Agent ID if applicable
            ip_address: IP address if applicable
            user_agent: User agent if applicable
            success: Whether the action was successful
            error_message: Error message if action failed
        """
        if not self.config.audit_enabled:
            return
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            security_level=security_level,
            source=source,
            action=action,
            details=details,
            user_id=user_id,
            session_id=self.session_id,
            agent_id=agent_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        try:
            self.audit_queue.put_nowait(event)
        except queue.Full:
            self.logger.error("Audit queue is full, dropping audit event")
    
    def agent_action(self,
                     agent_id: str,
                     action: str,
                     details: Dict[str, Any],
                     success: bool = True,
                     error_message: Optional[str] = None) -> None:
        """
        Log an agent action.
        
        Args:
            agent_id: ID of the agent
            action: Action performed by the agent
            details: Additional details about the action
            success: Whether the action was successful
            error_message: Error message if action failed
        """
        self.audit(
            event_type=AuditEventType.AGENT_ACTION,
            action=action,
            details=details,
            security_level=SecurityLevel.MEDIUM,
            source="agent",
            agent_id=agent_id,
            success=success,
            error_message=error_message
        )
    
    def security_event(self,
                       action: str,
                       details: Dict[str, Any],
                       security_level: SecurityLevel = SecurityLevel.HIGH,
                       user_id: Optional[str] = None,
                       ip_address: Optional[str] = None) -> None:
        """
        Log a security event.
        
        Args:
            action: Security action or event
            details: Additional details about the security event
            security_level: Security level of the event
            user_id: User ID if applicable
            ip_address: IP address if applicable
        """
        self.audit(
            event_type=AuditEventType.SECURITY_EVENT,
            action=action,
            details=details,
            security_level=security_level,
            source="security",
            user_id=user_id,
            ip_address=ip_address
        )
    
    def training_event(self,
                       action: str,
                       details: Dict[str, Any],
                       session_id: Optional[str] = None,
                       agent_id: Optional[str] = None) -> None:
        """
        Log a training event.
        
        Args:
            action: Training action or event
            details: Additional details about the training event
            session_id: Training session ID
            agent_id: Agent ID if applicable
        """
        self.audit(
            event_type=AuditEventType.TRAINING_EVENT,
            action=action,
            details=details,
            security_level=SecurityLevel.LOW,
            source="training",
            agent_id=agent_id
        )
    
    def tool_execution(self,
                       tool_name: str,
                       action: str,
                       details: Dict[str, Any],
                       agent_id: Optional[str] = None,
                       success: bool = True,
                       error_message: Optional[str] = None) -> None:
        """
        Log a tool execution event.
        
        Args:
            tool_name: Name of the tool being executed
            action: Action being performed with the tool
            details: Additional details about the tool execution
            agent_id: Agent ID if applicable
            success: Whether the tool execution was successful
            error_message: Error message if execution failed
        """
        tool_details = {
            'tool_name': tool_name,
            **details
        }
        
        self.audit(
            event_type=AuditEventType.TOOL_EXECUTION,
            action=action,
            details=tool_details,
            security_level=SecurityLevel.MEDIUM,
            source="tool_system",
            agent_id=agent_id,
            success=success,
            error_message=error_message
        )
    
    def communication_event(self,
                           action: str,
                           details: Dict[str, Any],
                           from_agent: Optional[str] = None,
                           to_agent: Optional[str] = None) -> None:
        """
        Log a communication event.
        
        Args:
            action: Communication action
            details: Additional details about the communication
            from_agent: ID of the sending agent
            to_agent: ID of the receiving agent
        """
        comm_details = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            **details
        }
        
        self.audit(
            event_type=AuditEventType.COMMUNICATION_EVENT,
            action=action,
            details=comm_details,
            security_level=SecurityLevel.LOW,
            source="communication"
        )
    
    def config_change(self,
                      action: str,
                      details: Dict[str, Any],
                      user_id: Optional[str] = None) -> None:
        """
        Log a configuration change event.
        
        Args:
            action: Configuration change action
            details: Details about the configuration change
            user_id: User ID if applicable
        """
        self.audit(
            event_type=AuditEventType.CONFIG_CHANGE,
            action=action,
            details=details,
            security_level=SecurityLevel.HIGH,
            source="config",
            user_id=user_id
        )
    
    def performance_metric(self,
                          metric_name: str,
                          value: Union[int, float],
                          details: Dict[str, Any]) -> None:
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the performance metric
            value: Metric value
            details: Additional details about the metric
        """
        metric_details = {
            'metric_name': metric_name,
            'value': value,
            **details
        }
        
        self.audit(
            event_type=AuditEventType.PERFORMANCE_METRIC,
            action="metric_recorded",
            details=metric_details,
            security_level=SecurityLevel.LOW,
            source="performance"
        )
    
    @contextmanager
    def audit_context(self,
                      event_type: AuditEventType,
                      action: str,
                      details: Dict[str, Any],
                      **kwargs):
        """
        Context manager for auditing operations.
        
        Args:
            event_type: Type of audit event
            action: Action being performed
            details: Additional event details
            **kwargs: Additional arguments for audit event
        """
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            # Add execution time to details
            details['execution_time'] = time.time() - start_time
            
            self.audit(
                event_type=event_type,
                action=action,
                details=details,
                success=success,
                error_message=error_message,
                **kwargs
            )
    
    def get_audit_events(self,
                         event_type: Optional[AuditEventType] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit events from the audit log.
        
        Args:
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events to return
            
        Returns:
            List of audit event dictionaries
        """
        events = []
        
        try:
            with open(self.config.audit_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event_timestamp = datetime.fromisoformat(event_data['timestamp'])
                        
                        # Apply filters
                        if event_type and event_data['event_type'] != event_type.value:
                            continue
                        
                        if start_time and event_timestamp < start_time:
                            continue
                        
                        if end_time and event_timestamp > end_time:
                            continue
                        
                        events.append(event_data)
                        
                        if len(events) >= limit:
                            break
                            
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
                        
        except FileNotFoundError:
            self.logger.warning("Audit log file not found")
        
        return events
    
    def shutdown(self) -> None:
        """Shutdown the audit logger gracefully."""
        if self.audit_thread:
            self.shutdown_event.set()
            self.audit_thread.join(timeout=5.0)
        
        # Process any remaining audit events
        while not self.audit_queue.empty():
            try:
                event = self.audit_queue.get_nowait()
                self._write_audit_event(event)
                self.audit_queue.task_done()
            except queue.Empty:
                break
    
    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes.
        
        Args:
            size_str: Size string (e.g., "10MB", "1GB")
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    """
    Get the global audit logger instance.
    
    Returns:
        Global AuditLogger instance or None if not initialized
    """
    return _global_audit_logger


def initialize_audit_logger(config: FrameworkConfig) -> AuditLogger:
    """
    Initialize the global audit logger.
    
    Args:
        config: Framework configuration instance
        
    Returns:
        Initialized AuditLogger instance
    """
    global _global_audit_logger
    _global_audit_logger = AuditLogger(config)
    return _global_audit_logger


def shutdown_audit_logger() -> None:
    """Shutdown the global audit logger."""
    global _global_audit_logger
    if _global_audit_logger:
        _global_audit_logger.shutdown()
        _global_audit_logger = None