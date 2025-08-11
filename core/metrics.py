#!/usr/bin/env python3
"""Metrics and Monitoring System for Environment Dev Deep Evaluation.

This module provides comprehensive metrics collection, monitoring capabilities,
and performance tracking for the system.
"""

import time
import threading
import psutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
from enum import Enum

from .base import SystemComponentBase, OperationResult
from .config import SystemConfiguration
from .exceptions import EnvironmentDevDeepEvaluationError


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """Container for a metric value with metadata."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit,
            "description": self.description
        }


@dataclass
class Alert:
    """Container for system alerts."""
    id: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold: Union[int, float]
    current_value: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "message": self.message,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class SystemHealth:
    """Container for system health metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system health to dictionary."""
        return asdict(self)


class MetricsCollector:
    """Thread-safe metrics collector."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize metrics collector.
        
        Args:
            max_history: Maximum number of metric values to keep in history
        """
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._max_history = max_history
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            tags: Optional tags for the metric
        """
        with self._lock:
            self._counters[name] += value
            metric = MetricValue(
                name=name,
                value=self._counters[name],
                metric_type=MetricType.COUNTER,
                tags=tags or {}
            )
            self._metrics[name].append(metric)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags for the metric
        """
        with self._lock:
            self._gauges[name] = value
            metric = MetricValue(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                tags=tags or {}
            )
            self._metrics[name].append(metric)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags for the metric
        """
        with self._lock:
            self._timers[name].append(duration)
            # Keep only recent timer values
            if len(self._timers[name]) > self._max_history:
                self._timers[name] = self._timers[name][-self._max_history:]
            
            metric = MetricValue(
                name=name,
                value=duration,
                metric_type=MetricType.TIMER,
                tags=tags or {},
                unit="seconds"
            )
            self._metrics[name].append(metric)
    
    def get_metric(self, name: str) -> Optional[MetricValue]:
        """Get the latest value for a metric.
        
        Args:
            name: Metric name
            
        Returns:
            Latest MetricValue or None if not found
        """
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1]
            return None
    
    def get_metric_history(self, name: str, limit: Optional[int] = None) -> List[MetricValue]:
        """Get metric history.
        
        Args:
            name: Metric name
            limit: Maximum number of values to return
            
        Returns:
            List of MetricValue objects
        """
        with self._lock:
            if name not in self._metrics:
                return []
            
            history = list(self._metrics[name])
            if limit:
                history = history[-limit:]
            return history
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a timer metric.
        
        Args:
            name: Timer metric name
            
        Returns:
            Dictionary with min, max, avg, count statistics
        """
        with self._lock:
            if name not in self._timers or not self._timers[name]:
                return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}
            
            values = self._timers[name]
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }
    
    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all metrics as dictionaries.
        
        Returns:
            Dictionary mapping metric names to lists of metric dictionaries
        """
        with self._lock:
            result = {}
            for name, history in self._metrics.items():
                result[name] = [metric.to_dict() for metric in history]
            return result
    
    def clear_metrics(self, name: Optional[str] = None) -> None:
        """Clear metrics.
        
        Args:
            name: Specific metric name to clear, or None to clear all
        """
        with self._lock:
            if name:
                if name in self._metrics:
                    self._metrics[name].clear()
                if name in self._counters:
                    del self._counters[name]
                if name in self._gauges:
                    del self._gauges[name]
                if name in self._timers:
                    del self._timers[name]
            else:
                self._metrics.clear()
                self._counters.clear()
                self._gauges.clear()
                self._timers.clear()


