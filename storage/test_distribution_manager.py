"""
Unit tests for Distribution Manager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime, timedelta

from .distribution_manager import DistributionManager
from .models import (
    DriveInfo, DistributionPlan, DistributionResult, CleanupResult,
    RemovalSuggestion, RemovalSuggestions
)


class TestDistributionManager(unittest.TestCase):
    """Test cases for DistributionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = DistributionManager()
        
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
            ),
            DriveInfo(
                drive_letter="E:",
                total_space=500000000000,  # 500GB
                available_space=100000000,  # 100MB (low space)
                used_space=499900000000,
                file_system="NTFS",
                drive_type="fixed",
                is_system_drive=False,
                performance_score=0.7
            )
        ]
        
        # Mock component data
        self.mock_components = [
            {
                'name': 'Git',
                'installation_size': 100000000,  # 100MB
                'priority': 'critical',
                'has_dependencies': False,
                'is_system_component': False
            },
            {
                'name': 'Node.js',
                'installation_size': 200000000,  # 200MB
                'priority': 'high',
                'has_dependencies': True,
                'is_system_component': False
            },
            {
                'name': 'Optional Tool',
                'installation_size': 500000000,  # 500MB
                'priority': 'optional',
                'has_dependencies': False,
                'is_system_component': False,
                'last_used': datetime.now() - timedelta(days=30)
            },
            {
                'name': 'Large Tool',
                'installation_size': 1000000000,  # 1GB
                'priority': 'medium',
                'has_dependencies': False,
                'is_system_component': False
            }
        ]
    
    def test_distribute_components_success(self):
        """Test successful component distribution"""
        result = self.manager.distribute_components(self.mock_drives, self.mock_components)
        
        self.assertIsInstance(result, DistributionResult)
        self.assertTrue(result.distribution_feasible)
        self.assertEqual(len(result.distribution_plans), len(self.mock_components))
        self.assertGreater(len(result.drives_used), 0)
        
        # Check that critical components are handled
        git_plan = next(p for p in result.distribution_plans if p.component_name == 'Git')
        self.assertIsNotNone(git_plan)
        self.assertIn(git_plan.target_drive, ['C:', 'D:'])  # Should go to a good drive
    
    def test_distribute_components_insufficient_space(self):
        """Test distribution when there's insufficient space"""
        # Create drives with very limited space
        limited_drives = [
            DriveInfo(
                drive_letter="C:",
                total_space=1000000000,  # 1GB
                available_space=50000000,  # 50MB
                used_space=950000000,
                file_system="NTFS",
                drive_type="fixed",
                is_system_drive=True,
                performance_score=0.8
            )
        ]
        
        result = self.manager.distribute_components(limited_drives, self.mock_components)
        
        self.assertIsInstance(result, DistributionResult)
        self.assertFalse(result.distribution_feasible)
        self.assertGreater(len(result.warnings), 0)
    
    def test_filter_suitable_drives(self):
        """Test filtering of suitable drives"""
        # Add unsuitable drives
        all_drives = self.mock_drives + [
            DriveInfo(
                drive_letter="F:",
                total_space=1000000000,
                available_space=500000000,  # 500MB - below 1GB threshold
                used_space=500000000,
                file_system="FAT32",
                drive_type="removable",
                is_system_drive=False,
                performance_score=0.3
            ),
            DriveInfo(
                drive_letter="Z:",
                total_space=5000000000000,
                available_space=4000000000000,
                used_space=1000000000000,
                file_system="NTFS",
                drive_type="network",
                is_system_drive=False,
                performance_score=0.5
            )
        ]
        
        suitable = self.manager._filter_suitable_drives(all_drives)
        
        # Should exclude the removable and network drives, and the one with insufficient space
        self.assertEqual(len(suitable), 2)  # Only C: and D:
        drive_letters = [d.drive_letter for d in suitable]
        self.assertIn("C:", drive_letters)
        self.assertIn("D:", drive_letters)
        self.assertNotIn("F:", drive_letters)  # Removable with low space
        self.assertNotIn("Z:", drive_letters)  # Network drive
    
    def test_sort_components_for_distribution(self):
        """Test component sorting for distribution"""
        sorted_components = self.manager._sort_components_for_distribution(self.mock_components)
        
        # Critical components should come first
        self.assertEqual(sorted_components[0]['name'], 'Git')  # Critical priority
        
        # Within same priority, larger components should come first
        high_priority_components = [c for c in sorted_components if c['priority'] == 'high']
        if len(high_priority_components) > 1:
            sizes = [c['installation_size'] for c in high_priority_components]
            self.assertEqual(sizes, sorted(sizes, reverse=True))
    
    def test_find_best_drive_for_component(self):
        """Test finding best drive for a component"""
        component = self.mock_components[0]  # Git - critical component
        
        best_drive = self.manager._find_best_drive_for_component(
            self.mock_drives, component, []
        )
        
        self.assertIsNotNone(best_drive)
        # Should prefer D: drive due to higher performance score and more space
        self.assertEqual(best_drive.drive_letter, "D:")
    
    def test_calculate_drive_score_for_component(self):
        """Test drive score calculation"""
        component = self.mock_components[0]  # Git
        drive = self.mock_drives[1]  # D: drive
        
        score = self.manager._calculate_drive_score_for_component(
            drive, component, 0, drive.available_space
        )
        
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('os.remove')
    def test_cleanup_temporary_files(self, mock_remove, mock_getsize, mock_getmtime, 
                                   mock_walk, mock_exists):
        """Test cleanup of temporary files"""
        # Mock file system
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/temp', [], ['file1.tmp', 'file2.log', 'file3.txt'])
        ]
        
        # Mock file times (old files)
        old_time = datetime.now() - timedelta(hours=2)
        mock_getmtime.return_value = old_time.timestamp()
        mock_getsize.return_value = 1024  # 1KB per file
        
        installation_paths = ['/test/install']
        result = self.manager.cleanup_temporary_files(installation_paths)
        
        self.assertIsInstance(result, CleanupResult)
        self.assertTrue(result.success)
        self.assertGreater(result.space_freed, 0)
        self.assertGreater(len(result.cleaned_files), 0)
    
    @patch('os.path.exists')
    @patch('os.walk')
    def test_cleanup_temporary_files_no_files(self, mock_walk, mock_exists):
        """Test cleanup when no files exist"""
        mock_exists.return_value = False
        
        result = self.manager.cleanup_temporary_files(['/nonexistent'])
        
        self.assertIsInstance(result, CleanupResult)
        self.assertTrue(result.success)
        self.assertEqual(result.space_freed, 0)
        self.assertEqual(len(result.cleaned_files), 0)
    
    def test_suggest_component_removal(self):
        """Test component removal suggestions"""
        required_space = 300000000  # 300MB
        
        suggestions = self.manager.suggest_component_removal(
            self.mock_components, required_space
        )
        
        self.assertIsInstance(suggestions, RemovalSuggestions)
        self.assertGreater(len(suggestions.suggestions), 0)
        self.assertGreater(suggestions.total_potential_space, 0)
        
        # Optional components should be suggested first
        first_suggestion = suggestions.suggestions[0]
        self.assertEqual(first_suggestion.component_name, 'Optional Tool')
        self.assertEqual(first_suggestion.removal_safety, 'safe')
    
    def test_sort_components_for_removal(self):
        """Test sorting components for removal"""
        sorted_components = self.manager._sort_components_for_removal(self.mock_components)
        
        # Optional components should come first
        self.assertEqual(sorted_components[0]['name'], 'Optional Tool')
        
        # Critical components should come last
        critical_components = [c for c in sorted_components if c['priority'] == 'critical']
        if critical_components:
            # Critical should be at the end
            critical_index = sorted_components.index(critical_components[0])
            self.assertGreater(critical_index, len(sorted_components) // 2)
    
    def test_assess_removal_safety(self):
        """Test removal safety assessment"""
        # Safe component
        safe_component = {
            'priority': 'optional',
            'has_dependencies': False,
            'is_system_component': False
        }
        safety = self.manager._assess_removal_safety(safe_component)
        self.assertEqual(safety, 'safe')
        
        # Risky component
        risky_component = {
            'priority': 'critical',
            'has_dependencies': False,
            'is_system_component': True
        }
        safety = self.manager._assess_removal_safety(risky_component)
        self.assertEqual(safety, 'risky')
        
        # Caution component
        caution_component = {
            'priority': 'high',
            'has_dependencies': True,
            'is_system_component': False
        }
        safety = self.manager._assess_removal_safety(caution_component)
        self.assertEqual(safety, 'caution')
    
    def test_assess_removal_impact(self):
        """Test removal impact assessment"""
        # High impact
        high_impact = {
            'priority': 'critical',
            'usage_frequency': 5,
            'has_dependencies': True
        }
        impact = self.manager._assess_removal_impact(high_impact)
        self.assertEqual(impact, 'high')
        
        # Low impact
        low_impact = {
            'priority': 'optional',
            'usage_frequency': 1,
            'has_dependencies': False
        }
        impact = self.manager._assess_removal_impact(low_impact)
        self.assertEqual(impact, 'low')
    
    def test_create_installation_path_windows(self):
        """Test installation path creation on Windows"""
        with patch('os.name', 'nt'):
            drive = self.mock_drives[0]  # C: drive
            path = self.manager._create_installation_path(drive, 'TestComponent')
            
            expected = os.path.join("C:", "Program Files", "EnvironmentDev", "TestComponent")
            self.assertEqual(path, expected)
    
    def test_create_installation_path_unix(self):
        """Test installation path creation on Unix"""
        with patch('os.name', 'posix'):
            drive = DriveInfo(
                drive_letter="/usr",
                total_space=1000000000000,
                available_space=500000000000,
                used_space=500000000000,
                file_system="ext4",
                drive_type="fixed",
                is_system_drive=False,
                performance_score=0.8
            )
            path = self.manager._create_installation_path(drive, 'TestComponent')
            
            expected = os.path.join("/usr", "opt", "environmentdev", "TestComponent")
            self.assertEqual(path, expected)
    
    def test_format_size(self):
        """Test size formatting"""
        self.assertEqual(self.manager._format_size(1024), "1.0 KB")
        self.assertEqual(self.manager._format_size(1048576), "1.0 MB")
        self.assertEqual(self.manager._format_size(1073741824), "1.0 GB")


if __name__ == '__main__':
    unittest.main()