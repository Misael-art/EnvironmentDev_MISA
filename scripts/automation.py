#!/usr/bin/env python3
"""
Automation Scripts for Common Development Tasks

Provides automated workflows for project setup, maintenance,
deployment, and other common development operations.
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.text import Text

console = Console()

@dataclass
class AutomationTask:
    """Automation task definition."""
    name: str
    description: str
    function: Callable
    category: str
    dependencies: List[str] = None
    estimated_time: str = "Unknown"

@dataclass
class ProjectTemplate:
    """Project template definition."""
    name: str
    description: str
    files: Dict[str, str]  # filename -> content
    directories: List[str]
    dependencies: List[str] = None
    post_setup_commands: List[str] = None

class ProjectSetupAutomation:
    """Automated project setup and initialization."""
    
    def __init__(self):
        """Initialize project setup automation."""
        self.console = Console()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """Load project templates.
        
        Returns:
            Dictionary of available templates
        """
        return {
            "python_cli": ProjectTemplate(
                name="Python CLI Application",
                description="A command-line application with Click/Typer",
                directories=[
                    "src", "tests", "docs", "scripts",
                    "src/cli", "src/core", "src/utils"
                ],
                files={
                    "README.md": self._get_readme_template("Python CLI"),
                    "requirements.txt": "click\nrich\ntyper\npytest\n",
                    "setup.py": self._get_setup_py_template(),
                    "src/__init__.py": "",
                    "src/cli/__init__.py": "",
                    "src/cli/main.py": self._get_cli_main_template(),
                    "src/core/__init__.py": "",
                    "src/utils/__init__.py": "",
                    "tests/__init__.py": "",
                    "tests/test_main.py": self._get_test_template(),
                    ".gitignore": self._get_gitignore_template("python"),
                    "pyproject.toml": self._get_pyproject_template()
                },
                dependencies=["python", "pip"],
                post_setup_commands=[
                    "pip install -r requirements.txt",
                    "pip install -e ."
                ]
            ),
            "python_web": ProjectTemplate(
                name="Python Web Application",
                description="A web application with Flask/FastAPI",
                directories=[
                    "app", "tests", "static", "templates", "migrations",
                    "app/api", "app/models", "app/services", "app/utils"
                ],
                files={
                    "README.md": self._get_readme_template("Python Web"),
                    "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\nalembic\npydantic\n",
                    "app/__init__.py": "",
                    "app/main.py": self._get_web_main_template(),
                    "app/api/__init__.py": "",
                    "app/models/__init__.py": "",
                    "app/services/__init__.py": "",
                    "app/utils/__init__.py": "",
                    "tests/__init__.py": "",
                    ".gitignore": self._get_gitignore_template("python"),
                    "docker-compose.yml": self._get_docker_compose_template()
                },
                dependencies=["python", "pip"],
                post_setup_commands=[
                    "pip install -r requirements.txt"
                ]
            ),
            "node_app": ProjectTemplate(
                name="Node.js Application",
                description="A Node.js application with Express",
                directories=[
                    "src", "tests", "public", "config",
                    "src/controllers", "src/models", "src/routes", "src/middleware"
                ],
                files={
                    "README.md": self._get_readme_template("Node.js"),
                    "package.json": self._get_package_json_template(),
                    "src/app.js": self._get_express_app_template(),
                    "src/server.js": self._get_server_template(),
                    ".gitignore": self._get_gitignore_template("node"),
                    ".env.example": "PORT=3000\nNODE_ENV=development\n"
                },
                dependencies=["node", "npm"],
                post_setup_commands=[
                    "npm install"
                ]
            )
        }
    
    def create_project(self, template_name: str, project_name: str, project_path: str = None):
        """Create a new project from template.
        
        Args:
            template_name: Name of the template to use
            project_name: Name of the new project
            project_path: Path where to create the project
        """
        if template_name not in self.templates:
            console.print(f"[red]Template '{template_name}' not found![/red]")
            return
        
        template = self.templates[template_name]
        
        # Determine project path
        if project_path is None:
            project_path = os.path.join(os.getcwd(), project_name)
        else:
            project_path = os.path.join(project_path, project_name)
        
        project_path = Path(project_path)
        
        console.print(f"🚀 Creating project '{project_name}' using template '{template.name}'")
        console.print(f"📁 Location: {project_path}")
        
        if project_path.exists():
            if not Confirm.ask(f"Directory {project_path} already exists. Continue?"):
                return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                # Create directories
                task1 = progress.add_task("Creating directories...", total=len(template.directories))
                for directory in template.directories:
                    dir_path = project_path / directory
                    dir_path.mkdir(parents=True, exist_ok=True)
                    progress.advance(task1)
                
                # Create files
                task2 = progress.add_task("Creating files...", total=len(template.files))
                for filename, content in template.files.items():
                    file_path = project_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Replace placeholders
                    content = content.replace("{{PROJECT_NAME}}", project_name)
                    content = content.replace("{{PROJECT_PATH}}", str(project_path))
                    content = content.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    progress.advance(task2)
                
                # Run post-setup commands
                if template.post_setup_commands:
                    task3 = progress.add_task("Running setup commands...", total=len(template.post_setup_commands))
                    for command in template.post_setup_commands:
                        try:
                            subprocess.run(
                                command.split(),
                                cwd=project_path,
                                check=True,
                                capture_output=True,
                                text=True
                            )
                        except subprocess.CalledProcessError as e:
                            console.print(f"[yellow]Warning: Command failed: {command}[/yellow]")
                            console.print(f"[yellow]Error: {e.stderr}[/yellow]")
                        progress.advance(task3)
            
            console.print(f"\n✅ Project '{project_name}' created successfully!")
            console.print(f"📁 Location: {project_path}")
            console.print("\n🚀 Next steps:")
            console.print(f"   cd {project_path}")
            if template.post_setup_commands:
                console.print("   # Dependencies should already be installed")
            console.print("   # Start developing!")
            
        except Exception as e:
            console.print(f"[red]Error creating project: {e}[/red]")
    
    def list_templates(self):
        """List available project templates."""
        console.print("📋 Available Project Templates", style="bold blue")
        console.print()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Template", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Description", style="yellow")
        table.add_column("Dependencies", style="green")
        
        for key, template in self.templates.items():
            deps = ", ".join(template.dependencies) if template.dependencies else "None"
            table.add_row(key, template.name, template.description, deps)
        
        console.print(table)
    
    def _get_readme_template(self, project_type: str) -> str:
        """Get README template.
        
        Args:
            project_type: Type of project
            
        Returns:
            README content
        """
        return f"""# {{{{PROJECT_NAME}}}}

