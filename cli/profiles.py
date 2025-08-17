#!/usr/bin/env python3
"""
Profile management for Environment Dev Deep Evaluation CLI.

Provides commands for creating, managing, and using component profiles.
"""

import typer
import yaml
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from core.config import ConfigurationManager

console = Console()

app = typer.Typer(
    name="profiles",
    help="Gerenciar perfis de componentes",
    rich_markup_mode="rich"
)

def get_profiles_dir() -> Path:
    """Get the profiles directory path."""
    config_manager = ConfigurationManager()
    config = config_manager.get_config()
    profiles_dir = Path(config.base_directory) / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir

def load_profile(profile_name: str) -> Dict[str, Any]:
    """Load a profile from file."""
    profiles_dir = get_profiles_dir()
    profile_file = profiles_dir / f"{profile_name}.yaml"
    
    if not profile_file.exists():
        raise FileNotFoundError(f"Profile '{profile_name}' not found")
    
    with open(profile_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_profile(profile_name: str, components: List[str], description: str = "") -> None:
    """Save a profile to file."""
    profiles_dir = get_profiles_dir()
    profile_file = profiles_dir / f"{profile_name}.yaml"
    
    profile_data = {
        "name": profile_name,
        "description": description,
        "components": components,
        "created_at": __import__('datetime').datetime.now().isoformat()
    }
    
    with open(profile_file, 'w', encoding='utf-8') as f:
        yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)

