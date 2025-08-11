"""
Configuration management system for Environment Dev Deep Evaluation.

This module provides centralized configuration management with support for
multiple configuration sources, validation, and runtime updates.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .exceptions import ConfigurationError, ValidationError


@dataclass
class SystemConfiguration:
    """System-wide configuration settings."""
    
    # Core system settings
    debug_mode: bool = False
    log_level: str = "INFO"
    max_parallel_operations: int = 4
    operation_timeout: int = 300  # seconds
    
    # Detection settings
    detection_cache_enabled: bool = True
    detection_cache_ttl: int = 3600  # seconds
    hierarchical_detection_enabled: bool = True
    
    # Download settings
    download_timeout: int = 300  # seconds
    max_download_retries: int = 3
    parallel_downloads_enabled: bool = True
    hash_verification_required: bool = True
    
    # Installation settings
    automatic_rollback_enabled: bool = True
    backup_before_installation: bool = True
    privilege_escalation_prompt: bool = True
    
    # Steam Deck settings
    steam_deck_detection_enabled: bool = True
    steam_deck_optimizations_enabled: bool = True
    
    # Storage settings
    intelligent_storage_enabled: bool = True
    compression_enabled: bool = True
    cleanup_after_installation: bool = True
    
    # Plugin settings
    plugin_system_enabled: bool = True
    plugin_signature_verification: bool = True
    plugin_sandboxing_enabled: bool = True
    
    # UI settings
    modern_ui_enabled: bool = True
    real_time_progress: bool = True
    detailed_feedback: bool = True
    
    # Paths
    base_directory: str = field(default_factory=lambda: os.getcwd())
    config_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "config"))
    cache_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "cache"))
    logs_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "logs"))
    downloads_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "downloads"))
    temp_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "temp"))
    backups_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "backups"))
    plugins_directory: str = field(default_factory=lambda: os.path.join(os.getcwd(), "plugins"))
    
    # Runtime detection settings
    essential_runtimes: List[str] = field(default_factory=lambda: [
        "Git 2.47.1",
        ".NET SDK 8.0", 
        "Java JDK 21",
        "Visual C++ Redistributables",
        "Anaconda3",
        ".NET Desktop Runtime 8.0/9.0",
        "PowerShell 7",
        "Node.js/Python (updated)"
    ])
    
    # Package managers to detect
    package_managers: List[str] = field(default_factory=lambda: [
        "npm", "pip", "conda", "yarn", "pipenv"
    ])


class ConfigurationManager:
    """
    Centralized configuration management system.
    
    Handles loading, validation, and management of system-wide configuration
    settings from multiple sources with proper validation and error handling.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self._config_path = Path(config_path) if config_path else None
        self._config = SystemConfiguration()
        self._config_sources: List[str] = []
        self._last_loaded: Optional[datetime] = None
        
        # Load configuration from available sources
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from available sources."""
        try:
            # Load from default locations
            self._load_from_default_locations()
            
            # Load from specified path if provided
            if self._config_path and self._config_path.exists():
                self._load_from_file(self._config_path)
            
            # Load from environment variables
            self._load_from_environment()
            
            # Validate configuration
            self._validate_configuration()
            
            self._last_loaded = datetime.now()
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                context={"config_sources": self._config_sources}
            ) from e
    
    def _load_from_default_locations(self) -> None:
        """Load configuration from default locations."""
        default_locations = [
            Path("config/environment_dev_deep_evaluation.yaml"),
            Path("config/environment_dev_deep_evaluation.json"),
            Path("environment_dev_deep_evaluation.yaml"),
            Path("environment_dev_deep_evaluation.json"),
        ]
        
        for location in default_locations:
            if location.exists():
                self._load_from_file(location)
                break
    
    def _load_from_file(self, file_path: Path) -> None:
        """Load configuration from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {file_path.suffix}")
            
            # Update configuration with loaded data
            self._update_config_from_dict(data)
            self._config_sources.append(str(file_path))
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {file_path}: {str(e)}"
            ) from e
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_prefix = "ENVDEV_DEEP_EVAL_"
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                
                # Convert string values to appropriate types
                if value.lower() in ['true', 'false']:
                    env_config[config_key] = value.lower() == 'true'
                elif value.isdigit():
                    env_config[config_key] = int(value)
                else:
                    env_config[config_key] = value
        
        if env_config:
            self._update_config_from_dict(env_config)
            self._config_sources.append("environment_variables")
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary data."""
        for key, value in data.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def _validate_configuration(self) -> None:
        """Validate configuration settings."""
        errors = []
        
        # Validate timeout values
        if self._config.operation_timeout <= 0:
            errors.append("operation_timeout must be positive")
        
        if self._config.download_timeout <= 0:
            errors.append("download_timeout must be positive")
        
        # Validate retry settings
        if self._config.max_download_retries < 0:
            errors.append("max_download_retries must be non-negative")
        
        # Validate parallel operations
        if self._config.max_parallel_operations <= 0:
            errors.append("max_parallel_operations must be positive")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self._config.log_level not in valid_log_levels:
            errors.append(f"log_level must be one of: {', '.join(valid_log_levels)}")
        
        # Validate directories exist or can be created
        directories = [
            self._config.config_directory,
            self._config.cache_directory,
            self._config.logs_directory,
            self._config.downloads_directory,
            self._config.temp_directory,
            self._config.backups_directory,
            self._config.plugins_directory,
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {directory}: {str(e)}")
        
        if errors:
            raise ValidationError(
                f"Configuration validation failed: {'; '.join(errors)}",
                context={"validation_errors": errors}
            )
    
    def get_config(self) -> SystemConfiguration:
        """Get current system configuration."""
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if not hasattr(self._config, key):
            raise ConfigurationError(f"Unknown configuration key: {key}")
        
        setattr(self._config, key, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        for key, value in updates.items():
            self.set(key, value)
        
        # Re-validate after updates
        self._validate_configuration()
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save current configuration to file."""
        file_path = Path(file_path)
        
        # Convert configuration to dictionary
        config_dict = {}
        for field_name in self._config.__dataclass_fields__:
            config_dict[field_name] = getattr(self._config, field_name)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
                    
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {file_path}: {str(e)}"
            ) from e
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._config_sources.clear()
        self._load_configuration()
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about configuration manager state."""
        return {
            "config_sources": self._config_sources,
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "config_path": str(self._config_path) if self._config_path else None,
        }