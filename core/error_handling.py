"""Enhanced error handling system for Environment Dev Deep Evaluation.

Provides comprehensive error handling, recovery mechanisms, and integration
with the logging system for better debugging and monitoring.
"""

import sys
import traceback
import functools
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Type, List, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from .exceptions import EnvironmentDevDeepEvaluationError
from .logging_system import get_logger, logging_system


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    VALIDATION = "validation"
    INSTALLATION = "installation"
    DETECTION = "detection"
    PLUGIN = "plugin"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    USER_INTERVENTION = "user_intervention"
    AUTOMATIC_FIX = "automatic_fix"


@dataclass
class ErrorContext:
    """Context information for errors."""
    
    # Basic information
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Error classification
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    
    # Context data
    user_data: Dict[str, Any] = field(default_factory=dict)
    system_data: Dict[str, Any] = field(default_factory=dict)
    environment_data: Dict[str, Any] = field(default_factory=dict)
    
    # Recovery information
    recovery_strategy: Optional[RecoveryStrategy] = None
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    
    # Additional metadata
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation of error context
        """
        return {
            "component": self.component,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "user_data": self.user_data,
            "system_data": self.system_data,
            "environment_data": self.environment_data,
            "recovery_strategy": self.recovery_strategy.value if self.recovery_strategy else None,
            "recovery_attempts": self.recovery_attempts,
            "max_recovery_attempts": self.max_recovery_attempts,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id
        }


@dataclass
class ErrorReport:
    """Comprehensive error report."""
    
    # Error information
    exception: Exception
    context: ErrorContext
    traceback_info: str
    
    # System state
    system_info: Dict[str, Any] = field(default_factory=dict)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    # Recovery information
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_details: Optional[str] = None
    
    # Reporting metadata
    report_id: str = field(default_factory=lambda: f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary.
        
        Returns:
            Dictionary representation of error report
        """
        return {
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat(),
            "exception": {
                "type": type(self.exception).__name__,
                "message": str(self.exception),
                "args": self.exception.args
            },
            "context": self.context.to_dict(),
            "traceback": self.traceback_info,
            "system_info": self.system_info,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "recovery_details": self.recovery_details
        }


