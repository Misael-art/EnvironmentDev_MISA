"""
Interfaces for platform integration and plugin management components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from ..core.base import SystemComponentBase, OperationResult


class PlatformType(Enum):
    """Types of platforms supported."""
    WINDOWS = "windows"
    STEAM_DECK = "steam_deck"
    GENERIC_LINUX = "generic_linux"


class PluginStatus(Enum):
    """Status of plugin operations."""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"


class IntegrationLevel(Enum):
    """Levels of platform integration."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


@dataclass
class PlatformInfo:
    """Information about the current platform."""
    platform_type: PlatformType
    version: str
    architecture: str
    capabilities: List[str]
    limitations: List[str]
    detection_confidence: float


@dataclass
class SteamDeckProfile:
    """Steam Deck specific configuration profile."""
    hardware_detected: bool
    detection_method: str
    controller_configuration: Dict[str, Any]
    power_optimization: Dict[str, Any]
    touchscreen_configuration: Dict[str, Any]
    glossi_integration: Dict[str, Any]
    steam_cloud_sync: Dict[str, Any]
    fallback_applied: bool


@dataclass
class PluginInfo:
    """Information about a plugin."""
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    capabilities: List[str]
    dependencies: List[str]
    file_path: str
    digital_signature: Optional[str]
    load_priority: int


@dataclass
class PluginValidationResult:
    """Result of plugin validation."""
    is_valid: bool
    structure_valid: bool
    signature_valid: bool
    dependencies_satisfied: bool
    security_check_passed: bool
    validation_errors: List[str]
    validation_warnings: List[str]


@dataclass
class PluginConflict:
    """Information about plugin conflicts."""
    conflict_id: str
    conflicting_plugins: List[str]
    conflict_type: str
    description: str
    resolution_suggestions: List[str]
    severity: str


@dataclass
class RuntimeAdditionRequest:
    """Request to add a new runtime via plugin."""
    runtime_name: str
    runtime_version: str
    detection_methods: List[str]
    installation_methods: List[str]
    validation_commands: List[str]
    plugin_id: str


class PlatformIntegrationInterface(SystemComponentBase, ABC):
    """
    Interface for platform-specific integration operations.
    
    Defines the contract for detecting platforms, applying
    optimizations, and managing platform-specific features.
    """
    
    @abstractmethod
    def detect_platform(self) -> PlatformInfo:
        """
        Detect current platform and capabilities.
        
        Returns:
            PlatformInfo: Information about detected platform
        """
        pass
    
    @abstractmethod
    def apply_platform_optimizations(
        self, 
        platform_info: PlatformInfo
    ) -> OperationResult:
        """
        Apply platform-specific optimizations.
        
        Args:
            platform_info: Platform information
            
        Returns:
            OperationResult: Result of optimization application
        """
        pass
    
    @abstractmethod
    def configure_platform_specific_settings(
        self, 
        settings: Dict[str, Any]
    ) -> OperationResult:
        """
        Configure platform-specific settings.
        
        Args:
            settings: Platform-specific settings to configure
            
        Returns:
            OperationResult: Configuration result
        """
        pass
    
    @abstractmethod
    def validate_platform_compatibility(
        self, 
        component: str
    ) -> OperationResult:
        """
        Validate component compatibility with current platform.
        
        Args:
            component: Component name to validate
            
        Returns:
            OperationResult: Compatibility validation result
        """
        pass


class SteamDeckIntegrationInterface(SystemComponentBase, ABC):
    """
    Interface for Steam Deck specific integration operations.
    
    Defines the contract for Steam Deck hardware detection,
    optimizations, and Steam ecosystem integration.
    """
    
    @abstractmethod
    def detect_steam_deck_via_dmi_smbios(self) -> OperationResult:
        """
        Detect Steam Deck hardware via DMI/SMBIOS.
        
        Returns:
            OperationResult: Detection result with hardware information
        """
        pass
    
    @abstractmethod
    def apply_controller_specific_configurations(self) -> OperationResult:
        """
        Apply controller-specific configurations.
        
        Returns:
            OperationResult: Controller configuration result
        """
        pass
    
    @abstractmethod
    def optimize_power_profiles(self) -> OperationResult:
        """
        Optimize power profiles for battery and performance.
        
        Returns:
            OperationResult: Power optimization result
        """
        pass
    
    @abstractmethod
    def configure_touchscreen_drivers(self) -> OperationResult:
        """
        Configure touchscreen drivers and calibration.
        
        Returns:
            OperationResult: Touchscreen configuration result
        """
        pass
    
    @abstractmethod
    def integrate_with_glossi(self) -> OperationResult:
        """
        Integrate with GlosSI for non-Steam app execution.
        
        Returns:
            OperationResult: GlosSI integration result
        """
        pass
    
    @abstractmethod
    def synchronize_via_steam_cloud(self) -> OperationResult:
        """
        Synchronize configurations via Steam Cloud.
        
        Returns:
            OperationResult: Steam Cloud synchronization result
        """
        pass
    
    @abstractmethod
    def implement_fallback_detection(self) -> OperationResult:
        """
        Implement fallback detection using Steam client.
        
        Returns:
            OperationResult: Fallback detection result
        """
        pass
    
    @abstractmethod
    def create_steam_deck_profile(self) -> SteamDeckProfile:
        """
        Create comprehensive Steam Deck profile.
        
        Returns:
            SteamDeckProfile: Complete Steam Deck configuration profile
        """
        pass


