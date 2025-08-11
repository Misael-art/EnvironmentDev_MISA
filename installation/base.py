"""
Base classes for installation components.
"""

from abc import ABC
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import hashlib
import time
import threading
from pathlib import Path

from ..core.base import SystemComponentBase, OperationResult
from ..core.exceptions import RobustDownloadError, AdvancedInstallationError
from .interfaces import (
    DownloadManagerInterface,
    InstallationManagerInterface,
    IntelligentPreparationInterface,
    RollbackManagerInterface,
    DownloadStatus,
    InstallationStatus,
    MirrorHealth,
    DownloadResult,
    InstallationResult,
    RollbackInfo
)


class InstallationBase(SystemComponentBase, ABC):
    """
    Base class for all installation components.
    
    Provides common functionality for download management,
    installation operations, and rollback handling.
    """
    
    def __init__(self, config_manager, component_name: Optional[str] = None):
        """Initialize installation base component."""
        super().__init__(config_manager, component_name)
        self._download_cache: Dict[str, Any] = {}
        self._installation_history: List[InstallationResult] = []
        self._active_downloads: Dict[str, threading.Thread] = {}
        self._rollback_points: Dict[str, RollbackInfo] = {}
        self._mirror_health_cache: Dict[str, Any] = {}
    
    def validate_configuration(self) -> None:
        """Validate installation-specific configuration."""
        config = self.get_config()
        
        # Validate installation-specific settings
        if not hasattr(config, 'download_timeout'):
            raise RobustDownloadError(
                "Missing download_timeout configuration",
                context={"component": self._component_name}
            )
        
        if not hasattr(config, 'automatic_rollback_enabled'):
            raise AdvancedInstallationError(
                "Missing automatic_rollback_enabled configuration",
                context={"component": self._component_name}
            )
        
        if not hasattr(config, 'hash_verification_required'):
            raise RobustDownloadError(
                "Missing hash_verification_required configuration",
                context={"component": self._component_name}
            )
    
    def _calculate_sha256(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: SHA256 hash in hexadecimal
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise RobustDownloadError(
                f"Failed to calculate SHA256 hash for {file_path}: {str(e)}",
                context={"file_path": file_path}
            ) from e
    
    def _verify_file_integrity(
        self, 
        file_path: str, 
        expected_hash: str
    ) -> bool:
        """
        Verify file integrity using SHA256 hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash
            
        Returns:
            bool: True if hash matches, False otherwise
        """
        if not self.get_config().hash_verification_required:
            self._logger.warning("Hash verification is disabled")
            return True
        
        try:
            actual_hash = self._calculate_sha256(file_path)
            matches = actual_hash.lower() == expected_hash.lower()
            
            if not matches:
                self._logger.error(
                    f"Hash verification failed for {file_path}. "
                    f"Expected: {expected_hash}, Actual: {actual_hash}"
                )
            
            return matches
            
        except Exception as e:
            self._logger.error(f"Hash verification error: {str(e)}")
            return False
    
    def _calculate_exponential_backoff(self, attempt: int, base_delay: int = 1) -> int:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            
        Returns:
            int: Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        # Cap at maximum delay to prevent excessive waits
        max_delay = 60  # Maximum 60 seconds
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)
    
    def _check_mirror_health(self, mirror_url: str) -> MirrorHealth:
        """
        Check health of a download mirror.
        
        Args:
            mirror_url: URL of mirror to check
            
        Returns:
            MirrorHealth: Health status of mirror
        """
        # Check cache first
        cache_key = f"mirror_health_{mirror_url}"
        cached_result = self._mirror_health_cache.get(cache_key)
        
        if cached_result:
            cache_age = (datetime.now() - cached_result["timestamp"]).total_seconds()
            if cache_age < 300:  # 5 minutes cache
                return cached_result["health"]
        
        # Perform health check (simplified implementation)
        try:
            import requests
            response = requests.head(mirror_url, timeout=10)
            
            if response.status_code == 200:
                health = MirrorHealth.HEALTHY
            elif response.status_code < 500:
                health = MirrorHealth.DEGRADED
            else:
                health = MirrorHealth.UNHEALTHY
                
        except Exception:
            health = MirrorHealth.UNHEALTHY
        
        # Cache result
        self._mirror_health_cache[cache_key] = {
            "health": health,
            "timestamp": datetime.now()
        }
        
        return health
    
    def _select_best_mirror(self, mirrors: List[str]) -> Optional[str]:
        """
        Select best mirror based on health and performance.
        
        Args:
            mirrors: List of mirror URLs
            
        Returns:
            Optional[str]: Best mirror URL or None if none available
        """
        if not mirrors:
            return None
        
        # Check health of all mirrors
        mirror_health = {}
        for mirror in mirrors:
            mirror_health[mirror] = self._check_mirror_health(mirror)
        
        # Prioritize healthy mirrors
        healthy_mirrors = [
            mirror for mirror, health in mirror_health.items()
            if health == MirrorHealth.HEALTHY
        ]
        
        if healthy_mirrors:
            return healthy_mirrors[0]  # Return first healthy mirror
        
        # Fall back to degraded mirrors
        degraded_mirrors = [
            mirror for mirror, health in mirror_health.items()
            if health == MirrorHealth.DEGRADED
        ]
        
        if degraded_mirrors:
            return degraded_mirrors[0]
        
        # Last resort: return first mirror even if unhealthy
        return mirrors[0]
    
    def _create_backup_directory(self, component: str) -> str:
        """
        Create backup directory for component.
        
        Args:
            component: Component name
            
        Returns:
            str: Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.get_config().backups_directory) / f"{component}_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir)
    
    def _backup_file_or_directory(self, source_path: str, backup_dir: str) -> str:
        """
        Backup file or directory to backup location.
        
        Args:
            source_path: Path to source file or directory
            backup_dir: Backup directory path
            
        Returns:
            str: Path to backup location
        """
        import shutil
        
        source = Path(source_path)
        if not source.exists():
            return ""
        
        backup_path = Path(backup_dir) / source.name
        
        try:
            if source.is_file():
                shutil.copy2(source, backup_path)
            elif source.is_dir():
                shutil.copytree(source, backup_path, dirs_exist_ok=True)
            
            return str(backup_path)
            
        except Exception as e:
            self._logger.warning(f"Failed to backup {source_path}: {str(e)}")
            return ""
    
    def _restore_from_backup(self, backup_path: str, restore_path: str) -> bool:
        """
        Restore file or directory from backup.
        
        Args:
            backup_path: Path to backup
            restore_path: Path to restore to
            
        Returns:
            bool: True if successful, False otherwise
        """
        import shutil
        
        try:
            backup = Path(backup_path)
            restore = Path(restore_path)
            
            if not backup.exists():
                return False
            
            # Remove existing file/directory if it exists
            if restore.exists():
                if restore.is_file():
                    restore.unlink()
                elif restore.is_dir():
                    shutil.rmtree(restore)
            
            # Restore from backup
            if backup.is_file():
                shutil.copy2(backup, restore)
            elif backup.is_dir():
                shutil.copytree(backup, restore)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to restore from backup {backup_path}: {str(e)}")
            return False
    
    def _execute_command_with_timeout(
        self, 
        command: List[str], 
        timeout: int = 300
    ) -> tuple[bool, str, str]:
        """
        Execute command with timeout.
        
        Args:
            command: Command to execute as list of strings
            timeout: Timeout in seconds
            
        Returns:
            tuple: (success, stdout, stderr)
        """
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def _update_installation_status(
        self, 
        component: str, 
        status: InstallationStatus,
        progress: float = 0.0,
        message: str = ""
    ) -> None:
        """
        Update installation status for tracking.
        
        Args:
            component: Component name
            status: Installation status
            progress: Progress percentage (0.0 to 100.0)
            message: Status message
        """
        status_info = {
            "component": component,
            "status": status.value,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self._logger.info(f"Installation status update: {status_info}")
        
        # Store status for monitoring (could be extended to use callbacks)
        # This is a placeholder for status tracking implementation
    
    def get_installation_history(self) -> List[Dict[str, Any]]:
        """Get installation history."""
        return [
            {
                "component": result.component_name,
                "version": result.version,
                "success": result.success,
                "installation_time": result.installation_time,
                "error_message": result.error_message,
            }
            for result in self._installation_history
        ]
    
    def get_active_downloads(self) -> List[str]:
        """Get list of active download component names."""
        return list(self._active_downloads.keys())
    
    def get_rollback_points(self) -> List[str]:
        """Get list of available rollback points."""
        return list(self._rollback_points.keys())
    
    def clear_installation_cache(self) -> None:
        """Clear installation-related caches."""
        self._download_cache.clear()
        self._mirror_health_cache.clear()
        self._logger.info("Installation cache cleared")