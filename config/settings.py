"""
ATS MAFIA Framework Settings Management

This module provides the main configuration management functionality for the ATS MAFIA framework.
It handles loading, validation, and access to configuration settings.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameworkConfig:
    """
    Main configuration class for the ATS MAFIA framework.
    
    This class handles all configuration settings, loading from files,
    environment variables, and providing access to configuration values.
    """
    
    # Framework metadata
    name: str = "ATS MAFIA Framework"
    version: str = "1.0.0"
    description: str = "Advanced Training System for Multi-Agent Interactive Framework"
    
    # Core settings
    max_concurrent_agents: int = 10
    session_timeout: int = 3600
    checkpoint_interval: int = 300
    recovery_enabled: bool = True
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file_path: str = "logs/ats_mafia.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    audit_enabled: bool = True
    audit_file_path: str = "logs/audit.log"
    
    # Profile management
    default_profile_path: str = "profiles/"
    cache_enabled: bool = True
    cache_size: int = 100
    validation_enabled: bool = True
    auto_reload: bool = False
    
    # Tool system
    enabled_tools: list = field(default_factory=list)
    tool_paths: list = field(default_factory=lambda: ["tools/"])
    tool_timeout: int = 30
    max_memory: str = "512MB"
    sandbox_enabled: bool = True
    
    # Communication settings
    communication_protocol: str = "websocket"
    communication_host: str = "localhost"
    communication_port: int = 8080
    ssl_enabled: bool = False
    max_connections: int = 100
    heartbeat_interval: int = 30
    message_queue_size: int = 1000
    
    # Training orchestrator
    max_concurrent_sessions: int = 5
    session_timeout: int = 7200
    auto_save_interval: int = 600
    scenario_timeout: int = 1800
    progress_tracking: bool = True
    
    # Voice processing
    voice_enabled: bool = False
    voice_engine: str = "pyttsx3"
    speech_recognition_engine: str = "speechrecognition"
    voice_language: str = "en-US"
    voice_rate: int = 200
    voice_volume: float = 0.9
    
    # UI settings
    ui_enabled: bool = True
    ui_theme: str = "dark"
    ui_port: int = 8501
    ui_debug: bool = False
    ui_auto_refresh: bool = True
    
    # API settings
    api_enabled: bool = True
    api_host: str = "localhost"
    api_port: int = 5000
    rate_limit: int = 100
    authentication_required: bool = False
    cors_enabled: bool = True
    
    # Security settings
    encryption_enabled: bool = True
    encryption_key_rotation: bool = True
    session_encryption: bool = True
    audit_logging: bool = True
    access_control: bool = False
    
    # Performance settings
    monitoring_enabled: bool = True
    metrics_collection: bool = True
    profiling_enabled: bool = False
    max_cpu_percent: int = 80
    max_memory_percent: int = 85
    max_disk_usage: str = "1GB"
    
    # Development settings
    debug_mode: bool = False
    verbose_logging: bool = False
    hot_reload: bool = False
    test_mode: bool = False
    mock_services: bool = False
    
    # Internal state
    _config_data: Dict[str, Any] = field(default_factory=dict)
    _config_file: Optional[str] = None
    
    def __post_init__(self):
        """Initialize the configuration after dataclass creation."""
        self._config_data = self._to_dict()
    
    @classmethod
    def from_file(cls, config_file: Union[str, Path]) -> 'FrameworkConfig':
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            FrameworkConfig instance with loaded settings
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            # Try to load default configuration
            default_path = Path(__file__).parent / "default.yaml"
            if default_path.exists():
                config_path = default_path
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
            
            # Create instance with loaded data
            config = cls()
            config._update_from_dict(config_data)
            config._config_file = str(config_path)
            
            logger.info(f"Configuration loaded from: {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise ValueError(f"Invalid configuration file: {e}")
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'FrameworkConfig':
        """
        Create configuration from a dictionary.
        
        Args:
            config_data: Dictionary containing configuration settings
            
        Returns:
            FrameworkConfig instance with provided settings
        """
        config = cls()
        config._update_from_dict(config_data)
        return config
    
    def _update_from_dict(self, config_data: Dict[str, Any]) -> None:
        """
        Update configuration settings from a dictionary.
        
        Args:
            config_data: Dictionary containing configuration settings
        """
        # Map configuration keys to instance attributes
        key_mapping = {
            'framework': {
                'name': 'name',
                'version': 'version',
                'description': 'description'
            },
            'core': {
                'max_concurrent_agents': 'max_concurrent_agents',
                'session_timeout': 'session_timeout',
                'checkpoint_interval': 'checkpoint_interval',
                'recovery_enabled': 'recovery_enabled'
            },
            'logging': {
                'level': 'log_level',
                'format': 'log_format',
                'file_path': 'log_file_path',
                'max_file_size': 'max_file_size',
                'backup_count': 'backup_count',
                'audit_enabled': 'audit_enabled',
                'audit_file_path': 'audit_file_path'
            },
            'profiles': {
                'default_profile_path': 'default_profile_path',
                'cache_enabled': 'cache_enabled',
                'cache_size': 'cache_size',
                'validation_enabled': 'validation_enabled',
                'auto_reload': 'auto_reload'
            },
            'tools': {
                'enabled_tools': 'enabled_tools',
                'tool_paths': 'tool_paths',
                'timeout': 'tool_timeout',
                'max_memory': 'max_memory',
                'sandbox_enabled': 'sandbox_enabled'
            },
            'communication': {
                'protocol': 'communication_protocol',
                'host': 'communication_host',
                'port': 'communication_port',
                'ssl_enabled': 'ssl_enabled',
                'max_connections': 'max_connections',
                'heartbeat_interval': 'heartbeat_interval',
                'message_queue_size': 'message_queue_size'
            },
            'orchestrator': {
                'max_concurrent_sessions': 'max_concurrent_sessions',
                'session_timeout': 'session_timeout',
                'auto_save_interval': 'auto_save_interval',
                'scenario_timeout': 'scenario_timeout',
                'progress_tracking': 'progress_tracking'
            },
            'voice': {
                'enabled': 'voice_enabled',
                'engine': 'voice_engine',
                'speech_recognition_engine': 'speech_recognition_engine',
                'language': 'voice_language',
                'rate': 'voice_rate',
                'volume': 'voice_volume'
            },
            'ui': {
                'enabled': 'ui_enabled',
                'theme': 'ui_theme',
                'port': 'ui_port',
                'debug': 'ui_debug',
                'auto_refresh': 'ui_auto_refresh'
            },
            'api': {
                'enabled': 'api_enabled',
                'host': 'api_host',
                'port': 'api_port',
                'rate_limit': 'rate_limit',
                'authentication_required': 'authentication_required',
                'cors_enabled': 'cors_enabled'
            },
            'security': {
                'encryption_enabled': 'encryption_enabled',
                'encryption_key_rotation': 'encryption_key_rotation',
                'session_encryption': 'session_encryption',
                'audit_logging': 'audit_logging',
                'access_control': 'access_control'
            },
            'performance': {
                'monitoring_enabled': 'monitoring_enabled',
                'metrics_collection': 'metrics_collection',
                'profiling_enabled': 'profiling_enabled',
                'resource_limits': {
                    'max_cpu_percent': 'max_cpu_percent',
                    'max_memory_percent': 'max_memory_percent',
                    'max_disk_usage': 'max_disk_usage'
                }
            },
            'development': {
                'debug_mode': 'debug_mode',
                'verbose_logging': 'verbose_logging',
                'hot_reload': 'hot_reload',
                'test_mode': 'test_mode',
                'mock_services': 'mock_services'
            }
        }
        
        # Update attributes based on configuration data
        for section, settings in key_mapping.items():
            if section in config_data:
                section_data = config_data[section]
                for config_key, attr_name in settings.items():
                    if isinstance(config_key, dict):
                        # Handle nested dictionaries (like performance.resource_limits)
                        for nested_key, nested_attr in config_key.items():
                            if nested_key in section_data:
                                setattr(self, nested_attr, section_data[nested_key])
                    else:
                        if config_key in section_data:
                            setattr(self, attr_name, section_data[config_key])
        
        # Update internal configuration data
        self._config_data.update(config_data)
    
    def _to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.
        
        Returns:
            Dictionary containing all configuration settings
        """
        return {
            'framework': {
                'name': self.name,
                'version': self.version,
                'description': self.description
            },
            'core': {
                'max_concurrent_agents': self.max_concurrent_agents,
                'session_timeout': self.session_timeout,
                'checkpoint_interval': self.checkpoint_interval,
                'recovery_enabled': self.recovery_enabled
            },
            'logging': {
                'level': self.log_level,
                'format': self.log_format,
                'file_path': self.log_file_path,
                'max_file_size': self.max_file_size,
                'backup_count': self.backup_count,
                'audit_enabled': self.audit_enabled,
                'audit_file_path': self.audit_file_path
            },
            'profiles': {
                'default_profile_path': self.default_profile_path,
                'cache_enabled': self.cache_enabled,
                'cache_size': self.cache_size,
                'validation_enabled': self.validation_enabled,
                'auto_reload': self.auto_reload
            },
            'tools': {
                'enabled_tools': self.enabled_tools,
                'tool_paths': self.tool_paths,
                'timeout': self.tool_timeout,
                'max_memory': self.max_memory,
                'sandbox_enabled': self.sandbox_enabled
            },
            'communication': {
                'protocol': self.communication_protocol,
                'host': self.communication_host,
                'port': self.communication_port,
                'ssl_enabled': self.ssl_enabled,
                'max_connections': self.max_connections,
                'heartbeat_interval': self.heartbeat_interval,
                'message_queue_size': self.message_queue_size
            },
            'orchestrator': {
                'max_concurrent_sessions': self.max_concurrent_sessions,
                'session_timeout': self.session_timeout,
                'auto_save_interval': self.auto_save_interval,
                'scenario_timeout': self.scenario_timeout,
                'progress_tracking': self.progress_tracking
            },
            'voice': {
                'enabled': self.voice_enabled,
                'engine': self.voice_engine,
                'speech_recognition_engine': self.speech_recognition_engine,
                'language': self.voice_language,
                'rate': self.voice_rate,
                'volume': self.voice_volume
            },
            'ui': {
                'enabled': self.ui_enabled,
                'theme': self.ui_theme,
                'port': self.ui_port,
                'debug': self.ui_debug,
                'auto_refresh': self.ui_auto_refresh
            },
            'api': {
                'enabled': self.api_enabled,
                'host': self.api_host,
                'port': self.api_port,
                'rate_limit': self.rate_limit,
                'authentication_required': self.authentication_required,
                'cors_enabled': self.cors_enabled
            },
            'security': {
                'encryption_enabled': self.encryption_enabled,
                'encryption_key_rotation': self.encryption_key_rotation,
                'session_encryption': self.session_encryption,
                'audit_logging': self.audit_logging,
                'access_control': self.access_control
            },
            'performance': {
                'monitoring_enabled': self.monitoring_enabled,
                'metrics_collection': self.metrics_collection,
                'profiling_enabled': self.profiling_enabled,
                'resource_limits': {
                    'max_cpu_percent': self.max_cpu_percent,
                    'max_memory_percent': self.max_memory_percent,
                    'max_disk_usage': self.max_disk_usage
                }
            },
            'development': {
                'debug_mode': self.debug_mode,
                'verbose_logging': self.verbose_logging,
                'hot_reload': self.hot_reload,
                'test_mode': self.test_mode,
                'mock_services': self.mock_services
            }
        }
    
    def save(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to a file.
        
        Args:
            file_path: Path to save the configuration. If not provided,
                      uses the original file path or creates a new one.
        """
        if file_path is None:
            file_path = self._config_file or "config.yaml"
        
        config_path = Path(file_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self._to_dict(), f, default_flow_style=False, indent=2)
                elif config_path.suffix.lower() == '.json':
                    json.dump(self._to_dict(), f, indent=2)
                else:
                    raise ValueError(f"Unsupported file format: {config_path.suffix}")
            
            logger.info(f"Configuration saved to: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'logging.level')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'logging.level')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Update the corresponding attribute if possible
        self._update_from_dict(self._config_data)
    
    def reload(self) -> None:
        """
        Reload configuration from the original file.
        """
        if self._config_file:
            self.from_file(self._config_file)
        else:
            logger.warning("No configuration file to reload from")
    
    def validate(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Basic validation rules
        if self.max_concurrent_agents <= 0:
            logger.error("max_concurrent_agents must be positive")
            return False
        
        if self.session_timeout <= 0:
            logger.error("session_timeout must be positive")
            return False
        
        if self.communication_port <= 0 or self.communication_port > 65535:
            logger.error("communication_port must be in range 1-65535")
            return False
        
        if self.api_port <= 0 or self.api_port > 65535:
            logger.error("api_port must be in range 1-65535")
            return False
        
        if self.ui_port <= 0 or self.ui_port > 65535:
            logger.error("ui_port must be in range 1-65535")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"FrameworkConfig(name='{self.name}', version='{self.version}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the configuration."""
        return f"FrameworkConfig(name='{self.name}', version='{self.version}', file='{self._config_file}')"


# Global configuration instance
_global_config: Optional[FrameworkConfig] = None


def get_config() -> FrameworkConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Global FrameworkConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = FrameworkConfig.from_file("config/default.yaml")
    return _global_config


def set_config(config: FrameworkConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: FrameworkConfig instance to set as global
    """
    global _global_config
    _global_config = config


def load_config(config_file: Union[str, Path]) -> FrameworkConfig:
    """
    Load configuration from a file and set it as global.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Loaded FrameworkConfig instance
    """
    config = FrameworkConfig.from_file(config_file)
    set_config(config)
    return config