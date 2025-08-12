"""Tests for core.plugin_system module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from core.plugin_system import (
    PluginStatus, ConflictType, PluginVersion, PluginDependency,
    PluginConflict, PluginMetadata, PluginConflictDetector
)
from core.exceptions import PluginSystemError, ValidationError


class TestPluginVersion:
    """Tests for PluginVersion class."""
    
    def test_version_creation(self):
        """Test creating a plugin version."""
        version = PluginVersion("1.2.3")
        
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert str(version) == "1.2.3"
    
    def test_version_comparison_equal(self):
        """Test version equality comparison."""
        v1 = PluginVersion("1.2.3")
        v2 = PluginVersion("1.2.3")
        v3 = PluginVersion("1.2.4")
        
        assert v1 == v2
        assert v1 != v3
    
    def test_version_comparison_less_than(self):
        """Test version less than comparison."""
        v1 = PluginVersion("1.2.3")
        v2 = PluginVersion("1.2.4")
        v3 = PluginVersion("1.3.0")
        v4 = PluginVersion("2.0.0")
        
        assert v1 < v2
        assert v1 < v3
        assert v1 < v4
        assert v2 < v3
        assert v3 < v4
    
    def test_version_comparison_greater_than(self):
        """Test version greater than comparison."""
        v1 = PluginVersion("2.0.0")
        v2 = PluginVersion("1.3.0")
        v3 = PluginVersion("1.2.4")
        v4 = PluginVersion("1.2.3")
        
        assert v1 > v2
        assert v1 > v3
        assert v1 > v4
        assert v2 > v3
        assert v3 > v4
    
    def test_version_comparison_less_equal(self):
        """Test version less than or equal comparison."""
        v1 = PluginVersion("1.2.3")
        v2 = PluginVersion("1.2.3")
        v3 = PluginVersion("1.2.4")
        
        assert v1 <= v2
        assert v1 <= v3
        assert not (v3 <= v1)
    
    def test_version_comparison_greater_equal(self):
        """Test version greater than or equal comparison."""
        v1 = PluginVersion("1.2.4")
        v2 = PluginVersion("1.2.3")
        v3 = PluginVersion("1.2.4")
        
        assert v1 >= v2
        assert v1 >= v3
        assert not (v2 >= v1)
    
    def test_invalid_version_format(self):
        """Test creating version with invalid format."""
        with pytest.raises(ValueError):
            PluginVersion("invalid")
        
        with pytest.raises(ValueError):
            PluginVersion("1.2")
        
        with pytest.raises(ValueError):
            PluginVersion("1.2.3.4")
    
    def test_version_with_non_numeric_parts(self):
        """Test creating version with non-numeric parts."""
        with pytest.raises(ValueError):
            PluginVersion("1.a.3")
        
        with pytest.raises(ValueError):
            PluginVersion("x.2.3")


class TestPluginDependency:
    """Tests for PluginDependency class."""
    
    def test_dependency_creation(self):
        """Test creating a plugin dependency."""
        dep = PluginDependency(
            name="test-plugin",
            version_constraint=">=1.0.0",
            required=True
        )
        
        assert dep.name == "test-plugin"
        assert dep.version_constraint == ">=1.0.0"
        assert dep.required is True
    
    def test_dependency_optional(self):
        """Test creating optional dependency."""
        dep = PluginDependency(
            name="optional-plugin",
            version_constraint="^2.0.0",
            required=False
        )
        
        assert dep.required is False
    
    def test_dependency_string_representation(self):
        """Test string representation of dependency."""
        dep = PluginDependency(
            name="test-plugin",
            version_constraint=">=1.0.0",
            required=True
        )
        
        expected = "test-plugin (>=1.0.0, required)"
        assert str(dep) == expected
    
    def test_optional_dependency_string_representation(self):
        """Test string representation of optional dependency."""
        dep = PluginDependency(
            name="optional-plugin",
            version_constraint="^2.0.0",
            required=False
        )
        
        expected = "optional-plugin (^2.0.0, optional)"
        assert str(dep) == expected


class TestPluginConflict:
    """Tests for PluginConflict class."""
    
    def test_conflict_creation(self):
        """Test creating a plugin conflict."""
        conflict = PluginConflict(
            conflict_type=ConflictType.VERSION_INCOMPATIBILITY,
            plugin_a="plugin-a",
            plugin_b="plugin-b",
            description="Version conflict between plugins"
        )
        
        assert conflict.conflict_type == ConflictType.VERSION_INCOMPATIBILITY
        assert conflict.plugin_a == "plugin-a"
        assert conflict.plugin_b == "plugin-b"
        assert "Version conflict" in conflict.description
    
    def test_conflict_string_representation(self):
        """Test string representation of conflict."""
        conflict = PluginConflict(
            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
            plugin_a="plugin-x",
            plugin_b="plugin-y",
            description="Dependency conflict detected"
        )
        
        expected = "DEPENDENCY_CONFLICT: plugin-x <-> plugin-y (Dependency conflict detected)"
        assert str(conflict) == expected


class TestPluginMetadata:
    """Tests for PluginMetadata class."""
    
    def test_metadata_creation(self):
        """Test creating plugin metadata."""
        dependencies = [
            PluginDependency("dep1", ">=1.0.0", True),
            PluginDependency("dep2", "^2.0.0", False)
        ]
        
        metadata = PluginMetadata(
            name="test-plugin",
            version=PluginVersion("1.2.3"),
            description="A test plugin",
            author="Test Author",
            dependencies=dependencies,
            status=PluginStatus.ACTIVE
        )
        
        assert metadata.name == "test-plugin"
        assert metadata.version == PluginVersion("1.2.3")
        assert metadata.description == "A test plugin"
        assert metadata.author == "Test Author"
        assert len(metadata.dependencies) == 2
        assert metadata.status == PluginStatus.ACTIVE
    
    def test_metadata_with_empty_dependencies(self):
        """Test creating metadata with no dependencies."""
        metadata = PluginMetadata(
            name="simple-plugin",
            version=PluginVersion("1.0.0"),
            description="Simple plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.INACTIVE
        )
        
        assert len(metadata.dependencies) == 0
        assert metadata.status == PluginStatus.INACTIVE
    
    def test_metadata_string_representation(self):
        """Test string representation of metadata."""
        metadata = PluginMetadata(
            name="example-plugin",
            version=PluginVersion("2.1.0"),
            description="Example plugin",
            author="Example Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        expected = "example-plugin v2.1.0 (ACTIVE)"
        assert str(metadata) == expected


class TestPluginConflictDetector:
    """Tests for PluginConflictDetector class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.plugin_system_enabled = True
        self.mock_config.plugin_signature_verification = True
        self.mock_config.plugin_sandboxing_enabled = True
        
        self.detector = PluginConflictDetector(self.mock_config)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detector_initialization(self):
        """Test PluginConflictDetector initialization."""
        assert self.detector._config == self.mock_config
        assert len(self.detector._plugins) == 0
        assert len(self.detector._conflicts) == 0
    
    def test_add_plugin(self):
        """Test adding a plugin to the detector."""
        metadata = PluginMetadata(
            name="test-plugin",
            version=PluginVersion("1.0.0"),
            description="Test plugin",
            author="Test Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(metadata)
        
        assert len(self.detector._plugins) == 1
        assert "test-plugin" in self.detector._plugins
        assert self.detector._plugins["test-plugin"] == metadata
    
    def test_add_duplicate_plugin(self):
        """Test adding a plugin with duplicate name."""
        metadata1 = PluginMetadata(
            name="duplicate-plugin",
            version=PluginVersion("1.0.0"),
            description="First plugin",
            author="Author 1",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        metadata2 = PluginMetadata(
            name="duplicate-plugin",
            version=PluginVersion("2.0.0"),
            description="Second plugin",
            author="Author 2",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(metadata1)
        
        with pytest.raises(PluginSystemError) as exc_info:
            self.detector.add_plugin(metadata2)
        
        assert "Plugin 'duplicate-plugin' already exists" in str(exc_info.value)
    
    def test_remove_plugin(self):
        """Test removing a plugin from the detector."""
        metadata = PluginMetadata(
            name="removable-plugin",
            version=PluginVersion("1.0.0"),
            description="Removable plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(metadata)
        assert len(self.detector._plugins) == 1
        
        self.detector.remove_plugin("removable-plugin")
        assert len(self.detector._plugins) == 0
        assert "removable-plugin" not in self.detector._plugins
    
    def test_remove_nonexistent_plugin(self):
        """Test removing a plugin that doesn't exist."""
        with pytest.raises(PluginSystemError) as exc_info:
            self.detector.remove_plugin("nonexistent-plugin")
        
        assert "Plugin 'nonexistent-plugin' not found" in str(exc_info.value)
    
    def test_detect_version_conflicts(self):
        """Test detecting version conflicts between plugins."""
        # Plugin A depends on Plugin C version >=2.0.0
        plugin_a = PluginMetadata(
            name="plugin-a",
            version=PluginVersion("1.0.0"),
            description="Plugin A",
            author="Author A",
            dependencies=[
                PluginDependency("plugin-c", ">=2.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        # Plugin B depends on Plugin C version <2.0.0
        plugin_b = PluginMetadata(
            name="plugin-b",
            version=PluginVersion("1.0.0"),
            description="Plugin B",
            author="Author B",
            dependencies=[
                PluginDependency("plugin-c", "<2.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        # Plugin C version 1.5.0
        plugin_c = PluginMetadata(
            name="plugin-c",
            version=PluginVersion("1.5.0"),
            description="Plugin C",
            author="Author C",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(plugin_a)
        self.detector.add_plugin(plugin_b)
        self.detector.add_plugin(plugin_c)
        
        conflicts = self.detector.detect_conflicts()
        
        # Should detect version incompatibility
        assert len(conflicts) > 0
        version_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.VERSION_INCOMPATIBILITY]
        assert len(version_conflicts) > 0
    
    def test_detect_dependency_conflicts(self):
        """Test detecting dependency conflicts."""
        # Plugin A depends on Plugin D
        plugin_a = PluginMetadata(
            name="plugin-a",
            version=PluginVersion("1.0.0"),
            description="Plugin A",
            author="Author A",
            dependencies=[
                PluginDependency("plugin-d", ">=1.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        # Plugin B also depends on Plugin D but it's not available
        plugin_b = PluginMetadata(
            name="plugin-b",
            version=PluginVersion("1.0.0"),
            description="Plugin B",
            author="Author B",
            dependencies=[
                PluginDependency("plugin-d", ">=2.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(plugin_a)
        self.detector.add_plugin(plugin_b)
        
        conflicts = self.detector.detect_conflicts()
        
        # Should detect dependency conflicts
        assert len(conflicts) > 0
        dependency_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DEPENDENCY_CONFLICT]
        assert len(dependency_conflicts) > 0
    
    def test_no_conflicts_detected(self):
        """Test case where no conflicts are detected."""
        # Compatible plugins with no conflicting dependencies
        plugin_a = PluginMetadata(
            name="plugin-a",
            version=PluginVersion("1.0.0"),
            description="Plugin A",
            author="Author A",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        plugin_b = PluginMetadata(
            name="plugin-b",
            version=PluginVersion("1.0.0"),
            description="Plugin B",
            author="Author B",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(plugin_a)
        self.detector.add_plugin(plugin_b)
        
        conflicts = self.detector.detect_conflicts()
        
        assert len(conflicts) == 0
    
    def test_get_plugin_info(self):
        """Test getting plugin information."""
        metadata = PluginMetadata(
            name="info-plugin",
            version=PluginVersion("1.2.3"),
            description="Info plugin",
            author="Info Author",
            dependencies=[
                PluginDependency("dep1", ">=1.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(metadata)
        
        info = self.detector.get_plugin_info("info-plugin")
        
        assert info["name"] == "info-plugin"
        assert info["version"] == "1.2.3"
        assert info["description"] == "Info plugin"
        assert info["author"] == "Info Author"
        assert info["status"] == "ACTIVE"
        assert len(info["dependencies"]) == 1
    
    def test_get_nonexistent_plugin_info(self):
        """Test getting info for nonexistent plugin."""
        with pytest.raises(PluginSystemError) as exc_info:
            self.detector.get_plugin_info("nonexistent-plugin")
        
        assert "Plugin 'nonexistent-plugin' not found" in str(exc_info.value)
    
    def test_list_all_plugins(self):
        """Test listing all plugins."""
        plugin1 = PluginMetadata(
            name="plugin-1",
            version=PluginVersion("1.0.0"),
            description="Plugin 1",
            author="Author 1",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        plugin2 = PluginMetadata(
            name="plugin-2",
            version=PluginVersion("2.0.0"),
            description="Plugin 2",
            author="Author 2",
            dependencies=[],
            status=PluginStatus.INACTIVE
        )
        
        self.detector.add_plugin(plugin1)
        self.detector.add_plugin(plugin2)
        
        all_plugins = self.detector.list_plugins()
        
        assert len(all_plugins) == 2
        assert "plugin-1" in all_plugins
        assert "plugin-2" in all_plugins
    
    def test_list_plugins_by_status(self):
        """Test listing plugins filtered by status."""
        active_plugin = PluginMetadata(
            name="active-plugin",
            version=PluginVersion("1.0.0"),
            description="Active plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        inactive_plugin = PluginMetadata(
            name="inactive-plugin",
            version=PluginVersion("1.0.0"),
            description="Inactive plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.INACTIVE
        )
        
        self.detector.add_plugin(active_plugin)
        self.detector.add_plugin(inactive_plugin)
        
        active_plugins = self.detector.list_plugins(status_filter=PluginStatus.ACTIVE)
        inactive_plugins = self.detector.list_plugins(status_filter=PluginStatus.INACTIVE)
        
        assert len(active_plugins) == 1
        assert "active-plugin" in active_plugins
        
        assert len(inactive_plugins) == 1
        assert "inactive-plugin" in inactive_plugins
    
    def test_update_plugin_status(self):
        """Test updating plugin status."""
        metadata = PluginMetadata(
            name="status-plugin",
            version=PluginVersion("1.0.0"),
            description="Status plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(metadata)
        
        # Update status to inactive
        self.detector.update_plugin_status("status-plugin", PluginStatus.INACTIVE)
        
        updated_plugin = self.detector._plugins["status-plugin"]
        assert updated_plugin.status == PluginStatus.INACTIVE
    
    def test_update_nonexistent_plugin_status(self):
        """Test updating status of nonexistent plugin."""
        with pytest.raises(PluginSystemError) as exc_info:
            self.detector.update_plugin_status("nonexistent-plugin", PluginStatus.INACTIVE)
        
        assert "Plugin 'nonexistent-plugin' not found" in str(exc_info.value)
    
    def test_clear_all_plugins(self):
        """Test clearing all plugins from detector."""
        plugin1 = PluginMetadata(
            name="plugin-1",
            version=PluginVersion("1.0.0"),
            description="Plugin 1",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        plugin2 = PluginMetadata(
            name="plugin-2",
            version=PluginVersion("1.0.0"),
            description="Plugin 2",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(plugin1)
        self.detector.add_plugin(plugin2)
        
        assert len(self.detector._plugins) == 2
        
        self.detector.clear_plugins()
        
        assert len(self.detector._plugins) == 0
        assert len(self.detector._conflicts) == 0
    
    def test_validate_plugin_compatibility(self):
        """Test validating plugin compatibility."""
        # Create a plugin with dependencies
        plugin_with_deps = PluginMetadata(
            name="dependent-plugin",
            version=PluginVersion("1.0.0"),
            description="Plugin with dependencies",
            author="Author",
            dependencies=[
                PluginDependency("required-plugin", ">=1.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        # Create the required plugin
        required_plugin = PluginMetadata(
            name="required-plugin",
            version=PluginVersion("1.5.0"),
            description="Required plugin",
            author="Author",
            dependencies=[],
            status=PluginStatus.ACTIVE
        )
        
        self.detector.add_plugin(required_plugin)
        
        # Should be compatible
        is_compatible = self.detector.validate_plugin_compatibility(plugin_with_deps)
        assert is_compatible is True
    
    def test_validate_plugin_incompatibility(self):
        """Test validating plugin incompatibility."""
        # Create a plugin with dependencies that can't be satisfied
        plugin_with_deps = PluginMetadata(
            name="dependent-plugin",
            version=PluginVersion("1.0.0"),
            description="Plugin with dependencies",
            author="Author",
            dependencies=[
                PluginDependency("missing-plugin", ">=1.0.0", True)
            ],
            status=PluginStatus.ACTIVE
        )
        
        # Should be incompatible (missing dependency)
        is_compatible = self.detector.validate_plugin_compatibility(plugin_with_deps)
        assert is_compatible is False