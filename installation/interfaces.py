"""
Interfaces for download management and installation components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from ..core.base import SystemComponentBase, OperationResult


class DownloadStatus(Enum):
    """Status of download operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"


class InstallationStatus(Enum):
    """Status of installation operations."""
    NOT_STARTED = "not_started"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    CONFIGURING = "configuring"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class MirrorHealth(Enum):
    """Health status of download mirrors."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DownloadRequest:
    """Request for downloading a component."""
    url: str
    expected_sha256: str
    destination_path: str
    component_name: str
    mirrors: List[str]
    timeout: int = 300
    max_retries: int = 3
    priority: int = 0


@dataclass
class DownloadResult:
    """Result of download operation."""
    success: bool
    file_path: str
    actual_sha256: str
    download_time: float
    bytes_downloaded: int
    mirror_used: str
    retries_used: int
    error_message: Optional[str] = None


@dataclass
class ParallelDownloadResult:
    """Result of parallel download operations."""
    total_downloads: int
    successful_downloads: int
    failed_downloads: int
    total_bytes: int
    total_time: float
    download_results: List[DownloadResult]
    integrity_summary: 'IntegritySummary'


@dataclass
class IntegritySummary:
    """Summary of download integrity verification."""
    total_files: int
    verified_files: int
    failed_verifications: int
    integrity_score: float
    failed_files: List[str]
    verification_details: Dict[str, Any]


@dataclass
class MirrorStatus:
    """Status information for a download mirror."""
    url: str
    health: MirrorHealth
    response_time: float
    success_rate: float
    last_check: datetime
    error_count: int


@dataclass
class InstallationRequest:
    """Request for installing a component."""
    component_name: str
    version: str
    installation_path: str
    download_urls: List[str]
    expected_hash: str
    environment_variables: Dict[str, str]
    validation_commands: List[str]
    dependencies: List[str]
    rollback_enabled: bool = True


@dataclass
class InstallationResult:
    """Result of installation operation."""
    success: bool
    component_name: str
    version: str
    installation_path: str
    installation_time: float
    environment_variables_set: Dict[str, str]
    validation_results: Dict[str, bool]
    rollback_info: Optional['RollbackInfo']
    error_message: Optional[str] = None


@dataclass
class RollbackInfo:
    """Information for rolling back an installation."""
    rollback_id: str
    component_name: str
    backup_paths: List[str]
    original_environment_variables: Dict[str, str]
    rollback_commands: List[str]
    created_timestamp: datetime


@dataclass
class PreparationResult:
    """Result of installation preparation."""
    directories_created: List[str]
    backups_created: List[str]
    privileges_requested: List[str]
    environment_prepared: bool
    preparation_time: float


@dataclass
class ValidationResult:
    """Result of post-installation validation."""
    component_name: str
    validation_passed: bool
    command_results: Dict[str, bool]
    version_detected: Optional[str]
    configuration_valid: bool
    error_details: List[str]


class DownloadManagerInterface(SystemComponentBase, ABC):
    """
    Interface for robust download management operations.
    
    Defines the contract for secure downloads with hash verification,
    mirror fallback, and parallel download capabilities.
    """
    
    @abstractmethod
    def download_with_mandatory_hash_verification(
        self, 
        url: str, 
        expected_sha256: str,
        destination: str
    ) -> DownloadResult:
        """
        Download file with mandatory SHA256 hash verification.
        
        Args:
            url: URL to download from
            expected_sha256: Expected SHA256 hash
            destination: Destination file path
            
        Returns:
            DownloadResult: Result of download operation
        """
        pass
    
    @abstractmethod
    def implement_intelligent_mirror_system(
        self, 
        mirrors: List[str]
    ) -> List[MirrorStatus]:
        """
        Implement intelligent mirror selection and health monitoring.
        
        Args:
            mirrors: List of mirror URLs
            
        Returns:
            List[MirrorStatus]: Status of all mirrors
        """
        pass
    
    @abstractmethod
    def execute_configurable_retries(
        self, 
        download_request: DownloadRequest
    ) -> DownloadResult:
        """
        Execute download with configurable retry mechanism.
        
        Args:
            download_request: Download request with retry configuration
            
        Returns:
            DownloadResult: Final result after retries
        """
        pass
    
    @abstractmethod
    def enable_parallel_downloads(
        self, 
        download_requests: List[DownloadRequest]
    ) -> ParallelDownloadResult:
        """
        Enable parallel downloads for multiple components.
        
        Args:
            download_requests: List of download requests
            
        Returns:
            ParallelDownloadResult: Results of parallel downloads
        """
        pass
    
    @abstractmethod
    def generate_integrity_summary(
        self, 
        download_results: List[DownloadResult]
    ) -> IntegritySummary:
        """
        Generate integrity summary before installation.
        
        Args:
            download_results: List of download results to summarize
            
        Returns:
            IntegritySummary: Comprehensive integrity summary
        """
        pass
    
    @abstractmethod
    def implement_exponential_backoff(self, attempt: int) -> int:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            int: Delay in seconds
        """
        pass


