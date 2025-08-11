"""Tests for core.exceptions module."""

import pytest
from datetime import datetime
from unittest.mock import patch

from core.exceptions import (
    EnvironmentDevDeepEvaluationError,
    ArchitectureAnalysisError,
    UnifiedDetectionError,
    DependencyValidationError,
    RobustDownloadError,
    AdvancedInstallationError,
    SteamDeckIntegrationError,
    IntelligentStorageError,
    PluginSystemError,
    ConfigurationError,
    ValidationError,
    SecurityError,
    PermissionError,
    NetworkError,
    FileSystemError,
    IntegrityError,
    ComponentError,
    DetectionError,
    InstallationError,
    DownloadError,
    HashVerificationError,
    PluginError,
    StorageError,
    AnalysisError,
    RecoveryError,
    TimeoutError,
    ResourceError,
    CompatibilityError,
    UserInputError,
    ExternalServiceError,
    EXCEPTION_CATEGORY_MAP,
    get_exception_category,
    create_context_exception
)


class TestEnvironmentDevDeepEvaluationError:
    """Tests for base EnvironmentDevDeepEvaluationError class."""
    
    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = EnvironmentDevDeepEvaluationError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "EnvironmentDevDeepEvaluationError"
        assert error.context == {}
        assert error.cause is None
        assert isinstance(error.timestamp, datetime)
    
    def test_initialization_with_all_parameters(self):
        """Test exception initialization with all parameters."""
        context = {"component": "test_component", "operation": "test_op"}
        cause = ValueError("Original error")
        
        error = EnvironmentDevDeepEvaluationError(
            message="Test error",
            error_code="CUSTOM_ERROR",
            context=context,
            cause=cause
        )
        
        assert error.message == "Test error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.context == context
        assert error.cause == cause
    
    def test_to_dict_method(self):
        """Test conversion to dictionary."""
        context = {"user_id": "123", "action": "download"}
        cause = ConnectionError("Network issue")
        
        error = EnvironmentDevDeepEvaluationError(
            message="Download failed",
            error_code="DOWNLOAD_ERROR",
            context=context,
            cause=cause
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "EnvironmentDevDeepEvaluationError"
        assert error_dict["error_code"] == "DOWNLOAD_ERROR"
        assert error_dict["message"] == "Download failed"
        assert error_dict["context"] == context
        assert error_dict["cause"] == "Network issue"
        assert "timestamp" in error_dict
        
        # Verify timestamp is in ISO format
        datetime.fromisoformat(error_dict["timestamp"])
    
    def test_to_dict_without_cause(self):
        """Test to_dict method when no cause is provided."""
        error = EnvironmentDevDeepEvaluationError("Test error")
        error_dict = error.to_dict()
        
        assert error_dict["cause"] is None


class TestSpecificExceptions:
    """Tests for specific exception classes."""
    
    def test_architecture_analysis_error(self):
        """Test ArchitectureAnalysisError inheritance and functionality."""
        error = ArchitectureAnalysisError("Architecture mapping failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Architecture mapping failed"
        assert error.error_code == "ArchitectureAnalysisError"
    
    def test_unified_detection_error(self):
        """Test UnifiedDetectionError inheritance and functionality."""
        error = UnifiedDetectionError("Detection failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Detection failed"
        assert error.error_code == "UnifiedDetectionError"
    
    def test_dependency_validation_error(self):
        """Test DependencyValidationError inheritance and functionality."""
        error = DependencyValidationError("Dependency conflict detected")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Dependency conflict detected"
        assert error.error_code == "DependencyValidationError"
    
    def test_robust_download_error(self):
        """Test RobustDownloadError inheritance and functionality."""
        error = RobustDownloadError("Download verification failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Download verification failed"
        assert error.error_code == "RobustDownloadError"
    
    def test_advanced_installation_error(self):
        """Test AdvancedInstallationError inheritance and functionality."""
        error = AdvancedInstallationError("Installation rollback failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Installation rollback failed"
        assert error.error_code == "AdvancedInstallationError"
    
    def test_steam_deck_integration_error(self):
        """Test SteamDeckIntegrationError inheritance and functionality."""
        error = SteamDeckIntegrationError("Steam Deck detection failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Steam Deck detection failed"
        assert error.error_code == "SteamDeckIntegrationError"
    
    def test_intelligent_storage_error(self):
        """Test IntelligentStorageError inheritance and functionality."""
        error = IntelligentStorageError("Storage optimization failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Storage optimization failed"
        assert error.error_code == "IntelligentStorageError"
    
    def test_plugin_system_error(self):
        """Test PluginSystemError inheritance and functionality."""
        error = PluginSystemError("Plugin loading failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Plugin loading failed"
        assert error.error_code == "PluginSystemError"


class TestGranularExceptions:
    """Tests for granular exception classes."""
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Invalid configuration"
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Data validation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Data validation failed"
    
    def test_security_error(self):
        """Test SecurityError."""
        error = SecurityError("Security check failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Security check failed"
    
    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Insufficient permissions")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Insufficient permissions"
    
    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Network connection failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Network connection failed"
    
    def test_file_system_error(self):
        """Test FileSystemError."""
        error = FileSystemError("File operation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "File operation failed"
    
    def test_integrity_error(self):
        """Test IntegrityError."""
        error = IntegrityError("Data integrity check failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Data integrity check failed"
    
    def test_component_error(self):
        """Test ComponentError."""
        error = ComponentError("Component operation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Component operation failed"
    
    def test_detection_error(self):
        """Test DetectionError."""
        error = DetectionError("Component detection failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Component detection failed"
    
    def test_installation_error(self):
        """Test InstallationError."""
        error = InstallationError("Installation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Installation failed"
    
    def test_download_error(self):
        """Test DownloadError."""
        error = DownloadError("Download failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Download failed"
    
    def test_hash_verification_error(self):
        """Test HashVerificationError."""
        error = HashVerificationError("Hash verification failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Hash verification failed"
    
    def test_plugin_error(self):
        """Test PluginError."""
        error = PluginError("Plugin operation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Plugin operation failed"
    
    def test_storage_error(self):
        """Test StorageError."""
        error = StorageError("Storage operation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Storage operation failed"
    
    def test_analysis_error(self):
        """Test AnalysisError."""
        error = AnalysisError("Analysis failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Analysis failed"
    
    def test_recovery_error(self):
        """Test RecoveryError."""
        error = RecoveryError("Recovery operation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Recovery operation failed"
    
    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Operation timed out")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Operation timed out"
    
    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError("Resource allocation failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Resource allocation failed"
    
    def test_compatibility_error(self):
        """Test CompatibilityError."""
        error = CompatibilityError("Compatibility check failed")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Compatibility check failed"
    
    def test_user_input_error(self):
        """Test UserInputError."""
        error = UserInputError("Invalid user input")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "Invalid user input"
    
    def test_external_service_error(self):
        """Test ExternalServiceError."""
        error = ExternalServiceError("External service unavailable")
        
        assert isinstance(error, EnvironmentDevDeepEvaluationError)
        assert error.message == "External service unavailable"


class TestExceptionCategoryMap:
    """Tests for exception category mapping."""
    
    def test_exception_category_map_completeness(self):
        """Test that all exception types are mapped to categories."""
        expected_exceptions = [
            ConfigurationError, ValidationError, SecurityError, PermissionError,
            NetworkError, FileSystemError, IntegrityError, ComponentError,
            DetectionError, InstallationError, DownloadError, HashVerificationError,
            PluginError, StorageError, AnalysisError, RecoveryError,
            TimeoutError, ResourceError, CompatibilityError, UserInputError,
            ExternalServiceError, ArchitectureAnalysisError, UnifiedDetectionError,
            DependencyValidationError, RobustDownloadError, AdvancedInstallationError,
            SteamDeckIntegrationError, IntelligentStorageError, PluginSystemError
        ]
        
        for exception_type in expected_exceptions:
            assert exception_type in EXCEPTION_CATEGORY_MAP
    
    def test_category_values(self):
        """Test that category values are valid."""
        valid_categories = {
            "configuration", "validation", "system", "permission", "network",
            "file_system", "detection", "installation", "plugin", "user_input",
            "external_service"
        }
        
        for category in EXCEPTION_CATEGORY_MAP.values():
            assert category in valid_categories


class TestGetExceptionCategory:
    """Tests for get_exception_category function."""
    
    def test_get_category_for_known_exception(self):
        """Test getting category for known exception types."""
        config_error = ConfigurationError("Test error")
        assert get_exception_category(config_error) == "configuration"
        
        network_error = NetworkError("Test error")
        assert get_exception_category(network_error) == "network"
        
        validation_error = ValidationError("Test error")
        assert get_exception_category(validation_error) == "validation"
    
    def test_get_category_for_unknown_exception(self):
        """Test getting category for unknown exception types."""
        unknown_error = ValueError("Test error")
        assert get_exception_category(unknown_error) == "unknown"
        
        runtime_error = RuntimeError("Test error")
        assert get_exception_category(runtime_error) == "unknown"


class TestCreateContextException:
    """Tests for create_context_exception function."""
    
    def test_create_context_exception_basic(self):
        """Test creating context exception with basic parameters."""
        original_error = ValueError("Original error message")
        
        context_error = create_context_exception(
            base_exception=original_error,
            component="test_component",
            operation="test_operation"
        )
        
        assert isinstance(context_error, EnvironmentDevDeepEvaluationError)
        assert "Error in test_component.test_operation" in context_error.message
        assert "Original error message" in context_error.message
        assert context_error.cause == original_error
        assert context_error.context["component"] == "test_component"
        assert context_error.context["operation"] == "test_operation"
        assert context_error.context["original_exception"] == "Original error message"
        assert context_error.context["original_type"] == "ValueError"
    
    def test_create_context_exception_with_additional_context(self):
        """Test creating context exception with additional context."""
        original_error = ConnectionError("Connection failed")
        additional_context = {
            "url": "https://example.com",
            "timeout": 30,
            "retry_count": 3
        }
        
        context_error = create_context_exception(
            base_exception=original_error,
            component="downloader",
            operation="download_file",
            context=additional_context
        )
        
        assert context_error.context["url"] == "https://example.com"
        assert context_error.context["timeout"] == 30
        assert context_error.context["retry_count"] == 3
        assert context_error.context["component"] == "downloader"
        assert context_error.context["operation"] == "download_file"
    
    def test_create_context_exception_preserves_original_info(self):
        """Test that context exception preserves original exception information."""
        original_error = FileNotFoundError("File not found: /path/to/file")
        
        context_error = create_context_exception(
            base_exception=original_error,
            component="file_manager",
            operation="read_file"
        )
        
        assert context_error.cause == original_error
        assert context_error.context["original_type"] == "FileNotFoundError"
        assert "File not found: /path/to/file" in context_error.context["original_exception"]


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""
    
    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from base exception."""
        exception_classes = [
            ArchitectureAnalysisError, UnifiedDetectionError, DependencyValidationError,
            RobustDownloadError, AdvancedInstallationError, SteamDeckIntegrationError,
            IntelligentStorageError, PluginSystemError, ConfigurationError,
            ValidationError, SecurityError, PermissionError, NetworkError,
            FileSystemError, IntegrityError, ComponentError, DetectionError,
            InstallationError, DownloadError, HashVerificationError, PluginError,
            StorageError, AnalysisError, RecoveryError, TimeoutError, ResourceError,
            CompatibilityError, UserInputError, ExternalServiceError
        ]
        
        for exception_class in exception_classes:
            error = exception_class("Test message")
            assert isinstance(error, EnvironmentDevDeepEvaluationError)
            assert isinstance(error, Exception)
    
    def test_exception_can_be_caught_as_base_type(self):
        """Test that specific exceptions can be caught as base type."""
        try:
            raise NetworkError("Network connection failed")
        except EnvironmentDevDeepEvaluationError as e:
            assert isinstance(e, NetworkError)
            assert e.message == "Network connection failed"
        else:
            pytest.fail("Exception was not caught")
    
    def test_exception_can_be_caught_as_specific_type(self):
        """Test that exceptions can be caught by their specific type."""
        try:
            raise ValidationError("Validation failed")
        except ValidationError as e:
            assert e.message == "Validation failed"
        except EnvironmentDevDeepEvaluationError:
            pytest.fail("Exception was caught by base type instead of specific type")
        else:
            pytest.fail("Exception was not caught")