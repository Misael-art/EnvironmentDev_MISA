#!/usr/bin/env python3
"""
CLI Autocompletion and Shell Integration

Provides shell completion functionality for the Environment Dev CLI,
including bash, zsh, and PowerShell completion support.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class CompletionManager:
    """Manages shell completion functionality for the CLI."""
    
    def __init__(self):
        """Initialize the completion manager."""
        self.app_name = "mecha"
        self.supported_shells = ["bash", "zsh", "fish", "powershell"]
        self.completion_dir = Path.home() / ".mecha" / "completions"
        self.completion_dir.mkdir(parents=True, exist_ok=True)
    
    def get_component_names(self, incomplete: str = "") -> List[str]:
        """Get list of available component names for completion.
        
        Args:
            incomplete: Partial component name being typed
            
        Returns:
            List of matching component names
        """
        components_dir = Path("components")
        if not components_dir.exists():
            return []
        
        component_names = []
        for yaml_file in components_dir.glob("*.yaml"):
            name = yaml_file.stem
            if incomplete.lower() in name.lower():
                component_names.append(name)
        
        return sorted(component_names)
    
    def get_categories(self, incomplete: str = "") -> List[str]:
        """Get list of available categories for completion.
        
        Args:
            incomplete: Partial category name being typed
            
        Returns:
            List of matching categories
        """
        categories = [
            "web", "database", "development", "tools", "security",
            "monitoring", "deployment", "testing", "documentation"
        ]
        
        return [cat for cat in categories if incomplete.lower() in cat.lower()]
    
    def get_commands(self, incomplete: str = "") -> List[str]:
        """Get list of available commands for completion.
        
        Args:
            incomplete: Partial command name being typed
            
        Returns:
            List of matching commands
        """
        commands = [
            "init", "list-components", "search", "info", "install",
            "uninstall", "update", "validate", "doctor", "version",
            "categories", "export", "import", "backup", "restore"
        ]
        
        return [cmd for cmd in commands if incomplete.lower() in cmd.lower()]
    
    def generate_bash_completion(self) -> str:
        """Generate bash completion script.
        
        Returns:
            Bash completion script content
        """
        return f'''
# Bash completion for {self.app_name}
_mecha_completion() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    
    # Main commands
    if [[ ${{COMP_CWORD}} == 1 ]]; then
        opts="init list-components search info install uninstall update validate doctor version categories export import backup restore"
        COMPREPLY=( $(compgen -W "${{opts}}" -- ${{cur}}) )
        return 0
    fi
    
    # Component names for relevant commands
    case "${{prev}}" in
        info|install|uninstall|update)
            local components=$(python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print(' '.join(cm.get_component_names()))" 2>/dev/null)
            COMPREPLY=( $(compgen -W "${{components}}" -- ${{cur}}) )
            return 0
            ;;
        search)
            # For search, we can suggest categories
            local categories=$(python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print(' '.join(cm.get_categories()))" 2>/dev/null)
            COMPREPLY=( $(compgen -W "${{categories}}" -- ${{cur}}) )
            return 0
            ;;
    esac
    
    # File completion as fallback
    COMPREPLY=( $(compgen -f -- ${{cur}}) )
}}

complete -F _mecha_completion mecha
complete -F _mecha_completion python mecha.py
'''
    
    def generate_zsh_completion(self) -> str:
        """Generate zsh completion script.
        
        Returns:
            Zsh completion script content
        """
        return f'''
#compdef {self.app_name}

_mecha() {{
    local context state line
    typeset -A opt_args
    
    _arguments -C \
        '1: :_mecha_commands' \
        '*: :_mecha_args'
}}

_mecha_commands() {{
    local commands
    commands=(
        'init:Initialize the system'
        'list-components:List available components'
        'search:Search for components'
        'info:Show component information'
        'install:Install a component'
        'uninstall:Uninstall a component'
        'update:Update a component'
        'validate:Validate components'
        'doctor:System diagnostics'
        'version:Show version information'
        'categories:List component categories'
        'export:Export configuration'
        'import:Import configuration'
        'backup:Create backup'
        'restore:Restore from backup'
    )
    _describe 'commands' commands
}}

_mecha_args() {{
    case $words[2] in
        info|install|uninstall|update)
            _mecha_components
            ;;
        search)
            _mecha_categories
            ;;
        *)
            _files
            ;;
    esac
}}

_mecha_components() {{
    local components
    components=($(python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print('\\n'.join(cm.get_component_names()))" 2>/dev/null))
    _describe 'components' components
}}

_mecha_categories() {{
    local categories
    categories=($(python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print('\\n'.join(cm.get_categories()))" 2>/dev/null))
    _describe 'categories' categories
}}

_mecha
'''
    
    def generate_powershell_completion(self) -> str:
        """Generate PowerShell completion script.
        
        Returns:
            PowerShell completion script content
        """
        return f'''
# PowerShell completion for {self.app_name}
Register-ArgumentCompleter -Native -CommandName mecha -ScriptBlock {{
    param($commandName, $wordToComplete, $cursorPosition)
    
    $commands = @(
        'init', 'list-components', 'search', 'info', 'install',
        'uninstall', 'update', 'validate', 'doctor', 'version',
        'categories', 'export', 'import', 'backup', 'restore'
    )
    
    $line = $wordToComplete
    $words = $line -split ' '
    
    if ($words.Count -eq 1) {{
        # Complete main commands
        $commands | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
    }}
    elseif ($words.Count -eq 2) {{
        $command = $words[0]
        switch ($command) {{
            {{ 'info', 'install', 'uninstall', 'update' -contains $_ }} {{
                # Complete component names
                try {{
                    $components = python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print('\\n'.join(cm.get_component_names()))" 2>$null
                    if ($components) {{
                        $components -split '\\n' | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
                            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                        }}
                    }}
                }} catch {{}}
            }}
            'search' {{
                # Complete categories
                try {{
                    $categories = python -c "from cli.completion import CompletionManager; cm = CompletionManager(); print('\\n'.join(cm.get_categories()))" 2>$null
                    if ($categories) {{
                        $categories -split '\\n' | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
                            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                        }}
                    }}
                }} catch {{}}
            }}
        }}
    }}
}}
'''
    
    def install_completion(self, shell: str) -> bool:
        """Install completion for specified shell.
        
        Args:
            shell: Shell type (bash, zsh, fish, powershell)
            
        Returns:
            True if installation was successful
        """
        if shell not in self.supported_shells:
            console.print(f"[red]❌ Unsupported shell: {shell}[/red]")
            return False
        
        try:
            if shell == "bash":
                content = self.generate_bash_completion()
                completion_file = self.completion_dir / "mecha_completion.bash"
                
            elif shell == "zsh":
                content = self.generate_zsh_completion()
                completion_file = self.completion_dir / "_mecha"
                
            elif shell == "powershell":
                content = self.generate_powershell_completion()
                completion_file = self.completion_dir / "mecha_completion.ps1"
            
            # Write completion file
            with open(completion_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Display installation instructions
            self._show_installation_instructions(shell, completion_file)
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error installing completion: {e}[/red]")
            return False
    
    def _show_installation_instructions(self, shell: str, completion_file: Path):
        """Show installation instructions for the completion script.
        
        Args:
            shell: Shell type
            completion_file: Path to the completion file
        """
        instructions = {
            "bash": f"""
