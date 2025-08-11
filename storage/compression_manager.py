"""
Compression Manager for Intelligent Storage Optimization

This module provides intelligent compression capabilities for rarely-accessed components,
version history, and configuration backups to optimize storage usage.
"""

import os
import gzip
import lzma
import shutil
import logging
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

from .models import (
    CompressionCandidate, CompressionResult, CompressionType
)


class CompressionManager:
    """
    Manages intelligent compression operations for storage optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.compression_metadata_file = "compression_metadata.json"
        self.access_tracking_file = "access_tracking.json"
        self.compression_lock = threading.Lock()
        
        # Compression settings
        self.min_file_size = 1024 * 1024  # 1MB minimum for compression
        self.access_threshold_days = 30  # Files not accessed in 30 days are candidates
        self.compression_ratio_threshold = 0.8  # Only compress if ratio < 0.8
        
        # File extensions that compress well
        self.compressible_extensions = {
            '.txt', '.log', '.xml', '.json', '.csv', '.sql', '.md', '.html',
            '.css', '.js', '.py', '.java', '.cpp', '.h', '.c', '.cs',
            '.config', '.ini', '.conf', '.yaml', '.yml'
        }
        
        # File extensions to avoid compressing
        self.avoid_compression = {
            '.zip', '.rar', '.7z', '.gz', '.bz2', '.xz', '.lzma',
            '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.avi',
            '.exe', '.dll', '.so', '.dylib'
        }
    
    def compress_intelligently(
        self, 
        target_paths: List[str],
        compression_criteria: Dict = None
    ) -> CompressionResult:
        """
        Perform intelligent compression on target paths
        
        Args:
            target_paths: Paths to analyze for compression
            compression_criteria: Custom criteria for compression decisions
            
        Returns:
            CompressionResult: Result of compression operations
        """
        try:
            self.logger.info(f"Starting intelligent compression for {len(target_paths)} paths")
            start_time = datetime.now()
            
            # Update criteria with defaults
            criteria = self._merge_compression_criteria(compression_criteria or {})
            
            # Identify compression candidates
            candidates = self.identify_compression_candidates(target_paths, criteria)
            
            if not candidates:
                self.logger.info("No compression candidates found")
                return CompressionResult(
                    compressed_files=[],
                    original_total_size=0,
                    compressed_total_size=0,
                    space_saved=0,
                    compression_ratio=1.0,
                    compression_duration=0.0,
                    errors=[],
                    success=True
                )
            
            # Perform compression
            compressed_files = []
            original_total_size = 0
            compressed_total_size = 0
            errors = []
            
            # Use thread pool for parallel compression
            max_workers = min(4, len(candidates))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit compression tasks
                future_to_candidate = {
                    executor.submit(self._compress_file, candidate): candidate
                    for candidate in candidates
                }
                
                # Collect results
                for future in as_completed(future_to_candidate):
                    candidate = future_to_candidate[future]
                    try:
                        success, original_size, compressed_size, error = future.result()
                        
                        if success:
                            compressed_files.append(candidate.file_path)
                            original_total_size += original_size
                            compressed_total_size += compressed_size
                        else:
                            if error:
                                errors.append(f"Error compressing {candidate.file_path}: {error}")
                            
                    except Exception as e:
                        errors.append(f"Exception compressing {candidate.file_path}: {str(e)}")
            
            # Calculate results
            space_saved = original_total_size - compressed_total_size
            compression_ratio = compressed_total_size / original_total_size if original_total_size > 0 else 1.0
            compression_duration = (datetime.now() - start_time).total_seconds()
            
            # Update metadata
            self._update_compression_metadata(compressed_files)
            
            result = CompressionResult(
                compressed_files=compressed_files,
                original_total_size=original_total_size,
                compressed_total_size=compressed_total_size,
                space_saved=space_saved,
                compression_ratio=compression_ratio,
                compression_duration=compression_duration,
                errors=errors,
                success=len(errors) == 0
            )
            
            self.logger.info(
                f"Compression completed: {len(compressed_files)} files, "
                f"{self._format_size(space_saved)} saved"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intelligent compression: {e}")
            return CompressionResult(
                compressed_files=[],
                original_total_size=0,
                compressed_total_size=0,
                space_saved=0,
                compression_ratio=1.0,
                compression_duration=0.0,
                errors=[str(e)],
                success=False
            )
    
    def identify_compression_candidates(
        self, 
        target_paths: List[str],
        criteria: Dict = None
    ) -> List[CompressionCandidate]:
        """
        Identify files that are good candidates for compression
        
        Args:
            target_paths: Paths to analyze
            criteria: Compression criteria
            
        Returns:
            List[CompressionCandidate]: List of compression candidates
        """
        try:
            candidates = []
            criteria = criteria or {}
            
            # Load access tracking data
            access_data = self._load_access_tracking()
            
            for target_path in target_paths:
                if not os.path.exists(target_path):
                    continue
                
                if os.path.isfile(target_path):
                    candidate = self._analyze_file_for_compression(target_path, access_data, criteria)
                    if candidate:
                        candidates.append(candidate)
                elif os.path.isdir(target_path):
                    dir_candidates = self._analyze_directory_for_compression(target_path, access_data, criteria)
                    candidates.extend(dir_candidates)
            
            # Sort candidates by potential space savings
            candidates.sort(key=lambda c: c.original_size * (1 - c.compression_ratio), reverse=True)
            
            self.logger.info(f"Identified {len(candidates)} compression candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error identifying compression candidates: {e}")
            return []
    
    def _analyze_file_for_compression(
        self, 
        file_path: str, 
        access_data: Dict,
        criteria: Dict
    ) -> Optional[CompressionCandidate]:
        """Analyze a single file for compression suitability"""
        try:
            # Check if file is already compressed
            if self._is_already_compressed(file_path):
                return None
            
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            
            # Skip small files
            min_size = criteria.get('min_file_size', self.min_file_size)
            if file_size < min_size:
                return None
            
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext in self.avoid_compression:
                return None
            
            # Estimate compression ratio
            compression_type, estimated_ratio = self._estimate_compression_ratio(file_path, ext)
            
            # Skip if compression won't be effective
            ratio_threshold = criteria.get('compression_ratio_threshold', self.compression_ratio_threshold)
            if estimated_ratio >= ratio_threshold:
                return None
            
            # Check access patterns
            last_accessed = datetime.fromtimestamp(stat.st_atime)
            access_frequency = access_data.get(file_path, 0)
            
            # Check access threshold
            access_threshold = criteria.get('access_threshold_days', self.access_threshold_days)
            if (datetime.now() - last_accessed).days < access_threshold:
                return None
            
            estimated_compressed_size = int(file_size * estimated_ratio)
            
            return CompressionCandidate(
                file_path=file_path,
                original_size=file_size,
                estimated_compressed_size=estimated_compressed_size,
                compression_ratio=estimated_ratio,
                last_accessed=last_accessed,
                access_frequency=access_frequency,
                compression_type=compression_type
            )
            
        except Exception as e:
            self.logger.warning(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _analyze_directory_for_compression(
        self, 
        directory: str, 
        access_data: Dict,
        criteria: Dict
    ) -> List[CompressionCandidate]:
        """Analyze directory for compression candidates"""
        candidates = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip certain directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    candidate = self._analyze_file_for_compression(file_path, access_data, criteria)
                    if candidate:
                        candidates.append(candidate)
                        
        except Exception as e:
            self.logger.warning(f"Error analyzing directory {directory}: {e}")
        
        return candidates
    
    def _estimate_compression_ratio(self, file_path: str, extension: str) -> Tuple[CompressionType, float]:
        """Estimate compression ratio for a file"""
        # Default ratios based on file type
        ratio_estimates = {
            '.txt': 0.3, '.log': 0.2, '.xml': 0.2, '.json': 0.3,
            '.csv': 0.4, '.sql': 0.3, '.md': 0.4, '.html': 0.3,
            '.css': 0.4, '.js': 0.5, '.py': 0.5, '.java': 0.5,
            '.cpp': 0.5, '.h': 0.5, '.c': 0.5, '.cs': 0.5,
            '.config': 0.3, '.ini': 0.4, '.conf': 0.3,
            '.yaml': 0.3, '.yml': 0.3
        }
        
        estimated_ratio = ratio_estimates.get(extension, 0.7)
        
        # Choose compression type based on file characteristics
        if extension in ['.log', '.txt', '.csv']:
            compression_type = CompressionType.GZIP
        elif extension in ['.xml', '.json', '.config']:
            compression_type = CompressionType.LZMA
        elif ZSTD_AVAILABLE and extension in ['.js', '.py', '.java']:
            compression_type = CompressionType.ZSTD
        else:
            compression_type = CompressionType.GZIP
        
        # For small sample, try actual compression to get better estimate
        try:
            if os.path.getsize(file_path) < 10 * 1024 * 1024:  # 10MB
                sample_ratio = self._sample_compression_ratio(file_path, compression_type)
                if sample_ratio > 0:
                    estimated_ratio = sample_ratio
        except Exception:
            pass  # Use default estimate
        
        return compression_type, estimated_ratio
    
    def _sample_compression_ratio(self, file_path: str, compression_type: CompressionType) -> float:
        """Sample compression ratio by compressing first part of file"""
        try:
            sample_size = min(1024 * 1024, os.path.getsize(file_path))  # 1MB sample
            
            with open(file_path, 'rb') as f:
                sample_data = f.read(sample_size)
            
            if compression_type == CompressionType.GZIP:
                compressed_data = gzip.compress(sample_data)
            elif compression_type == CompressionType.LZMA:
                compressed_data = lzma.compress(sample_data)
            elif compression_type == CompressionType.ZSTD and ZSTD_AVAILABLE:
                cctx = zstd.ZstdCompressor()
                compressed_data = cctx.compress(sample_data)
            else:
                return 0.0
            
            return len(compressed_data) / len(sample_data)
            
        except Exception:
            return 0.0
    
    def _compress_file(self, candidate: CompressionCandidate) -> Tuple[bool, int, int, Optional[str]]:
        """Compress a single file"""
        try:
            file_path = candidate.file_path
            compressed_path = file_path + '.compressed'
            
            # Get original size
            original_size = os.path.getsize(file_path)
            
            # Perform compression
            if candidate.compression_type == CompressionType.GZIP:
                success = self._compress_with_gzip(file_path, compressed_path)
            elif candidate.compression_type == CompressionType.LZMA:
                success = self._compress_with_lzma(file_path, compressed_path)
            elif candidate.compression_type == CompressionType.ZSTD and ZSTD_AVAILABLE:
                success = self._compress_with_zstd(file_path, compressed_path)
            else:
                return False, 0, 0, "Unsupported compression type"
            
            if not success:
                return False, 0, 0, "Compression failed"
            
            # Check if compression was effective
            compressed_size = os.path.getsize(compressed_path)
            actual_ratio = compressed_size / original_size
            
            if actual_ratio >= self.compression_ratio_threshold:
                # Compression not effective, remove compressed file
                os.remove(compressed_path)
                return False, 0, 0, "Compression not effective"
            
            # Replace original with compressed file
            backup_path = file_path + '.backup'
            os.rename(file_path, backup_path)
            os.rename(compressed_path, file_path)
            
            # Create metadata file
            self._create_compression_metadata(file_path, backup_path, candidate.compression_type, original_size)
            
            # Remove backup after successful compression
            os.remove(backup_path)
            
            return True, original_size, compressed_size, None
            
        except Exception as e:
            return False, 0, 0, str(e)
    
    def _compress_with_gzip(self, input_path: str, output_path: str) -> bool:
        """Compress file using gzip"""
        try:
            with open(input_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self.logger.error(f"GZIP compression failed for {input_path}: {e}")
            return False
    
    def _compress_with_lzma(self, input_path: str, output_path: str) -> bool:
        """Compress file using LZMA"""
        try:
            with open(input_path, 'rb') as f_in:
                with lzma.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self.logger.error(f"LZMA compression failed for {input_path}: {e}")
            return False
    
    def _compress_with_zstd(self, input_path: str, output_path: str) -> bool:
        """Compress file using Zstandard"""
        try:
            cctx = zstd.ZstdCompressor()
            with open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    cctx.copy_stream(f_in, f_out)
            return True
        except Exception as e:
            self.logger.error(f"ZSTD compression failed for {input_path}: {e}")
            return False
    
    def decompress_file(self, file_path: str) -> bool:
        """Decompress a previously compressed file"""
        try:
            metadata = self._load_compression_metadata(file_path)
            if not metadata:
                return False
            
            compression_type = CompressionType(metadata['compression_type'])
            original_size = metadata['original_size']
            
            # Create temporary decompressed file
            temp_path = file_path + '.decompressed'
            
            if compression_type == CompressionType.GZIP:
                success = self._decompress_gzip(file_path, temp_path)
            elif compression_type == CompressionType.LZMA:
                success = self._decompress_lzma(file_path, temp_path)
            elif compression_type == CompressionType.ZSTD and ZSTD_AVAILABLE:
                success = self._decompress_zstd(file_path, temp_path)
            else:
                return False
            
            if not success:
                return False
            
            # Verify decompressed size
            if os.path.getsize(temp_path) != original_size:
                os.remove(temp_path)
                return False
            
            # Replace compressed file with decompressed
            os.remove(file_path)
            os.rename(temp_path, file_path)
            
            # Remove metadata
            self._remove_compression_metadata(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error decompressing {file_path}: {e}")
            return False
    
    def _decompress_gzip(self, input_path: str, output_path: str) -> bool:
        """Decompress gzip file"""
        try:
            with gzip.open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception:
            return False
    
    def _decompress_lzma(self, input_path: str, output_path: str) -> bool:
        """Decompress LZMA file"""
        try:
            with lzma.open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception:
            return False
    
    def _decompress_zstd(self, input_path: str, output_path: str) -> bool:
        """Decompress Zstandard file"""
        try:
            dctx = zstd.ZstdDecompressor()
            with open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    dctx.copy_stream(f_in, f_out)
            return True
        except Exception:
            return False
    
    def compress_rarely_accessed_components(self, component_paths: List[str]) -> CompressionResult:
        """Compress components that are rarely accessed"""
        criteria = {
            'access_threshold_days': 60,  # 2 months
            'min_file_size': 5 * 1024 * 1024,  # 5MB
            'compression_ratio_threshold': 0.9
        }
        
        return self.compress_intelligently(component_paths, criteria)
    
    def compress_previous_version_history(self, history_paths: List[str]) -> CompressionResult:
        """Compress previous version history and backups"""
        criteria = {
            'access_threshold_days': 7,  # 1 week
            'min_file_size': 1024 * 1024,  # 1MB
            'compression_ratio_threshold': 0.8
        }
        
        return self.compress_intelligently(history_paths, criteria)
    
    def compress_configuration_backups(self, backup_paths: List[str]) -> CompressionResult:
        """Compress configuration backups"""
        criteria = {
            'access_threshold_days': 1,  # 1 day
            'min_file_size': 1024,  # 1KB
            'compression_ratio_threshold': 0.7
        }
        
        return self.compress_intelligently(backup_paths, criteria)
    
    def cleanup_temporary_files(
        self, 
        installation_paths: List[str],
        temp_directories: List[str]
    ) -> 'CleanupResult':
        """Clean up temporary files (imported from distribution_manager functionality)"""
        from .distribution_manager import DistributionManager
        
        # Use DistributionManager for cleanup functionality
        dist_manager = DistributionManager()
        return dist_manager.cleanup_temporary_files(installation_paths, temp_directories)
    
    def _is_already_compressed(self, file_path: str) -> bool:
        """Check if file is already compressed"""
        # Check if compression metadata exists
        metadata_path = file_path + '.compression_meta'
        if os.path.exists(metadata_path):
            return True
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.avoid_compression
    
    def _merge_compression_criteria(self, custom_criteria: Dict) -> Dict:
        """Merge custom criteria with defaults"""
        default_criteria = {
            'min_file_size': self.min_file_size,
            'access_threshold_days': self.access_threshold_days,
            'compression_ratio_threshold': self.compression_ratio_threshold
        }
        
        default_criteria.update(custom_criteria)
        return default_criteria
    
    def _load_access_tracking(self) -> Dict:
        """Load access tracking data"""
        try:
            if os.path.exists(self.access_tracking_file):
                with open(self.access_tracking_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _create_compression_metadata(
        self, 
        file_path: str, 
        backup_path: str,
        compression_type: CompressionType,
        original_size: int
    ):
        """Create compression metadata for a file"""
        metadata = {
            'compression_type': compression_type.value,
            'original_size': original_size,
            'compressed_timestamp': datetime.now().isoformat(),
            'original_hash': self._calculate_file_hash(backup_path)
        }
        
        metadata_path = file_path + '.compression_meta'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
    
    def _load_compression_metadata(self, file_path: str) -> Optional[Dict]:
        """Load compression metadata for a file"""
        metadata_path = file_path + '.compression_meta'
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _remove_compression_metadata(self, file_path: str):
        """Remove compression metadata for a file"""
        metadata_path = file_path + '.compression_meta'
        try:
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
        except Exception:
            pass
    
    def _update_compression_metadata(self, compressed_files: List[str]):
        """Update global compression metadata"""
        try:
            with self.compression_lock:
                metadata = {}
                if os.path.exists(self.compression_metadata_file):
                    with open(self.compression_metadata_file, 'r') as f:
                        metadata = json.load(f)
                
                metadata['last_compression'] = datetime.now().isoformat()
                metadata['compressed_files'] = metadata.get('compressed_files', [])
                metadata['compressed_files'].extend(compressed_files)
                
                with open(self.compression_metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            self.logger.warning(f"Error updating compression metadata: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"