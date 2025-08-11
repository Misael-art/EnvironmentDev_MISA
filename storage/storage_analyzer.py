"""
Storage Analysis System for Intelligent Storage Management

This module provides comprehensive storage analysis capabilities including
space requirement calculation, drive analysis, and installation feasibility assessment.
"""

import os
import shutil
import psutil
import platform
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from .models import (
    DriveInfo, ComponentSpaceRequirement, SpaceRequirement,
    SelectiveInstallationResult, StorageAnalysisResult,
    InstallationPriority, StorageUnit
)


class StorageAnalyzer:
    """
    Analyzes storage requirements and available space for intelligent installation planning
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._drive_cache = {}
        self._cache_timestamp = None
        self._cache_duration = 30  # seconds
        
    def analyze_system_storage(self) -> List[DriveInfo]:
        """
        Analyze all available drives in the system
        
        Returns:
            List[DriveInfo]: Information about all system drives
        """
        try:
            drives = []
            
            if platform.system() == "Windows":
                drives = self._analyze_windows_drives()
            else:
                drives = self._analyze_unix_drives()
                
            # Sort drives by performance score (system drive first, then by available space)
            drives.sort(key=lambda d: (not d.is_system_drive, -d.performance_score, -d.available_space))
            
            return drives
            
        except Exception as e:
            self.logger.error(f"Error analyzing system storage: {e}")
            return []
    
    def _analyze_windows_drives(self) -> List[DriveInfo]:
        """Analyze Windows drives"""
        drives = []
        
        for partition in psutil.disk_partitions():
            try:
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                drive_letter = partition.mountpoint.rstrip('\\')
                
                # Determine if it's the system drive
                is_system = drive_letter.upper() == os.environ.get('SystemDrive', 'C:').upper()
                
                # Calculate performance score based on drive type and characteristics
                performance_score = self._calculate_drive_performance_score(
                    partition, usage, is_system
                )
                
                drive_info = DriveInfo(
                    drive_letter=drive_letter,
                    total_space=usage.total,
                    available_space=usage.free,
                    used_space=usage.used,
                    file_system=partition.fstype,
                    drive_type=self._get_drive_type(partition),
                    is_system_drive=is_system,
                    performance_score=performance_score
                )
                
                drives.append(drive_info)
                
            except (PermissionError, FileNotFoundError) as e:
                self.logger.warning(f"Cannot access drive {partition.mountpoint}: {e}")
                continue
                
        return drives
    
    def _analyze_unix_drives(self) -> List[DriveInfo]:
        """Analyze Unix/Linux drives"""
        drives = []
        
        for partition in psutil.disk_partitions():
            try:
                if partition.fstype in ['tmpfs', 'devtmpfs', 'squashfs']:
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Determine if it's the system drive (root filesystem)
                is_system = partition.mountpoint == '/'
                
                performance_score = self._calculate_drive_performance_score(
                    partition, usage, is_system
                )
                
                drive_info = DriveInfo(
                    drive_letter=partition.mountpoint,
                    total_space=usage.total,
                    available_space=usage.free,
                    used_space=usage.used,
                    file_system=partition.fstype,
                    drive_type=self._get_drive_type(partition),
                    is_system_drive=is_system,
                    performance_score=performance_score
                )
                
                drives.append(drive_info)
                
            except (PermissionError, FileNotFoundError) as e:
                self.logger.warning(f"Cannot access partition {partition.mountpoint}: {e}")
                continue
                
        return drives
    
    def _calculate_drive_performance_score(self, partition, usage, is_system: bool) -> float:
        """Calculate performance score for a drive"""
        score = 0.0
        
        # Base score for system drive
        if is_system:
            score += 0.3
            
        # Score based on available space percentage
        free_percentage = usage.free / usage.total if usage.total > 0 else 0
        score += min(free_percentage * 0.4, 0.4)
        
        # Score based on drive type
        if 'ssd' in partition.device.lower() or 'nvme' in partition.device.lower():
            score += 0.2
        elif 'usb' in partition.device.lower() or 'removable' in partition.opts:
            score -= 0.1
            
        # Score based on file system
        if partition.fstype.lower() in ['ntfs', 'ext4', 'apfs']:
            score += 0.1
            
        return max(0.0, min(1.0, score))
    
    def _get_drive_type(self, partition) -> str:
        """Determine drive type from partition information"""
        if 'removable' in partition.opts:
            return 'removable'
        elif 'network' in partition.opts:
            return 'network'
        else:
            return 'fixed'
    
    def calculate_space_requirements(self, components: List[Dict]) -> SpaceRequirement:
        """
        Calculate space requirements for given components
        
        Args:
            components: List of component dictionaries with size information
            
        Returns:
            SpaceRequirement: Detailed space requirement analysis
        """
        try:
            component_requirements = []
            total_download = 0
            total_installation = 0
            total_temporary = 0
            
            for component in components:
                # Extract component information
                name = component.get('name', 'Unknown')
                download_size = component.get('download_size', 0)
                installation_size = component.get('installation_size', download_size * 2)
                priority = InstallationPriority(component.get('priority', 'medium'))
                
                # Calculate temporary space (for extraction, etc.)
                temporary_space = max(download_size, installation_size // 2)
                total_required = download_size + installation_size + temporary_space
                
                # Determine compression capability
                can_compress = component.get('can_compress', True)
                compression_ratio = component.get('compression_ratio', 0.7)
                
                comp_req = ComponentSpaceRequirement(
                    component_name=name,
                    download_size=download_size,
                    installation_size=installation_size,
                    temporary_space=temporary_space,
                    total_required=total_required,
                    priority=priority,
                    can_be_compressed=can_compress,
                    compression_ratio=compression_ratio
                )
                
                component_requirements.append(comp_req)
                total_download += download_size
                total_installation += installation_size
                total_temporary += temporary_space
            
            # Add 20% buffer for safety
            total_required = total_download + total_installation + total_temporary
            recommended_free = int(total_required * 1.2)
            
            return SpaceRequirement(
                components=component_requirements,
                total_download_size=total_download,
                total_installation_size=total_installation,
                total_temporary_space=total_temporary,
                total_required_space=total_required,
                recommended_free_space=recommended_free,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating space requirements: {e}")
            return SpaceRequirement(
                components=[],
                total_download_size=0,
                total_installation_size=0,
                total_temporary_space=0,
                total_required_space=0,
                recommended_free_space=0,
                analysis_timestamp=datetime.now()
            )
    
    def analyze_selective_installation(
        self, 
        space_requirements: SpaceRequirement, 
        available_space: int
    ) -> SelectiveInstallationResult:
        """
        Analyze which components can be installed based on available space
        
        Args:
            space_requirements: Calculated space requirements
            available_space: Available space in bytes
            
        Returns:
            SelectiveInstallationResult: Analysis of selective installation options
        """
        try:
            installable = []
            skipped = []
            current_space_used = 0
            recommendations = []
            
            # Sort components by priority (critical first)
            priority_order = {
                InstallationPriority.CRITICAL: 0,
                InstallationPriority.HIGH: 1,
                InstallationPriority.MEDIUM: 2,
                InstallationPriority.LOW: 3,
                InstallationPriority.OPTIONAL: 4
            }
            
            sorted_components = sorted(
                space_requirements.components,
                key=lambda c: (priority_order[c.priority], c.total_required)
            )
            
            for component in sorted_components:
                if current_space_used + component.total_required <= available_space:
                    installable.append(component.component_name)
                    current_space_used += component.total_required
                else:
                    skipped.append(component.component_name)
                    
                    # Add recommendations for skipped components
                    if component.priority in [InstallationPriority.CRITICAL, InstallationPriority.HIGH]:
                        recommendations.append(
                            f"Consider freeing space for critical component: {component.component_name}"
                        )
            
            space_saved = space_requirements.total_required_space - current_space_used
            installation_feasible = len(installable) > 0
            
            # Add general recommendations
            if skipped:
                recommendations.append(f"Consider installing {len(skipped)} skipped components later")
            if space_saved > 0:
                recommendations.append(f"Space saved by selective installation: {self._format_size(space_saved)}")
            
            return SelectiveInstallationResult(
                installable_components=installable,
                skipped_components=skipped,
                space_saved=space_saved,
                total_space_required=current_space_used,
                installation_feasible=installation_feasible,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing selective installation: {e}")
            return SelectiveInstallationResult(
                installable_components=[],
                skipped_components=[],
                space_saved=0,
                total_space_required=0,
                installation_feasible=False,
                recommendations=["Error occurred during analysis"]
            )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def get_drive_by_letter(self, drive_letter: str) -> Optional[DriveInfo]:
        """Get drive information by drive letter"""
        drives = self.analyze_system_storage()
        for drive in drives:
            if drive.drive_letter.upper() == drive_letter.upper():
                return drive
        return None
    
    def get_best_drive_for_installation(self, required_space: int) -> Optional[DriveInfo]:
        """Get the best drive for installation based on space and performance"""
        drives = self.analyze_system_storage()
        
        # Filter drives with enough space
        suitable_drives = [d for d in drives if d.available_space >= required_space]
        
        if not suitable_drives:
            return None
            
        # Return the drive with the highest performance score
        return max(suitable_drives, key=lambda d: d.performance_score)