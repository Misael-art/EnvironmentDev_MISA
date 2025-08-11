"""Tests for validation.schemas module."""

import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, mock_open

from pydantic import ValidationError

from validation.schemas import (
    InstallMethod,
    HashAlgorithm,
    VerificationActionType,
    ComponentCategory,
    VerificationAction,
    ComponentModel,
    ComponentsFile,
    load_components_from_yaml,
    validate_component_yaml,
    get_component_dependencies,
    get_components_by_category,
    validate_all_yaml_files
)


class TestVerificationAction:
    """Tests for VerificationAction model."""
    
    def test_file_exists_verification_valid(self):
        """Test valid file exists verification."""
        action = VerificationAction(
            type=VerificationActionType.FILE_EXISTS,
            path="/path/to/file.exe",
            description="Check if file exists"
        )
        assert action.type == VerificationActionType.FILE_EXISTS
        assert action.path == "/path/to/file.exe"
        assert action.description == "Check if file exists"
    
    def test_file_exists_verification_missing_path(self):
        """Test file exists verification without required path."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationAction(
                type=VerificationActionType.FILE_EXISTS,
                description="Check if file exists"
            )
        assert "Path is required for VerificationActionType.FILE_EXISTS verification" in str(exc_info.value)
    
    def test_command_exists_verification_valid(self):
        """Test valid command exists verification."""
        action = VerificationAction(
            type=VerificationActionType.COMMAND_EXISTS,
            name="python",
            description="Check if Python is available"
        )
        assert action.type == VerificationActionType.COMMAND_EXISTS
        assert action.name == "python"
    
    def test_command_exists_verification_missing_name(self):
        """Test command exists verification without required name."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationAction(
                type=VerificationActionType.COMMAND_EXISTS,
                description="Check if command exists"
            )
        assert "Name is required for VerificationActionType.COMMAND_EXISTS verification" in str(exc_info.value)
    
    def test_custom_script_verification_valid(self):
        """Test valid custom script verification."""
        action = VerificationAction(
            type=VerificationActionType.CUSTOM_SCRIPT,
            script="echo 'test'",
            description="Run custom script"
        )
        assert action.type == VerificationActionType.CUSTOM_SCRIPT
        assert action.script == "echo 'test'"
    
    def test_custom_script_verification_missing_script(self):
        """Test custom script verification without required script."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationAction(
                type=VerificationActionType.CUSTOM_SCRIPT,
                description="Run custom script"
            )
        assert "Script is required for VerificationActionType.CUSTOM_SCRIPT verification" in str(exc_info.value)
    
    def test_port_listening_verification_valid(self):
        """Test valid port listening verification."""
        action = VerificationAction(
            type=VerificationActionType.PORT_LISTENING,
            port=8080,
            description="Check if port is listening"
        )
        assert action.type == VerificationActionType.PORT_LISTENING
        assert action.port == 8080
    
    def test_port_listening_verification_missing_port(self):
        """Test port listening verification without required port."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationAction(
                type=VerificationActionType.PORT_LISTENING,
                description="Check if port is listening"
            )
        assert "Port is required for VerificationActionType.PORT_LISTENING verification" in str(exc_info.value)
    
    def test_port_validation_range(self):
        """Test port number validation range."""
        # Valid port
        action = VerificationAction(
            type=VerificationActionType.PORT_LISTENING,
            port=8080
        )
        assert action.port == 8080
        
        # Invalid port - too low
        with pytest.raises(ValidationError):
            VerificationAction(
                type=VerificationActionType.PORT_LISTENING,
                port=0
            )
        
        # Invalid port - too high
        with pytest.raises(ValidationError):
            VerificationAction(
                type=VerificationActionType.PORT_LISTENING,
                port=65536
            )


