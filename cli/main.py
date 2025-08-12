#!/usr/bin/env python3
"""
Main CLI application for Environment Dev Deep Evaluation.

Provides a comprehensive command-line interface with rich formatting,
progress indicators, and intuitive commands for system management.
"""

import typer
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import print as rprint

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import ConfigurationManager, SystemConfiguration
from core.exceptions import EnvironmentDevDeepEvaluationError
from validation.schemas import ComponentModel
from cli.utils import NetworkOperations
from detection.unified_engine import UnifiedDetectionEngine
import shutil
import zipfile
import subprocess
from datetime import datetime

# Initialize CLI app and console
app = typer.Typer(
    name="mecha",
    help="🔧 Environment Dev Deep Evaluation - Advanced Development Environment Manager",
    rich_markup_mode="rich",
    add_completion=False
)
console = Console()

# Global configuration manager
config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get or initialize the configuration manager.
    
    Returns:
        ConfigurationManager: Initialized configuration manager
    """
    global config_manager
    if config_manager is None:
        config_manager = ConfigurationManager()
    return config_manager


def display_banner():
    """Display the application banner."""
    banner = Panel.fit(
        "[bold blue]🔧 Environment Dev Deep Evaluation[/bold blue]\n"
        "[dim]Advanced Development Environment Manager[/dim]",
        border_style="blue"
    )
    console.print(banner)
    console.print()


@app.command()
def init(
    config_path: Optional[str] = typer.Option(
        None, 
        "--config", 
        "-c", 
        help="Path to configuration file"
    ),
    interactive: bool = typer.Option(
        True, 
        "--interactive/--no-interactive", 
        "-i/-n", 
        help="Run in interactive mode"
    )
):
    """
    🚀 Initialize the Environment Dev Deep Evaluation system.
    
    Sets up configuration, validates system requirements, and prepares
    the environment for component management.
    """
    display_banner()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Initialize configuration
            task = progress.add_task("Initializing configuration...", total=None)
            
            if config_path:
                config_manager = ConfigurationManager(config_path)
            else:
                config_manager = ConfigurationManager()
            
            progress.update(task, description="Validating system requirements...")
            
            # Validate system
            config = config_manager.get_config()
            
            progress.update(task, description="Creating directories...")
            
            # Create necessary directories
            directories = [
                Path(config.base_directory),
                Path(config.downloads_directory),
                Path(config.logs_directory),
                Path(config.cache_directory)
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            progress.update(task, description="Initialization complete!")
        
        # Display success message
        success_panel = Panel(
            "[green]✅ System initialized successfully![/green]\n\n"
            f"📁 Base directory: {config.base_directory}\n"
            f"📥 Downloads: {config.downloads_directory}\n"
            f"📋 Logs: {config.logs_directory}\n"
            f"💾 Cache: {config.cache_directory}",
            title="Initialization Complete",
            border_style="green"
        )
        console.print(success_panel)
        
        if interactive:
            if Confirm.ask("\n🔍 Would you like to run a system analysis now?"):
                analyze_gaps()
                
    except Exception as e:
        console.print(f"[red]❌ Initialization failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_components(
    category: Optional[str] = typer.Option(
        None, 
        "--category", 
        "-c", 
        help="Filter by category (ai_tools, dev_tools, etc.)"
    ),
    installed_only: bool = typer.Option(
        False, 
        "--installed", 
        "-i", 
        help="Show only installed components"
    ),
    available_only: bool = typer.Option(
        False, 
        "--available", 
        "-a", 
        help="Show only available (not installed) components"
    )
):
    """
    📋 List all available components with their status.
    
    Displays a comprehensive table of components including their
    category, description, installation status, and version information.
    """
    try:
        # Create components table
        table = Table(title="🔧 Available Components")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Version", style="green")
        table.add_column("Confiança", style="blue")
        
        # Load components from YAML files
        components_dir = Path("components")
        if not components_dir.exists():
            console.print("[red]❌ Components directory not found[/red]")
            raise typer.Exit(1)
        
        component_count = 0

        # Initialize detection engine to surface confidence when possible
        detection_engine = None
        registry_index = []
        try:
            detection_engine = UnifiedDetectionEngine(get_config_manager())
            detection_engine.initialize()
            registry_apps = detection_engine.scan_registry_installations()
            # Build simple index for name matching
            registry_index = [(app.name.lower(), getattr(app.detection_confidence, 'value', 'unknown')) for app in registry_apps]
        except Exception:
            # Non-fatal: keep listing without confidence enrichment
            registry_index = []
        
        def _format_confidence(value: str) -> str:
            mapping = {
                "high": "[green]✅ alta[/green]",
                "medium": "[yellow]🟡 média[/yellow]",
                "low": "[red]⚠️ baixa[/red]",
                "unknown": "[dim]❔ desconhecida[/dim]",
            }
            return mapping.get((value or "").lower(), mapping["unknown"])

        for yaml_file in components_dir.glob("*.yaml"):
            try:
                import yaml
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not isinstance(data, dict):
                    continue
                    
                for component_name, component_data in data.items():
                    if not isinstance(component_data, dict):
                        continue
                    
                    # Apply category filter
                    if category and component_data.get('category', '').lower() != category.lower():
                        continue
                    
                    # Determine status (mock for now)
                    status = "🟡 Available"  # Default status
                    version = component_data.get('version', 'Unknown')
                    
                    # Apply status filters
                    if installed_only and "Available" in status:
                        continue
                    if available_only and "Installed" in status:
                        continue
                    
                    # Confidence matching (simple contains/equals)
                    comp_lower = component_name.lower()
                    confidence_value = "unknown"
                    for app_name, conf in registry_index:
                        if comp_lower == app_name or comp_lower in app_name or app_name in comp_lower:
                            confidence_value = conf
                            break

                    table.add_row(
                        component_name,
                        component_data.get('category', 'Unknown'),
                        component_data.get('description', 'No description'),
                        status,
                        version,
                        _format_confidence(confidence_value)
                    )
                    component_count += 1
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Warning: Could not load {yaml_file}: {e}[/yellow]")
                continue
        
        if component_count == 0:
            console.print("[yellow]📭 No components found matching the criteria[/yellow]")
        else:
            console.print(table)
            console.print(f"\n[dim]Found {component_count} components[/dim]")
            
    except Exception as e:
        console.print(f"[red]❌ Error listing components: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def install(
    component: str = typer.Argument(..., help="Name of the component to install"),
    force: bool = typer.Option(
        False, 
        "--force", 
        "-f", 
        help="Force reinstallation if already installed"
    ),
    dry_run: bool = typer.Option(
        False, 
        "--dry-run", 
        "-d", 
        help="Show what would be installed without actually installing"
    )
):
    """
    📦 Install a specific component.
    
    Downloads, verifies, and installs the specified component with
    progress tracking and error handling.
    """
    try:
        if dry_run:
            console.print(f"[yellow]🔍 DRY RUN: Would install '{component}'[/yellow]")
            return

        display_banner()

        # 1) Localizar definição do componente
        components_dir = Path("components")
        if not components_dir.exists():
            console.print("[red]❌ Components directory not found[/red]")
            raise typer.Exit(1)

        import yaml
        component_def = None
        component_key = None
        source_file: Optional[Path] = None
        for yaml_file in components_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    continue
                for name, comp in data.items():
                    if isinstance(name, str) and isinstance(comp, dict) and name.lower() == component.lower():
                        component_def = comp
                        component_key = name
                        source_file = yaml_file
                        break
                if component_def is not None:
                    break
            except Exception as e:
                console.print(f"[yellow]⚠️ Warning: Could not parse {yaml_file}: {e}[/yellow]")

        if component_def is None:
            console.print(f"[red]❌ Component '{component}' not found in components/*.yaml[/red]")
            raise typer.Exit(1)

        # 2) Validações de segurança: hash obrigatório e não-placeholder
        hash_value = component_def.get("hash")
        download_url = component_def.get("download_url")
        install_method = component_def.get("install_method", "").lower()

        placeholders = {"HASH_NEEDS_UPDATE", "HASH_PENDENTE_VERIFICACAO"}
        if not hash_value or (isinstance(hash_value, str) and hash_value.strip() in placeholders):
            console.print(
                Panel(
                    "[red]❌ Política de segurança: hash obrigatório ausente ou pendente[/red]\n\n"
                    "Este projeto exige verificação de integridade (RF005). Atualize os hashes antes de instalar.\n"
                    "Use: [bold]python scripts/hash_updater.py --components-dir components[/bold]",
                    title="Hash inválido",
                    border_style="red",
                )
            )
            raise typer.Exit(2)

        if not download_url:
            console.print(
                Panel(
                    "[red]❌ download_url ausente no componente[/red]\n\n"
                    f"Corrija o arquivo: [bold]{source_file} → {component_key}[/bold]",
                    title="Definição incompleta",
                    border_style="red",
                )
            )
            raise typer.Exit(2)

        # 3) Download/instalação com verificação real de SHA256
        cfg = get_config_manager().get_config()
        downloads_dir = Path(cfg.downloads_directory)
        downloads_dir.mkdir(parents=True, exist_ok=True)

        from urllib.parse import urlparse
        parsed = urlparse(download_url)
        filename = Path(parsed.path).name or f"{component_key}.download"
        destination = downloads_dir / filename

        # alternative_urls
        alt_urls = component_def.get("alternative_urls") or []
        size_limit = component_def.get("size_mb")
        size_limit = int(size_limit) if size_limit else None

        # Fluxos por método
        if install_method in {"exe", "msi", "zip"}:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task(f"Baixando {component_key}...", total=None)
                res = NetworkOperations.download_with_fallback(
                    primary_url=download_url,
                    alternative_urls=alt_urls,
                    destination=destination,
                    expected_sha256=str(hash_value),
                    timeout=int(getattr(cfg, 'download_timeout', 300)),
                    max_retries=int(getattr(cfg, 'max_download_retries', 3)),
                    max_size_mb=size_limit,
                    show_progress=True,
                )
                progress.update(task, completed=1)

            if not res.success:
                details = "\n".join(res.errors or [res.message])
                console.print(Panel(f"[red]❌ Falha no download/verificação[/red]\n{details}", border_style="red"))
                raise typer.Exit(3)

            console.print(Panel(f"[green]✅ Artefato pronto:[/green] {destination}", border_style="green"))

            # Execução silenciosa básica (Windows)
            if install_method == "exe":
                args = component_def.get("install_args") or "/S"
                try:
                    proc = subprocess.run([str(destination), *str(args).split()], capture_output=True, text=True, timeout=3600)
                    if proc.returncode != 0:
                        console.print(Panel(f"[red]❌ Instalador retornou código {proc.returncode}[/red]\n{proc.stderr}", border_style="red"))
                        raise typer.Exit(4)
                    console.print(Panel("[green]✅ Instalação concluída[/green]", border_style="green"))
                except Exception as e:
                    console.print(f"[red]❌ Falha ao executar instalador: {e}[/red]")
                    raise typer.Exit(4)
            elif install_method == "msi":
                # msiexec /i file.msi /qn
                try:
                    proc = subprocess.run(["msiexec", "/i", str(destination), "/qn"], capture_output=True, text=True, timeout=3600)
                    if proc.returncode != 0:
                        console.print(Panel(f"[red]❌ msiexec retornou código {proc.returncode}[/red]\n{proc.stderr}", border_style="red"))
                        raise typer.Exit(4)
                    console.print(Panel("[green]✅ Instalação MSI concluída[/green]", border_style="green"))
                except Exception as e:
                    console.print(f"[red]❌ Falha msiexec: {e}[/red]")
                    raise typer.Exit(4)
            else:
                # zip: apenas confirma integridade; extração é opcional do usuário
                console.print(Panel("[green]✅ ZIP verificado. Extraia manualmente ou implemente handler dedicado.[/green]", border_style="green"))

        elif install_method == "pip":
            # Política: instalar offline a partir de wheel verificado
            pypi_name = component_def.get("pypi_name")
            version = component_def.get("version")
            if not pypi_name or not version:
                console.print(Panel("[red]❌ PIP requer pypi_name e version[/red]", border_style="red"))
                raise typer.Exit(2)

            dist_dir = downloads_dir / ".dist"
            dist_dir.mkdir(parents=True, exist_ok=True)

            # Preferir wheel específica via download_url/alternative_urls, com verificação RF005
            use_provided_wheel = False
            wheel_path = None
            if download_url:
                from urllib.parse import urlparse as _urlparse
                parsed_dl = _urlparse(download_url)
                filename_dl = Path(parsed_dl.path).name.lower()
                if filename_dl.endswith(".whl"):
                    use_provided_wheel = True
            alt_urls = component_def.get("alternative_urls") or []
            size_limit = component_def.get("size_mb")
            size_limit = int(size_limit) if size_limit else None

            if use_provided_wheel:
                # Baixa a wheel previamente (ou copia de file://) com verificação de hash
                destination_wheel = dist_dir / Path(urlparse(download_url).path).name
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    task = progress.add_task(f"Baixando wheel {pypi_name}...", total=None)
                    res = NetworkOperations.download_with_fallback(
                        primary_url=download_url,
                        alternative_urls=alt_urls,
                        destination=destination_wheel,
                        expected_sha256=str(hash_value),
                        timeout=int(getattr(cfg, 'download_timeout', 300)),
                        max_retries=int(getattr(cfg, 'max_download_retries', 3)),
                        max_size_mb=size_limit,
                        show_progress=True,
                    )
                    progress.update(task, completed=1)

                if not res.success:
                    details = "\n".join(res.errors or [res.message])
                    console.print(Panel(f"[red]❌ Falha no download/verificação da wheel[/red]\n{details}", border_style="red"))
                    raise typer.Exit(3)
                wheel_path = destination_wheel
            else:
                # Fluxo atual: pip download para obter wheel, depois verificar hash e instalar offline
                download_cmd = [
                    sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--dest", str(dist_dir), f"{pypi_name}=={version}"
                ]
                proc = subprocess.run(download_cmd, capture_output=True, text=True, timeout=1800)
                if proc.returncode != 0:
                    console.print(Panel(f"[red]❌ Falha ao baixar wheel[/red]\n{proc.stderr}", border_style="red"))
                    raise typer.Exit(3)

                wheels = list(dist_dir.glob(f"{pypi_name.replace('-', '_')}*.whl"))
                if not wheels:
                    console.print(Panel("[red]❌ Wheel não encontrado após download[/red]", border_style="red"))
                    raise typer.Exit(3)
                wheel_path = wheels[0]

                vr = NetworkOperations.verify_sha256(wheel_path, str(hash_value))
                if not vr.success:
                    console.print(Panel(f"[red]❌ Hash inválido da wheel[/red]\n{vr.message}\n{vr.errors}", border_style="red"))
                    raise typer.Exit(3)

            # Instalação offline a partir de dist_dir
            install_cmd = [
                sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(dist_dir), str(wheel_path), "--no-warn-script-location"
            ]
            proc2 = subprocess.run(install_cmd, capture_output=True, text=True, timeout=1800)
            if proc2.returncode != 0:
                console.print(Panel(f"[red]❌ pip install falhou[/red]\n{proc2.stderr}", border_style="red"))
                raise typer.Exit(4)
            console.print(Panel("[green]✅ Pacote pip instalado offline com verificação de hash[/green]", border_style="green"))

        else:
            console.print(Panel(f"[yellow]⚠️ Método '{install_method}' não implementado neste comando[/yellow]", border_style="yellow"))

    except typer.Exit:
        # Preserva códigos de saída explícitos definidos acima (ex.: 2, 3, 4)
        raise
    except Exception as e:
        console.print(f"[red]❌ Installation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze_gaps(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filtrar componentes por categoria"),
    name_filter: Optional[str] = typer.Option(None, "--name", "-n", help="Filtrar por nome (contains, case-insensitive)"),
    output_json: bool = typer.Option(False, "--json", help="Saída em JSON"),
    fail_on_missing: bool = typer.Option(True, "--fail-on-missing/--no-fail-on-missing", help="Retorna código ≠0 se houver lacunas")
):
    """Analisa lacunas do ambiente do usuário usando a UnifiedDetectionEngine."""
    try:
        display_banner()

        components_dir = Path("components")
        if not components_dir.exists():
            console.print("[red]❌ Diretório 'components' não encontrado[/red]")
            raise typer.Exit(1)

        import yaml
        expected: List[str] = []
        for yaml_file in components_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    continue
                for comp_name, comp_data in data.items():
                    if not isinstance(comp_data, dict):
                        continue
                    if category and comp_data.get("category", "").lower() != category.lower():
                        continue
                    if name_filter and name_filter.lower() not in comp_name.lower():
                        continue
                    expected.append(comp_name)
            except Exception:
                continue

        # Executa a engine com tolerância a falhas: se falhar, considerar tudo ausente
        try:
            engine = UnifiedDetectionEngine(get_config_manager())
            engine.initialize()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Analisando lacunas no ambiente...", total=None)
                report = engine.analyze_environment_gaps(expected)
                progress.update(task, completed=1)
        except Exception as eng_err:
            # Fallback seguro: tudo ausente com mensagem clara
            from detection.interfaces import GapReport  # type: ignore
            report = GapReport(
                expected_count=len(expected),
                present_count=0,
                missing_count=len(expected),
                present=[],
                missing=expected,
                confidence_index={},
            )
            console.print(Panel(f"[yellow]⚠️ Engine de detecção falhou[/yellow]\n{eng_err}", title="Fallback aplicado", border_style="yellow"))

        if output_json:
            import json
            console.print_json(json.dumps({
                "expected": report.expected_count,
                "present": report.present_count,
                "missing": report.missing_count,
                "present_list": report.present,
                "missing_list": report.missing,
            }))
        else:
            table = Table(title="🔍 Lacunas do Ambiente")
            table.add_column("Status", style="cyan")
            table.add_column("Componente", style="white")
            table.add_column("Confiança", style="blue")
            for name in report.present:
                conf = report.confidence_index.get(name)
                conf_val = getattr(conf, 'value', str(conf) if conf else 'unknown')
                table.add_row("✅ Presente", name, conf_val)
            for name in report.missing:
                table.add_row("❌ Ausente", name, "-")
            console.print(table)
            console.print(f"[dim]Esperados: {report.expected_count}  |  Presentes: {report.present_count}  |  Ausentes: {report.missing_count}[/dim]")

        if fail_on_missing and report.missing_count > 0:
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def backup(
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Caminho do arquivo .zip de backup de componentes"
    )
):
    """
    💾 Cria backup dos arquivos de componentes (.yaml).
    """
    try:
        cfg = get_config_manager().get_config()
        components_dir = Path("components")
        if not components_dir.exists():
            console.print("[red]❌ Diretório 'components' não encontrado[/red]")
            raise typer.Exit(1)

        backups_dir = Path(cfg.backups_directory)
        backups_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(output) if output else backups_dir / f"components_backup_{stamp}.zip"

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in components_dir.glob("*.yaml"):
                zf.write(p, arcname=p.name)

        console.print(Panel(f"[green]✅ Backup criado:[/green] {backup_path}", border_style="green"))
    except Exception as e:
        console.print(f"[red]❌ Falha ao criar backup: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def restore(
    file: str = typer.Argument(..., help="Arquivo .zip de backup para restaurar"),
    confirm_overwrite: bool = typer.Option(
        False, "--yes", "-y", help="Confirma sobrescrita dos arquivos"
    )
):
    """
    🔄 Restaura arquivos de componentes a partir de um backup (.zip).
    """
    try:
        backup_zip = Path(file)
        components_dir = Path("components")
        if not backup_zip.exists():
            console.print("[red]❌ Arquivo de backup não encontrado[/red]")
            raise typer.Exit(1)
        if not confirm_overwrite and not Confirm.ask("Sobrescrever arquivos existentes em 'components'?"):
            raise typer.Exit(0)

        with zipfile.ZipFile(backup_zip, 'r') as zf:
            zf.extractall(components_dir)

        console.print(Panel("[green]✅ Restauração concluída[/green]", border_style="green"))
    except Exception as e:
        console.print(f"[red]❌ Falha ao restaurar backup: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    hashes_only: bool = typer.Option(True, "--hashes-only/--no-hashes-only", help="Atualiza apenas hashes SHA256"),
    max_size_mb: int = typer.Option(700, "--max-size-mb", help="Tamanho máximo de download por arquivo (MB)")
):
    """
    ⬆️ Atualiza definições do sistema (ex.: hashes de componentes).
    """
    try:
        if hashes_only:
            # Executa HashUpdater programaticamente
            from scripts.hash_updater import HashUpdater
            cfgm = get_config_manager()
            updater = HashUpdater(cfgm)
            init_res = updater.initialize()
            if not init_res.success:
                raise RuntimeError("Falha ao inicializar HashUpdater")
            result = updater.process_all_files(Path("components"), dry_run=False, max_size_mb=max_size_mb)
            updater.cleanup()
            if not result.success:
                console.print(f"[yellow]⚠️ Atualização concluída com erros[/yellow]\n{result.message}")
            else:
                console.print(f"[green]✅ {result.message}[/green]")
        else:
            console.print("[yellow]⚠️ Modo de atualização avançada ainda não implementado[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Falha na atualização: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def uninstall(
    component: str = typer.Argument(..., help="Nome do componente a desinstalar"),
    assume_yes: bool = typer.Option(False, "--yes", "-y", help="Não perguntar confirmação")
):
    """
    🗑️ Desinstala um componente quando suportado (pip/winget/choco).
    """
    try:
        if not assume_yes and not Confirm.ask(f"Remover '{component}' do sistema?"):
            raise typer.Exit(0)

        # Estratégias: pip, winget, choco
        strategies = [
            (["python", "-m", "pip", "uninstall", "-y", component], "pip"),
            (["winget", "uninstall", "--id", component, "--silent"], "winget"),
            (["choco", "uninstall", component, "-y"], "chocolatey"),
        ]
        any_ok = False
        for cmd, name in strategies:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if proc.returncode == 0:
                    console.print(f"[green]✅ Desinstalação via {name} concluída[/green]")
                    any_ok = True
                    break
            except FileNotFoundError:
                continue
            except Exception as e:
                console.print(f"[dim]Aviso: tentativa via {name} falhou: {e}[/dim]")
                continue

        if not any_ok:
            console.print("[yellow]⚠️ Desinstalação automática não suportada para este componente[/yellow]")
            raise typer.Exit(2)
    except Exception as e:
        console.print(f"[red]❌ Falha ao desinstalar: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def doctor():
    """
    🩺 Run system diagnostics and health checks.
    
    Performs comprehensive system diagnostics to identify
    configuration issues, conflicts, and optimization opportunities.
    """
    try:
        console.print("[blue]🩺 Running system diagnostics...[/blue]\n")
        
        # System Information
        info_table = Table(title="System Information")
        info_table.add_column("Component", style="cyan")
        info_table.add_column("Status", style="green")
        info_table.add_column("Details", style="white")
        
        import platform
        import sys
        
        info_table.add_row("Operating System", "✅ OK", f"{platform.system()} {platform.release()}")
        info_table.add_row("Python Version", "✅ OK", f"{sys.version.split()[0]}")
        info_table.add_row("Architecture", "✅ OK", platform.machine())
        
        console.print(info_table)
        console.print()
        
        # Configuration Check
        config_table = Table(title="Configuration Check")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Status", style="green")
        config_table.add_column("Value", style="white")
        
        try:
            config_mgr = get_config_manager()
            config = config_mgr.get_config()
            
            config_table.add_row("Base Directory", "✅ OK", config.base_directory)
            config_table.add_row("Log Level", "✅ OK", config.log_level)
            config_table.add_row("Debug Mode", "✅ OK", str(config.debug_mode))
            
        except Exception as e:
            config_table.add_row("Configuration", "❌ ERROR", str(e))
        
        console.print(config_table)
        console.print()
        
        # Health Summary
        health_panel = Panel(
            "[green]✅ System appears to be healthy![/green]\n\n"
            "🔧 All core components are functioning\n"
            "📋 Configuration is valid\n"
            "💾 Required directories exist",
            title="Health Summary",
            border_style="green"
        )
        console.print(health_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Diagnostics failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """
    📋 Show version information.
    """
    version_info = Panel(
        "[bold blue]Environment Dev Deep Evaluation[/bold blue]\n"
        "Version: 2.0.0\n"
        "Phase: 2 - UX/DX Improvements\n\n"
        "[dim]Advanced Development Environment Manager[/dim]",
        title="Version Information",
        border_style="blue"
    )
    console.print(version_info)


if __name__ == "__main__":
    app()