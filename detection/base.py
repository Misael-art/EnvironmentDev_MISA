"""
Base classes for detection components.
"""

from abc import ABC
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import os

from ..core.base import SystemComponentBase, OperationResult
from ..core.exceptions import UnifiedDetectionError
from .interfaces import (
    DetectionEngineInterface,
    RuntimeDetectorInterface,
    HierarchicalDetectionInterface,
    DetectionResult,
    DetectionMethod,
    DetectionConfidence
)


class DetectionBase(SystemComponentBase, ABC):
    """
    Base class for all detection components.
    
    Provides common functionality for application detection,
    runtime detection, and hierarchical prioritization.
    """
    
    def __init__(self, config_manager, component_name: Optional[str] = None):
        """Initialize detection base component."""
        super().__init__(config_manager, component_name)
        self._detection_cache: Dict[str, Any] = {}
        self._last_detection_time: Optional[datetime] = None
        self._detection_methods_available: List[DetectionMethod] = []
    
    def validate_configuration(self) -> None:
        """Validate detection-specific configuration."""
        config = self.get_config()
        
        # Validate detection-specific settings
        if not hasattr(config, 'detection_cache_enabled'):
            raise UnifiedDetectionError(
                "Missing detection_cache_enabled configuration",
                context={"component": self._component_name}
            )
        
        if not hasattr(config, 'hierarchical_detection_enabled'):
            raise UnifiedDetectionError(
                "Missing hierarchical_detection_enabled configuration",
                context={"component": self._component_name}
            )
    
    def _cache_detection_result(self, key: str, result: Any) -> None:
        """Cache detection result for reuse."""
        if self.get_config().detection_cache_enabled:
            self._detection_cache[key] = {
                "result": result,
                "timestamp": datetime.now()
            }
    
    def _get_cached_detection(self, key: str) -> Optional[Any]:
        """Get cached detection result if still valid."""
        if not self.get_config().detection_cache_enabled:
            return None
        
        if key not in self._detection_cache:
            return None
        
        cached = self._detection_cache[key]
        cache_ttl = self.get_config().detection_cache_ttl
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        
        if age <= cache_ttl:
            return cached["result"]
        
        # Remove expired cache entry
        del self._detection_cache[key]
        return None
    
    def _execute_command_safely(
        self, 
        command: List[str], 
        timeout: int = 30
    ) -> Optional[str]:
        """
        Execute command safely and return output.
        
        Args:
            command: Command to execute as list of strings
            timeout: Timeout in seconds
            
        Returns:
            Command output or None if failed
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self._logger.debug(
                    f"Command failed: {' '.join(command)}, "
                    f"return code: {result.returncode}, "
                    f"stderr: {result.stderr}"
                )
                return None
                
        except subprocess.TimeoutExpired:
            self._logger.warning(f"Command timed out: {' '.join(command)}")
            return None
        except Exception as e:
            self._logger.debug(f"Command execution failed: {' '.join(command)}, error: {str(e)}")
            return None
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if file exists safely."""
        try:
            return os.path.isfile(file_path)
        except Exception:
            return False
    
    def _check_directory_exists(self, dir_path: str) -> bool:
        """Check if directory exists safely."""
        try:
            return os.path.isdir(dir_path)
        except Exception:
            return False
    
    def _get_environment_variable(self, var_name: str) -> Optional[str]:
        """Get environment variable safely."""
        try:
            return os.environ.get(var_name)
        except Exception:
            return None
    
    def _determine_detection_confidence(
        self, 
        detection_methods_used: List[DetectionMethod],
        validation_results: Dict[str, bool]
    ) -> DetectionConfidence:
        """
        Determine detection confidence based on methods and validation.
        
        Args:
            detection_methods_used: List of detection methods that succeeded
            validation_results: Results of validation commands
            
        Returns:
            DetectionConfidence: Calculated confidence level
        """
        # Calculate confidence based on multiple factors
        confidence_score = 0.0
        
        # Method-based confidence
        method_weights = {
            DetectionMethod.REGISTRY: 0.3,
            DetectionMethod.FILESYSTEM: 0.2,
            DetectionMethod.ENVIRONMENT_VARIABLES: 0.2,
            DetectionMethod.COMMAND_LINE: 0.3,
            DetectionMethod.DMI_SMBIOS: 0.4,
            DetectionMethod.STEAM_CLIENT: 0.2,
            DetectionMethod.MANUAL_CONFIG: 0.1,
        }
        
        for method in detection_methods_used:
            confidence_score += method_weights.get(method, 0.1)
        
        # Validation-based confidence
        if validation_results:
            validation_success_rate = sum(validation_results.values()) / len(validation_results)
            confidence_score += validation_success_rate * 0.4
        
        # Normalize and categorize
        confidence_score = min(1.0, confidence_score)
        
        if confidence_score >= 0.8:
            return DetectionConfidence.HIGH
        elif confidence_score >= 0.5:
            return DetectionConfidence.MEDIUM
        elif confidence_score >= 0.2:
            return DetectionConfidence.LOW
        else:
            return DetectionConfidence.UNKNOWN
    
    def _create_detection_result(
        self,
        detected: bool,
        method: DetectionMethod,
        details: Dict[str, Any],
        validation_results: Optional[Dict[str, bool]] = None
    ) -> DetectionResult:
        """
        Create standardized detection result.
        
        Args:
            detected: Whether detection was successful
            method: Primary detection method used
            details: Additional details about detection
            validation_results: Optional validation results
            
        Returns:
            DetectionResult: Standardized detection result
        """
        confidence = self._determine_detection_confidence(
            [method] if detected else [],
            validation_results or {}
        )
        
        return DetectionResult(
            detected=detected,
            confidence=confidence,
            method=method,
            details=details,
            timestamp=datetime.now()
        )
    
    def _prioritize_by_confidence(
        self, 
        results: List[DetectionResult]
    ) -> List[DetectionResult]:
        """
        Prioritize detection results by confidence level.
        
        Args:
            results: List of detection results to prioritize
            
        Returns:
            List[DetectionResult]: Results sorted by confidence (high to low)
        """
        confidence_order = {
            DetectionConfidence.HIGH: 0,
            DetectionConfidence.MEDIUM: 1,
            DetectionConfidence.LOW: 2,
            DetectionConfidence.UNKNOWN: 3,
        }
        
        return sorted(
            results,
            key=lambda result: confidence_order.get(result.confidence, 999)
        )
    
    def clear_detection_cache(self) -> None:
        """Clear detection cache."""
        self._detection_cache.clear()
        self._logger.info("Detection cache cleared")
    
    def get_detection_cache_info(self) -> Dict[str, Any]:
        """Get information about detection cache."""
        return {
            "cache_enabled": self.get_config().detection_cache_enabled,
            "cache_entries": len(self._detection_cache),
            "cache_keys": list(self._detection_cache.keys()),
            "last_detection_time": self._last_detection_time.isoformat() if self._last_detection_time else None,
            "available_methods": [method.value for method in self._detection_methods_available],
        }
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "total_detections_performed": self._operation_count,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "average_detection_time": self._calculate_average_detection_time(),
            "detection_success_rate": self._calculate_detection_success_rate(),
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # This would be implemented with actual cache hit tracking
        return 0.0
    
    def _calculate_average_detection_time(self) -> float:
        """Calculate average detection time."""
        # This would be implemented with actual timing tracking
        return 0.0
    
    def _calculate_detection_success_rate(self) -> float:
        """Calculate detection success rate."""
        # This would be implemented with actual success tracking
        return 0.0