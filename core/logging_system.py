"""Enhanced logging system for Environment Dev Deep Evaluation.

Provides centralized logging configuration, custom formatters, and improved
error handling with structured logging capabilities.
"""

import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import contextmanager

from .config import SystemConfiguration
from .exceptions import EnvironmentDevDeepEvaluationError


class LogLevel(str, Enum):
    """Supported log levels."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"  # Custom level for detailed tracing


class LogFormat(str, Enum):
    """Supported log formats."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LoggingConfiguration:
    """Configuration for the logging system."""
    
    # Basic settings
    level: LogLevel = LogLevel.INFO
    format_type: LogFormat = LogFormat.DETAILED
    enable_console: bool = True
    enable_file: bool = True
    
    # File settings
    log_directory: str = "logs"
    log_filename: str = "environment_dev_deep_evaluation.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Advanced settings
    enable_structured_logging: bool = True
    enable_performance_logging: bool = False
    enable_security_logging: bool = True
    log_sensitive_data: bool = False
    
    # Component-specific settings
    component_log_levels: Dict[str, LogLevel] = field(default_factory=dict)
    
    # Filter settings
    exclude_modules: List[str] = field(default_factory=lambda: [
        "urllib3.connectionpool",
        "requests.packages.urllib3"
    ])
    
    # Performance settings
    async_logging: bool = False
    buffer_size: int = 1000


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        """Initialize structured formatter.
        
        Args:
            include_extra: Whether to include extra fields in log records
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured data.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if enabled
        if self.include_extra and hasattr(record, 'context'):
            log_data["context"] = record.context
        
        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_') and key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """Enhanced formatter with detailed information."""
    
    def __init__(self):
        """Initialize detailed formatter."""
        super().__init__()
        self.format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)-30s | "
            "%(funcName)-20s:%(lineno)-4d | %(message)s"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with detailed information.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        # Apply base formatting
        formatted = super().format(record)
        
        # Add context information if available
        if hasattr(record, 'context') and record.context:
            context_str = json.dumps(record.context, default=str, ensure_ascii=False)
            formatted += f" | Context: {context_str}"
        
        # Add exception details if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format timestamp with milliseconds.
        
        Args:
            record: Log record
            datefmt: Date format string
            
        Returns:
            Formatted timestamp
        """
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class PerformanceFilter(logging.Filter):
    """Filter for performance-related log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter performance-related records.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be logged
        """
        # Only log performance records if they have timing information
        return hasattr(record, 'duration') or 'performance' in record.getMessage().lower()


