"""
Unit tests for Storage Analysis System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime

from .storage_analyzer import StorageAnalyzer
from .models import (
    DriveInfo, ComponentSpaceRequirement, SpaceRequirement,
    SelectiveInstallationResult, InstallationPriority
)


class TestStorageAnalyzer(unittest.TestCase):
    """Test cases for StorageAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = StorageAnalyzer()
        
        # Mock drive data
        self.mock_drives = [
            DriveInfo(
                drive_letter="C:",
                total_space=1000000000000,  # 1TB
                available_space=500000000000,  # 500GB
                used_space=500000000000,
                file_system="NTFS",
                drive_type="fixed",
                is_system_drive=True,
                performance_score=0.8
            ),
            DriveInfo(
                drive_letter="D:",
                total_space=2000000000000,  # 2TB
                available_space=1800000000000,  # 1.8TB
                used_space=200000000000,
                file_system="NTFS",
                drive_type="fixed",
                is_system_drive=False,
                performance_score=0.9
            )
        ]
        
        # Mock component data
        self.mock_components = [
            {
                'name': 'Git',
                'download_size': 50000000,  # 50MB
                'installation_size': 100000000,  # 100MB
                'priority': 'critical',
                'can_compress': True,
                'compression_ratio': 0.7
            },
            {
                'name': 'Node.js',
                'download_size': 30000000,  # 30MB
                'installation_size': 80000000,  # 80MB
                'priority': 'high',
                'can_compress': True,
                'compression_ratio': 0.6
            },
            {
                'name': 'Optional Tool',
                'download_size': 100000000,  # 100MB
                'installation_size': 200000000,  # 200MB
                'priority': 'optional',
                'can_compress': False,
                'compression_ratio': 1.0
            }
        ]
    
    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    @patch('platform.system')
    def test_analyze_system_storage_windows(self, mock_system, mock_usage, mock_partitions):
        """Test Windows drive analysis"""
        # Mock Windows system
        mock_system.return_value = "Windows"
        
        # Mock partition data
        mock_partition = Mock()
        mock_partition.mountpoint = "C:\\"
        mock_partition.fstype = "NTFS"
        mock_partition.opts = ""
        mock_partition.device = "C:"
        mock_partitions.return_value = [mock_partition]
        
        # Mock usage data
        mock_usage_obj = Mock()
        mock_usage_obj.total = 1000000000000
        mock_usage_obj.free = 500000000000
        mock_usage_obj.used = 500000000000
        mock_usage.return_value = mock_usage_obj
        
        # Mock environment variable
        with patch.dict(os.environ, {'SystemDrive': 'C:'}):
            drives = self.analyzer.analyze_system_storage()
        
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0].drive_letter, "C:")
        self.assertTrue(drives[0].is_system_drive)
        self.assertEqual(drives[0].file_system, "NTFS")
    
    def test_calculate_space_requirements(self):
        """Test space requirements calculation"""
        space_req = self.analyzer.calculate_space_requirements(self.mock_components)
        
        self.assertIsInstance(space_req, SpaceRequirement)
        self.assertEqual(len(space_req.components), 3)
        self.assertGreater(space_req.total_required_space, 0)
        self.assertGreater(space_req.recommended_free_space, space_req.total_required_space)
        
        # Check individual component requirements
        git_component = next(c for c in space_req.components if c.component_name == 'Git')
        self.assertEqual(git_component.priority, InstallationPriority.CRITICAL)
        self.assertTrue(git_component.can_be_compressed)
    
    def test_analyze_selective_installation_sufficient_space(self):
        """Test selective installation with sufficient space"""
        space_req = self.analyzer.calculate_space_requirements(self.mock_components)
        available_space = space_req.recommended_free_space + 1000000000  # Extra 1GB
        
        result = self.analyzer.analyze_selective_installation(space_req, available_space)
        
        self.assertIsInstance(result, SelectiveInstallationResult)
        self.assertTrue(result.installation_feasible)
        self.assertEqual(len(result.installable_components), 3)  # All components
        self.assertEqual(len(result.skipped_components), 0)
    
    def test_analyze_selective_installation_limited_space(self):
        """Test selective installation with limited space"""
        space_req = self.analyzer.calculate_space_requirements(self.mock_components)
        # Only enough space for critical and high priority components
        available_space = 300000000  # 300MB
        
        result = self.analyzer.analyze_selective_installation(space_req, available_space)
        
        self.assertIsInstance(result, SelectiveInstallationResult)
        self.assertTrue(result.installation_feasible)  # Should still be feasible for critical components
        self.assertGreater(len(result.skipped_components), 0)  # Some components should be skipped
        
        # Critical components should be prioritized
        self.assertIn('Git', result.installable_components)
    
    def test_analyze_selective_installation_insufficient_space(self):
        """Test selective installation with insufficient space"""
        space_req = self.analyzer.calculate_space_requirements(self.mock_components)
        available_space = 1000000  # Only 1MB
        
        result = self.analyzer.analyze_selective_installation(space_req, available_space)
        
        self.assertIsInstance(result, SelectiveInstallationResult)
        self.assertFalse(result.installation_feasible)
        self.assertEqual(len(result.installable_components), 0)
        self.assertEqual(len(result.skipped_components), 3)  # All components skipped
    
    def test_get_best_drive_for_installation(self):
        """Test getting best drive for installation"""
        with patch.object(self.analyzer, 'analyze_system_storage', return_value=self.mock_drives):
            required_space = 100000000000  # 100GB
            
            best_drive = self.analyzer.get_best_drive_for_installation(required_space)
            
            self.assertIsNotNone(best_drive)
            # Should return D: drive as it has better performance score and more space
            self.assertEqual(best_drive.drive_letter, "D:")
    
    def test_get_best_drive_insufficient_space(self):
        """Test getting best drive when no drive has sufficient space"""
        with patch.object(self.analyzer, 'analyze_system_storage', return_value=self.mock_drives):
            required_space = 3000000000000  # 3TB (more than any drive has)
            
            best_drive = self.analyzer.get_best_drive_for_installation(required_space)
            
            self.assertIsNone(best_drive)
    
    def test_format_size(self):
        """Test size formatting"""
        self.assertEqual(self.analyzer._format_size(1024), "1.0 KB")
        self.assertEqual(self.analyzer._format_size(1048576), "1.0 MB")
        self.assertEqual(self.analyzer._format_size(1073741824), "1.0 GB")
    
    def test_calculate_drive_performance_score(self):
        """Test drive performance score calculation"""
        # Mock partition for system drive
        system_partition = Mock()
        system_partition.device = "C:"
        system_partition.opts = ""
        system_partition.fstype = "NTFS"
        
        # Mock usage with 50% free space
        usage = Mock()
        usage.total = 1000000000000
        usage.free = 500000000000
        
        score = self.analyzer._calculate_drive_performance_score(system_partition, usage, True)
        
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # System drive should get bonus points
        self.assertGreater(score, 0.3)


if __name__ == '__main__':
    unittest.main()