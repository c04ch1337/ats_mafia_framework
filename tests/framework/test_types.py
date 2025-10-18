"""
ATS MAFIA Testing Framework Types

This module defines the core types and enums for the testing framework.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


class TestType(Enum):
    """Types of tests in the framework."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    UI = "ui"
    API = "api"


class TestStatus(Enum):
    """Status of test execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


class TestPriority(Enum):
    """Priority levels for tests."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TestResult:
    """Result of a test execution."""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    message: str = ""
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    assertions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.start_time.tzinfo is None:
            self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        
        if self.end_time and self.end_time.tzinfo is None:
            self.end_time = self.end_time.replace(tzinfo=timezone.utc)
        
        if self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test result to dictionary."""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'message': self.message,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'assertions': self.assertions,
            'metrics': self.metrics,
            'artifacts': self.artifacts,
            'tags': self.tags
        }


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_id: str
    suite_name: str
    test_results: List[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    total_duration: float = 0.0
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        self.total_tests = len(self.test_results)
        self.passed_tests = sum(1 for result in self.test_results if result.status == TestStatus.PASSED)
        self.failed_tests = sum(1 for result in self.test_results if result.status == TestStatus.FAILED)
        self.skipped_tests = sum(1 for result in self.test_results if result.status == TestStatus.SKIPPED)
        self.error_tests = sum(1 for result in self.test_results if result.status == TestStatus.ERROR)
        
        if self.end_time and self.start_time:
            self.total_duration = (self.end_time - self.start_time).total_seconds()
        else:
            self.total_duration = sum(result.duration for result in self.test_results)
    
    def add_result(self, result: TestResult) -> None:
        """Add a test result to the suite."""
        self.test_results.append(result)
        self.total_tests = len(self.test_results)
        
        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
        elif result.status == TestStatus.ERROR:
            self.error_tests += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate of the suite."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suite result to dictionary."""
        return {
            'suite_id': self.suite_id,
            'suite_name': self.suite_name,
            'test_results': [result.to_dict() for result in self.test_results],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'error_tests': self.error_tests,
            'total_duration': self.total_duration,
            'success_rate': self.get_success_rate()
        }


@dataclass
class TestExecutionConfig:
    """Configuration for test execution."""
    parallel_execution: bool = True
    max_workers: int = 4
    timeout: float = 300.0  # 5 minutes default
    retry_failed: bool = False
    max_retries: int = 2
    stop_on_first_failure: bool = False
    generate_reports: bool = True
    output_directory: str = "test_results"
    log_level: str = "INFO"
    test_filters: List[str] = field(default_factory=list)
    test_tags: List[str] = field(default_factory=list)
    test_priorities: List[TestPriority] = field(default_factory=list)
    environment_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'parallel_execution': self.parallel_execution,
            'max_workers': self.max_workers,
            'timeout': self.timeout,
            'retry_failed': self.retry_failed,
            'max_retries': self.max_retries,
            'stop_on_first_failure': self.stop_on_first_failure,
            'generate_reports': self.generate_reports,
            'output_directory': self.output_directory,
            'log_level': self.log_level,
            'test_filters': self.test_filters,
            'test_tags': self.test_tags,
            'test_priorities': [p.value for p in self.test_priorities],
            'environment_config': self.environment_config
        }


@dataclass
class TestExecutionContext:
    """Context for test execution."""
    execution_id: str
    config: TestExecutionConfig
    framework_config: Dict[str, Any]
    environment: str = "test"
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    artifacts_directory: str = ""
    log_file: str = ""
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        if not self.artifacts_directory:
            self.artifacts_directory = f"{self.config.output_directory}/artifacts/{self.execution_id}"
        
        if not self.log_file:
            self.log_file = f"{self.config.output_directory}/logs/{self.execution_id}.log"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'execution_id': self.execution_id,
            'config': self.config.to_dict(),
            'framework_config': self.framework_config,
            'environment': self.environment,
            'start_time': self.start_time.isoformat(),
            'artifacts_directory': self.artifacts_directory,
            'log_file': self.log_file
        }