class SecurityFilter(logging.Filter):
    """Filter for security-related log records."""
    
    def __init__(self, log_sensitive_data: bool = False):
        """Initialize security filter.
        
        Args:
            log_sensitive_data: Whether to log sensitive data
        """
        super().__init__()
        self.log_sensitive_data = log_sensitive_data
        self.sensitive_patterns = [
            'password', 'token', 'key', 'secret', 'credential',
            'auth', 'session', 'cookie', 'hash'
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter security-related records.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be logged
        """
        if not self.log_sensitive_data:
            message = record.getMessage().lower()
            for pattern in self.sensitive_patterns:
                if pattern in message:
                    # Sanitize the message
                    record.msg = "[SENSITIVE DATA REDACTED]"
                    record.args = ()
                    break
        
        return True


class EnhancedLoggingSystem:
    """Enhanced logging system with advanced features."""
    
    _instance: Optional['EnhancedLoggingSystem'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EnhancedLoggingSystem':
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logging system."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config: Optional[LoggingConfiguration] = None
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: List[logging.Handler] = []
        self._performance_data: Dict[str, List[float]] = {}
        
        # Add custom log level
        logging.addLevelName(5, "TRACE")
    
    def configure(self, config: Union[LoggingConfiguration, SystemConfiguration]) -> None:
        """Configure the logging system.
        
        Args:
            config: Logging configuration or system configuration
        """
        if isinstance(config, SystemConfiguration):
            self._config = self._create_logging_config_from_system_config(config)
        else:
            self._config = config
        
        self._setup_logging()
    
    def _create_logging_config_from_system_config(self, sys_config: SystemConfiguration) -> LoggingConfiguration:
        """Create logging configuration from system configuration.
        
        Args:
            sys_config: System configuration
            
        Returns:
            Logging configuration
        """
        return LoggingConfiguration(
            level=LogLevel(sys_config.log_level),
            log_directory=sys_config.logs_directory,
            enable_structured_logging=sys_config.detailed_feedback,
            enable_performance_logging=sys_config.debug_mode,
            log_sensitive_data=sys_config.debug_mode
        )
    
    def _setup_logging(self) -> None:
        """Setup logging handlers and formatters."""
        if not self._config:
            raise EnvironmentDevDeepEvaluationError("Logging system not configured")
        
        # Clear existing handlers
        self._clear_handlers()
        
        # Setup console handler
        if self._config.enable_console:
            self._setup_console_handler()
        
        # Setup file handler
        if self._config.enable_file:
            self._setup_file_handler()
        
        # Setup root logger
        self._setup_root_logger()
        
        # Apply filters
        self._apply_filters()
    
    def _clear_handlers(self) -> None:
        """Clear existing handlers."""
        root_logger = logging.getLogger()
        for handler in self._handlers:
            root_logger.removeHandler(handler)
            handler.close()
        self._handlers.clear()
    
    def _setup_console_handler(self) -> None:
        """Setup console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Choose formatter based on configuration
        if self._config.format_type == LogFormat.JSON:
            formatter = StructuredFormatter()
        elif self._config.format_type == LogFormat.DETAILED:
            formatter = DetailedFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self._config.level.value)
        
        self._handlers.append(console_handler)
        logging.getLogger().addHandler(console_handler)
    
    def _setup_file_handler(self) -> None:
        """Setup file logging handler."""
        # Ensure log directory exists
        log_dir = Path(self._config.log_directory)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / self._config.log_filename
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._config.max_file_size,
            backupCount=self._config.backup_count,
            encoding='utf-8'
        )
        
        # Use structured format for file logging
        if self._config.enable_structured_logging:
            formatter = StructuredFormatter()
        else:
            formatter = DetailedFormatter()
        
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self._config.level.value)
        
        self._handlers.append(file_handler)
        logging.getLogger().addHandler(file_handler)
    
    def _setup_root_logger(self) -> None:
        """Setup root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self._config.level.value)
    
    def _apply_filters(self) -> None:
        """Apply logging filters."""
        # Apply security filter
        if self._config.enable_security_logging:
            security_filter = SecurityFilter(self._config.log_sensitive_data)
            for handler in self._handlers:
                handler.addFilter(security_filter)
        
        # Apply module exclusion filters
        for module_name in self._config.exclude_modules:
            logging.getLogger(module_name).setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            
            # Apply component-specific log level if configured
            if self._config and name in self._config.component_log_levels:
                logger.setLevel(self._config.component_log_levels[name].value)
            
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    @contextmanager
    def performance_context(self, operation: str, logger: Optional[logging.Logger] = None):
        """Context manager for performance logging.
        
        Args:
            operation: Operation name
            logger: Logger to use (defaults to performance logger)
        """
        if not logger:
            logger = self.get_logger("performance")
        
        start_time = datetime.now()
        logger.info(f"Starting operation: {operation}")
        
        try:
            yield
            duration = (datetime.now() - start_time).total_seconds()
            
            # Store performance data
            if operation not in self._performance_data:
                self._performance_data[operation] = []
            self._performance_data[operation].append(duration)
            
            logger.info(
                f"Completed operation: {operation}",
                extra={"duration": duration, "operation": operation}
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Failed operation: {operation} - {str(e)}",
                extra={"duration": duration, "operation": operation, "error": str(e)}
            )
            raise
    
    def log_structured(self, logger: logging.Logger, level: str, message: str, **kwargs) -> None:
        """Log a structured message with additional context.
        
        Args:
            logger: Logger to use
            level: Log level
            message: Log message
            **kwargs: Additional context data
        """
        log_method = getattr(logger, level.lower())
        log_method(message, extra={"context": kwargs})
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics.
        
        Returns:
            Dictionary of performance statistics by operation
        """
        stats = {}
        
        for operation, durations in self._performance_data.items():
            if durations:
                stats[operation] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
        
        return stats
    
    def clear_performance_data(self) -> None:
        """Clear stored performance data."""
        self._performance_data.clear()
    
    def shutdown(self) -> None:
        """Shutdown the logging system."""
        self._clear_handlers()
        logging.shutdown()


# Global logging system instance
logging_system = EnhancedLoggingSystem()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging_system.get_logger(name)


def configure_logging(config: Union[LoggingConfiguration, SystemConfiguration]) -> None:
    """Configure the global logging system.
    
    Args:
        config: Logging configuration
    """
    logging_system.configure(config)


@contextmanager
def performance_context(operation: str, logger: Optional[logging.Logger] = None):
    """Global performance context manager.
    
    Args:
        operation: Operation name
        logger: Logger to use
    """
    with logging_system.performance_context(operation, logger) as ctx:
        yield ctx


def log_performance(operation: str, logger: Optional[logging.Logger] = None):
    """Decorator for performance logging.
    
    Args:
        operation: Operation name
        logger: Logger to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_context(operation, logger):
                return func(*args, **kwargs)
        return wrapper
    return decorator