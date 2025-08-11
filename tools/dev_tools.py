#!/usr/bin/env python3
"""
Development Tools Suite

Provides enhanced development tools, automation scripts, and utilities
for developers working with the Environment Dev Deep Evaluation system.
"""

import os
import sys
import json
import yaml
import time
import shutil
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout

class DevelopmentTools:
    """Main class for development tools and automation."""
    
    def __init__(self):
        self.console = Console()
        self.project_root = Path.cwd()
        self.tools_dir = self.project_root / "tools"
        self.logs_dir = self.project_root / "logs"
        self.backup_dir = self.project_root / "backups"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
    
    def show_main_menu(self):
        """Display the main development tools menu."""
        self.console.clear()
        
        # Header
        header = Panel(
            "[bold green]🔧 Environment Dev Development Tools[/bold green]\n"
            "[dim]Enhanced tools and automation for developers[/dim]",
            border_style="green"
        )
        self.console.print(header)
        self.console.print()
        
        # Menu options
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold cyan")
        table.add_column("Description")
        
        table.add_row("1", "🔍 Project Analysis & Health Check")
        table.add_row("2", "🧹 Code Quality & Cleanup Tools")
        table.add_row("3", "📦 Build & Deployment Automation")
        table.add_row("4", "🐛 Debugging & Diagnostic Tools")
        table.add_row("5", "📊 Performance Monitoring")
        table.add_row("6", "🔄 Backup & Recovery Tools")
        table.add_row("7", "⚙️ Configuration Management")
        table.add_row("8", "📝 Documentation Generator")
        table.add_row("q", "🚪 Quit")
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "[bold]Select a tool[/bold]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "q"],
            default="1"
        )
        
        if choice == "1":
            self.project_analysis()
        elif choice == "2":
            self.code_quality_tools()
        elif choice == "3":
            self.build_automation()
        elif choice == "4":
            self.debugging_tools()
        elif choice == "5":
            self.performance_monitoring()
        elif choice == "6":
            self.backup_recovery()
        elif choice == "7":
            self.configuration_management()
        elif choice == "8":
            self.documentation_generator()
        elif choice == "q":
            self.console.print("[green]👋 Thanks for using Development Tools![/green]")
            return
        
        # Return to main menu unless quitting
        if choice != "q":
            input("\nPress Enter to return to main menu...")
            self.show_main_menu()
    
    def project_analysis(self):
        """Analyze project structure and health."""
        self.console.clear()
        
        header = Panel(
            "[bold blue]🔍 Project Analysis & Health Check[/bold blue]",
            border_style="blue"
        )
        self.console.print(header)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            
            # Analyze project structure
            task1 = progress.add_task("Analyzing project structure...", total=None)
            structure_info = self._analyze_project_structure()
            progress.update(task1, completed=True)
            
            # Check dependencies
            task2 = progress.add_task("Checking dependencies...", total=None)
            deps_info = self._check_dependencies()
            progress.update(task2, completed=True)
            
            # Analyze code quality
            task3 = progress.add_task("Analyzing code quality...", total=None)
            quality_info = self._analyze_code_quality()
            progress.update(task3, completed=True)
            
            # Check configuration
            task4 = progress.add_task("Checking configuration...", total=None)
            config_info = self._check_configuration()
            progress.update(task4, completed=True)
        
        # Display results
        self._display_analysis_results(structure_info, deps_info, quality_info, config_info)
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the project directory structure."""
        structure = {
            "total_files": 0,
            "python_files": 0,
            "yaml_files": 0,
            "directories": 0,
            "size_mb": 0,
            "main_modules": []
        }
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            structure["directories"] += len(dirs)
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                structure["total_files"] += 1
                structure["size_mb"] += file_path.stat().st_size / (1024 * 1024)
                
                if file.endswith('.py'):
                    structure["python_files"] += 1
                elif file.endswith(('.yaml', '.yml')):
                    structure["yaml_files"] += 1
                
                # Check for main modules
                if file in ['main.py', '__init__.py', 'mecha.py', 'mecha-tui.py', 'mecha-docs.py']:
                    structure["main_modules"].append(str(file_path.relative_to(self.project_root)))
        
        return structure
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check project dependencies and their status."""
        deps_info = {
            "required_packages": [],
            "installed_packages": [],
            "missing_packages": [],
            "outdated_packages": []
        }
        
        # Define required packages
        required = ['rich', 'textual', 'typer', 'pyyaml', 'requests']
        deps_info["required_packages"] = required
        
        # Check installed packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            installed_lines = result.stdout.split('\n')[2:]  # Skip header
            
            installed = {}
            for line in installed_lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        installed[parts[0].lower()] = parts[1]
            
            for pkg in required:
                if pkg.lower() in installed:
                    deps_info["installed_packages"].append(f"{pkg} ({installed[pkg.lower()]})")
                else:
                    deps_info["missing_packages"].append(pkg)
                    
        except Exception as e:
            deps_info["error"] = str(e)
        
        return deps_info
    
    def _analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        quality = {
            "total_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "code_lines": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "docstrings": 0
        }
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                quality["total_lines"] += len(lines)
                
                in_docstring = False
                for line in lines:
                    stripped = line.strip()
                    
                    if not stripped:
                        quality["blank_lines"] += 1
                    elif stripped.startswith('#'):
                        quality["comment_lines"] += 1
                    elif '"""' in stripped or "'''" in stripped:
                        quality["docstrings"] += 1
                        in_docstring = not in_docstring
                    elif not in_docstring:
                        quality["code_lines"] += 1
                        
                        if stripped.startswith('def '):
                            quality["functions"] += 1
                        elif stripped.startswith('class '):
                            quality["classes"] += 1
                        elif stripped.startswith(('import ', 'from ')):
                            quality["imports"] += 1
                            
            except Exception:
                continue
        
        # Calculate ratios
        if quality["total_lines"] > 0:
            quality["comment_ratio"] = quality["comment_lines"] / quality["total_lines"]
            quality["docstring_ratio"] = quality["docstrings"] / quality["total_lines"]
        
        return quality
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration files and settings."""
        config = {
            "config_files": [],
            "yaml_files": [],
            "json_files": [],
            "env_files": [],
            "valid_configs": [],
            "invalid_configs": []
        }
        
        # Find configuration files
        config_patterns = ['*.yaml', '*.yml', '*.json', '*.env', '*.ini', '*.cfg']
        
        for pattern in config_patterns:
            for file_path in self.project_root.rglob(pattern):
                if '__pycache__' in str(file_path) or '.git' in str(file_path):
                    continue
                    
                rel_path = str(file_path.relative_to(self.project_root))
                config["config_files"].append(rel_path)
                
                # Categorize by type
                if file_path.suffix in ['.yaml', '.yml']:
                    config["yaml_files"].append(rel_path)
                    # Validate YAML
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                        config["valid_configs"].append(rel_path)
                    except Exception as e:
                        config["invalid_configs"].append(f"{rel_path}: {str(e)}")
                        
                elif file_path.suffix == '.json':
                    config["json_files"].append(rel_path)
                    # Validate JSON
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                        config["valid_configs"].append(rel_path)
                    except Exception as e:
                        config["invalid_configs"].append(f"{rel_path}: {str(e)}")
                        
                elif file_path.suffix == '.env':
                    config["env_files"].append(rel_path)
        
        return config
    
    def _display_analysis_results(self, structure, deps, quality, config):
        """Display the analysis results in a formatted way."""
        
        # Project Structure
        structure_table = Table(title="📁 Project Structure", border_style="blue")
        structure_table.add_column("Metric", style="cyan")
        structure_table.add_column("Value", style="white")
        
        structure_table.add_row("Total Files", str(structure["total_files"]))
        structure_table.add_row("Python Files", str(structure["python_files"]))
        structure_table.add_row("YAML Files", str(structure["yaml_files"]))
        structure_table.add_row("Directories", str(structure["directories"]))
        structure_table.add_row("Project Size", f"{structure['size_mb']:.2f} MB")
        
        self.console.print(structure_table)
        self.console.print()
        
        # Dependencies
        deps_table = Table(title="📦 Dependencies", border_style="green")
        deps_table.add_column("Status", style="cyan")
        deps_table.add_column("Packages", style="white")
        
        deps_table.add_row("Installed", ", ".join(deps["installed_packages"]) or "None")
        deps_table.add_row("Missing", ", ".join(deps["missing_packages"]) or "None")
        
        self.console.print(deps_table)
        self.console.print()
        
        # Code Quality
        quality_table = Table(title="📊 Code Quality", border_style="yellow")
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("Value", style="white")
        
        quality_table.add_row("Total Lines", str(quality["total_lines"]))
        quality_table.add_row("Code Lines", str(quality["code_lines"]))
        quality_table.add_row("Comment Lines", str(quality["comment_lines"]))
        quality_table.add_row("Functions", str(quality["functions"]))
        quality_table.add_row("Classes", str(quality["classes"]))
        
        if "comment_ratio" in quality:
            quality_table.add_row("Comment Ratio", f"{quality['comment_ratio']:.2%}")
        
        self.console.print(quality_table)
        self.console.print()
        
        # Configuration
        config_table = Table(title="⚙️ Configuration", border_style="magenta")
        config_table.add_column("Type", style="cyan")
        config_table.add_column("Count", style="white")
        
        config_table.add_row("YAML Files", str(len(config["yaml_files"])))
        config_table.add_row("JSON Files", str(len(config["json_files"])))
        config_table.add_row("Valid Configs", str(len(config["valid_configs"])))
        config_table.add_row("Invalid Configs", str(len(config["invalid_configs"])))
        
        self.console.print(config_table)
        
        if config["invalid_configs"]:
            self.console.print("\n[bold red]⚠️ Invalid Configuration Files:[/bold red]")
            for invalid in config["invalid_configs"]:
                self.console.print(f"  • {invalid}")
    
    def code_quality_tools(self):
        """Code quality and cleanup tools."""
        self.console.clear()
        
        header = Panel(
            "[bold yellow]🧹 Code Quality & Cleanup Tools[/bold yellow]",
            border_style="yellow"
        )
        self.console.print(header)
        
        # Submenu
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold cyan")
        table.add_column("Description")
        
        table.add_row("1", "🔍 Find Unused Imports")
        table.add_row("2", "📝 Check Docstring Coverage")
        table.add_row("3", "🧹 Remove Empty Files")
        table.add_row("4", "📊 Generate Code Metrics Report")
        table.add_row("5", "🔧 Fix Common Issues")
        table.add_row("b", "🔙 Back to Main Menu")
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "[bold]Select a tool[/bold]",
            choices=["1", "2", "3", "4", "5", "b"]
        )
        
        if choice == "1":
            self._find_unused_imports()
        elif choice == "2":
            self._check_docstring_coverage()
        elif choice == "3":
            self._remove_empty_files()
        elif choice == "4":
            self._generate_metrics_report()
        elif choice == "5":
            self._fix_common_issues()
        elif choice == "b":
            return
    
    def _find_unused_imports(self):
        """Find potentially unused imports in Python files."""
        self.console.print("\n[bold]🔍 Scanning for unused imports...[/bold]")
        
        unused_imports = []
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                imports = []
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        # Simple check - this could be more sophisticated
                        module_name = stripped.split()[1].split('.')[0]
                        if module_name not in content[len(line):]:  # Check if used after import
                            imports.append((i, stripped))
                
                if imports:
                    unused_imports.append((file_path, imports))
                    
            except Exception:
                continue
        
        if unused_imports:
            self.console.print(f"\n[yellow]Found potentially unused imports in {len(unused_imports)} files:[/yellow]")
            for file_path, imports in unused_imports:
                rel_path = file_path.relative_to(self.project_root)
                self.console.print(f"\n[cyan]{rel_path}:[/cyan]")
                for line_num, import_line in imports:
                    self.console.print(f"  Line {line_num}: {import_line}")
        else:
            self.console.print("\n[green]✅ No unused imports found![/green]")
    
    def _check_docstring_coverage(self):
        """Check docstring coverage for functions and classes."""
        self.console.print("\n[bold]📝 Checking docstring coverage...[/bold]")
        
        coverage_data = []
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                functions = 0
                classes = 0
                documented_functions = 0
                documented_classes = 0
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if line.startswith('def '):
                        functions += 1
                        # Check next few lines for docstring
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if '"""' in lines[j] or "'''" in lines[j]:
                                documented_functions += 1
                                break
                    
                    elif line.startswith('class '):
                        classes += 1
                        # Check next few lines for docstring
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if '"""' in lines[j] or "'''" in lines[j]:
                                documented_classes += 1
                                break
                    
                    i += 1
                
                if functions > 0 or classes > 0:
                    coverage_data.append({
                        'file': file_path.relative_to(self.project_root),
                        'functions': functions,
                        'documented_functions': documented_functions,
                        'classes': classes,
                        'documented_classes': documented_classes
                    })
                    
            except Exception:
                continue
        
        # Display results
        if coverage_data:
            table = Table(title="📝 Docstring Coverage Report", border_style="blue")
            table.add_column("File", style="cyan")
            table.add_column("Functions", justify="center")
            table.add_column("Documented", justify="center")
            table.add_column("Classes", justify="center")
            table.add_column("Documented", justify="center")
            table.add_column("Coverage", justify="center")
            
            total_items = 0
            total_documented = 0
            
            for data in coverage_data:
                items = data['functions'] + data['classes']
                documented = data['documented_functions'] + data['documented_classes']
                coverage = (documented / items * 100) if items > 0 else 0
                
                total_items += items
                total_documented += documented
                
                coverage_color = "green" if coverage >= 80 else "yellow" if coverage >= 50 else "red"
                
                table.add_row(
                    str(data['file']),
                    str(data['functions']),
                    str(data['documented_functions']),
                    str(data['classes']),
                    str(data['documented_classes']),
                    f"[{coverage_color}]{coverage:.1f}%[/{coverage_color}]"
                )
            
            self.console.print(table)
            
            overall_coverage = (total_documented / total_items * 100) if total_items > 0 else 0
            coverage_color = "green" if overall_coverage >= 80 else "yellow" if overall_coverage >= 50 else "red"
            
            self.console.print(f"\n[bold]Overall Coverage: [{coverage_color}]{overall_coverage:.1f}%[/{coverage_color}][/bold]")
        else:
            self.console.print("\n[yellow]No Python files with functions or classes found.[/yellow]")
    
    def _remove_empty_files(self):
        """Find and optionally remove empty files."""
        self.console.print("\n[bold]🧹 Scanning for empty files...[/bold]")
        
        empty_files = []
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size == 0:
                # Skip certain files that are meant to be empty
                if file_path.name not in ['__init__.py', '.gitkeep', '.keep']:
                    empty_files.append(file_path)
        
        if empty_files:
            self.console.print(f"\n[yellow]Found {len(empty_files)} empty files:[/yellow]")
            for file_path in empty_files:
                rel_path = file_path.relative_to(self.project_root)
                self.console.print(f"  • {rel_path}")
            
            if Confirm.ask("\nDo you want to remove these empty files?"):
                removed = 0
                for file_path in empty_files:
                    try:
                        file_path.unlink()
                        removed += 1
                    except Exception as e:
                        self.console.print(f"[red]Error removing {file_path}: {e}[/red]")
                
                self.console.print(f"\n[green]✅ Removed {removed} empty files.[/green]")
        else:
            self.console.print("\n[green]✅ No empty files found![/green]")
    
    def _generate_metrics_report(self):
        """Generate a comprehensive code metrics report."""
        self.console.print("\n[bold]📊 Generating code metrics report...[/bold]")
        
        # This would generate a detailed report and save it to a file
        report_path = self.logs_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write("Environment Dev Deep Evaluation - Code Metrics Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            
            # Add detailed metrics here
            f.write("This is a placeholder for detailed metrics.\n")
        
        self.console.print(f"\n[green]✅ Report saved to: {report_path}[/green]")
    
    def _fix_common_issues(self):
        """Fix common code issues automatically."""
        self.console.print("\n[bold]🔧 Scanning for common issues...[/bold]")
        
        issues_fixed = 0
        
        # Example: Remove trailing whitespace
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                modified = False
                new_lines = []
                
                for line in lines:
                    # Remove trailing whitespace
                    new_line = line.rstrip() + '\n' if line.endswith('\n') else line.rstrip()
                    new_lines.append(new_line)
                    
                    if new_line != line:
                        modified = True
                
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    issues_fixed += 1
                    
            except Exception:
                continue
        
        self.console.print(f"\n[green]✅ Fixed issues in {issues_fixed} files.[/green]")
    
    def build_automation(self):
        """Build and deployment automation tools."""
        self.console.clear()
        
        header = Panel(
            "[bold green]📦 Build & Deployment Automation[/bold green]",
            border_style="green"
        )
        self.console.print(header)
        
        # Implementation for build automation
        self.console.print("\n[dim]Build automation tools will be implemented here.[/dim]")
    
    def debugging_tools(self):
        """Debugging and diagnostic tools."""
        self.console.clear()
        
        header = Panel(
            "[bold red]🐛 Debugging & Diagnostic Tools[/bold red]",
            border_style="red"
        )
        self.console.print(header)
        
        # Implementation for debugging tools
        self.console.print("\n[dim]Debugging tools will be implemented here.[/dim]")
    
    def performance_monitoring(self):
        """Performance monitoring tools."""
        self.console.clear()
        
        header = Panel(
            "[bold yellow]📊 Performance Monitoring[/bold yellow]",
            border_style="yellow"
        )
        self.console.print(header)
        
        # Implementation for performance monitoring
        self.console.print("\n[dim]Performance monitoring tools will be implemented here.[/dim]")
    
    def backup_recovery(self):
        """Backup and recovery tools."""
        self.console.clear()
        
        header = Panel(
            "[bold blue]🔄 Backup & Recovery Tools[/bold blue]",
            border_style="blue"
        )
        self.console.print(header)
        
        # Submenu
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold cyan")
        table.add_column("Description")
        
        table.add_row("1", "💾 Create Project Backup")
        table.add_row("2", "📋 List Available Backups")
        table.add_row("3", "🔄 Restore from Backup")
        table.add_row("4", "🗑️ Clean Old Backups")
        table.add_row("b", "🔙 Back to Main Menu")
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "[bold]Select an option[/bold]",
            choices=["1", "2", "3", "4", "b"]
        )
        
        if choice == "1":
            self._create_backup()
        elif choice == "2":
            self._list_backups()
        elif choice == "3":
            self._restore_backup()
        elif choice == "4":
            self._clean_backups()
        elif choice == "b":
            return
    
    def _create_backup(self):
        """Create a project backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        self.console.print(f"\n[bold]💾 Creating backup: {backup_name}[/bold]")
        
        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Copy important files and directories
            important_items = ['core', 'cli', 'tui', 'docs', 'tools', '*.py', '*.yaml', '*.yml']
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                
                task = progress.add_task("Creating backup...", total=len(important_items))
                
                for item in important_items:
                    if '*' in item:
                        # Handle glob patterns
                        for file_path in self.project_root.glob(item):
                            if file_path.is_file():
                                shutil.copy2(file_path, backup_path / file_path.name)
                    else:
                        # Handle directories and specific files
                        item_path = self.project_root / item
                        if item_path.exists():
                            if item_path.is_dir():
                                shutil.copytree(item_path, backup_path / item, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item_path, backup_path / item)
                    
                    progress.update(task, advance=1)
            
            # Create backup info file
            info_file = backup_path / "backup_info.json"
            backup_info = {
                "timestamp": timestamp,
                "created": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "items_backed_up": important_items
            }
            
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.console.print(f"\n[green]✅ Backup created successfully: {backup_path}[/green]")
            
        except Exception as e:
            self.console.print(f"\n[red]❌ Error creating backup: {e}[/red]")
    
    def _list_backups(self):
        """List available backups."""
        self.console.print("\n[bold]📋 Available Backups[/bold]")
        
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                info_file = backup_dir / "backup_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            info = json.load(f)
                        backups.append((backup_dir, info))
                    except Exception:
                        backups.append((backup_dir, {"created": "Unknown"}))
                else:
                    backups.append((backup_dir, {"created": "Unknown"}))
        
        if backups:
            table = Table(border_style="blue")
            table.add_column("Backup Name", style="cyan")
            table.add_column("Created", style="white")
            table.add_column("Size", style="yellow")
            
            for backup_dir, info in sorted(backups, key=lambda x: x[1].get('created', ''), reverse=True):
                # Calculate backup size
                size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                
                created = info.get('created', 'Unknown')
                if created != 'Unknown':
                    try:
                        created_dt = datetime.fromisoformat(created)
                        created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                
                table.add_row(
                    backup_dir.name,
                    created,
                    f"{size_mb:.2f} MB"
                )
            
            self.console.print(table)
        else:
            self.console.print("\n[yellow]No backups found.[/yellow]")
    
    def _restore_backup