"""Pydantic schemas for YAML component validation.

This module defines Pydantic models for validating the structure and content
of YAML component files in the Environment Dev Deep Evaluation system.
"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
from pathlib import Path
import re
import os
from dataclasses import dataclass
import yaml


class InstallMethod(str, Enum):
    """Supported installation methods."""
    EXE = "exe"
    MSI = "msi"
    ZIP = "zip"
    PIP = "pip"
    NPM = "npm"
    CONDA = "conda"
    CHOCOLATEY = "chocolatey"
    WINGET = "winget"
    MANUAL = "manual"
    SCRIPT = "script"


class HashAlgorithm(str, Enum):
    """Supported hash algorithms."""
    SHA256 = "sha256"
    SHA1 = "sha1"
    MD5 = "md5"


class VerificationActionType(str, Enum):
    """Types of verification actions."""
    FILE_EXISTS = "file_exists"
    DIRECTORY_EXISTS = "directory_exists"
    COMMAND_EXISTS = "command_exists"
    ENV_VAR_EXISTS = "env_var_exists"
    REGISTRY_KEY_EXISTS = "registry_key_exists"
    SERVICE_RUNNING = "service_running"
    PORT_LISTENING = "port_listening"
    CUSTOM_SCRIPT = "custom_script"


class ComponentCategory(str, Enum):
    """Component categories."""
    AI_TOOLS = "AI Tools"
    BUILD_TOOLS = "Build Tools"
    COMPILERS = "Compilers"
    VERSION_CONTROL = "Version Control"
    EDITORS = "Editors"
    RUNTIMES = "Runtimes"
    CONTAINERS = "Containers"
    VIRTUALIZATION = "Virtualization"
    SYSTEM_TOOLS = "System Tools"
    NETWORK_TOOLS = "Network Tools"
    GAME_DEV = "Game Development"
    EMULATORS = "Emulators"
    COMMUNICATION = "Communication"
    PRODUCTIVITY = "Productivity"
    AUDIO_TOOLS = "Audio Tools"
    CAPTURE_STREAMING = "Capture & Streaming"
    BACKUP_SYNC = "Backup & Sync"
    OPTIMIZATION = "Optimization"
    MODDING_TOOLS = "Modding Tools"
    BOOT_MANAGERS = "Boot Managers"
    MISC = "Miscellaneous"


class VerificationAction(BaseModel):
    """Model for verification actions."""
    type: VerificationActionType = Field(..., description="Type of verification action")
    path: Optional[str] = Field(None, description="Path to verify (for file/directory checks)")
    name: Optional[str] = Field(None, description="Name to verify (for command/env var checks)")
    description: Optional[str] = Field(None, description="Description of the verification")
    script: Optional[str] = Field(None, description="Custom script for verification")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number for port checks")
    service_name: Optional[str] = Field(None, description="Service name for service checks")
    registry_path: Optional[str] = Field(None, description="Registry path for registry checks")
    
    @validator('path')
    def validate_path(cls, v, values):
        """Validate path field based on verification type."""
        action_type = values.get('type')
        if action_type in [VerificationActionType.FILE_EXISTS, VerificationActionType.DIRECTORY_EXISTS]:
            if not v:
                raise ValueError(f"Path is required for {action_type} verification")
        return v
    
    @validator('name')
    def validate_name(cls, v, values):
        """Validate name field based on verification type."""
        action_type = values.get('type')
        if action_type in [VerificationActionType.COMMAND_EXISTS, VerificationActionType.ENV_VAR_EXISTS]:
            if not v:
                raise ValueError(f"Name is required for {action_type} verification")
        return v
    
    @validator('script')
    def validate_script(cls, v, values):
        """Validate script field for custom script verification."""
        action_type = values.get('type')
        if action_type == VerificationActionType.CUSTOM_SCRIPT:
            if not v:
                raise ValueError("Script is required for custom_script verification")
        return v
    
    @validator('port')
    def validate_port(cls, v, values):
        """Validate port field for port listening verification."""
        action_type = values.get('type')
        if action_type == VerificationActionType.PORT_LISTENING:
            if not v:
                raise ValueError("Port is required for port_listening verification")
        return v


class ComponentModel(BaseModel):
    """Model for a single component definition."""
    category: ComponentCategory = Field(..., description="Component category")
    description: str = Field(..., min_length=1, max_length=500, description="Component description")
    download_url: Optional[str] = Field(None, description="Primary download URL")
    alternative_urls: Optional[List[str]] = Field(None, description="Alternative download URLs")
    install_method: InstallMethod = Field(..., description="Installation method")
    install_args: Optional[str] = Field(None, description="Installation arguments")
    hash: Optional[str] = Field(None, description="File hash for verification")
    hash_algorithm: Optional[HashAlgorithm] = Field(HashAlgorithm.SHA256, description="Hash algorithm")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="Component dependencies")
    verify_actions: Optional[List[VerificationAction]] = Field(default_factory=list, description="Verification actions")
    version: Optional[str] = Field(None, description="Component version")
    author: Optional[str] = Field(None, description="Component author/vendor")
    license: Optional[str] = Field(None, description="Component license")
    homepage: Optional[str] = Field(None, description="Component homepage URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    size_mb: Optional[float] = Field(None, ge=0, description="Download size in MB")
    install_time_minutes: Optional[int] = Field(None, ge=0, description="Estimated install time in minutes")
    requires_admin: Optional[bool] = Field(False, description="Requires administrator privileges")
    requires_reboot: Optional[bool] = Field(False, description="Requires system reboot")
    platform_specific: Optional[Dict[str, Any]] = Field(None, description="Platform-specific configurations")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Environment variables to set")
    post_install_scripts: Optional[List[str]] = Field(None, description="Post-installation scripts")
    uninstall_method: Optional[str] = Field(None, description="Uninstallation method")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('download_url')
    def validate_download_url(cls, v, values):
        """Validate download URL format."""
        if v:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(v):
                raise ValueError('Invalid URL format')
        return v
    
    @validator('alternative_urls')
    def validate_alternative_urls(cls, v):
        """Validate alternative URLs format."""
        if v:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?:\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            for url in v:
                if not url_pattern.match(url):
                    raise ValueError(f'Invalid alternative URL format: {url}')
        return v
    
    @validator('hash')
    def validate_hash(cls, v, values):
        """Validate hash format."""
        if v and v not in ['HASH_NEEDS_UPDATE', 'HASH_PENDENTE_VERIFICACAO']:
            hash_algorithm = values.get('hash_algorithm', HashAlgorithm.SHA256)
            
            if hash_algorithm == HashAlgorithm.SHA256:
                if not re.match(r'^[a-fA-F0-9]{64}$', v):
                    raise ValueError('Invalid SHA256 hash format (must be 64 hex characters)')
            elif hash_algorithm == HashAlgorithm.SHA1:
                if not re.match(r'^[a-fA-F0-9]{40}$', v):
                    raise ValueError('Invalid SHA1 hash format (must be 40 hex characters)')
            elif hash_algorithm == HashAlgorithm.MD5:
                if not re.match(r'^[a-fA-F0-9]{32}$', v):
                    raise ValueError('Invalid MD5 hash format (must be 32 hex characters)')
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        if v:
            # Allow semantic versioning and other common formats
            version_pattern = re.compile(
                r'^(?P<major>0|[1-9]\d*)'
                r'(?:\.(?P<minor>0|[1-9]\d*))?'
                r'(?:\.(?P<patch>0|[1-9]\d*))?'
                r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
                r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
            )
            
            # Also allow simpler formats like "2023.09", "17.0.6", etc.
            simple_pattern = re.compile(r'^[0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9a-zA-Z-]*)?$')
            
            if not (version_pattern.match(v) or simple_pattern.match(v)):
                raise ValueError('Invalid version format')
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_install_requirements(cls, values):
        """Validate installation requirements based on install method."""
        install_method = values.get('install_method')
        download_url = values.get('download_url')
        install_args = values.get('install_args')
        
        # Methods that require download URL
        download_required_methods = [
            InstallMethod.EXE, InstallMethod.MSI, InstallMethod.ZIP
        ]
        
        if install_method in download_required_methods and not download_url:
            raise ValueError(f'download_url is required for {install_method} installation method')
        
        # Methods that require install args
        args_required_methods = [
            InstallMethod.PIP,
            InstallMethod.NPM,
            InstallMethod.CONDA,
        ]

        if install_method in args_required_methods and not install_args:
            raise ValueError(f'install_args is required for {install_method} installation method')

        return values


class ComponentsFile(BaseModel):
    """Model representing a components file (mapping of components)."""
    components: Dict[str, ComponentModel]

    @validator('components')
    def validate_components_dict(cls, v: Dict[str, ComponentModel]):
        if not v:
            raise ValueError('Components dictionary cannot be empty')

        name_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        for name in v.keys():
            if len(name) > 100:
                raise ValueError(f"Component name '{name}' is too long")
            if not name_pattern.match(name):
                raise ValueError(f"Component name '{name}' contains invalid characters")
        return v

    @root_validator(skip_on_failure=True)
    def validate_dependencies_and_cycles(cls, values: Dict[str, Any]):
        components: Dict[str, ComponentModel] = values.get('components', {})
        if not components:
            return values

        # Undefined dependencies
        for name, comp in components.items():
            for dep in comp.dependencies or []:
                if dep not in components:
                    raise ValueError(f"Component '{name}' has undefined dependency '{dep}'")

        # Cycle detection
        adjacency: Dict[str, List[str]] = {name: (comp.dependencies or []) for name, comp in components.items()}
        visited: Dict[str, int] = {name: 0 for name in components}  # 0=unvisited,1=visiting,2=done

        def dfs(node: str) -> bool:
            if visited[node] == 1:
                return True  # cycle
            if visited[node] == 2:
                return False
            visited[node] = 1
            for nxt in adjacency.get(node, []):
                if dfs(nxt):
                    return True
            visited[node] = 2
            return False

        for node in components:
            if visited[node] == 0 and dfs(node):
                raise ValueError('Circular dependency detected')

        return values


def load_components_from_yaml(file_path: str) -> ComponentsFile:
    """Load components from a YAML file into a ComponentsFile model.

    Raises:
        FileNotFoundError: if file does not exist
        yaml.YAMLError: if YAML cannot be parsed
        ValidationError: if content does not conform to schema
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError('Component file not found')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        # Re-raise as yaml.YAMLError with expected message
        raise yaml.YAMLError(f"Failed to parse YAML file: {e}")

    # Accept either top-level 'components' key or direct mapping
    if isinstance(data, dict) and 'components' in data and isinstance(data['components'], dict):
        comp_map = data['components']
    elif isinstance(data, dict):
        comp_map = data
    else:
        comp_map = {}

    return ComponentsFile(components=comp_map)


