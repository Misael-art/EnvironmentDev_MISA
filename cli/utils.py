#!/usr/bin/env python3
"""
CLI Utilities module for Environment Dev Deep Evaluation.

Provides utility functions, helpers, and common operations
for the command-line interface.
"""

import os
import sys
import shutil
import subprocess
import hashlib
import requests
import time
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint
import yaml
import json
from datetime import datetime
import tempfile
import zipfile
import tarfile

console = Console()


class SystemInfo:
    """System information and detection utilities."""
    
    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """Get operating system information.
        
        Returns:
            Dict[str, str]: OS information dictionary
        """
        import platform
        
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0]
        }
    
    @staticmethod
    def get_python_info() -> Dict[str, str]:
        """Get Python interpreter information.
        
        Returns:
            Dict[str, str]: Python information dictionary
        """
        return {
            'version': sys.version.split()[0],
            'executable': sys.executable,
            'platform': sys.platform,
            'prefix': sys.prefix,
            'path': str(Path(sys.executable).parent)
        }
    
    @staticmethod
    def check_command_available(command: str) -> bool:
        """Check if a command is available in the system PATH.
        
        Args:
            command: Command name to check
            
        Returns:
            bool: True if command is available
        """
        return shutil.which(command) is not None
    
    @staticmethod
    def get_environment_variables() -> Dict[str, str]:
        """Get relevant environment variables.
        
        Returns:
            Dict[str, str]: Environment variables dictionary
        """
        relevant_vars = [
            'PATH', 'PYTHONPATH', 'HOME', 'USER', 'USERNAME',
            'TEMP', 'TMP', 'APPDATA', 'LOCALAPPDATA',
            'PROGRAMFILES', 'PROGRAMFILES(X86)', 'SYSTEMROOT'
        ]
        
        env_vars = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value
        
        return env_vars


