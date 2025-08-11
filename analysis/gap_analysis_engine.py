"""
Gap Analysis Engine implementation.

This module provides the GapAnalysisEngine class that handles gap identification,
criticality prioritization, and comprehensive documentation generation.
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .base import AnalysisBase
from .interfaces import (
    GapAnalysisInterface,
    GapAnalysisReport,
    CriticalGap,
    CriticalityLevel,
    ConsistencyResult,
    ConsistencyIssue
)
from ..core.base import OperationResult
from ..core.exceptions import ArchitectureAnalysisError


class GapAnalysisEngine(AnalysisBase, GapAnalysisInterface):
    """
    Engine for comprehensive gap analysis and documentation.
    
    Provides gap identification algorithms, criticality prioritization,
    and detailed documentation generation capabilities.
    """
    
    def __init__(self, config_manager, component_name: str = "GapAnalysisEngine"):
        """Initialize the gap analysis engine."""
        super().__init__(config_manager, component_name)
        self._gap_detection_rules = self._initialize_gap_detection_rules()
        self._criticality_weights = self._initialize_criticality_weights()
        self._documentation_templates = self._initialize_documentation_templates()
    
    def initialize(self) -> None:
        """Initialize the gap analysis engine."""
        try:
            self._logger.info("Initializing Gap Analysis Engine")
            
            # Initialize gap detection rules and templates
            self._gap_detection_rules = self._initialize_gap_detection_rules()
            self._criticality_weights = self._initialize_criticality_weights()
            self._documentation_templates = self._initialize_documentation_templates()
            
            # Set up workspace paths
            config = self.get_config()
            self._workspace_root = getattr(config, 'workspace_root', '.')
            self._specs_path = os.path.join(self._workspace_root, '.kiro', 'specs')
            
            self._logger.info("Gap Analysis Engine initialized successfully")
            
        except Exception as e:
            self._handle_error(e, "initialize")
    
    def generate_gap_analysis_report(self) -> GapAnalysisReport:
        """
        Generate comprehensive gap analysis report.
        
        Returns:
            GapAnalysisReport: Detailed gap analysis report
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Generating comprehensive gap analysis report")
            
            # Check cache first
            cached_result = self._get_cached_result("gap_analysis_report", max_age_seconds=1800)
            if cached_result:
                self._logger.info("Using cached gap analysis report")
                return cached_result
            
            # Identify all gaps using various detection methods
            all_gaps = self._identify_all_gaps()
            
            # Apply criticality prioritization
            prioritized_gaps = self._apply_criticality_prioritization(all_gaps)
            
            # Generate gap statistics
            gaps_by_criticality = self._calculate_gaps_by_criticality(prioritized_gaps)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(prioritized_gaps)
            
            # Generate next steps
            next_steps = self._generate_next_steps(prioritized_gaps)
            
            # Create comprehensive report
            report = GapAnalysisReport(
                report_id=f"gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                generation_timestamp=datetime.now(),
                total_gaps_identified=len(prioritized_gaps),
                gaps_by_criticality=gaps_by_criticality,
                detailed_gaps=prioritized_gaps,
                recommendations=recommendations,
                next_steps=next_steps
            )
            
            # Cache the result
            self._cache_analysis_result("gap_analysis_report", report)
            
            self._logger.info(f"Gap analysis report generated. Found {len(prioritized_gaps)} gaps total")
            
            return report
            
        except Exception as e:
            self._handle_error(e, "generate_gap_analysis_report")
    
    def validate_requirements_consistency(self, req_files: List[str]) -> ConsistencyResult:
        """
        Validate consistency between multiple requirements documents.
        
        Args:
            req_files: List of requirements file paths to validate
            
        Returns:
            ConsistencyResult: Results of consistency validation
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info(f"Validating requirements consistency across {len(req_files)} files")
            
            # Parse all requirements documents
            parsed_requirements = {}
            for req_file in req_files:
                if os.path.exists(req_file):
                    parsed_requirements[req_file] = self._parse_requirements_document(req_file)
                else:
                    self._logger.warning(f"Requirements file not found: {req_file}")
            
            if not parsed_requirements:
                return ConsistencyResult(
                    is_consistent=True,
                    total_requirements_checked=0,
                    consistency_issues=[],
                    consistency_score=1.0,
                    recommendations=["No requirements files found to validate"]
                )
            
            # Check for consistency issues
            consistency_issues = self._check_requirements_consistency(parsed_requirements)
            
            # Calculate consistency score
            total_requirements = sum(len(reqs.get("requirements", [])) for reqs in parsed_requirements.values())
            consistency_score = self._calculate_consistency_score(consistency_issues, total_requirements)
            
            # Generate recommendations
            recommendations = self._generate_consistency_recommendations(consistency_issues)
            
            result = ConsistencyResult(
                is_consistent=len(consistency_issues) == 0,
                total_requirements_checked=total_requirements,
                consistency_issues=consistency_issues,
                consistency_score=consistency_score,
                recommendations=recommendations
            )
            
            self._logger.info(f"Requirements consistency validation completed. "
                            f"Score: {consistency_score:.2f}, Issues: {len(consistency_issues)}")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "validate_requirements_consistency", {"req_files": req_files})
    
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
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Documenting architectural differences")
            
            # Analyze structural differences
            structural_differences = self._analyze_structural_differences(current, proposed)
            
            # Analyze component differences
            component_differences = self._analyze_component_differences(current, proposed)
            
            # Analyze interface differences
            interface_differences = self._analyze_interface_differences(current, proposed)
            
            # Generate documentation
            documentation = self._generate_architectural_differences_documentation(
                structural_differences,
                component_differences,
                interface_differences
            )
            
            # Save documentation to file
            doc_path = self._save_architectural_differences_documentation(documentation)
            
            return OperationResult(
                success=True,
                message="Architectural differences documented successfully",
                data={
                    "documentation_path": doc_path,
                    "structural_differences": len(structural_differences),
                    "component_differences": len(component_differences),
                    "interface_differences": len(interface_differences)
                }
            )
            
        except Exception as e:
            self._handle_error(e, "document_architectural_differences")
    
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
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info(f"Generating prioritized action plan for {len(gaps)} gaps")
            
            # Sort gaps by criticality and impact
            prioritized_gaps = self._prioritize_by_criticality_level(gaps, lambda gap: gap.criticality)
            
            # Group gaps by phase
            phases = self._group_gaps_by_implementation_phase(prioritized_gaps)
            
            # Generate action items for each phase
            action_plan = self._generate_phase_action_items(phases)
            
            # Calculate timeline and resource estimates
            timeline_estimates = self._calculate_implementation_timeline(phases)
            
            # Generate action plan document
            action_plan_doc = self._generate_action_plan_document(action_plan, timeline_estimates)
            
            # Save action plan to file
            plan_path = self._save_action_plan_document(action_plan_doc)
            
            return OperationResult(
                success=True,
                message="Prioritized action plan generated successfully",
                data={
                    "action_plan_path": plan_path,
                    "total_phases": len(phases),
                    "total_action_items": sum(len(phase["actions"]) for phase in action_plan.values()),
                    "estimated_timeline": timeline_estimates.get("total_weeks", 0)
                }
            )
            
        except Exception as e:
            self._handle_error(e, "generate_prioritized_action_plan", {"gaps_count": len(gaps)})
    
    def _initialize_gap_detection_rules(self) -> Dict[str, Any]:
        """Initialize rules for gap detection."""
        return {
            "missing_implementation_patterns": [
                r"TODO:\s*(.+)",
                r"FIXME:\s*(.+)",
                r"NotImplementedError",
                r"pass\s*#\s*TODO",
                r"raise\s+NotImplementedError"
            ],
            "security_gap_patterns": [
                r"#\s*SECURITY:\s*(.+)",
                r"#\s*UNSAFE:\s*(.+)",
                r"#\s*VULNERABILITY:\s*(.+)",
                r"password\s*=\s*[\"'].*[\"']",  # Hardcoded passwords
                r"api_key\s*=\s*[\"'].*[\"']"   # Hardcoded API keys
            ],
            "stability_gap_patterns": [
                r"#\s*HACK:\s*(.+)",
                r"#\s*TEMPORARY:\s*(.+)",
                r"#\s*WORKAROUND:\s*(.+)",
                r"except:\s*pass",  # Bare except clauses
                r"except\s+Exception:\s*pass"  # Overly broad exception handling
            ],
            "functionality_gap_patterns": [
                r"#\s*INCOMPLETE:\s*(.+)",
                r"#\s*PARTIAL:\s*(.+)",
                r"#\s*STUB:\s*(.+)",
                r"def\s+\w+\([^)]*\):\s*pass",  # Empty function definitions
                r"class\s+\w+[^:]*:\s*pass"     # Empty class definitions
            ]
        }
    
    def _initialize_criticality_weights(self) -> Dict[CriticalityLevel, float]:
        """Initialize weights for criticality prioritization."""
        return {
            CriticalityLevel.SECURITY: 1.0,      # Highest priority
            CriticalityLevel.STABILITY: 0.8,     # High priority
            CriticalityLevel.FUNCTIONALITY: 0.6, # Medium priority
            CriticalityLevel.UX: 0.4             # Lower priority
        }
    
    def _initialize_documentation_templates(self) -> Dict[str, str]:
        """Initialize templates for documentation generation."""
        return {
            "gap_analysis_report": """
