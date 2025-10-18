"""
ATS MAFIA Framework - Tool Validator

Comprehensive validation framework for tools.
Validates inputs, outputs, safety checks, and permissions.
"""

import logging
from typing import Dict, Any, Optional, Tuple
import re

from ...core.tool_system import (
    Tool, ToolMetadata, ToolValidation, ToolSafety, 
    ToolCategory, ToolRiskLevel, PermissionLevel
)


class ToolValidator:
    """
    Comprehensive tool validation framework.
    
    Validates tool implementations for:
    - Input schema compliance
    - Output format verification
    - Safety requirements
    - Permission checks
    - Simulation mode enforcement
    """
    
    def __init__(self, audit_logger: Optional[Any] = None):
        """
        Initialize tool validator.
        
        Args:
            audit_logger: Optional audit logger for validation events
        """
        self.logger = logging.getLogger("tool_validator")
        self.audit_logger = audit_logger
        self.validation = ToolValidation()
        self.safety = ToolSafety(audit_logger)
    
    def validate_tool(self, tool: Tool) -> Tuple[bool, Optional[str]]:
        """
        Perform comprehensive tool validation.
        
        Args:
            tool: Tool instance to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate metadata
        is_valid, error = self._validate_metadata(tool.metadata)
        if not is_valid:
            return False, f"Metadata validation failed: {error}"
        
        # Validate simulation mode
        if not tool.metadata.simulation_only:
            return False, "Tool must operate in simulation mode only"
        
        # Validate required methods
        is_valid, error = self._validate_methods(tool)
        if not is_valid:
            return False, f"Method validation failed: {error}"
        
        self.logger.info(f"Tool {tool.metadata.id} passed validation")
        return True, None
    
    def _validate_metadata(self, metadata: ToolMetadata) -> Tuple[bool, Optional[str]]:
        """Validate tool metadata."""
        required_fields = ['id', 'name', 'description', 'version', 'author', 
                          'tool_type', 'category']
        
        for field in required_fields:
            if not getattr(metadata, field, None):
                return False, f"Missing required field: {field}"
        
        # Validate ID format (alphanumeric and underscores only)
        if not re.match(r'^[a-z0-9_]+$', metadata.id):
            return False, "Tool ID must be lowercase alphanumeric with underscores"
        
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+$', metadata.version):
            return False, "Version must be in format X.Y.Z"
        
        return True, None
    
    def _validate_methods(self, tool: Tool) -> Tuple[bool, Optional[str]]:
        """Validate required tool methods."""
        required_methods = ['execute', 'validate_parameters']
        
        for method_name in required_methods:
            if not hasattr(tool, method_name):
                return False, f"Missing required method: {method_name}"
            
            method = getattr(tool, method_name)
            if not callable(method):
                return False, f"Method {method_name} is not callable"
        
        return True, None
    
    def validate_parameters(self, tool: Tool, parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate tool parameters against schema.
        
        Args:
            tool: Tool instance
            parameters: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not tool.metadata.config_schema:
            return True, None
        
        return self.validation.validate_schema(parameters, tool.metadata.config_schema)
    
    def check_safety(self, tool: Tool, parameters: Dict[str, Any], 
                    context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Run safety checks before tool execution.
        
        Args:
            tool: Tool instance
            parameters: Execution parameters
            context: Execution context
            
        Returns:
            Tuple of (passed, error_message)
        """
        # Check simulation mode
        if not tool.metadata.simulation_only:
            return False, "Tool must operate in simulation mode"
        
        # Check risk level
        if tool.metadata.risk_level == ToolRiskLevel.CRITICAL:
            if not context.get('allow_critical', False):
                return False, "Critical risk tools require explicit authorization"
        
        # Run registered safety checks
        return self.safety.run_safety_checks(tool.metadata.id, parameters, context)
    
    def validate_output(self, tool: Tool, result: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate tool output format.
        
        Args:
            tool: Tool instance
            result: Tool execution result
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if result is None:
            return False, "Tool result cannot be None"
        
        # Check if result has required attributes for ToolExecutionResult
        required_attrs = ['tool_id', 'execution_id', 'success']
        for attr in required_attrs:
            if not hasattr(result, attr):
                return False, f"Result missing required attribute: {attr}"
        
        return True, None
    
    def get_validation_report(self, tool: Tool) -> Dict[str, Any]:
        """
        Generate comprehensive validation report for a tool.
        
        Args:
            tool: Tool instance to report on
            
        Returns:
            Validation report dictionary
        """
        report = {
            'tool_id': tool.metadata.id,
            'tool_name': tool.metadata.name,
            'version': tool.metadata.version,
            'category': tool.metadata.category.value if isinstance(tool.metadata.category, ToolCategory) else tool.metadata.category,
            'risk_level': tool.metadata.risk_level.value,
            'simulation_only': tool.metadata.simulation_only,
            'validations': {}
        }
        
        # Run all validations
        is_valid, error = self.validate_tool(tool)
        report['validations']['overall'] = {'passed': is_valid, 'error': error}
        
        is_valid, error = self._validate_metadata(tool.metadata)
        report['validations']['metadata'] = {'passed': is_valid, 'error': error}
        
        is_valid, error = self._validate_methods(tool)
        report['validations']['methods'] = {'passed': is_valid, 'error': error}
        
        report['overall_status'] = 'PASS' if all(
            v['passed'] for v in report['validations'].values()
        ) else 'FAIL'
        
        return report


def validate_all_tools(tools: Dict[str, Tool]) -> Dict[str, Dict[str, Any]]:
    """
    Validate all tools in the registry.
    
    Args:
        tools: Dictionary of tool_id -> Tool
        
    Returns:
        Dictionary of validation reports
    """
    validator = ToolValidator()
    reports = {}
    
    for tool_id, tool in tools.items():
        reports[tool_id] = validator.get_validation_report(tool)
    
    return reports