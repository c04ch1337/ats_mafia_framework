"""
ATS MAFIA Framework Tool Extension System

This module provides the tool extension infrastructure for the ATS MAFIA framework.
It supports dynamic tool loading, sandboxed execution, permission management,
and comprehensive tool lifecycle management.
"""

import os
import sys
import importlib
import importlib.util
import inspect
import traceback
import threading
import time
import uuid
import json
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Callable, Union, Type
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging

from ..config.settings import FrameworkConfig
from .logging import AuditLogger, AuditEventType, SecurityLevel


class ToolType(Enum):
    """Types of tools supported by the framework."""
    PYTHON = "python"
    SCRIPT = "script"
    EXECUTABLE = "executable"
    API = "api"
    BUILTIN = "builtin"


class ToolStatus(Enum):
    """Status of tools in the system."""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNLOADED = "unloaded"


class PermissionLevel(Enum):
    """Permission levels for tool execution."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ToolCategory(Enum):
    """Categories of tools in the framework."""
    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    DEFENSE = "defense"
    FORENSICS = "forensics"
    SOCIAL_ENGINEERING = "social_engineering"
    UTILITIES = "utilities"
    POST_EXPLOITATION = "post_exploitation"
    EVASION = "evasion"
    MONITORING = "monitoring"
    INVESTIGATION = "investigation"
    RESPONSE = "response"


class ToolRiskLevel(Enum):
    """Risk levels for tool operations."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class ToolValidation:
    """
    Tool validation framework for input/output validation.
    
    Provides schema-based validation and type checking for tool parameters.
    """
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate
            schema: Schema definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            for key, constraints in schema.items():
                # Check required fields
                if constraints.get('required', False) and key not in data:
                    return False, f"Missing required parameter: {key}"
                
                if key not in data:
                    continue
                
                value = data[key]
                
                # Type validation
                expected_type = constraints.get('type')
                if expected_type:
                    if expected_type == 'string' and not isinstance(value, str):
                        return False, f"Parameter {key} must be a string"
                    elif expected_type == 'number' and not isinstance(value, (int, float)):
                        return False, f"Parameter {key} must be a number"
                    elif expected_type == 'boolean' and not isinstance(value, bool):
                        return False, f"Parameter {key} must be a boolean"
                    elif expected_type == 'array' and not isinstance(value, list):
                        return False, f"Parameter {key} must be an array"
                    elif expected_type == 'object' and not isinstance(value, dict):
                        return False, f"Parameter {key} must be an object"
                
                # Enum validation
                if 'enum' in constraints:
                    if value not in constraints['enum']:
                        return False, f"Parameter {key} must be one of {constraints['enum']}"
                
                # Range validation
                if 'min' in constraints and isinstance(value, (int, float)):
                    if value < constraints['min']:
                        return False, f"Parameter {key} must be >= {constraints['min']}"
                
                if 'max' in constraints and isinstance(value, (int, float)):
                    if value > constraints['max']:
                        return False, f"Parameter {key} must be <= {constraints['max']}"
                
                # Pattern validation
                if 'pattern' in constraints and isinstance(value, str):
                    import re
                    if not re.match(constraints['pattern'], value):
                        return False, f"Parameter {key} does not match required pattern"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_output(result: Any, expected_type: Optional[str] = None) -> bool:
        """
        Validate tool output format.
        
        Args:
            result: Tool result to validate
            expected_type: Expected output type
            
        Returns:
            True if output is valid
        """
        if expected_type:
            if expected_type == 'dict' and not isinstance(result, dict):
                return False
            elif expected_type == 'list' and not isinstance(result, list):
                return False
            elif expected_type == 'string' and not isinstance(result, str):
                return False
        
        return True


