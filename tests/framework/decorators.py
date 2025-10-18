"""
ATS MAFIA Testing Framework Decorators

This module provides decorators for marking and configuring test methods
in the ATS MAFIA testing framework.
"""

import functools
import time
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timezone

from .test_types import TestType, TestPriority
from .test_framework import TestCase


def test(
    name: Optional[str] = None,
    description: str = "",
    test_type: TestType = TestType.UNIT,
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 300.0,
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    expected_result: Any = None,
    retry_count: int = 0,
    skip: bool = False,
    skip_reason: str = ""
):
    """
    Decorator for marking test methods.
    
    Args:
        name: Test name (defaults to method name)
        description: Test description
        test_type: Type of test
        priority: Test priority
        timeout: Test timeout in seconds
        tags: Test tags
        dependencies: List of test dependencies
        expected_result: Expected result
        retry_count: Number of retries on failure
        skip: Whether to skip the test
        skip_reason: Reason for skipping
        
    Returns:
        Decorated test method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store test metadata on the function
        wrapper._test_metadata = {
            'name': name or func.__name__,
            'description': description,
            'test_type': test_type,
            'priority': priority,
            'timeout': timeout,
            'tags': tags or [],
            'dependencies': dependencies or [],
            'expected_result': expected_result,
            'retry_count': retry_count,
            'skip': skip,
            'skip_reason': skip_reason,
            'function': func
        }
        
        return wrapper
    
    return decorator


def unit_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 30.0,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for unit tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    return test(
        name=name,
        description=description,
        test_type=TestType.UNIT,
        priority=priority,
        timeout=timeout,
        tags=tags or [],
        **kwargs
    )


def integration_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 300.0,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for integration tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    return test(
        name=name,
        description=description,
        test_type=TestType.INTEGRATION,
        priority=priority,
        timeout=timeout,
        tags=tags or [],
        **kwargs
    )


def system_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 600.0,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for system tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    return test(
        name=name,
        description=description,
        test_type=TestType.SYSTEM,
        priority=priority,
        timeout=timeout,
        tags=tags or [],
        **kwargs
    )


def performance_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 900.0,
    max_response_time: Optional[float] = None,
    max_memory_usage: Optional[str] = None,
    max_cpu_usage: Optional[float] = None,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for performance tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        max_response_time: Maximum acceptable response time
        max_memory_usage: Maximum acceptable memory usage
        max_cpu_usage: Maximum acceptable CPU usage percentage
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    performance_tags = tags or []
    performance_tags.append('performance')
    
    return test(
        name=name,
        description=description,
        test_type=TestType.PERFORMANCE,
        priority=priority,
        timeout=timeout,
        tags=performance_tags,
        **kwargs
    )


def security_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.HIGH,
    timeout: float = 600.0,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for security tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    security_tags = tags or []
    security_tags.append('security')
    
    return test(
        name=name,
        description=description,
        test_type=TestType.SECURITY,
        priority=priority,
        timeout=timeout,
        tags=security_tags,
        **kwargs
    )


def compliance_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.HIGH,
    timeout: float = 300.0,
    compliance_standard: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for compliance tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        compliance_standard: Compliance standard being tested
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    compliance_tags = tags or []
    compliance_tags.append('compliance')
    if compliance_standard:
        compliance_tags.append(compliance_standard)
    
    return test(
        name=name,
        description=description,
        test_type=TestType.COMPLIANCE,
        priority=priority,
        timeout=timeout,
        tags=compliance_tags,
        **kwargs
    )


def ui_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 300.0,
    browser: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for UI tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        browser: Target browser for the test
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    ui_tags = tags or []
    ui_tags.append('ui')
    if browser:
        ui_tags.append(browser)
    
    return test(
        name=name,
        description=description,
        test_type=TestType.UI,
        priority=priority,
        timeout=timeout,
        tags=ui_tags,
        **kwargs
    )


def api_test(
    name: Optional[str] = None,
    description: str = "",
    priority: TestPriority = TestPriority.NORMAL,
    timeout: float = 300.0,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs
):
    """
    Decorator for API tests.
    
    Args:
        name: Test name
        description: Test description
        priority: Test priority
        timeout: Test timeout in seconds
        endpoint: API endpoint being tested
        method: HTTP method being tested
        tags: Test tags
        **kwargs: Additional test arguments
        
    Returns:
        Decorated test method
    """
    api_tags = tags or []
    api_tags.append('api')
    if method:
        api_tags.append(method.lower())
    
    return test(
        name=name,
        description=description,
        test_type=TestType.API,
        priority=priority,
        timeout=timeout,
        tags=api_tags,
        **kwargs
    )


def setup_test(func: Callable) -> Callable:
    """
    Decorator for test setup methods.
    
    Args:
        func: Setup function
        
    Returns:
        Decorated setup method
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._is_setup = True
    return wrapper


