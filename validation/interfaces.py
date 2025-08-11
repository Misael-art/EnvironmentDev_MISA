"""
Interfaces for dependency validation and conflict detection components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from core.base import SystemComponentBase, OperationResult


class ConflictType(Enum):
    """Types of dependency conflicts."""
    VERSION_CONFLICT = "version_conflict"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_DEPENDENCY = "missing_dependency"
    INCOMPATIBLE_VERSIONS = "incompatible_versions"
    DUPLICATE_DEPENDENCY = "duplicate_dependency"


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    UPDATE_TO_LATEST = "update_to_latest"
    DOWNGRADE_TO_COMPATIBLE = "downgrade_to_compatible"
    USE_ALTERNATIVE = "use_alternative"
    REMOVE_CONFLICTING = "remove_conflicting"
    MANUAL_RESOLUTION = "manual_resolution"


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    name: str
    version: str
    dependencies: List[str]
    dependents: List[str]
    is_essential: bool
    installation_path: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class DependencyEdge:
    """Represents an edge in the dependency graph."""
    from_node: str
    to_node: str
    version_constraint: str
    is_optional: bool
    conflict_detected: bool


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph."""
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    direct_dependencies: Dict[str, List[str]]
    transitive_dependencies: Dict[str, List[str]]
    version_conflicts: List['VersionConflict']
    circular_dependencies: List['CircularDependency']
    resolution_path: Optional['ResolutionPath']


@dataclass
class VersionConflict:
    """Represents a version conflict between dependencies."""
    conflict_id: str
    component_name: str
    required_versions: List[str]
    current_version: Optional[str]
    conflicting_dependencies: List[str]
    severity: str
    resolution_suggestions: List[str]


@dataclass
class CircularDependency:
    """Represents a circular dependency."""
    cycle_id: str
    components_in_cycle: List[str]
    cycle_path: List[str]
    break_suggestions: List[str]
    impact_assessment: str


@dataclass
class ResolutionPath:
    """Represents a path to resolve dependency conflicts."""
    path_id: str
    steps: List['ResolutionStep']
    estimated_time: int
    success_probability: float
    risks: List[str]
    alternatives: List['AlternativePath']


@dataclass
class ResolutionStep:
    """Represents a single step in conflict resolution."""
    step_id: str
    action: str
    component: str
    from_version: Optional[str]
    to_version: Optional[str]
    strategy: ResolutionStrategy
    dependencies: List[str]
    validation_commands: List[str]


@dataclass
class AlternativePath:
    """Represents an alternative resolution path."""
    path_id: str
    description: str
    components_affected: List[str]
    trade_offs: List[str]
    compatibility_score: float


@dataclass
class CompatibilityResult:
    """Result of contextual compatibility validation."""
    is_compatible: bool
    compatibility_score: float
    incompatible_components: List[str]
    suggestions: List[str]
    required_updates: List[str]
    required_downgrades: List[str]
    alternatives: List[str]


@dataclass
class DependencyAnalysisResult:
    """Result of comprehensive dependency analysis."""
    analysis_id: str
    timestamp: datetime
    total_components: int
    total_dependencies: int
    conflicts_detected: int
    circular_dependencies_detected: int
    resolution_paths_available: int
    overall_health_score: float
    recommendations: List[str]


class DependencyValidatorInterface(SystemComponentBase, ABC):
    """
    Interface for dependency validation operations.
    
    Defines the contract for creating dependency graphs,
    analyzing dependencies, and detecting conflicts.
    """
    
    @abstractmethod
    def create_dependency_graph(self, components: List[str]) -> DependencyGraph:
        """
        Create dependency graph for specified components.
        
        Args:
            components: List of component names to analyze
            
        Returns:
            DependencyGraph: Complete dependency graph
        """
        pass
    
    @abstractmethod
    def analyze_direct_dependencies(self, component: str) -> List[str]:
        """
        Analyze direct dependencies of a component.
        
        Args:
            component: Component name to analyze
            
        Returns:
            List[str]: List of direct dependencies
        """
        pass
    
    @abstractmethod
    def analyze_transitive_dependencies(self, component: str) -> List[str]:
        """
        Analyze transitive dependencies of a component.
        
        Args:
            component: Component name to analyze
            
        Returns:
            List[str]: List of transitive dependencies
        """
        pass
    
    @abstractmethod
    def validate_contextual_compatibility(self, component: str) -> CompatibilityResult:
        """
        Validate contextual compatibility of a component.
        
        Args:
            component: Component name to validate
            
        Returns:
            CompatibilityResult: Compatibility validation results
        """
        pass
    
    @abstractmethod
    def suggest_alternatives(self, conflicts: List[VersionConflict]) -> List[str]:
        """
        Suggest alternatives for conflicting dependencies.
        
        Args:
            conflicts: List of version conflicts
            
        Returns:
            List[str]: List of alternative suggestions
        """
        pass
    
    @abstractmethod
    def generate_dependency_report(self) -> DependencyAnalysisResult:
        """
        Generate comprehensive dependency analysis report.
        
        Returns:
            DependencyAnalysisResult: Complete dependency analysis
        """
        pass