# Gap Analysis Report

**Report ID:** {report_id}
**Generated:** {generation_timestamp}
**Total Gaps:** {total_gaps_identified}

## Executive Summary

This report identifies {total_gaps_identified} gaps in the current system architecture.

## Gaps by Criticality

{gaps_by_criticality_section}

## Detailed Gap Analysis

{detailed_gaps_section}

## Recommendations

{recommendations_section}

## Next Steps

{next_steps_section}
""",
            "architectural_differences": """
# Architectural Differences Analysis

**Generated:** {timestamp}

## Structural Differences

{structural_differences}

## Component Differences

{component_differences}

## Interface Differences

{interface_differences}

## Summary

{summary}
""",
            "action_plan": """
# Prioritized Action Plan

**Generated:** {timestamp}
**Total Phases:** {total_phases}
**Estimated Timeline:** {estimated_timeline} weeks

## Implementation Phases

{phases_section}

## Resource Requirements

{resource_requirements}

## Risk Assessment

{risk_assessment}
"""
        }
    
    def _identify_all_gaps(self) -> List[CriticalGap]:
        """Identify all gaps using various detection methods."""
        all_gaps = []
        gap_counter = 1
        
        try:
            # Scan codebase for implementation gaps
            code_gaps = self._scan_codebase_for_gaps()
            all_gaps.extend(code_gaps)
            
            # Check for architectural gaps
            arch_gaps = self._identify_architectural_gaps()
            all_gaps.extend(arch_gaps)
            
            # Check for documentation gaps
            doc_gaps = self._identify_documentation_gaps()
            all_gaps.extend(doc_gaps)
            
            # Check for testing gaps
            test_gaps = self._identify_testing_gaps()
            all_gaps.extend(test_gaps)
            
            # Assign unique IDs to gaps
            for i, gap in enumerate(all_gaps, 1):
                if not gap.gap_id:
                    gap.gap_id = f"gap_{i:03d}"
            
            return all_gaps
            
        except Exception as e:
            self._logger.error(f"Error identifying gaps: {e}")
            return all_gaps
    
    def _scan_codebase_for_gaps(self) -> List[CriticalGap]:
        """Scan codebase for implementation gaps."""
        gaps = []
        gap_counter = 1
        
        try:
            # Find all Python files
            workspace_path = Path(self._workspace_root)
            python_files = list(workspace_path.rglob("*.py"))
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for various gap patterns
                    file_gaps = self._detect_gaps_in_file(file_path, content)
                    gaps.extend(file_gaps)
                    
                except Exception as e:
                    self._logger.warning(f"Error scanning file {file_path}: {e}")
            
            return gaps
            
        except Exception as e:
            self._logger.error(f"Error scanning codebase: {e}")
            return gaps
    
    def _detect_gaps_in_file(self, file_path: Path, content: str) -> List[CriticalGap]:
        """Detect gaps in a single file."""
        gaps = []
        
        try:
            relative_path = str(file_path.relative_to(Path(self._workspace_root))) if hasattr(self, '_workspace_root') else file_path.name
            
            # Check for different types of gaps
            for gap_type, patterns in self._gap_detection_rules.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        
                        # Determine criticality based on gap type
                        criticality = self._determine_gap_criticality(gap_type, match.group(0))
                        
                        gap = CriticalGap(
                            gap_id="",  # Will be assigned later
                            description=f"{gap_type.replace('_', ' ').title()} in {relative_path}:{line_number}: {match.group(0)[:100]}",
                            criticality=criticality,
                            affected_components=[relative_path],
                            impact_assessment=self._assess_gap_impact(gap_type, match.group(0)),
                            recommended_action=self._recommend_gap_action(gap_type, match.group(0)),
                            estimated_effort=self._estimate_gap_effort(gap_type, match.group(0))
                        )
                        gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            self._logger.warning(f"Error detecting gaps in file {file_path}: {e}")
            return gaps
    
    def _determine_gap_criticality(self, gap_type: str, gap_content: str) -> CriticalityLevel:
        """Determine criticality level of a gap."""
        if "security" in gap_type.lower():
            return CriticalityLevel.SECURITY
        elif "stability" in gap_type.lower():
            return CriticalityLevel.STABILITY
        elif "functionality" in gap_type.lower():
            return CriticalityLevel.FUNCTIONALITY
        else:
            return CriticalityLevel.UX
    
    def _assess_gap_impact(self, gap_type: str, gap_content: str) -> str:
        """Assess the impact of a gap."""
        impact_map = {
            "missing_implementation_patterns": "Feature incomplete, may cause runtime errors",
            "security_gap_patterns": "Security vulnerability, potential data breach",
            "stability_gap_patterns": "System instability, potential crashes",
            "functionality_gap_patterns": "Reduced functionality, user experience degraded"
        }
        return impact_map.get(gap_type, "Impact assessment needed")
    
    def _recommend_gap_action(self, gap_type: str, gap_content: str) -> str:
        """Recommend action for addressing a gap."""
        action_map = {
            "missing_implementation_patterns": "Complete implementation according to specifications",
            "security_gap_patterns": "Implement proper security measures and validation",
            "stability_gap_patterns": "Replace with robust implementation and proper error handling",
            "functionality_gap_patterns": "Implement complete functionality with proper testing"
        }
        return action_map.get(gap_type, "Review and implement proper solution")
    
    def _estimate_gap_effort(self, gap_type: str, gap_content: str) -> str:
        """Estimate effort required to fix a gap."""
        effort_map = {
            "missing_implementation_patterns": "Medium (2-5 days)",
            "security_gap_patterns": "High (5-10 days)",
            "stability_gap_patterns": "Medium (2-5 days)",
            "functionality_gap_patterns": "Low (1-2 days)"
        }
        return effort_map.get(gap_type, "Medium (2-5 days)")
    
    def _identify_architectural_gaps(self) -> List[CriticalGap]:
        """Identify architectural gaps."""
        # This would integrate with the ArchitectureAnalysisEngine
        # For now, return empty list as placeholder
        return []
    
    def _identify_documentation_gaps(self) -> List[CriticalGap]:
        """Identify documentation gaps."""
        gaps = []
        
        try:
            # Check for missing docstrings
            workspace_path = Path(self._workspace_root)
            python_files = list(workspace_path.rglob("*.py"))
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for functions/classes without docstrings
                    doc_gaps = self._check_missing_docstrings(file_path, content)
                    gaps.extend(doc_gaps)
                    
                except Exception as e:
                    self._logger.warning(f"Error checking documentation in {file_path}: {e}")
            
            return gaps
            
        except Exception as e:
            self._logger.error(f"Error identifying documentation gaps: {e}")
            return gaps
    
    def _check_missing_docstrings(self, file_path: Path, content: str) -> List[CriticalGap]:
        """Check for missing docstrings in a file."""
        gaps = []
        
        try:
            relative_path = str(file_path.relative_to(Path(self._workspace_root))) if hasattr(self, '_workspace_root') else file_path.name
            
            # Find function definitions without docstrings
            func_pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n(?!\s*"""|\s*\'\'\')'
            func_matches = re.finditer(func_pattern, content, re.MULTILINE)
            
            for match in func_matches:
                line_number = content[:match.start()].count('\n') + 1
                func_name = match.group(1)
                
                gap = CriticalGap(
                    gap_id="",
                    description=f"Missing docstring for function '{func_name}' in {relative_path}:{line_number}",
                    criticality=CriticalityLevel.UX,
                    affected_components=[relative_path],
                    impact_assessment="Documentation incomplete, reduces code maintainability",
                    recommended_action=f"Add comprehensive docstring to function '{func_name}'",
                    estimated_effort="Low (1 hour)"
                )
                gaps.append(gap)
            
            # Find class definitions without docstrings
            class_pattern = r'class\s+(\w+)[^:]*:\s*\n(?!\s*"""|\s*\'\'\')'
            class_matches = re.finditer(class_pattern, content, re.MULTILINE)
            
            for match in class_matches:
                line_number = content[:match.start()].count('\n') + 1
                class_name = match.group(1)
                
                gap = CriticalGap(
                    gap_id="",
                    description=f"Missing docstring for class '{class_name}' in {relative_path}:{line_number}",
                    criticality=CriticalityLevel.UX,
                    affected_components=[relative_path],
                    impact_assessment="Documentation incomplete, reduces code maintainability",
                    recommended_action=f"Add comprehensive docstring to class '{class_name}'",
                    estimated_effort="Low (1 hour)"
                )
                gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            self._logger.warning(f"Error checking docstrings in {file_path}: {e}")
            return gaps
    
    def _identify_testing_gaps(self) -> List[CriticalGap]:
        """Identify testing gaps."""
        gaps = []
        
        try:
            # Check for missing test files
            workspace_path = Path(self._workspace_root)
            python_files = list(workspace_path.rglob("*.py"))
            test_files = list(workspace_path.rglob("test_*.py"))
            
            # Find source files without corresponding test files
            for file_path in python_files:
                if "test" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                
                # Check if there's a corresponding test file
                expected_test_file = f"test_{file_path.stem}.py"
                test_exists = any(expected_test_file in str(test_file) for test_file in test_files)
                
                if not test_exists:
                    relative_path = str(file_path.relative_to(workspace_path)) if hasattr(self, '_workspace_root') else file_path.name
                    
                    gap = CriticalGap(
                        gap_id="",
                        description=f"Missing test file for {relative_path}",
                        criticality=CriticalityLevel.STABILITY,
                        affected_components=[relative_path],
                        impact_assessment="No test coverage, potential for undetected bugs",
                        recommended_action=f"Create comprehensive test file: {expected_test_file}",
                        estimated_effort="Medium (2-4 hours)"
                    )
                    gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            self._logger.error(f"Error identifying testing gaps: {e}")
            return gaps
    
    def _apply_criticality_prioritization(self, gaps: List[CriticalGap]) -> List[CriticalGap]:
        """Apply criticality prioritization to gaps."""
        return self._prioritize_by_criticality_level(gaps, lambda gap: gap.criticality)
    
    def _calculate_gaps_by_criticality(self, gaps: List[CriticalGap]) -> Dict[CriticalityLevel, int]:
        """Calculate gap counts by criticality level."""
        counts = {level: 0 for level in CriticalityLevel}
        
        for gap in gaps:
            counts[gap.criticality] += 1
        
        return counts    

    def _generate_recommendations(self, gaps: List[CriticalGap]) -> List[str]:
        """Generate recommendations based on identified gaps."""
        recommendations = []
        
        # Count gaps by criticality
        security_gaps = sum(1 for gap in gaps if gap.criticality == CriticalityLevel.SECURITY)
        stability_gaps = sum(1 for gap in gaps if gap.criticality == CriticalityLevel.STABILITY)
        functionality_gaps = sum(1 for gap in gaps if gap.criticality == CriticalityLevel.FUNCTIONALITY)
        ux_gaps = sum(1 for gap in gaps if gap.criticality == CriticalityLevel.UX)
        
        # Generate specific recommendations
        if security_gaps > 0:
            recommendations.append(f"Address {security_gaps} security gaps immediately - these pose critical risks")
            recommendations.append("Implement security code review process to prevent future security gaps")
        
        if stability_gaps > 0:
            recommendations.append(f"Prioritize {stability_gaps} stability gaps to prevent system crashes")
            recommendations.append("Implement comprehensive error handling and logging")
        
        if functionality_gaps > 0:
            recommendations.append(f"Complete {functionality_gaps} functionality gaps to improve user experience")
            recommendations.append("Establish clear implementation standards and code review process")
        
        if ux_gaps > 0:
            recommendations.append(f"Address {ux_gaps} UX gaps to improve code maintainability")
            recommendations.append("Implement documentation standards and automated documentation checks")
        
        # General recommendations
        if len(gaps) > 20:
            recommendations.append("Consider implementing automated gap detection in CI/CD pipeline")
        
        if not recommendations:
            recommendations.append("No critical gaps identified - maintain current quality standards")
        
        return recommendations
    
    def _generate_next_steps(self, gaps: List[CriticalGap]) -> List[str]:
        """Generate next steps based on identified gaps."""
        next_steps = []
        
        if not gaps:
            next_steps.append("Continue monitoring for new gaps")
            return next_steps
        
        # Prioritize by criticality
        security_gaps = [gap for gap in gaps if gap.criticality == CriticalityLevel.SECURITY]
        stability_gaps = [gap for gap in gaps if gap.criticality == CriticalityLevel.STABILITY]
        
        if security_gaps:
            next_steps.append(f"IMMEDIATE: Address {len(security_gaps)} security gaps")
            next_steps.append("Conduct security audit of entire codebase")
        
        if stability_gaps:
            next_steps.append(f"HIGH PRIORITY: Fix {len(stability_gaps)} stability gaps")
            next_steps.append("Implement comprehensive testing for affected components")
        
        # Implementation phases
        next_steps.append("Phase 1: Address all security and stability gaps (Week 1-2)")
        next_steps.append("Phase 2: Complete functionality gaps (Week 3-4)")
        next_steps.append("Phase 3: Improve documentation and UX gaps (Week 5-6)")
        next_steps.append("Phase 4: Implement preventive measures and monitoring")
        
        return next_steps
    
    def _parse_requirements_document(self, file_path: str) -> Dict[str, Any]:
        """Parse a requirements document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract requirements sections
            requirements = []
            current_requirement = None
            
            for line in content.splitlines():
                line = line.strip()
                
                # Check for requirement headers
                if line.startswith("### Requisito") or line.startswith("### Requirement"):
                    if current_requirement:
                        requirements.append(current_requirement)
                    
                    current_requirement = {
                        "id": line,
                        "user_story": "",
                        "acceptance_criteria": []
                    }
                
                elif line.startswith("**User Story:**") and current_requirement:
                    current_requirement["user_story"] = line.replace("**User Story:**", "").strip()
                
                elif line.startswith("#### Acceptance Criteria") and current_requirement:
                    # Start collecting acceptance criteria
                    continue
                
                elif line and line[0].isdigit() and current_requirement:
                    # This is an acceptance criterion
                    current_requirement["acceptance_criteria"].append(line)
            
            # Add the last requirement
            if current_requirement:
                requirements.append(current_requirement)
            
            return {
                "file_path": file_path,
                "requirements": requirements,
                "parsed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"Error parsing requirements document {file_path}: {e}")
            return {"file_path": file_path, "requirements": [], "error": str(e)}
    
    def _check_requirements_consistency(self, parsed_requirements: Dict[str, Dict[str, Any]]) -> List[ConsistencyIssue]:
        """Check for consistency issues between requirements documents."""
        issues = []
        issue_counter = 1
        
        try:
            # Extract all requirements from all documents
            all_requirements = {}
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    req_id = req.get("id", "")
                    if req_id:
                        if req_id not in all_requirements:
                            all_requirements[req_id] = []
                        all_requirements[req_id].append({
                            "file": file_path,
                            "data": req
                        })
            
            # Check for duplicate requirement IDs
            for req_id, occurrences in all_requirements.items():
                if len(occurrences) > 1:
                    issue = ConsistencyIssue(
                        issue_id=f"consistency_{issue_counter:03d}",
                        description=f"Duplicate requirement ID: {req_id}",
                        conflicting_documents=[occ["file"] for occ in occurrences],
                        conflicting_requirements=[req_id],
                        severity="High",
                        resolution_suggestion="Ensure each requirement has a unique ID across all documents"
                    )
                    issues.append(issue)
                    issue_counter += 1
            
            # Check for conflicting acceptance criteria
            issues.extend(self._check_conflicting_acceptance_criteria(all_requirements, issue_counter))
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking requirements consistency: {e}")
            return issues
    
    def _check_conflicting_acceptance_criteria(
        self, 
        all_requirements: Dict[str, List[Dict[str, Any]]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for conflicting acceptance criteria."""
        issues = []
        
        try:
            # Look for similar requirements with different criteria
            req_ids = list(all_requirements.keys())
            
            for i, req_id1 in enumerate(req_ids):
                for req_id2 in req_ids[i+1:]:
                    # Check if requirements are similar but have different criteria
                    similarity = self._calculate_requirement_similarity(req_id1, req_id2)
                    
                    if similarity > 0.7:  # High similarity threshold
                        req1_data = all_requirements[req_id1][0]["data"]
                        req2_data = all_requirements[req_id2][0]["data"]
                        
                        criteria1 = set(req1_data.get("acceptance_criteria", []))
                        criteria2 = set(req2_data.get("acceptance_criteria", []))
                        
                        if criteria1 != criteria2:
                            issue = ConsistencyIssue(
                                issue_id=f"consistency_{issue_counter:03d}",
                                description=f"Similar requirements with different acceptance criteria: {req_id1} vs {req_id2}",
                                conflicting_documents=[
                                    all_requirements[req_id1][0]["file"],
                                    all_requirements[req_id2][0]["file"]
                                ],
                                conflicting_requirements=[req_id1, req_id2],
                                severity="Medium",
                                resolution_suggestion="Review and align acceptance criteria for similar requirements"
                            )
                            issues.append(issue)
                            issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking conflicting acceptance criteria: {e}")
            return issues
    
    def _calculate_requirement_similarity(self, req_id1: str, req_id2: str) -> float:
        """Calculate similarity between two requirements."""
        # Simple similarity based on common words in requirement IDs
        words1 = set(req_id1.lower().split())
        words2 = set(req_id2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_consistency_score(self, issues: List[ConsistencyIssue], total_requirements: int) -> float:
        """Calculate consistency score based on issues found."""
        if total_requirements == 0:
            return 1.0
        
        # Weight issues by severity
        severity_weights = {"High": 1.0, "Medium": 0.5, "Low": 0.2}
        
        total_weight = sum(severity_weights.get(issue.severity, 0.5) for issue in issues)
        
        # Calculate score (higher is better)
        max_possible_weight = total_requirements * 1.0  # Assuming all could be high severity
        consistency_score = max(0.0, 1.0 - (total_weight / max_possible_weight))
        
        return min(1.0, consistency_score)
    
    def _generate_consistency_recommendations(self, issues: List[ConsistencyIssue]) -> List[str]:
        """Generate recommendations for consistency issues."""
        recommendations = []
        
        if not issues:
            recommendations.append("Requirements are consistent across all documents")
            return recommendations
        
        high_severity_count = sum(1 for issue in issues if issue.severity == "High")
        medium_severity_count = sum(1 for issue in issues if issue.severity == "Medium")
        
        if high_severity_count > 0:
            recommendations.append(f"Address {high_severity_count} high-severity consistency issues immediately")
        
        if medium_severity_count > 0:
            recommendations.append(f"Review and resolve {medium_severity_count} medium-severity consistency issues")
        
        recommendations.append("Implement requirements review process to prevent future inconsistencies")
        recommendations.append("Consider using a requirements management tool for better consistency")
        
        return recommendations
    
    def _analyze_structural_differences(self, current: Dict[str, Any], proposed: Dict[str, Any]) -> List[str]:
        """Analyze structural differences between architectures."""
        differences = []
        
        try:
            # Compare layers
            current_layers = set(current.get("layers", {}).keys())
            proposed_layers = set(proposed.get("layers", {}).keys())
            
            missing_layers = proposed_layers - current_layers
            extra_layers = current_layers - proposed_layers
            
            for layer in missing_layers:
                differences.append(f"Missing architectural layer: {layer}")
            
            for layer in extra_layers:
                differences.append(f"Extra architectural layer not in design: {layer}")
            
            return differences
            
        except Exception as e:
            self._logger.error(f"Error analyzing structural differences: {e}")
            return differences
    
    def _analyze_component_differences(self, current: Dict[str, Any], proposed: Dict[str, Any]) -> List[str]:
        """Analyze component differences between architectures."""
        differences = []
        
        try:
            # Extract components from both architectures
            current_components = set()
            for component_info in current.get("components", {}).values():
                current_components.update(component_info.get("classes", []))
            
            proposed_components = set()
            for component_list in proposed.get("components", {}).values():
                if isinstance(component_list, list):
                    proposed_components.update(component_list)
            
            missing_components = proposed_components - current_components
            extra_components = current_components - proposed_components
            
            for component in missing_components:
                differences.append(f"Missing component: {component}")
            
            for component in extra_components:
                differences.append(f"Extra component not in design: {component}")
            
            return differences
            
        except Exception as e:
            self._logger.error(f"Error analyzing component differences: {e}")
            return differences
    
    def _analyze_interface_differences(self, current: Dict[str, Any], proposed: Dict[str, Any]) -> List[str]:
        """Analyze interface differences between architectures."""
        differences = []
        
        try:
            # Extract interfaces from both architectures
            current_interfaces = set()
            for component_info in current.get("components", {}).values():
                current_interfaces.update(component_info.get("interfaces", []))
            
            proposed_interfaces = set()
            for interface_list in proposed.get("interfaces", {}).values():
                if isinstance(interface_list, list):
                    proposed_interfaces.update(interface_list)
            
            missing_interfaces = proposed_interfaces - current_interfaces
            extra_interfaces = current_interfaces - proposed_interfaces
            
            for interface in missing_interfaces:
                differences.append(f"Missing interface: {interface}")
            
            for interface in extra_interfaces:
                differences.append(f"Extra interface not in design: {interface}")
            
            return differences
            
        except Exception as e:
            self._logger.error(f"Error analyzing interface differences: {e}")
            return differences
    
    def _generate_architectural_differences_documentation(
        self,
        structural_differences: List[str],
        component_differences: List[str],
        interface_differences: List[str]
    ) -> str:
        """Generate documentation for architectural differences."""
        template = self._documentation_templates["architectural_differences"]
        
        return template.format(
            timestamp=datetime.now().isoformat(),
            structural_differences="\n".join(f"- {diff}" for diff in structural_differences) or "No structural differences found",
            component_differences="\n".join(f"- {diff}" for diff in component_differences) or "No component differences found",
            interface_differences="\n".join(f"- {diff}" for diff in interface_differences) or "No interface differences found",
            summary=f"Total differences: {len(structural_differences + component_differences + interface_differences)}"
        )
    
    def _save_architectural_differences_documentation(self, documentation: str) -> str:
        """Save architectural differences documentation to file."""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(self._workspace_root, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"architectural_differences_{timestamp}.md"
            file_path = os.path.join(reports_dir, filename)
            
            # Write documentation to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            self._logger.info(f"Architectural differences documentation saved to {file_path}")
            return file_path
            
        except Exception as e:
            self._logger.error(f"Error saving architectural differences documentation: {e}")
            return ""
    
    def _group_gaps_by_implementation_phase(self, gaps: List[CriticalGap]) -> Dict[str, List[CriticalGap]]:
        """Group gaps by implementation phase."""
        phases = {
            "Phase 1 - Critical Security & Stability": [],
            "Phase 2 - Core Functionality": [],
            "Phase 3 - Documentation & UX": []
        }
        
        for gap in gaps:
            if gap.criticality in [CriticalityLevel.SECURITY, CriticalityLevel.STABILITY]:
                phases["Phase 1 - Critical Security & Stability"].append(gap)
            elif gap.criticality == CriticalityLevel.FUNCTIONALITY:
                phases["Phase 2 - Core Functionality"].append(gap)
            else:
                phases["Phase 3 - Documentation & UX"].append(gap)
        
        return phases
    
    def _generate_phase_action_items(self, phases: Dict[str, List[CriticalGap]]) -> Dict[str, Dict[str, Any]]:
        """Generate action items for each phase."""
        action_plan = {}
        
        for phase_name, gaps in phases.items():
            if not gaps:
                continue
            
            actions = []
            for gap in gaps:
                actions.append({
                    "gap_id": gap.gap_id,
                    "description": gap.description,
                    "action": gap.recommended_action,
                    "effort": gap.estimated_effort,
                    "priority": gap.criticality.value
                })
            
            action_plan[phase_name] = {
                "actions": actions,
                "total_gaps": len(gaps),
                "estimated_effort": self._calculate_phase_effort(gaps)
            }
        
        return action_plan
    
    def _calculate_phase_effort(self, gaps: List[CriticalGap]) -> str:
        """Calculate total effort for a phase."""
        # Simple effort calculation based on gap count and types
        total_days = 0
        
        for gap in gaps:
            effort_str = gap.estimated_effort.lower()
            if "low" in effort_str:
                total_days += 1
            elif "medium" in effort_str:
                total_days += 3
            elif "high" in effort_str:
                total_days += 7
            else:
                total_days += 3  # Default
        
        weeks = max(1, total_days // 5)
        return f"{weeks} weeks ({total_days} days)"
    
    def _calculate_implementation_timeline(self, phases: Dict[str, List[CriticalGap]]) -> Dict[str, Any]:
        """Calculate implementation timeline."""
        total_weeks = 0
        phase_timelines = {}
        
        for phase_name, gaps in phases.items():
            if gaps:
                phase_effort = self._calculate_phase_effort(gaps)
                weeks = int(phase_effort.split()[0])
                phase_timelines[phase_name] = weeks
                total_weeks += weeks
        
        return {
            "total_weeks": total_weeks,
            "phase_timelines": phase_timelines,
            "estimated_completion": f"{total_weeks} weeks from start"
        }
    
    def _generate_action_plan_document(
        self, 
        action_plan: Dict[str, Dict[str, Any]], 
        timeline_estimates: Dict[str, Any]
    ) -> str:
        """Generate action plan document."""
        template = self._documentation_templates["action_plan"]
        
        # Generate phases section
        phases_section = ""
        for phase_name, phase_data in action_plan.items():
            phases_section += f"\n## {phase_name}\n\n"
            phases_section += f"**Total Actions:** {phase_data['total_gaps']}\n"
            phases_section += f"**Estimated Effort:** {phase_data['estimated_effort']}\n\n"
            
            for action in phase_data["actions"]:
                phases_section += f"- **{action['gap_id']}:** {action['description']}\n"
                phases_section += f"  - Action: {action['action']}\n"
                phases_section += f"  - Effort: {action['effort']}\n\n"
        
        return template.format(
            timestamp=datetime.now().isoformat(),
            total_phases=len(action_plan),
            estimated_timeline=timeline_estimates["total_weeks"],
            phases_section=phases_section,
            resource_requirements="Development team with security and architecture expertise",
            risk_assessment="Medium risk - requires careful coordination and testing"
        )
    
    def _save_action_plan_document(self, action_plan_doc: str) -> str:
        """Save action plan document to file."""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(self._workspace_root, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gap_analysis_action_plan_{timestamp}.md"
            file_path = os.path.join(reports_dir, filename)
            
            # Write action plan to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(action_plan_doc)
            
            self._logger.info(f"Action plan document saved to {file_path}")
            return file_path
            
        except Exception as e:
            self._logger.error(f"Error saving action plan document: {e}")
            return ""