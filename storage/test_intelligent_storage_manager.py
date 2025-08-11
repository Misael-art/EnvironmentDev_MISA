"""
Unit tests for Intelligent Storage Manager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from .intelligent_storage_manager import IntelligentStorageManager
from .models import (
    SpaceRequirement, SelectiveInstallationResult, CleanupResult,
    RemovalSuggestions, DistributionResult, CompressionResult,
    StorageAnalysisResult, DriveInfo, ComponentSpaceRequirement,
    InstallationPriority
)


class TestIntelligentStorageManager(unittest.TestCase):
    """Test cases for IntelligentStorageManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = IntelligentStorageManager()
        
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
            }
        ]
        
        # Mock drives
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
    
    @patch.object(IntelligentStorageManager, '_format_size')
    def test_calculate_space_requirements_before_installation(self, mock_format):
        """Test space requirements calculation"""
        mock_format.return_value = "200 MB"
        
        with patch.object(self.manager.storage_analyzer, 'calculate_space_requirements') as mock_calc:
            mock_space_req = SpaceRequirement(
                components=[
                    ComponentSpaceRequirement(
                        component_name='Git',
                        download_size=50000000,
                        installation_size=100000000,
                        temporary_space=50000000,
                        total_required=200000000,
                        priority=InstallationPriority.CRITICAL,
                        can_be_compressed=True,
                        compression_ratio=0.7
                    )
                ],
                total_download_size=50000000,
                total_installation_size=100000000,
                total_temporary_space=50000000,
                total_required_space=200000000,
                recommended_free_space=240000000,
                analysis_timestamp=datetime.now()
            )
            mock_calc.return_value = mock_space_req
            
            result = self.manager.calculate_space_requirements_before_installation(
                self.mock_components
            )
            
            self.assertIsInstance(result, SpaceRequirement)
            self.assertEqual(result.total_required_space, 200000000)
            mock_calc.assert_called_once_with(self.mock_components)
    
    def test_enable_selective_installation_based_on_available_space(self):
        """Test selective installation analysis"""
        available_space = 1000000000  # 1GB
        
        with patch.object(self.manager, 'calculate_space_requirements_before_installation') as mock_calc:
            with patch.object(self.manager.storage_analyzer, 'analyze_selective_installation') as mock_analyze:
                # Mock space requirements
                mock_space_req = Mock()
                mock_calc.return_value = mock_space_req
                
                # Mock selective installation result
                mock_result = SelectiveInstallationResult(
                    installable_components=['Git', 'Node.js'],
                    skipped_components=[],
                    space_saved=0,
                    total_space_required=180000000,
                    installation_feasible=True,
                    recommendations=['All components can be installed']
                )
                mock_analyze.return_value = mock_result
                
                result = self.manager.enable_selective_installation_based_on_available_space(
                    available_space, self.mock_components
                )
                
                self.assertIsInstance(result, SelectiveInstallationResult)
                self.assertTrue(result.installation_feasible)
                self.assertEqual(len(result.installable_components), 2)
                mock_analyze.assert_called_once_with(mock_space_req, available_space)
    
    def test_automatically_remove_temporary_files_after_installation(self):
        """Test automatic cleanup of temporary files"""
        installation_paths = ['/test/install1', '/test/install2']
        
        # Mock compression manager initialization and cleanup
        with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.CompressionManager') as mock_cm_class:
            mock_cm = Mock()
            mock_cm_class.return_value = mock_cm
            
            mock_cleanup_result = CleanupResult(
                cleaned_files=['/temp/file1.tmp', '/temp/file2.log'],
                space_freed=1048576,  # 1MB
                cleanup_duration=2.5,
                errors=[],
                success=True
            )
            mock_cm.cleanup_temporary_files.return_value = mock_cleanup_result
            
            result = self.manager.automatically_remove_temporary_files_after_installation(
                installation_paths
            )
            
            self.assertIsInstance(result, CleanupResult)
            self.assertTrue(result.success)
            self.assertEqual(result.space_freed, 1048576)
            mock_cm.cleanup_temporary_files.assert_called_once_with(installation_paths, [])
    
    def test_suggest_components_for_removal_when_storage_low(self):
        """Test component removal suggestions"""
        required_space = 500000000  # 500MB
        
        # Mock distribution manager initialization and suggestions
        with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.DistributionManager') as mock_dm_class:
            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_suggestions = RemovalSuggestions(
                suggestions=[],
                total_potential_space=300000000,
                recommended_removals=['Optional Tool'],
                analysis_timestamp=datetime.now()
            )
            mock_dm.suggest_component_removal.return_value = mock_suggestions
            
            result = self.manager.suggest_components_for_removal_when_storage_low(
                self.mock_components, required_space
            )
            
            self.assertIsInstance(result, RemovalSuggestions)
            self.assertEqual(result.total_potential_space, 300000000)
            mock_dm.suggest_component_removal.assert_called_once_with(
                self.mock_components, required_space
            )
    
    def test_intelligently_distribute_across_multiple_drives(self):
        """Test intelligent distribution across drives"""
        # Mock distribution manager initialization and distribution
        with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.DistributionManager') as mock_dm_class:
            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_distribution = DistributionResult(
                distribution_plans=[],
                total_components=2,
                drives_used=['C:', 'D:'],
                space_optimization=75.0,
                distribution_feasible=True,
                warnings=[]
            )
            mock_dm.distribute_components.return_value = mock_distribution
            
            result = self.manager.intelligently_distribute_across_multiple_drives(
                self.mock_drives, self.mock_components
            )
            
            self.assertIsInstance(result, DistributionResult)
            self.assertTrue(result.distribution_feasible)
            self.assertEqual(len(result.drives_used), 2)
            mock_dm.distribute_components.assert_called_once_with(
                self.mock_drives, self.mock_components
            )
    
    def test_implement_intelligent_compression(self):
        """Test intelligent compression implementation"""
        target_paths = ['/test/path1', '/test/path2']
        
        # Mock compression manager initialization and compression
        with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.CompressionManager') as mock_cm_class:
            mock_cm = Mock()
            mock_cm_class.return_value = mock_cm
            
            mock_compression = CompressionResult(
                compressed_files=['/test/path1/file1.txt'],
                original_total_size=1048576,
                compressed_total_size=314572,
                space_saved=734004,
                compression_ratio=0.3,
                compression_duration=3.2,
                errors=[],
                success=True
            )
            mock_cm.compress_intelligently.return_value = mock_compression
            
            result = self.manager.implement_intelligent_compression(target_paths)
            
            self.assertIsInstance(result, CompressionResult)
            self.assertTrue(result.success)
            self.assertGreater(result.space_saved, 0)
            mock_cm.compress_intelligently.assert_called_once_with(target_paths, {})
    
    def test_perform_comprehensive_storage_analysis(self):
        """Test comprehensive storage analysis"""
        # Mock all the sub-components
        with patch.object(self.manager.storage_analyzer, 'analyze_system_storage') as mock_drives:
            with patch.object(self.manager, 'calculate_space_requirements_before_installation') as mock_space:
                with patch.object(self.manager.storage_analyzer, 'get_best_drive_for_installation') as mock_best:
                    with patch.object(self.manager, 'enable_selective_installation_based_on_available_space') as mock_selective:
                        with patch.object(self.manager, 'suggest_components_for_removal_when_storage_low') as mock_removal:
                            with patch.object(self.manager, 'intelligently_distribute_across_multiple_drives') as mock_distribute:
                                
                                # Setup mocks
                                mock_drives.return_value = self.mock_drives
                                mock_space.return_value = Mock(recommended_free_space=200000000)
                                mock_best.return_value = self.mock_drives[1]  # D: drive
                                mock_selective.return_value = Mock(installation_feasible=True)
                                mock_removal.return_value = Mock(suggestions=[])
                                mock_distribute.return_value = Mock(distribution_feasible=True)
                                
                                result = self.manager.perform_comprehensive_storage_analysis(
                                    self.mock_components
                                )
                                
                                self.assertIsInstance(result, StorageAnalysisResult)
                                self.assertTrue(result.overall_feasibility)
                                self.assertEqual(len(result.drives), 2)
                                self.assertIsNotNone(result.space_requirements)
                                self.assertIsNotNone(result.selective_installation)
                                self.assertIsNotNone(result.distribution_result)
    
    def test_format_size(self):
        """Test size formatting"""
        self.assertEqual(self.manager._format_size(1024), "1.0 KB")
        self.assertEqual(self.manager._format_size(1048576), "1.0 MB")
        self.assertEqual(self.manager._format_size(1073741824), "1.0 GB")
    
    def test_error_handling_in_space_calculation(self):
        """Test error handling in space calculation"""
        with patch.object(self.manager.storage_analyzer, 'calculate_space_requirements') as mock_calc:
            mock_calc.side_effect = Exception("Test error")
            
            with self.assertRaises(Exception):
                self.manager.calculate_space_requirements_before_installation(
                    self.mock_components
                )
    
    def test_error_handling_in_selective_installation(self):
        """Test error handling in selective installation"""
        with patch.object(self.manager, 'calculate_space_requirements_before_installation') as mock_calc:
            mock_calc.side_effect = Exception("Test error")
            
            with self.assertRaises(Exception):
                self.manager.enable_selective_installation_based_on_available_space(
                    1000000000, self.mock_components
                )
    
    def test_lazy_initialization_of_managers(self):
        """Test that managers are initialized only when needed"""
        # Initially, managers should be None
        self.assertIsNone(self.manager.distribution_manager)
        self.assertIsNone(self.manager.compression_manager)
        
        # After calling methods that need them, they should be initialized
        with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.CompressionManager') as mock_cm:
            with patch('environment_dev_deep_evaluation.storage.intelligent_storage_manager.DistributionManager') as mock_dm:
                mock_cm.return_value = Mock()
                mock_dm.return_value = Mock()
                
                # This should initialize compression_manager
                self.manager.automatically_remove_temporary_files_after_installation([])
                mock_cm.assert_called_once()
                
                # This should initialize distribution_manager
                self.manager.suggest_components_for_removal_when_storage_low([], 1000)
                mock_dm.assert_called_once()


if __name__ == '__main__':
    unittest.main()