class TestComponentModel:
    """Tests for ComponentModel."""
    
    def test_valid_component_creation(self):
        """Test creating a valid component."""
        component = ComponentModel(
            category=ComponentCategory.AI_TOOLS,
            description="Test AI tool",
            download_url="https://example.com/download.exe",
            install_method=InstallMethod.EXE,
            hash="a" * 64,  # Valid SHA256 hash
            version="1.0.0"
        )
        assert component.category == ComponentCategory.AI_TOOLS
        assert component.description == "Test AI tool"
        assert component.download_url == "https://example.com/download.exe"
        assert component.install_method == InstallMethod.EXE
        assert component.hash == "a" * 64
        assert component.version == "1.0.0"
    
    def test_invalid_download_url(self):
        """Test component with invalid download URL."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                download_url="invalid-url",
                install_method=InstallMethod.EXE
            )
        assert "Invalid URL format" in str(exc_info.value)
    
    def test_invalid_alternative_urls(self):
        """Test component with invalid alternative URLs."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                download_url="https://example.com/download.exe",
                alternative_urls=["https://valid.com/file.exe", "invalid-url"],
                install_method=InstallMethod.EXE
            )
        assert "Invalid alternative URL format" in str(exc_info.value)
    
    def test_invalid_sha256_hash(self):
        """Test component with invalid SHA256 hash."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                download_url="https://example.com/download.exe",
                install_method=InstallMethod.EXE,
                hash="invalid-hash",
                hash_algorithm=HashAlgorithm.SHA256
            )
        assert "Invalid SHA256 hash format" in str(exc_info.value)
    
    def test_valid_pending_hash(self):
        """Test component with pending hash markers."""
        component = ComponentModel(
            category=ComponentCategory.AI_TOOLS,
            description="Test tool",
            download_url="https://example.com/download.exe",
            install_method=InstallMethod.EXE,
            hash="HASH_NEEDS_UPDATE"
        )
        assert component.hash == "HASH_NEEDS_UPDATE"
        
        component2 = ComponentModel(
            category=ComponentCategory.AI_TOOLS,
            description="Test tool",
            download_url="https://example.com/download.exe",
            install_method=InstallMethod.EXE,
            hash="HASH_PENDENTE_VERIFICACAO"
        )
        assert component2.hash == "HASH_PENDENTE_VERIFICACAO"
    
    def test_invalid_version_format(self):
        """Test component with invalid version format."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                download_url="https://example.com/download.exe",
                install_method=InstallMethod.EXE,
                version="invalid..version"
            )
        assert "Invalid version format" in str(exc_info.value)
    
    def test_valid_version_formats(self):
        """Test component with various valid version formats."""
        valid_versions = [
            "1.0.0",
            "2.1",
            "3",
            "1.0.0-alpha",
            "2.1.0-beta.1",
            "1.0.0+build.1",
            "2023.09",
            "17.0.6",
            "1.0a1"
        ]
        
        for version in valid_versions:
            component = ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                download_url="https://example.com/download.exe",
                install_method=InstallMethod.EXE,
                version=version
            )
            assert component.version == version
    
    def test_install_requirements_validation_exe_without_url(self):
        """Test EXE install method without download URL."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                install_method=InstallMethod.EXE
            )
        assert "download_url is required for InstallMethod.EXE installation method" in str(exc_info.value)
    
    def test_install_requirements_validation_pip_without_args(self):
        """Test PIP install method without install args."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Test tool",
                install_method=InstallMethod.PIP
            )
        assert "install_args is required for InstallMethod.PIP installation method" in str(exc_info.value)
    
    def test_valid_pip_component(self):
        """Test valid PIP component."""
        component = ComponentModel(
            category=ComponentCategory.AI_TOOLS,
            description="Test Python package",
            install_method=InstallMethod.PIP,
            install_args="tensorflow"
        )
        assert component.install_method == InstallMethod.PIP
        assert component.install_args == "tensorflow"


