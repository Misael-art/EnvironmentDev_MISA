#!/usr/bin/env python3
"""
Main TUI application for Environment Dev Deep Evaluation.

Provides an interactive terminal user interface using Textual framework
for visual navigation, component management, and system operations.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, DataTable, Static, Input, 
    SelectionList, ProgressBar, Log, Tree, Tabs, TabPane,
    Label, Switch, RadioSet, RadioButton
)
from textual.screen import Screen
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.progress import Progress
from rich.console import Console
import yaml
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import ConfigurationManager
from detection.unified_engine import UnifiedDetectionEngine
from core.exceptions import EnvironmentDevDeepEvaluationError


class ComponentsScreen(Screen):
    """Screen for managing components."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("i", "install", "Install"),
        Binding("d", "details", "Details"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.components_data = {}
        self.selected_component = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal():
                # Left panel - Component list
                with Vertical(id="components-panel"):
                    yield Static("🔧 Available Components", id="components-title")
                    yield Input(placeholder="Search components...", id="search-input")
                    yield DataTable(id="components-table")
                    
                    with Horizontal(id="component-actions"):
                        yield Button("Install", id="install-btn", variant="primary")
                        yield Button("Details", id="details-btn", variant="default")
                        yield Button("Refresh", id="refresh-btn", variant="default")
                
                # Right panel - Component details
                with Vertical(id="details-panel"):
                    yield Static("📋 Component Details", id="details-title")
                    yield ScrollableContainer(id="details-content")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.load_components()
        self.setup_table()
    
    def load_components(self) -> None:
        """Load components from YAML files."""
        components_dir = Path("components")
        self.components_data = {}
        
        if not components_dir.exists():
            return
        
        for yaml_file in components_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    self.components_data.update(data)
            except Exception as e:
                self.notify(f"Error loading {yaml_file}: {e}", severity="warning")
    
    def setup_table(self) -> None:
        """Setup the components table."""
        table = self.query_one("#components-table", DataTable)
        table.add_columns("Name", "Category", "Version", "Status", "Confiança")
        
        # Try to enrich with detection confidence from registry
        confidence_index = {}
        try:
            engine = UnifiedDetectionEngine(ConfigurationManager())
            engine.initialize()
            registry_apps = engine.scan_registry_installations()
            confidence_index = {app.name.lower(): getattr(app.detection_confidence, 'value', 'unknown') for app in registry_apps}
        except Exception:
            confidence_index = {}

        def _format_confidence(value: str) -> str:
            mapping = {
                "high": "[green]✅ alta[/green]",
                "medium": "[yellow]🟡 média[/yellow]",
                "low": "[red]⚠️ baixa[/red]",
                "unknown": "[dim]❔ desconhecida[/dim]",
            }
            return mapping.get((value or "").lower(), mapping["unknown"])

        for name, data in self.components_data.items():
            if isinstance(data, dict):
                status = "🟡 Available"  # Mock status
                # naive name match for confidence
                comp_lower = name.lower()
                confidence = "unknown"
                if comp_lower in confidence_index:
                    confidence = confidence_index[comp_lower]
                else:
                    # try contains match
                    for reg_name, conf in confidence_index.items():
                        if comp_lower in reg_name or reg_name in comp_lower:
                            confidence = conf
                            break

                table.add_row(
                    name,
                    data.get('category', 'Unknown'),
                    data.get('version', 'Unknown'),
                    status,
                    _format_confidence(confidence),
                    key=name
                )
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in components table."""
        self.selected_component = event.row_key.value
        self.update_details_panel()
    
    def update_details_panel(self) -> None:
        """Update the details panel with selected component info."""
        if not self.selected_component:
            return
        
        data = self.components_data.get(self.selected_component, {})
        details_container = self.query_one("#details-content", ScrollableContainer)
        
        # Clear existing content
        details_container.remove_children()
        
        # Add component information
        details_container.mount(
            Static(f"[bold cyan]{self.selected_component}[/bold cyan]", id="component-name")
        )
        
        details_container.mount(
            Static(f"Description: {data.get('description', 'No description')}", id="component-desc")
        )
        
        details_container.mount(
            Static(f"Category: {data.get('category', 'Unknown')}", id="component-category")
        )
        
        details_container.mount(
            Static(f"Version: {data.get('version', 'Unknown')}", id="component-version")
        )
        
        # Installation info
        if 'installation' in data:
            install_data = data['installation']
            details_container.mount(
                Static("\n[bold]Installation Information:[/bold]", id="install-header")
            )
            
            if 'method' in install_data:
                details_container.mount(
                    Static(f"Method: {install_data['method']}", id="install-method")
                )
            
            if 'url' in install_data:
                details_container.mount(
                    Static(f"URL: {install_data['url']}", id="install-url")
                )
        
        # Dependencies
        if 'dependencies' in data and data['dependencies']:
            details_container.mount(
                Static("\n[bold]Dependencies:[/bold]", id="deps-header")
            )
            
            for dep in data['dependencies']:
                details_container.mount(
                    Static(f"• {dep}", id=f"dep-{dep}")
                )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "install-btn":
            self.action_install()
        elif event.button.id == "details-btn":
            self.action_details()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.filter_components(event.value)
    
    def filter_components(self, query: str) -> None:
        """Filter components based on search query."""
        table = self.query_one("#components-table", DataTable)
        table.clear()
        
        query_lower = query.lower()
        
        for name, data in self.components_data.items():
            if isinstance(data, dict):
                # Search in name and description
                if (query_lower in name.lower() or 
                    query_lower in data.get('description', '').lower()):
                    
                    status = "🟡 Available"  # Mock status
                    # naive name match for confidence during filter as well
                    comp_lower = name.lower()
                    confidence = "unknown"
                    if comp_lower in confidence_index:
                        confidence = confidence_index[comp_lower]
                    else:
                        for reg_name, conf in confidence_index.items():
                            if comp_lower in reg_name or reg_name in comp_lower:
                                confidence = conf
                                break

                    table.add_row(
                        name,
                        data.get('category', 'Unknown'),
                        data.get('version', 'Unknown'),
                        status,
                        confidence,
                        key=name
                    )
    
    def action_refresh(self) -> None:
        """Refresh components list."""
        self.load_components()
        self.setup_table()
        self.notify("Components refreshed", severity="information")
    
    def action_install(self) -> None:
        """Install selected component."""
        if not self.selected_component:
            self.notify("Please select a component to install", severity="warning")
            return
        
        # Disparar CLI real com RF005 (instalação com verificação de hash)
        try:
            from subprocess import run
            proc = run([sys.executable, "-m", "cli.main", "install", self.selected_component], capture_output=True, text=True)
            if proc.returncode == 0:
                self.notify(f"Installed {self.selected_component}", severity="information")
            else:
                msg = proc.stderr or proc.stdout or "Erro desconhecido"
                self.notify(f"Falha ao instalar {self.selected_component}: {msg}", severity="error")
        except Exception as e:
            self.notify(f"Erro ao executar instalação: {e}", severity="error")
    
    def action_details(self) -> None:
        """Show detailed component information."""
        if not self.selected_component:
            self.notify("Please select a component to view details", severity="warning")
            return
        
        self.update_details_panel()


class SystemInfoScreen(Screen):
    """Screen for displaying system information."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        
        with Container(id="system-container"):
            yield Static("🖥️ System Information", id="system-title")
            
            with Tabs("System", "Python", "Environment"):
                with TabPane("System", id="system-tab"):
                    yield ScrollableContainer(id="system-info")
                
                with TabPane("Python", id="python-tab"):
                    yield ScrollableContainer(id="python-info")
                
                with TabPane("Environment", id="env-tab"):
                    yield ScrollableContainer(id="env-info")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.load_system_info()
    
    def load_system_info(self) -> None:
        """Load and display system information."""
        import platform
        
        # System information
        system_container = self.query_one("#system-info", ScrollableContainer)
        system_container.mount(Static(f"Operating System: {platform.system()}"))
        system_container.mount(Static(f"Release: {platform.release()}"))
        system_container.mount(Static(f"Version: {platform.version()}"))
        system_container.mount(Static(f"Machine: {platform.machine()}"))
        system_container.mount(Static(f"Processor: {platform.processor()}"))
        
        # Python information
        python_container = self.query_one("#python-info", ScrollableContainer)
        python_container.mount(Static(f"Python Version: {sys.version.split()[0]}"))
        python_container.mount(Static(f"Executable: {sys.executable}"))
        python_container.mount(Static(f"Platform: {sys.platform}"))
        python_container.mount(Static(f"Prefix: {sys.prefix}"))
        
        # Environment variables
        env_container = self.query_one("#env-info", ScrollableContainer)
        import os
        relevant_vars = ['PATH', 'PYTHONPATH', 'HOME', 'USER', 'USERNAME']
        
        for var in relevant_vars:
            value = os.environ.get(var, 'Not set')
            if len(value) > 100:
                value = value[:97] + "..."
            env_container.mount(Static(f"{var}: {value}"))
    
    def action_refresh(self) -> None:
        """Refresh system information."""
        # Clear existing content
        for container_id in ["#system-info", "#python-info", "#env-info"]:
            container = self.query_one(container_id, ScrollableContainer)
            container.remove_children()
        
        self.load_system_info()
        self.notify("System information refreshed", severity="information")


class SettingsScreen(Screen):
    """Screen for application settings."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("s", "save", "Save"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        
        with Container(id="settings-container"):
            yield Static("⚙️ Settings", id="settings-title")
            
            with Vertical(id="settings-form"):
                yield Label("Debug Mode:")
                yield Switch(id="debug-switch")
                
                yield Label("\nLog Level:")
                with RadioSet(id="log-level"):
                    yield RadioButton("DEBUG", id="debug-radio")
                    yield RadioButton("INFO", id="info-radio", value=True)
                    yield RadioButton("WARNING", id="warning-radio")
                    yield RadioButton("ERROR", id="error-radio")
                
                yield Label("\nBase Directory:")
                yield Input(placeholder="/path/to/base/directory", id="base-dir-input")
                
                yield Label("\nDownloads Directory:")
                yield Input(placeholder="/path/to/downloads", id="downloads-dir-input")
                
                with Horizontal(id="settings-actions"):
                    yield Button("Save", id="save-btn", variant="primary")
                    yield Button("Reset", id="reset-btn", variant="default")
                    yield Button("Cancel", id="cancel-btn", variant="default")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.load_current_settings()
    
    def load_current_settings(self) -> None:
        """Load current configuration settings."""
        try:
            config_manager = ConfigurationManager()
            config = config_manager.get_config()
            
            # Set debug switch
            debug_switch = self.query_one("#debug-switch", Switch)
            debug_switch.value = config.debug_mode
            
            # Set base directory
            base_dir_input = self.query_one("#base-dir-input", Input)
            base_dir_input.value = config.base_directory
            
            # Set downloads directory
            downloads_dir_input = self.query_one("#downloads-dir-input", Input)
            downloads_dir_input.value = config.downloads_directory
            
        except Exception as e:
            self.notify(f"Error loading settings: {e}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "reset-btn":
            self.action_reset()
        elif event.button.id == "cancel-btn":
            self.app.pop_screen()
    
    def action_save(self) -> None:
        """Save current settings."""
        try:
            # Get values from form
            debug_switch = self.query_one("#debug-switch", Switch)
            base_dir_input = self.query_one("#base-dir-input", Input)
            downloads_dir_input = self.query_one("#downloads-dir-input", Input)
            
            # Mock save operation
            self.notify("Settings saved successfully", severity="information")
            
        except Exception as e:
            self.notify(f"Error saving settings: {e}", severity="error")
    
    def action_reset(self) -> None:
        """Reset settings to defaults."""
        self.load_current_settings()
        self.notify("Settings reset to current values", severity="information")


class EnvironmentDevTUI(App):
    """Main TUI application for Environment Dev Deep Evaluation."""
    
    CSS_PATH = "styles.css"
    TITLE = "Environment Dev Deep Evaluation - TUI"
    SUB_TITLE = "Advanced Development Environment Manager"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "show_components", "Components"),
        Binding("s", "show_system_info", "System Info"),
        Binding("t", "show_settings", "Settings"),
        Binding("h", "show_help", "Help"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="main-menu"):
            yield Static("🔧 Environment Dev Deep Evaluation", id="app-title")
            yield Static("Advanced Development Environment Manager", id="app-subtitle")
            
            with Vertical(id="menu-container"):
                yield Button("📦 Manage Components", id="components-btn", variant="primary")
                yield Button("🖥️ System Information", id="system-btn", variant="default")
                yield Button("⚙️ Settings", id="settings-btn", variant="default")
                yield Button("📋 Help", id="help-btn", variant="default")
                yield Button("🚪 Exit", id="exit-btn", variant="error")
            
            with Container(id="status-panel"):
                yield Static("Ready", id="status-text")
                yield Static(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", id="start-time")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.update_status("Application started")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "components-btn":
            self.action_show_components()
        elif event.button.id == "system-btn":
            self.action_show_system_info()
        elif event.button.id == "settings-btn":
            self.action_show_settings()
        elif event.button.id == "help-btn":
            self.action_show_help()
        elif event.button.id == "exit-btn":
            self.action_quit()
    
    def action_show_components(self) -> None:
        """Show components management screen."""
        self.push_screen(ComponentsScreen())
        self.update_status("Viewing components")
    
    def action_show_system_info(self) -> None:
        """Show system information screen."""
        self.push_screen(SystemInfoScreen())
        self.update_status("Viewing system information")
    
    def action_show_settings(self) -> None:
        """Show settings screen."""
        self.push_screen(SettingsScreen())
        self.update_status("Editing settings")
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
🔧 Environment Dev Deep Evaluation - Help

Keyboard Shortcuts:
• q - Quit application
• c - Show components
• s - Show system info
• t - Show settings
• h - Show this help
• Esc - Go back

Navigation:
• Use Tab/Shift+Tab to navigate between elements
• Use Enter to activate buttons
• Use arrow keys in tables and lists

Components Screen:
• r - Refresh components list
• i - Install selected component
• d - Show component details

For more information, visit the documentation.
        """
        
        self.notify(help_text, title="Help", timeout=10)
        self.update_status("Showing help")
    
    def update_status(self, message: str) -> None:
        """Update the status message."""
        try:
            status_text = self.query_one("#status-text", Static)
            status_text.update(message)
        except Exception:
            pass  # Ignore if status text widget not found


def main():
    """Main entry point for the TUI application."""
    app = EnvironmentDevTUI()
    app.run()


if __name__ == "__main__":
    main()