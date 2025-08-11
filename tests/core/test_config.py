"""Tests for core.config module."""

import os
import json
import yaml
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from datetime import datetime

from core.config import ConfigurationManager, SystemConfiguration
from core.exceptions import ConfigurationError, ValidationError


class TestSystemConfiguration:
    """Tests for SystemConfiguration dataclass."""
    
    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = SystemConfiguration()
        
        # Core settings
        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.max_parallel_operations == 4
        assert config.operation_timeout == 300
        
        # Detection settings
        assert config.detection_cache_enabled is True
        assert config.detection_cache_ttl == 3600
        assert config.hierarchical_detection_enabled is True
        
        # Download settings
        assert config.download_timeout == 300
        assert config.max_download_retries == 3
        assert config.parallel_downloads_enabled is True
        assert config.hash_verification_required is True
        
        # Installation settings
        assert config.automatic_rollback_enabled is True
        assert config.backup_before_installation is True
        assert config.privilege_escalation_prompt is True
        
        # Plugin settings
        assert config.plugin_system_enabled is True
        assert config.plugin_signature_verification is True
        assert config.plugin_sandboxing_enabled is True
    
    def test_essential_runtimes_default(self):
        """Test that essential runtimes list is populated correctly."""
        config = SystemConfiguration()
        
        expected_runtimes = [
            "Git 2.47.1",
            ".NET SDK 8.0", 
            "Java JDK 21",
            "Visual C++ Redistributables",
            "Anaconda3",
            ".NET Desktop Runtime 8.0/9.0",
            "PowerShell 7",
            "Node.js/Python (updated)"
        ]
        
        assert config.essential_runtimes == expected_runtimes
    
    def test_package_managers_default(self):
        """Test that package managers list is populated correctly."""
        config = SystemConfiguration()
        
        expected_managers = ["npm", "pip", "conda", "yarn", "pipenv"]
        assert config.package_managers == expected_managers