class FileOperations:
    """File and directory operation utilities."""
    
    @staticmethod
    def ensure_directory(path: Path) -> bool:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to create directory {path}: {e}[/red]")
            return False
    
    @staticmethod
    def safe_remove(path: Path) -> bool:
        """Safely remove a file or directory.
        
        Args:
            path: Path to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remove {path}: {e}[/red]")
            return False
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
        """Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use
            
        Returns:
            Optional[str]: File hash or None if failed
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        except Exception as e:
            console.print(f"[red]❌ Failed to calculate hash for {file_path}: {e}[/red]")
            return None
    
    @staticmethod
    def get_file_size(file_path: Path) -> Optional[int]:
        """Get file size in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[int]: File size in bytes or None if failed
        """
        try:
            return file_path.stat().st_size
        except Exception:
            return None
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class NetworkOperations:
    """Operações de rede com segurança RF005.

    - Download com verificação obrigatória de SHA256
    - Suporte a file://, HEAD best-effort, limites de tamanho e retries exponenciais
    - Retorna OperationResult(success, errors, data)
    """

    @staticmethod
    def _exponential_backoff(attempt: int, base_seconds: float = 1.0, max_seconds: float = 30.0) -> float:
        delay = min(max_seconds, base_seconds * (2 ** attempt))
        jitter = min(0.25 * delay, 1.0)
        return delay + (jitter * 0.5)

    @staticmethod
    def verify_sha256(file_path: Path, expected_hash: str) -> "OperationResult":
        from core.base import OperationResult
        try:
            actual_hash = FileOperations.calculate_file_hash(file_path)
            if not actual_hash:
                return OperationResult(
                    success=False,
                    message="Falha ao calcular SHA256",
                    data={"file": str(file_path)},
                    errors=["Não foi possível calcular o hash do arquivo"]
                )
            if actual_hash.lower() != expected_hash.lower():
                return OperationResult(
                    success=False,
                    message="Mismatch de SHA256",
                    data={"file": str(file_path), "expected": expected_hash, "actual": actual_hash},
                    errors=["Verificação de integridade falhou: SHA256 divergente"]
                )
            return OperationResult(
                success=True,
                message="SHA256 verificado com sucesso",
                data={"file": str(file_path), "sha256": actual_hash},
                errors=[]
            )
        except Exception as exc:
            return OperationResult(
                success=False,
                message="Erro ao verificar SHA256",
                data={"file": str(file_path)},
                errors=[str(exc)]
            )

    @staticmethod
    def download_with_hash(
        url: str,
        destination: Path,
        expected_sha256: str,
        timeout: int = 300,
        max_retries: int = 3,
        max_size_mb: Optional[int] = None,
        show_progress: bool = True
    ) -> "OperationResult":
        from core.base import OperationResult
        try:
            FileOperations.ensure_directory(destination.parent)

            parsed = urlparse(url)
            if parsed.scheme.lower() == "file":
                local_path = Path(parsed.path)
                if not local_path.exists() or not local_path.is_file():
                    return OperationResult(False, "Arquivo local não encontrado", {"url": url}, [f"file:// inválido ou inexistente: {local_path}"])
                if max_size_mb is not None:
                    size_mb = local_path.stat().st_size / (1024 * 1024)
                    if size_mb > max_size_mb:
                        return OperationResult(False, "Arquivo local excede limite", {"url": url, "size_mb": f"{size_mb:.1f}", "limit_mb": max_size_mb}, ["Arquivo maior que o limite permitido"]) 
                try:
                    with open(local_path, "rb") as src, open(destination, "wb") as dst:
                        for chunk in iter(lambda: src.read(1024 * 1024), b""):
                            dst.write(chunk)
                except Exception as io_err:
                    return OperationResult(False, "Falha ao copiar arquivo local", {"url": url}, [str(io_err)])
                return NetworkOperations.verify_sha256(destination, expected_sha256)

            # HEAD best-effort
            try:
                head = requests.head(url, allow_redirects=True, timeout=timeout)
                if head.ok and max_size_mb is not None:
                    cl = head.headers.get("content-length")
                    if cl and (int(cl) / (1024 * 1024)) > max_size_mb:
                        return OperationResult(False, "Arquivo remoto excede limite", {"url": url, "size_mb": f"{int(cl)/(1024*1024):.1f}", "limit_mb": max_size_mb}, ["Tamanho reportado pelo servidor excede limite"])
            except Exception:
                pass

            attempt = 0
            while attempt <= max_retries:
                try:
                    with requests.get(url, stream=True, timeout=timeout) as resp:
                        resp.raise_for_status()
                        total_size = int(resp.headers.get("content-length", 0))
                        if max_size_mb is not None and total_size and (total_size / (1024 * 1024)) > max_size_mb:
                            return OperationResult(False, "Arquivo remoto excede limite", {"url": url, "size_mb": f"{total_size/(1024*1024):.1f}", "limit_mb": max_size_mb}, ["Tamanho reportado pelo servidor excede limite"])

                        hasher = hashlib.sha256()
                        written = 0
                        if show_progress and total_size:
                            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), DownloadColumn(), TransferSpeedColumn(), console=console) as progress:
                                task = progress.add_task(f"Downloading {destination.name}...", total=total_size)
                                with open(destination, "wb") as f:
                                    for chunk in resp.iter_content(chunk_size=1024 * 64):
                                        if not chunk:
                                            continue
                                        f.write(chunk)
                                        hasher.update(chunk)
                                        written += len(chunk)
                                        progress.advance(task, len(chunk))
                        else:
                            with open(destination, "wb") as f:
                                for chunk in resp.iter_content(chunk_size=1024 * 64):
                                    if not chunk:
                                        continue
                                    f.write(chunk)
                                    hasher.update(chunk)
                                    written += len(chunk)

                    if max_size_mb is not None and (written / (1024 * 1024)) > max_size_mb:
                        FileOperations.safe_remove(destination)
                        return OperationResult(False, "Download excedeu limite de tamanho", {"url": url, "written_mb": f"{written/(1024*1024):.1f}", "limit_mb": max_size_mb}, ["Arquivo maior que o limite permitido"]) 

                    actual = hasher.hexdigest()
                    if actual.lower() != expected_sha256.lower():
                        FileOperations.safe_remove(destination)
                        return OperationResult(False, "Verificação de SHA256 falhou", {"expected": expected_sha256, "actual": actual, "url": url}, ["Integridade inválida: SHA256 divergente"]) 

                    return OperationResult(True, "Download concluído e verificado", {"url": url, "file": str(destination), "sha256": actual, "bytes": written}, [])

                except requests.exceptions.RequestException as net_err:
                    if attempt >= max_retries:
                        if destination.exists():
                            FileOperations.safe_remove(destination)
                        return OperationResult(False, "Falha de rede ao baixar artefato", {"url": url, "attempts": attempt + 1}, [str(net_err)])
                    time.sleep(NetworkOperations._exponential_backoff(attempt))
                    attempt += 1
                except Exception as exc:
                    if destination.exists():
                        FileOperations.safe_remove(destination)
                    return OperationResult(False, "Erro inesperado durante download", {"url": url}, [str(exc)])

        except Exception as e:
            if destination.exists():
                FileOperations.safe_remove(destination)
            from core.base import OperationResult
            return OperationResult(False, "Erro geral de download", {"url": url}, [str(e)])

    @staticmethod
    def download_with_fallback(
        primary_url: str,
        alternative_urls: Optional[List[str]],
        destination: Path,
        expected_sha256: str,
        timeout: int = 300,
        max_retries: int = 3,
        max_size_mb: Optional[int] = None,
        show_progress: bool = True
    ) -> "OperationResult":
        from core.base import OperationResult
        urls: List[str] = [primary_url] + (alternative_urls or [])
        errors: List[str] = []
        for u in urls:
            res = NetworkOperations.download_with_hash(
                url=u,
                destination=destination,
                expected_sha256=expected_sha256,
                timeout=timeout,
                max_retries=max_retries,
                max_size_mb=max_size_mb,
                show_progress=show_progress
            )
            if res.success:
                return res
            errors.extend(res.errors or [res.message])
            if destination.exists():
                FileOperations.safe_remove(destination)
        return OperationResult(False, "Falha ao baixar de todas as URLs", {"destination": str(destination)}, errors)

    @staticmethod
    def check_url_accessible(url: str, timeout: int = 10) -> bool:
        try:
            r = requests.head(url, timeout=timeout)
            return r.ok
        except Exception:
            return False


