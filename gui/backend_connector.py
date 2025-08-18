"""
Backend Connector for the EnvironmentDev_MISA GUI.
This module acts as a bridge between the GUI frontend and the core CLI logic.
It provides methods to call CLI functions and retrieve results in a format suitable for the GUI.
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Union
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Adjust level as needed

# Create a console handler for immediate feedback during development
# In production, this might go to a file or be configured elsewhere
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class BackendConnectorError(Exception):
    """Custom exception for BackendConnector errors."""
    pass

class BackendConnector:
    """
    A class to connect the GUI to the backend logic via CLI commands.
    It handles execution, error checking, and JSON parsing of CLI outputs.
    """
    
    # Constants for CLI command paths
    # Using 'python -m cli.main' assumes the package is installed or PYTHONPATH includes the root
    # If running as a script, you might need to adjust this path
    CLI_MODULE_PATH = ["python", "-m", "cli.main"]
    
    @staticmethod
    def _execute_cli_command(command_parts: List[str], cwd: Union[str, Path, None]=None) -> Dict[str, Any]:
        """
        Executes a CLI command and returns structured output.

        Args:
            command_parts (List[str]): The parts of the CLI command to execute.
                                         Should not include 'python' or '-m cli.main'.
            cwd (Union[str, Path, None], optional): Working directory for the command.
                                                     Defaults to None (uses current directory).

        Returns:
            Dict[str, Any]: A dictionary with keys:
                - 'success' (bool): True if command executed without error.
                - 'data' (Any): Parsed JSON data if successful, None otherwise.
                - 'raw_stdout' (str): Raw standard output from the command.
                - 'error' (str): Error message if unsuccessful, None otherwise.
        """
        full_command = BackendConnector.CLI_MODULE_PATH + command_parts
        logger.debug(f"Executing CLI command: {' '.join(full_command)}")
        
        try:
            # Use shell=False for security, pass command as a list
            # Capture both stdout and stderr
            # Timeout can be added if commands are expected to be long-running
            # cwd parameter allows specifying the working directory if needed
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=False, # Don't raise exception on non-zero exit code, we handle it
                cwd=cwd
            )
            
            logger.debug(f"CLI command exited with code: {result.returncode}")
            logger.debug(f"CLI stdout: {result.stdout[:200]}...") # Log first 200 chars
            if result.stderr:
                logger.debug(f"CLI stderr: {result.stderr[:200]}...")

            if result.returncode != 0:
                # Command failed
                error_msg = f"CLI command failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "data": None,
                    "raw_stdout": result.stdout,
                    "error": error_msg
                }

            # Command succeeded
            # Try to parse stdout as JSON
            try:
                parsed_data = json.loads(result.stdout) if result.stdout.strip() else {}
                logger.debug("CLI command output successfully parsed as JSON.")
                return {
                    "success": True,
                    "data": parsed_data,
                    "raw_stdout": result.stdout,
                    "error": None
                }
            except json.JSONDecodeError as e:
                # stdout is not valid JSON
                error_msg = f"CLI command succeeded but output is not valid JSON: {e}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "data": None,
                    "raw_stdout": result.stdout,
                    "error": error_msg
                }

        except FileNotFoundError:
            # Most likely means 'python' executable wasn't found
            error_msg = "Failed to execute CLI command: 'python' not found. Is Python installed and in PATH?"
            logger.critical(error_msg)
            return {
                "success": False,
                "data": None,
                "raw_stdout": "",
                "error": error_msg
            }
        except Exception as e:
            # Catch-all for other unexpected errors during subprocess execution
            error_msg = f"Unexpected error occurred while executing CLI command: {e}"
            logger.exception(error_msg) # Logs the full traceback
            return {
                "success": False,
                "data": None,
                "raw_stdout": "",
                "error": error_msg
            }

    @staticmethod
    def list_components(gap_analysis: bool = False, json_output: bool = True) -> Dict[str, Any]:
        """
        Calls the equivalent of `list_components` CLI command.

        Args:
            gap_analysis (bool): If True, includes gap analysis information.
            json_output (bool): If True, requests JSON output from the CLI.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["list-components"]
        if gap_analysis:
            cmd.append("--gap-analysis")
        if json_output:
            cmd.append("--json")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def get_component_info(component_name: str, json_output: bool = True) -> Dict[str, Any]:
        """
        Calls the equivalent of `info_command` CLI command for a specific component.

        Args:
            component_name (str): The name of the component to get info for.
            json_output (bool): If True, requests JSON output from the CLI.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["info", component_name]
        if json_output:
            cmd.append("--json")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def run_doctor(json_output: bool = True, verbose: bool = False) -> Dict[str, Any]:
        """
        Calls the equivalent of `doctor` CLI command.

        Args:
            json_output (bool): If True, requests JSON output from the CLI.
            verbose (bool): If True, requests verbose output.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["doctor"]
        if json_output:
            cmd.append("--json")
        if verbose:
            cmd.append("--verbose")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def install_component(component_name: str, silent: bool = True) -> Dict[str, Any]:
        """
        Initiates the installation of a component via the CLI.

        Args:
            component_name (str): The name of the component to install.
            silent (bool): If True, runs the installer silently.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["install", component_name]
        if silent:
            cmd.append("--silent")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def uninstall_component(component_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Initiates the uninstallation of a component via the CLI.

        Args:
            component_name (str): The name of the component to uninstall.
            force (bool): If True, forces uninstallation without confirmation prompts.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["uninstall", component_name]
        if force:
            cmd.append("--force")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def generate_report(format_type: str = "json", include_plugins: bool = False, output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        """
        Calls the equivalent of `report` CLI command.

        Args:
            format_type (str): The format of the report ('json' or 'html').
            include_plugins (bool): If True, includes plugin data in the report.
            output_file (Union[str, Path, None]): Optional path to save the report directly.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["report", f"--format={format_type}"]
        if include_plugins:
            cmd.append("--include-plugins")
        if output_file:
            cmd.extend(["--output", str(output_file)])
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def update_hashes(only_hashes: bool = False) -> Dict[str, Any]:
        """
        Calls the equivalent of `update` CLI command, primarily for updating hashes.

        Args:
            only_hashes (bool): If True, updates only hashes without installing/updating components.

        Returns:
            Dict[str, Any]: Structured result from `_execute_cli_command`.
        """
        cmd = ["update"]
        if only_hashes:
            cmd.append("--hashes-only")
            
        return BackendConnector._execute_cli_command(cmd)

    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """
        Gets a comprehensive system status by running the doctor command.
        This is an alias for run_doctor with appropriate flags for a general status check.

        Returns:
            Dict[str, Any]: Structured result from `run_doctor`.
        """
        # Run doctor in a standard way for system status
        return BackendConnector.run_doctor(json_output=True, verbose=False)