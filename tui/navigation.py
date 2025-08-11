#!/usr/bin/env python3
"""
Advanced Navigation System for TUI

Provides enhanced navigation features including context menus,
keyboard shortcuts, breadcrumbs, and visual navigation aids.
"""

from typing import Optional, List, Dict, Any, Callable
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, Button, Tree, ListView, ListItem, Label,
    Input, OptionList, SelectionList, Tabs, TabPane
)
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message
from textual.reactive import reactive
from rich.text import Text
from rich.console import Console

console = Console()

class NavigationBreadcrumb(Static):
    """Breadcrumb navigation widget."""
    
    def __init__(self, path: List[str] = None, **kwargs):
        """Initialize breadcrumb navigation.
        
        Args:
            path: List of navigation path items
        """
        super().__init__(**kwargs)
        self.path = path or []
    
    def update_path(self, path: List[str]):
        """Update the breadcrumb path.
        
        Args:
            path: New navigation path
        """
        self.path = path
        self.update(self._render_breadcrumb())
    
    def _render_breadcrumb(self) -> Text:
        """Render the breadcrumb navigation.
        
        Returns:
            Formatted breadcrumb text
        """
        if not self.path:
            return Text("🏠 Home", style="dim")
        
        breadcrumb = Text()
        breadcrumb.append("🏠 ", style="blue")
        
        for i, item in enumerate(self.path):
            if i > 0:
                breadcrumb.append(" › ", style="dim")
            
            if i == len(self.path) - 1:
                # Current page - highlighted
                breadcrumb.append(item, style="bold cyan")
            else:
                # Previous pages - clickable
                breadcrumb.append(item, style="blue underline")
        
        return breadcrumb
    
    def render(self) -> Text:
        """Render the breadcrumb widget.
        
        Returns:
            Rendered breadcrumb
        """
        return self._render_breadcrumb()

class ContextMenu(Container):
    """Context menu widget for right-click actions."""
    
    def __init__(self, items: List[Dict[str, Any]], **kwargs):
        """Initialize context menu.
        
        Args:
            items: List of menu items with 'label', 'action', and optional 'shortcut'
        """
        super().__init__(**kwargs)
        self.items = items
        self.visible = False
    
    def compose(self) -> ComposeResult:
        """Compose the context menu.
        
        Yields:
            Menu items as buttons
        """
        with Vertical(classes="context-menu"):
            for item in self.items:
                label = item['label']
                if 'shortcut' in item:
                    label += f" ({item['shortcut']})"
                
                yield Button(
                    label,
                    id=f"ctx-{item['label'].lower().replace(' ', '-')}",
                    classes="context-menu-item"
                )
    
    def show_at(self, x: int, y: int):
        """Show context menu at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.visible = True
        self.styles.display = "block"
        self.styles.offset = (x, y)
    
    def hide(self):
        """Hide the context menu."""
        self.visible = False
        self.styles.display = "none"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle context menu item selection.
        
        Args:
            event: Button press event
        """
        button_id = event.button.id
        if button_id and button_id.startswith("ctx-"):
            action_name = button_id[4:].replace('-', ' ')
            
            # Find and execute the action
            for item in self.items:
                if item['label'].lower().replace(' ', '-') == action_name:
                    if 'action' in item and callable(item['action']):
                        item['action']()
                    break
            
            self.hide()

