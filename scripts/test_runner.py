#!/usr/bin/env python3
"""Test Runner Script for Environment Dev Deep Evaluation.

This script provides utilities for running tests, generating coverage reports,
and performing code quality checks.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.base import SystemComponentBase, OperationResult
from core.config import ConfigurationManager
from core.exceptions import EnvironmentDevDeepEvaluationError


@dataclass
class TestResults:
    """Container for test execution results."""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    errors: List[str] = None
    coverage_percentage: float = 0.0
    execution_time: float = 0.0
    
    def __post_init__(self):
        """Initialize errors list if None."""
        if self.errors is None:
            self.errors = []
    
    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def is_successful(self) -> bool:
        """Check if all tests passed."""
        return self.failed_tests == 0 and self.total_tests > 0


class TestRunner(SystemComponentBase):
    """Component for running tests and generating reports."""
    
    def __init__(self, config_manager: ConfigurationManager):
        """Initialize the test runner.
        
        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self._config_manager = config_manager
        self._project_root = Path(__file__).parent.parent
        self._tests_dir = self._project_root / "tests"
        self._coverage_dir = self._project_root / "coverage"
        
        # Test configuration
        self._pytest_args = [
            "--verbose",
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ]
        
        # Coverage configuration
        self._coverage_args = [
            "--cov=core",
            "--cov=validation",
            "--cov=analysis",
            "--cov=components",
            "--cov=detection",
            "--cov=installation",
            "--cov=integration",
            "--cov=storage",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term-missing",
            f"--cov-report=html:{self._coverage_dir / 'html'}",
            f"--cov-report=xml:{self._coverage_dir / 'coverage.xml'}"
        ]
    
    def validate_configuration(self) -> None:
        """Validate test runner configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self._config_manager:
            raise ValueError("Configuration manager is required")
    
    def initialize(self) -> OperationResult:
        """Initialize the test runner component."""
        try:
            self._logger.info("Initializing Test Runner")
            
            # Create coverage directory
            self._coverage_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if pytest is available
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return OperationResult(
                    success=False,
                    error="pytest is not installed. Please install it with: pip install pytest pytest-cov"
                )
            
            self._logger.info(f"pytest version: {result.stdout.strip()}")
            
            return OperationResult(
                success=True,
                message="Test Runner initialized successfully"
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize Test Runner: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def cleanup(self) -> OperationResult:
        """Cleanup the test runner component."""
        try:
            self._logger.info("Cleaning up Test Runner")
            return OperationResult(
                success=True,
                message="Test Runner cleaned up successfully"
            )
        except Exception as e:
            error_msg = f"Failed to cleanup Test Runner: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def run_tests(
        self,
        test_path: Optional[str] = None,
        include_coverage: bool = True,
        parallel: bool = False,
        verbose: bool = True
    ) -> OperationResult:
        """Run tests with optional coverage reporting.
        
        Args:
            test_path: Specific test file or directory to run
            include_coverage: Whether to include coverage reporting
            parallel: Whether to run tests in parallel
            verbose: Whether to use verbose output
            
        Returns:
            OperationResult containing TestResults
        """
        try:
            self._logger.info(f"Running tests: {test_path or 'all tests'}")
            start_time = datetime.now()
            
            # Build pytest command
            cmd = [sys.executable, "-m", "pytest"]
            
            # Add test path or default to tests directory
            if test_path:
                cmd.append(test_path)
            else:
                cmd.append(str(self._tests_dir))
            
            # Add pytest arguments
            cmd.extend(self._pytest_args)
            
            # Add coverage arguments if requested
            if include_coverage:
                cmd.extend(self._coverage_args)
            
            # Add parallel execution if requested
            if parallel:
                try:
                    import pytest_xdist
                    cmd.extend(["-n", "auto"])
                    self._logger.info("Running tests in parallel")
                except ImportError:
                    self._logger.warning("pytest-xdist not available, running tests sequentially")
            
            # Set verbosity
            if not verbose:
                cmd = [arg for arg in cmd if arg != "--verbose"]
                cmd.append("-q")
            
            self._logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self._project_root,
                capture_output=True,
                text=True
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Parse test results
            test_results = self._parse_pytest_output(result.stdout, result.stderr)
            test_results.execution_time = execution_time
            
            # Parse coverage if available
            if include_coverage:
                coverage_percentage = self._parse_coverage_output(result.stdout)
                test_results.coverage_percentage = coverage_percentage
            
            # Log results
            self._log_test_results(test_results)
            
            return OperationResult(
                success=test_results.is_successful,
                message=f"Tests completed: {test_results.passed_tests}/{test_results.total_tests} passed",
                data=test_results
            )
            
        except Exception as e:
            error_msg = f"Failed to run tests: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def run_specific_module_tests(self, module_name: str) -> OperationResult:
        """Run tests for a specific module.
        
        Args:
            module_name: Name of the module to test (e.g., 'core', 'validation')
            
        Returns:
            OperationResult containing TestResults
        """
        test_path = self._tests_dir / module_name
        
        if not test_path.exists():
            return OperationResult(
                success=False,
                error=f"Test directory not found: {test_path}"
            )
        
        return self.run_tests(str(test_path), include_coverage=True)
    
    def run_coverage_only(self) -> OperationResult:
        """Run coverage analysis without running tests.
        
        Returns:
            OperationResult containing coverage percentage
        """
        try:
            self._logger.info("Running coverage analysis")
            
            cmd = [
                sys.executable, "-m", "coverage", "run",
                "--source=core,validation,analysis,components,detection,installation,integration,storage",
                "-m", "pytest", str(self._tests_dir)
            ]
            
            # Run coverage
            result = subprocess.run(
                cmd,
                cwd=self._project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return OperationResult(
                    success=False,
                    error=f"Coverage analysis failed: {result.stderr}"
                )
            
            # Generate coverage report
            report_cmd = [sys.executable, "-m", "coverage", "report"]
            report_result = subprocess.run(
                report_cmd,
                cwd=self._project_root,
                capture_output=True,
                text=True
            )
            
            coverage_percentage = self._parse_coverage_output(report_result.stdout)
            
            return OperationResult(
                success=True,
                message=f"Coverage analysis completed: {coverage_percentage:.1f}%",
                data=coverage_percentage
            )
            
        except Exception as e:
            error_msg = f"Failed to run coverage analysis: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def generate_test_report(self, output_file: Optional[str] = None) -> OperationResult:
        """Generate a comprehensive test report.
        
        Args:
            output_file: Optional output file path for the report
            
        Returns:
            OperationResult indicating success/failure
        """
        try:
            self._logger.info("Generating comprehensive test report")
            
            # Run all tests with coverage
            test_result = self.run_tests(include_coverage=True)
            
            if not test_result.success:
                return test_result
            
            test_results = test_result.data
            
            # Generate report data
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self._project_root),
                "test_summary": {
                    "total_tests": test_results.total_tests,
                    "passed_tests": test_results.passed_tests,
                    "failed_tests": test_results.failed_tests,
                    "skipped_tests": test_results.skipped_tests,
                    "success_rate": test_results.success_rate,
                    "execution_time": test_results.execution_time
                },
                "coverage": {
                    "percentage": test_results.coverage_percentage,
                    "html_report": str(self._coverage_dir / "html" / "index.html"),
                    "xml_report": str(self._coverage_dir / "coverage.xml")
                },
                "errors": test_results.errors
            }
            
            # Save report
            if output_file:
                output_path = Path(output_file)
            else:
                output_path = self._project_root / "test_report.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Test report saved to: {output_path}")
            
            return OperationResult(
                success=True,
                message=f"Test report generated: {output_path}",
                data=str(output_path)
            )
            
        except Exception as e:
            error_msg = f"Failed to generate test report: {e}"
            self._logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestResults:
        """Parse pytest output to extract test results.
        
        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest
            
        Returns:
            TestResults object
        """
        results = TestResults()
        
        # Parse test summary line
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'error' in line:
                # Look for summary line like "5 passed, 2 failed, 1 skipped"
                if 'passed' in line:
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'passed' and i > 0:
                                results.passed_tests = int(parts[i-1])
                            elif part == 'failed' and i > 0:
                                results.failed_tests = int(parts[i-1])
                            elif part == 'skipped' and i > 0:
                                results.skipped_tests = int(parts[i-1])
                    except (ValueError, IndexError):
                        pass
        
        results.total_tests = results.passed_tests + results.failed_tests + results.skipped_tests
        
        # Extract errors from stderr
        if stderr:
            results.errors.append(stderr)
        
        return results
    
    def _parse_coverage_output(self, output: str) -> float:
        """Parse coverage percentage from output.
        
        Args:
            output: Coverage output text
            
        Returns:
            Coverage percentage as float
        """
        lines = output.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                try:
                    # Extract percentage from line like "TOTAL    100    25    75%"
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            return float(part[:-1])
                except (ValueError, IndexError):
                    pass
        
        return 0.0
    
    def _log_test_results(self, results: TestResults) -> None:
        """Log test results summary.
        
        Args:
            results: TestResults object to log
        """
        self._logger.info(f"Test Results Summary:")
        self._logger.info(f"  Total Tests: {results.total_tests}")
        self._logger.info(f"  Passed: {results.passed_tests}")
        self._logger.info(f"  Failed: {results.failed_tests}")
        self._logger.info(f"  Skipped: {results.skipped_tests}")
        self._logger.info(f"  Success Rate: {results.success_rate:.1f}%")
        self._logger.info(f"  Coverage: {results.coverage_percentage:.1f}%")
        self._logger.info(f"  Execution Time: {results.execution_time:.2f}s")
        
        if results.errors:
            self._logger.warning(f"Errors encountered: {len(results.errors)}")
            for error in results.errors:
                self._logger.error(f"  {error}")


def main():
    """Main entry point for the test runner script."""
    parser = argparse.ArgumentParser(
        description="Run tests and generate coverage reports for Environment Dev Deep Evaluation"
    )
    
    parser.add_argument(
        "--test-path",
        type=str,
        help="Specific test file or directory to run"
    )
    
    parser.add_argument(
        "--module",
        type=str,
        help="Specific module to test (e.g., 'core', 'validation')"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Run coverage analysis only"
    )
    
    parser.add_argument(
        "--report",
        type=str,
        help="Generate comprehensive test report to specified file"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        if args.config:
            config_manager.load_from_file(args.config)
        
        # Initialize test runner
        test_runner = TestRunner(config_manager)
        init_result = test_runner.initialize()
        
        if not init_result.success:
            print(f"Error: {init_result.error}")
            sys.exit(1)
        
        # Execute requested operation
        if args.coverage_only:
            result = test_runner.run_coverage_only()
        elif args.report:
            result = test_runner.generate_test_report(args.report)
        elif args.module:
            result = test_runner.run_specific_module_tests(args.module)
        else:
            result = test_runner.run_tests(
                test_path=args.test_path,
                include_coverage=not args.no_coverage,
                parallel=args.parallel,
                verbose=not args.quiet
            )
        
        # Print results
        print(f"\n{result.message}")
        
        if result.data and hasattr(result.data, 'success_rate'):
            test_results = result.data
            print(f"Success Rate: {test_results.success_rate:.1f}%")
            print(f"Coverage: {test_results.coverage_percentage:.1f}%")
        
        # Cleanup
        test_runner.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()