class PluginManagerInterface(SystemComponentBase, ABC):
    """
    Interface for plugin system management operations.
    
    Defines the contract for loading, validating, and managing
    plugins with security and conflict detection.
    """
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> OperationResult:
        """
        Load plugin from specified path.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            OperationResult: Plugin loading result
        """
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_id: str) -> OperationResult:
        """
        Unload plugin by ID.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            OperationResult: Plugin unloading result
        """
        pass
    
    @abstractmethod
    def validate_plugin_structure(self, plugin_path: str) -> PluginValidationResult:
        """
        Validate plugin structure and dependencies.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            PluginValidationResult: Validation results
        """
        pass
    
    @abstractmethod
    def verify_digital_signature(self, plugin_path: str) -> bool:
        """
        Verify digital signature of plugin.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def detect_plugin_conflicts(self, plugins: List[PluginInfo]) -> List[PluginConflict]:
        """
        Detect conflicts between plugins.
        
        Args:
            plugins: List of plugin information
            
        Returns:
            List[PluginConflict]: List of detected conflicts
        """
        pass
    
    @abstractmethod
    def manage_plugin_versions(self, plugin_id: str) -> OperationResult:
        """
        Manage plugin versions and updates.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            OperationResult: Version management result
        """
        pass
    
    @abstractmethod
    def enable_runtime_addition_via_plugins(
        self, 
        request: RuntimeAdditionRequest
    ) -> OperationResult:
        """
        Enable addition of new runtimes via plugins.
        
        Args:
            request: Runtime addition request
            
        Returns:
            OperationResult: Runtime addition result
        """
        pass
    
    @abstractmethod
    def provide_secure_api_access(self, plugin_id: str) -> Dict[str, Callable]:
        """
        Provide secure API access for plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Dict[str, Callable]: Dictionary of available API functions
        """
        pass
    
    @abstractmethod
    def implement_plugin_sandboxing(self, plugin_id: str) -> OperationResult:
        """
        Implement sandboxing for plugin execution.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            OperationResult: Sandboxing implementation result
        """
        pass


class StorageManagerInterface(SystemComponentBase, ABC):
    """
    Interface for intelligent storage management operations.
    
    Defines the contract for storage analysis, distribution,
    and compression management.
    """
    
    @abstractmethod
    def calculate_space_requirements(self, components: List[str]) -> Dict[str, int]:
        """
        Calculate space requirements for components.
        
        Args:
            components: List of component names
            
        Returns:
            Dict[str, int]: Mapping of components to space requirements in bytes
        """
        pass
    
    @abstractmethod
    def analyze_available_space(self) -> Dict[str, int]:
        """
        Analyze available space across drives.
        
        Returns:
            Dict[str, int]: Mapping of drive paths to available space in bytes
        """
        pass
    
    @abstractmethod
    def enable_selective_installation(
        self, 
        components: List[str],
        available_space: int
    ) -> List[str]:
        """
        Enable selective installation based on available space.
        
        Args:
            components: List of components to consider
            available_space: Available space in bytes
            
        Returns:
            List[str]: List of components that can be installed
        """
        pass
    
    @abstractmethod
    def suggest_components_for_removal(self) -> List[str]:
        """
        Suggest components for removal when storage is low.
        
        Returns:
            List[str]: List of components suggested for removal
        """
        pass
    
    @abstractmethod
    def distribute_across_drives(
        self, 
        components: List[str],
        drives: List[str]
    ) -> Dict[str, List[str]]:
        """
        Intelligently distribute components across multiple drives.
        
        Args:
            components: List of components to distribute
            drives: List of available drive paths
            
        Returns:
            Dict[str, List[str]]: Mapping of drives to components
        """
        pass
    
    @abstractmethod
    def implement_intelligent_compression(self) -> OperationResult:
        """
        Implement intelligent compression for rarely accessed components.
        
        Returns:
            OperationResult: Compression implementation result
        """
        pass
    
    @abstractmethod
    def cleanup_temporary_files(self) -> OperationResult:
        """
        Automatically cleanup temporary files after installation.
        
        Returns:
            OperationResult: Cleanup operation result
        """
        pass


class PackageManagerIntegrationInterface(SystemComponentBase, ABC):
    """
    Interface for package manager integration operations.
    
    Defines the contract for integrating with various package
    managers for dependency resolution.
    """
    
    @abstractmethod
    def detect_package_managers(self) -> List[str]:
        """
        Detect available package managers.
        
        Returns:
            List[str]: List of detected package manager names
        """
        pass
    
    @abstractmethod
    def integrate_with_npm(self) -> OperationResult:
        """
        Integrate with npm package manager.
        
        Returns:
            OperationResult: npm integration result
        """
        pass
    
    @abstractmethod
    def integrate_with_pip(self) -> OperationResult:
        """
        Integrate with pip package manager.
        
        Returns:
            OperationResult: pip integration result
        """
        pass
    
    @abstractmethod
    def integrate_with_conda(self) -> OperationResult:
        """
        Integrate with conda package manager.
        
        Returns:
            OperationResult: conda integration result
        """
        pass
    
    @abstractmethod
    def resolve_dependencies_via_package_managers(
        self, 
        dependencies: List[str]
    ) -> OperationResult:
        """
        Resolve dependencies using integrated package managers.
        
        Args:
            dependencies: List of dependencies to resolve
            
        Returns:
            OperationResult: Dependency resolution result
        """
        pass