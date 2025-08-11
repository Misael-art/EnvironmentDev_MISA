"""
Interfaces for architecture analysis and gap detection components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..core.base import SystemComponentBase, OperationResult


class CriticalityLevel(Enum):
    """Criticality levels for gaps and issues."""
    SECURITY = "security"
    STABILITY = "stability" 
    FUNCTIONALITY = "functionality"
    UX = "ux"


@dataclass
class ArchitectureAnalysis:
    """Result of architecture analysis."""
    current_architecture: Dict[str, Any]
    design_architecture: Dict[str, Any]
    identified_gaps: List['CriticalGap']
    lost_functionalities: List['LostFunctionality']
    consistency_issues: List['ConsistencyIssue']
    prioritized_fixes: List['PrioritizedFix']
    analysis_timestamp: datetime


@dataclass
class CriticalGap:
    """Represents a critical gap in the architecture."""
    gap_id: str
    description: str
    criticality: CriticalityLevel
    affected_components: List[str]
    impact_assessment: str
    recommended_action: str
    estimated_effort: str


@dataclass
class LostFunctionality:
    """Represents functionality that was lost during refactoring."""
    functionality_id: str
    name: str
    description: str
    original_location: str
    last_seen_version: Optional[str]
    impact_on_users: str
    recovery_complexity: str


@dataclass
class ConsistencyIssue:
    """Represents inconsistency between requirements documents."""
    issue_id: str
    description: str
    conflicting_documents: List[str]
    conflicting_requirements: List[str]
    severity: str
    resolution_suggestion: str


@dataclass
class PrioritizedFix:
    """Represents a prioritized fix for identified issues."""
    fix_id: str
    description: str
    priority: int
    criticality: CriticalityLevel
    estimated_effort: str
    dependencies: List[str]
    success_criteria: List[str]


@dataclass
class ComparisonResult:
    """Result of comparing current implementation with design."""
    matches: List[str]
    missing_components: List[str]
    extra_components: List[str]
    architectural_differences: List[str]
    compliance_score: float


@dataclass
class GapAnalysisReport:
    """Comprehensive gap analysis report."""
    report_id: str
    generation_timestamp: datetime
    total_gaps_identified: int
    gaps_by_criticality: Dict[CriticalityLevel, int]
    detailed_gaps: List[CriticalGap]
    recommendations: List[str]
    next_steps: List[str]


@dataclass
class ConsistencyResult:
    """Result of requirements consistency validation."""
    is_consistent: bool
    total_requirements_checked: int
    consistency_issues: List[ConsistencyIssue]
    consistency_score: float
    recommendations: List[str]


class ArchitectureAnalysisInterface(SystemComponentBase, ABC):
    """
    Interface for architecture analysis operations.
    
    Defines the contract for analyzing current architecture,
    comparing with design documents, and identifying gaps.
    """
    
    @abstractmethod
    def analyze_current_architecture(self) -> ArchitectureAnalysis:
        """
        Analyze the current system architecture.
        
        Returns:
            ArchitectureAnalysis: Complete analysis of current architecture
        """
        pass
    
    @abstractmethod
    def compare_with_design_documents(self, design_paths: List[str]) -> ComparisonResult:
        """
        Compare current implementation with design documents.
        
        Args:
            design_paths: Paths to design documents to compare against
            
        Returns:
            ComparisonResult: Detailed comparison results
        """
        pass
    
    @abstractmethod
    def identify_critical_gaps(self) -> List[CriticalGap]:
        """
        Identify critical gaps in the current implementation.
        
        Returns:
            List[CriticalGap]: List of identified critical gaps
        """
        pass
    
    @abstractmethod
    def map_lost_functionalities(self) -> List[LostFunctionality]:
        """
        Map functionalities that were lost during refactoring.
        
        Returns:
            List[LostFunctionality]: List of lost functionalities
        """
        pass
    
    @abstractmethod
    def prioritize_by_criticality(self, gaps: List[CriticalGap]) -> List[PrioritizedFix]:
        """
        Prioritize gaps by criticality level.
        
        Args:
            gaps: List of gaps to prioritize
            
        Returns:
            List[PrioritizedFix]: Prioritized list of fixes
        """
        pass


class GapAnalysisInterface(SystemComponentBase, ABC):
    """
    Interface for gap analysis and documentation operations.
    
    Defines the contract for generating comprehensive gap analysis
    reports and documentation.
    """
    
    @abstractmethod
    def generate_gap_analysis_report(self) -> GapAnalysisReport:
        """
        Generate comprehensive gap analysis report.
        
        Returns:
            GapAnalysisReport: Detailed gap analysis report
        """
        pass
    
    @abstractmethod
    def validate_requirements_consistency(self, req_files: List[str]) -> ConsistencyResult:
        """
        Validate consistency between multiple requirements documents.
        
        Args:
            req_files: List of requirements file paths to validate
            
        Returns:
            ConsistencyResult: Results of consistency validation
        """
        pass
    
    @abstractmethod
    def document_architectural_differences(
        self, 
        current: Dict[str, Any], 
        proposed: Dict[str, Any]
    ) -> OperationResult:
        """
        Document differences between current and proposed architecture.
        
        Args:
            current: Current architecture representation
            proposed: Proposed architecture representation
            
        Returns:
            OperationResult: Result of documentation operation
        """
        pass
    
    @abstractmethod
    def generate_prioritized_action_plan(
        self, 
        gaps: List[CriticalGap]
    ) -> OperationResult:
        """
        Generate prioritized action plan for addressing gaps.
        
        Args:
            gaps: List of critical gaps to address
            
        Returns:
            OperationResult: Result containing action plan
        """
        pass


class CodeConsistencyAnalyzerInterface(SystemComponentBase, ABC):
    """
    Interface for code consistency analysis operations.
    
    Defines the contract for analyzing code consistency across
    the system and identifying inconsistencies.
    """
    
    @abstractmethod
    def analyze_code_consistency(self, code_paths: List[str]) -> OperationResult:
        """
        Analyze code consistency across specified paths.
        
        Args:
            code_paths: List of code paths to analyze
            
        Returns:
            OperationResult: Results of consistency analysis
        """
        pass
    
    @abstractmethod
    def identify_naming_inconsistencies(self) -> List[str]:
        """
        Identify naming inconsistencies in the codebase.
        
        Returns:
            List[str]: List of identified naming inconsistencies
        """
        pass
    
    @abstractmethod
    def validate_architectural_patterns(self) -> OperationResult:
        """
        Validate adherence to architectural patterns.
        
        Returns:
            OperationResult: Results of pattern validation
        """
        pass
    
    @abstractmethod
    def check_interface_compliance(self) -> OperationResult:
        """
        Check compliance with defined interfaces.
        
        Returns:
            OperationResult: Results of interface compliance check
        """
        pass