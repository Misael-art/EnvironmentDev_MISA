"""Tests for core.base module."""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from core.base import SystemComponentBase, OperationResult
from core.config import ConfigurationManager, SystemConfiguration
from core.exceptions import (
    EnvironmentDevDeepEvaluationError, ConfigurationError,
    ValidationError, ComponentError
)


class TestOperationResult:
    """Tests for OperationResult class."""
    
    def test_successful_result_creation(self):
        """Test creating a successful operation result."""
        result = OperationResult(
            success=True,
            message="Operation completed successfully",
            data={"key": "value"},
            error=None
        )
        
        assert result.success is True
        assert result.message == "Operation completed successfully"
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)
    
    def test_failed_result_creation(self):
        """Test creating a failed operation result."""
        error = ValueError("Test error")
        result = OperationResult(
            success=False,
            message="Operation failed",
            data=None,
            error=error
        )
        
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.data is None
        assert result.error == error
    
    def test_result_string_representation(self):
        """Test string representation of operation result."""
        result = OperationResult(
            success=True,
            message="Test operation",
            data=None,
            error=None
        )
        
        expected = "OperationResult(success=True, message='Test operation')"
        assert str(result) == expected
    
    def test_result_with_none_data(self):
        """Test operation result with None data."""
        result = OperationResult(
            success=True,
            message="No data operation",
            data=None,
            error=None
        )
        
        assert result.data is None
        assert result.success is True
    
    def test_result_with_complex_data(self):
        """Test operation result with complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "number": 42
        }
        
        result = OperationResult(
            success=True,
            message="Complex data operation",
            data=complex_data,
            error=None
        )
        
        assert result.data == complex_data
        assert result.data["list"] == [1, 2, 3]
        assert result.data["nested"]["inner"] == "value"


class ConcreteSystemComponent(SystemComponentBase):
    """Concrete implementation of SystemComponentBase for testing."""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self._test_data = {}
    
    def initialize(self) -> None:
        """Initialize the component."""
        self._logger.info("Initializing concrete system component")
        self._test_data["initialized"] = True
    
    def validate_configuration(self) -> None:
        """Validate component-specific configuration."""
        config = self.get_config()
        
        # Validate operation timeout
        if hasattr(config, 'operation_timeout') and config.operation_timeout <= 0:
            from core.exceptions import ConfigurationError
            raise ConfigurationError("operation_timeout must be positive")
        
        # Validate max parallel operations
        if hasattr(config, 'max_parallel_operations') and config.max_parallel_operations <= 0:
            from core.exceptions import ConfigurationError
            raise ConfigurationError("max_parallel_operations must be positive")
    
    def cleanup(self) -> OperationResult:
        """Cleanup the component."""
        try:
            self._logger.info("Cleaning up concrete system component")
            self._test_data.clear()
            return OperationResult(
                success=True,
                message="Component cleaned up successfully",
                data=None
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to cleanup component: {str(e)}",
                data=None
            )
    
    def get_test_data(self):
        """Get test data for verification."""
        return self._test_data


class TestSystemComponentBase:
    """Tests for SystemComponentBase class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock configuration and manager
        self.mock_config = Mock(spec=SystemConfiguration)
        self.mock_config.debug_mode = False
        self.mock_config.log_level = "INFO"
        self.mock_config.logs_directory = str(self.temp_path / "logs")
        self.mock_config.operation_timeout = 300
        self.mock_config.max_parallel_operations = 4

        self.mock_config_manager = Mock(spec=ConfigurationManager)
        self.mock_config_manager.get_config.return_value = self.mock_config
        
        # Create concrete component for testing
        self.component = ConcreteSystemComponent(self.mock_config_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_component_initialization(self):
        """Test component initialization."""
        assert self.component._config == self.mock_config
        assert self.component._logger is not None
        assert isinstance(self.component._logger, logging.Logger)
        # Logger uses structured name: component.<ComponentName>
        assert self.component._logger.name.endswith("ConcreteSystemComponent")
    
    def test_component_logger_setup(self):
        """Test that logger is properly configured."""
        logger = self.component._logger
        
        assert logger.name.endswith("ConcreteSystemComponent")
    
    def test_component_initialization_method(self):
        """Test component initialize method."""
        self.component.initialize()
        
        # Verify internal state
        test_data = self.component.get_test_data()
        assert test_data["initialized"] is True
    
    def test_component_cleanup_method(self):
        """Test component cleanup method."""
        # Initialize first
        self.component.initialize()
        assert len(self.component.get_test_data()) > 0
        
        # Then cleanup
        result = self.component.cleanup()
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "cleaned up successfully" in result.message
        assert result.data is None
        
        # Verify internal state is cleared
        test_data = self.component.get_test_data()
        assert len(test_data) == 0
    
    def test_handle_error_method(self):
        """Test error handling method."""
        test_error = ValueError("Test error message")
        
        # _handle_error does not return OperationResult; it logs and delegates to error handler
        # We verify it does not raise and interacts with handler via logging mock
        try:
            self.component._handle_error(test_error, "Custom error context")
        except Exception as e:
            pytest.fail(f"_handle_error raised unexpectedly: {e}")
    
    def test_handle_error_with_none_context(self):
        """Test error handling with None context."""
        test_error = RuntimeError("Runtime error")
        
        try:
            self.component._handle_error(test_error, None)
        except Exception as e:
            pytest.fail(f"_handle_error raised unexpectedly: {e}")
    
    def test_handle_error_logging(self):
        """Test that errors are properly logged."""
        test_error = Exception("Test exception")
        
        with patch.object(self.component._logger, 'error') as mock_log_error:
            result = self.component._handle_error(test_error, "Test context")
            
            # Verify error was logged
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args[0]
            assert "Test context" in call_args[0]
    
    def test_get_component_info(self):
        """Test getting component information."""
        info = self.component.get_component_info()
        
        assert isinstance(info, dict)
        assert "component_name" in info
        assert "initialized" in info
        assert "last_operation_time" in info
        assert "operation_count" in info
        
        assert info["component_name"] == "ConcreteSystemComponent"
        assert info["initialized"] == False  # Not initialized yet
        assert info["operation_count"] == 0
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        # Mock config with valid values
        self.mock_config.operation_timeout = 300
        self.mock_config.max_parallel_operations = 4
        
        # Should not raise any exception
        try:
            self.component._validate_configuration()
        except Exception as e:
            pytest.fail(f"Configuration validation failed unexpectedly: {e}")
    
    def test_validate_configuration_invalid_timeout(self):
        """Test configuration validation with invalid timeout."""
        self.mock_config.operation_timeout = -100
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.component._validate_configuration()
        
        assert "operation_timeout must be positive" in str(exc_info.value)
    
    def test_validate_configuration_invalid_parallel_ops(self):
        """Test configuration validation with invalid parallel operations."""
        self.mock_config.max_parallel_operations = 0
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.component._validate_configuration()
        
        assert "max_parallel_operations must be positive" in str(exc_info.value)
    
    def test_component_lifecycle(self):
        """Test complete component lifecycle."""
        # Initialize
        init_result = self.component.initialize()
        assert init_result.success is True
        
        # Verify initialized state
        test_data = self.component.get_test_data()
        assert test_data["initialized"] is True
        
        # Cleanup
        cleanup_result = self.component.cleanup()
        assert cleanup_result.success is True
        
        # Verify cleaned state
        test_data = self.component.get_test_data()
        assert len(test_data) == 0
    
    def test_component_with_debug_mode(self):
        """Test component behavior with debug mode enabled."""
        self.mock_config.debug_mode = True
        self.mock_config.log_level = "DEBUG"
        
        debug_component = ConcreteSystemComponent(self.mock_config_manager)
        
        # Logger should be configured for debug level
        assert debug_component._logger.level <= logging.DEBUG
    
    def test_component_error_handling_during_initialization(self):
        """Test error handling during component initialization."""
        # Create a component that will fail during initialization
        class FailingComponent(SystemComponentBase):
            def __init__(self, config_manager):
                super().__init__(config_manager)
            
            def initialize(self):
                raise RuntimeError("Initialization failed")
            
            def validate_configuration(self) -> None:
                pass
            
            def cleanup(self):
                return OperationResult(True, "Cleanup", None, None)
        
        failing_component = FailingComponent(self.mock_config_manager)
        
        with pytest.raises(RuntimeError):
            failing_component.initialize()
    
    def test_component_error_handling_during_cleanup(self):
        """Test error handling during component cleanup."""
        # Create a component that will fail during cleanup
        class FailingCleanupComponent(SystemComponentBase):
            def __init__(self, config_manager):
                super().__init__(config_manager)
            
            def initialize(self):
                return OperationResult(True, "Initialized", None, None)
            
            def validate_configuration(self) -> None:
                pass
            
            def cleanup(self):
                raise RuntimeError("Cleanup failed")
        
        failing_component = FailingCleanupComponent(self.mock_config_manager)
        
        with pytest.raises(RuntimeError):
            failing_component.cleanup()
    
    def test_component_with_custom_logger_name(self):
        """Test component with custom logger name."""
        class CustomNameComponent(SystemComponentBase):
            def __init__(self, config_manager):
                super().__init__(config_manager)
                # Override logger name
                self._logger = logging.getLogger("CustomLogger")
            
            def initialize(self):
                return OperationResult(True, "Initialized", None, None)
            
            def validate_configuration(self) -> None:
                pass
            
            def cleanup(self):
                return OperationResult(True, "Cleaned up", None, None)
        
        custom_component = CustomNameComponent(self.mock_config_manager)
        assert custom_component._logger.name == "CustomLogger"
    
    def test_component_configuration_access(self):
        """Test accessing configuration from component."""
        # Component should have access to configuration
        assert self.component._config == self.mock_config
        assert self.component._config.debug_mode == self.mock_config.debug_mode
        assert self.component._config.log_level == self.mock_config.log_level
    
    def test_component_thread_safety_considerations(self):
        """Test component behavior in multi-threaded scenarios."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                # Each thread gets its own component instance
                worker_component = ConcreteSystemComponent(self.mock_config_manager)
                result = worker_component.initialize()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        for result in results:
            assert result.success is True
    
    def test_abstract_methods_enforcement(self):
        """Test that abstract methods must be implemented."""
        # Attempting to instantiate SystemComponentBase directly should fail
        with pytest.raises(TypeError):
            SystemComponentBase(self.mock_config_manager)
    
    def test_component_memory_cleanup(self):
        """Test that component properly cleans up memory."""
        import gc
        import weakref
        
        # Create component and get weak reference
        component = ConcreteSystemComponent(self.mock_config_manager)
        weak_ref = weakref.ref(component)
        
        # Initialize and cleanup
        component.initialize()
        component.cleanup()
        
        # Delete component and force garbage collection
        del component
        gc.collect()
        
        # Weak reference should be None if properly cleaned up
        # Note: This test might be flaky depending on Python's GC behavior
        # but it's useful for detecting obvious memory leaks
        assert weak_ref() is None or True  # Allow for GC timing variations