class ConflictDetectorInterface(SystemComponentBase, ABC):
    """
    Interface for conflict detection operations.
    
    Defines the contract for detecting version conflicts,
    circular dependencies, and calculating resolution paths.
    """
    
    @abstractmethod
    def detect_version_conflicts(self, components: List[str]) -> List[VersionConflict]:
        """
        Detect version conflicts between components.
        
        Args:
            components: List of components to check for conflicts
            
        Returns:
            List[VersionConflict]: List of detected version conflicts
        """
        pass
    
    @abstractmethod
    def detect_circular_dependencies(self, components: List[str]) -> List[CircularDependency]:
        """
        Detect circular dependencies in component graph.
        
        Args:
            components: List of components to check
            
        Returns:
            List[CircularDependency]: List of detected circular dependencies
        """
        pass
    
    @abstractmethod
    def calculate_resolution_path(self, conflicts: List[VersionConflict]) -> ResolutionPath:
        """
        Calculate shortest path to resolve conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            
        Returns:
            ResolutionPath: Calculated resolution path
        """
        pass
    
    @abstractmethod
    def find_shortest_resolution_path(
        self, 
        conflicts: List[VersionConflict]
    ) -> Optional[ResolutionPath]:
        """
        Find shortest path to resolve all conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            
        Returns:
            Optional[ResolutionPath]: Shortest resolution path or None
        """
        pass
    
    @abstractmethod
    def identify_critical_dependencies(
        self, 
        graph: DependencyGraph
    ) -> List[str]:
        """
        Identify critical dependencies in the graph.
        
        Args:
            graph: Dependency graph to analyze
            
        Returns:
            List[str]: List of critical dependency names
        """
        pass
    
    @abstractmethod
    def optimize_installation_order(self, components: List[str]) -> List[str]:
        """
        Optimize installation order to minimize conflicts.
        
        Args:
            components: List of components to order
            
        Returns:
            List[str]: Optimized installation order
        """
        pass


class DependencyGraphAnalyzerInterface(SystemComponentBase, ABC):
    """
    Interface for dependency graph analysis operations.
    
    Defines the contract for analyzing dependency graphs,
    visualizing relationships, and optimizing dependency resolution.
    """
    
    @abstractmethod
    def visualize_dependencies(self, graph: DependencyGraph) -> OperationResult:
        """
        Create visualization of dependency graph.
        
        Args:
            graph: Dependency graph to visualize
            
        Returns:
            OperationResult: Result containing visualization data
        """
        pass
    
    @abstractmethod
    def analyze_dependency_depth(self, component: str) -> Dict[str, int]:
        """
        Analyze dependency depth for a component.
        
        Args:
            component: Component to analyze
            
        Returns:
            Dict[str, int]: Mapping of dependencies to their depth levels
        """
        pass
    
    @abstractmethod
    def find_dependency_cycles(self, graph: DependencyGraph) -> List[List[str]]:
        """
        Find all cycles in the dependency graph.
        
        Args:
            graph: Dependency graph to analyze
            
        Returns:
            List[List[str]]: List of cycles, each cycle is a list of component names
        """
        pass
    
    @abstractmethod
    def calculate_impact_analysis(
        self, 
        component: str, 
        change_type: str
    ) -> Dict[str, Any]:
        """
        Calculate impact of changes to a component.
        
        Args:
            component: Component being changed
            change_type: Type of change (update, remove, etc.)
            
        Returns:
            Dict[str, Any]: Impact analysis results
        """
        pass
    
    @abstractmethod
    def suggest_dependency_optimizations(
        self, 
        graph: DependencyGraph
    ) -> List[str]:
        """
        Suggest optimizations for the dependency graph.
        
        Args:
            graph: Dependency graph to optimize
            
        Returns:
            List[str]: List of optimization suggestions
        """
        pass
    
    @abstractmethod
    def validate_graph_integrity(self, graph: DependencyGraph) -> OperationResult:
        """
        Validate integrity of dependency graph.
        
        Args:
            graph: Dependency graph to validate
            
        Returns:
            OperationResult: Validation results
        """
        pass