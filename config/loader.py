"""
ATS MAFIA Framework Configuration Loader

This module provides utilities for loading configuration from various sources
including files, environment variables, and command-line arguments.
"""

import os
import yaml
import json
import argparse
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Configuration loader that can load settings from multiple sources.
    
    Supports loading from:
    - YAML/JSON configuration files
    - Environment variables
    - Command-line arguments
    - Default values
    """
    
    def __init__(self):
        """Initialize the configuration loader."""
        self._config_data: Dict[str, Any] = {}
        self._sources: List[str] = []
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the loaded configuration
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
        """
        config_path = Path(file_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
            
            self._merge_config(config_data)
            self._sources.append(f"file:{config_path}")
            
            logger.info(f"Configuration loaded from file: {config_path}")
            return config_data
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise ValueError(f"Invalid configuration file: {e}")
    
    def load_from_env(self, prefix: str = "ATS_MAFIA_") -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variables (default: "ATS_MAFIA_")
            
        Returns:
            Dictionary containing the loaded configuration
        """
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Handle nested keys with underscores
                keys = config_key.split('_')
                
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Build nested dictionary structure
                current = env_config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = converted_value
        
        if env_config:
            self._merge_config(env_config)
            self._sources.append(f"env:{prefix}")
            logger.info(f"Configuration loaded from environment variables with prefix: {prefix}")
        
        return env_config
    
    def load_from_args(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Load configuration from command-line arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Dictionary containing the loaded configuration
        """
        if args is None:
            return {}
        
        args_config = {}
        
        # Extract configuration-related arguments
        config_args = {
            'max_concurrent_agents': getattr(args, 'max_concurrent_agents', None),
            'session_timeout': getattr(args, 'session_timeout', None),
            'log_level': getattr(args, 'log_level', None),
            'communication_port': getattr(args, 'communication_port', None),
            'api_port': getattr(args, 'api_port', None),
            'ui_port': getattr(args, 'ui_port', None),
            'debug_mode': getattr(args, 'debug_mode', None),
            'config_file': getattr(args, 'config_file', None)
        }
        
        # Filter out None values
        config_args = {k: v for k, v in config_args.items() if v is not None}
        
        if config_args:
            self._merge_config(config_args)
            self._sources.append("args:command_line")
            logger.info("Configuration loaded from command-line arguments")
        
        return config_args
    
    def load_default(self, default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load default configuration.
        
        Args:
            default_config: Default configuration dictionary
            
        Returns:
            Dictionary containing the default configuration
        """
        if default_config is None:
            # Load from default configuration file
            default_path = Path(__file__).parent / "default.yaml"
            if default_path.exists():
                with open(default_path, 'r', encoding='utf-8') as f:
                    default_config = yaml.safe_load(f)
            else:
                default_config = {}
        
        self._merge_config(default_config)
        self._sources.append("default")
        logger.info("Default configuration loaded")
        
        return default_config
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the merged configuration.
        
        Returns:
            Dictionary containing the merged configuration from all sources
        """
        return self._config_data.copy()
    
    def get_sources(self) -> List[str]:
        """
        Get the list of configuration sources.
        
        Returns:
            List of configuration sources in order of loading
        """
        return self._sources.copy()
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration with existing configuration.
        
        Args:
            new_config: New configuration to merge
        """
        self._deep_merge(self._config_data, new_config)
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary to merge into
            update: Dictionary to merge from
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable value to appropriate type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value (int, float, bool, or string)
        """
        # Try to convert to boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """
        Create an argument parser for configuration options.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description="ATS MAFIA Framework",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to configuration file'
        )
        
        parser.add_argument(
            '--max-concurrent-agents',
            type=int,
            help='Maximum number of concurrent agents'
        )
        
        parser.add_argument(
            '--session-timeout',
            type=int,
            help='Session timeout in seconds'
        )
        
        parser.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Logging level'
        )
        
        parser.add_argument(
            '--communication-port',
            type=int,
            help='Communication server port'
        )
        
        parser.add_argument(
            '--api-port',
            type=int,
            help='API server port'
        )
        
        parser.add_argument(
            '--ui-port',
            type=int,
            help='UI server port'
        )
        
        parser.add_argument(
            '--debug-mode',
            action='store_true',
            help='Enable debug mode'
        )
        
        parser.add_argument(
            '--verbose-logging',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Enable test mode'
        )
        
        return parser
    
    def load_all(self, 
                 config_file: Optional[Union[str, Path]] = None,
                 env_prefix: str = "ATS_MAFIA_",
                 args: Optional[argparse.Namespace] = None,
                 default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from all sources in priority order.
        
        Priority order (highest to lowest):
        1. Command-line arguments
        2. Environment variables
        3. Configuration file
        4. Default values
        
        Args:
            config_file: Path to configuration file
            env_prefix: Prefix for environment variables
            args: Parsed command-line arguments
            default_config: Default configuration dictionary
            
        Returns:
            Dictionary containing the merged configuration
        """
        # Load default configuration first
        self.load_default(default_config)
        
        # Load from configuration file
        if config_file:
            try:
                self.load_from_file(config_file)
            except FileNotFoundError:
                logger.warning(f"Configuration file not found: {config_file}")
        
        # Load from environment variables
        self.load_from_env(env_prefix)
        
        # Load from command-line arguments
        self.load_from_args(args)
        
        logger.info(f"Configuration loaded from sources: {self.get_sources()}")
        return self.get_config()


def load_config(config_file: Optional[Union[str, Path]] = None,
                env_prefix: str = "ATS_MAFIA_",
                args: Optional[argparse.Namespace] = None,
                default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration from all sources.
    
    Args:
        config_file: Path to configuration file
        env_prefix: Prefix for environment variables
        args: Parsed command-line arguments
        default_config: Default configuration dictionary
        
    Returns:
        Dictionary containing the merged configuration
    """
    loader = ConfigLoader()
    return loader.load_all(config_file, env_prefix, args, default_config)