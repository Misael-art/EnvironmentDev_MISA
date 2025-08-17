#!/usr/bin/env python3
"""
Installation progress screen for Environment Dev Deep Evaluation TUI.

Provides asynchronous installation with real-time progress updates,
logging, and error handling.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Header, Footer, Static, ProgressBar, Log, Button
)
from textual.screen import Screen
from textual.binding import Binding
import subprocess
import json


class InstallationProgressScreen(Screen):
    """Screen for displaying installation progress."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, components: List[str], **kwargs):
        """Initialize installation progress screen.
        
        Args:
            components: List of component names to install
        """
        super().__init__(**kwargs)
        self.components = components
        self.process: Optional[asyncio.subprocess.Process] = None
        self.installing_component = ""
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """Check if installation is running."""
        return self._is_running
    
    @is_running.setter
    def is_running(self, value: bool) -> None:
        """Set installation running status."""
        self._is_running = value
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        
        with Container(id="progress-container"):
            yield Static(f"📦 Installing {len(self.components)} component(s)", id="title")
            
            with Vertical(id="progress-section"):
                yield Static("Status: Waiting to start...", id="status-text")
                yield ProgressBar(id="progress-bar", show_percentage=True)
                
            with Vertical(id="log-section"):
                yield Static("Installation Log:", id="log-title")
                yield Log(id="install-log", auto_scroll=True)
                
            with Horizontal(id="actions"):
                yield Button("Cancel", id="cancel-btn", variant="error")
                
        yield Footer()
        
    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#status-text", Static).update("Status: Ready to start...")
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            await self.cancel_installation()
            
    async def run_installation(self) -> bool:
        """Run the installation process.
        
        Returns:
            True if installation was successful, False otherwise
        """
        if self.is_running:
            return False
            
        self.is_running = True
        log_widget = self.query_one("#install-log", Log)
        status_widget = self.query_one("#status-text", Static)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        
        try:
            # Update UI
            status_widget.update("Status: Starting installation...")
            log_widget.write_line(f"Starting installation of {len(self.components)} component(s)...")
            
            # Prepare command
            cmd = [sys.executable, "-m", "cli.main", "install-many", *self.components, "--continue", "--json"]
            
            # Create subprocess
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Read output asynchronously
            await self._read_process_output()
            
            # Wait for process to complete
            returncode = await self.process.wait()
            
            if returncode == 0:
                status_widget.update("Status: Installation completed successfully!")
                log_widget.write_line("✅ Installation completed successfully!")
                return True
            else:
                status_widget.update(f"Status: Installation failed with code {returncode}")
                log_widget.write_line(f"❌ Installation failed with code {returncode}")
                return False
                
        except Exception as e:
            status_widget.update(f"Status: Error - {str(e)}")
            log_widget.write_line(f"❌ Error: {str(e)}")
            return False
        finally:
            self.is_running = False
            
    async def _read_process_output(self) -> None:
        """Read process output asynchronously."""
        if not self.process:
            return
            
        log_widget = self.query_one("#install-log", Log)
        status_widget = self.query_one("#status-text", Static)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        
        # Create tasks to read stdout and stderr
        stdout_task = asyncio.create_task(self.process.stdout.readline())
        stderr_task = asyncio.create_task(self.process.stderr.readline())
        
        while not self.process.stdout.at_eof() or not self.process.stderr.at_eof():
            # Wait for either stdout or stderr to have data
            done, pending = await asyncio.wait(
                [stdout_task, stderr_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                try:
                    line = await task
                    if line:
                        # Try to parse as JSON for structured output
                        try:
                            data = json.loads(line.decode())
                            await self._handle_json_output(data, log_widget, status_widget, progress_bar)
                        except json.JSONDecodeError:
                            # Regular text output
                            text = line.decode().strip()
                            log_widget.write_line(text)
                            
                            # Update status if it looks like a component name
                            if text.startswith("[") and "]" in text:
                                # Extract component name from format like "[1/5] Installing ComponentName"
                                parts = text.split(" ", 3)
                                if len(parts) >= 4:
                                    self.installing_component = parts[3]
                                    status_widget.update(f"Status: Installing {self.installing_component}")
                except Exception:
                    pass
                    
                # Recreate the completed task
                if task is stdout_task and not self.process.stdout.at_eof():
                    stdout_task = asyncio.create_task(self.process.stdout.readline())
                elif task is stderr_task and not self.process.stderr.at_eof():
                    stderr_task = asyncio.create_task(self.process.stderr.readline())
                    
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                
    async def _handle_json_output(self, data: dict, log_widget: Log, status_widget: Static, progress_bar: ProgressBar) -> None:
        """Handle JSON output from the installation process."""
        if not isinstance(data, dict):
            return
            
        # Handle different types of JSON output
        if "status" in data:
            status = data["status"]
            if status == "installing":
                component = data.get("component", "Unknown")
                self.installing_component = component
                status_widget.update(f"Status: Installing {component}")
                log_widget.write_line(f"📦 Installing {component}...")
                
            elif status == "success":
                component = data.get("component", "Unknown")
                log_widget.write_line(f"✅ Successfully installed {component}")
                
            elif status == "error":
                component = data.get("component", "Unknown")
                error_msg = data.get("message", "Unknown error")
                log_widget.write_line(f"❌ Failed to install {component}: {error_msg}")
                
        elif "summary" in data:
            # Summary output
            summary = data["summary"]
            installed = summary.get("installed", 0)
            failed = summary.get("failed", 0)
            total = summary.get("total", 0)
            status_widget.update(f"Status: Installed {installed}/{total} components ({failed} failed)")
            
        elif "progress" in data:
            # Progress update
            progress = data["progress"]
            if isinstance(progress, (int, float)):
                progress_bar.progress = progress
                
    async def cancel_installation(self) -> None:
        """Cancel the installation process."""
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                await self.process.wait()
                self.query_one("#status-text", Static).update("Status: Installation cancelled")
                self.query_one("#install-log", Log).write_line("⚠️ Installation cancelled by user")
            except Exception as e:
                self.query_one("#install-log", Log).write_line(f"❌ Error cancelling installation: {e}")
        else:
            await self.app.pop_screen()