To enable bash completion, add this line to your ~/.bashrc:
source {completion_file}

Or run: echo 'source {completion_file}' >> ~/.bashrc
""",
            "zsh": f"""
To enable zsh completion:
1. Ensure {completion_file.parent} is in your $fpath
2. Add this line to your ~/.zshrc:
fpath=({completion_file.parent} $fpath)
autoload -U compinit && compinit
""",
            "powershell": f"""
To enable PowerShell completion, add this line to your PowerShell profile:
. {completion_file}

To find your profile location, run: $PROFILE
"""
        }
        
        panel = Panel(
            instructions.get(shell, "Manual installation required"),
            title=f"📋 {shell.title()} Completion Installation",
            border_style="green"
        )
        console.print(panel)

# Completion functions for Typer
def complete_component_name(incomplete: str) -> List[str]:
    """Completion function for component names.
    
    Args:
        incomplete: Partial component name
        
    Returns:
        List of matching component names
    """
    cm = CompletionManager()
    return cm.get_component_names(incomplete)

def complete_category(incomplete: str) -> List[str]:
    """Completion function for categories.
    
    Args:
        incomplete: Partial category name
        
    Returns:
        List of matching categories
    """
    cm = CompletionManager()
    return cm.get_categories(incomplete)

def complete_shell(incomplete: str) -> List[str]:
    """Completion function for shell types.
    
    Args:
        incomplete: Partial shell name
        
    Returns:
        List of matching shell types
    """
    shells = ["bash", "zsh", "fish", "powershell"]
    return [shell for shell in shells if incomplete.lower() in shell.lower()]

# CLI command for managing completions
def completion_command(
    action: str = typer.Argument(
        ..., 
        help="Action to perform: install, uninstall, list",
        autocompletion=lambda: ["install", "uninstall", "list"]
    ),
    shell: Optional[str] = typer.Option(
        None,
        "--shell", "-s",
        help="Shell type for completion",
        autocompletion=complete_shell
    )
):
    """Manage shell completion for the CLI.
    
    Args:
        action: Action to perform (install, uninstall, list)
        shell: Shell type (bash, zsh, fish, powershell)
    """
    cm = CompletionManager()
    
    if action == "list":
        console.print("[bold]📋 Supported Shells:[/bold]")
        for shell_type in cm.supported_shells:
            console.print(f"  • {shell_type}")
    
    elif action == "install":
        if not shell:
            # Try to detect shell
            shell = os.environ.get('SHELL', '').split('/')[-1]
            if not shell or shell not in cm.supported_shells:
                console.print("[yellow]⚠️ Could not detect shell. Please specify with --shell[/yellow]")
                return
        
        console.print(f"[bold]📦 Installing completion for {shell}...[/bold]")
        if cm.install_completion(shell):
            console.print(f"[green]✅ Completion installed for {shell}[/green]")
        else:
            console.print(f"[red]❌ Failed to install completion for {shell}[/red]")
    
    elif action == "uninstall":
        console.print("[yellow]🗑️ Uninstall functionality not yet implemented[/yellow]")
    
    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]")

if __name__ == "__main__":
    # Test completion functionality
    cm = CompletionManager()
    print("Available components:", cm.get_component_names())
    print("Available categories:", cm.get_categories())