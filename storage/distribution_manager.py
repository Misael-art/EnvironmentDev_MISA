"""
Distribution Manager for Intelligent Multi-Drive Distribution

This module provides intelligent distribution algorithms for installing components
across multiple drives, cleanup operations, and component removal suggestions.
"""

import os
import shutil
import logging
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import glob

from .models import (
    DriveInfo, DistributionPlan, DistributionResult, CleanupResult,
    RemovalSuggestion, RemovalSuggestions, InstallationPriority
)


class DistributionManager:
    """
    Manages intelligent distribution of components across multiple drives
    and handles cleanup operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_directories = [
            tempfile.gettempdir(),
            os.path.expandvars('%TEMP%') if os.name == 'nt' else '/tmp',
            './temp',
            './temp_download',
            './cache'
        ]
    
    def distribute_components(
        self, 
        drives: List[DriveInfo], 
        components: List[Dict]
    ) -> DistributionResult:
        """
        Intelligently distribute components across multiple drives
        
        Args:
            drives: Available drives for installation
            components: Components to distribute
            
        Returns:
            DistributionResult: Distribution plan and results
        """
        try:
            self.logger.info(f"Starting distribution of {len(components)} components across {len(drives)} drives")
            
            # Filter and sort drives by suitability
            suitable_drives = self._filter_suitable_drives(drives)
            if not suitable_drives:
                return self._create_failed_distribution_result("No suitable drives available")
            
            # Create distribution plans
            distribution_plans = []
            drives_used = set()
            total_space_used = 0
            warnings = []
            
            # Sort components by priority and size
            sorted_components = self._sort_components_for_distribution(components)
            
            for component in sorted_components:
                component_name = component.get('name', 'Unknown')
                installation_size = component.get('installation_size', 0)
                priority = component.get('priority', 'medium')
                
                # Find best drive for this component
                best_drive = self._find_best_drive_for_component(
                    suitable_drives, component, distribution_plans
                )
                
                if not best_drive:
                    warnings.append(f"No suitable drive found for component: {component_name}")
                    continue
                
                # Create installation path
                installation_path = self._create_installation_path(best_drive, component_name)
                
                # Create distribution plan
                plan = DistributionPlan(
                    component_name=component_name,
                    target_drive=best_drive.drive_letter,
                    installation_path=installation_path,
                    space_required=installation_size,
                    reason=self._get_distribution_reason(best_drive, component, priority)
                )
                
                distribution_plans.append(plan)
                drives_used.add(best_drive.drive_letter)
                total_space_used += installation_size
                
                # Update drive available space for next iteration
                best_drive.available_space -= installation_size
            
            # Calculate optimization metrics
            space_optimization = self._calculate_space_optimization(
                drives, distribution_plans, total_space_used
            )
            
            distribution_feasible = len(distribution_plans) == len(components)
            
            if not distribution_feasible:
                warnings.append(f"Could not distribute all components: {len(distribution_plans)}/{len(components)}")
            
            result = DistributionResult(
                distribution_plans=distribution_plans,
                total_components=len(components),
                drives_used=list(drives_used),
                space_optimization=space_optimization,
                distribution_feasible=distribution_feasible,
                warnings=warnings
            )
            
            self.logger.info(f"Distribution completed: {len(distribution_plans)} plans created")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in component distribution: {e}")
            return self._create_failed_distribution_result(f"Distribution error: {str(e)}")
    
    def _filter_suitable_drives(self, drives: List[DriveInfo]) -> List[DriveInfo]:
        """Filter drives suitable for installation"""
        suitable = []
        
        for drive in drives:
            # Skip drives with less than 1GB available space
            if drive.available_space < 1073741824:  # 1GB
                continue
                
            # Skip removable drives unless they're the only option
            if drive.drive_type == 'removable' and len(drives) > 1:
                continue
                
            # Skip network drives for performance reasons
            if drive.drive_type == 'network':
                continue
                
            suitable.append(drive)
        
        # Sort by performance score and available space
        suitable.sort(key=lambda d: (-d.performance_score, -d.available_space))
        return suitable
    
    def _sort_components_for_distribution(self, components: List[Dict]) -> List[Dict]:
        """Sort components for optimal distribution"""
        priority_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'optional': 4
        }
        
        return sorted(
            components,
            key=lambda c: (
                priority_order.get(c.get('priority', 'medium'), 2),
                -c.get('installation_size', 0)  # Larger components first
            )
        )
    
    def _find_best_drive_for_component(
        self, 
        drives: List[DriveInfo], 
        component: Dict,
        existing_plans: List[DistributionPlan]
    ) -> Optional[DriveInfo]:
        """Find the best drive for a specific component"""
        component_size = component.get('installation_size', 0)
        priority = component.get('priority', 'medium')
        
        # Calculate current usage per drive
        drive_usage = {}
        for plan in existing_plans:
            drive_usage[plan.target_drive] = drive_usage.get(plan.target_drive, 0) + plan.space_required
        
        best_drive = None
        best_score = -1
        
        for drive in drives:
            # Check if drive has enough space
            current_usage = drive_usage.get(drive.drive_letter, 0)
            available_after_usage = drive.available_space - current_usage
            
            if available_after_usage < component_size:
                continue
            
            # Calculate score for this drive
            score = self._calculate_drive_score_for_component(
                drive, component, current_usage, available_after_usage
            )
            
            if score > best_score:
                best_score = score
                best_drive = drive
        
        return best_drive
    
    def _calculate_drive_score_for_component(
        self, 
        drive: DriveInfo, 
        component: Dict, 
        current_usage: int,
        available_space: int
    ) -> float:
        """Calculate score for placing component on specific drive"""
        score = 0.0
        
        # Base performance score
        score += drive.performance_score * 0.4
        
        # Available space factor (prefer drives with more available space)
        space_ratio = available_space / drive.total_space
        score += space_ratio * 0.3
        
        # Load balancing (prefer less used drives)
        usage_ratio = current_usage / drive.total_space
        score += (1.0 - usage_ratio) * 0.2
        
        # System drive preference for critical components
        if component.get('priority') == 'critical' and drive.is_system_drive:
            score += 0.1
        elif not drive.is_system_drive:
            # Prefer non-system drives for non-critical components
            score += 0.05
        
        return score
    
    def _create_installation_path(self, drive: DriveInfo, component_name: str) -> str:
        """Create installation path for component"""
        if os.name == 'nt':  # Windows
            base_path = os.path.join(drive.drive_letter, "Program Files", "EnvironmentDev")
        else:  # Unix-like
            base_path = os.path.join(drive.drive_letter, "opt", "environmentdev")
        
        return os.path.join(base_path, component_name)
    
    def _get_distribution_reason(self, drive: DriveInfo, component: Dict, priority: str) -> str:
        """Get reason for distribution decision"""
        reasons = []
        
        if drive.is_system_drive and priority == 'critical':
            reasons.append("System drive for critical component")
        elif not drive.is_system_drive:
            reasons.append("Non-system drive to preserve system space")
        
        if drive.performance_score > 0.8:
            reasons.append("High performance drive")
        
        if drive.available_space > 100 * 1024 * 1024 * 1024:  # 100GB
            reasons.append("Ample available space")
        
        return "; ".join(reasons) if reasons else "Best available option"
    
    def _calculate_space_optimization(
        self, 
        original_drives: List[DriveInfo], 
        plans: List[DistributionPlan],
        total_space_used: int
    ) -> float:
        """Calculate space optimization percentage"""
        if not plans or total_space_used == 0:
            return 0.0
        
        # Calculate how much space would be used if everything went to the first suitable drive
        first_drive_space = max(d.available_space for d in original_drives)
        
        # Calculate actual distribution efficiency
        drives_used = len(set(plan.target_drive for plan in plans))
        distribution_efficiency = min(drives_used / len(original_drives), 1.0)
        
        # Space utilization efficiency
        max_single_drive_usage = max(
            sum(p.space_required for p in plans if p.target_drive == drive)
            for drive in set(p.target_drive for p in plans)
        )
        
        space_efficiency = 1.0 - (max_single_drive_usage / total_space_used) if total_space_used > 0 else 0.0
        
        return (distribution_efficiency + space_efficiency) * 50.0  # Convert to percentage
    
    def cleanup_temporary_files(
        self, 
        installation_paths: List[str],
        additional_temp_dirs: List[str] = None
    ) -> CleanupResult:
        """
        Clean up temporary files after installation
        
        Args:
            installation_paths: Paths where installations occurred
            additional_temp_dirs: Additional temporary directories to clean
            
        Returns:
            CleanupResult: Result of cleanup operations
        """
        try:
            self.logger.info("Starting cleanup of temporary files")
            start_time = datetime.now()
            
            cleaned_files = []
            space_freed = 0
            errors = []
            
            # Combine all temp directories
            temp_dirs = self.temp_directories.copy()
            if additional_temp_dirs:
                temp_dirs.extend(additional_temp_dirs)
            
            # Add installation-specific temp directories
            for install_path in installation_paths:
                temp_dirs.extend([
                    os.path.join(install_path, 'temp'),
                    os.path.join(install_path, 'cache'),
                    os.path.join(install_path, 'downloads')
                ])
            
            # Clean each temp directory
            for temp_dir in temp_dirs:
                try:
                    if os.path.exists(temp_dir):
                        files_cleaned, space_freed_dir = self._clean_directory(temp_dir)
                        cleaned_files.extend(files_cleaned)
                        space_freed += space_freed_dir
                except Exception as e:
                    errors.append(f"Error cleaning {temp_dir}: {str(e)}")
            
            # Clean specific file patterns
            patterns_to_clean = [
                '*.tmp',
                '*.temp',
                '*.log',
                '*~',
                '*.bak',
                '*.old'
            ]
            
            for install_path in installation_paths:
                for pattern in patterns_to_clean:
                    try:
                        pattern_files, pattern_space = self._clean_file_pattern(
                            install_path, pattern
                        )
                        cleaned_files.extend(pattern_files)
                        space_freed += pattern_space
                    except Exception as e:
                        errors.append(f"Error cleaning pattern {pattern} in {install_path}: {str(e)}")
            
            cleanup_duration = (datetime.now() - start_time).total_seconds()
            success = len(errors) == 0
            
            result = CleanupResult(
                cleaned_files=cleaned_files,
                space_freed=space_freed,
                cleanup_duration=cleanup_duration,
                errors=errors,
                success=success
            )
            
            self.logger.info(
                f"Cleanup completed: {len(cleaned_files)} files, "
                f"{self._format_size(space_freed)} freed"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return CleanupResult(
                cleaned_files=[],
                space_freed=0,
                cleanup_duration=0.0,
                errors=[str(e)],
                success=False
            )
    
    def _clean_directory(self, directory: str) -> Tuple[List[str], int]:
        """Clean a specific directory"""
        cleaned_files = []
        space_freed = 0
        
        if not os.path.exists(directory):
            return cleaned_files, space_freed
        
        # Only clean files older than 1 hour to avoid interfering with ongoing operations
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Check file age
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime > cutoff_time:
                        continue
                    
                    # Get file size before deletion
                    file_size = os.path.getsize(file_path)
                    
                    # Delete file
                    os.remove(file_path)
                    cleaned_files.append(file_path)
                    space_freed += file_size
                    
                except (OSError, IOError) as e:
                    # File might be in use or permission denied
                    continue
        
        return cleaned_files, space_freed
    
    def _clean_file_pattern(self, directory: str, pattern: str) -> Tuple[List[str], int]:
        """Clean files matching a specific pattern"""
        cleaned_files = []
        space_freed = 0
        
        if not os.path.exists(directory):
            return cleaned_files, space_freed
        
        pattern_path = os.path.join(directory, pattern)
        matching_files = glob.glob(pattern_path, recursive=True)
        
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for file_path in matching_files:
            try:
                if os.path.isfile(file_path):
                    # Check file age
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime > cutoff_time:
                        continue
                    
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    cleaned_files.append(file_path)
                    space_freed += file_size
                    
            except (OSError, IOError):
                continue
        
        return cleaned_files, space_freed
    
    def suggest_component_removal(
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
            
            suggestions = []
            total_potential_space = 0
            recommended_removals = []
            
            # Sort components by removal priority (optional first, then by size)
            sorted_components = self._sort_components_for_removal(current_components)
            
            for component in sorted_components:
                component_name = component.get('name', 'Unknown')
                installation_size = component.get('installation_size', 0)
                priority = component.get('priority', 'medium')
                last_used = component.get('last_used', datetime.now())
                
                # Determine removal safety and impact
                removal_safety = self._assess_removal_safety(component)
                impact_level = self._assess_removal_impact(component)
                
                # Create suggestion
                suggestion = RemovalSuggestion(
                    component_name=component_name,
                    space_freed=installation_size,
                    impact_level=impact_level,
                    removal_safety=removal_safety,
                    description=self._create_removal_description(component, removal_safety, impact_level)
                )
                
                suggestions.append(suggestion)
                total_potential_space += installation_size
                
                # Add to recommended removals if safe and meets criteria
                if (removal_safety == 'safe' and 
                    priority in ['optional', 'low'] and
                    installation_size >= required_space * 0.1):  # At least 10% of needed space
                    recommended_removals.append(component_name)
                
                # Stop if we have enough potential space
                if total_potential_space >= required_space * 1.5:  # 150% of needed space
                    break
            
            return RemovalSuggestions(
                suggestions=suggestions,
                total_potential_space=total_potential_space,
                recommended_removals=recommended_removals,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error generating removal suggestions: {e}")
            return RemovalSuggestions(
                suggestions=[],
                total_potential_space=0,
                recommended_removals=[],
                analysis_timestamp=datetime.now()
            )
    
    def _sort_components_for_removal(self, components: List[Dict]) -> List[Dict]:
        """Sort components by removal priority"""
        priority_order = {
            'optional': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        return sorted(
            components,
            key=lambda c: (
                priority_order.get(c.get('priority', 'medium'), 2),
                -c.get('installation_size', 0),  # Larger components first within same priority
                c.get('last_used', datetime.now())  # Older components first
            )
        )
    
    def _assess_removal_safety(self, component: Dict) -> str:
        """Assess safety of removing a component"""
        priority = component.get('priority', 'medium')
        has_dependencies = component.get('has_dependencies', False)
        is_system_component = component.get('is_system_component', False)
        
        if is_system_component or priority == 'critical':
            return 'risky'
        elif has_dependencies or priority == 'high':
            return 'caution'
        else:
            return 'safe'
    
    def _assess_removal_impact(self, component: Dict) -> str:
        """Assess impact of removing a component"""
        priority = component.get('priority', 'medium')
        usage_frequency = component.get('usage_frequency', 0)
        has_dependencies = component.get('has_dependencies', False)
        
        if priority in ['critical', 'high'] or has_dependencies:
            return 'high'
        elif priority == 'medium' or usage_frequency > 10:
            return 'medium'
        else:
            return 'low'
    
    def _create_removal_description(self, component: Dict, safety: str, impact: str) -> str:
        """Create description for removal suggestion"""
        name = component.get('name', 'Unknown')
        priority = component.get('priority', 'medium')
        size = self._format_size(component.get('installation_size', 0))
        
        description = f"{name} ({size}) - Priority: {priority}"
        
        if safety == 'risky':
            description += " - WARNING: Removal may affect system stability"
        elif safety == 'caution':
            description += " - CAUTION: May affect other components"
        
        if impact == 'high':
            description += " - High impact on functionality"
        elif impact == 'medium':
            description += " - Moderate impact on functionality"
        else:
            description += " - Low impact on functionality"
        
        return description
    
    def _create_failed_distribution_result(self, error_message: str) -> DistributionResult:
        """Create a failed distribution result"""
        return DistributionResult(
            distribution_plans=[],
            total_components=0,
            drives_used=[],
            space_optimization=0.0,
            distribution_feasible=False,
            warnings=[error_message]
        )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"