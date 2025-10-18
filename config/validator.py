"""
ATS MAFIA Framework Configuration Validator

This module provides validation functionality for configuration settings
to ensure they meet the framework's requirements and constraints.
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Union
import re
import ipaddress
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for configuration validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that caused the error
        """
        self.message = message
        self.field = field
        super().__init__(self.message)


class ConfigValidator:
    """
    Configuration validator for ATS MAFIA framework settings.
    
    Provides validation rules and checks for various configuration parameters
    to ensure they meet the framework's requirements.
    """
    
    def __init__(self):
        """Initialize the configuration validator."""
        self.validation_rules = self._get_validation_rules()
        self.errors: List[ValidationError] = []
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the entire configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        self.errors.clear()
        
        try:
            self._validate_framework(config.get('framework', {}))
            self._validate_core(config.get('core', {}))
            self._validate_logging(config.get('logging', {}))
            self._validate_profiles(config.get('profiles', {}))
            self._validate_tools(config.get('tools', {}))
            self._validate_communication(config.get('communication', {}))
            self._validate_orchestrator(config.get('orchestrator', {}))
            self._validate_voice(config.get('voice', {}))
            self._validate_ui(config.get('ui', {}))
            self._validate_api(config.get('api', {}))
            self._validate_security(config.get('security', {}))
            self._validate_performance(config.get('performance', {}))
            self._validate_development(config.get('development', {}))
            
            if self.errors:
                for error in self.errors:
                    logger.error(f"Validation error in '{error.field}': {error.message}")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            self.errors.append(ValidationError(str(e)))
            return False
    
    def get_errors(self) -> List[ValidationError]:
        """
        Get validation errors.
        
        Returns:
            List of validation errors
        """
        return self.errors.copy()
    
    def _validate_framework(self, framework: Dict[str, Any]) -> None:
        """Validate framework section."""
        required_fields = ['name', 'version', 'description']
        
        for field in required_fields:
            if field not in framework:
                self.errors.append(ValidationError(f"Missing required field: {field}", f"framework.{field}"))
            elif not isinstance(framework[field], str) or not framework[field].strip():
                self.errors.append(ValidationError(f"Field must be a non-empty string: {field}", f"framework.{field}"))
        
        # Validate version format (semantic versioning)
        if 'version' in framework:
            version_pattern = r'^\d+\.\d+\.\d+$'
            if not re.match(version_pattern, framework['version']):
                self.errors.append(ValidationError("Version must follow semantic versioning (x.y.z)", "framework.version"))
    
    def _validate_core(self, core: Dict[str, Any]) -> None:
        """Validate core section."""
        # Validate max_concurrent_agents
        if 'max_concurrent_agents' in core:
            if not isinstance(core['max_concurrent_agents'], int) or core['max_concurrent_agents'] <= 0:
                self.errors.append(ValidationError("max_concurrent_agents must be a positive integer", "core.max_concurrent_agents"))
        
        # Validate session_timeout
        if 'session_timeout' in core:
            if not isinstance(core['session_timeout'], int) or core['session_timeout'] <= 0:
                self.errors.append(ValidationError("session_timeout must be a positive integer", "core.session_timeout"))
        
        # Validate checkpoint_interval
        if 'checkpoint_interval' in core:
            if not isinstance(core['checkpoint_interval'], int) or core['checkpoint_interval'] <= 0:
                self.errors.append(ValidationError("checkpoint_interval must be a positive integer", "core.checkpoint_interval"))
        
        # Validate recovery_enabled
        if 'recovery_enabled' in core:
            if not isinstance(core['recovery_enabled'], bool):
                self.errors.append(ValidationError("recovery_enabled must be a boolean", "core.recovery_enabled"))
    
    def _validate_logging(self, logging: Dict[str, Any]) -> None:
        """Validate logging section."""
        # Validate log_level
        if 'level' in logging:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if logging['level'] not in valid_levels:
                self.errors.append(ValidationError(f"log_level must be one of: {valid_levels}", "logging.level"))
        
        # Validate log_format
        if 'format' in logging:
            if not isinstance(logging['format'], str) or not logging['format'].strip():
                self.errors.append(ValidationError("log_format must be a non-empty string", "logging.format"))
        
        # Validate file_path
        if 'file_path' in logging:
            self._validate_file_path(logging['file_path'], "logging.file_path")
        
        # Validate backup_count
        if 'backup_count' in logging:
            if not isinstance(logging['backup_count'], int) or logging['backup_count'] < 0:
                self.errors.append(ValidationError("backup_count must be a non-negative integer", "logging.backup_count"))
        
        # Validate audit_enabled
        if 'audit_enabled' in logging:
            if not isinstance(logging['audit_enabled'], bool):
                self.errors.append(ValidationError("audit_enabled must be a boolean", "logging.audit_enabled"))
    
    def _validate_profiles(self, profiles: Dict[str, Any]) -> None:
        """Validate profiles section."""
        # Validate default_profile_path
        if 'default_profile_path' in profiles:
            self._validate_directory_path(profiles['default_profile_path'], "profiles.default_profile_path")
        
        # Validate cache_enabled
        if 'cache_enabled' in profiles:
            if not isinstance(profiles['cache_enabled'], bool):
                self.errors.append(ValidationError("cache_enabled must be a boolean", "profiles.cache_enabled"))
        
        # Validate cache_size
        if 'cache_size' in profiles:
            if not isinstance(profiles['cache_size'], int) or profiles['cache_size'] <= 0:
                self.errors.append(ValidationError("cache_size must be a positive integer", "profiles.cache_size"))
    
    def _validate_tools(self, tools: Dict[str, Any]) -> None:
        """Validate tools section."""
        # Validate enabled_tools
        if 'enabled_tools' in tools:
            if not isinstance(tools['enabled_tools'], list):
                self.errors.append(ValidationError("enabled_tools must be a list", "tools.enabled_tools"))
        
        # Validate tool_paths
        if 'tool_paths' in tools:
            if not isinstance(tools['tool_paths'], list):
                self.errors.append(ValidationError("tool_paths must be a list", "tools.tool_paths"))
            else:
                for i, path in enumerate(tools['tool_paths']):
                    self._validate_directory_path(path, f"tools.tool_paths[{i}]")
        
        # Validate timeout
        if 'timeout' in tools:
            if not isinstance(tools['timeout'], int) or tools['timeout'] <= 0:
                self.errors.append(ValidationError("timeout must be a positive integer", "tools.timeout"))
        
        # Validate sandbox_enabled
        if 'sandbox_enabled' in tools:
            if not isinstance(tools['sandbox_enabled'], bool):
                self.errors.append(ValidationError("sandbox_enabled must be a boolean", "tools.sandbox_enabled"))
    
    def _validate_communication(self, communication: Dict[str, Any]) -> None:
        """Validate communication section."""
        # Validate protocol
        if 'protocol' in communication:
            valid_protocols = ['websocket', 'http', 'tcp', 'udp']
            if communication['protocol'] not in valid_protocols:
                self.errors.append(ValidationError(f"protocol must be one of: {valid_protocols}", "communication.protocol"))
        
        # Validate host
        if 'host' in communication:
            self._validate_host(communication['host'], "communication.host")
        
        # Validate port
        if 'port' in communication:
            self._validate_port(communication['port'], "communication.port")
        
        # Validate ssl_enabled
        if 'ssl_enabled' in communication:
            if not isinstance(communication['ssl_enabled'], bool):
                self.errors.append(ValidationError("ssl_enabled must be a boolean", "communication.ssl_enabled"))
        
        # Validate max_connections
        if 'max_connections' in communication:
            if not isinstance(communication['max_connections'], int) or communication['max_connections'] <= 0:
                self.errors.append(ValidationError("max_connections must be a positive integer", "communication.max_connections"))
    
    def _validate_orchestrator(self, orchestrator: Dict[str, Any]) -> None:
        """Validate orchestrator section."""
        # Validate max_concurrent_sessions
        if 'max_concurrent_sessions' in orchestrator:
            if not isinstance(orchestrator['max_concurrent_sessions'], int) or orchestrator['max_concurrent_sessions'] <= 0:
                self.errors.append(ValidationError("max_concurrent_sessions must be a positive integer", "orchestrator.max_concurrent_sessions"))
        
        # Validate session_timeout
        if 'session_timeout' in orchestrator:
            if not isinstance(orchestrator['session_timeout'], int) or orchestrator['session_timeout'] <= 0:
                self.errors.append(ValidationError("session_timeout must be a positive integer", "orchestrator.session_timeout"))
        
        # Validate auto_save_interval
        if 'auto_save_interval' in orchestrator:
            if not isinstance(orchestrator['auto_save_interval'], int) or orchestrator['auto_save_interval'] <= 0:
                self.errors.append(ValidationError("auto_save_interval must be a positive integer", "orchestrator.auto_save_interval"))
        
        # Validate scenario_timeout
        if 'scenario_timeout' in orchestrator:
            if not isinstance(orchestrator['scenario_timeout'], int) or orchestrator['scenario_timeout'] <= 0:
                self.errors.append(ValidationError("scenario_timeout must be a positive integer", "orchestrator.scenario_timeout"))
    
    def _validate_voice(self, voice: Dict[str, Any]) -> None:
        """Validate voice section."""
        # Validate enabled
        if 'enabled' in voice:
            if not isinstance(voice['enabled'], bool):
                self.errors.append(ValidationError("enabled must be a boolean", "voice.enabled"))
        
        # Validate engine
        if 'engine' in voice:
            valid_engines = ['pyttsx3', 'espeak', 'festival']
            if voice['engine'] not in valid_engines:
                self.errors.append(ValidationError(f"engine must be one of: {valid_engines}", "voice.engine"))
        
        # Validate language
        if 'language' in voice:
            language_pattern = r'^[a-z]{2}-[A-Z]{2}$'
            if not re.match(language_pattern, voice['language']):
                self.errors.append(ValidationError("language must follow format: xx-XX (e.g., en-US)", "voice.language"))
        
        # Validate rate
        if 'rate' in voice:
            if not isinstance(voice['rate'], int) or voice['rate'] <= 0:
                self.errors.append(ValidationError("rate must be a positive integer", "voice.rate"))
        
        # Validate volume
        if 'volume' in voice:
            if not isinstance(voice['volume'], (int, float)) or not (0.0 <= voice['volume'] <= 1.0):
                self.errors.append(ValidationError("volume must be a number between 0.0 and 1.0", "voice.volume"))
    
    def _validate_ui(self, ui: Dict[str, Any]) -> None:
        """Validate UI section."""
        # Validate enabled
        if 'enabled' in ui:
            if not isinstance(ui['enabled'], bool):
                self.errors.append(ValidationError("enabled must be a boolean", "ui.enabled"))
        
        # Validate theme
        if 'theme' in ui:
            valid_themes = ['light', 'dark', 'auto']
            if ui['theme'] not in valid_themes:
                self.errors.append(ValidationError(f"theme must be one of: {valid_themes}", "ui.theme"))
        
        # Validate port
        if 'port' in ui:
            self._validate_port(ui['port'], "ui.port")
        
        # Validate debug
        if 'debug' in ui:
            if not isinstance(ui['debug'], bool):
                self.errors.append(ValidationError("debug must be a boolean", "ui.debug"))
    
    def _validate_api(self, api: Dict[str, Any]) -> None:
        """Validate API section."""
        # Validate enabled
        if 'enabled' in api:
            if not isinstance(api['enabled'], bool):
                self.errors.append(ValidationError("enabled must be a boolean", "api.enabled"))
        
        # Validate host
        if 'host' in api:
            self._validate_host(api['host'], "api.host")
        
        # Validate port
        if 'port' in api:
            self._validate_port(api['port'], "api.port")
        
        # Validate rate_limit
        if 'rate_limit' in api:
            if not isinstance(api['rate_limit'], int) or api['rate_limit'] <= 0:
                self.errors.append(ValidationError("rate_limit must be a positive integer", "api.rate_limit"))
        
        # Validate authentication_required
        if 'authentication_required' in api:
            if not isinstance(api['authentication_required'], bool):
                self.errors.append(ValidationError("authentication_required must be a boolean", "api.authentication_required"))
    
    def _validate_security(self, security: Dict[str, Any]) -> None:
        """Validate security section."""
        boolean_fields = [
            'encryption_enabled', 'encryption_key_rotation', 'session_encryption',
            'audit_logging', 'access_control'
        ]
        
        for field in boolean_fields:
            if field in security:
                if not isinstance(security[field], bool):
                    self.errors.append(ValidationError(f"{field} must be a boolean", f"security.{field}"))
    
    def _validate_performance(self, performance: Dict[str, Any]) -> None:
        """Validate performance section."""
        # Validate boolean fields
        boolean_fields = ['monitoring_enabled', 'metrics_collection', 'profiling_enabled']
        for field in boolean_fields:
            if field in performance:
                if not isinstance(performance[field], bool):
                    self.errors.append(ValidationError(f"{field} must be a boolean", f"performance.{field}"))
        
        # Validate resource_limits
        if 'resource_limits' in performance:
            limits = performance['resource_limits']
            
            if 'max_cpu_percent' in limits:
                if not isinstance(limits['max_cpu_percent'], (int, float)) or not (0 <= limits['max_cpu_percent'] <= 100):
                    self.errors.append(ValidationError("max_cpu_percent must be between 0 and 100", "performance.resource_limits.max_cpu_percent"))
            
            if 'max_memory_percent' in limits:
                if not isinstance(limits['max_memory_percent'], (int, float)) or not (0 <= limits['max_memory_percent'] <= 100):
                    self.errors.append(ValidationError("max_memory_percent must be between 0 and 100", "performance.resource_limits.max_memory_percent"))
            
            if 'max_disk_usage' in limits:
                self._validate_size_string(limits['max_disk_usage'], "performance.resource_limits.max_disk_usage")
    
    def _validate_development(self, development: Dict[str, Any]) -> None:
        """Validate development section."""
        boolean_fields = [
            'debug_mode', 'verbose_logging', 'hot_reload', 'test_mode', 'mock_services'
        ]
        
        for field in boolean_fields:
            if field in development:
                if not isinstance(development[field], bool):
                    self.errors.append(ValidationError(f"{field} must be a boolean", f"development.{field}"))
    
    def _validate_port(self, port: Any, field: str) -> None:
        """Validate port number."""
        if not isinstance(port, int) or not (1 <= port <= 65535):
            self.errors.append(ValidationError("Port must be an integer between 1 and 65535", field))
    
    def _validate_host(self, host: Any, field: str) -> None:
        """Validate host address."""
        if not isinstance(host, str) or not host.strip():
            self.errors.append(ValidationError("Host must be a non-empty string", field))
            return
        
        try:
            # Try to validate as IP address
            ipaddress.ip_address(host)
        except ValueError:
            # If not a valid IP, check if it's a valid hostname
            hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(hostname_pattern, host):
                self.errors.append(ValidationError("Host must be a valid IP address or hostname", field))
    
    def _validate_file_path(self, path: Any, field: str) -> None:
        """Validate file path."""
        if not isinstance(path, str) or not path.strip():
            self.errors.append(ValidationError("File path must be a non-empty string", field))
            return
        
        try:
            Path(path)
        except Exception:
            self.errors.append(ValidationError("Invalid file path format", field))
    
    def _validate_directory_path(self, path: Any, field: str) -> None:
        """Validate directory path."""
        if not isinstance(path, str) or not path.strip():
            self.errors.append(ValidationError("Directory path must be a non-empty string", field))
            return
        
        try:
            Path(path)
        except Exception:
            self.errors.append(ValidationError("Invalid directory path format", field))
    
    def _validate_size_string(self, size: Any, field: str) -> None:
        """Validate size string (e.g., '10MB', '1GB')."""
        if not isinstance(size, str) or not size.strip():
            self.errors.append(ValidationError("Size must be a non-empty string", field))
            return
        
        size_pattern = r'^\d+[KMGT]?B$'
        if not re.match(size_pattern, size.upper()):
            self.errors.append(ValidationError("Size must be in format like '10MB', '1GB', etc.", field))
    
    def _get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get validation rules for configuration fields."""
        return {
            'framework': {
                'required': ['name', 'version', 'description'],
                'types': {
                    'name': str,
                    'version': str,
                    'description': str
                }
            },
            'core': {
                'required': ['max_concurrent_agents', 'session_timeout'],
                'types': {
                    'max_concurrent_agents': int,
                    'session_timeout': int,
                    'checkpoint_interval': int,
                    'recovery_enabled': bool
                },
                'ranges': {
                    'max_concurrent_agents': (1, 1000),
                    'session_timeout': (60, 86400),
                    'checkpoint_interval': (30, 3600)
                }
            },
            # Add more validation rules as needed
        }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Convenience function to validate configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if validation passes, False otherwise
    """
    validator = ConfigValidator()
    return validator.validate(config)


def get_validation_errors(config: Dict[str, Any]) -> List[ValidationError]:
    """
    Convenience function to get validation errors.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        List of validation errors
    """
    validator = ConfigValidator()
    validator.validate(config)
    return validator.get_errors()