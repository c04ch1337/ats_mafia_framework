"""
ATS MAFIA Testing Framework Core

This module provides the core testing framework infrastructure including
test cases, test suites, and test management functionality.
"""

import asyncio
import time
import uuid
import inspect
import traceback
from typing import Dict, Any, Optional, List, Callable, Union, Type
from datetime import datetime, timezone
from pathlib import Path
import logging

from .test_types import (
    TestType, TestStatus, TestPriority, TestResult, TestSuiteResult,
    TestExecutionConfig, TestExecutionContext
)
from ..utils import TestUtils


class TestCase:
    """
    Base class for test cases in the ATS MAFIA framework.
    
    All test cases should inherit from this class and implement
    the test methods with appropriate decorators.
    """
    
    def __init__(self, name: str, test_type: TestType = TestType.UNIT):
        """
        Initialize test case.
        
        Args:
            name: Test case name
            test_type: Type of test
        """
        self.name = name
        self.test_type = test_type
        self.test_id = str(uuid.uuid4())
        self.priority = TestPriority.NORMAL
        self.tags: List[str] = []
        self.timeout: float = 300.0
        self.setup_method: Optional[Callable] = None
        self.teardown_method: Optional[Callable] = None
        self.test_method: Optional[Callable] = None
        self.dependencies: List[str] = []
        self.description: str = ""
        self.expected_result: Any = None
        self.assertions: List[str] = []
        
    def setup(self) -> None:
        """Setup method called before test execution."""
        pass
    
    def teardown(self) -> None:
        """Teardown method called after test execution."""
        pass
    
    async def run(self, context: TestExecutionContext) -> TestResult:
        """
        Run the test case.
        
        Args:
            context: Test execution context
            
        Returns:
            Test result
        """
        start_time = datetime.now(timezone.utc)
        result = TestResult(
            test_id=self.test_id,
            test_name=self.name,
            test_type=self.test_type,
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        try:
            # Run setup
            if self.setup_method:
                if asyncio.iscoroutinefunction(self.setup_method):
                    await self.setup_method()
                else:
                    self.setup_method()
            
            # Run test method
            if self.test_method:
                if asyncio.iscoroutinefunction(self.test_method):
                    await asyncio.wait_for(
                        self.test_method(),
                        timeout=self.timeout
                    )
                else:
                    # Run synchronous tests in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.test_method()
                    )
            
            result.status = TestStatus.PASSED
            result.message = "Test passed successfully"
            result.assertions = self.assertions.copy()
            
        except asyncio.TimeoutError:
            result.status = TestStatus.TIMEOUT
            result.error_message = f"Test timed out after {self.timeout} seconds"
            
        except AssertionError as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            
        finally:
            # Run teardown
            try:
                if self.teardown_method:
                    if asyncio.iscoroutinefunction(self.teardown_method):
                        await self.teardown_method()
                    else:
                        self.teardown_method()
            except Exception as e:
                # Log teardown error but don't override test result
                logging.error(f"Error in teardown for test {self.name}: {e}")
            
            result.end_time = datetime.now(timezone.utc)
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result


