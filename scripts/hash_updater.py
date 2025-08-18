#!/usr/bin/env python3
"""Hash Updater Script for Environment Dev Deep Evaluation.

This script automatically downloads files and updates pending hashes in YAML component files.
It supports both HASH_NEEDS_UPDATE and HASH_PENDENTE_VERIFICACAO placeholders.
"""

import os
import sys
import yaml
import hashlib
import requests
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import tempfile
import shutil
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import ConfigurationManager
from core.base import SystemComponentBase, OperationResult
from core.exceptions import ValidationError, ComponentError


class HashUpdater(SystemComponentBase):
    """Component for updating pending hashes in YAML files."""
    
    PENDING_HASH_MARKERS = [
        "HASH_NEEDS_UPDATE",
        "HASH_PENDENTE_VERIFICACAO"
    ]
    # Optional per-component download size overrides (in MB)
    COMPONENT_SIZE_LIMITS: Dict[str, int] = {
        "Docker Desktop": 1500,
        "NVIDIA Game Ready Driver": 900,
    }
    
    def __init__(self, config_manager: ConfigurationManager):
        """Initialize the hash updater.
        
        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self._config_manager = config_manager
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        })
        
        # Statistics tracking
        self._stats = {
            'files_processed': 0,
            'hashes_updated': 0,
            'download_errors': 0,
            'hash_calculation_errors': 0,
            'yaml_update_errors': 0
        }
    
    def validate_configuration(self) -> None:
        """Validate configuration required by HashUpdater.
        Ensures download timeout is positive.
        """
        errors: List[str] = []
        try:
            if getattr(self._config, 'download_timeout', 0) <= 0:
                errors.append("download_timeout must be positive")
        except Exception:
            errors.append("download_timeout not available in configuration")

        if errors:
            raise ValidationError(
                f"Invalid configuration: {'; '.join(errors)}",
                context={"component": "HashUpdater", "validation_errors": errors}
            )

    def initialize(self) -> OperationResult:
        """Initialize the hash updater component."""
        try:
            self._logger.info("Initializing Hash Updater")
            
            # Validate configuration
            self.validate_configuration()
            
            # Setup session with timeouts
            self._session.timeout = self._config.download_timeout
            
            self._logger.info("Hash Updater initialized successfully")
            return OperationResult(
                success=True,
                message="Hash Updater initialized",
                data={'component': 'HashUpdater'},
                errors=[]
            )
            
        except Exception as e:
            self._logger.error(f"Initialization error: {e}")
            return OperationResult(
                success=False,
                message="Failed to initialize Hash Updater",
                data=None,
                errors=[str(e)]
            )
    
    def cleanup(self) -> OperationResult:
        """Cleanup the hash updater component."""
        try:
            self._logger.info("Cleaning up Hash Updater")
            
            if self._session:
                self._session.close()
            
            self._logger.info("Hash Updater cleaned up successfully")
            return OperationResult(
                success=True,
                message="Hash Updater cleaned up",
                data=None,
                errors=[]
            )
            
        except Exception as e:
            self._logger.error(f"Cleanup error: {e}")
            return OperationResult(
                success=False,
                message="Failed to cleanup Hash Updater",
                data=None,
                errors=[str(e)]
            )
    
    def find_yaml_files(self, components_dir: Path) -> List[Path]:
        """Find all YAML files in the components directory.
        
        Args:
            components_dir: Path to components directory
            
        Returns:
            List of YAML file paths
        """
        yaml_files = []
        
        if not components_dir.exists():
            self._logger.warning(f"Components directory not found: {components_dir}")
            return yaml_files
        
        for file_path in components_dir.glob("*.yaml"):
            # Skip backup files
            if file_path.name.endswith('.backup'):
                continue
            yaml_files.append(file_path)
        
        self._logger.info(f"Found {len(yaml_files)} YAML files to process")
        return yaml_files
    
    def load_yaml_file(self, file_path: Path) -> Tuple[Optional[Dict], Optional[str]]:
        """Load and parse a YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (parsed_data, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data, None
            
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error in {file_path}: {e}"
            self._logger.error(error_msg)
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Error loading {file_path}: {e}"
            self._logger.error(error_msg)
            return None, error_msg
    
    def save_yaml_file(self, file_path: Path, data: Dict) -> bool:
        """Save data to a YAML file.
        
        Args:
            file_path: Path to YAML file
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                self._logger.debug(f"Created backup: {backup_path}")
            
            # Save updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self._logger.info(f"Updated YAML file: {file_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error saving {file_path}: {e}")
            self._stats['yaml_update_errors'] += 1
            return False
    
    def download_file(self, url: str, max_size_mb: int = 500) -> Tuple[Optional[bytes], Optional[str]]:
        """Download a file from URL.
        
        Args:
            url: URL to download
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (file_content, error_message)
        """
        try:
            self._logger.info(f"Downloading: {url}")
            # Local file support (file://)
            if url.lower().startswith("file://"):
                try:
                    local_path = url[7:]
                    path = Path(local_path)
                    if not path.exists() or not path.is_file():
                        return None, f"Local file not found: {local_path}"
                    if path.stat().st_size > max_size_mb * 1024 * 1024:
                        return None, f"File too large: {path.stat().st_size/(1024*1024):.1f}MB > {max_size_mb}MB"
                    content = path.read_bytes()
                    self._logger.info(f"Loaded local file {local_path} ({len(content)} bytes)")
                    return content, None
                except Exception as e:
                    return None, f"Error reading local file: {e}"
            
            # Head request to check file size (best-effort). If it fails, we proceed with guarded GET.
            head_response = None
            try:
                head_response = self._session.head(
                    url, allow_redirects=True, timeout=getattr(self._config, 'download_timeout', 60)
                )
            except Exception as e:
                self._logger.debug(f"HEAD request exception for {url}: {e}")
            
            if head_response is not None and getattr(head_response, 'status_code', 0) == 200:
                content_length = head_response.headers.get('content-length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        return None, f"File too large: {size_mb:.1f}MB > {max_size_mb}MB"
            else:
                self._logger.debug(f"HEAD not usable for {url}; proceeding with guarded GET")
            
            # Download file
            response = self._session.get(
                url, stream=True, timeout=getattr(self._config, 'download_timeout', 60)
            )
            response.raise_for_status()

            # Validate content-type to avoid hashing páginas HTML indevidas
            ctype = (response.headers.get('content-type') or '').lower()
            # Tipos binários comuns aceitos
            allowed_types = [
                'application/octet-stream',
                'application/x-msdownload',
                'application/zip',
                'application/x-zip-compressed',
                'application/x-7z-compressed',
                'application/vnd.microsoft.portable-executable',
                'application/x-msi',
                'application/x-wheel+zip',
            ]
            # Heurística: se for texto/html/markdown/xml/json e URL não aponta explicitamente para artefato,
            # rejeitar para não gravar hash incorreto (RF005)
            textual_types = ['text/', 'application/json', 'application/xml', 'text/html', 'text/plain']
            url_lc = url.lower()
            looks_like_artifact = any(url_lc.endswith(ext) for ext in (
                '.exe', '.msi', '.zip', '.7z', '.whl'
            ))
            if any(ctype.startswith(t) for t in textual_types) and not looks_like_artifact:
                return None, f"Non-binary content-type '{ctype}' for URL (likely HTML page): {url}"
            
            content = b''
            downloaded_size = 0
            max_size_bytes = max_size_mb * 1024 * 1024
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    downloaded_size += len(chunk)
                    
                    if downloaded_size > max_size_bytes:
                        return None, f"Download exceeded size limit: {max_size_mb}MB"
            
            self._logger.info(f"Downloaded {len(content)} bytes from {url}")
            return content, None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Download error for {url}: {e}"
            self._logger.error(error_msg)
            self._stats['download_errors'] += 1
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error downloading {url}: {e}"
            self._logger.error(error_msg)
            self._stats['download_errors'] += 1
            return None, error_msg
    
    def calculate_sha256(self, content: bytes) -> str:
        """Calculate SHA256 hash of content.
        
        Args:
            content: File content as bytes
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        try:
            sha256_hash = hashlib.sha256()
            sha256_hash.update(content)
            return sha256_hash.hexdigest()
            
        except Exception as e:
            self._logger.error(f"Error calculating SHA256: {e}")
            self._stats['hash_calculation_errors'] += 1
            raise
    
    def find_pending_hashes(self, data: Dict) -> List[Tuple[str, str, str]]:
        """Find components with pending hashes.
        
        Args:
            data: Parsed YAML data
            
        Returns:
            List of tuples (component_name, download_url, current_hash)
        """
        pending_hashes = []
        
        if not isinstance(data, dict):
            return pending_hashes
        
        for component_name, component_data in data.items():
            if not isinstance(component_data, dict):
                continue
            
            current_hash = component_data.get('hash', '')
            download_url = component_data.get('download_url', '')
            
            if current_hash in self.PENDING_HASH_MARKERS and download_url:
                pending_hashes.append((component_name, download_url, current_hash))
        
        return pending_hashes
    
    def update_component_hash(self, data: Dict, component_name: str, new_hash: str) -> bool:
        """Update hash for a specific component.
        
        Args:
            data: YAML data dictionary
            component_name: Name of component to update
            new_hash: New hash value
            
        Returns:
            True if updated successfully
        """
        try:
            if component_name in data and isinstance(data[component_name], dict):
                old_hash = data[component_name].get('hash', '')
                data[component_name]['hash'] = new_hash
                
                self._logger.info(
                    f"Updated hash for {component_name}: {old_hash} -> {new_hash}"
                )
                self._stats['hashes_updated'] += 1
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error updating hash for {component_name}: {e}")
            return False
    
    def process_file(self, file_path: Path, dry_run: bool = False, max_size_mb: int = 500) -> OperationResult:
        """Process a single YAML file to update pending hashes.
        
        Args:
            file_path: Path to YAML file
            dry_run: If True, don't actually update files
            
        Returns:
            OperationResult with processing details
        """
        try:
            self._logger.info(f"Processing file: {file_path}")
            self._stats['files_processed'] += 1
            
            # Load YAML file
            data, error = self.load_yaml_file(file_path)
            if error:
                return OperationResult(
                    success=False,
                    message=f"Failed to load {file_path}",
                    data=None,
                    errors=[error]
                )
            
            # Find pending hashes
            pending_hashes = self.find_pending_hashes(data)
            if not pending_hashes:
                self._logger.debug(f"No pending hashes found in {file_path}")
                return OperationResult(
                    success=True,
                    message=f"No pending hashes in {file_path}",
                    data={'pending_count': 0},
                    errors=[]
                )
            
            self._logger.info(
                f"Found {len(pending_hashes)} pending hashes in {file_path}"
            )
            
            updated_count = 0
            errors = []
            
            # Process each pending hash
            for component_name, download_url, current_hash in pending_hashes:
                self._logger.info(
                    f"Processing {component_name}: {current_hash} -> downloading from {download_url}"
                )
                
                if dry_run:
                    self._logger.info(f"DRY RUN: Would download and update {component_name}")
                    updated_count += 1
                    continue
                
                # Determine effective size limit
                effective_limit = self.COMPONENT_SIZE_LIMITS.get(component_name, max_size_mb)
                if effective_limit != max_size_mb:
                    self._logger.info(
                        f"Using per-component size limit for {component_name}: {effective_limit}MB"
                    )
                # Download file
                content, download_error = self.download_file(download_url, max_size_mb=effective_limit)
                if download_error:
                    # Try alternative URLs if available
                    alt_urls = []
                    try:
                        comp_data = data.get(component_name, {})
                        alt_urls = comp_data.get('alternative_urls', []) or []
                    except Exception:
                        alt_urls = []

                    alt_success = False
                    for alt in alt_urls:
                        self._logger.info(f"Trying alternative URL for {component_name}: {alt}")
                        content, alt_err = self.download_file(alt, max_size_mb=effective_limit)
                        if not alt_err and content:
                            download_error = None
                            alt_success = True
                            break
                        else:
                            self._logger.warning(f"Alternative URL failed for {component_name}: {alt_err}")

                    if download_error and not alt_success:
                        error_msg = f"Failed to download {component_name}: {download_error}"
                        self._logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                
                # Calculate hash
                try:
                    new_hash = self.calculate_sha256(content)
                    self._logger.info(f"Calculated SHA256 for {component_name}: {new_hash}")
                    
                    # Update hash in data
                    if self.update_component_hash(data, component_name, new_hash):
                        updated_count += 1
                    else:
                        error_msg = f"Failed to update hash for {component_name}"
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Failed to calculate hash for {component_name}: {e}"
                    self._logger.error(error_msg)
                    errors.append(error_msg)
            
            # Save updated file if any hashes were updated
            if updated_count > 0 and not dry_run:
                if not self.save_yaml_file(file_path, data):
                    errors.append(f"Failed to save updated file: {file_path}")
            
            result_message = f"Processed {file_path}: {updated_count}/{len(pending_hashes)} hashes updated"
            if errors:
                result_message += f", {len(errors)} errors"
            
            return OperationResult(
                success=len(errors) == 0,
                message=result_message,
                data={
                    'file_path': str(file_path),
                    'pending_count': len(pending_hashes),
                    'updated_count': updated_count,
                    'errors': errors
                },
                errors=errors
            )
            
        except Exception as e:
            self._logger.error(f"Failed to process {file_path}: {e}")
            return OperationResult(
                success=False,
                message=f"Failed to process {file_path}",
                data={'file_path': str(file_path)},
                errors=[str(e)]
            )
    
    def process_all_files(self, components_dir: Path, dry_run: bool = False, max_size_mb: int = 500) -> OperationResult:
        """Process all YAML files in the components directory.
        
        Args:
            components_dir: Path to components directory
            dry_run: If True, don't actually update files
            
        Returns:
            OperationResult with overall processing results
        """
        try:
            self._logger.info(f"Starting hash update process for directory: {components_dir}")
            
            # Reset statistics
            self._stats = {
                'files_processed': 0,
                'hashes_updated': 0,
                'download_errors': 0,
                'hash_calculation_errors': 0,
                'yaml_update_errors': 0
            }
            
            # Find YAML files
            yaml_files = self.find_yaml_files(components_dir)
            if not yaml_files:
                return OperationResult(
                    success=True,
                    message="No YAML files found to process",
                    data=self._stats,
                    errors=[]
                )
            
            # Process each file
            all_errors = []
            successful_files = 0
            
            for file_path in yaml_files:
                result = self.process_file(file_path, dry_run, max_size_mb=max_size_mb)
                
                if result.success:
                    successful_files += 1
                else:
                    first_error = (result.errors[0] if hasattr(result, 'errors') and result.errors else 'unknown error')
                    all_errors.append(f"{file_path}: {first_error}")
            
            # Generate summary
            summary_message = (
                f"Hash update process completed. "
                f"Files: {successful_files}/{len(yaml_files)} successful, "
                f"Hashes updated: {self._stats['hashes_updated']}, "
                f"Errors: {len(all_errors)}"
            )
            
            if dry_run:
                summary_message = f"DRY RUN - {summary_message}"
            
            self._logger.info(summary_message)
            
            return OperationResult(
                success=len(all_errors) == 0,
                message=summary_message,
                data={
                    **self._stats,
                    'total_files': len(yaml_files),
                    'successful_files': successful_files,
                    'errors': all_errors
                },
                errors=all_errors
            )
            
        except Exception as e:
            self._logger.error(f"Failed to process all files: {e}")
            return OperationResult(
                success=False,
                message="Failed to process all files",
                data=None,
                errors=[str(e)]
            )
    
    def get_statistics(self) -> Dict:
        """Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return self._stats.copy()


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('hash_updater.log')
        ]
    )


def main():
    """Main entry point for the hash updater script."""
    parser = argparse.ArgumentParser(
        description="Update pending hashes in YAML component files"
    )
    parser.add_argument(
        "--components-dir",
        type=Path,
        default=Path("components"),
        help="Path to components directory (default: components)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=500,
        help="Maximum download size per file in MB (default: 500)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager(str(args.config) if args.config else None)
        
        # Initialize hash updater
        hash_updater = HashUpdater(config_manager)
        
        # Initialize component
        init_result = hash_updater.initialize()
        if not init_result.success:
            logger.error(f"Failed to initialize hash updater: {init_result.errors[0] if init_result.errors else 'unknown error'}")
            return 1
        
        # Process files
        result = hash_updater.process_all_files(args.components_dir, args.dry_run, max_size_mb=args.max_size_mb)
        
        # Print results
        print(f"\n{result.message}")
        if result.data:
            print(f"Statistics: {result.data}")
        
        if result.data and result.data.get('errors'):
            print("\nErrors encountered:")
            for error in result.data['errors']:
                print(f"  - {error}")
        
        # Cleanup
        cleanup_result = hash_updater.cleanup()
        if not cleanup_result.success:
            logger.warning(f"Cleanup warning: {cleanup_result.errors[0] if cleanup_result.errors else 'unknown error'}")
        
        return 0 if result.success else 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())