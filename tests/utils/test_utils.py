"""
ATS MAFIA Test Utilities

This module provides general utility functions for testing
the ATS MAFIA framework.
"""

import asyncio
import json
import time
import uuid
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone
import logging


class TestUtils:
    """
    Utility class providing common test helper functions.
    """
    
    def __init__(self):
        """Initialize test utilities."""
        self.logger = logging.getLogger("test_utils")
        self.temp_dirs: List[str] = []
        self.temp_files: List[str] = []
    
    def cleanup(self) -> None:
        """Clean up temporary files and directories."""
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp dir {temp_dir}: {e}")
        
        self.temp_files.clear()
        self.temp_dirs.clear()
    
    def create_temp_dir(self, prefix: str = "ats_test_") -> str:
        """
        Create a temporary directory.
        
        Args:
            prefix: Directory name prefix
            
        Returns:
            Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, 
                        content: str = "", 
                        suffix: str = ".tmp", 
                        prefix: str = "ats_test_") -> str:
        """
        Create a temporary file with content.
        
        Args:
            content: File content
            suffix: File suffix
            prefix: File prefix
            
        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=suffix, 
            prefix=prefix, 
            delete=False
        ) as f:
            f.write(content)
            temp_file = f.name
        
        self.temp_files.append(temp_file)
        return temp_file
    
    def generate_uuid(self) -> str:
        """
        Generate a UUID string.
        
        Returns:
            UUID string
        """
        return str(uuid.uuid4())
    
    def generate_timestamp(self) -> str:
        """
        Generate a timestamp string.
        
        Returns:
            ISO format timestamp
        """
        return datetime.now(timezone.utc).isoformat()
    
    def calculate_hash(self, data: Union[str, bytes]) -> str:
        """
        Calculate SHA-256 hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
    def wait_for_condition(self,
                          condition: Callable[[], bool],
                          timeout: float = 30.0,
                          interval: float = 0.1) -> bool:
        """
        Wait for a condition to become true.
        
        Args:
            condition: Function that returns boolean
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            
        Returns:
            True if condition became true, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(interval)
        
        return False
    
    async def wait_for_condition_async(self,
                                     condition: Callable[[], bool],
                                     timeout: float = 30.0,
                                     interval: float = 0.1) -> bool:
        """
        Wait for a condition to become true (async version).
        
        Args:
            condition: Async function that returns boolean
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            
        Returns:
            True if condition became true, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if asyncio.iscoroutinefunction(condition):
                result = await condition()
            else:
                result = condition()
            
            if result:
                return True
            
            await asyncio.sleep(interval)
        
        return False
    
    def measure_time(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Measure execution time of a function.
        
        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, execution_time_seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time
    
    async def measure_time_async(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Measure execution time of an async function.
        
        Args:
            func: Async function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, execution_time_seconds)
        """
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time
    
    def assert_file_exists(self, file_path: str) -> None:
        """
        Assert that a file exists.
        
        Args:
            file_path: Path to file
            
        Raises:
            AssertionError: If file doesn't exist
        """
        if not Path(file_path).exists():
            raise AssertionError(f"File does not exist: {file_path}")
    
    def assert_file_contains(self, file_path: str, content: str) -> None:
        """
        Assert that a file contains specific content.
        
        Args:
            file_path: Path to file
            content: Content to check for
            
        Raises:
            AssertionError: If content not found
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        if content not in file_content:
            raise AssertionError(f"File {file_path} does not contain: {content}")
    
    def assert_json_file_valid(self, file_path: str) -> Dict[str, Any]:
        """
        Assert that a file contains valid JSON.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            AssertionError: If JSON is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON in file {file_path}: {e}")
    
    def create_mock_config(self, **overrides) -> Dict[str, Any]:
        """
        Create a mock configuration for testing.
        
        Args:
            **overrides: Configuration overrides
            
        Returns:
            Mock configuration dictionary
        """
        default_config = {
            'framework': {
                'name': 'ATS MAFIA Framework',
                'version': '1.0.0',
                'description': 'Test Configuration'
            },
            'core': {
                'max_concurrent_agents': 5,
                'session_timeout': 1800,
                'checkpoint_interval': 300,
                'recovery_enabled': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/test.log',
                'audit_enabled': True
            },
            'profiles': {
                'default_profile_path': 'profiles/',
                'cache_enabled': True,
                'validation_enabled': True
            },
            'tools': {
                'enabled_tools': [],
                'tool_paths': ['tools/'],
                'timeout': 30,
                'sandbox_enabled': True
            },
            'communication': {
                'protocol': 'websocket',
                'host': 'localhost',
                'port': 8080,
                'ssl_enabled': False
            },
            'orchestrator': {
                'max_concurrent_sessions': 3,
                'session_timeout': 3600,
                'progress_tracking': True
            },
            'voice': {
                'enabled': False,
                'engine': 'pyttsx3',
                'language': 'en-US'
            },
            'ui': {
                'enabled': True,
                'theme': 'dark',
                'port': 8501
            },
            'api': {
                'enabled': True,
                'host': 'localhost',
                'port': 5000
            },
            'security': {
                'encryption_enabled': True,
                'audit_logging': True
            },
            'performance': {
                'monitoring_enabled': True,
                'metrics_collection': True
            },
            'development': {
                'debug_mode': True,
                'test_mode': True,
                'mock_services': True
            }
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                # Handle nested keys like 'logging.level'
                parts = key.split('.')
                config_section = default_config
                for part in parts[:-1]:
                    if part not in config_section:
                        config_section[part] = {}
                    config_section = config_section[part]
                config_section[parts[-1]] = value
            else:
                default_config[key] = value
        
        return default_config
    
    def create_test_environment(self, name: str = "test_env") -> Dict[str, Any]:
        """
        Create a test environment setup.
        
        Args:
            name: Environment name
            
        Returns:
            Test environment configuration
        """
        env_dir = self.create_temp_dir(f"ats_env_{name}_")
        
        environment = {
            'name': name,
            'directory': env_dir,
            'config_file': f"{env_dir}/config.yaml",
            'log_directory': f"{env_dir}/logs",
            'data_directory': f"{env_dir}/data",
            'profile_directory': f"{env_dir}/profiles",
            'tool_directory': f"{env_dir}/tools"
        }
        
        # Create directories
        for directory in [environment['log_directory'], 
                         environment['data_directory'],
                         environment['profile_directory'],
                         environment['tool_directory']]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        return environment
    
    def capture_logs(self, logger_name: str, level: str = "INFO") -> List[str]:
        """
        Capture logs from a specific logger.
        
        Args:
            logger_name: Name of the logger
            level: Log level to capture
            
        Returns:
            List of log messages
        """
        # This is a simplified implementation
        # In a real scenario, you would use logging handlers
        # to capture log messages
        return []
    
    def simulate_network_delay(self, delay: float = 0.1) -> None:
        """
        Simulate network delay for testing.
        
        Args:
            delay: Delay in seconds
        """
        time.sleep(delay)
    
    async def simulate_network_delay_async(self, delay: float = 0.1) -> None:
        """
        Simulate network delay for testing (async version).
        
        Args:
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
    
    def retry_until_success(self,
                           func: Callable,
                           max_attempts: int = 3,
                           delay: float = 1.0) -> Any:
        """
        Retry a function until it succeeds.
        
        Args:
            func: Function to retry
            max_attempts: Maximum number of attempts
            delay: Delay between attempts
            
        Returns:
            Function result
            
        Raises:
            Exception: If all attempts fail
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    time.sleep(delay)
        
        raise last_exception
    
    async def retry_until_success_async(self,
                                      func: Callable,
                                      max_attempts: int = 3,
                                      delay: float = 1.0) -> Any:
        """
        Retry an async function until it succeeds.
        
        Args:
            func: Async function to retry
            max_attempts: Maximum number of attempts
            delay: Delay between attempts
            
        Returns:
            Function result
            
        Raises:
            Exception: If all attempts fail
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay)
        
        raise last_exception