A {project_type} application created on {{{{DATE}}}}.

## Description

Add your project description here.

## Installation

```bash
# Add installation instructions
```

## Usage

```bash
# Add usage examples
```

## Development

```bash
# Add development setup instructions
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
"""
    
    def _get_setup_py_template(self) -> str:
        """Get setup.py template.
        
        Returns:
            setup.py content
        """
        return """from setuptools import setup, find_packages

setup(
    name="{{PROJECT_NAME}}",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click",
        "rich",
        "typer",
    ],
    entry_points={
        "console_scripts": [
            "{{PROJECT_NAME}}=cli.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/{{PROJECT_NAME}}",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
"""
    
    def _get_cli_main_template(self) -> str:
        """Get CLI main template.
        
        Returns:
            CLI main content
        """
        return """#!/usr/bin/env python3
"""
Main CLI application for {{PROJECT_NAME}}
"""

import typer
from rich.console import Console
from rich import print

console = Console()
app = typer.Typer()

@app.command()
def hello(name: str = typer.Option("World", help="Name to greet")):
    """Say hello to someone."""
    print(f"Hello {name}! 👋")

@app.command()
def version():
    """Show version information."""
    print("{{PROJECT_NAME}} v0.1.0")

def main():
    """Main entry point."""
    app()

if __name__ == "__main__":
    main()
"""
    
    def _get_test_template(self) -> str:
        """Get test template.
        
        Returns:
            Test content
        """
        return """#!/usr/bin/env python3
"""
Tests for {{PROJECT_NAME}}
"""

import pytest
from cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

def test_hello_default():
    """Test hello command with default name."""
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello World" in result.stdout

def test_hello_custom_name():
    """Test hello command with custom name."""
    result = runner.invoke(app, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello Alice" in result.stdout

def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "v0.1.0" in result.stdout
"""
    
    def _get_gitignore_template(self, project_type: str) -> str:
        """Get .gitignore template.
        
        Args:
            project_type: Type of project
            
        Returns:
            .gitignore content
        """
        if project_type == "python":
            return """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
PYMANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
"""
        elif project_type == "node":
            return """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Directory for instrumented libs generated by jscoverage/JSCover
lib-cov

# Coverage directory used by tools like istanbul
coverage

# nyc test coverage
.nyc_output

# Grunt intermediate storage
.grunt

# Bower dependency directory
bower_components

# node-waf configuration
.lock-wscript

# Compiled binary addons
build/Release

# Dependency directories
node_modules/
jspm_packages/

# TypeScript v1 declaration files
typings/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test

# parcel-bundler cache
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless/

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/
"""
        else:
            return "# Add your ignore patterns here\n"
    
    def _get_pyproject_template(self) -> str:
        """Get pyproject.toml template.
        
        Returns:
            pyproject.toml content
        """
        return """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{{PROJECT_NAME}}"
version = "0.1.0"
description = "A CLI application"
readme = "README.md"
requires-python = ">=3.8"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]
dependencies = [
    "click",
    "rich",
    "typer",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "black",
    "flake8",
    "mypy",
]

[project.scripts]
{{PROJECT_NAME}} = "cli.main:main"

[tool.black]
line-length = 88
target-version = ['py38']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
"""
    
    def _get_web_main_template(self) -> str:
        """Get web application main template.
        
        Returns:
            Web main content
        """
        return """#!/usr/bin/env python3
"""
Main web application for {{PROJECT_NAME}}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{{PROJECT_NAME}}",
    description="A web application",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello from {{PROJECT_NAME}}!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    def _get_docker_compose_template(self) -> str:
        """Get docker-compose template.
        
        Returns:
            docker-compose.yml content
        """
        return """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/{{PROJECT_NAME}}
    depends_on:
      - db
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB={{PROJECT_NAME}}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""
    
    def _get_package_json_template(self) -> str:
        """Get package.json template.
        
        Returns:
            package.json content
        """
        return """{
  "name": "{{PROJECT_NAME}}",
  "version": "1.0.0",
  "description": "A Node.js application",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "jest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "helmet": "^6.0.0",
    "morgan": "^1.10.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.0",
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  },
  "keywords": ["node", "express", "api"],
  "author": "Your Name",
  "license": "MIT"
}
"""
    
    def _get_express_app_template(self) -> str:
        """Get Express app template.
        
        Returns:
            Express app content
        """
        return """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'Hello from {{PROJECT_NAME}}!' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

module.exports = app;
"""
    
    def _get_server_template(self) -> str:
        """Get server template.
        
        Returns:
            Server content
        """
        return """require('dotenv').config();
const app = require('./app');

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📍 http://localhost:${PORT}`);
});
"""

class MaintenanceAutomation:
    """Automated maintenance tasks."""
    
    def __init__(self):
        """Initialize maintenance automation."""
        self.console = Console()
    
    def cleanup_project(self, project_path: str = None):
        """Clean up project files and directories.
        
        Args:
            project_path: Path to project (default: current directory)
        """
        if project_path is None:
            project_path = os.getcwd()
        
        project_path = Path(project_path)
        
        console.print(f"🧹 Cleaning up project: {project_path}")
        
        cleanup_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/.pytest_cache",
            "**/.coverage",
            "**/htmlcov",
            "**/node_modules",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.log",
            "**/dist",
            "**/build",
            "**/*.egg-info"
        ]
        
        removed_count = 0
        removed_size = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Scanning for cleanup targets...", total=None)
            
            for pattern in cleanup_patterns:
                for path in project_path.glob(pattern):
                    if path.exists():
                        try:
                            if path.is_file():
                                size = path.stat().st_size
                                path.unlink()
                                removed_size += size
                                removed_count += 1
                            elif path.is_dir():
                                size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                                shutil.rmtree(path)
                                removed_size += size
                                removed_count += 1
                        except Exception as e:
                            console.print(f"[yellow]Warning: Could not remove {path}: {e}[/yellow]")
        
        console.print(f"\n✅ Cleanup completed!")
        console.print(f"📁 Removed {removed_count} items")
        console.print(f"💾 Freed {removed_size / (1024*1024):.2f} MB")
    
    def update_dependencies(self, project_path: str = None):
        """Update project dependencies.
        
        Args:
            project_path: Path to project (default: current directory)
        """
        if project_path is None:
            project_path = os.getcwd()
        
        project_path = Path(project_path)
        
        console.print(f"📦 Updating dependencies for: {project_path}")
        
        # Check for different project types
        if (project_path / "requirements.txt").exists():
            self._update_python_dependencies(project_path)
        
        if (project_path / "package.json").exists():
            self._update_node_dependencies(project_path)
        
        if (project_path / "Pipfile").exists():
            self._update_pipenv_dependencies(project_path)
    
    def _update_python_dependencies(self, project_path: Path):
        """Update Python dependencies.
        
        Args:
            project_path: Path to project
        """
        console.print("🐍 Updating Python dependencies...")
        
        try:
            # Update pip first
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            # Update requirements
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            console.print("✅ Python dependencies updated")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error updating Python dependencies: {e}[/red]")
    
    def _update_node_dependencies(self, project_path: Path):
        """Update Node.js dependencies.
        
        Args:
            project_path: Path to project
        """
        console.print("📦 Updating Node.js dependencies...")
        
        try:
            subprocess.run(
                ["npm", "update"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            console.print("✅ Node.js dependencies updated")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error updating Node.js dependencies: {e}[/red]")
    
    def _update_pipenv_dependencies(self, project_path: Path):
        """Update Pipenv dependencies.
        
        Args:
            project_path: Path to project
        """
        console.print("🔒 Updating Pipenv dependencies...")
        
        try:
            subprocess.run(
                ["pipenv", "update"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            console.print("✅ Pipenv dependencies updated")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error updating Pipenv dependencies: {e}[/red]")
    
    def backup_project(self, project_path: str = None, backup_path: str = None):
        """Create a backup of the project.
        
        Args:
            project_path: Path to project (default: current directory)
            backup_path: Path for backup (default: project_path/../backups)
        """
        if project_path is None:
            project_path = os.getcwd()
        
        project_path = Path(project_path)
        project_name = project_path.name
        
        if backup_path is None:
            backup_path = project_path.parent / "backups"
        else:
            backup_path = Path(backup_path)
        
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{project_name}_backup_{timestamp}.zip"
        backup_file = backup_path / backup_filename
        
        console.print(f"💾 Creating backup: {backup_file}")
        
        # Patterns to exclude from backup
        exclude_patterns = {
            "__pycache__", ".pytest_cache", "node_modules", ".git",
            "dist", "build", "*.pyc", "*.pyo", "*.log"
        }
        
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    
                    task = progress.add_task("Creating backup...", total=None)
                    
                    for file_path in project_path.rglob('*'):
                        if file_path.is_file():
                            # Check if file should be excluded
                            relative_path = file_path.relative_to(project_path)
                            
                            should_exclude = False
                            for pattern in exclude_patterns:
                                if pattern in str(relative_path) or relative_path.name.endswith(pattern.replace('*', '')):
                                    should_exclude = True
                                    break
                            
                            if not should_exclude:
                                zipf.write(file_path, relative_path)
            
            backup_size = backup_file.stat().st_size
            console.print(f"\n✅ Backup created successfully!")
            console.print(f"📁 File: {backup_file}")
            console.print(f"💾 Size: {backup_size / (1024*1024):.2f} MB")
            
        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")

class AutomationManager:
    """Main automation manager."""
    
    def __init__(self):
        """Initialize automation manager."""
        self.console = Console()
        self.project_setup = ProjectSetupAutomation()
        self.maintenance = MaintenanceAutomation()
        
        self.tasks = {
            "setup": {
                "create_project": AutomationTask(
                    "create_project",
                    "Create a new project from template",
                    self._create_project_interactive,
                    "setup",
                    estimated_time="2-5 minutes"
                ),
                "list_templates": AutomationTask(
                    "list_templates",
                    "List available project templates",
                    self.project_setup.list_templates,
                    "setup",
                    estimated_time="< 1 minute"
                )
            },
            "maintenance": {
                "cleanup": AutomationTask(
                    "cleanup",
                    "Clean up project files and directories",
                    self._cleanup_interactive,
                    "maintenance",
                    estimated_time="1-3 minutes"
                ),
                "update_deps": AutomationTask(
                    "update_deps",
                    "Update project dependencies",
                    self._update_deps_interactive,
                    "maintenance",
                    estimated_time="2-10 minutes"
                ),
                "backup": AutomationTask(
                    "backup",
                    "Create project backup",
                    self._backup_interactive,