class InstallationManagerInterface(SystemComponentBase, ABC):
    """
    Interface for advanced installation management operations.
    
    Defines the contract for installations with automatic rollback,
    environment configuration, and runtime-specific handling.
    """
    
    @abstractmethod
    def install_with_automatic_rollback(
        self, 
        installation_request: InstallationRequest
    ) -> InstallationResult:
        """
        Install component with automatic rollback capability.
        
        Args:
            installation_request: Installation request details
            
        Returns:
            InstallationResult: Result of installation operation
        """
        pass
    
    @abstractmethod
    def configure_persistent_environment_variables(
        self, 
        variables: Dict[str, str]
    ) -> OperationResult:
        """
        Configure persistent environment variables.
        
        Args:
            variables: Dictionary of environment variables to set
            
        Returns:
            OperationResult: Result of configuration operation
        """
        pass
    
    @abstractmethod
    def validate_installation_with_specific_commands(
        self, 
        component: str,
        validation_commands: List[str]
    ) -> ValidationResult:
        """
        Validate installation using specific commands.
        
        Args:
            component: Component name to validate
            validation_commands: List of commands to execute for validation
            
        Returns:
            ValidationResult: Validation results
        """
        pass
    
    @abstractmethod
    def generate_detailed_success_failure_report(
        self, 
        installation_results: List[InstallationResult]
    ) -> OperationResult:
        """
        Generate detailed success/failure report.
        
        Args:
            installation_results: List of installation results
            
        Returns:
            OperationResult: Report generation result
        """
        pass
    
    @abstractmethod
    def handle_runtime_specific_cases(
        self, 
        runtime: str,
        installation_request: InstallationRequest
    ) -> InstallationResult:
        """
        Handle runtime-specific installation cases.
        
        Args:
            runtime: Runtime name (Git, .NET, Java, etc.)
            installation_request: Installation request
            
        Returns:
            InstallationResult: Runtime-specific installation result
        """
        pass
    
    @abstractmethod
    def implement_intelligent_preparation(
        self, 
        components: List[str]
    ) -> PreparationResult:
        """
        Implement intelligent preparation for installations.
        
        Args:
            components: List of components to prepare for
            
        Returns:
            PreparationResult: Preparation results
        """
        pass


class IntelligentPreparationInterface(SystemComponentBase, ABC):
    """
    Interface for intelligent preparation operations.
    
    Defines the contract for preparing the system for installations
    with directory creation, backups, and privilege management.
    """
    
    @abstractmethod
    def create_necessary_directory_structure(
        self, 
        component: str
    ) -> OperationResult:
        """
        Create necessary directory structure for component.
        
        Args:
            component: Component name
            
        Returns:
            OperationResult: Directory creation result
        """
        pass
    
    @abstractmethod
    def backup_existing_configurations(
        self, 
        paths: List[str]
    ) -> OperationResult:
        """
        Backup existing configurations before installation.
        
        Args:
            paths: List of paths to backup
            
        Returns:
            OperationResult: Backup operation result
        """
        pass
    
    @abstractmethod
    def request_privileges_only_when_necessary(
        self, 
        operation: str
    ) -> OperationResult:
        """
        Request privileges only when necessary for operation.
        
        Args:
            operation: Description of operation requiring privileges
            
        Returns:
            OperationResult: Privilege request result
        """
        pass
    
    @abstractmethod
    def configure_critical_path_variables(
        self, 
        component: str
    ) -> OperationResult:
        """
        Configure critical PATH and environment variables.
        
        Args:
            component: Component name
            
        Returns:
            OperationResult: Configuration result
        """
        pass


class RollbackManagerInterface(SystemComponentBase, ABC):
    """
    Interface for rollback management operations.
    
    Defines the contract for managing installation rollbacks
    and recovery operations.
    """
    
    @abstractmethod
    def create_rollback_point(
        self, 
        component: str,
        installation_path: str
    ) -> RollbackInfo:
        """
        Create rollback point before installation.
        
        Args:
            component: Component name
            installation_path: Path where component will be installed
            
        Returns:
            RollbackInfo: Rollback information
        """
        pass
    
    @abstractmethod
    def execute_rollback(self, rollback_info: RollbackInfo) -> OperationResult:
        """
        Execute rollback using rollback information.
        
        Args:
            rollback_info: Rollback information
            
        Returns:
            OperationResult: Rollback execution result
        """
        pass
    
    @abstractmethod
    def validate_rollback_integrity(
        self, 
        rollback_info: RollbackInfo
    ) -> OperationResult:
        """
        Validate integrity of rollback information.
        
        Args:
            rollback_info: Rollback information to validate
            
        Returns:
            OperationResult: Validation result
        """
        pass
    
    @abstractmethod
    def cleanup_rollback_data(
        self, 
        rollback_info: RollbackInfo
    ) -> OperationResult:
        """
        Cleanup rollback data after successful installation.
        
        Args:
            rollback_info: Rollback information to cleanup
            
        Returns:
            OperationResult: Cleanup result
        """
        pass