class ToolSafety:
    """
    Safety controls and audit logging for tools.
    
    Ensures tools operate safely and all actions are logged.
    """
    
    def __init__(self, audit_logger: Optional['AuditLogger'] = None):
        """
        Initialize safety controls.
        
        Args:
            audit_logger: Audit logger instance
        """
        self.audit_logger = audit_logger
        self.safety_checks: Dict[str, Callable] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_safety_check(self, check_name: str, check_func: Callable) -> None:
        """
        Register a safety check function.
        
        Args:
            check_name: Name of the safety check
            check_func: Function to execute for check
        """
        self.safety_checks[check_name] = check_func
    
    def run_safety_checks(self, tool_id: str, parameters: Dict[str, Any],
                         context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Run all safety checks for a tool execution.
        
        Args:
            tool_id: Tool identifier
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tuple of (passed, error_message)
        """
        for check_name, check_func in self.safety_checks.items():
            try:
                passed, message = check_func(tool_id, parameters, context)
                if not passed:
                    return False, f"Safety check '{check_name}' failed: {message}"
            except Exception as e:
                return False, f"Safety check '{check_name}' error: {str(e)}"
        
        return True, None
    
    def set_rate_limit(self, tool_id: str, max_calls: int, window_seconds: int) -> None:
        """
        Set rate limit for a tool.
        
        Args:
            tool_id: Tool identifier
            max_calls: Maximum calls allowed
            window_seconds: Time window in seconds
        """
        self.rate_limits[tool_id] = {
            'max_calls': max_calls,
            'window_seconds': window_seconds,
            'calls': []
        }
    
    def check_rate_limit(self, tool_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if tool execution is within rate limits.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tuple of (allowed, error_message)
        """
        if tool_id not in self.rate_limits:
            return True, None
        
        limit_info = self.rate_limits[tool_id]
        current_time = time.time()
        window_start = current_time - limit_info['window_seconds']
        
        # Remove old calls outside the window
        limit_info['calls'] = [t for t in limit_info['calls'] if t > window_start]
        
        # Check if limit exceeded
        if len(limit_info['calls']) >= limit_info['max_calls']:
            return False, f"Rate limit exceeded: {limit_info['max_calls']} calls per {limit_info['window_seconds']}s"
        
        # Record this call
        limit_info['calls'].append(current_time)
        return True, None
    
    def log_execution(self, tool_id: str, parameters: Dict[str, Any],
                     result: 'ToolExecutionResult') -> None:
        """
        Log tool execution for audit trail.
        
        Args:
            tool_id: Tool identifier
            parameters: Execution parameters
            result: Execution result
        """
        execution_record = {
            'timestamp': time.time(),
            'tool_id': tool_id,
            'execution_id': result.execution_id,
            'success': result.success,
            'execution_time': result.execution_time,
            'parameters': parameters,
            'error': result.error
        }
        
        self.execution_history.append(execution_record)
        
        if self.audit_logger:
            self.audit_logger.tool_execution(
                tool_name=tool_id,
                action="tool_executed",
                details=execution_record,
                success=result.success,
                error_message=result.error
            )


class ToolChaining:
    """
    Framework for chaining tool executions in sequence.
    
    Allows tools to call other tools and pass results between them.
    """
    
    def __init__(self, tool_registry: 'ToolRegistry'):
        """
        Initialize tool chaining.
        
        Args:
            tool_registry: Tool registry instance
        """
        self.tool_registry = tool_registry
        self.chain_history: List[Dict[str, Any]] = []
    
    async def execute_chain(self, chain_definition: List[Dict[str, Any]],
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a chain of tool calls.
        
        Args:
            chain_definition: List of tool calls with parameters
            context: Execution context
            
        Returns:
            Dictionary containing results from all tools in chain
        """
        chain_id = str(uuid.uuid4())
        results = {}
        chain_context = context.copy()
        
        for step_index, step in enumerate(chain_definition):
            tool_id = step['tool_id']
            parameters = step.get('parameters', {})
            
            # Support parameter substitution from previous results
            parameters = self._substitute_parameters(parameters, results)
            
            # Execute tool
            result = await self.tool_registry.execute_tool(
                tool_id=tool_id,
                parameters=parameters,
                context=chain_context,
                timeout=step.get('timeout')
            )
            
            # Store result
            step_name = step.get('name', f"step_{step_index}")
            results[step_name] = result
            
            # Check if step failed and break if configured
            if not result.success and step.get('stop_on_failure', True):
                break
            
            # Update chain context with result
            chain_context[f'{step_name}_result'] = result.result
        
        # Record chain execution
        self.chain_history.append({
            'chain_id': chain_id,
            'timestamp': time.time(),
            'steps': len(chain_definition),
            'successful_steps': sum(1 for r in results.values() if r.success),
            'results': results
        })
        
        return results
    
    def _substitute_parameters(self, parameters: Dict[str, Any],
                              results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute parameters with values from previous results.
        
        Args:
            parameters: Parameters with potential placeholders
            results: Previous step results
            
        Returns:
            Parameters with substituted values
        """
        substituted = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract result reference: ${step_name.field}
                reference = value[2:-1]
                parts = reference.split('.')
                
                if len(parts) >= 2:
                    step_name = parts[0]
                    field_path = parts[1:]
                    
                    if step_name in results and results[step_name].success:
                        result_data = results[step_name].result
                        
                        # Navigate nested fields
                        for field in field_path:
                            if isinstance(result_data, dict) and field in result_data:
                                result_data = result_data[field]
                            else:
                                result_data = None
                                break
                        
                        substituted[key] = result_data if result_data is not None else value
                    else:
                        substituted[key] = value
                else:
                    substituted[key] = value
            else:
                substituted[key] = value
        
        return substituted


class ToolTemplates:
    """
    Templates for common tool patterns.
    
    Provides reusable patterns for building tools efficiently.
    """
    
    @staticmethod
    def create_scanner_template(name: str, description: str,
                               scan_function: Callable) -> Dict[str, Any]:
        """
        Create a scanner tool template.
        
        Args:
            name: Tool name
            description: Tool description
            scan_function: Function to perform scanning
            
        Returns:
            Tool template dictionary
        """
        return {
            'name': name,
            'description': description,
            'category': ToolCategory.RECONNAISSANCE,
            'risk_level': ToolRiskLevel.LOW_RISK,
            'parameters_schema': {
                'target': {'type': 'string', 'required': True},
                'scan_depth': {'type': 'string', 'enum': ['quick', 'normal', 'deep'], 'default': 'normal'},
                'timeout': {'type': 'number', 'default': 30}
            },
            'execute': scan_function
        }
    
    @staticmethod
    def create_analyzer_template(name: str, description: str,
                                analysis_function: Callable) -> Dict[str, Any]:
        """
        Create an analyzer tool template.
        
        Args:
            name: Tool name
            description: Tool description
            analysis_function: Function to perform analysis
            
        Returns:
            Tool template dictionary
        """
        return {
            'name': name,
            'description': description,
            'category': ToolCategory.FORENSICS,
            'risk_level': ToolRiskLevel.SAFE,
            'parameters_schema': {
                'input_data': {'type': 'string', 'required': True},
                'analysis_type': {'type': 'string', 'required': True},
                'output_format': {'type': 'string', 'enum': ['json', 'text', 'html'], 'default': 'json'}
            },
            'execute': analysis_function
        }
    
    @staticmethod
    def create_monitor_template(name: str, description: str,
                               monitor_function: Callable) -> Dict[str, Any]:
        """
        Create a monitoring tool template.
        
        Args:
            name: Tool name
            description: Tool description
            monitor_function: Function to perform monitoring
            
        Returns:
            Tool template dictionary
        """
        return {
            'name': name,
            'description': description,
            'category': ToolCategory.MONITORING,
            'risk_level': ToolRiskLevel.SAFE,
            'parameters_schema': {
                'monitor_target': {'type': 'string', 'required': True},
                'duration': {'type': 'number', 'default': 60},
                'alert_threshold': {'type': 'number', 'default': 0.8},
                'sampling_rate': {'type': 'number', 'default': 1.0}
            },
            'execute': monitor_function
        }


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    id: str
    name: str
    description: str
    version: str
    author: str
    tool_type: ToolType
    category: Union[str, ToolCategory]
    tags: List[str]
    permissions_required: List[PermissionLevel]
    dependencies: List[str]
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW_RISK
    file_path: Optional[str] = None
    entry_point: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    simulation_only: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['tool_type'] = self.tool_type.value
        data['risk_level'] = self.risk_level.value
        if isinstance(self.category, ToolCategory):
            data['category'] = self.category.value
        data['permissions_required'] = [p.value for p in self.permissions_required]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolMetadata':
        """Create metadata from dictionary."""
        data['tool_type'] = ToolType(data['tool_type'])
        if 'risk_level' in data:
            data['risk_level'] = ToolRiskLevel(data['risk_level'])
        if isinstance(data.get('category'), str) and data['category'] in [c.value for c in ToolCategory]:
            data['category'] = ToolCategory(data['category'])
        data['permissions_required'] = [
            PermissionLevel(p) for p in data['permissions_required']
        ]
        return cls(**data)


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    tool_id: str
    execution_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: int = 0
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize result after dataclass creation."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)


class Tool(ABC):
    """
    Abstract base class for all tools in the ATS MAFIA framework.
    
    All tools must inherit from this class and implement the required methods.
    """
    
    def __init__(self, metadata: ToolMetadata):
        """
        Initialize the tool.
        
        Args:
            metadata: Tool metadata
        """
        self.metadata = metadata
        self.status = ToolStatus.LOADED
        self.config = {}
        self.logger = logging.getLogger(f"tool.{metadata.id}")
    
    @abstractmethod
    async def execute(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Execution parameters
            context: Execution context (agent info, session info, etc.)
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate execution parameters.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the tool.
        
        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        self.status = ToolStatus.ACTIVE
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get tool information.
        
        Returns:
            Dictionary containing tool information
        """
        return {
            'metadata': self.metadata.to_dict(),
            'status': self.status.value,
            'config': self.config
        }


class PythonTool(Tool):
    """
    Python-based tool implementation.
    
    Executes Python code in a controlled environment.
    """
    
    def __init__(self, metadata: ToolMetadata, module: Any):
        """
        Initialize Python tool.
        
        Args:
            metadata: Tool metadata
            module: Python module containing the tool implementation
        """
        super().__init__(metadata)
        self.module = module
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def execute(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the Python tool.
        
        Args:
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Invalid parameters"
                )
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._execute_sync,
                parameters,
                context
            )
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _execute_sync(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the tool synchronously.
        
        Args:
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Check if module has execute function
            if hasattr(self.module, 'execute'):
                result = self.module.execute(parameters, context)
            elif hasattr(self.module, 'main'):
                result = self.module.main(parameters)
            else:
                raise AttributeError("Tool module must have 'execute' or 'main' function")
            
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                traceback=traceback.format_exc()
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters using module's validate function if available.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        if hasattr(self.module, 'validate_parameters'):
            return self.module.validate_parameters(parameters)
        return True


class ScriptTool(Tool):
    """
    Script-based tool implementation.
    
    Executes external scripts in a sandboxed environment.
    """
    
    def __init__(self, metadata: ToolMetadata, script_path: str):
        """
        Initialize script tool.
        
        Args:
            metadata: Tool metadata
            script_path: Path to the script file
        """
        super().__init__(metadata)
        self.script_path = script_path
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def execute(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the script tool.
        
        Args:
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolExecutionResult(
                    tool_id=self.metadata.id,
                    execution_id=execution_id,
                    success=False,
                    result=None,
                    error="Invalid parameters"
                )
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._execute_sync,
                parameters,
                context
            )
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _execute_sync(self, 
                     parameters: Dict[str, Any],
                     context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the script synchronously.
        
        Args:
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Prepare parameters file
                params_file = os.path.join(temp_dir, 'parameters.json')
                with open(params_file, 'w') as f:
                    json.dump(parameters, f)
                
                # Prepare context file
                context_file = os.path.join(temp_dir, 'context.json')
                with open(context_file, 'w') as f:
                    json.dump(context, f)
                
                # Execute script
                cmd = [self.script_path, params_file, context_file]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_dir,
                    timeout=self.config.get('timeout', 30)
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    # Try to parse result from stdout
                    try:
                        result = json.loads(stdout)
                    except json.JSONDecodeError:
                        result = stdout
                    
                    return ToolExecutionResult(
                        tool_id=self.metadata.id,
                        execution_id=execution_id,
                        success=True,
                        result=result,
                        stdout=stdout,
                        stderr=stderr
                    )
                else:
                    return ToolExecutionResult(
                        tool_id=self.metadata.id,
                        execution_id=execution_id,
                        success=False,
                        result=None,
                        error=f"Script failed with return code {process.returncode}",
                        stdout=stdout,
                        stderr=stderr
                    )
                
        except subprocess.TimeoutExpired:
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error="Script execution timed out"
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_id=self.metadata.id,
                execution_id=execution_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate script parameters.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Basic validation - can be extended
        return isinstance(parameters, dict)


class ToolRegistry:
    """
    Registry for managing tools in the ATS MAFIA framework.
    
    Handles tool loading, unloading, and lifecycle management.
    """
    
    def __init__(self, config: FrameworkConfig, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the tool registry.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.tools: Dict[str, Tool] = {}
        self.tool_metadata: Dict[str, ToolMetadata] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger("tool_registry")
        
        # Load tools from configured paths
        self._load_tools_from_paths()
    
    def _load_tools_from_paths(self) -> None:
        """Load tools from configured tool paths."""
        for tool_path in self.config.tool_paths:
            self._load_tools_from_directory(tool_path)
    
    def _load_tools_from_directory(self, directory: str) -> None:
        """
        Load tools from a directory.
        
        Args:
            directory: Directory to load tools from
        """
        tool_dir = Path(directory)
        
        if not tool_dir.exists():
            self.logger.warning(f"Tool directory does not exist: {directory}")
            return
        
        # Look for tool metadata files
        for metadata_file in tool_dir.glob("**/tool.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata_data = json.load(f)
                
                metadata = ToolMetadata.from_dict(metadata_data)
                self.register_tool_metadata(metadata)
                
            except Exception as e:
                self.logger.error(f"Error loading tool metadata from {metadata_file}: {e}")
        
        # Look for Python modules
        for py_file in tool_dir.glob("**/*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                self._load_python_tool(py_file)
            except Exception as e:
                self.logger.error(f"Error loading Python tool from {py_file}: {e}")
    
    def _load_python_tool(self, file_path: Path) -> None:
        """
        Load a Python tool from a file.
        
        Args:
            file_path: Path to the Python file
        """
        # Create module spec
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        # Load module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if module has tool metadata
        if hasattr(module, 'TOOL_METADATA'):
            metadata = ToolMetadata.from_dict(module.TOOL_METADATA)
        else:
            # Create basic metadata
            metadata = ToolMetadata(
                id=module_name,
                name=module_name,
                description=f"Python tool from {file_path.name}",
                version="1.0.0",
                author="Unknown",
                tool_type=ToolType.PYTHON,
                category="general",
                tags=[],
                permissions_required=[PermissionLevel.EXECUTE],
                dependencies=[],
                file_path=str(file_path)
            )
        
        # Create tool instance
        tool = PythonTool(metadata, module)
        self.register_tool(tool)
        
        if self.audit_logger:
            self.audit_logger.tool_execution(
                tool_name=metadata.name,
                action="tool_loaded",
                details={'file_path': str(file_path)},
                success=True
            )
    
    def register_tool_metadata(self, metadata: ToolMetadata) -> None:
        """
        Register tool metadata.
        
        Args:
            metadata: Tool metadata to register
        """
        self.tool_metadata[metadata.id] = metadata
        
        if self.audit_logger:
            self.audit_logger.tool_execution(
                tool_name=metadata.name,
                action="metadata_registered",
                details={'tool_id': metadata.id},
                success=True
            )
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.metadata.id] = tool
        self.tool_metadata[tool.metadata.id] = tool.metadata
        
        if self.audit_logger:
            self.audit_logger.tool_execution(
                tool_name=tool.metadata.name,
                action="tool_registered",
                details={'tool_id': tool.metadata.id},
                success=True
            )
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_id: ID of the tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_id in self.tools:
            tool = self.tools[tool_id]
            
            # Clean up tool resources
            if hasattr(tool, 'executor'):
                tool.executor.shutdown(wait=True)
            
            del self.tools[tool_id]
            del self.tool_metadata[tool_id]
            
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_unregistered",
                    details={'tool_id': tool_id},
                    success=True
                )
            
            return True
        
        return False
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_id)
    
    def get_tool_metadata(self, tool_id: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata by ID.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            Tool metadata or None if not found
        """
        return self.tool_metadata.get(tool_id)
    
    def list_tools(self, 
                   category: Optional[str] = None,
                   tool_type: Optional[ToolType] = None,
                   status: Optional[ToolStatus] = None) -> List[Dict[str, Any]]:
        """
        List tools with optional filtering.
        
        Args:
            category: Filter by category
            tool_type: Filter by tool type
            status: Filter by status
            
        Returns:
            List of tool information dictionaries
        """
        tools = []
        
        for tool in self.tools.values():
            # Apply filters
            if category and tool.metadata.category != category:
                continue
            
            if tool_type and tool.metadata.tool_type != tool_type:
                continue
            
            if status and tool.status != status:
                continue
            
            tools.append(tool.get_info())
        
        return tools
    
    async def execute_tool(self, 
                          tool_id: str,
                          parameters: Dict[str, Any],
                          context: Dict[str, Any],
                          timeout: Optional[float] = None) -> ToolExecutionResult:
        """
        Execute a tool.
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Execution parameters
            context: Execution context
            timeout: Execution timeout in seconds
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_id)
        
        if not tool:
            return ToolExecutionResult(
                tool_id=tool_id,
                execution_id=str(uuid.uuid4()),
                success=False,
                result=None,
                error=f"Tool {tool_id} not found"
            )
        
        if tool.status != ToolStatus.ACTIVE:
            return ToolExecutionResult(
                tool_id=tool_id,
                execution_id=str(uuid.uuid4()),
                success=False,
                result=None,
                error=f"Tool {tool_id} is not active (status: {tool.status.value})"
            )
        
        # Check permissions
        if not self._check_permissions(tool, context):
            return ToolExecutionResult(
                tool_id=tool_id,
                execution_id=str(uuid.uuid4()),
                success=False,
                result=None,
                error="Insufficient permissions to execute tool"
            )
        
        start_time = time.time()
        
        try:
            # Execute with timeout
            if timeout:
                result = await asyncio.wait_for(
                    tool.execute(parameters, context),
                    timeout=timeout
                )
            else:
                result = await tool.execute(parameters, context)
            
            # Log execution
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_executed",
                    details={
                        'tool_id': tool_id,
                        'parameters': parameters,
                        'execution_time': result.execution_time
                    },
                    success=result.success,
                    error_message=result.error
                )
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_execution_timeout",
                    details={
                        'tool_id': tool_id,
                        'timeout': timeout,
                        'execution_time': execution_time
                    },
                    success=False
                )
            
            return ToolExecutionResult(
                tool_id=tool_id,
                execution_id=str(uuid.uuid4()),
                success=False,
                result=None,
                error=f"Tool execution timed out after {timeout} seconds",
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_execution_error",
                    details={
                        'tool_id': tool_id,
                        'error': str(e),
                        'execution_time': execution_time
                    },
                    success=False
                )
            
            return ToolExecutionResult(
                tool_id=tool_id,
                execution_id=str(uuid.uuid4()),
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _check_permissions(self, tool: Tool, context: Dict[str, Any]) -> bool:
        """
        Check if the context has sufficient permissions to execute the tool.
        
        Args:
            tool: Tool to check permissions for
            context: Execution context
            
        Returns:
            True if permissions are sufficient, False otherwise
        """
        # Get user/agent permissions from context
        user_permissions = context.get('permissions', [])
        
        # Check if tool requires any permissions
        if not tool.metadata.permissions_required:
            return True
        
        # Check if user has required permissions
        for required_perm in tool.metadata.permissions_required:
            if required_perm.value not in user_permissions:
                return False
        
        return True
    
    def configure_tool(self, tool_id: str, config: Dict[str, Any]) -> bool:
        """
        Configure a tool.
        
        Args:
            tool_id: ID of the tool to configure
            config: Configuration dictionary
            
        Returns:
            True if configuration successful, False otherwise
        """
        tool = self.get_tool(tool_id)
        
        if not tool:
            return False
        
        try:
            tool.configure(config)
            
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_configured",
                    details={'tool_id': tool_id, 'config': config},
                    success=True
                )
            
            return True
            
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.tool_execution(
                    tool_name=tool.metadata.name,
                    action="tool_configuration_failed",
                    details={'tool_id': tool_id, 'error': str(e)},
                    success=False
                )
            
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tool system statistics.
        
        Returns:
            Dictionary containing statistics
        """
        tools_by_type = {}
        tools_by_status = {}
        
        for tool in self.tools.values():
            # Count by type
            tool_type = tool.metadata.tool_type.value
            tools_by_type[tool_type] = tools_by_type.get(tool_type, 0) + 1
            
            # Count by status
            status = tool.status.value
            tools_by_status[status] = tools_by_status.get(status, 0) + 1
        
        return {
            'total_tools': len(self.tools),
            'tools_by_type': tools_by_type,
            'tools_by_status': tools_by_status,
            'configured_paths': self.config.tool_paths
        }
    
    def shutdown(self) -> None:
        """Shutdown the tool registry and clean up resources."""
        # Shutdown all tool executors
        for tool in self.tools.values():
            if hasattr(tool, 'executor'):
                tool.executor.shutdown(wait=True)
        
        # Shutdown registry executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Tool registry shutdown complete")


# Global tool registry instance
_global_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> Optional[ToolRegistry]:
    """
    Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry instance or None if not initialized
    """
    return _global_tool_registry


def initialize_tool_registry(config: FrameworkConfig, 
                           audit_logger: Optional[AuditLogger] = None) -> ToolRegistry:
    """
    Initialize the global tool registry.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized ToolRegistry instance
    """
    global _global_tool_registry
    _global_tool_registry = ToolRegistry(config, audit_logger)
    return _global_tool_registry


def shutdown_tool_registry() -> None:
    """Shutdown the global tool registry."""
    global _global_tool_registry
    if _global_tool_registry:
        _global_tool_registry.shutdown()
        _global_tool_registry = None