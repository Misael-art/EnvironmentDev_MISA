"""
Intelligent Storage Manager

Main interface for intelligent storage management that coordinates all storage-related
operations including analysis, distribution, and compression.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .storage_analyzer import StorageAnalyzer
from .distribution_manager import DistributionManager
from .compression_manager import CompressionManager
from .models import (
    SpaceRequirement, SelectiveInstallationResult, CleanupResult,
    RemovalSuggestions, DistributionResult, CompressionResult,
    StorageAnalysisResult, DriveInfo
)


class IntelligentStorageManager:
    """
    Main intelligent storage management system that coordinates all storage operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.storage_analyzer = StorageAnalyzer()
        self.distribution_manager = None  # Will be initialized when needed
        self.compression_manager = None   # Will be initialized when needed
        
    def calculate_space_requirements_before_installation(
        self, 
        components: List[Dict]
    ) -> SpaceRequirement:
        """
        Calculate space requirements before installation
        
        Args:
            components: List of components to be installed
            
        Returns:
            SpaceRequirement: Detailed space requirement analysis
        """
        try:
            self.logger.info(f"Calculating space requirements for {len(components)} components")
            
            space_requirements = self.storage_analyzer.calculate_space_requirements(components)
            
            self.logger.info(
                f"Total space required: {self._format_size(space_requirements.total_required_space)}"
            )
            
            return space_requirements
            
        except Exception as e:
            self.logger.error(f"Error calculating space requirements: {e}")
            raise
    
    def enable_selective_installation_based_on_available_space(
        self, 
        available_space: int,
        components: List[Dict]
    ) -> SelectiveInstallationResult:
        """
        Enable selective installation based on available space
        
        Args:
            available_space: Available space in bytes
            components: List of components to analyze
            
        Returns:
            SelectiveInstallationResult: Analysis of what can be installed
        """
        try:
            self.logger.info(f"Analyzing selective installation with {self._format_size(available_space)} available")
            
            # Calculate space requirements first
            space_requirements = self.calculate_space_requirements_before_installation(components)
            
            # Analyze selective installation
            selective_result = self.storage_analyzer.analyze_selective_installation(
                space_requirements, available_space
            )
            
            self.logger.info(
                f"Selective installation analysis: {len(selective_result.installable_components)} "
                f"installable, {len(selective_result.skipped_components)} skipped"
            )
            
            return selective_result
            
        except Exception as e:
            self.logger.error(f"Error in selective installation analysis: {e}")
            raise
    
    def automatically_remove_temporary_files_after_installation(
        self,
        installation_paths: List[str],
        temp_directories: List[str] = None
    ) -> CleanupResult:
        """
        Automatically remove temporary files after installation
        
        Args:
            installation_paths: Paths where installations occurred
            temp_directories: Additional temporary directories to clean
            
        Returns:
            CleanupResult: Result of cleanup operations
        """
        try:
            self.logger.info("Starting automatic cleanup of temporary files")
            
            # Initialize compression manager if needed (it handles cleanup too)
            if not self.compression_manager:
                from .compression_manager import CompressionManager
                self.compression_manager = CompressionManager()
            
            cleanup_result = self.compression_manager.cleanup_temporary_files(
                installation_paths, temp_directories or []
            )
            
            self.logger.info(
                f"Cleanup completed: {self._format_size(cleanup_result.space_freed)} freed"
            )
            
            return cleanup_result
            
        except Exception as e:
            self.logger.error(f"Error during automatic cleanup: {e}")
            raise
    
    def suggest_components_for_removal_when_storage_low(
        self,
        current_components: List[Dict],
        required_space: int
    ) -> RemovalSuggestions:
        """
        Suggest components for removal when storage is low
        
        Args:
            current_components: Currently installed components
            required_space: Space needed for new installation
            
        Returns:
            RemovalSuggestions: Suggestions for component removal
        """
        try:
            self.logger.info(f"Generating removal suggestions for {self._format_size(required_space)} needed")
            
            # Initialize distribution manager if needed (it handles removal suggestions)
            if not self.distribution_manager:
                from .distribution_manager import DistributionManager
                self.distribution_manager = DistributionManager()
            
            removal_suggestions = self.distribution_manager.suggest_component_removal(
                current_components, required_space
            )
            
            self.logger.info(
                f"Generated {len(removal_suggestions.suggestions)} removal suggestions"
            )
            
            return removal_suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating removal suggestions: {e}")
            raise
    
    def intelligently_distribute_across_multiple_drives(
        self,
        drives: List[DriveInfo],
        components: List[Dict]
    ) -> DistributionResult:
        """
        Intelligently distribute installations across multiple drives
        
        Args:
            drives: Available drives for installation
            components: Components to distribute
            
        Returns:
            DistributionResult: Distribution plan and results
        """
        try:
            self.logger.info(f"Distributing {len(components)} components across {len(drives)} drives")
            
            # Initialize distribution manager if needed
            if not self.distribution_manager:
                from .distribution_manager import DistributionManager
                self.distribution_manager = DistributionManager()
            
            distribution_result = self.distribution_manager.distribute_components(
                drives, components
            )
            
            self.logger.info(
                f"Distribution completed: {len(distribution_result.distribution_plans)} plans created"
            )
            
            return distribution_result
            
        except Exception as e:
            self.logger.error(f"Error in intelligent distribution: {e}")
            raise
    
    def implement_intelligent_compression(
        self,
        target_paths: List[str],
        compression_criteria: Dict = None
    ) -> CompressionResult:
        """
        Implement intelligent compression for space optimization
        
        Args:
            target_paths: Paths to analyze for compression
            compression_criteria: Criteria for compression decisions
            
        Returns:
            CompressionResult: Result of compression operations
        """
        try:
            self.logger.info(f"Starting intelligent compression for {len(target_paths)} paths")
            
            # Initialize compression manager if needed
            if not self.compression_manager:
                from .compression_manager import CompressionManager
                self.compression_manager = CompressionManager()
            
            compression_result = self.compression_manager.compress_intelligently(
                target_paths, compression_criteria or {}
            )
            
            self.logger.info(
                f"Compression completed: {self._format_size(compression_result.space_saved)} saved"
            )
            
            return compression_result
            
        except Exception as e:
            self.logger.error(f"Error in intelligent compression: {e}")
            raise
    
    def perform_comprehensive_storage_analysis(
        self,
        components: List[Dict]
    ) -> StorageAnalysisResult:
        """
        Perform comprehensive storage analysis
        
        Args:
            components: Components to analyze
            
        Returns:
            StorageAnalysisResult: Comprehensive analysis results
        """
        try:
            self.logger.info("Starting comprehensive storage analysis")
            
            # Analyze system drives
            drives = self.storage_analyzer.analyze_system_storage()
            
            # Calculate space requirements
            space_requirements = self.calculate_space_requirements_before_installation(components)
            
            # Determine available space (use best drive)
            best_drive = self.storage_analyzer.get_best_drive_for_installation(
                space_requirements.recommended_free_space
            )
            available_space = best_drive.available_space if best_drive else 0
            
            # Analyze selective installation
            selective_installation = self.enable_selective_installation_based_on_available_space(
                available_space, components
            )
            
            # Generate removal suggestions if needed
            removal_suggestions = RemovalSuggestions(
                suggestions=[],
                total_potential_space=0,
                recommended_removals=[],
                analysis_timestamp=datetime.now()
            )
            
            if not selective_installation.installation_feasible:
                removal_suggestions = self.suggest_components_for_removal_when_storage_low(
                    components, space_requirements.recommended_free_space
                )
            
            # Analyze distribution options
            distribution_result = self.intelligently_distribute_across_multiple_drives(
                drives, components
            )
            
            # Identify compression opportunities
            compression_opportunities = []
            if self.compression_manager:
                compression_opportunities = self.compression_manager.identify_compression_candidates(
                    [drive.drive_letter for drive in drives]
                )
            
            # Determine overall feasibility
            overall_feasibility = (
                selective_installation.installation_feasible or
                distribution_result.distribution_feasible or
                len(removal_suggestions.suggestions) > 0
            )
            
            # Generate recommendations
            recommendations = []
            if not overall_feasibility:
                recommendations.append("Insufficient storage space for installation")
            if len(drives) > 1:
                recommendations.append("Consider using multiple drives for optimal distribution")
            if compression_opportunities:
                recommendations.append(f"Found {len(compression_opportunities)} compression opportunities")
            
            analysis_result = StorageAnalysisResult(
                drives=drives,
                space_requirements=space_requirements,
                selective_installation=selective_installation,
                removal_suggestions=removal_suggestions,
                distribution_result=distribution_result,
                compression_opportunities=compression_opportunities,
                overall_feasibility=overall_feasibility,
                recommendations=recommendations,
                analysis_timestamp=datetime.now()
            )
            
            self.logger.info("Comprehensive storage analysis completed")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive storage analysis: {e}")
            raise
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"