class ErrorRecoveryManager:
    """Manages error recovery strategies."""
    
    def __init__(self):
        """Initialize recovery manager."""
        self.logger = get_logger("error_recovery")
        self.recovery_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_stats: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()
    
    def register_recovery_handler(
        self, 
        category: ErrorCategory, 
        handler: Callable[[Exception, ErrorContext], bool]
    ) -> None:
        """Register a recovery handler for a specific error category.
        
        Args:
            category: Error category
            handler: Recovery handler function that returns True if recovery succeeded
        """
        if category not in self.recovery_handlers:
            self.recovery_handlers[category] = []
        
        self.recovery_handlers[category].append(handler)
        self.logger.info(f"Registered recovery handler for category: {category.value}")
    
    def attempt_recovery(self, exception: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from an error.
        
        Args:
            exception: The exception that occurred
            context: Error context
            
        Returns:
            True if recovery was successful
        """
        with self._lock:
            context.recovery_attempts += 1
            
            if context.recovery_attempts > context.max_recovery_attempts:
                self.logger.warning(
                    f"Maximum recovery attempts exceeded for {context.component}.{context.operation}"
                )
                return False
            
            # Get handlers for the error category
            handlers = self.recovery_handlers.get(context.category, [])
            
            if not handlers:
                self.logger.debug(f"No recovery handlers for category: {context.category.value}")
                return False
            
            # Try each recovery handler
            for handler in handlers:
                try:
                    self.logger.info(
                        f"Attempting recovery with handler: {handler.__name__}",
                        extra={"context": context.to_dict()}
                    )
                    
                    if handler(exception, context):
                        self.logger.info(
                            f"Recovery successful with handler: {handler.__name__}",
                            extra={"context": context.to_dict()}
                        )
                        self._update_recovery_stats(context.category.value, "success")
                        return True
                    
                except Exception as recovery_error:
                    self.logger.error(
                        f"Recovery handler {handler.__name__} failed: {str(recovery_error)}",
                        extra={"context": context.to_dict()}
                    )
                    self._update_recovery_stats(context.category.value, "handler_error")
            
            self._update_recovery_stats(context.category.value, "failure")
            return False
    
    def _update_recovery_stats(self, category: str, outcome: str) -> None:
        """Update recovery statistics.
        
        Args:
            category: Error category
            outcome: Recovery outcome
        """
        if category not in self.recovery_stats:
            self.recovery_stats[category] = {}
        
        if outcome not in self.recovery_stats[category]:
            self.recovery_stats[category][outcome] = 0
        
        self.recovery_stats[category][outcome] += 1
    
    def get_recovery_stats(self) -> Dict[str, Dict[str, int]]:
        """Get recovery statistics.
        
        Returns:
            Dictionary of recovery statistics by category
        """
        return self.recovery_stats.copy()


class EnhancedErrorHandler:
    """Enhanced error handling system."""
    
    _instance: Optional['EnhancedErrorHandler'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EnhancedErrorHandler':
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize error handler."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = get_logger("error_handler")
        self.recovery_manager = ErrorRecoveryManager()
        self.error_reports: List[ErrorReport] = []
        self.error_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
        
        # Register default recovery handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default recovery handlers."""
        
        def retry_handler(exception: Exception, context: ErrorContext) -> bool:
            """Default retry handler."""
            if context.recovery_strategy == RecoveryStrategy.RETRY:
                self.logger.info(f"Retrying operation: {context.operation}")
                # This is a placeholder - actual retry logic would be implemented
                # by the calling code using the retry decorator
                return True
            return False
        
        def permission_handler(exception: Exception, context: ErrorContext) -> bool:
            """Handler for permission errors."""
            if isinstance(exception, PermissionError):
                self.logger.warning("Permission error detected - suggesting elevation")
                context.recovery_strategy = RecoveryStrategy.USER_INTERVENTION
                return False  # Requires user intervention
            return False
        
        def network_handler(exception: Exception, context: ErrorContext) -> bool:
            """Handler for network errors."""
            import socket
            if isinstance(exception, (socket.error, ConnectionError)):
                self.logger.info("Network error detected - will retry with backoff")
                context.recovery_strategy = RecoveryStrategy.RETRY
                return False  # Let retry mechanism handle it
            return False
        
        # Register handlers
        self.recovery_manager.register_recovery_handler(ErrorCategory.SYSTEM, retry_handler)
        self.recovery_manager.register_recovery_handler(ErrorCategory.PERMISSION, permission_handler)
        self.recovery_manager.register_recovery_handler(ErrorCategory.NETWORK, network_handler)
    
    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        reraise: bool = True
    ) -> Optional[ErrorReport]:
        """Handle an error with comprehensive logging and recovery.
        
        Args:
            exception: The exception that occurred
            context: Error context
            reraise: Whether to reraise the exception after handling
            
        Returns:
            Error report if created
        """
        with self._lock:
            # Create error report
            report = self._create_error_report(exception, context)
            
            # Log the error
            self._log_error(exception, context, report)
            
            # Update error counts
            error_key = f"{context.component}.{context.operation}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Attempt recovery if strategy is defined
            if context.recovery_strategy:
                report.recovery_attempted = True
                report.recovery_successful = self.recovery_manager.attempt_recovery(exception, context)
                
                if report.recovery_successful:
                    report.recovery_details = f"Recovered using strategy: {context.recovery_strategy.value}"
                    self.logger.info(
                        f"Error recovery successful for {context.component}.{context.operation}",
                        extra={"context": context.to_dict()}
                    )
                    return report
            
            # Store error report
            self.error_reports.append(report)
            
            # Reraise if requested
            if reraise:
                if not isinstance(exception, EnvironmentDevDeepEvaluationError):
                    raise EnvironmentDevDeepEvaluationError(
                        f"Error in {context.component}.{context.operation}: {str(exception)}",
                        context=context.to_dict(),
                        cause=exception
                    ) from exception
                else:
                    raise exception
            
            return report
    
    def _create_error_report(self, exception: Exception, context: ErrorContext) -> ErrorReport:
        """Create a comprehensive error report.
        
        Args:
            exception: The exception that occurred
            context: Error context
            
        Returns:
            Error report
        """
        # Get system information
        system_info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "thread_count": threading.active_count()
        }
        
        # Get memory and CPU usage if available
        memory_usage = None
        cpu_usage = None
        
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_percent()
            cpu_usage = process.cpu_percent()
        except ImportError:
            pass
        except Exception:
            pass
        
        return ErrorReport(
            exception=exception,
            context=context,
            traceback_info=traceback.format_exc(),
            system_info=system_info,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage
        )
    
    def _log_error(self, exception: Exception, context: ErrorContext, report: ErrorReport) -> None:
        """Log error with appropriate level and context.
        
        Args:
            exception: The exception that occurred
            context: Error context
            report: Error report
        """
        log_level = self._get_log_level_for_severity(context.severity)
        
        log_data = {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "context": context.to_dict(),
            "report_id": report.report_id
        }
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR in {context.component}.{context.operation}: {str(exception)}",
                extra=log_data,
                exc_info=True
            )
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"HIGH SEVERITY ERROR in {context.component}.{context.operation}: {str(exception)}",
                extra=log_data,
                exc_info=True
            )
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"ERROR in {context.component}.{context.operation}: {str(exception)}",
                extra=log_data
            )
        else:
            self.logger.info(
                f"Minor error in {context.component}.{context.operation}: {str(exception)}",
                extra=log_data
            )
    
    def _get_log_level_for_severity(self, severity: ErrorSeverity) -> str:
        """Get appropriate log level for error severity.
        
        Args:
            severity: Error severity
            
        Returns:
            Log level string
        """
        mapping = {
            ErrorSeverity.LOW: "info",
            ErrorSeverity.MEDIUM: "warning",
            ErrorSeverity.HIGH: "error",
            ErrorSeverity.CRITICAL: "critical"
        }
        return mapping.get(severity, "error")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics.
        
        Returns:
            Dictionary of error statistics
        """
        total_errors = len(self.error_reports)
        
        if total_errors == 0:
            return {"total_errors": 0}
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        component_counts = {}
        
        for report in self.error_reports:
            # Category counts
            category = report.context.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Severity counts
            severity = report.context.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Component counts
            component = report.context.component
            component_counts[component] = component_counts.get(component, 0) + 1
        
        return {
            "total_errors": total_errors,
            "by_category": category_counts,
            "by_severity": severity_counts,
            "by_component": component_counts,
            "recovery_stats": self.recovery_manager.get_recovery_stats(),
            "error_counts": self.error_counts.copy()
        }
    
    def clear_error_history(self) -> None:
        """Clear error history and statistics."""
        with self._lock:
            self.error_reports.clear()
            self.error_counts.clear()
            self.recovery_manager.recovery_stats.clear()


# Global error handler instance
error_handler = EnhancedErrorHandler()


def handle_errors(
    component: str,
    operation: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_strategy: Optional[RecoveryStrategy] = None,
    max_retries: int = 3,
    **context_data
):
    """Decorator for automatic error handling.
    
    Args:
        component: Component name
        operation: Operation name
        category: Error category
        severity: Error severity
        recovery_strategy: Recovery strategy
        max_retries: Maximum retry attempts
        **context_data: Additional context data
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                component=component,
                operation=operation,
                category=category,
                severity=severity,
                recovery_strategy=recovery_strategy,
                max_recovery_attempts=max_retries,
                user_data=context_data
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(e, context)
        
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying operations on error.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Backoff factor for delay
        exceptions: Tuple of exceptions to retry on
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        get_logger("retry").info(
                            f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} after {current_delay}s"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        get_logger("retry").error(
                            f"All retry attempts failed for {func.__name__}"
                        )
                        raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


@contextmanager
def error_context(
    component: str,
    operation: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    **context_data
):
    """Context manager for error handling.
    
    Args:
        component: Component name
        operation: Operation name
        category: Error category
        severity: Error severity
        **context_data: Additional context data
    """
    context = ErrorContext(
        component=component,
        operation=operation,
        category=category,
        severity=severity,
        user_data=context_data
    )
    
    try:
        yield context
    except Exception as e:
        error_handler.handle_error(e, context)