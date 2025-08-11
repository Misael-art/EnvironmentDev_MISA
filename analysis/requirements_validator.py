"""
Requirements Consistency Validator implementation.

This module provides the RequirementsConsistencyValidator class that handles
parsing multiple requirements documents and validating consistency between them.
"""

import os
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path

from .base import AnalysisBase
from .interfaces import (
    ConsistencyResult,
    ConsistencyIssue,
    CriticalityLevel
)
from ..core.base import OperationResult
from ..core.exceptions import ArchitectureAnalysisError


class RequirementsConsistencyValidator(AnalysisBase):
    """
    Validator for requirements consistency across multiple documents.
    
    Provides comprehensive parsing of requirements documents and validation
    of consistency between multiple requirements files.
    """
    
    def __init__(self, config_manager, component_name: str = "RequirementsConsistencyValidator"):
        """Initialize the requirements consistency validator."""
        super().__init__(config_manager, component_name)
        self._parsing_patterns = self._initialize_parsing_patterns()
        self._consistency_rules = self._initialize_consistency_rules()
        self._validation_weights = self._initialize_validation_weights()
    
    def initialize(self) -> None:
        """Initialize the requirements consistency validator."""
        try:
            self._logger.info("Initializing Requirements Consistency Validator")
            
            # Initialize parsing patterns and validation rules
            self._parsing_patterns = self._initialize_parsing_patterns()
            self._consistency_rules = self._initialize_consistency_rules()
            self._validation_weights = self._initialize_validation_weights()
            
            # Set up workspace paths
            config = self.get_config()
            self._workspace_root = getattr(config, 'workspace_root', '.')
            self._specs_path = os.path.join(self._workspace_root, '.kiro', 'specs')
            
            self._logger.info("Requirements Consistency Validator initialized successfully")
            
        except Exception as e:
            self._handle_error(e, "initialize")
    
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
            
            # Check cache first
            cache_key = f"consistency_{hash(tuple(sorted(req_files)))}"
            cached_result = self._get_cached_result(cache_key, max_age_seconds=1800)
            if cached_result:
                self._logger.info("Using cached consistency validation result")
                return cached_result
            
            # Parse all requirements documents
            parsed_requirements = self._parse_multiple_requirements_documents(req_files)
            
            if not parsed_requirements:
                return ConsistencyResult(
                    is_consistent=True,
                    total_requirements_checked=0,
                    consistency_issues=[],
                    consistency_score=1.0,
                    recommendations=["No requirements files found to validate"]
                )
            
            # Perform comprehensive consistency validation
            consistency_issues = self._perform_comprehensive_consistency_validation(parsed_requirements)
            
            # Calculate consistency metrics
            total_requirements = self._count_total_requirements(parsed_requirements)
            consistency_score = self._calculate_comprehensive_consistency_score(consistency_issues, total_requirements)
            
            # Generate detailed recommendations
            recommendations = self._generate_detailed_consistency_recommendations(consistency_issues, parsed_requirements)
            
            result = ConsistencyResult(
                is_consistent=len(consistency_issues) == 0,
                total_requirements_checked=total_requirements,
                consistency_issues=consistency_issues,
                consistency_score=consistency_score,
                recommendations=recommendations
            )
            
            # Cache the result
            self._cache_analysis_result(cache_key, result)
            
            self._logger.info(f"Requirements consistency validation completed. "
                            f"Score: {consistency_score:.2f}, Issues: {len(consistency_issues)}")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "validate_requirements_consistency", {"req_files": req_files})
    
    def parse_requirements_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a single requirements document with comprehensive extraction.
        
        Args:
            file_path: Path to the requirements document
            
        Returns:
            Dict containing parsed requirements data
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info(f"Parsing requirements document: {file_path}")
            
            if not os.path.exists(file_path):
                raise ArchitectureAnalysisError(
                    f"Requirements file not found: {file_path}",
                    context={"file_path": file_path}
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract document metadata
            metadata = self._extract_document_metadata(content, file_path)
            
            # Parse requirements sections
            requirements = self._parse_requirements_sections(content)
            
            # Extract cross-references
            cross_references = self._extract_cross_references(content)
            
            # Analyze requirement structure
            structure_analysis = self._analyze_requirement_structure(requirements)
            
            parsed_data = {
                "file_path": file_path,
                "metadata": metadata,
                "requirements": requirements,
                "cross_references": cross_references,
                "structure_analysis": structure_analysis,
                "parsed_at": datetime.now().isoformat(),
                "content_hash": hash(content)
            }
            
            self._logger.info(f"Parsed {len(requirements)} requirements from {file_path}")
            
            return parsed_data
            
        except Exception as e:
            self._handle_error(e, "parse_requirements_document", {"file_path": file_path})
    
    def generate_consistency_report(self, consistency_result: ConsistencyResult) -> str:
        """
        Generate a detailed consistency report.
        
        Args:
            consistency_result: Result of consistency validation
            
        Returns:
            Formatted consistency report
        """
        self.ensure_initialized()
        self._record_operation()
        
        try:
            self._logger.info("Generating detailed consistency report")
            
            report_sections = []
            
            # Executive Summary
            report_sections.append(self._generate_executive_summary(consistency_result))
            
            # Detailed Issues Analysis
            if consistency_result.consistency_issues:
                report_sections.append(self._generate_issues_analysis(consistency_result.consistency_issues))
            
            # Consistency Metrics
            report_sections.append(self._generate_consistency_metrics(consistency_result))
            
            # Recommendations
            report_sections.append(self._generate_recommendations_section(consistency_result.recommendations))
            
            # Action Plan
            report_sections.append(self._generate_action_plan_section(consistency_result.consistency_issues))
            
            # Combine all sections
            report = "\n\n".join(report_sections)
            
            self._logger.info("Consistency report generated successfully")
            
            return report
            
        except Exception as e:
            self._handle_error(e, "generate_consistency_report")
    
    def _initialize_parsing_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for parsing requirements documents."""
        return {
            "requirement_headers": [
                r"###\s+(Requisito|Requirement)\s+(\d+(?:\.\d+)*):?\s*(.+)",
                r"##\s+(Requisito|Requirement)\s+(\d+(?:\.\d+)*):?\s*(.+)",
                r"#\s+(Requisito|Requirement)\s+(\d+(?:\.\d+)*):?\s*(.+)"
            ],
            "user_story_patterns": [
                r"\*\*User Story:\*\*\s*(.+)",
                r"User Story:\s*(.+)",
                r"Como\s+(.+?),\s*eu\s+quero\s+(.+?),\s*para\s+que\s+(.+)"
            ],
            "acceptance_criteria_patterns": [
                r"####\s+Acceptance Criteria",
                r"###\s+Acceptance Criteria",
                r"##\s+Acceptance Criteria",
                r"Critérios de Aceitação"
            ],
            "criteria_item_patterns": [
                r"^\s*(\d+)\.\s+(WHEN|IF|GIVEN)\s+(.+?)\s+(THEN|AND)\s+(.+)",
                r"^\s*-\s+(WHEN|IF|GIVEN)\s+(.+?)\s+(THEN|AND)\s+(.+)",
                r"^\s*\*\s+(WHEN|IF|GIVEN)\s+(.+?)\s+(THEN|AND)\s+(.+)"
            ],
            "cross_reference_patterns": [
                r"Requirements?:?\s*([\d\.,\s]+)",
                r"Requisitos?:?\s*([\d\.,\s]+)",
                r"_Requirements?:\s*([\d\.,\s]+)_",
                r"Ref:\s*([\d\.,\s]+)"
            ]
        }
    
    def _initialize_consistency_rules(self) -> Dict[str, Any]:
        """Initialize rules for consistency validation."""
        return {
            "duplicate_id_check": {
                "enabled": True,
                "severity": "High",
                "description": "Check for duplicate requirement IDs across documents"
            },
            "conflicting_criteria_check": {
                "enabled": True,
                "severity": "Medium",
                "description": "Check for conflicting acceptance criteria in similar requirements"
            },
            "missing_cross_references_check": {
                "enabled": True,
                "severity": "Low",
                "description": "Check for missing cross-references between related requirements"
            },
            "inconsistent_terminology_check": {
                "enabled": True,
                "severity": "Medium",
                "description": "Check for inconsistent terminology usage across documents"
            },
            "structural_consistency_check": {
                "enabled": True,
                "severity": "Low",
                "description": "Check for consistent document structure and formatting"
            },
            "completeness_check": {
                "enabled": True,
                "severity": "High",
                "description": "Check for incomplete requirements (missing user stories or criteria)"
            }
        }
    
    def _initialize_validation_weights(self) -> Dict[str, float]:
        """Initialize weights for different validation aspects."""
        return {
            "duplicate_ids": 1.0,
            "conflicting_criteria": 0.8,
            "missing_cross_references": 0.3,
            "inconsistent_terminology": 0.6,
            "structural_inconsistency": 0.4,
            "incomplete_requirements": 0.9
        }
    
    def _parse_multiple_requirements_documents(self, req_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse multiple requirements documents."""
        parsed_requirements = {}
        
        for req_file in req_files:
            try:
                if os.path.exists(req_file):
                    parsed_requirements[req_file] = self.parse_requirements_document(req_file)
                else:
                    self._logger.warning(f"Requirements file not found: {req_file}")
            except Exception as e:
                self._logger.error(f"Error parsing requirements file {req_file}: {e}")
        
        return parsed_requirements
    
    def _extract_document_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        metadata = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "line_count": len(content.splitlines()),
            "character_count": len(content),
            "language": self._detect_document_language(content),
            "document_title": self._extract_document_title(content),
            "creation_date": self._extract_creation_date(content),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() if os.path.exists(file_path) else None
        }
        
        return metadata
    
    def _detect_document_language(self, content: str) -> str:
        """Detect the language of the document."""
        # Simple language detection based on keywords
        portuguese_keywords = ["Requisito", "Como", "eu quero", "para que", "Critérios de Aceitação"]
        english_keywords = ["Requirement", "As a", "I want", "so that", "Acceptance Criteria"]
        
        portuguese_count = sum(1 for keyword in portuguese_keywords if keyword in content)
        english_count = sum(1 for keyword in english_keywords if keyword in content)
        
        if portuguese_count > english_count:
            return "Portuguese"
        elif english_count > portuguese_count:
            return "English"
        else:
            return "Unknown"
    
    def _extract_document_title(self, content: str) -> Optional[str]:
        """Extract document title from content."""
        lines = content.splitlines()
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('#') and not line.startswith('##'):
                return line.lstrip('#').strip()
        return None
    
    def _extract_creation_date(self, content: str) -> Optional[str]:
        """Extract creation date from content."""
        # Look for date patterns in the first few lines
        date_patterns = [
            r"Created?:?\s*(\d{4}-\d{2}-\d{2})",
            r"Date:?\s*(\d{4}-\d{2}-\d{2})",
            r"(\d{4}-\d{2}-\d{2})"
        ]
        
        lines = content.splitlines()[:20]  # Check first 20 lines
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
        
        return None
    
    def _parse_requirements_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse requirements sections from content."""
        requirements = []
        lines = content.splitlines()
        current_requirement = None
        current_section = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for requirement headers
            requirement_match = self._match_requirement_header(line_stripped)
            if requirement_match:
                # Save previous requirement
                if current_requirement:
                    requirements.append(current_requirement)
                
                # Start new requirement
                current_requirement = {
                    "id": requirement_match["id"],
                    "title": requirement_match["title"],
                    "line_number": i + 1,
                    "user_story": "",
                    "acceptance_criteria": [],
                    "cross_references": [],
                    "metadata": {
                        "section_start": i + 1,
                        "section_end": None
                    }
                }
                current_section = "header"
                continue
            
            if not current_requirement:
                continue
            
            # Check for user story
            user_story_match = self._match_user_story(line_stripped)
            if user_story_match:
                current_requirement["user_story"] = user_story_match
                current_section = "user_story"
                continue
            
            # Check for acceptance criteria section
            if self._is_acceptance_criteria_header(line_stripped):
                current_section = "acceptance_criteria"
                continue
            
            # Parse acceptance criteria items
            if current_section == "acceptance_criteria":
                criteria_match = self._match_criteria_item(line_stripped)
                if criteria_match:
                    current_requirement["acceptance_criteria"].append(criteria_match)
                    continue
            
            # Extract cross-references
            cross_refs = self._extract_line_cross_references(line_stripped)
            if cross_refs:
                current_requirement["cross_references"].extend(cross_refs)
        
        # Add the last requirement
        if current_requirement:
            requirements.append(current_requirement)
        
        # Set section end line numbers
        for i, req in enumerate(requirements):
            if i < len(requirements) - 1:
                req["metadata"]["section_end"] = requirements[i + 1]["metadata"]["section_start"] - 1
            else:
                req["metadata"]["section_end"] = len(lines)
        
        return requirements
    
    def _match_requirement_header(self, line: str) -> Optional[Dict[str, str]]:
        """Match requirement header patterns."""
        for pattern in self._parsing_patterns["requirement_headers"]:
            match = re.match(pattern, line)
            if match:
                return {
                    "type": match.group(1),
                    "id": match.group(2),
                    "title": match.group(3) if len(match.groups()) >= 3 else ""
                }
        return None
    
    def _match_user_story(self, line: str) -> Optional[str]:
        """Match user story patterns."""
        for pattern in self._parsing_patterns["user_story_patterns"]:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) == 1:
                    return match.group(1).strip()
                elif len(match.groups()) == 3:
                    # Portuguese format: Como X, eu quero Y, para que Z
                    return f"Como {match.group(1)}, eu quero {match.group(2)}, para que {match.group(3)}"
        return None
    
    def _is_acceptance_criteria_header(self, line: str) -> bool:
        """Check if line is an acceptance criteria header."""
        for pattern in self._parsing_patterns["acceptance_criteria_patterns"]:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _match_criteria_item(self, line: str) -> Optional[Dict[str, str]]:
        """Match acceptance criteria item patterns."""
        for pattern in self._parsing_patterns["criteria_item_patterns"]:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 4:
                    return {
                        "condition": f"{groups[1]} {groups[2]}".strip(),
                        "result": f"{groups[3]} {groups[4]}".strip() if len(groups) >= 5 else groups[3].strip(),
                        "full_text": line.strip()
                    }
                elif len(groups) >= 3:
                    return {
                        "condition": f"{groups[0]} {groups[1]}".strip(),
                        "result": f"{groups[2]}".strip(),
                        "full_text": line.strip()
                    }
        return None
    
    def _extract_line_cross_references(self, line: str) -> List[str]:
        """Extract cross-references from a line."""
        cross_refs = []
        
        for pattern in self._parsing_patterns["cross_reference_patterns"]:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Parse comma-separated requirement IDs
                ref_text = match.group(1).strip()
                refs = [ref.strip() for ref in re.split(r'[,\s]+', ref_text) if ref.strip()]
                cross_refs.extend(refs)
        
        return cross_refs
    
    def _extract_cross_references(self, content: str) -> List[str]:
        """Extract all cross-references from content."""
        all_cross_refs = []
        
        for line in content.splitlines():
            line_refs = self._extract_line_cross_references(line.strip())
            all_cross_refs.extend(line_refs)
        
        return list(set(all_cross_refs))  # Remove duplicates
    
    def _analyze_requirement_structure(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure of parsed requirements."""
        analysis = {
            "total_requirements": len(requirements),
            "requirements_with_user_stories": 0,
            "requirements_with_acceptance_criteria": 0,
            "requirements_with_cross_references": 0,
            "average_criteria_per_requirement": 0,
            "id_format_consistency": True,
            "structural_issues": []
        }
        
        total_criteria = 0
        id_formats = set()
        
        for req in requirements:
            # Count requirements with user stories
            if req.get("user_story"):
                analysis["requirements_with_user_stories"] += 1
            else:
                analysis["structural_issues"].append(f"Requirement {req['id']} missing user story")
            
            # Count requirements with acceptance criteria
            if req.get("acceptance_criteria"):
                analysis["requirements_with_acceptance_criteria"] += 1
                total_criteria += len(req["acceptance_criteria"])
            else:
                analysis["structural_issues"].append(f"Requirement {req['id']} missing acceptance criteria")
            
            # Count requirements with cross-references
            if req.get("cross_references"):
                analysis["requirements_with_cross_references"] += 1
            
            # Analyze ID format
            id_format = self._analyze_id_format(req["id"])
            id_formats.add(id_format)
        
        # Calculate averages
        if analysis["total_requirements"] > 0:
            analysis["average_criteria_per_requirement"] = total_criteria / analysis["total_requirements"]
        
        # Check ID format consistency
        analysis["id_format_consistency"] = len(id_formats) <= 1
        if not analysis["id_format_consistency"]:
            analysis["structural_issues"].append(f"Inconsistent ID formats found: {list(id_formats)}")
        
        return analysis
    
    def _analyze_id_format(self, req_id: str) -> str:
        """Analyze the format of a requirement ID."""
        # Extract just the ID part (remove "Requisito" or "Requirement")
        id_part = re.sub(r'^(Requisito|Requirement)\s+', '', req_id, flags=re.IGNORECASE)
        
        if re.match(r'^\d+$', id_part):
            return "numeric"
        elif re.match(r'^\d+\.\d+$', id_part):
            return "decimal"
        elif re.match(r'^[A-Z]+\d+$', id_part):
            return "alphanumeric"
        else:
            return "custom"    

    def _perform_comprehensive_consistency_validation(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]]
    ) -> List[ConsistencyIssue]:
        """Perform comprehensive consistency validation."""
        all_issues = []
        issue_counter = 1
        
        try:
            # Check for duplicate requirement IDs
            if self._consistency_rules["duplicate_id_check"]["enabled"]:
                duplicate_issues = self._check_duplicate_requirement_ids(parsed_requirements, issue_counter)
                all_issues.extend(duplicate_issues)
                issue_counter += len(duplicate_issues)
            
            # Check for conflicting acceptance criteria
            if self._consistency_rules["conflicting_criteria_check"]["enabled"]:
                criteria_issues = self._check_conflicting_acceptance_criteria(parsed_requirements, issue_counter)
                all_issues.extend(criteria_issues)
                issue_counter += len(criteria_issues)
            
            # Check for missing cross-references
            if self._consistency_rules["missing_cross_references_check"]["enabled"]:
                cross_ref_issues = self._check_missing_cross_references(parsed_requirements, issue_counter)
                all_issues.extend(cross_ref_issues)
                issue_counter += len(cross_ref_issues)
            
            # Check for inconsistent terminology
            if self._consistency_rules["inconsistent_terminology_check"]["enabled"]:
                terminology_issues = self._check_inconsistent_terminology(parsed_requirements, issue_counter)
                all_issues.extend(terminology_issues)
                issue_counter += len(terminology_issues)
            
            # Check for structural consistency
            if self._consistency_rules["structural_consistency_check"]["enabled"]:
                structural_issues = self._check_structural_consistency(parsed_requirements, issue_counter)
                all_issues.extend(structural_issues)
                issue_counter += len(structural_issues)
            
            # Check for completeness
            if self._consistency_rules["completeness_check"]["enabled"]:
                completeness_issues = self._check_requirements_completeness(parsed_requirements, issue_counter)
                all_issues.extend(completeness_issues)
                issue_counter += len(completeness_issues)
            
            return all_issues
            
        except Exception as e:
            self._logger.error(f"Error in comprehensive consistency validation: {e}")
            return all_issues
    
    def _check_duplicate_requirement_ids(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for duplicate requirement IDs across documents."""
        issues = []
        
        try:
            # Collect all requirement IDs with their sources
            id_occurrences = {}
            
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    req_id = req.get("id", "")
                    if req_id:
                        if req_id not in id_occurrences:
                            id_occurrences[req_id] = []
                        id_occurrences[req_id].append({
                            "file": file_path,
                            "line": req.get("line_number", 0),
                            "title": req.get("title", "")
                        })
            
            # Find duplicates
            for req_id, occurrences in id_occurrences.items():
                if len(occurrences) > 1:
                    issue = ConsistencyIssue(
                        issue_id=f"consistency_{issue_counter:03d}",
                        description=f"Duplicate requirement ID '{req_id}' found in {len(occurrences)} documents",
                        conflicting_documents=[occ["file"] for occ in occurrences],
                        conflicting_requirements=[req_id],
                        severity=self._consistency_rules["duplicate_id_check"]["severity"],
                        resolution_suggestion=f"Ensure requirement ID '{req_id}' is unique across all documents. "
                                            f"Consider using prefixes or different numbering schemes."
                    )
                    issues.append(issue)
                    issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking duplicate requirement IDs: {e}")
            return issues
    
    def _check_conflicting_acceptance_criteria(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for conflicting acceptance criteria in similar requirements."""
        issues = []
        
        try:
            # Collect all requirements with their criteria
            all_requirements = []
            
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    all_requirements.append({
                        "file": file_path,
                        "id": req.get("id", ""),
                        "title": req.get("title", ""),
                        "user_story": req.get("user_story", ""),
                        "acceptance_criteria": req.get("acceptance_criteria", [])
                    })
            
            # Compare requirements for similarity and conflicting criteria
            for i, req1 in enumerate(all_requirements):
                for req2 in all_requirements[i+1:]:
                    # Calculate similarity
                    similarity = self._calculate_requirement_similarity(req1, req2)
                    
                    if similarity > 0.7:  # High similarity threshold
                        # Check for conflicting criteria
                        conflicts = self._find_criteria_conflicts(req1["acceptance_criteria"], req2["acceptance_criteria"])
                        
                        if conflicts:
                            issue = ConsistencyIssue(
                                issue_id=f"consistency_{issue_counter:03d}",
                                description=f"Similar requirements with conflicting acceptance criteria: "
                                          f"'{req1['id']}' vs '{req2['id']}'",
                                conflicting_documents=[req1["file"], req2["file"]],
                                conflicting_requirements=[req1["id"], req2["id"]],
                                severity=self._consistency_rules["conflicting_criteria_check"]["severity"],
                                resolution_suggestion=f"Review and align acceptance criteria for similar requirements. "
                                                    f"Conflicts found: {', '.join(conflicts)}"
                            )
                            issues.append(issue)
                            issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking conflicting acceptance criteria: {e}")
            return issues
    
    def _check_missing_cross_references(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for missing cross-references between related requirements."""
        issues = []
        
        try:
            # Collect all requirement IDs
            all_req_ids = set()
            requirements_by_id = {}
            
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    req_id = req.get("id", "")
                    if req_id:
                        all_req_ids.add(req_id)
                        requirements_by_id[req_id] = {
                            "file": file_path,
                            "requirement": req
                        }
            
            # Check for broken cross-references
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    cross_refs = req.get("cross_references", [])
                    
                    for ref in cross_refs:
                        if ref not in all_req_ids:
                            issue = ConsistencyIssue(
                                issue_id=f"consistency_{issue_counter:03d}",
                                description=f"Broken cross-reference in requirement '{req['id']}': "
                                          f"references non-existent requirement '{ref}'",
                                conflicting_documents=[file_path],
                                conflicting_requirements=[req["id"]],
                                severity=self._consistency_rules["missing_cross_references_check"]["severity"],
                                resolution_suggestion=f"Verify that requirement '{ref}' exists or remove the reference"
                            )
                            issues.append(issue)
                            issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking missing cross-references: {e}")
            return issues
    
    def _check_inconsistent_terminology(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for inconsistent terminology usage across documents."""
        issues = []
        
        try:
            # Extract terminology from all documents
            terminology_usage = {}
            
            for file_path, doc_data in parsed_requirements.items():
                # Check document language consistency
                doc_language = doc_data.get("metadata", {}).get("language", "Unknown")
                
                if doc_language not in terminology_usage:
                    terminology_usage[doc_language] = []
                terminology_usage[doc_language].append(file_path)
            
            # Check for mixed languages
            if len(terminology_usage) > 1:
                issue = ConsistencyIssue(
                    issue_id=f"consistency_{issue_counter:03d}",
                    description="Inconsistent language usage across requirements documents",
                    conflicting_documents=list(parsed_requirements.keys()),
                    conflicting_requirements=[],
                    severity=self._consistency_rules["inconsistent_terminology_check"]["severity"],
                    resolution_suggestion="Standardize on a single language for all requirements documents"
                )
                issues.append(issue)
                issue_counter += 1
            
            # Check for inconsistent key terms
            key_terms = self._extract_key_terms(parsed_requirements)
            term_inconsistencies = self._find_term_inconsistencies(key_terms)
            
            for inconsistency in term_inconsistencies:
                issue = ConsistencyIssue(
                    issue_id=f"consistency_{issue_counter:03d}",
                    description=f"Inconsistent terminology: {inconsistency['description']}",
                    conflicting_documents=inconsistency["files"],
                    conflicting_requirements=[],
                    severity=self._consistency_rules["inconsistent_terminology_check"]["severity"],
                    resolution_suggestion=f"Standardize terminology: {inconsistency['suggestion']}"
                )
                issues.append(issue)
                issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking inconsistent terminology: {e}")
            return issues
    
    def _check_structural_consistency(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for structural consistency across documents."""
        issues = []
        
        try:
            # Analyze structure of each document
            document_structures = {}
            
            for file_path, doc_data in parsed_requirements.items():
                structure_analysis = doc_data.get("structure_analysis", {})
                document_structures[file_path] = structure_analysis
            
            # Check for structural inconsistencies
            if len(document_structures) > 1:
                # Compare ID format consistency
                id_formats = set()
                for file_path, structure in document_structures.items():
                    if not structure.get("id_format_consistency", True):
                        issue = ConsistencyIssue(
                            issue_id=f"consistency_{issue_counter:03d}",
                            description=f"Inconsistent requirement ID formats within document: {file_path}",
                            conflicting_documents=[file_path],
                            conflicting_requirements=[],
                            severity=self._consistency_rules["structural_consistency_check"]["severity"],
                            resolution_suggestion="Use consistent ID format throughout the document"
                        )
                        issues.append(issue)
                        issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking structural consistency: {e}")
            return issues
    
    def _check_requirements_completeness(
        self, 
        parsed_requirements: Dict[str, Dict[str, Any]], 
        issue_counter: int
    ) -> List[ConsistencyIssue]:
        """Check for incomplete requirements."""
        issues = []
        
        try:
            for file_path, doc_data in parsed_requirements.items():
                for req in doc_data.get("requirements", []):
                    req_id = req.get("id", "")
                    
                    # Check for missing user story
                    if not req.get("user_story"):
                        issue = ConsistencyIssue(
                            issue_id=f"consistency_{issue_counter:03d}",
                            description=f"Requirement '{req_id}' missing user story",
                            conflicting_documents=[file_path],
                            conflicting_requirements=[req_id],
                            severity=self._consistency_rules["completeness_check"]["severity"],
                            resolution_suggestion=f"Add user story to requirement '{req_id}'"
                        )
                        issues.append(issue)
                        issue_counter += 1
                    
                    # Check for missing acceptance criteria
                    if not req.get("acceptance_criteria"):
                        issue = ConsistencyIssue(
                            issue_id=f"consistency_{issue_counter:03d}",
                            description=f"Requirement '{req_id}' missing acceptance criteria",
                            conflicting_documents=[file_path],
                            conflicting_requirements=[req_id],
                            severity=self._consistency_rules["completeness_check"]["severity"],
                            resolution_suggestion=f"Add acceptance criteria to requirement '{req_id}'"
                        )
                        issues.append(issue)
                        issue_counter += 1
            
            return issues
            
        except Exception as e:
            self._logger.error(f"Error checking requirements completeness: {e}")
            return issues
    
    def _calculate_requirement_similarity(self, req1: Dict[str, Any], req2: Dict[str, Any]) -> float:
        """Calculate similarity between two requirements."""
        try:
            # Compare titles
            title_similarity = self._calculate_text_similarity(req1.get("title", ""), req2.get("title", ""))
            
            # Compare user stories
            story_similarity = self._calculate_text_similarity(req1.get("user_story", ""), req2.get("user_story", ""))
            
            # Weighted average
            similarity = (title_similarity * 0.6) + (story_similarity * 0.4)
            
            return similarity
            
        except Exception as e:
            self._logger.error(f"Error calculating requirement similarity: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _find_criteria_conflicts(self, criteria1: List[Dict[str, str]], criteria2: List[Dict[str, str]]) -> List[str]:
        """Find conflicts between acceptance criteria."""
        conflicts = []
        
        try:
            # Compare criteria for contradictions
            for c1 in criteria1:
                for c2 in criteria2:
                    # Check for contradictory conditions or results
                    if self._are_criteria_contradictory(c1, c2):
                        conflicts.append(f"'{c1.get('full_text', '')}' vs '{c2.get('full_text', '')}'")
            
            return conflicts
            
        except Exception as e:
            self._logger.error(f"Error finding criteria conflicts: {e}")
            return conflicts
    
    def _are_criteria_contradictory(self, criteria1: Dict[str, str], criteria2: Dict[str, str]) -> bool:
        """Check if two criteria are contradictory."""
        # Simple contradiction detection based on keywords
        text1 = criteria1.get("full_text", "").lower()
        text2 = criteria2.get("full_text", "").lower()
        
        # Look for opposite keywords
        contradictory_pairs = [
            ("shall", "shall not"),
            ("must", "must not"),
            ("will", "will not"),
            ("should", "should not"),
            ("allow", "prevent"),
            ("enable", "disable")
        ]
        
        for positive, negative in contradictory_pairs:
            if positive in text1 and negative in text2:
                return True
            if negative in text1 and positive in text2:
                return True
        
        return False
    
    def _extract_key_terms(self, parsed_requirements: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract key terms from all requirements."""
        key_terms = {}
        
        for file_path, doc_data in parsed_requirements.items():
            terms = []
            
            for req in doc_data.get("requirements", []):
                # Extract terms from title and user story
                title_terms = self._extract_terms_from_text(req.get("title", ""))
                story_terms = self._extract_terms_from_text(req.get("user_story", ""))
                
                terms.extend(title_terms)
                terms.extend(story_terms)
            
            key_terms[file_path] = list(set(terms))  # Remove duplicates
        
        return key_terms
    
    def _extract_terms_from_text(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Simple term extraction - look for important nouns and verbs
        important_words = []
        
        # Remove common words and extract meaningful terms
        common_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "as", "i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can", "must", "shall"
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        important_words = [word for word in words if len(word) > 3 and word not in common_words]
        
        return important_words
    
    def _find_term_inconsistencies(self, key_terms: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find terminology inconsistencies across documents."""
        inconsistencies = []
        
        # This is a simplified implementation
        # In a real system, you might use more sophisticated NLP techniques
        
        return inconsistencies
    
    def _count_total_requirements(self, parsed_requirements: Dict[str, Dict[str, Any]]) -> int:
        """Count total requirements across all documents."""
        total = 0
        for doc_data in parsed_requirements.values():
            total += len(doc_data.get("requirements", []))
        return total
    
    def _calculate_comprehensive_consistency_score(
        self, 
        issues: List[ConsistencyIssue], 
        total_requirements: int
    ) -> float:
        """Calculate comprehensive consistency score."""
        if total_requirements == 0:
            return 1.0
        
        # Weight issues by severity and type
        severity_weights = {"High": 1.0, "Medium": 0.6, "Low": 0.3}
        
        total_weight = 0
        for issue in issues:
            weight = severity_weights.get(issue.severity, 0.5)
            total_weight += weight
        
        # Calculate score (higher is better)
        max_possible_weight = total_requirements * 1.0  # Assuming all could be high severity
        consistency_score = max(0.0, 1.0 - (total_weight / max_possible_weight))
        
        return min(1.0, consistency_score)
    
    def _generate_detailed_consistency_recommendations(
        self, 
        issues: List[ConsistencyIssue], 
        parsed_requirements: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate detailed consistency recommendations."""
        recommendations = []
        
        if not issues:
            recommendations.append("Requirements are consistent across all documents")
            return recommendations
        
        # Categorize issues by severity
        high_severity_count = sum(1 for issue in issues if issue.severity == "High")
        medium_severity_count = sum(1 for issue in issues if issue.severity == "Medium")
        low_severity_count = sum(1 for issue in issues if issue.severity == "Low")
        
        # Generate severity-based recommendations
        if high_severity_count > 0:
            recommendations.append(f"URGENT: Address {high_severity_count} high-severity consistency issues immediately")
            recommendations.append("High-severity issues may impact system functionality and should be resolved first")
        
        if medium_severity_count > 0:
            recommendations.append(f"IMPORTANT: Review and resolve {medium_severity_count} medium-severity consistency issues")
            recommendations.append("Medium-severity issues may cause confusion and should be addressed soon")
        
        if low_severity_count > 0:
            recommendations.append(f"Consider addressing {low_severity_count} low-severity consistency issues for better documentation quality")
        
        # Generate specific recommendations based on issue types
        issue_types = {}
        for issue in issues:
            issue_type = self._categorize_issue_type(issue.description)
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        for issue_type, count in issue_types.items():
            if issue_type == "duplicate_ids":
                recommendations.append(f"Implement unique ID management system to prevent {count} duplicate ID issues")
            elif issue_type == "missing_content":
                recommendations.append(f"Complete {count} incomplete requirements with missing user stories or acceptance criteria")
            elif issue_type == "terminology":
                recommendations.append(f"Standardize terminology to resolve {count} terminology inconsistencies")
            elif issue_type == "cross_references":
                recommendations.append(f"Validate and fix {count} broken cross-references")
        
        # General process recommendations
        recommendations.append("Implement requirements review process to prevent future inconsistencies")
        recommendations.append("Consider using a requirements management tool for better consistency tracking")
        recommendations.append("Establish requirements documentation standards and templates")
        
        return recommendations
    
    def _categorize_issue_type(self, description: str) -> str:
        """Categorize issue type based on description."""
        description_lower = description.lower()
        
        if "duplicate" in description_lower:
            return "duplicate_ids"
        elif "missing" in description_lower:
            return "missing_content"
        elif "terminology" in description_lower or "language" in description_lower:
            return "terminology"
        elif "cross-reference" in description_lower or "reference" in description_lower:
            return "cross_references"
        elif "conflicting" in description_lower or "conflict" in description_lower:
            return "conflicts"
        else:
            return "other"
    
    def _generate_executive_summary(self, consistency_result: ConsistencyResult) -> str:
        """Generate executive summary section."""
        summary = f"""# Requirements Consistency Report

## Executive Summary

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Requirements Analyzed:** {consistency_result.total_requirements_checked}
**Consistency Score:** {consistency_result.consistency_score:.2f}/1.00
**Overall Status:** {'✅ CONSISTENT' if consistency_result.is_consistent else '⚠️ ISSUES FOUND'}

### Summary Statistics
- **Total Issues Found:** {len(consistency_result.consistency_issues)}
- **High Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'High')}
- **Medium Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Medium')}
- **Low Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Low')}
"""
        return summary
    
    def _generate_issues_analysis(self, issues: List[ConsistencyIssue]) -> str:
        """Generate detailed issues analysis section."""
        analysis = "## Detailed Issues Analysis\n\n"
        
        for i, issue in enumerate(issues, 1):
            analysis += f"### Issue {i}: {issue.description}\n\n"
            analysis += f"**Severity:** {issue.severity}\n"
            analysis += f"**Affected Documents:** {', '.join(issue.conflicting_documents)}\n"
            if issue.conflicting_requirements:
                analysis += f"**Affected Requirements:** {', '.join(issue.conflicting_requirements)}\n"
            analysis += f"**Resolution:** {issue.resolution_suggestion}\n\n"
        
        return analysis
    
    def _generate_consistency_metrics(self, consistency_result: ConsistencyResult) -> str:
        """Generate consistency metrics section."""
        metrics = f"""## Consistency Metrics

### Overall Metrics
- **Consistency Score:** {consistency_result.consistency_score:.2f}/1.00
- **Requirements Analyzed:** {consistency_result.total_requirements_checked}
- **Issues Found:** {len(consistency_result.consistency_issues)}

### Issue Distribution
- **High Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'High')} ({sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'High')/len(consistency_result.consistency_issues)*100:.1f}% of total issues)
- **Medium Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Medium')} ({sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Medium')/len(consistency_result.consistency_issues)*100:.1f}% of total issues)
- **Low Severity:** {sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Low')} ({sum(1 for issue in consistency_result.consistency_issues if issue.severity == 'Low')/len(consistency_result.consistency_issues)*100:.1f}% of total issues)
""" if consistency_result.consistency_issues else """## Consistency Metrics

### Overall Metrics
- **Consistency Score:** {consistency_result.consistency_score:.2f}/1.00
- **Requirements Analyzed:** {consistency_result.total_requirements_checked}
- **Issues Found:** 0

✅ **Perfect Consistency Achieved**
"""
        return metrics
    
    def _generate_recommendations_section(self, recommendations: List[str]) -> str:
        """Generate recommendations section."""
        section = "## Recommendations\n\n"
        
        for i, recommendation in enumerate(recommendations, 1):
            section += f"{i}. {recommendation}\n"
        
        return section
    
    def _generate_action_plan_section(self, issues: List[ConsistencyIssue]) -> str:
        """Generate action plan section."""
        if not issues:
            return "## Action Plan\n\n✅ No actions required - requirements are consistent.\n"
        
        action_plan = "## Action Plan\n\n"
        
        # Group by priority
        high_priority = [issue for issue in issues if issue.severity == "High"]
        medium_priority = [issue for issue in issues if issue.severity == "Medium"]
        low_priority = [issue for issue in issues if issue.severity == "Low"]
        
        if high_priority:
            action_plan += "### Phase 1: High Priority (Immediate Action Required)\n\n"
            for i, issue in enumerate(high_priority, 1):
                action_plan += f"{i}. **{issue.description}**\n"
                action_plan += f"   - Action: {issue.resolution_suggestion}\n"
                action_plan += f"   - Documents: {', '.join(issue.conflicting_documents)}\n\n"
        
        if medium_priority:
            action_plan += "### Phase 2: Medium Priority (Address Within 1 Week)\n\n"
            for i, issue in enumerate(medium_priority, 1):
                action_plan += f"{i}. **{issue.description}**\n"
                action_plan += f"   - Action: {issue.resolution_suggestion}\n"
                action_plan += f"   - Documents: {', '.join(issue.conflicting_documents)}\n\n"
        
        if low_priority:
            action_plan += "### Phase 3: Low Priority (Address When Convenient)\n\n"
            for i, issue in enumerate(low_priority, 1):
                action_plan += f"{i}. **{issue.description}**\n"
                action_plan += f"   - Action: {issue.resolution_suggestion}\n"
                action_plan += f"   - Documents: {', '.join(issue.conflicting_documents)}\n\n"
        
        return action_plan