class TestComponentsFile:
    """Tests for ComponentsFile model."""
    
    def test_valid_components_file(self):
        """Test creating a valid components file."""
        components_data = {
            "python": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Python runtime",
                download_url="https://python.org/download.exe",
                install_method=InstallMethod.EXE
            ),
            "git": ComponentModel(
                category=ComponentCategory.VERSION_CONTROL,
                description="Git version control",
                download_url="https://git-scm.com/download.exe",
                install_method=InstallMethod.EXE
            )
        }
        
        components_file = ComponentsFile(components=components_data)
        assert len(components_file.components) == 2
        assert "python" in components_file.components
        assert "git" in components_file.components
    
    def test_empty_components_file(self):
        """Test components file with empty components dictionary."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentsFile(components={})
        assert "Components dictionary cannot be empty" in str(exc_info.value)
    
    def test_invalid_component_names(self):
        """Test components file with invalid component names."""
        components_data = {
            "invalid name with spaces": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Invalid component",
                download_url="https://example.com/download.exe",
                install_method=InstallMethod.EXE
            )
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ComponentsFile(components=components_data)
        assert "contains invalid characters" in str(exc_info.value)
    
    def test_component_name_too_long(self):
        """Test components file with component name that's too long."""
        long_name = "a" * 101  # 101 characters, exceeds 100 limit
        components_data = {
            long_name: ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Component with long name",
                download_url="https://example.com/download.exe",
                install_method=InstallMethod.EXE
            )
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ComponentsFile(components=components_data)
        assert "is too long" in str(exc_info.value)
    
    def test_undefined_dependency(self):
        """Test components file with undefined dependency."""
        components_data = {
            "app": ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="App that depends on undefined component",
                download_url="https://example.com/app.exe",
                install_method=InstallMethod.EXE,
                dependencies=["undefined_component"]
            )
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ComponentsFile(components=components_data)
        assert "has undefined dependency" in str(exc_info.value)
    
    def test_circular_dependency(self):
        """Test components file with circular dependencies."""
        components_data = {
            "app_a": ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="App A",
                download_url="https://example.com/a.exe",
                install_method=InstallMethod.EXE,
                dependencies=["app_b"]
            ),
            "app_b": ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="App B",
                download_url="https://example.com/b.exe",
                install_method=InstallMethod.EXE,
                dependencies=["app_a"]
            )
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ComponentsFile(components=components_data)
        assert "Circular dependency detected" in str(exc_info.value)
    
    def test_valid_dependencies(self):
        """Test components file with valid dependencies."""
        components_data = {
            "python": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Python runtime",
                download_url="https://python.org/download.exe",
                install_method=InstallMethod.EXE
            ),
            "pip_package": ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Python package",
                install_method=InstallMethod.PIP,
                install_args="tensorflow",
                dependencies=["python"]
            )
        }
        
        components_file = ComponentsFile(components=components_data)
        assert len(components_file.components) == 2
        assert components_file.components["pip_package"].dependencies == ["python"]


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_load_components_from_yaml_valid(self):
        """Test loading valid YAML file."""
        yaml_content = """
components:
  python:
    category: Runtimes
    description: Python runtime
    download_url: https://python.org/download.exe
    install_method: exe
  git:
    category: Version Control
    description: Git version control
    download_url: https://git-scm.com/download.exe
    install_method: exe
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.yaml"
            temp_file.write_text(yaml_content)
            
            components_file = load_components_from_yaml(str(temp_file))
            assert len(components_file.components) == 2
            assert "python" in components_file.components
            assert "git" in components_file.components
    
    def test_load_components_from_yaml_without_components_key(self):
        """Test loading YAML file without 'components' key."""
        yaml_content = """
python:
  category: Runtimes
  description: Python runtime
  download_url: https://python.org/download.exe
  install_method: exe
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.yaml"
            temp_file.write_text(yaml_content)
            
            components_file = load_components_from_yaml(str(temp_file))
            assert len(components_file.components) == 1
            assert "python" in components_file.components
    
    def test_load_components_from_yaml_file_not_found(self):
        """Test loading non-existent YAML file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_components_from_yaml("non_existent_file.yaml")
        assert "Component file not found" in str(exc_info.value)
    
    def test_load_components_from_yaml_invalid_yaml(self):
        """Test loading invalid YAML file."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.yaml"
            temp_file.write_text(invalid_yaml)
            
            with pytest.raises(yaml.YAMLError) as exc_info:
                load_components_from_yaml(str(temp_file))
            assert "Failed to parse YAML file" in str(exc_info.value)
    
    def test_validate_component_yaml_valid(self):
        """Test validating valid YAML file."""
        yaml_content = """
components:
  python:
    category: Runtimes
    description: Python runtime
    download_url: https://python.org/download.exe
    install_method: exe
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.yaml"
            temp_file.write_text(yaml_content)
            
            is_valid, errors = validate_component_yaml(str(temp_file))
            assert is_valid is True
            assert errors == []
    
    def test_validate_component_yaml_invalid(self):
        """Test validating invalid YAML file."""
        yaml_content = """
