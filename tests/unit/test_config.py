"""
ATS MAFIA Framework Configuration Unit Tests

This module contains unit tests for the configuration management system.
"""

import unittest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from ...config.settings import FrameworkConfig
from ...config.loader import ConfigLoader
from ...config.validator import ConfigValidator
from ..framework.decorators import unit_test, setup_test, teardown_test
from ..framework.test_framework import TestSuite, TestCase
from ..framework.test_types import TestType, TestPriority
from ..utils import TestUtils


class TestConfig(TestCase):
    """Unit tests for configuration management."""
    
    def __init__(self):
        super().__init__("test_config", TestType.UNIT)
        self.test_utils = TestUtils()
        self.temp_dir = None
        self.config_file = None
    
    @setup_test
    def setup(self):
        """Set up test environment."""
        self.temp_dir = self.test_utils.create_temp_dir("config_test_")
    
    @teardown_test
    def teardown(self):
        """Clean up test environment."""
        self.test_utils.cleanup()
    
    @unit_test(
        name="test_framework_config_creation",
        description="Test basic FrameworkConfig creation",
        priority=TestPriority.NORMAL
    )
    def test_framework_config_creation(self):
        """Test basic FrameworkConfig creation."""
        config = FrameworkConfig()
        
        # Test default values
        assert config.name == "ATS MAFIA Framework"
        assert config.version == "1.0.0"
        assert config.max_concurrent_agents == 10
        assert config.session_timeout == 3600
        assert config.log_level == "INFO"
        assert config.audit_enabled is True
        
        self.assertions.append("FrameworkConfig created with correct defaults")
    
    @unit_test(
        name="test_framework_config_from_dict",
        description="Test FrameworkConfig creation from dictionary",
        priority=TestPriority.NORMAL
    )
    def test_framework_config_from_dict(self):
        """Test FrameworkConfig creation from dictionary."""
        config_data = {
            "name": "Test Config",
            "version": "2.0.0",
            "max_concurrent_agents": 20,
            "session_timeout": 7200,
            "log_level": "DEBUG"
        }
        
        config = FrameworkConfig.from_dict(config_data)
        
        assert config.name == "Test Config"
        assert config.version == "2.0.0"
        assert config.max_concurrent_agents == 20
        assert config.session_timeout == 7200
        assert config.log_level == "DEBUG"
        
        self.assertions.append("FrameworkConfig created correctly from dictionary")
    
    @unit_test(
        name="test_framework_config_to_dict",
        description="Test FrameworkConfig conversion to dictionary",
        priority=TestPriority.NORMAL
    )
    def test_framework_config_to_dict(self):
        """Test FrameworkConfig conversion to dictionary."""
        config = FrameworkConfig()
        config.name = "Test Config"
        config.version = "2.0.0"
        config.max_concurrent_agents = 20
        
        config_dict = config.to_dict()
        
        assert config_dict["name"] == "Test Config"
        assert config_dict["version"] == "2.0.0"
        assert config_dict["max_concurrent_agents"] == 20
        assert isinstance(config_dict, dict)
        
        self.assertions.append("FrameworkConfig converted to dictionary correctly")
    
    @unit_test(
        name="test_framework_config_from_yaml_file",
        description="Test FrameworkConfig loading from YAML file",
        priority=TestPriority.NORMAL
    )
    def test_framework_config_from_yaml_file(self):
        """Test FrameworkConfig loading from YAML file."""
        # Create test YAML config file
        config_data = {
            "name": "YAML Test Config",
            "version": "1.5.0",
            "max_concurrent_agents": 15,
            "session_timeout": 5400,
            "log_level": "WARNING"
        }
        
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load config from file
        config = FrameworkConfig.from_file(str(self.config_file))
        
        assert config.name == "YAML Test Config"
        assert config.version == "1.5.0"
        assert config.max_concurrent_agents == 15
        assert config.session_timeout == 5400
        assert config.log_level == "WARNING"
        
        self.assertions.append("FrameworkConfig loaded from YAML file correctly")
    
    @unit_test(
        name="test_framework_config_from_json_file",
        description="Test FrameworkConfig loading from JSON file",
        priority=TestPriority.NORMAL
    )
    def test_framework_config_from_json_file(self):
        """Test FrameworkConfig loading from JSON file."""
        # Create test JSON config file
        config_data = {
            "name": "JSON Test Config",
            "version": "1.8.0",
            "max_concurrent_agents": 25,
            "session_timeout": 9000,
            "log_level": "ERROR"
        }
        
        self.config_file = Path(self.temp_dir) / "test_config.json"
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Load config from file
        config = FrameworkConfig.from_file(str(self.config_file))
        
        assert config.name == "JSON Test Config"
        assert config.version == "1.8.0"
        assert config.max_concurrent_agents == 25
        assert config.session_timeout == 9000
        assert config.log_level == "ERROR"
        
        self.assertions.append("FrameworkConfig loaded from JSON file correctly")
    
    @unit_test(
        name="test_framework_config_validation",
        description="Test FrameworkConfig validation",
        priority=TestPriority.HIGH
    )
    def test_framework_config_validation(self):
        """Test FrameworkConfig validation."""
        # Test valid config
        valid_config = FrameworkConfig()
        assert valid_config.validate() is True
        
        # Test invalid config (negative values)
        invalid_config = FrameworkConfig()
        invalid_config.max_concurrent_agents = -1
        assert invalid_config.validate() is False
        
        # Test invalid config (invalid port)
        invalid_config = FrameworkConfig()
        invalid_config.communication_port = 70000
        assert invalid_config.validate() is False
        
        self.assertions.append("FrameworkConfig validation working correctly")
    
    @unit_test(
        name="test_config_loader",
        description="Test ConfigLoader functionality",
        priority=TestPriority.NORMAL
    )
    def test_config_loader(self):
        """Test ConfigLoader functionality."""
        loader = ConfigLoader()
        
        # Create test config file
        config_data = {
            "name": "Loader Test Config",
            "version": "1.0.0",
            "max_concurrent_agents": 10
        }
        
        self.config_file = Path(self.temp_dir) / "loader_test.yaml"
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load config
        config = loader.load(str(self.config_file))
        
        assert config is not None
        assert config.name == "Loader Test Config"
        assert config.max_concurrent_agents == 10
        
        self.assertions.append("ConfigLoader working correctly")
    
    @unit_test(
        name="test_config_validator",
        description="Test ConfigValidator functionality",
        priority=TestPriority.NORMAL
    )
    def test_config_validator(self):
        """Test ConfigValidator functionality."""
        validator = ConfigValidator()
        
        # Test valid config
        valid_config = FrameworkConfig()
        validation_result = validator.validate(valid_config)
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # Test invalid config
        invalid_config = FrameworkConfig()
        invalid_config.max_concurrent_agents = -5
        validation_result = validator.validate(invalid_config)
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        
        self.assertions.append("ConfigValidator working correctly")
    
    @unit_test(
        name="test_config_environment_override",
        description="Test configuration override from environment variables",
        priority=TestPriority.NORMAL
    )
    def test_config_environment_override(self):
        """Test configuration override from environment variables."""
        # Test with environment variable override
        with patch.dict('os.environ', {'ATS_MAFIA_LOG_LEVEL': 'DEBUG'}):
            config = FrameworkConfig()
            config.apply_environment_overrides()
            assert config.log_level == "DEBUG"
        
        self.assertions.append("Environment variable override working correctly")
    
    @unit_test(
        name="test_config_merge",
        description="Test configuration merging",
        priority=TestPriority.NORMAL
    )
    def test_config_merge(self):
        """Test configuration merging."""
        base_config = FrameworkConfig()
        base_config.name = "Base Config"
        base_config.max_concurrent_agents = 10
        
        override_config = {
            "max_concurrent_agents": 20,
            "log_level": "DEBUG"
        }
        
        # Merge configurations
        base_config.merge(override_config)
        
        assert base_config.name == "Base Config"  # Should remain unchanged
        assert base_config.max_concurrent_agents == 20  # Should be overridden
        assert base_config.log_level == "DEBUG"  # Should be added
        
        self.assertions.append("Configuration merging working correctly")
    
    @unit_test(
        name="test_config_nested_access",
        description="Test nested configuration access",
        priority=TestPriority.NORMAL
    )
    def test_config_nested_access(self):
        """Test nested configuration access."""
        config = FrameworkConfig()
        
        # Test nested access
        assert config.get("logging.level") == config.log_level
        assert config.get("communication.port") == config.communication_port
        
        # Test nested setting
        config.set("logging.level", "DEBUG")
        assert config.log_level == "DEBUG"
        
        config.set("communication.port", 9090)
        assert config.communication_port == 9090
        
        self.assertions.append("Nested configuration access working correctly")
    
    @unit_test(
        name="test_config_copy",
        description="Test configuration copying",
        priority=TestPriority.NORMAL
    )
    def test_config_copy(self):
        """Test configuration copying."""
        original_config = FrameworkConfig()
        original_config.name = "Original Config"
        original_config.max_concurrent_agents = 15
        
        # Create copy
        copied_config = original_config.copy()
        
        # Verify copy
        assert copied_config.name == "Original Config"
        assert copied_config.max_concurrent_agents == 15
        
        # Modify original and verify copy is unchanged
        original_config.name = "Modified Config"
        assert copied_config.name == "Original Config"
        
        self.assertions.append("Configuration copying working correctly")


class TestConfigSuite(TestSuite):
    """Test suite for configuration tests."""
    
    def __init__(self):
        super().__init__(
            name="Configuration Tests",
            description="Unit tests for configuration management system"
        )
        
        # Add test cases
        self.add_test(TestConfig())