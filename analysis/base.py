"""
Base classes for analysis components.
"""

from abc import ABC
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.base import SystemComponentBase, OperationResult
from ..core.exceptions import ArchitectureAnalysisError
from .interfaces import (
    ArchitectureAnalysisInterface,
    GapAnalysisInterface, 
    CodeConsistencyAnalyzerInterface,
    CriticalityLevel
)


class AnalysisBase(SystemComponentBase, ABC):
    """
    Base class for all analysis components.
    
    Provides common functionality for architecture analysis,
    gap detection, and consistency checking.
    """
    
    def __init__(self, config_manager, component_name: Optional[str] = None):
        """Initialize analysis base component."""
        super().__init__(config_manager, component_name)
        self._analysis_cache: Dict[str, Any] = {}
        self._last_analysis_time: Optional[datetime] = None
    
    def validate_configuration(self) -> None:
        """Validate analysis-specific configuration."""
        config = self.get_config()
        
        # Validate analysis-specific settings
        if not hasattr(config, 'debug_mode'):
            raise ArchitectureAnalysisError(
                "Missing debug_mode configuration",
                context={"component": self._component_name}
            )
    
    def _cache_analysis_result(self, key: str, result: Any) -> None:
        """Cache analysis result for reuse."""
        self._analysis_cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    def _get_cached_result(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """Get cached analysis result if still valid."""
        if key not in self._analysis_cache:
            return None
        
        cached = self._analysis_cache[key]
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        
        if age <= max_age_seconds:
            return cached["result"]
        
        # Remove expired cache entry
        del self._analysis_cache[key]
        return None
    
    def _prioritize_by_criticality_level(
        self, 
        items: List[Any], 
        get_criticality_func
    ) -> List[Any]:
        """
        Prioritize items by criticality level.
        
        Args:
            items: List of items to prioritize
            get_criticality_func: Function to extract criticality from item
            
        Returns:
            List of items sorted by criticality (security > stability > functionality > UX)
        """
        criticality_order = {
            CriticalityLevel.SECURITY: 0,
            CriticalityLevel.STABILITY: 1,
            CriticalityLevel.FUNCTIONALITY: 2,
            CriticalityLevel.UX: 3,
        }
        
        return sorted(
            items,
            key=lambda item: criticality_order.get(get_criticality_func(item), 999)
        )
    
    def _calculate_compliance_score(
        self, 
        total_items: int, 
        compliant_items: int
    ) -> float:
        """
        Calculate compliance score as percentage.
        
        Args:
            total_items: Total number of items checked
            compliant_items: Number of compliant items
            
        Returns:
            Compliance score between 0.0 and 1.0
        """
        if total_items == 0:
            return 1.0
        
        return min(1.0, max(0.0, compliant_items / total_items))
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self._analysis_cache.clear()
        self._logger.info("Analysis cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about analysis cache."""
        return {
            "cache_entries": len(self._analysis_cache),
            "cache_keys": list(self._analysis_cache.keys()),
            "last_analysis_time": self._last_analysis_time.isoformat() if self._last_analysis_time else None,
        }