class ArchiveOperations:
    """Archive extraction and manipulation utilities."""
    
    @staticmethod
    def extract_archive(archive_path: Path, destination: Path) -> bool:
        """Extract an archive file to a destination directory.
        
        Args:
            archive_path: Path to the archive file
            destination: Directory to extract to
            
        Returns:
            bool: True if extraction was successful
        """
        try:
            FileOperations.ensure_directory(destination)
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(destination)
            
            elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(destination)
            
            else:
                console.print(f"[red]❌ Unsupported archive format: {archive_path.suffix}[/red]")
                return False
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Archive extraction failed: {e}[/red]")
            return False
    
    @staticmethod
    def list_archive_contents(archive_path: Path) -> List[str]:
        """List contents of an archive file.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            List[str]: List of file paths in the archive
        """
        try:
            contents = []
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    contents = zip_ref.namelist()
            
            elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    contents = tar_ref.getnames()
            
            return contents
            
        except Exception as e:
            console.print(f"[red]❌ Failed to list archive contents: {e}[/red]")
            return []


class ProcessOperations:
    """Process execution and management utilities."""
    
    @staticmethod
    def run_command(
        command: List[str], 
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        show_output: bool = False
    ) -> Tuple[bool, str, str]:
        """Run a command and return the result.
        
        Args:
            command: Command and arguments as a list
            cwd: Working directory for the command
            capture_output: Whether to capture stdout/stderr
            show_output: Whether to show output in real-time
            
        Returns:
            Tuple[bool, str, str]: (success, stdout, stderr)
        """
        try:
            if show_output:
                # Run with real-time output
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                output_lines = []
                for line in process.stdout:
                    line = line.rstrip()
                    console.print(f"[dim]{line}[/dim]")
                    output_lines.append(line)
                
                process.wait()
                stdout = '\n'.join(output_lines)
                stderr = ''
                
            else:
                # Run with captured output
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                stdout = result.stdout if capture_output else ''
                stderr = result.stderr if capture_output else ''
                process = result
            
            return process.returncode == 0, stdout, stderr
            
        except subprocess.TimeoutExpired:
            console.print(f"[red]❌ Command timed out: {' '.join(command)}[/red]")
            return False, '', 'Command timed out'
        except Exception as e:
            console.print(f"[red]❌ Command failed: {e}[/red]")
            return False, '', str(e)
    
    @staticmethod
    def find_executable(name: str) -> Optional[Path]:
        """Find the path to an executable.
        
        Args:
            name: Executable name
            
        Returns:
            Optional[Path]: Path to executable or None if not found
        """
        path = shutil.which(name)
        return Path(path) if path else None