class AlertManager:
    """Manager for system alerts and thresholds."""
    
    def __init__(self):
        """Initialize alert manager."""
        self._alerts: Dict[str, Alert] = {}
        self._thresholds: Dict[str, Dict[str, Union[int, float]]] = {}
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.RLock()
    
    def set_threshold(
        self,
        metric_name: str,
        warning_threshold: Optional[Union[int, float]] = None,
        error_threshold: Optional[Union[int, float]] = None,
        critical_threshold: Optional[Union[int, float]] = None
    ) -> None:
        """Set alert thresholds for a metric.
        
        Args:
            metric_name: Name of the metric
            warning_threshold: Warning level threshold
            error_threshold: Error level threshold
            critical_threshold: Critical level threshold
        """
        with self._lock:
            self._thresholds[metric_name] = {}
            if warning_threshold is not None:
                self._thresholds[metric_name]["warning"] = warning_threshold
            if error_threshold is not None:
                self._thresholds[metric_name]["error"] = error_threshold
            if critical_threshold is not None:
                self._thresholds[metric_name]["critical"] = critical_threshold
    
    def check_thresholds(self, metric: MetricValue) -> Optional[Alert]:
        """Check if a metric value exceeds any thresholds.
        
        Args:
            metric: MetricValue to check
            
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        with self._lock:
            if metric.name not in self._thresholds:
                return None
            
            thresholds = self._thresholds[metric.name]
            alert_level = None
            threshold_value = None
            
            # Check thresholds in order of severity
            if "critical" in thresholds and metric.value >= thresholds["critical"]:
                alert_level = AlertLevel.CRITICAL
                threshold_value = thresholds["critical"]
            elif "error" in thresholds and metric.value >= thresholds["error"]:
                alert_level = AlertLevel.ERROR
                threshold_value = thresholds["error"]
            elif "warning" in thresholds and metric.value >= thresholds["warning"]:
                alert_level = AlertLevel.WARNING
                threshold_value = thresholds["warning"]
            
            if alert_level:
                alert_id = f"{metric.name}_{alert_level.value}_{int(time.time())}"
                alert = Alert(
                    id=alert_id,
                    level=alert_level,
                    message=f"{metric.name} exceeded {alert_level.value} threshold",
                    metric_name=metric.name,
                    threshold=threshold_value,
                    current_value=metric.value
                )
                
                self._alerts[alert_id] = alert
                
                # Notify handlers
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception:
                        pass  # Don't let handler errors break alerting
                
                return alert
            
            return None
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function.
        
        Args:
            handler: Function to call when alerts are triggered
        """
        with self._lock:
            self._alert_handlers.append(handler)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts.
        
        Returns:
            List of active Alert objects
        """
        with self._lock:
            return [alert for alert in self._alerts.values() if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            True if alert was resolved, False if not found
        """
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                self._alerts[alert_id].resolved_at = datetime.now()
                return True
            return False


