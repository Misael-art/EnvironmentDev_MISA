"""
Core exception hierarchy for Environment Dev Deep Evaluation system.

This module defines all exceptions used throughout the system, organized
in a hierarchical structure for proper error handling and categorization.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class EnvironmentDevDeepEvaluationError(Exception):
    """
    Base exception for Environment Dev Deep Evaluation system.
    
    All other exceptions in the system inherit from this base class,
    providing a common interface for error handling and logging.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }


class ArchitectureAnalysisError(EnvironmentDevDeepEvaluationError):
    """
    Errors during architecture analysis operations.
    
    Raised when issues occur during:
    - Architecture mapping and comparison
    - Gap analysis and documentation
    - Requirements consistency validation
    """
    pass


class UnifiedDetectionError(EnvironmentDevDeepEvaluationError):
    """
    Errors during unified detection operations.
    
    Raised when issues occur during:
    - Application and runtime detection
    - Registry scanning
    - Portable application detection
    - Hierarchical detection prioritization
    """
    pass


class DependencyValidationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during dependency validation operations.
    
    Raised when issues occur during:
    - Dependency graph creation and analysis
    - Conflict detection and resolution
    - Contextual compatibility validation
    """
    pass


class RobustDownloadError(EnvironmentDevDeepEvaluationError):
    """
    Errors during robust download operations.
    
    Raised when issues occur during:
    - Secure download with hash verification
    - Mirror fallback and retry mechanisms
    - Parallel download coordination
    """
    pass


class AdvancedInstallationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during advanced installation operations.
    
    Raised when issues occur during:
    - Installation with automatic rollback
    - Environment variable configuration
    - Runtime-specific installation handling
    """
    pass


class SteamDeckIntegrationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during Steam Deck integration operations.
    
    Raised when issues occur during:
    - Steam Deck hardware detection
    - Controller and power optimizations
    - Steam ecosystem integration
    """
    pass


class IntelligentStorageError(EnvironmentDevDeepEvaluationError):
    """
    Errors during intelligent storage management operations.
    
    Raised when issues occur during:
    - Storage analysis and planning
    - Intelligent distribution and cleanup
    - Compression system operations
    """
    pass


class PluginSystemError(EnvironmentDevDeepEvaluationError):
    """
    Errors during plugin system operations.
    
    Raised when issues occur during:
    - Plugin loading and validation
    - Plugin conflict detection
    - Plugin integration mechanisms
    """
    pass


# Specific sub-exceptions for more granular error handling

class ConfigurationError(EnvironmentDevDeepEvaluationError):
    """Errors related to system configuration management."""
    pass


class ValidationError(EnvironmentDevDeepEvaluationError):
    """Errors related to data validation and verification."""
    pass


class SecurityError(EnvironmentDevDeepEvaluationError):
    """Errors related to security validation and verification."""
    pass


class PermissionError(EnvironmentDevDeepEvaluationError):
    """Errors related to insufficient permissions or privilege escalation."""
    pass


class NetworkError(EnvironmentDevDeepEvaluationError):
    """Errors related to network operations and connectivity."""
    pass


class FileSystemError(EnvironmentDevDeepEvaluationError):
    """Errors related to file system operations."""
    pass


class IntegrityError(EnvironmentDevDeepEvaluationError):
    """Errors related to data integrity and verification."""
    pass


class ComponentError(EnvironmentDevDeepEvaluationError):
    """Errors related to component operations and management."""
    pass


class DetectionError(EnvironmentDevDeepEvaluationError):
    """Errors related to component detection and discovery."""
    pass


class InstallationError(EnvironmentDevDeepEvaluationError):
    """Errors related to component installation and setup."""
    pass


class DownloadError(EnvironmentDevDeepEvaluationError):
    """Errors related to file download operations."""
    pass


class HashVerificationError(EnvironmentDevDeepEvaluationError):
    """Errors related to hash verification and integrity checks."""
    pass


class PluginError(EnvironmentDevDeepEvaluationError):
    """Errors related to plugin operations and management."""
    pass


class StorageError(EnvironmentDevDeepEvaluationError):
    """Errors related to storage operations and management."""
    pass


class AnalysisError(EnvironmentDevDeepEvaluationError):
    """Errors related to analysis operations and processing."""
    pass


class RecoveryError(EnvironmentDevDeepEvaluationError):
    """Errors related to error recovery operations."""
    pass


class TimeoutError(EnvironmentDevDeepEvaluationError):
    """Errors related to operation timeouts."""
    pass


class ResourceError(EnvironmentDevDeepEvaluationError):
    """Errors related to resource allocation and management."""
    pass


class CompatibilityError(EnvironmentDevDeepEvaluationError):
    """Errors related to compatibility checks and validation."""
    pass


class UserInputError(EnvironmentDevDeepEvaluationError):
    """Errors related to user input validation and processing."""
    pass


class ExternalServiceError(EnvironmentDevDeepEvaluationError):
    """Errors related to external service interactions."""
    pass


# Exception mapping for error categorization
EXCEPTION_CATEGORY_MAP = {
    ConfigurationError: "configuration",
    ValidationError: "validation",
    SecurityError: "system",
    PermissionError: "permission",
    NetworkError: "network",
    FileSystemError: "file_system",
    IntegrityError: "validation",
    ComponentError: "system",
    DetectionError: "detection",
    InstallationError: "installation",
    DownloadError: "network",
    HashVerificationError: "validation",
    PluginError: "plugin",
    StorageError: "file_system",
    AnalysisError: "system",
    RecoveryError: "system",
    TimeoutError: "system",
    ResourceError: "system",
    CompatibilityError: "validation",
    UserInputError: "user_input",
    ExternalServiceError: "external_service",
    ArchitectureAnalysisError: "system",
    UnifiedDetectionError: "detection",
    DependencyValidationError: "validation",
    RobustDownloadError: "network",
    AdvancedInstallationError: "installation",
    SteamDeckIntegrationError: "system",
    IntelligentStorageError: "file_system",
    PluginSystemError: "plugin"
}


def get_exception_category(exception: Exception) -> str:
    """Get the category for an exception type.
    
    Args:
        exception: Exception instance
        
    Returns:
        Category string for the exception
    """
    exception_type = type(exception)
    return EXCEPTION_CATEGORY_MAP.get(exception_type, "unknown")


def create_context_exception(
    base_exception: Exception,
    component: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> EnvironmentDevDeepEvaluationError:
    """Create a context-aware exception from a base exception.
    
    Args:
        base_exception: Original exception
        component: Component name where error occurred
        operation: Operation being performed
        context: Additional context information
        
    Returns:
        Enhanced exception with context
    """
    enhanced_context = {
        "component": component,
        "operation": operation,
        "original_exception": str(base_exception),
        "original_type": type(base_exception).__name__
    }
    
    if context:
        enhanced_context.update(context)
    
    message = f"Error in {component}.{operation}: {str(base_exception)}"
    
    return EnvironmentDevDeepEvaluationError(
        message=message,
        context=enhanced_context,
        cause=base_exception
    )