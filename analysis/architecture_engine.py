"""
Architecture Analysis Engine implementation.

This module provides the core ArchitectureAnalysisEngine class that handles
architecture mapping, comparison with design documents, and gap identification.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

from .base import AnalysisBase
from .interfaces import (
    ArchitectureAnalysisInterface,
    ArchitectureAnalysis,
    ComparisonResult,
    CriticalGap,
    LostFunctionality,
    ConsistencyIssue,
    PrioritizedFix,
    CriticalityLevel
)
from ..core.exceptions import ArchitectureAnalysisError


class ArchitectureAnalysisEngine(AnalysisBase, ArchitectureAnalysisInterface):
    """
    Core engine for architecture analysis and comparison.
    
    Provides comprehensive analysis of current system architecture,
    comparison with design documents, and identification of critical gaps.
    """
    
    def __init__(self, config_manager, component_name: str = "ArchitectureAnalysisEngine"):
        """Initialize the architecture analysis engine."""
        super().__init__(config_manager, component_name)
        self._design_documents: Dict[str, Dict[str, Any]] = {}
        self._current_architecture: Optional[Dict[str, Any]] = None
        self._analysis_patterns = self._initialize_analysis_patterns()
    
    def initialize(self) -> None:
        """Initialize the architecture analysis engine."""
        try:
            self._logger.info("Initializing Architecture Analysis Engine")
            
            # Initialize analysis patterns and rules
            self._analysis_patterns = self._initialize_analysis_patterns()
            
            # Set up workspace paths
            config = self.get_config()
            self._workspace_root = getattr(config, 'workspace_root', '.')
            self._specs_path = os.path.join(self._workspace_root, '.kiro', 'specs')
            
            self._logger.info("Architecture Analysis Engine initialized successfully")
            
        except Exception as e:
            self._handle_error(e, "initialize")
    
    def analyze_current_architecture(self) -> ArchitectureAnalysis:
        """
        Analyze the current system architecture.
        
        Returns:
            ArchitectureAnalysis: Complete analysis of current architecture
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Starting current architecture analysis")
            
            # Check cache first
            cached_result = self._get_cached_result("current_architecture", max_age_seconds=1800)
            if cached_result:
                self._logger.info("Using cached architecture analysis")
                return cached_result
            
            # Map current architecture
            current_arch = self._map_current_architecture()
            self._current_architecture = current_arch
            
            # Load design documents for comparison
            design_arch = self._load_design_documents()
            
            # Identify gaps and issues
            gaps = self._identify_architectural_gaps(current_arch, design_arch)
            lost_functionalities = self._identify_lost_functionalities(current_arch, design_arch)
            consistency_issues = self._check_consistency_issues()
            prioritized_fixes = self._prioritize_fixes(gaps)
            
            # Create comprehensive analysis
            analysis = ArchitectureAnalysis(
                current_architecture=current_arch,
                design_architecture=design_arch,
                identified_gaps=gaps,
                lost_functionalities=lost_functionalities,
                consistency_issues=consistency_issues,
                prioritized_fixes=prioritized_fixes,
                analysis_timestamp=datetime.now()
            )
            
            # Cache the result
            self._cache_analysis_result("current_architecture", analysis)
            
            self._logger.info(f"Architecture analysis completed. Found {len(gaps)} gaps, "
                            f"{len(lost_functionalities)} lost functionalities")
            
            return analysis
            
        except Exception as e:
            self._handle_error(e, "analyze_current_architecture")
    
    def compare_with_design_documents(self, design_paths: List[str]) -> ComparisonResult:
        """
        Compare current implementation with design documents.
        
        Args:
            design_paths: Paths to design documents to compare against
            
        Returns:
            ComparisonResult: Detailed comparison results
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info(f"Comparing with design documents: {design_paths}")
            
            # Load design documents
            design_data = {}
            for path in design_paths:
                design_data[path] = self._parse_design_document(path)
            
            # Get current architecture if not already loaded
            if not self._current_architecture:
                self._current_architecture = self._map_current_architecture()
            
            # Perform comparison
            matches = self._find_architectural_matches(self._current_architecture, design_data)
            missing_components = self._find_missing_components(self._current_architecture, design_data)
            extra_components = self._find_extra_components(self._current_architecture, design_data)
            differences = self._find_architectural_differences(self._current_architecture, design_data)
            
            # Calculate compliance score
            total_expected = len(matches) + len(missing_components)
            compliance_score = len(matches) / total_expected if total_expected > 0 else 1.0
            
            result = ComparisonResult(
                matches=matches,
                missing_components=missing_components,
                extra_components=extra_components,
                architectural_differences=differences,
                compliance_score=compliance_score
            )
            
            self._logger.info(f"Comparison completed. Compliance score: {compliance_score:.2f}")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "compare_with_design_documents", {"design_paths": design_paths})
    
    def identify_critical_gaps(self) -> List[CriticalGap]:
        """
        Identify critical gaps in the current implementation.
        
        Returns:
            List[CriticalGap]: List of identified critical gaps
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Identifying critical gaps")
            
            # Get current architecture
            if not self._current_architecture:
                self._current_architecture = self._map_current_architecture()
            
            # Load design documents
            design_arch = self._load_design_documents()
            
            # Identify gaps
            gaps = self._identify_architectural_gaps(self._current_architecture, design_arch)
            
            # Filter for critical gaps only
            critical_gaps = [gap for gap in gaps if gap.criticality in [
                CriticalityLevel.SECURITY, 
                CriticalityLevel.STABILITY
            ]]
            
            self._logger.info(f"Identified {len(critical_gaps)} critical gaps out of {len(gaps)} total gaps")
            
            return critical_gaps
            
        except Exception as e:
            self._handle_error(e, "identify_critical_gaps")
    
    def map_lost_functionalities(self) -> List[LostFunctionality]:
        """
        Map functionalities that were lost during refactoring.
        
        Returns:
            List[LostFunctionality]: List of lost functionalities
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Mapping lost functionalities")
            
            # Get current architecture
            if not self._current_architecture:
                self._current_architecture = self._map_current_architecture()
            
            # Load design documents
            design_arch = self._load_design_documents()
            
            # Identify lost functionalities
            lost_functionalities = self._identify_lost_functionalities(self._current_architecture, design_arch)
            
            self._logger.info(f"Identified {len(lost_functionalities)} lost functionalities")
            
            return lost_functionalities
            
        except Exception as e:
            self._handle_error(e, "map_lost_functionalities")
    
    def prioritize_by_criticality(self, gaps: List[CriticalGap]) -> List[PrioritizedFix]:
        """
        Prioritize gaps by criticality level.
        
        Args:
            gaps: List of gaps to prioritize
            
        Returns:
            List[PrioritizedFix]: Prioritized list of fixes
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info(f"Prioritizing {len(gaps)} gaps by criticality")
            
            # Sort gaps by criticality
            sorted_gaps = self._prioritize_by_criticality_level(gaps, lambda gap: gap.criticality)
            
            # Convert to prioritized fixes
            prioritized_fixes = []
            for i, gap in enumerate(sorted_gaps):
                fix = PrioritizedFix(
                    fix_id=f"fix_{gap.gap_id}",
                    description=f"Fix gap: {gap.description}",
                    priority=i + 1,
                    criticality=gap.criticality,
                    estimated_effort=gap.estimated_effort,
                    dependencies=self._analyze_fix_dependencies(gap),
                    success_criteria=self._define_success_criteria(gap)
                )
                prioritized_fixes.append(fix)
            
            self._logger.info(f"Created {len(prioritized_fixes)} prioritized fixes")
            
            return prioritized_fixes
            
        except Exception as e:
            self._handle_error(e, "prioritize_by_criticality", {"gaps_count": len(gaps)}) 
   
    def _initialize_analysis_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for architecture analysis."""
        return {
            "component_patterns": {
                "class_definition": r"class\s+(\w+).*:",
                "interface_definition": r"class\s+(\w+Interface).*:",
                "function_definition": r"def\s+(\w+)\s*\(",
                "import_statement": r"from\s+(.+)\s+import\s+(.+)",
            },
            "architecture_markers": {
                "layer_indicators": ["interface", "base", "engine", "manager", "system"],
                "component_types": ["detector", "analyzer", "validator", "installer", "downloader"],
                "critical_components": ["security", "authentication", "validation", "integrity"],
            },
            "gap_indicators": {
                "missing_implementations": ["TODO", "NotImplemented", "pass  # TODO"],
                "incomplete_features": ["# FIXME", "# HACK", "# TEMPORARY"],
                "security_gaps": ["# SECURITY", "# UNSAFE", "# VULNERABILITY"],
            }
        }
    
    def _map_current_architecture(self) -> Dict[str, Any]:
        """Map the current system architecture by analyzing code structure."""
        try:
            architecture = {
                "components": {},
                "layers": {},
                "interfaces": {},
                "implementations": {},
                "dependencies": {},
                "metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "total_files_analyzed": 0,
                    "total_components_found": 0
                }
            }
            
            # Analyze workspace structure
            workspace_path = Path(self._workspace_root)
            
            # Find all Python files in the project
            python_files = list(workspace_path.rglob("*.py"))
            architecture["metadata"]["total_files_analyzed"] = len(python_files)
            
            for file_path in python_files:
                try:
                    self._analyze_file_architecture(file_path, architecture)
                except Exception as e:
                    self._logger.warning(f"Failed to analyze file {file_path}: {e}")
            
            # Analyze directory structure
            self._analyze_directory_structure(workspace_path, architecture)
            
            # Identify architectural layers
            self._identify_architectural_layers(architecture)
            
            architecture["metadata"]["total_components_found"] = len(architecture["components"])
            
            return architecture
            
        except Exception as e:
            raise ArchitectureAnalysisError(
                f"Failed to map current architecture: {e}",
                context={"workspace_root": self._workspace_root}
            ) from e
    
    def _analyze_file_architecture(self, file_path: Path, architecture: Dict[str, Any]) -> None:
        """Analyze a single file's contribution to the architecture."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Handle workspace_root not being set in tests
            if hasattr(self, '_workspace_root'):
                relative_path = str(file_path.relative_to(Path(self._workspace_root)))
            else:
                relative_path = file_path.name
            
            # Extract classes and interfaces
            classes = re.findall(self._analysis_patterns["component_patterns"]["class_definition"], content)
            interfaces = re.findall(self._analysis_patterns["component_patterns"]["interface_definition"], content)
            functions = re.findall(self._analysis_patterns["component_patterns"]["function_definition"], content)
            imports = re.findall(self._analysis_patterns["component_patterns"]["import_statement"], content)
            
            # Store component information
            if classes or interfaces or functions:
                architecture["components"][relative_path] = {
                    "classes": classes,
                    "interfaces": interfaces,
                    "functions": functions,
                    "imports": imports,
                    "file_size": len(content),
                    "line_count": len(content.splitlines())
                }
            
            # Analyze dependencies
            if imports:
                architecture["dependencies"][relative_path] = imports
            
        except Exception as e:
            self._logger.warning(f"Error analyzing file {file_path}: {e}")
    
    def _analyze_directory_structure(self, workspace_path: Path, architecture: Dict[str, Any]) -> None:
        """Analyze the directory structure to understand architectural organization."""
        try:
            # Find all directories
            directories = [d for d in workspace_path.rglob("*") if d.is_dir()]
            
            architecture["directory_structure"] = {}
            
            for directory in directories:
                relative_path = str(directory.relative_to(workspace_path))
                
                # Skip hidden and cache directories
                if any(part.startswith('.') or part == '__pycache__' for part in directory.parts):
                    continue
                
                # Count Python files in directory
                python_files = list(directory.glob("*.py"))
                
                if python_files:
                    architecture["directory_structure"][relative_path] = {
                        "python_files": len(python_files),
                        "subdirectories": len([d for d in directory.iterdir() if d.is_dir()]),
                        "files": [f.name for f in python_files]
                    }
            
        except Exception as e:
            self._logger.warning(f"Error analyzing directory structure: {e}")
    
    def _identify_architectural_layers(self, architecture: Dict[str, Any]) -> None:
        """Identify architectural layers based on directory structure and naming patterns."""
        try:
            layers = {
                "presentation": [],
                "analysis": [],
                "core": [],
                "detection": [],
                "validation": [],
                "installation": [],
                "integration": [],
                "storage": [],
                "plugins": []
            }
            
            # Categorize components by layer
            for component_path, component_info in architecture["components"].items():
                path_parts = component_path.split(os.sep)
                
                # Determine layer based on path
                if "gui" in path_parts or "frontend" in path_parts:
                    layers["presentation"].append(component_path)
                elif "analysis" in path_parts:
                    layers["analysis"].append(component_path)
                elif "core" in path_parts:
                    layers["core"].append(component_path)
                elif "detection" in path_parts:
                    layers["detection"].append(component_path)
                elif "validation" in path_parts:
                    layers["validation"].append(component_path)
                elif "installation" in path_parts:
                    layers["installation"].append(component_path)
                elif "integration" in path_parts:
                    layers["integration"].append(component_path)
                elif "storage" in path_parts:
                    layers["storage"].append(component_path)
                elif "plugin" in path_parts:
                    layers["plugins"].append(component_path)
            
            architecture["layers"] = layers
            
        except Exception as e:
            self._logger.warning(f"Error identifying architectural layers: {e}")
    
    def _load_design_documents(self) -> Dict[str, Any]:
        """Load and parse design documents."""
        try:
            design_data = {}
            
            # Handle specs_path not being set in tests
            specs_path = getattr(self, '_specs_path', None)
            if not specs_path:
                return design_data
            
            # Look for design documents in specs directory
            if os.path.exists(specs_path):
                for spec_dir in os.listdir(specs_path):
                    spec_path = os.path.join(specs_path, spec_dir)
                    if os.path.isdir(spec_path):
                        design_file = os.path.join(spec_path, "design.md")
                        if os.path.exists(design_file):
                            design_data[spec_dir] = self._parse_design_document(design_file)
            
            return design_data
            
        except Exception as e:
            raise ArchitectureAnalysisError(
                f"Failed to load design documents: {e}",
                context={"specs_path": getattr(self, '_specs_path', 'not_set')}
            ) from e
    
    def _parse_design_document(self, file_path: str) -> Dict[str, Any]:
        """Parse a design document and extract architectural information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.splitlines():
                if line.startswith('#'):
                    if current_section:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = line.strip('#').strip().lower()
                    current_content = []
                else:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Extract components and interfaces from design
            components = self._extract_components_from_design(content)
            interfaces = self._extract_interfaces_from_design(content)
            
            return {
                "file_path": file_path,
                "sections": sections,
                "components": components,
                "interfaces": interfaces,
                "parsed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ArchitectureAnalysisError(
                f"Failed to parse design document {file_path}: {e}",
                context={"file_path": file_path}
            ) from e
    
    def _extract_components_from_design(self, content: str) -> List[str]:
        """Extract component names from design document."""
        components = []
        
        # Look for class definitions in code blocks
        code_blocks = re.findall(r'```python(.*?)```', content, re.DOTALL)
        for block in code_blocks:
            classes = re.findall(r'class\s+(\w+)', block)
            components.extend(classes)
        
        # Look for component mentions in text
        component_patterns = [
            r'(\w+Engine)',
            r'(\w+Manager)',
            r'(\w+System)',
            r'(\w+Analyzer)',
            r'(\w+Detector)',
            r'(\w+Validator)'
        ]
        
        for pattern in component_patterns:
            matches = re.findall(pattern, content)
            components.extend(matches)
        
        return list(set(components))  # Remove duplicates
    
    def _extract_interfaces_from_design(self, content: str) -> List[str]:
        """Extract interface names from design document."""
        interfaces = []
        
        # Look for interface definitions in code blocks
        code_blocks = re.findall(r'```python(.*?)```', content, re.DOTALL)
        for block in code_blocks:
            interface_classes = re.findall(r'class\s+(\w+Interface)', block)
            interfaces.extend(interface_classes)
        
        return list(set(interfaces))  # Remove duplicates
    
    def _identify_architectural_gaps(
        self, 
        current_arch: Dict[str, Any], 
        design_arch: Dict[str, Any]
    ) -> List[CriticalGap]:
        """Identify gaps between current architecture and design."""
        gaps = []
        gap_counter = 1
        
        try:
            # Extract expected components from design
            expected_components = set()
            for spec_name, spec_data in design_arch.items():
                expected_components.update(spec_data.get("components", []))
                expected_components.update(spec_data.get("interfaces", []))
            
            # Extract current components
            current_components = set()
            for component_path, component_info in current_arch.get("components", {}).items():
                current_components.update(component_info.get("classes", []))
                current_components.update(component_info.get("interfaces", []))
            
            # Find missing components
            missing_components = expected_components - current_components
            
            for component in missing_components:
                criticality = self._determine_component_criticality(component)
                
                gap = CriticalGap(
                    gap_id=f"gap_{gap_counter:03d}",
                    description=f"Missing component: {component}",
                    criticality=criticality,
                    affected_components=[component],
                    impact_assessment=self._assess_component_impact(component),
                    recommended_action=f"Implement {component} according to design specifications",
                    estimated_effort=self._estimate_implementation_effort(component)
                )
                gaps.append(gap)
                gap_counter += 1
            
            # Check for incomplete implementations
            incomplete_gaps = self._find_incomplete_implementations(current_arch)
            gaps.extend(incomplete_gaps)
            
            return gaps
            
        except Exception as e:
            self._logger.error(f"Error identifying architectural gaps: {e}")
            return gaps
    
    def _determine_component_criticality(self, component_name: str) -> CriticalityLevel:
        """Determine the criticality level of a component based on its name and purpose."""
        component_lower = component_name.lower()
        
        # Security-critical components
        if any(keyword in component_lower for keyword in ['security', 'auth', 'validation', 'integrity']):
            return CriticalityLevel.SECURITY
        
        # Stability-critical components
        if any(keyword in component_lower for keyword in ['core', 'base', 'engine', 'manager']):
            return CriticalityLevel.STABILITY
        
        # Functionality components
        if any(keyword in component_lower for keyword in ['detector', 'analyzer', 'installer']):
            return CriticalityLevel.FUNCTIONALITY
        
        # UX components
        if any(keyword in component_lower for keyword in ['gui', 'interface', 'frontend']):
            return CriticalityLevel.UX
        
        return CriticalityLevel.FUNCTIONALITY  # Default
    
    def _assess_component_impact(self, component_name: str) -> str:
        """Assess the impact of a missing component."""
        criticality = self._determine_component_criticality(component_name)
        
        impact_map = {
            CriticalityLevel.SECURITY: "High - Security vulnerability, system may be compromised",
            CriticalityLevel.STABILITY: "High - System stability affected, potential crashes or data loss",
            CriticalityLevel.FUNCTIONALITY: "Medium - Feature functionality impacted, user experience degraded",
            CriticalityLevel.UX: "Low - User interface affected, usability issues"
        }
        
        return impact_map.get(criticality, "Medium - Impact assessment needed")
    
    def _estimate_implementation_effort(self, component_name: str) -> str:
        """Estimate the effort required to implement a component."""
        component_lower = component_name.lower()
        
        # Complex components
        if any(keyword in component_lower for keyword in ['engine', 'system', 'manager']):
            return "High (5-10 days)"
        
        # Medium complexity components
        if any(keyword in component_lower for keyword in ['analyzer', 'detector', 'validator']):
            return "Medium (2-5 days)"
        
        # Simple components
        if any(keyword in component_lower for keyword in ['interface', 'base', 'model']):
            return "Low (1-2 days)"
        
        return "Medium (2-5 days)"  # Default
    
    def _find_incomplete_implementations(self, current_arch: Dict[str, Any]) -> List[CriticalGap]:
        """Find incomplete implementations in the current architecture."""
        gaps = []
        gap_counter = 1000  # Start from 1000 to distinguish from missing component gaps
        
        try:
            # Look for TODO, FIXME, and other incomplete markers
            for component_path, component_info in current_arch.get("components", {}).items():
                try:
                    with open(os.path.join(self._workspace_root, component_path), 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for incomplete implementation markers
                    for marker_type, markers in self._analysis_patterns["gap_indicators"].items():
                        for marker in markers:
                            if marker in content:
                                criticality = CriticalityLevel.SECURITY if "security" in marker_type else CriticalityLevel.FUNCTIONALITY
                                
                                gap = CriticalGap(
                                    gap_id=f"gap_{gap_counter:03d}",
                                    description=f"Incomplete implementation in {component_path}: {marker}",
                                    criticality=criticality,
                                    affected_components=[component_path],
                                    impact_assessment=f"Incomplete implementation may cause {marker_type}",
                                    recommended_action=f"Complete implementation in {component_path}",
                                    estimated_effort="Low (1-2 days)"
                                )
                                gaps.append(gap)
                                gap_counter += 1
                
                except Exception as e:
                    self._logger.warning(f"Error checking file {component_path}: {e}")
            
            return gaps
            
        except Exception as e:
            self._logger.error(f"Error finding incomplete implementations: {e}")
            return gaps
    
    def _identify_lost_functionalities(
        self, 
        current_arch: Dict[str, Any], 
        design_arch: Dict[str, Any]
    ) -> List[LostFunctionality]:
        """Identify functionalities that were lost during refactoring."""
        lost_functionalities = []
        functionality_counter = 1
        
        try:
            # This is a simplified implementation - in a real scenario, you'd compare
            # with previous versions or git history
            
            # Look for design-specified functionalities that aren't implemented
            for spec_name, spec_data in design_arch.items():
                sections = spec_data.get("sections", {})
                
                # Check for functionality mentioned in design but not found in current implementation
                if "components and interfaces" in sections:
                    content = sections["components and interfaces"]
                    
                    # Extract functionality descriptions
                    functionality_patterns = [
                        r'(\w+) functionality',
                        r'provides (\w+)',
                        r'handles (\w+)',
                        r'manages (\w+)'
                    ]
                    
                    for pattern in functionality_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Check if this functionality exists in current implementation
                            if not self._functionality_exists_in_current(match, current_arch):
                                lost_func = LostFunctionality(
                                    functionality_id=f"lost_{functionality_counter:03d}",
                                    name=match,
                                    description=f"Functionality '{match}' mentioned in design but not found in implementation",
                                    original_location=f"Design document: {spec_name}",
                                    last_seen_version=None,
                                    impact_on_users="Functionality not available to users",
                                    recovery_complexity="Medium - requires implementation according to design"
                                )
                                lost_functionalities.append(lost_func)
                                functionality_counter += 1
            
            return lost_functionalities
            
        except Exception as e:
            self._logger.error(f"Error identifying lost functionalities: {e}")
            return lost_functionalities
    
    def _functionality_exists_in_current(self, functionality: str, current_arch: Dict[str, Any]) -> bool:
        """Check if a functionality exists in the current implementation."""
        functionality_lower = functionality.lower()
        
        # Check in component names and functions
        for component_path, component_info in current_arch.get("components", {}).items():
            # Check class names
            for class_name in component_info.get("classes", []):
                if functionality_lower in class_name.lower():
                    return True
            
            # Check function names
            for func_name in component_info.get("functions", []):
                if functionality_lower in func_name.lower():
                    return True
        
        return False
    
    def _check_consistency_issues(self) -> List[ConsistencyIssue]:
        """Check for consistency issues in the current implementation."""
        issues = []
        issue_counter = 1
        
        try:
            # This is a placeholder for consistency checking logic
            # In a real implementation, you'd check for:
            # - Naming convention violations
            # - Interface implementation mismatches
            # - Architectural pattern violations
            
            # For now, return empty list
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking consistency issues: {e}")
            return issues
    
    def _prioritize_fixes(self, gaps: List[CriticalGap]) -> List[PrioritizedFix]:
        """Convert gaps to prioritized fixes."""
        return self.prioritize_by_criticality(gaps)
    
    def _analyze_fix_dependencies(self, gap: CriticalGap) -> List[str]:
        """Analyze dependencies for fixing a gap."""
        dependencies = []
        
        # Basic dependency analysis based on component type
        if "Engine" in gap.description:
            dependencies.extend(["Core interfaces", "Base classes"])
        elif "Manager" in gap.description:
            dependencies.extend(["Configuration system", "Logging system"])
        elif "Interface" in gap.description:
            dependencies.extend(["Base interfaces"])
        
        return dependencies
    
    def _define_success_criteria(self, gap: CriticalGap) -> List[str]:
        """Define success criteria for fixing a gap."""
        criteria = [
            f"Component {gap.affected_components[0]} is implemented",
            "All unit tests pass",
            "Integration tests pass",
            "Code review completed"
        ]
        
        if gap.criticality == CriticalityLevel.SECURITY:
            criteria.append("Security review completed")
        
        return criteria
    
    def _find_architectural_matches(
        self, 
        current_arch: Dict[str, Any], 
        design_data: Dict[str, Any]
    ) -> List[str]:
        """Find components that match between current architecture and design."""
        matches = []
        
        # Get current components
        current_components = set()
        for component_info in current_arch.get("components", {}).values():
            current_components.update(component_info.get("classes", []))
            current_components.update(component_info.get("interfaces", []))
        
        # Get design components
        design_components = set()
        for spec_data in design_data.values():
            design_components.update(spec_data.get("components", []))
            design_components.update(spec_data.get("interfaces", []))
        
        # Find matches
        matches = list(current_components.intersection(design_components))
        
        return matches
    
    def _find_missing_components(
        self, 
        current_arch: Dict[str, Any], 
        design_data: Dict[str, Any]
    ) -> List[str]:
        """Find components that are in design but missing from current implementation."""
        # Get current components
        current_components = set()
        for component_info in current_arch.get("components", {}).values():
            current_components.update(component_info.get("classes", []))
            current_components.update(component_info.get("interfaces", []))
        
        # Get design components
        design_components = set()
        for spec_data in design_data.values():
            design_components.update(spec_data.get("components", []))
            design_components.update(spec_data.get("interfaces", []))
        
        # Find missing
        missing = list(design_components - current_components)
        
        return missing
    
    def _find_extra_components(
        self, 
        current_arch: Dict[str, Any], 
        design_data: Dict[str, Any]
    ) -> List[str]:
        """Find components that are in current implementation but not in design."""
        # Get current components
        current_components = set()
        for component_info in current_arch.get("components", {}).values():
            current_components.update(component_info.get("classes", []))
            current_components.update(component_info.get("interfaces", []))
        
        # Get design components
        design_components = set()
        for spec_data in design_data.values():
            design_components.update(spec_data.get("components", []))
            design_components.update(spec_data.get("interfaces", []))
        
        # Find extra
        extra = list(current_components - design_components)
        
        return extra
    
    def _find_architectural_differences(
        self, 
        current_arch: Dict[str, Any], 
        design_data: Dict[str, Any]
    ) -> List[str]:
        """Find architectural differences between current and design."""
        differences = []
        
        # Compare layer organization
        current_layers = set(current_arch.get("layers", {}).keys())
        
        # Expected layers from design (simplified)
        expected_layers = {
            "presentation", "analysis", "core", "detection", 
            "validation", "installation", "integration"
        }
        
        missing_layers = expected_layers - current_layers
        for layer in missing_layers:
            differences.append(f"Missing architectural layer: {layer}")
        
        extra_layers = current_layers - expected_layers
        for layer in extra_layers:
            differences.append(f"Extra architectural layer: {layer}")
        
        return differences