def teardown_test(func: Callable) -> Callable:
    """
    Decorator for test teardown methods.
    
    Args:
        func: Teardown function
        
    Returns:
        Decorated teardown method
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._is_teardown = True
    return wrapper


def setup_suite(func: Callable) -> Callable:
    """
    Decorator for suite setup methods.
    
    Args:
        func: Suite setup function
        
    Returns:
        Decorated suite setup method
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._is_suite_setup = True
    return wrapper


def teardown_suite(func: Callable) -> Callable:
    """
    Decorator for suite teardown methods.
    
    Args:
        func: Suite teardown function
        
    Returns:
        Decorated suite teardown method
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._is_suite_teardown = True
    return wrapper


def benchmark(
    iterations: int = 1000,
    warmup_iterations: int = 100,
    min_time: float = 1.0
):
    """
    Decorator for benchmarking test performance.
    
    Args:
        iterations: Number of iterations to run
        warmup_iterations: Number of warmup iterations
        min_time: Minimum time to run (seconds)
        
    Returns:
        Decorated benchmark method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Warmup
            for _ in range(warmup_iterations):
                func(*args, **kwargs)
            
            # Benchmark
            start_time = time.time()
            iteration_times = []
            
            for i in range(iterations):
                iter_start = time.time()
                func(*args, **kwargs)
                iter_time = time.time() - iter_start
                iteration_times.append(iter_time)
                
                # Stop if minimum time reached
                if time.time() - start_time >= min_time:
                    break
            
            total_time = time.time() - start_time
            actual_iterations = len(iteration_times)
            
            # Calculate statistics
            avg_time = sum(iteration_times) / actual_iterations
            min_iter_time = min(iteration_times)
            max_iter_time = max(iteration_times)
            
            # Store benchmark results
            wrapper._benchmark_results = {
                'iterations': actual_iterations,
                'total_time': total_time,
                'avg_time': avg_time,
                'min_time': min_iter_time,
                'max_time': max_iter_time,
                'throughput': actual_iterations / total_time
            }
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def flaky(
    max_attempts: int = 3,
    retry_delay: float = 1.0
):
    """
    Decorator for flaky tests that may need retries.
    
    Args:
        max_attempts: Maximum number of attempts
        retry_delay: Delay between retries (seconds)
        
    Returns:
        Decorated flaky test method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(retry_delay)
                    else:
                        raise last_exception
            
            return func(*args, **kwargs)
        
        wrapper._is_flaky = True
        wrapper._max_attempts = max_attempts
        wrapper._retry_delay = retry_delay
        
        return wrapper
    
    return decorator


def slow_test(
    reason: str = "Test is slow by nature"
):
    """
    Decorator for marking slow tests.
    
    Args:
        reason: Reason why the test is slow
        
    Returns:
        Decorated slow test method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._is_slow = True
        wrapper._slow_reason = reason
        
        return wrapper
    
    return decorator