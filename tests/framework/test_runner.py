"""
ATS MAFIA Test Runner

This module provides the test runner implementation for executing
test suites and managing test execution workflows.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from pathlib import Path
import logging

from .test_types import (
    TestType, TestStatus, TestPriority, TestExecutionConfig, 
    TestExecutionContext, TestSuiteResult
)
from .test_framework import TestFramework, TestSuite, TestCase
from ..reports import TestReporter


class TestRunner:
    """
    Test runner for executing ATS MAFIA test suites.
    
    Provides comprehensive test execution management including
    parallel execution, retry logic, and detailed reporting.
    """
    
    def __init__(self, config: TestExecutionConfig):
        """
        Initialize the test runner.
        
        Args:
            config: Test execution configuration
        """
        self.config = config
        self.logger = logging.getLogger("test_runner")
        self.framework: Optional[TestFramework] = None
        self.reporter: Optional[TestReporter] = None
        self.execution_hooks: Dict[str, List[Callable]] = {
            'before_execution': [],
            'after_execution': [],
            'before_suite': [],
            'after_suite': [],
            'before_test': [],
            'after_test': []
        }
        
    def register_hook(self, event: str, hook: Callable) -> None:
        """
        Register a hook for a specific event.
        
        Args:
            event: Event name (before_execution, after_execution, etc.)
            hook: Hook function to register
        """
        if event not in self.execution_hooks:
            self.execution_hooks[event] = []
        self.execution_hooks[event].append(hook)
    
    async def _call_hooks(self, event: str, *args, **kwargs) -> None:
        """
        Call all hooks for a specific event.
        
        Args:
            event: Event name
            *args: Arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks
        """
        for hook in self.execution_hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args, **kwargs)
                else:
                    hook(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in {event} hook: {e}")
    
    def set_framework(self, framework: TestFramework) -> None:
        """
        Set the test framework.
        
        Args:
            framework: Test framework instance
        """
        self.framework = framework
        
    def set_reporter(self, reporter: TestReporter) -> None:
        """
        Set the test reporter.
        
        Args:
            reporter: Test reporter instance
        """
        self.reporter = reporter
    
    async def run_tests(self, 
                       framework_config: Dict[str, Any],
                       test_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run tests with the configured framework.
        
        Args:
            framework_config: Framework configuration
            test_filters: Optional list of test filters
            
        Returns:
            Dictionary containing execution results and metadata
        """
        if not self.framework:
            raise ValueError("No test framework configured")
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Starting test execution: {execution_id}")
        
        # Create execution context
        context = TestExecutionContext(
            execution_id=execution_id,
            config=self.config,
            framework_config=framework_config
        )
        
        # Apply test filters if provided
        if test_filters:
            framework_config['test_filters'] = test_filters
        
        # Call before execution hooks
        await self._call_hooks('before_execution', context)
        
        try:
            # Run the tests
            results = await self.framework.run_all_tests(framework_config)
            
            # Calculate overall statistics
            total_tests = sum(result.total_tests for result in results)
            total_passed = sum(result.passed_tests for result in results)
            total_failed = sum(result.failed_tests for result in results)
            total_skipped = sum(result.skipped_tests for result in results)
            total_errors = sum(result.error_tests for result in results)
            total_duration = sum(result.total_duration for result in results)
            
            execution_result = {
                'execution_id': execution_id,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'total_duration': total_duration,
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_failed,
                'skipped_tests': total_skipped,
                'error_tests': total_errors,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
                'suite_results': [result.to_dict() for result in results],
                'framework_config': framework_config,
                'test_config': self.config.to_dict()
            }
            
            # Generate reports if configured
            if self.config.generate_reports and self.reporter:
                await self.reporter.generate_reports(execution_result, context)
            
            # Call after execution hooks
            await self._call_hooks('after_execution', execution_result)
            
            self.logger.info(f"Test execution completed: {execution_id}")
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            
            # Create error result
            error_result = {
                'execution_id': execution_id,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'total_duration': (datetime.now(timezone.utc) - start_time).total_seconds(),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'error_tests': 1,
                'success_rate': 0,
                'suite_results': [],
                'framework_config': framework_config,
                'test_config': self.config.to_dict(),
                'error': str(e)
            }
            
            # Call after execution hooks
            await self._call_hooks('after_execution', error_result)
            
            return error_result
    
    async def run_specific_suite(self, 
                                suite_id: str,
                                framework_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Run a specific test suite.
        
        Args:
            suite_id: ID of the suite to run
            framework_config: Framework configuration
            
        Returns:
            Dictionary containing execution results or None if suite not found
        """
        if not self.framework:
            raise ValueError("No test framework configured")
        
        suite = self.framework.get_suite(suite_id)
        if not suite:
            self.logger.error(f"Test suite not found: {suite_id}")
            return None
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Starting suite execution: {suite.name} ({execution_id})")
        
        # Create execution context
        context = TestExecutionContext(
            execution_id=execution_id,
            config=self.config,
            framework_config=framework_config
        )
        
        # Call before suite hooks
        await self._call_hooks('before_suite', suite, context)
        
        try:
            # Run the suite
            result = await suite.run(context)
            
            suite_result = {
                'execution_id': execution_id,
                'suite_id': suite_id,
                'suite_name': suite.name,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'total_duration': result.total_duration,
                'total_tests': result.total_tests,
                'passed_tests': result.passed_tests,
                'failed_tests': result.failed_tests,
                'skipped_tests': result.skipped_tests,
                'error_tests': result.error_tests,
                'success_rate': result.get_success_rate(),
                'test_results': [test_result.to_dict() for test_result in result.test_results],
                'framework_config': framework_config,
                'test_config': self.config.to_dict()
            }
            
            # Generate suite report if configured
            if self.config.generate_reports and self.reporter:
                await self.reporter.generate_suite_report(suite_result, context)
            
            # Call after suite hooks
            await self._call_hooks('after_suite', suite, suite_result)
            
            self.logger.info(f"Suite execution completed: {suite.name}")
            return suite_result
            
        except Exception as e:
            self.logger.error(f"Suite execution failed: {e}")
            
            # Create error result
            error_result = {
                'execution_id': execution_id,
                'suite_id': suite_id,
                'suite_name': suite.name,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'total_duration': (datetime.now(timezone.utc) - start_time).total_seconds(),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'error_tests': 1,
                'success_rate': 0,
                'test_results': [],
                'framework_config': framework_config,
                'test_config': self.config.to_dict(),
                'error': str(e)
            }
            
            # Call after suite hooks
            await self._call_hooks('after_suite', suite, error_result)
            
            return error_result
    
    async def run_failed_tests(self, 
                              previous_results: Dict[str, Any],
                              framework_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-run only the failed tests from a previous execution.
        
        Args:
            previous_results: Results from previous execution
            framework_config: Framework configuration
            
        Returns:
            Dictionary containing execution results
        """
        if not self.framework:
            raise ValueError("No test framework configured")
        
        # Extract failed tests from previous results
        failed_tests = []
        for suite_result in previous_results.get('suite_results', []):
            for test_result in suite_result.get('test_results', []):
                if test_result.get('status') in ['failed', 'error']:
                    failed_tests.append(test_result)
        
        if not failed_tests:
            self.logger.info("No failed tests to re-run")
            return {'message': 'No failed tests to re-run'}
        
        self.logger.info(f"Re-running {len(failed_tests)} failed tests")
        
        # Create a temporary framework with only failed tests
        temp_framework = TestFramework(self.config)
        
        # This is a simplified implementation
        # In a real scenario, you would need to reconstruct the test cases
        # from the previous results
        
        # For now, just return the previous failed tests as results
        retry_results = {
            'execution_id': str(uuid.uuid4()),
            'start_time': datetime.now(timezone.utc).isoformat(),
            'end_time': datetime.now(timezone.utc).isoformat(),
            'total_duration': 0,
            'total_tests': len(failed_tests),
            'passed_tests': 0,
            'failed_tests': len(failed_tests),
            'skipped_tests': 0,
            'error_tests': 0,
            'success_rate': 0,
            'suite_results': [],
            'framework_config': framework_config,
            'test_config': self.config.to_dict(),
            'retry_of': previous_results.get('execution_id'),
            'failed_tests': failed_tests
        }
        
        return retry_results
    
    def get_execution_summary(self, results: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of test execution results.
        
        Args:
            results: Test execution results
            
        Returns:
            Formatted summary string
        """
        total_tests = results.get('total_tests', 0)
        passed_tests = results.get('passed_tests', 0)
        failed_tests = results.get('failed_tests', 0)
        skipped_tests = results.get('skipped_tests', 0)
        error_tests = results.get('error_tests', 0)
        success_rate = results.get('success_rate', 0)
        duration = results.get('total_duration', 0)
        
        summary = f"""
Test Execution Summary
=======================
Execution ID: {results.get('execution_id', 'Unknown')}
Start Time: {results.get('start_time', 'Unknown')}
End Time: {results.get('end_time', 'Unknown')}
Duration: {duration:.2f} seconds

Results:
--------
Total Tests: {total_tests}
Passed: {passed_tests}
Failed: {failed_tests}
Skipped: {skipped_tests}
Errors: {error_tests}
Success Rate: {success_rate:.1f}%

Status: {'PASSED' if failed_tests + error_tests == 0 else 'FAILED'}
"""
        
        return summary
    
    async def save_results(self, results: Dict[str, Any], file_path: str) -> None:
        """
        Save test execution results to a file.
        
        Args:
            results: Test execution results
            file_path: Path to save results
        """
        try:
            results_path = Path(file_path)
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Results saved to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    async def load_results(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load test execution results from a file.
        
        Args:
            file_path: Path to load results from
            
        Returns:
            Test execution results or None if file not found
        """
        try:
            results_path = Path(file_path)
            
            if not results_path.exists():
                self.logger.error(f"Results file not found: {file_path}")
                return None
            
            with open(results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            self.logger.info(f"Results loaded from: {file_path}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to load results: {e}")
            return None


class TestExecutionResult:
    """
    Wrapper class for test execution results with additional utility methods.
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize execution result wrapper.
        
        Args:
            results: Raw test execution results
        """
        self.results = results
        
    @property
    def is_success(self) -> bool:
        """Check if the execution was successful."""
        return (self.results.get('failed_tests', 0) + 
                self.results.get('error_tests', 0)) == 0
    
    @property
    def total_tests(self) -> int:
        """Get total number of tests."""
        return self.results.get('total_tests', 0)
    
    @property
    def passed_tests(self) -> int:
        """Get number of passed tests."""
        return self.results.get('passed_tests', 0)
    
    @property
    def failed_tests(self) -> int:
        """Get number of failed tests."""
        return self.results.get('failed_tests', 0)
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        return self.results.get('success_rate', 0.0)
    
    def get_failed_test_names(self) -> List[str]:
        """Get list of failed test names."""
        failed_tests = []
        for suite_result in self.results.get('suite_results', []):
            for test_result in suite_result.get('test_results', []):
                if test_result.get('status') in ['failed', 'error']:
                    failed_tests.append(test_result.get('test_name', 'Unknown'))
        return failed_tests
    
    def get_suite_results(self, suite_name: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific suite."""
        for suite_result in self.results.get('suite_results', []):
            if suite_result.get('suite_name') == suite_name:
                return suite_result
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Get raw results dictionary."""
        return self.results.copy()