class SystemMonitor:
    """System resource monitor."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize system monitor.
        
        Args:
            metrics_collector: MetricsCollector instance
        """
        self._metrics = metrics_collector
        self._start_time = time.time()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 5.0  # seconds
    
    def start_monitoring(self, interval: float = 5.0) -> None:
        """Start system monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitor_interval = interval
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health metrics.
        
        Returns:
            SystemHealth object with current metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime_seconds = time.time() - self._start_time
            
            return SystemHealth(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                uptime_seconds=uptime_seconds
            )
            
        except Exception:
            # Return default values if psutil fails
            return SystemHealth(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                process_count=0,
                uptime_seconds=time.time() - self._start_time
            )
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                health = self.get_system_health()
                
                # Record system metrics
                self._metrics.set_gauge("system.cpu_percent", health.cpu_percent)
                self._metrics.set_gauge("system.memory_percent", health.memory_percent)
                self._metrics.set_gauge("system.disk_percent", health.disk_percent)
                self._metrics.set_gauge("system.process_count", health.process_count)
                self._metrics.set_gauge("system.uptime_seconds", health.uptime_seconds)
                
                # Record network metrics if available
                if health.network_io:
                    for key, value in health.network_io.items():
                        self._metrics.set_gauge(f"system.network.{key}", value)
                
                time.sleep(self._monitor_interval)
                
            except Exception:
                time.sleep(self._monitor_interval)


class MetricsSystem(SystemComponentBase):
    """Main metrics and monitoring system."""
    
    def __init__(self, config: SystemConfiguration):
        """Initialize metrics system.
        
        Args:
            config: System configuration
        """
        super().__init__(config)
        self._collector = MetricsCollector()
        self._alert_manager = AlertManager()
        self._system_monitor = SystemMonitor(self._collector)
        self._export_path: Optional[Path] = None
        
        # Set up default alert thresholds
        self._setup_default_thresholds()
    
    def initialize(self) -> OperationResult:
        """Initialize the metrics system."""
        try:
            self._logger.info("Initializing Metrics System")
            
            # Set up export path
            self._export_path = Path(self._config.storage_path) / "metrics"
            self._export_path.mkdir(parents=True, exist_ok=True)
            
            # Start system monitoring
            self._system_monitor.start_monitoring()
            
            # Add default alert handler
            self._alert_manager.add_alert_handler(self._log_alert)
            
            self._logger.info("Metrics System initialized successfully")
            return OperationResult(
                success=True,
                message="Metrics System initialized"
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize Metrics System: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def cleanup(self) -> OperationResult:
        """Cleanup the metrics system."""
        try:
            self._logger.info("Cleaning up Metrics System")
            
            # Stop monitoring
            self._system_monitor.stop_monitoring()
            
            # Export final metrics
            self.export_metrics()
            
            self._logger.info("Metrics System cleaned up successfully")
            return OperationResult(
                success=True,
                message="Metrics System cleaned up"
            )
            
        except Exception as e:
            error_msg = f"Failed to cleanup Metrics System: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    @property
    def collector(self) -> MetricsCollector:
        """Get the metrics collector."""
        return self._collector
    
    @property
    def alert_manager(self) -> AlertManager:
        """Get the alert manager."""
        return self._alert_manager
    
    @property
    def system_monitor(self) -> SystemMonitor:
        """Get the system monitor."""
        return self._system_monitor
    
    def record_operation(self, operation_name: str, success: bool, duration: float) -> None:
        """Record an operation metric.
        
        Args:
            operation_name: Name of the operation
            success: Whether the operation succeeded
            duration: Operation duration in seconds
        """
        # Record operation count
        self._collector.increment(f"operations.{operation_name}.total")
        
        # Record success/failure
        if success:
            self._collector.increment(f"operations.{operation_name}.success")
        else:
            self._collector.increment(f"operations.{operation_name}.failure")
        
        # Record duration
        self._collector.record_timer(f"operations.{operation_name}.duration", duration)
        
        # Check for alerts
        duration_metric = MetricValue(
            name=f"operations.{operation_name}.duration",
            value=duration,
            metric_type=MetricType.TIMER
        )
        self._alert_manager.check_thresholds(duration_metric)
    
    def export_metrics(self, filename: Optional[str] = None) -> OperationResult:
        """Export metrics to JSON file.
        
        Args:
            filename: Optional filename for export
            
        Returns:
            OperationResult indicating success/failure
        """
        try:
            if not self._export_path:
                return OperationResult(
                    success=False,
                    error="Export path not configured"
                )
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metrics_{timestamp}.json"
            
            export_file = self._export_path / filename
            
            # Collect all data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self._collector.get_all_metrics(),
                "alerts": [alert.to_dict() for alert in self._alert_manager.get_active_alerts()],
                "system_health": self._system_monitor.get_system_health().to_dict()
            }
            
            # Write to file
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Metrics exported to: {export_file}")
            return OperationResult(
                success=True,
                message=f"Metrics exported to {export_file}",
                data=str(export_file)
            )
            
        except Exception as e:
            error_msg = f"Failed to export metrics: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def _setup_default_thresholds(self) -> None:
        """Set up default alert thresholds."""
        # System resource thresholds
        self._alert_manager.set_threshold(
            "system.cpu_percent",
            warning_threshold=70.0,
            error_threshold=85.0,
            critical_threshold=95.0
        )
        
        self._alert_manager.set_threshold(
            "system.memory_percent",
            warning_threshold=75.0,
            error_threshold=90.0,
            critical_threshold=98.0
        )
        
        self._alert_manager.set_threshold(
            "system.disk_percent",
            warning_threshold=80.0,
            error_threshold=90.0,
            critical_threshold=95.0
        )
        
        # Operation duration thresholds (in seconds)
        operation_types = [
            "download", "install", "detection", "analysis",
            "validation", "storage", "integration"
        ]
        
        for op_type in operation_types:
            self._alert_manager.set_threshold(
                f"operations.{op_type}.duration",
                warning_threshold=30.0,
                error_threshold=60.0,
                critical_threshold=120.0
            )
    
    def _log_alert(self, alert: Alert) -> None:
        """Default alert handler that logs alerts.
        
        Args:
            alert: Alert to log
        """
        level_map = {
            AlertLevel.INFO: self._logger.info,
            AlertLevel.WARNING: self._logger.warning,
            AlertLevel.ERROR: self._logger.error,
            AlertLevel.CRITICAL: self._logger.critical
        }
        
        log_func = level_map.get(alert.level, self._logger.info)
        log_func(
            f"ALERT [{alert.level.value.upper()}]: {alert.message} "
            f"(Current: {alert.current_value}, Threshold: {alert.threshold})"
        )


# Decorators for automatic metrics collection

def timed(metric_name: Optional[str] = None, metrics_system: Optional[MetricsSystem] = None):
    """Decorator to automatically time function execution.
    
    Args:
        metric_name: Optional custom metric name
        metrics_system: Optional MetricsSystem instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                name = metric_name or f"function.{func.__name__}"
                
                if metrics_system:
                    metrics_system.record_operation(name, success, duration)
                
        return wrapper
    return decorator


@contextmanager
def measure_time(metric_name: str, metrics_system: MetricsSystem):
    """Context manager to measure execution time.
    
    Args:
        metric_name: Name of the metric
        metrics_system: MetricsSystem instance
    """
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        metrics_system.record_operation(metric_name, success, duration)