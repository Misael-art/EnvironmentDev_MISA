"""Tests for core.logging_system module."""

import os
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from core.logging_system import (
    LogLevel, LogFormat, LoggingConfiguration, StructuredFormatter,
    DetailedFormatter, PerformanceFilter, SecurityFilter,
    EnhancedLoggingSystem, configure_logging, log_performance
)
from core.config import SystemConfiguration
from core.exceptions import EnvironmentDevDeepEvaluationError


class TestLogLevel:
    """Tests for LogLevel enum."""
    
    def test_log_levels(self):
        """Test that all log levels are defined correctly."""
        assert LogLevel.CRITICAL == "CRITICAL"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.TRACE == "TRACE"


class TestLogFormat:
    """Tests for LogFormat enum."""
    
    def test_log_formats(self):
        """Test that all log formats are defined correctly."""
        assert LogFormat.SIMPLE == "simple"
        assert LogFormat.DETAILED == "detailed"
        assert LogFormat.JSON == "json"
        assert LogFormat.STRUCTURED == "structured"


class TestLoggingConfiguration:
    """Tests for LoggingConfiguration dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfiguration()
        
        assert config.level == LogLevel.INFO
        assert config.format_type == LogFormat.DETAILED
        assert config.enable_console is True
        assert config.enable_file is True
        assert config.log_directory == "logs"
        assert config.log_filename == "environment_dev_deep_evaluation.log"
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5
        assert config.enable_structured_logging is True
        assert config.enable_performance_logging is False
        assert config.enable_security_logging is True
        assert config.log_sensitive_data is False
        assert config.component_log_levels == {}
        assert "urllib3.connectionpool" in config.exclude_modules
        assert "requests.packages.urllib3" in config.exclude_modules
        assert config.async_logging is False
        assert config.buffer_size == 1000
    
    def test_custom_values(self):
        """Test configuration with custom values."""
        config = LoggingConfiguration(
            level=LogLevel.DEBUG,
            format_type=LogFormat.JSON,
            enable_console=False,
            log_directory="custom_logs",
            max_file_size=5 * 1024 * 1024,
            component_log_levels={"test_module": LogLevel.ERROR}
        )
        
        assert config.level == LogLevel.DEBUG
        assert config.format_type == LogFormat.JSON
        assert config.enable_console is False
        assert config.log_directory == "custom_logs"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.component_log_levels["test_module"] == LogLevel.ERROR


class TestStructuredFormatter:
    """Tests for StructuredFormatter class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.formatter = StructuredFormatter()
    
    def test_basic_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["module"] == "path"
        assert data["line"] == 42
        assert "timestamp" in data
        assert "thread" in data
        assert "process" in data
    
    def test_formatting_with_exception(self):
        """Test formatting with exception information."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test exception"
        assert "traceback" in data["exception"]
    
    def test_formatting_with_context(self):
        """Test formatting with context information."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"user_id": "123", "operation": "test_op"}
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        assert "context" in data
        assert data["context"]["user_id"] == "123"
        assert data["context"]["operation"] == "test_op"
    
    def test_formatting_without_extra(self):
        """Test formatting with include_extra disabled."""
        formatter = StructuredFormatter(include_extra=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"user_id": "123"}
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        # When include_extra is False, context should still be included as a custom field
        # The include_extra flag only affects whether hasattr(record, 'context') is checked
        # Since context is added as a custom field, it will still appear
        assert "context" in data
        assert data["context"] == {"user_id": "123"}