def validate_component_yaml(file_path: str) -> tuple[bool, List[str]]:
    """Validate a YAML file containing component definitions.

    Returns (is_valid, errors).
    """
    try:
        _ = load_components_from_yaml(file_path)
        return True, []
    except Exception as e:
        return False, [str(e)]


def get_component_dependencies(components_file: ComponentsFile, component_name: str) -> List[str]:
    """Return ordered list of dependency names for a given component (bottom-up)."""
    components = components_file.components
    if component_name not in components:
        raise ValueError(f"Component '{component_name}' not found")

    ordered: List[str] = []
    visited: Dict[str, bool] = {}

    def visit(name: str):
        for dep in components[name].dependencies or []:
            if dep not in visited:
                visit(dep)
                visited[dep] = True
                ordered.append(dep)

    visit(component_name)
    return ordered


def get_components_by_category(components_file: ComponentsFile, category: ComponentCategory) -> Dict[str, ComponentModel]:
    """Filter components by category."""
    return {name: comp for name, comp in components_file.components.items() if comp.category == category}


def validate_all_yaml_files(directory: str) -> Dict[str, tuple[bool, List[str]]]:
    """Validate all .yaml files in a directory. Ignores non-YAML files.

    Returns a mapping from file path to (is_valid, errors).
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return {}

    results: Dict[str, tuple[bool, List[str]]] = {}
    for file in path.iterdir():
        if file.is_file() and file.suffix.lower() in {'.yaml', '.yml'}:
            is_valid, errors = validate_component_yaml(str(file))
            results[str(file)] = (is_valid, errors)
    return results