#!/usr/bin/env python3
"""
CLI Commands module for Environment Dev Deep Evaluation.

Provides specialized command implementations for component management,
system operations, and development workflows.
"""

import typer
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm, Prompt, IntPrompt
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich import print as rprint
import yaml
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import ConfigurationManager
from core.exceptions import EnvironmentDevDeepEvaluationError

console = Console()


class ComponentManager:
    """Manages component operations and data."""
    
    def __init__(self):
        """Initialize the component manager."""
        self.components_dir = Path("components")
        self.config_manager = ConfigurationManager()
    
    def load_components(self) -> Dict[str, Dict[str, Any]]:
        """Load all components from YAML files.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of component data
        """
        components = {}
        
        if not self.components_dir.exists():
            return components
        
        for yaml_file in self.components_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    components.update(data)
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Warning: Could not load {yaml_file}: {e}[/yellow]")
                continue
        
        return components
    
    def get_component_categories(self) -> List[str]:
        """Get all available component categories.
        
        Returns:
            List[str]: List of unique categories
        """
        components = self.load_components()
        categories = set()
        
        for component_data in components.values():
            if isinstance(component_data, dict) and 'category' in component_data:
                categories.add(component_data['category'])
        
        return sorted(list(categories))
    
    def search_components(self, query: str) -> Dict[str, Dict[str, Any]]:
        """Search components by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            Dict[str, Dict[str, Any]]: Matching components
        """
        components = self.load_components()
        results = {}
        
        query_lower = query.lower()
        
        for name, data in components.items():
            if isinstance(data, dict):
                # Search in name
                if query_lower in name.lower():
                    results[name] = data
                    continue
                
                # Search in description
                description = data.get('description', '').lower()
                if query_lower in description:
                    results[name] = data
                    continue
                
                # Search in tags
                tags = data.get('tags', [])
                if isinstance(tags, list):
                    for tag in tags:
                        if query_lower in str(tag).lower():
                            results[name] = data
                            break
        
        return results


def search_command(
    query: str = typer.Argument(..., help="Search query for components"),
    category: Optional[str] = typer.Option(
        None, 
        "--category", 
        "-c", 
        help="Filter by category"
    )
):
    """
    🔍 Search for components by name, description, or tags.
    
    Performs a comprehensive search across all component metadata
    to help you find the tools you need.
    """
    try:
        manager = ComponentManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching components...", total=None)
            
            # Search components
            results = manager.search_components(query)
            
            # Apply category filter if specified
            if category:
                filtered_results = {}
                for name, data in results.items():
                    if isinstance(data, dict) and data.get('category', '').lower() == category.lower():
                        filtered_results[name] = data
                results = filtered_results
        
        if not results:
            console.print(f"[yellow]📭 No components found matching '{query}'[/yellow]")
            
            # Suggest similar categories
            categories = manager.get_component_categories()
            if categories:
                console.print("\n[dim]Available categories:[/dim]")
                for cat in categories:
                    console.print(f"  • {cat}")
            return
        
        # Display results
        table = Table(title=f"🔍 Search Results for '{query}'")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Version", style="green")
        table.add_column("Tags", style="blue")
        
        for name, data in results.items():
            if isinstance(data, dict):
                tags = data.get('tags', [])
                tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                
                table.add_row(
                    name,
                    data.get('category', 'Unknown'),
                    data.get('description', 'No description')[:50] + "..." if len(data.get('description', '')) > 50 else data.get('description', 'No description'),
                    data.get('version', 'Unknown'),
                    tags_str[:30] + "..." if len(tags_str) > 30 else tags_str
                )
        
        console.print(table)
        console.print(f"\n[dim]Found {len(results)} components[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Search failed: {e}[/red]")
        raise typer.Exit(1)