class TestSuite:
    """
    Test suite for organizing and managing related test cases.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize test suite.
        
        Args:
            name: Suite name
            description: Suite description
        """
        self.name = name
        self.description = description
        self.suite_id = str(uuid.uuid4())
        self.test_cases: List[TestCase] = []
        self.setup_suite_method: Optional[Callable] = None
        self.teardown_suite_method: Optional[Callable] = None
        self.tags: List[str] = []
        
    def add_test(self, test_case: TestCase) -> None:
        """
        Add a test case to the suite.
        
        Args:
            test_case: Test case to add
        """
        self.test_cases.append(test_case)
    
    def remove_test(self, test_id: str) -> bool:
        """
        Remove a test case from the suite.
        
        Args:
            test_id: ID of test case to remove
            
        Returns:
            True if test was removed, False if not found
        """
        for i, test in enumerate(self.test_cases):
            if test.test_id == test_id:
                del self.test_cases[i]
                return True
        return False
    
    def get_test_by_name(self, name: str) -> Optional[TestCase]:
        """
        Get a test case by name.
        
        Args:
            name: Test case name
            
        Returns:
            Test case or None if not found
        """
        for test in self.test_cases:
            if test.name == name:
                return test
        return None
    
    def filter_tests(self, 
                    test_types: Optional[List[TestType]] = None,
                    tags: Optional[List[str]] = None,
                    priorities: Optional[List[TestPriority]] = None) -> List[TestCase]:
        """
        Filter test cases based on criteria.
        
        Args:
            test_types: Filter by test types
            tags: Filter by tags
            priorities: Filter by priorities
            
        Returns:
            Filtered list of test cases
        """
        filtered_tests = self.test_cases.copy()
        
        if test_types:
            filtered_tests = [t for t in filtered_tests if t.test_type in test_types]
        
        if tags:
            filtered_tests = [t for t in filtered_tests if any(tag in t.tags for tag in tags)]
        
        if priorities:
            filtered_tests = [t for t in filtered_tests if t.priority in priorities]
        
        return filtered_tests
    
    async def run(self, context: TestExecutionContext) -> TestSuiteResult:
        """
        Run the test suite.
        
        Args:
            context: Test execution context
            
        Returns:
            Test suite result
        """
        start_time = datetime.now(timezone.utc)
        result = TestSuiteResult(
            suite_id=self.suite_id,
            suite_name=self.name,
            start_time=start_time
        )
        
        try:
            # Run suite setup
            if self.setup_suite_method:
                if asyncio.iscoroutinefunction(self.setup_suite_method):
                    await self.setup_suite_method()
                else:
                    self.setup_suite_method()
            
            # Run test cases
            if context.config.parallel_execution and len(self.test_cases) > 1:
                # Run tests in parallel
                tasks = [test.run(context) for test in self.test_cases]
                test_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, test_result in enumerate(test_results):
                    if isinstance(test_result, Exception):
                        # Handle exceptions in parallel execution
                        error_result = TestResult(
                            test_id=self.test_cases[i].test_id,
                            test_name=self.test_cases[i].name,
                            test_type=self.test_cases[i].test_type,
                            status=TestStatus.ERROR,
                            start_time=start_time,
                            end_time=datetime.now(timezone.utc),
                            error_message=str(test_result),
                            stack_trace=traceback.format_exc()
                        )
                        result.add_result(error_result)
                    else:
                        result.add_result(test_result)
            else:
                # Run tests sequentially
                for test_case in self.test_cases:
                    test_result = await test_case.run(context)
                    result.add_result(test_result)
                    
                    # Stop on first failure if configured
                    if (context.config.stop_on_first_failure and 
                        test_result.status in [TestStatus.FAILED, TestStatus.ERROR]):
                        break
            
        except Exception as e:
            # Add error result for the entire suite
            error_result = TestResult(
                test_id=str(uuid.uuid4()),
                test_name=f"{self.name}_suite_error",
                test_type=TestType.SYSTEM,
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                error_message=f"Suite execution error: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            result.add_result(error_result)
            
        finally:
            # Run suite teardown
            try:
                if self.teardown_suite_method:
                    if asyncio.iscoroutinefunction(self.teardown_suite_method):
                        await self.teardown_suite_method()
                    else:
                        self.teardown_suite_method()
            except Exception as e:
                # Log teardown error but don't override suite result
                logging.error(f"Error in suite teardown for {self.name}: {e}")
            
            result.end_time = datetime.now(timezone.utc)
            result.total_duration = (result.end_time - result.start_time).total_seconds()
        
        return result


class TestFramework:
    """
    Main testing framework class for ATS MAFIA.
    
    Provides comprehensive test management, execution, and reporting capabilities.
    """
    
    def __init__(self, config: TestExecutionConfig):
        """
        Initialize the testing framework.
        
        Args:
            config: Test execution configuration
        """
        self.config = config
        self.test_suites: Dict[str, TestSuite] = {}
        self.global_setup_method: Optional[Callable] = None
        self.global_teardown_method: Optional[Callable] = None
        self.logger = logging.getLogger("test_framework")
        self.test_utils = TestUtils()
        
        # Create output directories
        Path(config.output_directory).mkdir(parents=True, exist_ok=True)
        Path(f"{config.output_directory}/logs").mkdir(parents=True, exist_ok=True)
        Path(f"{config.output_directory}/artifacts").mkdir(parents=True, exist_ok=True)
        Path(f"{config.output_directory}/reports").mkdir(parents=True, exist_ok=True)
    
    def add_suite(self, suite: TestSuite) -> None:
        """
        Add a test suite to the framework.
        
        Args:
            suite: Test suite to add
        """
        self.test_suites[suite.suite_id] = suite
        self.logger.info(f"Added test suite: {suite.name}")
    
    def remove_suite(self, suite_id: str) -> bool:
        """
        Remove a test suite from the framework.
        
        Args:
            suite_id: ID of suite to remove
            
        Returns:
            True if suite was removed, False if not found
        """
        if suite_id in self.test_suites:
            suite_name = self.test_suites[suite_id].name
            del self.test_suites[suite_id]
            self.logger.info(f"Removed test suite: {suite_name}")
            return True
        return False
    
    def get_suite(self, suite_id: str) -> Optional[TestSuite]:
        """
        Get a test suite by ID.
        
        Args:
            suite_id: ID of the suite
            
        Returns:
            Test suite or None if not found
        """
        return self.test_suites.get(suite_id)
    
    def list_suites(self) -> List[TestSuite]:
        """
        List all test suites.
        
        Returns:
            List of test suites
        """
        return list(self.test_suites.values())
    
    def discover_tests(self, test_directory: str) -> None:
        """
        Automatically discover and load tests from a directory.
        
        Args:
            test_directory: Directory to search for tests
        """
        test_path = Path(test_directory)
        
        if not test_path.exists():
            self.logger.warning(f"Test directory does not exist: {test_directory}")
            return
        
        # Look for Python test files
        for py_file in test_path.glob("**/*_test.py"):
            try:
                self._load_tests_from_file(py_file)
            except Exception as e:
                self.logger.error(f"Error loading tests from {py_file}: {e}")
    
    def _load_tests_from_file(self, file_path: Path) -> None:
        """
        Load tests from a Python file.
        
        Args:
            file_path: Path to the test file
        """
        # This is a simplified implementation
        # In a real scenario, you would use importlib to dynamically load modules
        # and inspect them for test methods
        module_name = file_path.stem
        self.logger.info(f"Loading tests from module: {module_name}")
    
    async def run_all_tests(self, framework_config: Dict[str, Any]) -> List[TestSuiteResult]:
        """
        Run all test suites.
        
        Args:
            framework_config: Framework configuration
            
        Returns:
            List of test suite results
        """
        execution_id = str(uuid.uuid4())
        context = TestExecutionContext(
            execution_id=execution_id,
            config=self.config,
            framework_config=framework_config
        )
        
        self.logger.info(f"Starting test execution: {execution_id}")
        
        results = []
        
        try:
            # Run global setup
            if self.global_setup_method:
                if asyncio.iscoroutinefunction(self.global_setup_method):
                    await self.global_setup_method()
                else:
                    self.global_setup_method()
            
            # Run all suites
            if self.config.parallel_execution and len(self.test_suites) > 1:
                # Run suites in parallel
                tasks = [suite.run(context) for suite in self.test_suites.values()]
                suite_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for suite_result in suite_results:
                    if isinstance(suite_result, Exception):
                        self.logger.error(f"Suite execution error: {suite_result}")
                    else:
                        results.append(suite_result)
            else:
                # Run suites sequentially
                for suite in self.test_suites.values():
                    suite_result = await suite.run(context)
                    results.append(suite_result)
                    
                    # Stop on first failure if configured
                    if (self.config.stop_on_first_failure and 
                        any(result.status in [TestStatus.FAILED, TestStatus.ERROR] 
                            for result in suite_result.test_results)):
                        break
        
        except Exception as e:
            self.logger.error(f"Framework execution error: {e}")
            
        finally:
            # Run global teardown
            try:
                if self.global_teardown_method:
                    if asyncio.iscoroutinefunction(self.global_teardown_method):
                        await self.global_teardown_method()
                    else:
                        self.global_teardown_method()
            except Exception as e:
                self.logger.error(f"Error in global teardown: {e}")
        
        self.logger.info(f"Test execution completed: {execution_id}")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get framework statistics.
        
        Returns:
            Dictionary containing framework statistics
        """
        total_tests = sum(len(suite.test_cases) for suite in self.test_suites.values())
        
        tests_by_type = {}
        tests_by_priority = {}
        
        for suite in self.test_suites.values():
            for test in suite.test_cases:
                # Count by type
                test_type = test.test_type.value
                tests_by_type[test_type] = tests_by_type.get(test_type, 0) + 1
                
                # Count by priority
                priority = test.priority.value
                tests_by_priority[priority] = tests_by_priority.get(priority, 0) + 1
        
        return {
            'total_suites': len(self.test_suites),
            'total_tests': total_tests,
            'tests_by_type': tests_by_type,
            'tests_by_priority': tests_by_priority,
            'config': self.config.to_dict()
        }