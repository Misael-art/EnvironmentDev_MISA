"""
Base classes for validation components.
"""

from abc import ABC
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
import networkx as nx

from core.base import SystemComponentBase, OperationResult
from core.exceptions import DependencyValidationError
from .interfaces import (
    DependencyValidatorInterface,
    ConflictDetectorInterface,
    DependencyGraphAnalyzerInterface,
    DependencyGraph,
    DependencyNode,
    DependencyEdge,
    VersionConflict,
    CircularDependency,
    ConflictType,
    ResolutionStrategy
)


class ValidationBase(SystemComponentBase, ABC):
    """
    Base class for all validation components.
    
    Provides common functionality for dependency validation,
    conflict detection, and graph analysis.
    """
    
    def __init__(self, config_manager, component_name: Optional[str] = None):
        """Initialize validation base component."""
        super().__init__(config_manager, component_name)
        self._validation_cache: Dict[str, Any] = {}
        self._dependency_graphs: Dict[str, DependencyGraph] = {}
        self._last_validation_time: Optional[datetime] = None
        self._conflict_history: List[VersionConflict] = []
    
    def validate_configuration(self) -> None:
        """Validate validation-specific configuration."""
        config = self.get_config()
        
        # Validate validation-specific settings
        if not hasattr(config, 'operation_timeout'):
            raise DependencyValidationError(
                "Missing operation_timeout configuration",
                context={"component": self._component_name}
            )
    
    def _cache_validation_result(self, key: str, result: Any) -> None:
        """Cache validation result for reuse."""
        self._validation_cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    def _get_cached_validation(self, key: str, max_age_seconds: int = 1800) -> Optional[Any]:
        """Get cached validation result if still valid."""
        if key not in self._validation_cache:
            return None
        
        cached = self._validation_cache[key]
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        
        if age <= max_age_seconds:
            return cached["result"]
        
        # Remove expired cache entry
        del self._validation_cache[key]
        return None
    
    def _create_networkx_graph(self, dependency_graph: DependencyGraph) -> nx.DiGraph:
        """
        Create NetworkX graph from dependency graph for analysis.
        
        Args:
            dependency_graph: Dependency graph to convert
            
        Returns:
            nx.DiGraph: NetworkX directed graph
        """
        graph = nx.DiGraph()
        
        # Add nodes
        for node in dependency_graph.nodes:
            graph.add_node(
                node.name,
                version=node.version,
                is_essential=node.is_essential,
                installation_path=node.installation_path,
                metadata=node.metadata
            )
        
        # Add edges
        for edge in dependency_graph.edges:
            graph.add_edge(
                edge.from_node,
                edge.to_node,
                version_constraint=edge.version_constraint,
                is_optional=edge.is_optional,
                conflict_detected=edge.conflict_detected
            )
        
        return graph
    
    def _find_cycles_in_graph(self, graph: nx.DiGraph) -> List[List[str]]:
        """
        Find all cycles in a directed graph.
        
        Args:
            graph: NetworkX directed graph
            
        Returns:
            List[List[str]]: List of cycles
        """
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except Exception as e:
            self._logger.warning(f"Error finding cycles: {str(e)}")
            return []
    
    def _calculate_shortest_path(
        self, 
        graph: nx.DiGraph, 
        source: str, 
        target: str
    ) -> Optional[List[str]]:
        """
        Calculate shortest path between two nodes.
        
        Args:
            graph: NetworkX directed graph
            source: Source node name
            target: Target node name
            
        Returns:
            Optional[List[str]]: Shortest path or None if no path exists
        """
        try:
            if nx.has_path(graph, source, target):
                return nx.shortest_path(graph, source, target)
            return None
        except Exception as e:
            self._logger.warning(f"Error calculating shortest path: {str(e)}")
            return None
    
    def _analyze_node_centrality(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Analyze node centrality to identify critical dependencies.
        
        Args:
            graph: NetworkX directed graph
            
        Returns:
            Dict[str, float]: Mapping of node names to centrality scores
        """
        try:
            # Use betweenness centrality to identify critical nodes
            centrality = nx.betweenness_centrality(graph)
            return centrality
        except Exception as e:
            self._logger.warning(f"Error calculating centrality: {str(e)}")
            return {}
    
    def _parse_version_string(self, version: str) -> Tuple[int, ...]:
        """
        Parse version string into comparable tuple.
        
        Args:
            version: Version string (e.g., "1.2.3")
            
        Returns:
            Tuple[int, ...]: Parsed version tuple
        """
        try:
            # Remove common prefixes and suffixes
            clean_version = version.strip().lstrip('v').split('-')[0].split('+')[0]
            
            # Split by dots and convert to integers
            parts = []
            for part in clean_version.split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    # Handle non-numeric parts
                    parts.append(0)
            
            return tuple(parts)
        except Exception:
            # Return default version if parsing fails
            return (0, 0, 0)
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1_tuple = self._parse_version_string(version1)
        v2_tuple = self._parse_version_string(version2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0
    
    def _is_version_compatible(
        self, 
        required_version: str, 
        available_version: str,
        constraint: str = ">=",
    ) -> bool:
        """
        Check if available version satisfies required version constraint.
        
        Args:
            required_version: Required version string
            available_version: Available version string
            constraint: Version constraint operator (>=, <=, ==, !=, >, <)
            
        Returns:
            bool: True if compatible, False otherwise
        """
        try:
            comparison = self._compare_versions(available_version, required_version)
            
            if constraint == ">=":
                return comparison >= 0
            elif constraint == "<=":
                return comparison <= 0
            elif constraint == "==":
                return comparison == 0
            elif constraint == "!=":
                return comparison != 0
            elif constraint == ">":
                return comparison > 0
            elif constraint == "<":
                return comparison < 0
            else:
                # Default to >= if constraint is unknown
                return comparison >= 0
                
        except Exception as e:
            self._logger.warning(f"Error comparing versions: {str(e)}")
            return False
    
    def _calculate_dependency_depth(
        self, 
        graph: nx.DiGraph, 
        start_node: str
    ) -> Dict[str, int]:
        """
        Calculate dependency depth from a starting node.
        
        Args:
            graph: NetworkX directed graph
            start_node: Starting node name
            
        Returns:
            Dict[str, int]: Mapping of node names to their depth levels
        """
        try:
            if start_node not in graph:
                return {}
            
            depths = {}
            visited = set()
            queue = [(start_node, 0)]
            
            while queue:
                node, depth = queue.pop(0)
                
                if node in visited:
                    continue
                
                visited.add(node)
                depths[node] = depth
                
                # Add successors with increased depth
                for successor in graph.successors(node):
                    if successor not in visited:
                        queue.append((successor, depth + 1))
            
            return depths
            
        except Exception as e:
            self._logger.warning(f"Error calculating dependency depth: {str(e)}")
            return {}
    
    def _generate_conflict_id(self, component: str, conflict_type: ConflictType) -> str:
        """Generate unique conflict ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{conflict_type.value}_{component}_{timestamp}"
    
    def _assess_conflict_severity(self, conflict: VersionConflict) -> str:
        """
        Assess severity of a version conflict.
        
        Args:
            conflict: Version conflict to assess
            
        Returns:
            str: Severity level (critical, high, medium, low)
        """
        # Assess based on number of conflicting dependencies and version differences
        num_conflicts = len(conflict.conflicting_dependencies)
        
        if num_conflicts >= 5:
            return "critical"
        elif num_conflicts >= 3:
            return "high"
        elif num_conflicts >= 2:
            return "medium"
        else:
            return "low"
    
    def clear_validation_cache(self) -> None:
        """Clear validation cache."""
        self._validation_cache.clear()
        self._dependency_graphs.clear()
        self._logger.info("Validation cache cleared")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations_performed": self._operation_count,
            "cached_dependency_graphs": len(self._dependency_graphs),
            "conflict_history_count": len(self._conflict_history),
            "last_validation_time": self._last_validation_time.isoformat() if self._last_validation_time else None,
            "cache_entries": len(self._validation_cache),
        }
    
    def get_conflict_history(self) -> List[Dict[str, Any]]:
        """Get history of detected conflicts."""
        return [
            {
                "conflict_id": conflict.conflict_id,
                "component": conflict.component_name,
                "severity": conflict.severity,
                "required_versions": conflict.required_versions,
                "current_version": conflict.current_version,
            }
            for conflict in self._conflict_history
        ]