#!/usr/bin/env python3
"""
Interactive Documentation System

Provides interactive tutorials, examples, and guided walkthroughs
for the Environment Dev Deep Evaluation system.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.tree import Tree

class InteractiveDocumentation:
    """Main class for interactive documentation system."""
    
    def __init__(self):
        self.console = Console()
        self.tutorials = {}
        self.examples = {}
        self.current_tutorial = None
        self.user_progress = {}
        
        # Load built-in tutorials and examples
        self._load_tutorials()
        self._load_examples()
    
    def _load_tutorials(self):
        """Load available tutorials."""
        self.tutorials = {
            "getting_started": {
                "title": "🚀 Getting Started with Environment Dev",
                "description": "Learn the basics of using the Environment Dev system",
                "steps": [
                    {
                        "title": "Introduction",
                        "content": "Welcome to Environment Dev Deep Evaluation! This tutorial will guide you through the basic concepts and usage.",
                        "action": self._tutorial_introduction
                    },
                    {
                        "title": "CLI Basics",
                        "content": "Learn how to use the command-line interface",
                        "action": self._tutorial_cli_basics
                    },
                    {
                        "title": "TUI Navigation",
                        "content": "Explore the terminal user interface",
                        "action": self._tutorial_tui_navigation
                    },
                    {
                        "title": "Component Management",
                        "content": "Understanding components and their management",
                        "action": self._tutorial_components
                    }
                ]
            },
            "advanced_usage": {
                "title": "🔧 Advanced Usage Patterns",
                "description": "Advanced techniques and best practices",
                "steps": [
                    {
                        "title": "Custom Components",
                        "content": "Creating and managing custom components",
                        "action": self._tutorial_custom_components
                    },
                    {
                        "title": "Plugin Development",
                        "content": "Developing plugins for the system",
                        "action": self._tutorial_plugin_development
                    },
                    {
                        "title": "Configuration Management",
                        "content": "Advanced configuration techniques",
                        "action": self._tutorial_configuration
                    }
                ]
            },
            "troubleshooting": {
                "title": "🔍 Troubleshooting Guide",
                "description": "Common issues and their solutions",
                "steps": [
                    {
                        "title": "Common Errors",
                        "content": "Identifying and fixing common errors",
                        "action": self._tutorial_common_errors
                    },
                    {
                        "title": "Debug Tools",
                        "content": "Using built-in debugging tools",
                        "action": self._tutorial_debug_tools
                    },
                    {
                        "title": "Performance Optimization",
                        "content": "Optimizing system performance",
                        "action": self._tutorial_performance
                    }
                ]
            }
        }
    
    def _load_examples(self):
        """Load code examples."""
        self.examples = {
            "basic_cli": {
                "title": "Basic CLI Usage",
                "description": "Common CLI commands and their usage",
                "code": '''
# Initialize the system
python mecha.py init

# List available components
python mecha.py list-components

# Get system information
python mecha.py doctor

# Check version
python mecha.py version
''',
                "language": "bash"
            },
            "component_search": {
                "title": "Component Search and Management",
                "description": "How to search and manage components",
                "code": '''
# Search for components
python mecha.py search "web server"

# Get component information
python mecha.py info nginx

# List component categories
python mecha.py categories

# Validate components
python mecha.py validate
''',
                "language": "bash"
            },
            "python_api": {
                "title": "Python API Usage",
                "description": "Using the Python API directly",
                "code": '''
from core.configuration_manager import ConfigurationManager
from core.component_loader import ComponentLoader

# Initialize configuration
config = ConfigurationManager()
config.load_configuration()

# Load components
loader = ComponentLoader(config)
components = loader.load_all_components()

# Filter components by category
web_components = [c for c in components if c.category == "web"]

print(f"Found {len(web_components)} web components")
''',
                "language": "python"
            },
            "custom_component": {
                "title": "Creating Custom Components",
                "description": "Example of a custom component definition",
                "code": '''
# custom_component.yaml
name: "my-custom-app"
version: "1.0.0"
category: "development"
description: "My custom development application"

installation:
  windows:
    method: "download"
    url: "https://example.com/app.zip"
    hash: "sha256:abc123..."
    extract_to: "tools/my-app"
  
  linux:
    method: "package"
    package_manager: "apt"
    packages: ["my-app"]

validation:
  command: "my-app --version"
  expected_output: "My App v1.0.0"

tags: ["development", "custom", "tools"]
''',
                "language": "yaml"
            }
        }
    
    def show_main_menu(self):
        """Display the main documentation menu."""
        self.console.clear()
        
        # Header
        header = Panel(
            "[bold blue]📚 Environment Dev Interactive Documentation[/bold blue]\n"
            "[dim]Learn, explore, and master the Environment Dev system[/dim]",
            border_style="blue"
        )
        self.console.print(header)
        self.console.print()
        
        # Menu options
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold cyan")
        table.add_column("Description")
        
        table.add_row("1", "📖 Interactive Tutorials")
        table.add_row("2", "💡 Code Examples")
        table.add_row("3", "🔍 Search Documentation")
        table.add_row("4", "📊 Progress Tracker")
        table.add_row("5", "❓ Quick Help")
        table.add_row("q", "🚪 Quit")
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "[bold]Select an option[/bold]",
            choices=["1", "2", "3", "4", "5", "q"],
            default="1"
        )
        
        if choice == "1":
            self.show_tutorials_menu()
        elif choice == "2":
            self.show_examples_menu()
        elif choice == "3":
            self.search_documentation()
        elif choice == "4":
            self.show_progress_tracker()
        elif choice == "5":
            self.show_quick_help()
        elif choice == "q":
            self.console.print("[green]👋 Thanks for using Environment Dev Documentation![/green]")
            return
        
        # Return to main menu unless quitting
        if choice != "q":
            input("\nPress Enter to return to main menu...")
            self.show_main_menu()
    
    def show_tutorials_menu(self):
        """Display available tutorials."""
        self.console.clear()
        
        header = Panel(
            "[bold green]📖 Interactive Tutorials[/bold green]\n"
            "[dim]Step-by-step guided learning experiences[/dim]",
            border_style="green"
        )
        self.console.print(header)
        self.console.print()
        
        # List tutorials
        for i, (key, tutorial) in enumerate(self.tutorials.items(), 1):
            progress = self.user_progress.get(key, 0)
            total_steps = len(tutorial["steps"])
            progress_bar = "█" * progress + "░" * (total_steps - progress)
            
            panel = Panel(
                f"[bold]{tutorial['title']}[/bold]\n"
                f"{tutorial['description']}\n\n"
                f"Progress: [{progress}/{total_steps}] {progress_bar}",
                title=f"Tutorial {i}",
                border_style="dim"
            )
            self.console.print(panel)
        
        self.console.print()
        choice = Prompt.ask(
            "[bold]Select a tutorial (1-3) or 'b' to go back[/bold]",
            choices=["1", "2", "3", "b"]
        )
        
        if choice == "b":
            return
        
        tutorial_keys = list(self.tutorials.keys())
        selected_tutorial = tutorial_keys[int(choice) - 1]
        self.start_tutorial(selected_tutorial)
    
    def start_tutorial(self, tutorial_key: str):
        """Start an interactive tutorial."""
        tutorial = self.tutorials[tutorial_key]
        self.current_tutorial = tutorial_key
        
        self.console.clear()
        self.console.print(Panel(
            f"[bold blue]Starting Tutorial: {tutorial['title']}[/bold blue]",
            border_style="blue"
        ))
        
        current_step = self.user_progress.get(tutorial_key, 0)
        
        for i, step in enumerate(tutorial["steps"][current_step:], current_step):
            self.console.print(f"\n[bold cyan]Step {i + 1}: {step['title']}[/bold cyan]")
            self.console.print(step["content"])
            self.console.print()
            
            if "action" in step and callable(step["action"]):
                step["action"]()
            
            if not Confirm.ask("Continue to next step?", default=True):
                break
            
            # Update progress
            self.user_progress[tutorial_key] = i + 1
        
        self.console.print("\n[bold green]✅ Tutorial completed![/bold green]")
    
    def show_examples_menu(self):
        """Display code examples."""
        self.console.clear()
        
        header = Panel(
            "[bold yellow]💡 Code Examples[/bold yellow]\n"
            "[dim]Practical code examples and snippets[/dim]",
            border_style="yellow"
        )
        self.console.print(header)
        self.console.print()
        
        # List examples
        for i, (key, example) in enumerate(self.examples.items(), 1):
            self.console.print(f"[bold cyan]{i}.[/bold cyan] {example['title']}")
            self.console.print(f"   {example['description']}")
            self.console.print()
        
        choice = Prompt.ask(
            "[bold]Select an example (1-4) or 'b' to go back[/bold]",
            choices=["1", "2", "3", "4", "b"]
        )
        
        if choice == "b":
            return
        
        example_keys = list(self.examples.keys())
        selected_example = example_keys[int(choice) - 1]
        self.show_example(selected_example)
    
    def show_example(self, example_key: str):
        """Display a specific code example."""
        example = self.examples[example_key]
        
        self.console.clear()
        self.console.print(Panel(
            f"[bold yellow]{example['title']}[/bold yellow]\n"
            f"{example['description']}",
            border_style="yellow"
        ))
        
        # Display code with syntax highlighting
        syntax = Syntax(
            example["code"],
            example["language"],
            theme="monokai",
            line_numbers=True
        )
        self.console.print(syntax)
        
        self.console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
    
    def search_documentation(self):
        """Search through documentation content."""
        self.console.clear()
        
        header = Panel(
            "[bold magenta]🔍 Search Documentation[/bold magenta]\n"
            "[dim]Find specific topics and information[/dim]",
            border_style="magenta"
        )
        self.console.print(header)
        
        query = Prompt.ask("[bold]Enter search term[/bold]")
        
        if not query:
            return
        
        # Simple search implementation
        results = []
        
        # Search tutorials
        for key, tutorial in self.tutorials.items():
            if query.lower() in tutorial["title"].lower() or query.lower() in tutorial["description"].lower():
                results.append(("Tutorial", tutorial["title"], key))
            
            for step in tutorial["steps"]:
                if query.lower() in step["title"].lower() or query.lower() in step["content"].lower():
                    results.append(("Tutorial Step", f"{tutorial['title']} - {step['title']}", key))
        
        # Search examples
        for key, example in self.examples.items():
            if query.lower() in example["title"].lower() or query.lower() in example["description"].lower():
                results.append(("Example", example["title"], key))
        
        self.console.print(f"\n[bold]Search results for '{query}':[/bold]")
        
        if not results:
            self.console.print("[dim]No results found.[/dim]")
        else:
            for i, (type_, title, key) in enumerate(results, 1):
                self.console.print(f"[cyan]{i}.[/cyan] [{type_}] {title}")
        
        input("\nPress Enter to continue...")
    
    def show_progress_tracker(self):
        """Show user's learning progress."""
        self.console.clear()
        
        header = Panel(
            "[bold blue]📊 Progress Tracker[/bold blue]\n"
            "[dim]Track your learning journey[/dim]",
            border_style="blue"
        )
        self.console.print(header)
        
        if not self.user_progress:
            self.console.print("\n[dim]No progress recorded yet. Start a tutorial to begin tracking![/dim]")
        else:
            for tutorial_key, progress in self.user_progress.items():
                tutorial = self.tutorials[tutorial_key]
                total_steps = len(tutorial["steps"])
                percentage = (progress / total_steps) * 100
                
                self.console.print(f"\n[bold]{tutorial['title']}[/bold]")
                self.console.print(f"Progress: {progress}/{total_steps} steps ({percentage:.1f}%)")
                
                # Progress bar
                bar_length = 20
                filled = int((progress / total_steps) * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                self.console.print(f"[green]{bar}[/green]")
        
        input("\nPress Enter to continue...")
    
    def show_quick_help(self):
        """Show quick help and tips."""
        self.console.clear()
        
        help_content = """
# Quick Help & Tips

## Navigation
- Use number keys to select menu options
- Press 'b' to go back in most menus
- Press 'q' to quit from the main menu

## Tutorials
- Interactive step-by-step guides
- Progress is automatically saved
- You can resume tutorials where you left off

## Examples
- Copy-paste ready code snippets
- Syntax highlighted for better readability
- Covers common use cases

## Search
- Search across all documentation content
- Case-insensitive matching
- Finds tutorials, steps, and examples

## Tips
- Take your time with tutorials
- Try examples in your own environment
- Use the search feature to find specific topics
- Check your progress regularly
"""
        
        markdown = Markdown(help_content)
        self.console.print(markdown)
        
        input("\nPress Enter to continue...")
    
    # Tutorial action methods
    def _tutorial_introduction(self):
        """Introduction tutorial step."""
        intro_text = """
Environment Dev Deep Evaluation is a comprehensive system for managing
development environments and components. It provides:

• **CLI Interface**: Command-line tools for quick operations
• **TUI Interface**: Interactive terminal interface for visual navigation
• **Component Management**: Automated installation and configuration
• **Plugin System**: Extensible architecture for custom functionality

Let's explore these features together!
"""
        self.console.print(Panel(intro_text, title="Welcome!", border_style="green"))
    
    def _tutorial_cli_basics(self):
        """CLI basics tutorial step."""
        cli_example = """
# Basic CLI commands
python mecha.py --help          # Show help
python mecha.py version         # Show version
python mecha.py init            # Initialize system
python mecha.py list-components # List components
python mecha.py doctor          # System diagnostics
"""
        syntax = Syntax(cli_example, "bash", theme="monokai")
        self.console.print(syntax)
        
        if Confirm.ask("Would you like to try running 'python mecha.py --help' now?"):
            self.console.print("\n[dim]Run this command in another terminal:[/dim]")
            self.console.print("[bold cyan]python mecha.py --help[/bold cyan]")
    
    def _tutorial_tui_navigation(self):
        """TUI navigation tutorial step."""
        tui_info = """
The Terminal User Interface (TUI) provides a visual way to interact with the system:

• **Navigation**: Use arrow keys or vim-style keys (h,j,k,l)
• **Shortcuts**: Press 'q' to quit, 'h' for help
• **Screens**: Components, System Info, Settings
• **Interactive**: Click or use keyboard shortcuts

To start the TUI, run: `python mecha-tui.py`
"""
        self.console.print(Panel(tui_info, title="TUI Navigation", border_style="blue"))
    
    def _tutorial_components(self):
        """Components tutorial step."""
        components_info = """
Components are the building blocks of your development environment:

• **Categories**: web, database, development, tools, etc.
• **Installation**: Automated download and setup
• **Validation**: Verify components are working correctly
• **Management**: Search, install, update, remove

Example component operations:
- Search: `python mecha.py search "web server"`
- Info: `python mecha.py info nginx`
- Validate: `python mecha.py validate`
"""
        self.console.print(Panel(components_info, title="Component Management", border_style="yellow"))
    
    def _tutorial_custom_components(self):
        """Custom components tutorial step."""
        self.console.print("[bold]Creating Custom Components[/bold]")
        self.console.print("Custom components are defined in YAML files with specific structure...")
    
    def _tutorial_plugin_development(self):
        """Plugin development tutorial step."""
        self.console.print("[bold]Plugin Development[/bold]")
        self.console.print("Plugins extend the system functionality...")
    
    def _tutorial_configuration(self):
        """Configuration tutorial step."""
        self.console.print("[bold]Configuration Management[/bold]")
        self.console.print("Advanced configuration techniques...")
    
    def _tutorial_common_errors(self):
        """Common errors tutorial step."""
        self.console.print("[bold]Common Errors and Solutions[/bold]")
        self.console.print("Here are the most common issues and how to fix them...")
    
    def _tutorial_debug_tools(self):
        """Debug tools tutorial step."""
        self.console.print("[bold]Debug Tools[/bold]")
        self.console.print("Using built-in debugging and diagnostic tools...")
    
    def _tutorial_performance(self):
        """Performance tutorial step."""
        self.console.print("[bold]Performance Optimization[/bold]")
        self.console.print("Tips for optimizing system performance...")

def main():
    """Main entry point for interactive documentation."""
    try:
        docs = InteractiveDocumentation()
        docs.show_main_menu()
    except KeyboardInterrupt:
        print("\n👋 Documentation session ended.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()