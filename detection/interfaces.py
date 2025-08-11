"""
Interfaces for unified detection and runtime detection components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..core.base import SystemComponentBase, OperationResult


class DetectionMethod(Enum):
    """Methods used for detection."""
    REGISTRY = "registry"
    FILESYSTEM = "filesystem"
    ENVIRONMENT_VARIABLES = "environment_variables"
    COMMAND_LINE = "command_line"
    DMI_SMBIOS = "dmi_smbios"
    STEAM_CLIENT = "steam_client"
    MANUAL_CONFIG = "manual_config"


class DetectionConfidence(Enum):
    """Confidence levels for detection results."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    """Base result for detection operations."""
    detected: bool
    confidence: DetectionConfidence
    method: DetectionMethod
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class RegistryApp:
    """Represents an application detected via Windows Registry."""
    name: str
    version: str
    publisher: str
    install_location: str
    uninstall_string: str
    registry_key: str
    detection_confidence: DetectionConfidence


@dataclass
class PortableApp:
    """Represents a portable application detected via filesystem."""
    name: str
    version: Optional[str]
    executable_path: str
    directory: str
    detection_method: str
    confidence: DetectionConfidence


@dataclass
class RuntimeDetectionResult:
    """Result of essential runtime detection."""
    runtime_name: str
    detected: bool
    version: Optional[str]
    install_path: Optional[str]
    environment_variables: Dict[str, str]
    validation_commands: List[str]
    validation_results: Dict[str, bool]
    detection_method: DetectionMethod
    confidence: DetectionConfidence


@dataclass
class PackageManager:
    """Represents a detected package manager."""
    name: str
    version: str
    executable_path: str
    global_packages: List[str]
    virtual_environments: List[str]
    configuration_files: List[str]


@dataclass
class SteamDeckDetectionResult:
    """Result of Steam Deck hardware detection."""
    is_steam_deck: bool
    detection_method: DetectionMethod
    hardware_info: Dict[str, Any]
    steam_client_detected: bool
    controller_detected: bool
    fallback_applied: bool
    confidence: DetectionConfidence


@dataclass
class HierarchicalResult:
    """Result with hierarchical prioritization."""
    primary_detections: List[DetectionResult]
    secondary_detections: List[DetectionResult]
    priority_scores: Dict[str, float]
    selection_rationale: str


@dataclass
class ComprehensiveDetectionReport:
    """Comprehensive detection report."""
    report_id: str
    generation_timestamp: datetime
    registry_applications: List[RegistryApp]
    portable_applications: List[PortableApp]
    essential_runtimes: List[RuntimeDetectionResult]
    package_managers: List[PackageManager]
    steam_deck_info: SteamDeckDetectionResult
    hierarchical_results: HierarchicalResult
    detection_summary: Dict[str, Any]


class DetectionEngineInterface(SystemComponentBase, ABC):
    """
    Interface for unified detection operations.
    
    Defines the contract for detecting applications, runtimes,
    and system components across different detection methods.
    """
    
    @abstractmethod
    def detect_all_applications(self) -> DetectionResult:
        """
        Detect all applications using unified detection methods.
        
        Returns:
            DetectionResult: Combined results from all detection methods
        """
        pass
    
    @abstractmethod
    def scan_registry_installations(self) -> List[RegistryApp]:
        """
        Scan Windows Registry for installed applications.
        
        Returns:
            List[RegistryApp]: List of applications found in registry
        """
        pass
    
    @abstractmethod
    def detect_portable_applications(self) -> List[PortableApp]:
        """
        Detect portable applications via filesystem scanning.
        
        Returns:
            List[PortableApp]: List of detected portable applications
        """
        pass
    
    @abstractmethod
    def detect_essential_runtimes(self) -> List[RuntimeDetectionResult]:
        """
        Detect all essential runtimes (Git, .NET, Java, etc.).
        
        Returns:
            List[RuntimeDetectionResult]: Detection results for essential runtimes
        """
        pass
    
    @abstractmethod
    def detect_package_managers(self) -> List[PackageManager]:
        """
        Detect package managers (npm, pip, conda, etc.).
        
        Returns:
            List[PackageManager]: List of detected package managers
        """
        pass
    
    @abstractmethod
    def detect_steam_deck_hardware(self) -> SteamDeckDetectionResult:
        """
        Detect Steam Deck hardware and configuration.
        
        Returns:
            SteamDeckDetectionResult: Steam Deck detection results
        """
        pass
    
    @abstractmethod
    def apply_hierarchical_detection(self) -> HierarchicalResult:
        """
        Apply hierarchical prioritization to detection results.
        
        Returns:
            HierarchicalResult: Prioritized detection results
        """
        pass
    
    @abstractmethod
    def generate_comprehensive_report(self) -> ComprehensiveDetectionReport:
        """
        Generate comprehensive detection report.
        
        Returns:
            ComprehensiveDetectionReport: Complete detection report
        """
        pass


class RuntimeDetectorInterface(SystemComponentBase, ABC):
    """
    Interface for runtime-specific detection operations.
    
    Defines the contract for detecting specific runtimes
    with detailed version and configuration information.
    """
    
    @abstractmethod
    def detect_git_2_47_1(self) -> RuntimeDetectionResult:
        """
        Detect Git 2.47.1 installation.
        
        Returns:
            RuntimeDetectionResult: Git detection results
        """
        pass
    
    @abstractmethod
    def detect_dotnet_sdk_8_0(self) -> RuntimeDetectionResult:
        """
        Detect .NET SDK 8.0 installation.
        
        Returns:
            RuntimeDetectionResult: .NET SDK detection results
        """
        pass
    
    @abstractmethod
    def detect_java_jdk_21(self) -> RuntimeDetectionResult:
        """
        Detect Java JDK 21 installation.
        
        Returns:
            RuntimeDetectionResult: Java JDK detection results
        """
        pass
    
    @abstractmethod
    def detect_vcpp_redistributables(self) -> RuntimeDetectionResult:
        """
        Detect Visual C++ Redistributables.
        
        Returns:
            RuntimeDetectionResult: Visual C++ Redistributables detection results
        """
        pass
    
    @abstractmethod
    def detect_anaconda3(self) -> RuntimeDetectionResult:
        """
        Detect Anaconda3 installation.
        
        Returns:
            RuntimeDetectionResult: Anaconda3 detection results
        """
        pass
    
    @abstractmethod
    def detect_dotnet_desktop_runtime(self) -> RuntimeDetectionResult:
        """
        Detect .NET Desktop Runtime 8.0/9.0.
        
        Returns:
            RuntimeDetectionResult: .NET Desktop Runtime detection results
        """
        pass
    
    @abstractmethod
    def detect_powershell_7(self) -> RuntimeDetectionResult:
        """
        Detect PowerShell 7 installation.
        
        Returns:
            RuntimeDetectionResult: PowerShell 7 detection results
        """
        pass
    
    @abstractmethod
    def detect_updated_nodejs_python(self) -> RuntimeDetectionResult:
        """
        Detect updated Node.js and Python installations.
        
        Returns:
            RuntimeDetectionResult: Node.js/Python detection results
        """
        pass
    
    @abstractmethod
    def validate_runtime_installation(
        self, 
        runtime_name: str, 
        expected_version: Optional[str] = None
    ) -> OperationResult:
        """
        Validate runtime installation with specific commands.
        
        Args:
            runtime_name: Name of runtime to validate
            expected_version: Expected version (optional)
            
        Returns:
            OperationResult: Validation results
        """
        pass


class HierarchicalDetectionInterface(SystemComponentBase, ABC):
    """
    Interface for hierarchical detection prioritization.
    
    Defines the contract for prioritizing detection results
    based on installation status, compatibility, and location.
    """
    
    @abstractmethod
    def prioritize_installed_applications(
        self, 
        detections: List[DetectionResult]
    ) -> List[DetectionResult]:
        """
        Prioritize already installed applications.
        
        Args:
            detections: List of detection results to prioritize
            
        Returns:
            List[DetectionResult]: Prioritized detection results
        """
        pass
    
    @abstractmethod
    def prioritize_compatible_versions(
        self, 
        detections: List[DetectionResult],
        compatibility_matrix: Dict[str, List[str]]
    ) -> List[DetectionResult]:
        """
        Prioritize compatible versions.
        
        Args:
            detections: List of detection results
            compatibility_matrix: Version compatibility information
            
        Returns:
            List[DetectionResult]: Prioritized by compatibility
        """
        pass
    
    @abstractmethod
    def prioritize_standard_locations(
        self, 
        detections: List[DetectionResult]
    ) -> List[DetectionResult]:
        """
        Prioritize applications in standard system locations.
        
        Args:
            detections: List of detection results
            
        Returns:
            List[DetectionResult]: Prioritized by location
        """
        pass
    
    @abstractmethod
    def prioritize_custom_configurations(
        self, 
        detections: List[DetectionResult],
        user_preferences: Dict[str, Any]
    ) -> List[DetectionResult]:
        """
        Prioritize based on custom user configurations.
        
        Args:
            detections: List of detection results
            user_preferences: User preference settings
            
        Returns:
            List[DetectionResult]: Prioritized by user preferences
        """
        pass