components:
  invalid_component:
    category: Invalid Category
    description: ""
    install_method: invalid_method
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.yaml"
            temp_file.write_text(yaml_content)
            
            is_valid, errors = validate_component_yaml(str(temp_file))
            assert is_valid is False
            assert len(errors) > 0
    
    def test_get_component_dependencies(self):
        """Test getting component dependencies."""
        components_data = {
            "base": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Base component",
                download_url="https://example.com/base.exe",
                install_method=InstallMethod.EXE
            ),
            "middle": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Middle component",
                download_url="https://example.com/middle.exe",
                install_method=InstallMethod.EXE,
                dependencies=["base"]
            ),
            "top": ComponentModel(
                category=ComponentCategory.AI_TOOLS,
                description="Top component",
                download_url="https://example.com/top.exe",
                install_method=InstallMethod.EXE,
                dependencies=["middle"]
            )
        }
        
        components_file = ComponentsFile(components=components_data)
        dependencies = get_component_dependencies(components_file, "top")
        
        # Should return dependencies in order: base, middle
        assert dependencies == ["base", "middle"]
    
    def test_get_component_dependencies_nonexistent(self):
        """Test getting dependencies for non-existent component."""
        components_data = {
            "python": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Python runtime",
                download_url="https://python.org/download.exe",
                install_method=InstallMethod.EXE
            )
        }
        
        components_file = ComponentsFile(components=components_data)
        
        with pytest.raises(ValueError) as exc_info:
            get_component_dependencies(components_file, "nonexistent")
        assert "Component 'nonexistent' not found" in str(exc_info.value)
    
    def test_get_components_by_category(self):
        """Test getting components by category."""
        components_data = {
            "python": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Python runtime",
                download_url="https://python.org/download.exe",
                install_method=InstallMethod.EXE
            ),
            "git": ComponentModel(
                category=ComponentCategory.VERSION_CONTROL,
                description="Git version control",
                download_url="https://git-scm.com/download.exe",
                install_method=InstallMethod.EXE
            ),
            "node": ComponentModel(
                category=ComponentCategory.RUNTIMES,
                description="Node.js runtime",
                download_url="https://nodejs.org/download.exe",
                install_method=InstallMethod.EXE
            )
        }
        
        components_file = ComponentsFile(components=components_data)
        runtime_components = get_components_by_category(components_file, ComponentCategory.RUNTIMES)
        
        assert len(runtime_components) == 2
        assert "python" in runtime_components
        assert "node" in runtime_components
        assert "git" not in runtime_components
    
    def test_validate_all_yaml_files(self):
        """Test validating all YAML files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid YAML file
            valid_yaml = temp_path / "valid.yaml"
            valid_yaml.write_text("""
components:
  python:
    category: Runtimes
    description: Python runtime
    download_url: https://python.org/download.exe
    install_method: exe
""")
            
            # Create invalid YAML file
            invalid_yaml = temp_path / "invalid.yaml"
            invalid_yaml.write_text("""
components:
  invalid:
    category: Invalid Category
    description: ""
    install_method: invalid
""")
            
            # Create non-YAML file (should be ignored)
            non_yaml = temp_path / "readme.txt"
            non_yaml.write_text("This is not a YAML file")
            
            results = validate_all_yaml_files(str(temp_path))
            
            assert len(results) == 2
            assert str(valid_yaml) in results
            assert str(invalid_yaml) in results
            assert str(non_yaml) not in results
            
            # Check validation results
            assert results[str(valid_yaml)][0] is True  # Valid file
            assert results[str(invalid_yaml)][0] is False  # Invalid file
    
    def test_validate_all_yaml_files_nonexistent_directory(self):
        """Test validating YAML files in non-existent directory."""
        results = validate_all_yaml_files("/nonexistent/directory")
        assert results == {}