class TestConfigurationManager:
    """Tests for ConfigurationManager class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_without_config_path(self):
        """Test ConfigurationManager initialization without config path."""
        with patch.object(ConfigurationManager, '_load_configuration'):
            manager = ConfigurationManager()
            
            assert manager._config_path is None
            assert isinstance(manager._config, SystemConfiguration)
            assert manager._config_sources == []
            assert manager._last_loaded is None
    
    def test_initialization_with_config_path(self):
        """Test ConfigurationManager initialization with config path."""
        config_path = self.temp_path / "test_config.yaml"
        
        with patch.object(ConfigurationManager, '_load_configuration'):
            manager = ConfigurationManager(str(config_path))
            
            assert manager._config_path == config_path
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "debug_mode": True,
            "log_level": "DEBUG",
            "max_parallel_operations": 8,
            "operation_timeout": 600
        }
        
        config_file = self.temp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager(str(config_file))
        
        assert manager._config.debug_mode is True
        assert manager._config.log_level == "DEBUG"
        assert manager._config.max_parallel_operations == 8
        assert manager._config.operation_timeout == 600
        assert str(config_file) in manager._config_sources
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "debug_mode": True,
            "log_level": "WARNING",
            "max_download_retries": 5
        }
        
        config_file = self.temp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigurationManager(str(config_file))
        
        assert manager._config.debug_mode is True
        assert manager._config.log_level == "WARNING"
        assert manager._config.max_download_retries == 5
        assert str(config_file) in manager._config_sources
    
    def test_load_from_environment_variables(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "ENVDEV_DEEP_EVAL_DEBUG_MODE": "true",
            "ENVDEV_DEEP_EVAL_LOG_LEVEL": "ERROR",
            "ENVDEV_DEEP_EVAL_MAX_PARALLEL_OPERATIONS": "6",
            "ENVDEV_DEEP_EVAL_OPERATION_TIMEOUT": "450"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigurationManager()
            
            assert manager._config.debug_mode is True
            assert manager._config.log_level == "ERROR"
            assert manager._config.max_parallel_operations == 6
            assert manager._config.operation_timeout == 450
            assert "environment_variables" in manager._config_sources
    
    def test_environment_variable_type_conversion(self):
        """Test proper type conversion for environment variables."""
        env_vars = {
            "ENVDEV_DEEP_EVAL_DEBUG_MODE": "false",
            "ENVDEV_DEEP_EVAL_DETECTION_CACHE_ENABLED": "true",
            "ENVDEV_DEEP_EVAL_MAX_PARALLEL_OPERATIONS": "10",
            "ENVDEV_DEEP_EVAL_BASE_DIRECTORY": "/custom/path"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigurationManager()
            
            assert manager._config.debug_mode is False
            assert manager._config.detection_cache_enabled is True
            assert manager._config.max_parallel_operations == 10
            assert manager._config.base_directory == "/custom/path"
    
    def test_configuration_validation_success(self):
        """Test successful configuration validation."""
        config_data = {
            "operation_timeout": 300,
            "download_timeout": 300,
            "max_download_retries": 3,
            "max_parallel_operations": 4,
            "log_level": "INFO"
        }
        
        config_file = self.temp_path / "valid_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Should not raise any exception
        manager = ConfigurationManager(str(config_file))
        assert manager._config.operation_timeout == 300
    
    def test_configuration_validation_invalid_timeout(self):
        """Test configuration validation with invalid timeout values."""
        config_data = {
            "operation_timeout": -100,
            "download_timeout": 0
        }
        
        config_file = self.temp_path / "invalid_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValidationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "operation_timeout must be positive" in str(exc_info.value)
        assert "download_timeout must be positive" in str(exc_info.value)
    
    def test_configuration_validation_invalid_log_level(self):
        """Test configuration validation with invalid log level."""
        config_data = {
            "log_level": "INVALID_LEVEL"
        }
        
        config_file = self.temp_path / "invalid_log_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValidationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "log_level must be one of" in str(exc_info.value)
    
    def test_configuration_validation_invalid_retries(self):
        """Test configuration validation with invalid retry values."""
        config_data = {
            "max_download_retries": -1,
            "max_parallel_operations": 0
        }
        
        config_file = self.temp_path / "invalid_retries_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValidationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "max_download_retries must be non-negative" in str(exc_info.value)
        assert "max_parallel_operations must be positive" in str(exc_info.value)
    
    def test_unsupported_file_format(self):
        """Test loading configuration from unsupported file format."""
        config_file = self.temp_path / "config.txt"
        config_file.write_text("some content")
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "Unsupported configuration file format" in str(exc_info.value)
    
    def test_malformed_yaml_file(self):
        """Test loading configuration from malformed YAML file."""
        config_file = self.temp_path / "malformed.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "Failed to load configuration from" in str(exc_info.value)
    
    def test_malformed_json_file(self):
        """Test loading configuration from malformed JSON file."""
        config_file = self.temp_path / "malformed.json"
        config_file.write_text('{"invalid": json, "content"}')
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationManager(str(config_file))
        
        assert "Failed to load configuration from" in str(exc_info.value)
    
    def test_get_config(self):
        """Test getting current configuration."""
        manager = ConfigurationManager()
        config = manager.get_config()
        
        assert isinstance(config, SystemConfiguration)
        assert config.debug_mode is False  # Default value
    
    def test_get_configuration_value(self):
        """Test getting specific configuration values."""
        manager = ConfigurationManager()
        
        assert manager.get("debug_mode") is False
        assert manager.get("log_level") == "INFO"
        assert manager.get("nonexistent_key", "default") == "default"
    
    def test_set_configuration_value(self):
        """Test setting configuration values."""
        manager = ConfigurationManager()
        
        manager.set("debug_mode", True)
        assert manager._config.debug_mode is True
        
        manager.set("log_level", "DEBUG")
        assert manager._config.log_level == "DEBUG"
    
    def test_set_invalid_configuration_key(self):
        """Test setting invalid configuration key."""
        manager = ConfigurationManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.set("invalid_key", "value")
        
        assert "Unknown configuration key" in str(exc_info.value)
    
    def test_update_multiple_values(self):
        """Test updating multiple configuration values."""
        manager = ConfigurationManager()
        
        updates = {
            "debug_mode": True,
            "log_level": "DEBUG",
            "max_parallel_operations": 8
        }
        
        manager.update(updates)
        
        assert manager._config.debug_mode is True
        assert manager._config.log_level == "DEBUG"
        assert manager._config.max_parallel_operations == 8
    
    def test_update_with_validation_error(self):
        """Test update that triggers validation error."""
        manager = ConfigurationManager()
        
        updates = {
            "operation_timeout": -100,
            "log_level": "INVALID"
        }
        
        with pytest.raises(ValidationError):
            manager.update(updates)
    
    def test_save_to_yaml_file(self):
        """Test saving configuration to YAML file."""
        manager = ConfigurationManager()
        manager.set("debug_mode", True)
        manager.set("log_level", "DEBUG")
        
        output_file = self.temp_path / "output_config.yaml"
        manager.save_to_file(output_file)
        
        assert output_file.exists()
        
        # Load and verify saved content
        with open(output_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["debug_mode"] is True
        assert saved_data["log_level"] == "DEBUG"
    
    def test_save_to_json_file(self):
        """Test saving configuration to JSON file."""
        manager = ConfigurationManager()
        manager.set("debug_mode", True)
        manager.set("max_parallel_operations", 6)
        
        output_file = self.temp_path / "output_config.json"
        manager.save_to_file(output_file)
        
        assert output_file.exists()
        
        # Load and verify saved content
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["debug_mode"] is True
        assert saved_data["max_parallel_operations"] == 6
    
    def test_save_to_unsupported_format(self):
        """Test saving configuration to unsupported file format."""
        manager = ConfigurationManager()
        output_file = self.temp_path / "config.txt"
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.save_to_file(output_file)
        
        assert "Unsupported file format" in str(exc_info.value)
    
    def test_reload_configuration(self):
        """Test reloading configuration from sources."""
        # Create initial config file
        config_data = {"debug_mode": False, "log_level": "INFO"}
        config_file = self.temp_path / "reload_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager(str(config_file))
        assert manager._config.debug_mode is False
        
        # Modify config file
        config_data["debug_mode"] = True
        config_data["log_level"] = "DEBUG"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Reload and verify changes
        manager.reload()
        assert manager._config.debug_mode is True
        assert manager._config.log_level == "DEBUG"
    
    def test_get_info(self):
        """Test getting configuration manager information."""
        config_file = self.temp_path / "info_config.yaml"
        config_file.write_text("debug_mode: true")
        
        manager = ConfigurationManager(str(config_file))
        info = manager.get_info()
        
        assert "config_sources" in info
        assert "last_loaded" in info
        assert "config_path" in info
        assert str(config_file) in info["config_sources"]
        assert info["config_path"] == str(config_file)
        assert info["last_loaded"] is not None
    
    def test_multiple_config_sources_precedence(self):
        """Test configuration precedence when multiple sources are used."""
        # Create config file
        config_data = {"debug_mode": False, "log_level": "INFO"}
        config_file = self.temp_path / "precedence_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Set environment variables (should override file)
        env_vars = {
            "ENVDEV_DEEP_EVAL_DEBUG_MODE": "true",
            "ENVDEV_DEEP_EVAL_LOG_LEVEL": "ERROR"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigurationManager(str(config_file))
            
            # Environment variables should take precedence
            assert manager._config.debug_mode is True
            assert manager._config.log_level == "ERROR"
            
            # Both sources should be recorded
            assert str(config_file) in manager._config_sources
            assert "environment_variables" in manager._config_sources
    
    def test_directory_creation_during_validation(self):
        """Test that required directories are created during validation."""
        config_data = {
            "config_directory": str(self.temp_path / "custom_config"),
            "cache_directory": str(self.temp_path / "custom_cache"),
            "logs_directory": str(self.temp_path / "custom_logs")
        }
        
        config_file = self.temp_path / "dir_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager(str(config_file))
        
        # Directories should be created
        assert Path(manager._config.config_directory).exists()
        assert Path(manager._config.cache_directory).exists()
        assert Path(manager._config.logs_directory).exists()
    
    def test_load_from_default_locations(self):
        """Test loading configuration from default locations."""
        # Create config directory and file
        config_dir = self.temp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "environment_dev_deep_evaluation.yaml"
        
        config_data = {"debug_mode": True, "log_level": "DEBUG"}
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Change working directory to temp_path
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_path)
            manager = ConfigurationManager()
            
            assert manager._config.debug_mode is True
            assert manager._config.log_level == "DEBUG"
            assert str(config_file) in manager._config_sources
        finally:
            os.chdir(original_cwd)