class QuickSearch(Container):
    """Quick search overlay widget."""
    
    def __init__(self, search_callback: Callable[[str], List[Dict]], **kwargs):
        """Initialize quick search.
        
        Args:
            search_callback: Function to call for searching
        """
        super().__init__(**kwargs)
        self.search_callback = search_callback
        self.visible = False
    
    def compose(self) -> ComposeResult:
        """Compose the quick search overlay.
        
        Yields:
            Search input and results
        """
        with Vertical(classes="quick-search-overlay"):
            yield Static("🔍 Quick Search", classes="search-title")
            yield Input(placeholder="Type to search...", id="search-input")
            yield ListView(id="search-results")
    
    def show(self):
        """Show the quick search overlay."""
        self.visible = True
        self.styles.display = "block"
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    def hide(self):
        """Hide the quick search overlay."""
        self.visible = False
        self.styles.display = "none"
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes.
        
        Args:
            event: Input change event
        """
        if event.input.id == "search-input":
            query = event.value
            if len(query) >= 2:  # Start searching after 2 characters
                results = self.search_callback(query)
                self._update_results(results)
    
    def _update_results(self, results: List[Dict]):
        """Update search results display.
        
        Args:
            results: List of search results
        """
        results_list = self.query_one("#search-results", ListView)
        results_list.clear()
        
        for result in results[:10]:  # Limit to 10 results
            item_text = f"{result.get('title', 'Unknown')} - {result.get('description', '')}"
            results_list.append(ListItem(Label(item_text)))

class NavigationSidebar(Container):
    """Enhanced navigation sidebar with tree view and shortcuts."""
    
    def __init__(self, **kwargs):
        """Initialize navigation sidebar."""
        super().__init__(**kwargs)
        self.current_section = "components"
    
    def compose(self) -> ComposeResult:
        """Compose the navigation sidebar.
        
        Yields:
            Navigation tree and shortcuts
        """
        with Vertical(classes="nav-sidebar"):
            yield Static("📋 Navigation", classes="nav-title")
            
            # Main navigation tree
            nav_tree = Tree("Environment Dev", id="nav-tree")
            nav_tree.root.expand()
            
            # Components section
            components_node = nav_tree.root.add("📦 Components")
            components_node.add_leaf("📋 List All")
            components_node.add_leaf("🔍 Search")
            components_node.add_leaf("📊 Categories")
            components_node.add_leaf("✅ Validation")
            
            # System section
            system_node = nav_tree.root.add("🖥️ System")
            system_node.add_leaf("ℹ️ Information")
            system_node.add_leaf("🏥 Health Check")
            system_node.add_leaf("📊 Performance")
            system_node.add_leaf("📝 Logs")
            
            # Tools section
            tools_node = nav_tree.root.add("🔧 Tools")
            tools_node.add_leaf("🛠️ Development")
            tools_node.add_leaf("🐛 Debugging")
            tools_node.add_leaf("📦 Build")
            tools_node.add_leaf("🔄 Automation")
            
            # Settings section
            settings_node = nav_tree.root.add("⚙️ Settings")
            settings_node.add_leaf("🎨 Appearance")
            settings_node.add_leaf("⌨️ Shortcuts")
            settings_node.add_leaf("🔧 Configuration")
            settings_node.add_leaf("📁 Paths")
            
            yield nav_tree
            
            # Quick actions
            yield Static("⚡ Quick Actions", classes="section-title")
            yield Button("🚀 Quick Start", id="quick-start", classes="nav-button")
            yield Button("📖 Documentation", id="docs", classes="nav-button")
            yield Button("❓ Help", id="help", classes="nav-button")
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle navigation tree selection.
        
        Args:
            event: Tree node selection event
        """
        node = event.node
        if node.data:
            # Handle navigation based on selected node
            self._navigate_to_section(str(node.data))
    
    def _navigate_to_section(self, section: str):
        """Navigate to a specific section.
        
        Args:
            section: Section identifier
        """
        self.current_section = section
        # Post navigation message to parent app
        self.post_message(NavigationChanged(section))

class NavigationChanged(Message):
    """Message sent when navigation changes."""
    
    def __init__(self, section: str):
        """Initialize navigation change message.
        
        Args:
            section: New section identifier
        """
        super().__init__()
        self.section = section

class StatusBar(Container):
    """Enhanced status bar with context information."""
    
    def __init__(self, **kwargs):
        """Initialize status bar."""
        super().__init__(**kwargs)
        self.status_text = "Ready"
        self.context_info = ""
        self.shortcuts = []
    
    def compose(self) -> ComposeResult:
        """Compose the status bar.
        
        Yields:
            Status information and shortcuts
        """
        with Horizontal(classes="status-bar"):
            yield Static(self.status_text, id="status-text", classes="status-text")
            yield Static(self.context_info, id="context-info", classes="context-info")
            yield Static(self._format_shortcuts(), id="shortcuts", classes="shortcuts")
    
    def update_status(self, text: str, context: str = "", shortcuts: List[str] = None):
        """Update status bar information.
        
        Args:
            text: Main status text
            context: Context information
            shortcuts: List of available shortcuts
        """
        self.status_text = text
        self.context_info = context
        self.shortcuts = shortcuts or []
        
        # Update widgets
        try:
            self.query_one("#status-text", Static).update(text)
            self.query_one("#context-info", Static).update(context)
            self.query_one("#shortcuts", Static).update(self._format_shortcuts())
        except Exception:
            pass  # Widgets might not be mounted yet
    
    def _format_shortcuts(self) -> str:
        """Format shortcuts for display.
        
        Returns:
            Formatted shortcuts string
        """
        if not self.shortcuts:
            return ""
        
        return " | ".join(self.shortcuts)

