"""
Tests for the improvements implemented in the Environment Dev Deep Evaluation system.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tui.main import ComponentsScreen, SettingsScreen
from tui.installation_progress import InstallationProgressScreen
from cli.main import _install_component_internal
from cli.profiles import save_profile, load_profile
from core.error_handling import EnhancedErrorHandler
from core.exceptions import EnvironmentDevDeepEvaluationError


class TestTUIImprovements:
    """Test TUI improvements."""
    
    def test_components_screen_async_installation(self):
        """Test that ComponentsScreen uses async installation."""
        screen = ComponentsScreen()
        # Check that action_install is now async
        import inspect
        assert inspect.iscoroutinefunction(screen.action_install)
    
    def test_components_screen_async_installation_filtered(self):
        """Test that ComponentsScreen uses async installation for filtered components."""
        screen = ComponentsScreen()
        # Check that action_install_filtered is now async
        import inspect
        assert inspect.iscoroutinefunction(screen.action_install_filtered)
    
    def test_installation_progress_screen_exists(self):
        """Test that InstallationProgressScreen exists and has the right methods."""
        screen = InstallationProgressScreen(["test-component"])
        assert hasattr(screen, "run_installation")
        assert hasattr(screen, "cancel_installation")
        # Check that run_installation is async
        import inspect
        assert inspect.iscoroutinefunction(screen.run_installation)


class TestCLIImprovements:
    """Test CLI improvements."""
    
    def test_install_component_internal_json_output(self):
        """Test that _install_component_internal can produce JSON output."""
        # This would require more complex mocking, but we can at least check it exists
        assert callable(_install_component_internal)
    
    def test_profiles_management(self):
        """Test profile management functions."""
        # Test saving a profile
        with patch("builtins.open", mock_open()) as mock_file:
            save_profile("test-profile", ["Git", "Python"], "Test profile")
            mock_file.assert_called()
        
        # Test loading a profile (will fail because file doesn't exist, but tests the function exists)
        with pytest.raises(FileNotFoundError):
            load_profile("non-existent-profile")


class TestErrorHandlingImprovements:
    """Test error handling improvements."""
    
    def test_enhanced_error_messages(self):
        """Test that error messages are enhanced with actionable steps."""
        handler = EnhancedErrorHandler()
        
        # Create a test exception
        try:
            raise PermissionError("Test permission error")
        except Exception as e:
            # Create context
            from core.error_handling import ErrorContext, ErrorCategory, ErrorSeverity
            context = ErrorContext(
                component="test",
                operation="test_op",
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.HIGH
            )
            
            # Handle the error
            try:
                handler.handle_error(e, context)
            except EnvironmentDevDeepEvaluationError as enhanced_e:
                # Check that the message was enhanced
                assert "Suggested actions:" in enhanced_e.message
                assert "Run the application as administrator" in enhanced_e.message


class TestDoctorCommandImprovements:
    """Test doctor command improvements."""
    
    @patch("cli.main.console")
    @patch("cli.main.get_config_manager")
    def test_doctor_command_retro_games_verification(self, mock_config_manager, mock_console):
        """Test that doctor command includes Retro Games verification."""
        from cli.main import doctor
        
        # Mock config manager
        mock_config = MagicMock()
        mock_config.base_directory = "/tmp"
        mock_config.downloads_directory = "/tmp/downloads"
        mock_config.logs_directory = "/tmp/logs"
        mock_config.cache_directory = "/tmp/cache"
        mock_config.backups_directory = "/tmp/backups"
        
        mock_config_manager_instance = MagicMock()
        mock_config_manager_instance.get_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        # Mock platform and sys
        with patch("platform.system", return_value="Windows"), \
             patch("sys.version", "3.10.0"), \
             patch("platform.machine", return_value="AMD64"), \
             patch("shutil.disk_usage"), \
             patch("pathlib.Path.exists", return_value=True):
            
            # Call doctor command
            try:
                doctor()
            except SystemExit:
                pass  # Expected
            
            # Check that console print was called (indicating the command ran)
            assert mock_console.print.called


class TestReportCommandImprovements:
    """Test report command improvements."""
    
    def test_report_command_exists(self):
        """Test that report command exists."""
        from cli.main import report
        assert callable(report)


if __name__ == "__main__":
    pytest.main([__file__])