@app.command()
def create(
    name: str = typer.Argument(..., help="Nome do perfil"),
    components: List[str] = typer.Option([], "--component", "-c", help="Componentes para incluir no perfil"),
    from_installed: bool = typer.Option(False, "--from-installed", help="Criar perfil a partir de componentes instalados"),
    description: str = typer.Option("", "--description", "-d", help="Descrição do perfil")
):
    """
    📝 Criar um novo perfil de componentes.
    
    Cria um perfil com os componentes especificados ou a partir dos componentes instalados.
    """
    try:
        if from_installed:
            # Get installed components using the detection engine
            from detection.unified_engine import UnifiedDetectionEngine
            config_manager = ConfigurationManager()
            engine = UnifiedDetectionEngine(config_manager)
            engine.initialize()
            
            # Load all components
            components_dir = Path("components")
            all_components = []
            for yaml_file in components_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        all_components.extend(data.keys())
                except Exception:
                    continue
            
            # Analyze gaps to find installed components
            gap_report = engine.analyze_environment_gaps(all_components)
            components = gap_report.present
            
            if not components:
                console.print("[yellow]⚠️ Nenhum componente instalado encontrado[/yellow]")
                return
        
        if not components:
            # Interactive mode to select components
            components = _interactive_component_selection()
        
        if not components:
            console.print("[yellow]⚠️ Nenhum componente selecionado[/yellow]")
            return
        
        # Save profile
        save_profile(name, components, description)
        
        success_panel = Panel(
            f"[green]✅ Perfil '{name}' criado com sucesso![/green]\n\n"
            f"📁 Arquivo: {get_profiles_dir() / f'{name}.yaml'}\n"
            f"📊 Componentes: {len(components)}\n"
            f"📝 Descrição: {description or 'Nenhuma'}",
            title="Perfil Criado",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Falha ao criar perfil: {e}[/red]")
        raise typer.Exit(1)

def _interactive_component_selection() -> List[str]:
    """Interactive component selection."""
    # Load all available components
    components_dir = Path("components")
    all_components = []
    for yaml_file in components_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                all_components.extend([(name, data[name].get('description', '')) for name in data.keys()])
        except Exception:
            continue
    
    if not all_components:
        console.print("[yellow]⚠️ Nenhum componente encontrado[/yellow]")
        return []
    
    # Sort components by name
    all_components.sort(key=lambda x: x[0])
    
    # Display components in a table
    table = Table(title="Componentes Disponíveis")
    table.add_column("Selecionar", style="cyan", no_wrap=True)
    table.add_column("Componente", style="white")
    table.add_column("Descrição", style="dim")
    
    for i, (name, description) in enumerate(all_components, start=1):
        table.add_row(str(i), name, description[:50] + "..." if len(description) > 50 else description)
    
    console.print(table)
    
    # Get user selection
    selected_indices = Prompt.ask(
        "\nDigite os números dos componentes separados por vírgula (ex: 1,3,5) ou 'all' para todos"
    )
    
    if selected_indices.lower() == 'all':
        return [name for name, _ in all_components]
    
    try:
        indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
        selected_components = [all_components[i][0] for i in indices if 0 <= i < len(all_components)]
        return selected_components
    except Exception:
        console.print("[red]❌ Entrada inválida[/red]")
        return []

@app.command()
def list_profiles():
    """
    📋 Listar todos os perfis disponíveis.
    
    Exibe uma lista de todos os perfis de componentes criados.
    """
    try:
        profiles_dir = get_profiles_dir()
        profiles = list(profiles_dir.glob("*.yaml"))
        
        if not profiles:
            console.print("[yellow]📭 Nenhum perfil encontrado[/yellow]")
            return
        
        table = Table(title=" Perfis de Componentes")
        table.add_column("Nome", style="cyan", no_wrap=True)
        table.add_column("Descrição", style="white")
        table.add_column("Componentes", style="green", justify="right")
        table.add_column("Criado em", style="dim")
        
        for profile_file in sorted(profiles):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
                
                name = profile_data.get('name', profile_file.stem)
                description = profile_data.get('description', '')
                components = profile_data.get('components', [])
                created_at = profile_data.get('created_at', 'Desconhecido')
                
                table.add_row(
                    name,
                    description,
                    str(len(components)),
                    created_at
                )
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao ler perfil {profile_file.name}: {e}[/yellow]")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Falha ao listar perfis: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def show(
    name: str = typer.Argument(..., help="Nome do perfil")
):
    """
    👁️ Mostrar detalhes de um perfil.
    
    Exibe os componentes e informações detalhadas de um perfil específico.
    """
    try:
        profile_data = load_profile(name)
        
        # Profile header
        header = Panel(
            f"[bold cyan]{profile_data.get('name', name)}[/bold cyan]\n"
            f"[dim]{profile_data.get('description', 'Nenhuma descrição')}[/dim]",
            title="Perfil de Componentes",
            border_style="cyan"
        )
        console.print(header)
        console.print()
        
        # Components list
        components = profile_data.get('components', [])
        if not components:
            console.print("[yellow]📭 Nenhum componente no perfil[/yellow]")
            return
        
        table = Table(title="Componentes no Perfil")
        table.add_column("Componente", style="cyan")
        
        for component in sorted(components):
            table.add_row(component)
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(components)} componentes[/dim]")
        
        # Installation command
        install_cmd = f"mecha install-many {' '.join(components)}"
        console.print(f"\n[bold]Comando de instalação:[/bold]")
        console.print(f"[green]{install_cmd}[/green]")
        
    except FileNotFoundError:
        console.print(f"[red]❌ Perfil '{name}' não encontrado[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Falha ao mostrar perfil: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def delete(
    name: str = typer.Argument(..., help="Nome do perfil"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirmar exclusão sem perguntar")
):
    """
    🗑️ Excluir um perfil.
    
    Remove um perfil de componentes do sistema.
    """
    try:
        profiles_dir = get_profiles_dir()
        profile_file = profiles_dir / f"{name}.yaml"
        
        if not profile_file.exists():
            console.print(f"[red]❌ Perfil '{name}' não encontrado[/red]")
            raise typer.Exit(1)
        
        if not confirm:
            if not Confirm.ask(f"Excluir o perfil '{name}'?"):
                console.print("[yellow]Operação cancelada[/yellow]")
                return
        
        profile_file.unlink()
        
        console.print(f"[green]✅ Perfil '{name}' excluído com sucesso![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Falha ao excluir perfil: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def export_profile(
    name: str = typer.Argument(..., help="Nome do perfil"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Arquivo de saída"),
    format: str = typer.Option("yaml", "--format", "-f", help="Formato de saída (yaml, json)")
):
    """
    📤 Exportar um perfil para arquivo.
    
    Exporta um perfil de componentes para um arquivo em formato YAML ou JSON.
    """
    try:
        profile_data = load_profile(name)
        
        # Generate output filename if not specified
        if not output:
            output = f"{name}_export.{format}"
        
        output_path = Path(output)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)
        
        console.print(f"[green]✅ Perfil exportado para:[/green] {output_path}")
        
    except FileNotFoundError:
        console.print(f"[red]❌ Perfil '{name}' não encontrado[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Falha ao exportar perfil: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def import_profile(
    file: str = typer.Argument(..., help="Arquivo de perfil para importar"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Nome do perfil (usará nome do arquivo se não especificado)")
):
    """
    📥 Importar um perfil de arquivo.
    
    Importa um perfil de componentes de um arquivo YAML ou JSON.
    """
    try:
        input_file = Path(file)
        
        if not input_file.exists():
            console.print(f"[red]❌ Arquivo '{file}' não encontrado[/red]")
            raise typer.Exit(1)
        
        # Load profile data
        if input_file.suffix.lower() in ['.yaml', '.yml']:
            with open(input_file, 'r', encoding='utf-8') as f:
                profile_data = yaml.safe_load(f)
        elif input_file.suffix.lower() == '.json':
            with open(input_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        else:
            console.print(f"[red]❌ Formato não suportado: {input_file.suffix}[/red]")
            raise typer.Exit(1)
        
        # Use provided name or extract from file
        profile_name = name or input_file.stem.replace('_export', '')
        profile_data['name'] = profile_name
        
        # Save profile
        save_profile(
            profile_name,
            profile_data.get('components', []),
            profile_data.get('description', '')
        )
        
        console.print(f"[green]✅ Perfil '{profile_name}' importado com sucesso![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Falha ao importar perfil: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