class NavigationManager:
    """Manages navigation state and history."""
    
    def __init__(self):
        """Initialize navigation manager."""
        self.history: List[str] = []
        self.current_index = -1
        self.breadcrumb_path: List[str] = []
    
    def navigate_to(self, section: str, title: str = None):
        """Navigate to a new section.
        
        Args:
            section: Section identifier
            title: Display title for breadcrumb
        """
        # Add to history
        if self.current_index < len(self.history) - 1:
            # Remove forward history if we're not at the end
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(section)
        self.current_index = len(self.history) - 1
        
        # Update breadcrumb
        if title:
            self.breadcrumb_path.append(title)
    
    def go_back(self) -> Optional[str]:
        """Go back in navigation history.
        
        Returns:
            Previous section or None if at beginning
        """
        if self.current_index > 0:
            self.current_index -= 1
            if self.breadcrumb_path:
                self.breadcrumb_path.pop()
            return self.history[self.current_index]
        return None
    
    def go_forward(self) -> Optional[str]:
        """Go forward in navigation history.
        
        Returns:
            Next section or None if at end
        """
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def can_go_back(self) -> bool:
        """Check if can go back.
        
        Returns:
            True if can go back
        """
        return self.current_index > 0
    
    def can_go_forward(self) -> bool:
        """Check if can go forward.
        
        Returns:
            True if can go forward
        """
        return self.current_index < len(self.history) - 1

class KeyboardShortcuts:
    """Manages keyboard shortcuts and help."""
    
    def __init__(self):
        """Initialize keyboard shortcuts manager."""
        self.shortcuts = {
            # Navigation
            "ctrl+h": {"action": "go_home", "description": "Go to home screen"},
            "ctrl+b": {"action": "go_back", "description": "Go back in history"},
            "ctrl+f": {"action": "go_forward", "description": "Go forward in history"},
            "ctrl+r": {"action": "refresh", "description": "Refresh current view"},
            
            # Search and navigation
            "ctrl+k": {"action": "quick_search", "description": "Open quick search"},
            "ctrl+p": {"action": "command_palette", "description": "Open command palette"},
            "ctrl+shift+p": {"action": "show_shortcuts", "description": "Show all shortcuts"},
            
            # Components
            "ctrl+l": {"action": "list_components", "description": "List all components"},
            "ctrl+s": {"action": "search_components", "description": "Search components"},
            "ctrl+i": {"action": "component_info", "description": "Show component info"},
            
            # System
            "ctrl+d": {"action": "system_info", "description": "Show system information"},
            "ctrl+shift+d": {"action": "doctor", "description": "Run system diagnostics"},
            
            # Tools
            "ctrl+t": {"action": "dev_tools", "description": "Open development tools"},
            "ctrl+shift+t": {"action": "debug_tools", "description": "Open debugging tools"},
            
            # General
            "f1": {"action": "help", "description": "Show help"},
            "f5": {"action": "refresh", "description": "Refresh current view"},
            "escape": {"action": "cancel", "description": "Cancel current action"},
            "ctrl+q": {"action": "quit", "description": "Quit application"},
        }
    
    def get_shortcuts_for_context(self, context: str) -> List[str]:
        """Get relevant shortcuts for current context.
        
        Args:
            context: Current context (e.g., 'components', 'system')
            
        Returns:
            List of relevant shortcuts
        """
        relevant = []
        
        # Always show general shortcuts
        relevant.extend(["F1 Help", "Ctrl+Q Quit", "Ctrl+K Search"])
        
        # Context-specific shortcuts
        if context == "components":
            relevant.extend(["Ctrl+L List", "Ctrl+S Search", "Ctrl+I Info"])
        elif context == "system":
            relevant.extend(["Ctrl+D Info", "Ctrl+Shift+D Doctor"])
        elif context == "tools":
            relevant.extend(["Ctrl+T Dev Tools", "Ctrl+Shift+T Debug"])
        
        return relevant
    
    def get_all_shortcuts(self) -> Dict[str, Dict[str, str]]:
        """Get all available shortcuts.
        
        Returns:
            Dictionary of all shortcuts
        """
        return self.shortcuts.copy()
    
    def format_shortcuts_help(self) -> str:
        """Format shortcuts for help display.
        
        Returns:
            Formatted shortcuts help text
        """
        help_text = "\n🔧 Keyboard Shortcuts\n\n"
        
        categories = {
            "Navigation": ["ctrl+h", "ctrl+b", "ctrl+f", "ctrl+r"],
            "Search": ["ctrl+k", "ctrl+p", "ctrl+shift+p"],
            "Components": ["ctrl+l", "ctrl+s", "ctrl+i"],
            "System": ["ctrl+d", "ctrl+shift+d"],
            "Tools": ["ctrl+t", "ctrl+shift+t"],
            "General": ["f1", "f5", "escape", "ctrl+q"]
        }
        
        for category, keys in categories.items():
            help_text += f"\n{category}:\n"
            for key in keys:
                if key in self.shortcuts:
                    shortcut = self.shortcuts[key]
                    help_text += f"  {key.upper():<15} {shortcut['description']}\n"
        
        return help_text