class ConfigurationHelpers:
    """Configuration and settings helper utilities."""
    
    @staticmethod
    def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Optional[Dict[str, Any]]: Parsed YAML data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            console.print(f"[red]❌ Failed to load YAML file {file_path}: {e}[/red]")
            return None
    
    @staticmethod
    def save_yaml_file(data: Dict[str, Any], file_path: Path) -> bool:
        """Save data to a YAML file.
        
        Args:
            data: Data to save
            file_path: Path to save to
            
        Returns:
            bool: True if saved successfully
        """
        try:
            FileOperations.ensure_directory(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to save YAML file {file_path}: {e}[/red]")
            return False
    
    @staticmethod
    def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]❌ Failed to load JSON file {file_path}: {e}[/red]")
            return None
    
    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: Path) -> bool:
        """Save data to a JSON file.
        
        Args:
            data: Data to save
            file_path: Path to save to
            
        Returns:
            bool: True if saved successfully
        """
        try:
            FileOperations.ensure_directory(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to save JSON file {file_path}: {e}[/red]")
            return False


class ValidationHelpers:
    """Validation and verification helper utilities."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if a string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            bool: True if URL is valid
        """
        import re
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_hash(hash_string: str, algorithm: str = 'sha256') -> bool:
        """Validate if a string is a valid hash.
        
        Args:
            hash_string: Hash string to validate
            algorithm: Hash algorithm
            
        Returns:
            bool: True if hash is valid format
        """
        expected_lengths = {
            'md5': 32,
            'sha1': 40,
            'sha256': 64,
            'sha512': 128
        }
        
        expected_length = expected_lengths.get(algorithm.lower())
        if not expected_length:
            return False
        
        return (
            len(hash_string) == expected_length and
            all(c in '0123456789abcdefABCDEF' for c in hash_string)
        )
    
    @staticmethod
    def validate_version(version: str) -> bool:
        """Validate if a string is a valid version number.
        
        Args:
            version: Version string to validate
            
        Returns:
            bool: True if version is valid
        """
        import re
        
        # Semantic versioning pattern
        version_pattern = re.compile(
            r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
            r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
            r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
        )
        
        return bool(version_pattern.match(version))


class DisplayHelpers:
    """Display and formatting helper utilities."""
    
    @staticmethod
    def create_status_table(items: List[Dict[str, Any]], title: str = "Status") -> Table:
        """Create a status table for display.
        
        Args:
            items: List of items with status information
            title: Table title
            
        Returns:
            Table: Rich table object
        """
        table = Table(title=title)
        table.add_column("Item", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        for item in items:
            status_icon = "✅" if item.get('success', False) else "❌"
            status_text = f"{status_icon} {item.get('status', 'Unknown')}"
            
            table.add_row(
                item.get('name', 'Unknown'),
                status_text,
                item.get('details', '')
            )
        
        return table
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            str: Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text to a maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


class TemporaryOperations:
    """Temporary file and directory operations."""
    
    @staticmethod
    def create_temp_directory() -> Path:
        """Create a temporary directory.
        
        Returns:
            Path: Path to the temporary directory
        """
        return Path(tempfile.mkdtemp())
    
    @staticmethod
    def create_temp_file(suffix: str = '') -> Path:
        """Create a temporary file.
        
        Args:
            suffix: File suffix
            
        Returns:
            Path: Path to the temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)  # Close the file descriptor
        return Path(path)