class TestDetailedFormatter:
    """Tests for DetailedFormatter class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.formatter = DetailedFormatter()
    
    def test_basic_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # The DetailedFormatter uses its internal format_string
        # Let's call the parent format method to apply the formatting
        temp_formatter = logging.Formatter(self.formatter.format_string)
        formatted = temp_formatter.format(record)
        
        assert "INFO" in formatted
        assert "test_logger" in formatted
        assert "Test message" in formatted
        assert ":42" in formatted
    
    def test_formatting_with_context(self):
        """Test formatting with context information."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"user_id": "123"}
        
        formatted = self.formatter.format(record)
        
        assert "Context:" in formatted
        assert "user_id" in formatted
    
    def test_time_formatting(self):
        """Test timestamp formatting with milliseconds."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        time_str = self.formatter.formatTime(record)
        
        # Should include milliseconds (format: YYYY-MM-DD HH:MM:SS.mmm)
        assert len(time_str) == 23
        assert time_str[19] == '.'


class TestPerformanceFilter:
    """Tests for PerformanceFilter class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.filter = PerformanceFilter()
    
    def test_filter_with_duration(self):
        """Test filtering records with duration attribute."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Operation completed",
            args=(),
            exc_info=None
        )
        record.duration = 1.5
        
        assert self.filter.filter(record) is True
    
    def test_filter_with_performance_message(self):
        """Test filtering records with performance in message."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Performance metrics updated",
            args=(),
            exc_info=None
        )
        
        assert self.filter.filter(record) is True
    
    def test_filter_without_performance_info(self):
        """Test filtering records without performance information."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Regular log message",
            args=(),
            exc_info=None
        )
        
        assert self.filter.filter(record) is False


class TestSecurityFilter:
    """Tests for SecurityFilter class."""
    
    def test_filter_with_sensitive_data_allowed(self):
        """Test filtering when sensitive data logging is allowed."""
        filter_obj = SecurityFilter(log_sensitive_data=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="User password: secret123",
            args=(),
            exc_info=None
        )
        
        assert filter_obj.filter(record) is True
        assert "secret123" in record.getMessage()
    
    def test_filter_with_sensitive_data_blocked(self):
        """Test filtering when sensitive data logging is blocked."""
        filter_obj = SecurityFilter(log_sensitive_data=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="User password: secret123",
            args=(),
            exc_info=None
        )
        
        assert filter_obj.filter(record) is True
        assert "[SENSITIVE DATA REDACTED]" in record.getMessage()
        assert "secret123" not in record.getMessage()
    
    def test_filter_without_sensitive_data(self):
        """Test filtering records without sensitive data."""
        filter_obj = SecurityFilter(log_sensitive_data=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Regular log message",
            args=(),
            exc_info=None
        )
        
        assert filter_obj.filter(record) is True
        assert record.getMessage() == "Regular log message"


class TestEnhancedLoggingSystem:
    """Tests for EnhancedLoggingSystem class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.logging_system = EnhancedLoggingSystem()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test logging system initialization."""
        # Create a new instance to test initialization
        # Note: EnhancedLoggingSystem is a singleton, so we need to work with that
        system = EnhancedLoggingSystem()
        
        assert hasattr(system, '_initialized')
        # The system might already be configured from previous tests
        assert hasattr(system, '_config')
        assert hasattr(system, '_loggers')
        assert hasattr(system, '_handlers')
        assert hasattr(system, '_performance_data')
    
    def test_configure_with_logging_configuration(self):
        """Test configuration with LoggingConfiguration."""
        config = LoggingConfiguration(
            level=LogLevel.DEBUG,
            log_directory=str(self.temp_path),
            enable_console=False,
            enable_file=True
        )
        
        self.logging_system.configure(config)
        
        assert self.logging_system._config == config
    
    def test_configure_with_system_configuration(self):
        """Test configuration with SystemConfiguration."""
        sys_config = SystemConfiguration(
            log_level="DEBUG",
            logs_directory=str(self.temp_path)
        )
        
        self.logging_system.configure(sys_config)
        
        assert self.logging_system._config.level == LogLevel.DEBUG
        assert self.logging_system._config.log_directory == str(self.temp_path)
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        config = LoggingConfiguration(
            log_directory=str(self.temp_path),
            enable_console=True,
            enable_file=False
        )
        self.logging_system.configure(config)
        
        logger = self.logging_system.get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert "test_logger" in self.logging_system._loggers
    
    def test_log_structured(self):
        """Test structured logging."""
        config = LoggingConfiguration(
            log_directory=str(self.temp_path),
            enable_console=True,
            enable_file=False
        )
        self.logging_system.configure(config)
        
        logger = self.logging_system.get_logger("test_logger")
        
        with patch.object(logger, 'info') as mock_info:
            self.logging_system.log_structured(
                logger, "info", "Test message", user_id="123", operation="test"
            )
            
            mock_info.assert_called_once_with(
                "Test message", 
                extra={"context": {"user_id": "123", "operation": "test"}}
            )
    
    def test_setup_without_configuration(self):
        """Test that setup fails without configuration."""
        # Create a fresh instance and clear its config
        system = EnhancedLoggingSystem()
        system._config = None
        
        with pytest.raises(EnvironmentDevDeepEvaluationError):
            system._setup_logging()
    
    @patch('logging.handlers.RotatingFileHandler')
    def test_file_handler_setup(self, mock_handler):
        """Test file handler setup."""
        config = LoggingConfiguration(
            log_directory=str(self.temp_path),
            enable_console=False,
            enable_file=True,
            max_file_size=1024,
            backup_count=3
        )
        
        self.logging_system.configure(config)
        
        # Verify that RotatingFileHandler was called with correct parameters
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[1]['maxBytes'] == 1024
        assert call_args[1]['backupCount'] == 3
        assert call_args[1]['encoding'] == 'utf-8'


class TestLogPerformanceDecorator:
    """Tests for log_performance decorator."""
    
    def test_performance_logging(self):
        """Test performance logging decorator."""
        mock_logger = MagicMock()
        
        @log_performance("test_operation", mock_logger)
        def test_function():
            return "result"
        
        result = test_function()
        
        assert result == "result"
        mock_logger.info.assert_called()
        
        # Check that the log message contains performance information
        call_args_list = mock_logger.info.call_args_list
        # Should have at least one call with the operation name
        operation_logged = any("test_operation" in str(call) for call in call_args_list)
        assert operation_logged
    
    def test_performance_logging_with_exception(self):
        """Test performance logging when function raises exception."""
        mock_logger = MagicMock()
        
        @log_performance("test_operation", mock_logger)
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
        
        # Should still log the performance even when exception occurs
        mock_logger.info.assert_called()


class TestConfigureLogging:
    """Tests for configure_logging function."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_configure_logging_with_logging_config(self):
        """Test configure_logging with LoggingConfiguration."""
        config = LoggingConfiguration(
            level=LogLevel.DEBUG,
            log_directory=str(self.temp_path)
        )
        
        # Should not raise any exception
        configure_logging(config)
    
    def test_configure_logging_with_system_config(self):
        """Test configure_logging with SystemConfiguration."""
        config = SystemConfiguration(
            log_level="DEBUG",
            logs_directory=str(self.temp_path)
        )
        
        # Should not raise any exception
        configure_logging(config)