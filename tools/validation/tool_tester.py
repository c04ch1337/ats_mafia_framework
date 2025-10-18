"""
ATS MAFIA Framework - Tool Tester

Automated testing framework for tools.
Provides unit tests, integration tests, and performance benchmarks.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ...core.tool_system import Tool, ToolExecutionResult
from .tool_validator import ToolValidator


@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    tool_id: str
    passed: bool
    execution_time: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'tool_id': self.tool_id,
            'passed': self.passed,
            'execution_time': self.execution_time,
            'error': self.error,
            'details': self.details
        }


class ToolTester:
    """
    Automated testing framework for tools.
    
    Provides:
    - Unit tests for individual tools
    - Integration tests
    - Performance benchmarks
    - Safety verification
    """
    
    def __init__(self):
        """Initialize tool tester."""
        self.logger = logging.getLogger("tool_tester")
        self.validator = ToolValidator()
        self.test_results: List[TestResult] = []
    
    async def test_tool(self, tool: Tool, test_parameters: Optional[Dict[str, Any]] = None) -> List[TestResult]:
        """
        Run comprehensive tests on a tool.
        
        Args:
            tool: Tool to test
            test_parameters: Optional test parameters
            
        Returns:
            List of test results
        """
        results = []
        
        # Test 1: Validation
        results.append(await self._test_validation(tool))
        
        # Test 2: Parameter validation
        results.append(await self._test_parameter_validation(tool, test_parameters))
        
        # Test 3: Execution
        if test_parameters:
            results.append(await self._test_execution(tool, test_parameters))
        
        # Test 4: Error handling
        results.append(await self._test_error_handling(tool))
        
        # Test 5: Performance
        if test_parameters:
            results.append(await self._test_performance(tool, test_parameters))
        
        self.test_results.extend(results)
        return results
    
    async def _test_validation(self, tool: Tool) -> TestResult:
        """Test tool validation."""
        start_time = time.time()
        
        try:
            is_valid, error = self.validator.validate_tool(tool)
            
            return TestResult(
                test_name="validation",
                tool_id=tool.metadata.id,
                passed=is_valid,
                execution_time=time.time() - start_time,
                error=error,
                details={'validated': is_valid}
            )
        except Exception as e:
            return TestResult(
                test_name="validation",
                tool_id=tool.metadata.id,
                passed=False,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _test_parameter_validation(self, tool: Tool, 
                                        test_parameters: Optional[Dict[str, Any]]) -> TestResult:
        """Test parameter validation."""
        start_time = time.time()
        
        try:
            if not test_parameters:
                test_parameters = self._generate_test_parameters(tool)
            
            is_valid = tool.validate_parameters(test_parameters)
            
            return TestResult(
                test_name="parameter_validation",
                tool_id=tool.metadata.id,
                passed=is_valid,
                execution_time=time.time() - start_time,
                details={'parameters_valid': is_valid}
            )
        except Exception as e:
            return TestResult(
                test_name="parameter_validation",
                tool_id=tool.metadata.id,
                passed=False,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _test_execution(self, tool: Tool, test_parameters: Dict[str, Any]) -> TestResult:
        """Test tool execution."""
        start_time = time.time()
        
        try:
            context = {
                'execution_id': 'test_execution',
                'permissions': ['read', 'write', 'execute', 'admin'],
                'allow_critical': True
            }
            
            result = await tool.execute(test_parameters, context)
            
            passed = isinstance(result, ToolExecutionResult) and result.success
            
            return TestResult(
                test_name="execution",
                tool_id=tool.metadata.id,
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'execution_success': result.success if hasattr(result, 'success') else False,
                    'has_result': result.result is not None if hasattr(result, 'result') else False
                }
            )
        except Exception as e:
            return TestResult(
                test_name="execution",
                tool_id=tool.metadata.id,
                passed=False,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _test_error_handling(self, tool: Tool) -> TestResult:
        """Test error handling with invalid parameters."""
        start_time = time.time()
        
        try:
            # Test with empty parameters
            context = {'execution_id': 'test_error_handling'}
            result = await tool.execute({}, context)
            
            # Tool should handle errors gracefully
            passed = isinstance(result, ToolExecutionResult)
            
            return TestResult(
                test_name="error_handling",
                tool_id=tool.metadata.id,
                passed=passed,
                execution_time=time.time() - start_time,
                details={'graceful_failure': not result.success if passed else False}
            )
        except Exception as e:
            # Exceptions should be caught by the tool
            return TestResult(
                test_name="error_handling",
                tool_id=tool.metadata.id,
                passed=False,
                execution_time=time.time() - start_time,
                error=f"Tool did not handle error gracefully: {str(e)}"
            )
    
    async def _test_performance(self, tool: Tool, test_parameters: Dict[str, Any]) -> TestResult:
        """Test tool performance."""
        start_time = time.time()
        
        try:
            context = {'execution_id': 'test_performance', 'permissions': ['read', 'write', 'execute']}
            
            # Run multiple iterations
            iterations = 3
            execution_times = []
            
            for _ in range(iterations):
                iter_start = time.time()
                await tool.execute(test_parameters, context)
                execution_times.append(time.time() - iter_start)
            
            avg_time = sum(execution_times) / len(execution_times)
            passed = avg_time < 10.0  # Should complete within 10 seconds
            
            return TestResult(
                test_name="performance",
                tool_id=tool.metadata.id,
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'average_execution_time': avg_time,
                    'iterations': iterations,
                    'all_times': execution_times
                }
            )
        except Exception as e:
            return TestResult(
                test_name="performance",
                tool_id=tool.metadata.id,
                passed=False,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _generate_test_parameters(self, tool: Tool) -> Dict[str, Any]:
        """Generate test parameters based on tool schema."""
        parameters = {}
        
        if not tool.metadata.config_schema:
            return {'target': 'test_target'}
        
        for param_name, param_config in tool.metadata.config_schema.items():
            if param_config.get('required'):
                if param_config.get('type') == 'string':
                    parameters[param_name] = 'test_value'
                elif param_config.get('type') == 'number':
                    parameters[param_name] = 1
                elif param_config.get('type') == 'boolean':
                    parameters[param_name] = True
        
        return parameters if parameters else {'target': 'test_target'}
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Returns:
            Test report dictionary
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        tests_by_tool = {}
        for result in self.test_results:
            if result.tool_id not in tests_by_tool:
                tests_by_tool[result.tool_id] = {'passed': 0, 'failed': 0, 'tests': []}
            
            if result.passed:
                tests_by_tool[result.tool_id]['passed'] += 1
            else:
                tests_by_tool[result.tool_id]['failed'] += 1
            
            tests_by_tool[result.tool_id]['tests'].append(result.to_dict())
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'by_tool': tests_by_tool,
            'all_results': [r.to_dict() for r in self.test_results]
        }


async def test_all_tools(tools: Dict[str, Tool]) -> Dict[str, Any]:
    """
    Test all tools in the registry.
    
    Args:
        tools: Dictionary of tool_id -> Tool
        
    Returns:
        Comprehensive test report
    """
    tester = ToolTester()
    
    for tool_id, tool in tools.items():
        await tester.test_tool(tool)
    
    return tester.generate_report()