"""
Unit tests for Compression Manager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
import gzip
import json
from datetime import datetime, timedelta

from .compression_manager import CompressionManager
from .models import CompressionCandidate, CompressionResult, CompressionType


class TestCompressionManager(unittest.TestCase):
    """Test cases for CompressionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CompressionManager()
        
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock compression candidates
        self.mock_candidates = [
            CompressionCandidate(
                file_path="/test/file1.txt",
                original_size=1048576,  # 1MB
                estimated_compressed_size=314572,  # ~30% compression
                compression_ratio=0.3,
                last_accessed=datetime.now() - timedelta(days=45),
                access_frequency=2,
                compression_type=CompressionType.GZIP
            ),
            CompressionCandidate(
                file_path="/test/file2.log",
                original_size=2097152,  # 2MB
                estimated_compressed_size=419430,  # ~20% compression
                compression_ratio=0.2,
                last_accessed=datetime.now() - timedelta(days=60),
                access_frequency=1,
                compression_type=CompressionType.GZIP
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.stat')
    def test_identify_compression_candidates(self, mock_stat, mock_walk, mock_exists):
        """Test identification of compression candidates"""
        # Mock file system
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/test', [], ['file1.txt', 'file2.log', 'file3.jpg'])
        ]
        
        # Mock file stats
        mock_stat_obj = Mock()
        mock_stat_obj.st_size = 2 * 1024 * 1024  # 2MB
        mock_stat_obj.st_atime = (datetime.now() - timedelta(days=45)).timestamp()
        mock_stat.return_value = mock_stat_obj
        
        # Mock access tracking
        with patch.object(self.manager, '_load_access_tracking', return_value={}):
            with patch.object(self.manager, '_is_already_compressed', return_value=False):
                with patch.object(self.manager, '_estimate_compression_ratio', 
                                return_value=(CompressionType.GZIP, 0.3)):
                    
                    candidates = self.manager.identify_compression_candidates(['/test'])
        
        # Should find candidates for .txt and .log files, but not .jpg
        self.assertGreater(len(candidates), 0)
        
        # Verify candidate properties
        for candidate in candidates:
            self.assertIsInstance(candidate, CompressionCandidate)
            self.assertGreater(candidate.original_size, 0)
            self.assertLess(candidate.compression_ratio, 1.0)
    
    @patch('os.path.exists')
    @patch('os.stat')
    def test_analyze_file_for_compression_suitable(self, mock_stat, mock_exists):
        """Test analysis of suitable file for compression"""
        mock_exists.return_value = True
        
        # Mock file stats for old, large text file
        mock_stat_obj = Mock()
        mock_stat_obj.st_size = 5 * 1024 * 1024  # 5MB
        mock_stat_obj.st_atime = (datetime.now() - timedelta(days=45)).timestamp()
        mock_stat.return_value = mock_stat_obj
        
        access_data = {}
        criteria = {}
        
        with patch.object(self.manager, '_is_already_compressed', return_value=False):
            with patch.object(self.manager, '_estimate_compression_ratio', 
                            return_value=(CompressionType.GZIP, 0.3)):
                
                candidate = self.manager._analyze_file_for_compression(
                    '/test/large_old_file.txt', access_data, criteria
                )
        
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.file_path, '/test/large_old_file.txt')
        self.assertEqual(candidate.original_size, 5 * 1024 * 1024)
        self.assertEqual(candidate.compression_ratio, 0.3)
    
    @patch('os.path.exists')
    @patch('os.stat')
    def test_analyze_file_for_compression_unsuitable(self, mock_stat, mock_exists):
        """Test analysis of unsuitable file for compression"""
        mock_exists.return_value = True
        
        # Mock file stats for recent, small file
        mock_stat_obj = Mock()
        mock_stat_obj.st_size = 1024  # 1KB (too small)
        mock_stat_obj.st_atime = datetime.now().timestamp()  # Recently accessed
        mock_stat.return_value = mock_stat_obj
        
        access_data = {}
        criteria = {}
        
        with patch.object(self.manager, '_is_already_compressed', return_value=False):
            candidate = self.manager._analyze_file_for_compression(
                '/test/small_recent_file.txt', access_data, criteria
            )
        
        self.assertIsNone(candidate)  # Should not be a candidate
    
    def test_estimate_compression_ratio(self):
        """Test compression ratio estimation"""
        # Test different file types
        test_cases = [
            ('.txt', 0.3),
            ('.log', 0.2),
            ('.jpg', 0.7),  # Should use default for unknown compressible type
            ('.zip', 0.7)   # Should use default
        ]
        
        for extension, expected_min_ratio in test_cases:
            with patch('os.path.getsize', return_value=100 * 1024 * 1024):  # 100MB
                compression_type, ratio = self.manager._estimate_compression_ratio(
                    f'/test/file{extension}', extension
                )
                
                self.assertIsInstance(compression_type, CompressionType)
                self.assertGreater(ratio, 0.0)
                self.assertLessEqual(ratio, 1.0)
    
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test data' * 1000)
    def test_sample_compression_ratio(self, mock_file, mock_getsize):
        """Test sample compression ratio calculation"""
        mock_getsize.return_value = 9000  # 9KB
        
        ratio = self.manager._sample_compression_ratio('/test/file.txt', CompressionType.GZIP)
        
        self.assertGreater(ratio, 0.0)
        self.assertLess(ratio, 1.0)  # Should achieve some compression
    
    @patch('os.path.getsize')
    @patch('os.rename')
    @patch('os.remove')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test data' * 1000)
    def test_compress_file_success(self, mock_file, mock_remove, mock_rename, mock_getsize):
        """Test successful file compression"""
        # Mock file sizes
        mock_getsize.side_effect = [9000, 3000]  # Original: 9KB, Compressed: 3KB
        
        candidate = self.mock_candidates[0]
        
        with patch.object(self.manager, '_compress_with_gzip', return_value=True):
            with patch.object(self.manager, '_create_compression_metadata'):
                success, original_size, compressed_size, error = self.manager._compress_file(candidate)
        
        self.assertTrue(success)
        self.assertEqual(original_size, 9000)
        self.assertEqual(compressed_size, 3000)
        self.assertIsNone(error)
    
    @patch('os.path.getsize')
    def test_compress_file_ineffective(self, mock_getsize):
        """Test compression when it's not effective"""
        # Mock file sizes - compression not effective
        mock_getsize.side_effect = [1000, 900]  # Only 10% compression
        
        candidate = self.mock_candidates[0]
        
        with patch.object(self.manager, '_compress_with_gzip', return_value=True):
            with patch('os.remove'):
                success, original_size, compressed_size, error = self.manager._compress_file(candidate)
        
        self.assertFalse(success)
        self.assertEqual(error, "Compression not effective")
    
    def test_compress_with_gzip(self):
        """Test GZIP compression"""
        # Create test input file
        input_path = os.path.join(self.temp_dir, 'input.txt')
        output_path = os.path.join(self.temp_dir, 'output.gz')
        
        test_data = b'This is test data for compression. ' * 100
        with open(input_path, 'wb') as f:
            f.write(test_data)
        
        # Test compression
        success = self.manager._compress_with_gzip(input_path, output_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify compressed file is smaller
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        self.assertLess(compressed_size, original_size)
        
        # Verify decompression works
        with gzip.open(output_path, 'rb') as f:
            decompressed_data = f.read()
        self.assertEqual(decompressed_data, test_data)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_compression_metadata(self, mock_file, mock_exists):
        """Test loading compression metadata"""
        mock_exists.return_value = True
        mock_metadata = {
            'compression_type': 'gzip',
            'original_size': 1000,
            'compressed_timestamp': '2023-01-01T00:00:00',
            'original_hash': 'abc123'
        }
        mock_file.return_value.read.return_value = json.dumps(mock_metadata)
        
        metadata = self.manager._load_compression_metadata('/test/file.txt')
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['compression_type'], 'gzip')
        self.assertEqual(metadata['original_size'], 1000)
    
    @patch('os.path.exists')
    def test_load_compression_metadata_not_exists(self, mock_exists):
        """Test loading metadata when file doesn't exist"""
        mock_exists.return_value = False
        
        metadata = self.manager._load_compression_metadata('/test/file.txt')
        
        self.assertIsNone(metadata)
    
    def test_is_already_compressed(self):
        """Test checking if file is already compressed"""
        # Test with compression metadata
        with patch('os.path.exists', return_value=True):
            self.assertTrue(self.manager._is_already_compressed('/test/file.txt'))
        
        # Test with compressed extension
        with patch('os.path.exists', return_value=False):
            self.assertTrue(self.manager._is_already_compressed('/test/file.zip'))
            self.assertFalse(self.manager._is_already_compressed('/test/file.txt'))
    
    def test_merge_compression_criteria(self):
        """Test merging compression criteria"""
        custom_criteria = {
            'min_file_size': 2048,
            'custom_setting': 'value'
        }
        
        merged = self.manager._merge_compression_criteria(custom_criteria)
        
        self.assertEqual(merged['min_file_size'], 2048)  # Custom value
        self.assertEqual(merged['access_threshold_days'], self.manager.access_threshold_days)  # Default
        self.assertEqual(merged['custom_setting'], 'value')  # Custom setting preserved
    
    @patch.object(CompressionManager, 'identify_compression_candidates')
    @patch.object(CompressionManager, '_compress_file')
    def test_compress_intelligently_success(self, mock_compress_file, mock_identify):
        """Test intelligent compression with successful results"""
        # Mock candidates
        mock_identify.return_value = self.mock_candidates
        
        # Mock compression results
        mock_compress_file.side_effect = [
            (True, 1048576, 314572, None),  # First file
            (True, 2097152, 419430, None)   # Second file
        ]
        
        with patch.object(self.manager, '_update_compression_metadata'):
            result = self.manager.compress_intelligently(['/test'])
        
        self.assertIsInstance(result, CompressionResult)
        self.assertTrue(result.success)
        self.assertEqual(len(result.compressed_files), 2)
        self.assertGreater(result.space_saved, 0)
        self.assertLess(result.compression_ratio, 1.0)
    
    @patch.object(CompressionManager, 'identify_compression_candidates')
    def test_compress_intelligently_no_candidates(self, mock_identify):
        """Test intelligent compression with no candidates"""
        mock_identify.return_value = []
        
        result = self.manager.compress_intelligently(['/test'])
        
        self.assertIsInstance(result, CompressionResult)
        self.assertTrue(result.success)
        self.assertEqual(len(result.compressed_files), 0)
        self.assertEqual(result.space_saved, 0)
        self.assertEqual(result.compression_ratio, 1.0)
    
    def test_compress_rarely_accessed_components(self):
        """Test compression of rarely accessed components"""
        with patch.object(self.manager, 'compress_intelligently') as mock_compress:
            mock_compress.return_value = CompressionResult(
                compressed_files=['/test/file.txt'],
                original_total_size=1000,
                compressed_total_size=300,
                space_saved=700,
                compression_ratio=0.3,
                compression_duration=1.0,
                errors=[],
                success=True
            )
            
            result = self.manager.compress_rarely_accessed_components(['/test'])
            
            self.assertTrue(result.success)
            mock_compress.assert_called_once()
            
            # Check that criteria were passed correctly
            args, kwargs = mock_compress.call_args
            criteria = args[1] if len(args) > 1 else kwargs.get('compression_criteria', {})
            self.assertEqual(criteria['access_threshold_days'], 60)
    
    def test_compress_configuration_backups(self):
        """Test compression of configuration backups"""
        with patch.object(self.manager, 'compress_intelligently') as mock_compress:
            mock_compress.return_value = CompressionResult(
                compressed_files=['/test/config.bak'],
                original_total_size=500,
                compressed_total_size=150,
                space_saved=350,
                compression_ratio=0.3,
                compression_duration=0.5,
                errors=[],
                success=True
            )
            
            result = self.manager.compress_configuration_backups(['/test'])
            
            self.assertTrue(result.success)
            mock_compress.assert_called_once()
            
            # Check criteria
            args, kwargs = mock_compress.call_args
            criteria = args[1] if len(args) > 1 else kwargs.get('compression_criteria', {})
            self.assertEqual(criteria['access_threshold_days'], 1)
            self.assertEqual(criteria['min_file_size'], 1024)
    
    def test_format_size(self):
        """Test size formatting"""
        self.assertEqual(self.manager._format_size(1024), "1.0 KB")
        self.assertEqual(self.manager._format_size(1048576), "1.0 MB")
        self.assertEqual(self.manager._format_size(1073741824), "1.0 GB")


if __name__ == '__main__':
    unittest.main()