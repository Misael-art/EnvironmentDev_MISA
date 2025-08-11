"""
Base classes for integration components.
"""

from abc import ABC
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import platform
import subprocess
import json
from pathlib import Path

from ..core.base import SystemComponentBase, OperationResult
from ..core.exceptions import SteamDeckIntegrationError, PluginSystemError, IntelligentStorageError
from .interfaces import (
    PlatformIntegrationInterface,
    SteamDeckIntegrationInterface,
    PluginManagerInterface,
    StorageManagerInterface,
    PackageManagerIntegrationInterface,
    PlatformType,
    PlatformInfo,
    PluginStatus,
    PluginInfo,
    PluginValidationResult
)


class IntegrationBase(SystemComponentBase, ABC):
    """
    Base class for all integration components.
    
    Provides common functionality for platform integration,
    plugin management, and storage operations.
    """
    
    def __init__(self, config_manager, component_name: Optional[str] = None):
        """Initialize integration base component."""
        super().__init__(config_manager, component_name)
        self._platform_cache: Dict[str, Any] = {}
        self._plugin_registry: Dict[str, PluginInfo] = {}
        self._storage_analysis_cache: Dict[str, Any] = {}
        self._package_manager_cache: Dict[str, Any] = {}
        self._last_platform_detection: Optional[datetime] = None
    
    def validate_configuration(self) -> None:
        """Validate integration-specific configuration."""
        config = self.get_config()
        
        # Validate integration-specific settings
        if not hasattr(config, 'steam_deck_detection_enabled'):
            raise SteamDeckIntegrationError(
                "Missing steam_deck_detection_enabled configuration",
                context={"component": self._component_name}
            )
        
        if not hasattr(config, 'plugin_system_enabled'):
            raise PluginSystemError(
                "Missing plugin_system_enabled configuration",
                context={"component": self._component_name}
            )
        
        if not hasattr(config, 'intelligent_storage_enabled'):
            raise IntelligentStorageError(
                "Missing intelligent_storage_enabled configuration",
                context={"component": self._component_name}
            )
    
    def _detect_platform_type(self) -> PlatformType:
        """
        Detect the current platform type.
        
        Returns:
            PlatformType: Detected platform type
        """
        # Check cache first
        cache_key = "platform_type"
        cached_result = self._platform_cache.get(cache_key)
        
        if cached_result:
            cache_age = (datetime.now() - cached_result["timestamp"]).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return cached_result["platform_type"]
        
        # Detect platform
        system = platform.system().lower()
        
        if system == "windows":
            platform_type = PlatformType.WINDOWS
        elif system == "linux":
            # Check if it's Steam Deck
            if self._is_steam_deck():
                platform_type = PlatformType.STEAM_DECK
            else:
                platform_type = PlatformType.GENERIC_LINUX
        else:
            # Default to generic Linux for other Unix-like systems
            platform_type = PlatformType.GENERIC_LINUX
        
        # Cache result
        self._platform_cache[cache_key] = {
            "platform_type": platform_type,
            "timestamp": datetime.now()
        }
        
        return platform_type
    
    def _is_steam_deck(self) -> bool:
        """
        Check if current system is Steam Deck.
        
        Returns:
            bool: True if Steam Deck, False otherwise
        """
        try:
            # Method 1: Check DMI/SMBIOS information
            if self._check_dmi_smbios_for_steam_deck():
                return True
            
            # Method 2: Check for Steam Deck specific files
            steam_deck_files = [
                "/sys/devices/virtual/dmi/id/product_name",
                "/sys/devices/virtual/dmi/id/sys_vendor"
            ]
            
            for file_path in steam_deck_files:
                if Path(file_path).exists():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().strip().lower()
                            if "steam deck" in content or "valve" in content:
                                return True
                    except Exception:
                        continue
            
            # Method 3: Check for Steam client in typical Steam Deck locations
            steam_deck_paths = [
                "/home/deck/.steam",
                "/home/deck/.local/share/Steam"
            ]
            
            for path in steam_deck_paths:
                if Path(path).exists():
                    return True
            
            return False
            
        except Exception as e:
            self._logger.debug(f"Error detecting Steam Deck: {str(e)}")
            return False
    
    def _check_dmi_smbios_for_steam_deck(self) -> bool:
        """
        Check DMI/SMBIOS information for Steam Deck indicators.
        
        Returns:
            bool: True if Steam Deck indicators found
        """
        try:
            # Try using dmidecode if available
            result = subprocess.run(
                ["dmidecode", "-s", "system-product-name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                product_name = result.stdout.strip().lower()
                if "steam deck" in product_name:
                    return True
            
            # Try alternative method
            result = subprocess.run(
                ["dmidecode", "-s", "system-manufacturer"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                manufacturer = result.stdout.strip().lower()
                if "valve" in manufacturer:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _get_system_capabilities(self, platform_type: PlatformType) -> List[str]:
        """
        Get system capabilities based on platform type.
        
        Args:
            platform_type: Platform type
            
        Returns:
            List[str]: List of system capabilities
        """
        capabilities = []
        
        if platform_type == PlatformType.WINDOWS:
            capabilities.extend([
                "registry_access",
                "windows_services",
                "powershell",
                "wmi_access"
            ])
        elif platform_type == PlatformType.STEAM_DECK:
            capabilities.extend([
                "steam_integration",
                "controller_support",
                "touchscreen",
                "power_management",
                "glossi_support"
            ])
        elif platform_type == PlatformType.GENERIC_LINUX:
            capabilities.extend([
                "package_managers",
                "systemd",
                "desktop_environments"
            ])
        
        # Common capabilities
        capabilities.extend([
            "file_system_access",
            "network_access",
            "process_management"
        ])
        
        return capabilities
    
    def _get_system_limitations(self, platform_type: PlatformType) -> List[str]:
        """
        Get system limitations based on platform type.
        
        Args:
            platform_type: Platform type
            
        Returns:
            List[str]: List of system limitations
        """
        limitations = []
        
        if platform_type == PlatformType.STEAM_DECK:
            limitations.extend([
                "limited_storage",
                "battery_constraints",
                "read_only_filesystem",
                "limited_package_managers"
            ])
        elif platform_type == PlatformType.GENERIC_LINUX:
            limitations.extend([
                "permission_restrictions",
                "distribution_variations"
            ])
        
        return limitations
    
    def _get_available_disk_space(self, path: str) -> int:
        """
        Get available disk space for a path.
        
        Args:
            path: Path to check
            
        Returns:
            int: Available space in bytes
        """
        try:
            import shutil
            _, _, free_bytes = shutil.disk_usage(path)
            return free_bytes
        except Exception as e:
            self._logger.warning(f"Failed to get disk space for {path}: {str(e)}")
            return 0
    
    def _get_directory_size(self, path: str) -> int:
        """
        Get total size of directory.
        
        Args:
            path: Directory path
            
        Returns:
            int: Directory size in bytes
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in Path(path).walk():
                for filename in filenames:
                    file_path = dirpath / filename
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
            return total_size
        except Exception as e:
            self._logger.warning(f"Failed to get directory size for {path}: {str(e)}")
            return 0
    
    def _validate_plugin_structure(self, plugin_path: str) -> PluginValidationResult:
        """
        Validate plugin structure and format.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            PluginValidationResult: Validation results
        """
        errors = []
        warnings = []
        
        try:
            plugin_file = Path(plugin_path)
            
            # Check if file exists
            if not plugin_file.exists():
                errors.append(f"Plugin file does not exist: {plugin_path}")
                return PluginValidationResult(
                    is_valid=False,
                    structure_valid=False,
                    signature_valid=False,
                    dependencies_satisfied=False,
                    security_check_passed=False,
                    validation_errors=errors,
                    validation_warnings=warnings
                )
            
            # Check file extension
            if plugin_file.suffix.lower() not in ['.py', '.zip', '.tar.gz']:
                warnings.append(f"Unusual plugin file extension: {plugin_file.suffix}")
            
            # Basic structure validation (simplified)
            structure_valid = True
            signature_valid = True  # Placeholder - would implement actual signature verification
            dependencies_satisfied = True  # Placeholder - would check actual dependencies
            security_check_passed = True  # Placeholder - would implement security scanning
            
            is_valid = (
                structure_valid and 
                signature_valid and 
                dependencies_satisfied and 
                security_check_passed and
                len(errors) == 0
            )
            
            return PluginValidationResult(
                is_valid=is_valid,
                structure_valid=structure_valid,
                signature_valid=signature_valid,
                dependencies_satisfied=dependencies_satisfied,
                security_check_passed=security_check_passed,
                validation_errors=errors,
                validation_warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Plugin validation error: {str(e)}")
            return PluginValidationResult(
                is_valid=False,
                structure_valid=False,
                signature_valid=False,
                dependencies_satisfied=False,
                security_check_passed=False,
                validation_errors=errors,
                validation_warnings=warnings
            )
    
    def _detect_package_managers(self) -> List[str]:
        """
        Detect available package managers on the system.
        
        Returns:
            List[str]: List of detected package manager names
        """
        package_managers = []
        
        # Common package managers to check
        managers_to_check = {
            "npm": ["npm", "--version"],
            "pip": ["pip", "--version"],
            "pip3": ["pip3", "--version"],
            "conda": ["conda", "--version"],
            "yarn": ["yarn", "--version"],
            "pipenv": ["pipenv", "--version"],
            "poetry": ["poetry", "--version"],
        }
        
        for manager_name, check_command in managers_to_check.items():
            try:
                result = subprocess.run(
                    check_command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    package_managers.append(manager_name)
                    
            except Exception:
                continue
        
        return package_managers
    
    def clear_integration_cache(self) -> None:
        """Clear integration-related caches."""
        self._platform_cache.clear()
        self._storage_analysis_cache.clear()
        self._package_manager_cache.clear()
        self._logger.info("Integration cache cleared")
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            "platform_cache_entries": len(self._platform_cache),
            "registered_plugins": len(self._plugin_registry),
            "storage_cache_entries": len(self._storage_analysis_cache),
            "package_manager_cache_entries": len(self._package_manager_cache),
            "last_platform_detection": self._last_platform_detection.isoformat() if self._last_platform_detection else None,
        }
    
    def get_plugin_registry(self) -> Dict[str, Dict[str, Any]]:
        """Get plugin registry information."""
        return {
            plugin_id: {
                "name": plugin.name,
                "version": plugin.version,
                "author": plugin.author,
                "capabilities": plugin.capabilities,
                "file_path": plugin.file_path,
            }
            for plugin_id, plugin in self._plugin_registry.items()
        }