def info_command(
    component: str = typer.Argument(..., help="Name of the component to show info for")
):
    """
    ℹ️ Show detailed information about a specific component.
    
    Displays comprehensive information including dependencies,
    installation requirements, and configuration options.
    """
    try:
        manager = ComponentManager()
        components = manager.load_components()
        
        if component not in components:
            console.print(f"[red]❌ Component '{component}' not found[/red]")
            
            # Suggest similar components
            similar = manager.search_components(component)
            if similar:
                console.print("\n[yellow]Did you mean one of these?[/yellow]")
                for name in list(similar.keys())[:5]:
                    console.print(f"  • {name}")
            
            raise typer.Exit(1)
        
        data = components[component]
        
        # Component header
        header = Panel(
            f"[bold cyan]{component}[/bold cyan]\n"
            f"[dim]{data.get('description', 'No description available')}[/dim]",
            title="Component Information",
            border_style="cyan"
        )
        console.print(header)
        console.print()
        
        # Basic information
        info_table = Table(title="Basic Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Category", data.get('category', 'Unknown'))
        info_table.add_row("Version", data.get('version', 'Unknown'))
        info_table.add_row("License", data.get('license', 'Unknown'))
        info_table.add_row("Homepage", data.get('homepage', 'Not specified'))
        
        # Tags
        tags = data.get('tags', [])
        if isinstance(tags, list) and tags:
            info_table.add_row("Tags", ", ".join(tags))
        
        console.print(info_table)
        console.print()
        
        # Installation information
        if 'installation' in data:
            install_data = data['installation']
            
            install_table = Table(title="Installation Information")
            install_table.add_column("Property", style="cyan")
            install_table.add_column("Value", style="white")
            
            if 'method' in install_data:
                install_table.add_row("Method", install_data['method'])
            
            if 'url' in install_data:
                install_table.add_row("Download URL", install_data['url'])
            
            if 'hash' in install_data:
                hash_value = install_data['hash']
                if len(hash_value) > 50:
                    hash_value = hash_value[:47] + "..."
                install_table.add_row("SHA256 Hash", hash_value)
            
            if 'size' in install_data:
                install_table.add_row("Size", install_data['size'])
            
            console.print(install_table)
            console.print()
        
        # Dependencies
        if 'dependencies' in data:
            deps = data['dependencies']
            if isinstance(deps, list) and deps:
                deps_panel = Panel(
                    "\n".join([f"• {dep}" for dep in deps]),
                    title="Dependencies",
                    border_style="yellow"
                )
                console.print(deps_panel)
                console.print()
        
        # Configuration
        if 'configuration' in data:
            config_data = data['configuration']
            if isinstance(config_data, dict):
                config_panel = Panel(
                    "\n".join([f"• {key}: {value}" for key, value in config_data.items()]),
                    title="Configuration Options",
                    border_style="green"
                )
                console.print(config_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Error showing component info: {e}[/red]")
        raise typer.Exit(1)


def categories_command():
    """
    📂 List all available component categories.
    
    Shows a comprehensive overview of component categories
    with counts and descriptions.
    """
    try:
        manager = ComponentManager()
        components = manager.load_components()
        categories = {}
        
        # Count components by category
        for component_data in components.values():
            if isinstance(component_data, dict):
                category = component_data.get('category', 'Unknown')
                if category not in categories:
                    categories[category] = {
                        'count': 0,
                        'components': []
                    }
                categories[category]['count'] += 1
                categories[category]['components'].append(component_data.get('name', 'Unknown'))
        
        if not categories:
            console.print("[yellow]📭 No categories found[/yellow]")
            return
        
        # Display categories
        table = Table(title="📂 Component Categories")
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("Description", style="white")
        
        # Category descriptions
        category_descriptions = {
            'ai_tools': 'Artificial Intelligence and Machine Learning tools',
            'dev_tools': 'Development and programming utilities',
            'system_tools': 'System administration and management tools',
            'productivity': 'Productivity and workflow enhancement tools',
            'security': 'Security and privacy tools',
            'multimedia': 'Audio, video, and image processing tools',
            'network': 'Network and communication tools',
            'database': 'Database management and tools',
            'cloud': 'Cloud services and deployment tools',
            'Unknown': 'Uncategorized components'
        }
        
        for category, data in sorted(categories.items()):
            description = category_descriptions.get(category, 'No description available')
            table.add_row(
                category,
                str(data['count']),
                description
            )
        
        console.print(table)
        console.print(f"\n[dim]Total categories: {len(categories)}[/dim]")
        
        # Show category tree
        if Confirm.ask("\n🌳 Would you like to see a detailed category tree?"):
            tree = Tree("📂 Component Categories")
            
            for category, data in sorted(categories.items()):
                category_branch = tree.add(f"[cyan]{category}[/cyan] ({data['count']} components)")
                
                # Show first few components
                components_to_show = data['components'][:5]
                for component in components_to_show:
                    category_branch.add(f"[dim]{component}[/dim]")
                
                if len(data['components']) > 5:
                    category_branch.add(f"[dim]... and {len(data['components']) - 5} more[/dim]")
            
            console.print(tree)
        
    except Exception as e:
        console.print(f"[red]❌ Error listing categories: {e}[/red]")
        raise typer.Exit(1)


def export_command(
    format: str = typer.Option(
        "json", 
        "--format", 
        "-f", 
        help="Export format (json, yaml, csv)"
    ),
    output: Optional[str] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="Output file path"
    ),
    category: Optional[str] = typer.Option(
        None, 
        "--category", 
        "-c", 
        help="Export only specific category"
    )
):
    """
    📤 Export component data to various formats.
    
    Exports component information to JSON, YAML, or CSV format
    for external processing or backup purposes.
    """
    try:
        manager = ComponentManager()
        components = manager.load_components()
        
        # Filter by category if specified
        if category:
            filtered_components = {}
            for name, data in components.items():
                if isinstance(data, dict) and data.get('category', '').lower() == category.lower():
                    filtered_components[name] = data
            components = filtered_components
        
        if not components:
            console.print("[yellow]📭 No components to export[/yellow]")
            return
        
        # Generate output filename if not specified
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            category_suffix = f"_{category}" if category else ""
            output = f"components_export{category_suffix}_{timestamp}.{format}"
        
        # Export data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Exporting to {format.upper()}...", total=None)
            
            if format.lower() == 'json':
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(components, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'yaml':
                with open(output, 'w', encoding='utf-8') as f:
                    yaml.dump(components, f, default_flow_style=False, allow_unicode=True)
            
            elif format.lower() == 'csv':
                import csv
                with open(output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow(['Name', 'Category', 'Version', 'Description', 'License', 'Homepage'])
                    
                    # Write data
                    for name, data in components.items():
                        if isinstance(data, dict):
                            writer.writerow([
                                name,
                                data.get('category', ''),
                                data.get('version', ''),
                                data.get('description', ''),
                                data.get('license', ''),
                                data.get('homepage', '')
                            ])
            
            else:
                console.print(f"[red]❌ Unsupported format: {format}[/red]")
                raise typer.Exit(1)
        
        # Success message
        success_panel = Panel(
            f"[green]✅ Export completed successfully![/green]\n\n"
            f"📁 File: {output}\n"
            f"📊 Format: {format.upper()}\n"
            f"🔢 Components: {len(components)}",
            title="Export Complete",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")
        raise typer.Exit(1)


def validate_command(
    component: Optional[str] = typer.Argument(
        None, 
        help="Specific component to validate (validates all if not specified)"
    ),
    fix: bool = typer.Option(
        False, 
        "--fix", 
        "-f", 
        help="Attempt to fix validation errors automatically"
    )
):
    """
    ✅ Validate component definitions and integrity.
    
    Performs comprehensive validation of component YAML files,
    checking for schema compliance, hash integrity, and dependencies.
    """
    try:
        manager = ComponentManager()
        
        if component:
            # Validate specific component
            components = manager.load_components()
            if component not in components:
                console.print(f"[red]❌ Component '{component}' not found[/red]")
                raise typer.Exit(1)
            
            components_to_validate = {component: components[component]}
        else:
            # Validate all components
            components_to_validate = manager.load_components()
        
        if not components_to_validate:
            console.print("[yellow]📭 No components to validate[/yellow]")
            return
        
        validation_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Validating components...", total=len(components_to_validate))
            
            for name, data in components_to_validate.items():
                progress.update(task, description=f"Validating {name}...")
                
                errors = []
                warnings = []
                
                # Basic structure validation
                if not isinstance(data, dict):
                    errors.append("Component data is not a dictionary")
                else:
                    # Required fields
                    required_fields = ['category', 'description', 'version']
                    for field in required_fields:
                        if field not in data:
                            errors.append(f"Missing required field: {field}")
                    
                    # Hash validation
                    if 'installation' in data and isinstance(data['installation'], dict):
                        hash_value = data['installation'].get('hash', '')
                        if hash_value in ['HASH_NEEDS_UPDATE', 'HASH_PENDENTE_VERIFICACAO']:
                            warnings.append(f"Hash needs update: {hash_value}")
                        elif not hash_value:
                            warnings.append("No hash specified for installation")
                    
                    # URL validation
                    if 'installation' in data and isinstance(data['installation'], dict):
                        url = data['installation'].get('url', '')
                        if not url:
                            warnings.append("No download URL specified")
                        elif not url.startswith(('http://', 'https://')):
                            errors.append(f"Invalid URL format: {url}")
                
                validation_results.append({
                    'name': name,
                    'errors': errors,
                    'warnings': warnings
                })
                
                progress.advance(task)
        
        # Display results
        total_errors = sum(len(result['errors']) for result in validation_results)
        total_warnings = sum(len(result['warnings']) for result in validation_results)
        
        if total_errors == 0 and total_warnings == 0:
            success_panel = Panel(
                "[green]✅ All components passed validation![/green]\n\n"
                f"🔍 Validated {len(components_to_validate)} components\n"
                "🎉 No errors or warnings found",
                title="Validation Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            # Show detailed results
            table = Table(title="🔍 Validation Results")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Issues", style="yellow")
            
            for result in validation_results:
                status_parts = []
                issues_parts = []
                
                if result['errors']:
                    status_parts.append(f"[red]{len(result['errors'])} errors[/red]")
                    issues_parts.extend([f"❌ {error}" for error in result['errors']])
                
                if result['warnings']:
                    status_parts.append(f"[yellow]{len(result['warnings'])} warnings[/yellow]")
                    issues_parts.extend([f"⚠️ {warning}" for warning in result['warnings']])
                
                if not status_parts:
                    status_parts.append("[green]✅ OK[/green]")
                    issues_parts.append("No issues found")
                
                table.add_row(
                    result['name'],
                    " | ".join(status_parts),
                    "\n".join(issues_parts)
                )
            
            console.print(table)
            
            # Summary
            summary_panel = Panel(
                f"📊 Validation Summary\n\n"
                f"🔍 Components validated: {len(components_to_validate)}\n"
                f"❌ Total errors: {total_errors}\n"
                f"⚠️ Total warnings: {total_warnings}",
                title="Summary",
                border_style="blue"
            )
            console.print(summary_panel)
            
            if fix and (total_errors > 0 or total_warnings > 0):
                if Confirm.ask("\n🔧 Would you like to attempt automatic fixes?"):
                    console.print("[yellow]🔧 Automatic fixing is not yet implemented[/yellow]")
                    console.print("[dim]This feature will be available in a future update[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1)