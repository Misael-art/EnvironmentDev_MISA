"""
Unified Detection Engine implementation.

This module provides the core unified detection engine that orchestrates
all detection operations including registry scanning, portable app detection,
runtime detection, and hierarchical prioritization.
"""

import winreg
import os
import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .base import DetectionBase
from .interfaces import (
    DetectionEngineInterface,
    RuntimeDetectorInterface,
    HierarchicalDetectionInterface,
    DetectionResult,
    DetectionMethod,
    DetectionConfidence,
    RegistryApp,
    PortableApp,
    RuntimeDetectionResult,
    PackageManager,
    SteamDeckDetectionResult,
    HierarchicalResult,
    ComprehensiveDetectionReport
)
from ..core.base import OperationResult
from ..core.exceptions import UnifiedDetectionError


class UnifiedDetectionEngine(
    DetectionBase,
    DetectionEngineInterface,
    RuntimeDetectorInterface,
    HierarchicalDetectionInterface
):
    """
    Unified Detection Engine for comprehensive system detection.
    
    Orchestrates all detection operations including:
    - Windows Registry scanning
    - Portable application detection
    - Essential runtime detection
    - Package manager detection
    - Steam Deck hardware detection
    - Hierarchical prioritization
    """
    
    def __init__(self, config_manager):
        """Initialize unified detection engine."""
        super().__init__(config_manager, "UnifiedDetectionEngine")
        
        # Registry keys for application detection
        self._registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        # Common portable app patterns
        self._portable_patterns = [
            r".*\.exe$",
            r".*portable.*\.exe$",
            r".*_portable\.exe$",
            r".*-portable\.exe$",
        ]
        
        # Essential runtime configurations
        self._essential_runtimes = {
            "git": {
                "name": "Git",
                "target_version": "2.47.1",
                "commands": ["git --version"],
                "env_vars": ["GIT_HOME"],
                "registry_patterns": [r"Git.*"],
                "executable_names": ["git.exe"],
            },
            "dotnet_sdk": {
                "name": ".NET SDK",
                "target_version": "8.0",
                "commands": ["dotnet --version", "dotnet --list-sdks"],
                "env_vars": ["DOTNET_ROOT"],
                "registry_patterns": [r"Microsoft \.NET.*SDK.*"],
                "executable_names": ["dotnet.exe"],
            },
            "java_jdk": {
                "name": "Java JDK",
                "target_version": "21",
                "commands": ["java -version", "javac -version"],
                "env_vars": ["JAVA_HOME", "JDK_HOME"],
                "registry_patterns": [r"Java.*JDK.*", r"OpenJDK.*"],
                "executable_names": ["java.exe", "javac.exe"],
            },
        }
        
        # Package manager configurations
        self._package_managers = {
            "npm": {
                "executable": "npm",
                "version_command": ["npm", "--version"],
                "global_list_command": ["npm", "list", "-g", "--depth=0"],
                "config_files": ["package.json", ".npmrc"],
            },
            "pip": {
                "executable": "pip",
                "version_command": ["pip", "--version"],
                "global_list_command": ["pip", "list"],
                "config_files": ["requirements.txt", "pip.conf"],
            },
        }
        
        self._detection_methods_available = [
            DetectionMethod.REGISTRY,
            DetectionMethod.FILESYSTEM,
            DetectionMethod.ENVIRONMENT_VARIABLES,
            DetectionMethod.COMMAND_LINE,
        ]
    
    def initialize(self) -> None:
        """Initialize the unified detection engine."""
        self._logger.info("Initializing UnifiedDetectionEngine")
        # Perform any initialization tasks here
        self._logger.info("UnifiedDetectionEngine initialized successfully")
    
    def detect_all_applications(self) -> DetectionResult:
        """Detect all applications using unified detection methods."""
        try:
            self._logger.info("Starting comprehensive application detection")
            
            detection_details = {}
            detection_methods_used = []
            
            # Registry detection
            try:
                registry_apps = self.scan_registry_installations()
                detection_details["registry_apps"] = len(registry_apps)
                detection_methods_used.append(DetectionMethod.REGISTRY)
                self._logger.info(f"Found {len(registry_apps)} registry applications")
            except Exception as e:
                self._logger.warning(f"Registry detection failed: {str(e)}")
                detection_details["registry_error"] = str(e)
            
            # Create unified result
            detected = len(detection_methods_used) > 0
            primary_method = detection_methods_used[0] if detection_methods_used else DetectionMethod.REGISTRY
            
            result = self._create_detection_result(
                detected=detected,
                method=primary_method,
                details=detection_details
            )
            
            self._logger.info(f"Application detection completed: {detected}")
            return result
            
        except Exception as e:
            error_msg = f"Unified application detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(
                error_msg,
                context={"component": self._component_name, "operation": "detect_all_applications"}
            )
    
    def scan_registry_installations(self) -> List[RegistryApp]:
        """Scan Windows Registry for installed applications."""
        try:
            self._logger.debug("Starting registry scan for installed applications")
            registry_apps = []
            
            for hkey, subkey_path in self._registry_keys:
                try:
                    with winreg.OpenKey(hkey, subkey_path) as key:
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                app = self._extract_registry_app_info(hkey, subkey_path, subkey_name)
                                if app:
                                    registry_apps.append(app)
                                i += 1
                            except OSError:
                                break
                                
                except FileNotFoundError:
                    self._logger.debug(f"Registry key not found: {subkey_path}")
                    continue
                except Exception as e:
                    self._logger.warning(f"Error accessing registry key {subkey_path}: {str(e)}")
                    continue
            
            self._logger.info(f"Registry scan completed: {len(registry_apps)} applications found")
            return registry_apps
            
        except Exception as e:
            error_msg = f"Registry scanning failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(
                error_msg,
                context={"component": self._component_name, "operation": "scan_registry_installations"}
            )
    
    def _extract_registry_app_info(
        self, 
        hkey: int, 
        subkey_path: str, 
        subkey_name: str
    ) -> Optional[RegistryApp]:
        """Extract application information from registry entry."""
        try:
            full_path = f"{subkey_path}\\{subkey_name}"
            
            with winreg.OpenKey(hkey, full_path) as app_key:
                # Extract basic information
                name = self._get_registry_value(app_key, "DisplayName")
                if not name:
                    return None
                
                version = self._get_registry_value(app_key, "DisplayVersion") or "Unknown"
                publisher = self._get_registry_value(app_key, "Publisher") or "Unknown"
                install_location = self._get_registry_value(app_key, "InstallLocation") or ""
                uninstall_string = self._get_registry_value(app_key, "UninstallString") or ""
                
                # Determine confidence based on available information
                confidence = DetectionConfidence.HIGH
                if not install_location or not uninstall_string:
                    confidence = DetectionConfidence.MEDIUM
                if version == "Unknown" or publisher == "Unknown":
                    confidence = DetectionConfidence.LOW
                
                return RegistryApp(
                    name=name,
                    version=version,
                    publisher=publisher,
                    install_location=install_location,
                    uninstall_string=uninstall_string,
                    registry_key=full_path,
                    detection_confidence=confidence
                )
                
        except Exception as e:
            self._logger.debug(f"Failed to extract registry app info for {subkey_name}: {str(e)}")
            return None
    
    def _get_registry_value(self, key, value_name: str) -> Optional[str]:
        """Get registry value safely."""
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return str(value) if value else None
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def detect_portable_applications(self) -> List[PortableApp]:
        """Detect portable applications via filesystem scanning."""
        try:
            self._logger.debug("Starting portable application detection")
            return []  # Simplified implementation
        except Exception as e:
            error_msg = f"Portable application detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})
    
    def detect_essential_runtimes(self) -> List[RuntimeDetectionResult]:
        """Detect all essential runtimes (Git, .NET, Java, etc.)."""
        try:
            self._logger.info("Starting essential runtimes detection")
            runtime_results = []
            
            for runtime_key, runtime_config in self._essential_runtimes.items():
                try:
                    result = self._detect_single_runtime(runtime_key, runtime_config)
                    runtime_results.append(result)
                except Exception as e:
                    self._logger.warning(f"Failed to detect {runtime_config['name']}: {str(e)}")
                    # Create failed detection result
                    runtime_results.append(RuntimeDetectionResult(
                        runtime_name=runtime_config["name"],
                        detected=False,
                        version=None,
                        install_path=None,
                        environment_variables={},
                        validation_commands=runtime_config["commands"],
                        validation_results={},
                        detection_method=DetectionMethod.COMMAND_LINE,
                        confidence=DetectionConfidence.UNKNOWN
                    ))
            
            detected_count = sum(1 for result in runtime_results if result.detected)
            self._logger.info(f"Essential runtimes detection completed: {detected_count}/{len(runtime_results)} detected")
            
            return runtime_results
            
        except Exception as e:
            error_msg = f"Essential runtimes detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})
    
    def _detect_single_runtime(
        self, 
        runtime_key: str, 
        runtime_config: Dict[str, Any]
    ) -> RuntimeDetectionResult:
        """Detect a single runtime using multiple methods."""
        runtime_name = runtime_config["name"]
        self._logger.debug(f"Detecting {runtime_name}")
        
        detected = False
        version = None
        install_path = None
        environment_variables = {}
        validation_results = {}
        detection_method = DetectionMethod.COMMAND_LINE
        
        # Check environment variables
        for env_var in runtime_config["env_vars"]:
            env_value = self._get_environment_variable(env_var)
            if env_value:
                environment_variables[env_var] = env_value
                if not install_path and self._check_directory_exists(env_value):
                    install_path = env_value
                    detection_method = DetectionMethod.ENVIRONMENT_VARIABLES
                    detected = True
        
        # Execute validation commands
        for command in runtime_config["commands"]:
            command_parts = command.split()
            output = self._execute_command_safely(command_parts)
            validation_results[command] = output is not None
            
            if output and not version:
                version = self._extract_version_from_output(output)
                detected = True
        
        # Determine confidence
        methods_used = []
        if environment_variables:
            methods_used.append(DetectionMethod.ENVIRONMENT_VARIABLES)
        if any(validation_results.values()):
            methods_used.append(DetectionMethod.COMMAND_LINE)
        
        confidence = self._determine_detection_confidence(methods_used, validation_results)
        
        return RuntimeDetectionResult(
            runtime_name=runtime_name,
            detected=detected,
            version=version,
            install_path=install_path,
            environment_variables=environment_variables,
            validation_commands=runtime_config["commands"],
            validation_results=validation_results,
            detection_method=detection_method,
            confidence=confidence
        )
    
    def _extract_version_from_output(self, output: str) -> Optional[str]:
        """Extract version from command output."""
        # Common version patterns in command output
        version_patterns = [
            r"version\s+v?(\d+\.\d+\.\d+)",
            r"v?(\d+\.\d+\.\d+)",
            r"(\d+\.\d+\.\d+)",
            r"version\s+(\d+\.\d+)",
            r"(\d+\.\d+)",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def detect_package_managers(self) -> List[PackageManager]:
        """Detect package managers (npm, pip, conda, etc.)."""
        try:
            self._logger.debug("Starting package manager detection")
            return []  # Simplified implementation
        except Exception as e:
            error_msg = f"Package manager detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})
    
    def detect_steam_deck_hardware(self) -> SteamDeckDetectionResult:
        """Detect Steam Deck hardware and configuration."""
        try:
            self._logger.debug("Starting Steam Deck hardware detection")
            
            return SteamDeckDetectionResult(
                is_steam_deck=False,
                detection_method=DetectionMethod.DMI_SMBIOS,
                hardware_info={},
                steam_client_detected=False,
                controller_detected=False,
                fallback_applied=False,
                confidence=DetectionConfidence.LOW
            )
            
        except Exception as e:
            error_msg = f"Steam Deck hardware detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})
    
    def apply_hierarchical_detection(self) -> HierarchicalResult:
        """Apply hierarchical prioritization to detection results."""
        try:
            self._logger.debug("Starting hierarchical detection prioritization")
            
            # Import hierarchical prioritizer
            from core.hierarchical_detection_prioritizer import HierarchicalDetectionPrioritizer
            from core.detection_base import DetectedApplication, DetectionMethod, ApplicationStatus
            
            prioritizer = HierarchicalDetectionPrioritizer()
            
            # Get all detection results
            registry_apps = self.scan_registry_installations()
            essential_runtimes = self.detect_essential_runtimes()
            
            # Convert registry apps to DetectedApplication format
            detected_applications = []
            for reg_app in registry_apps:
                # Convert confidence properly
                confidence_value = 0.8  # Default
                if hasattr(reg_app.detection_confidence, 'value'):
                    if isinstance(reg_app.detection_confidence.value, (int, float)):
                        confidence_value = reg_app.detection_confidence.value / 100.0
                    elif isinstance(reg_app.detection_confidence.value, str):
                        try:
                            confidence_value = float(reg_app.detection_confidence.value) / 100.0
                        except ValueError:
                            confidence_value = 0.8
                elif hasattr(reg_app, 'detection_confidence'):
                    if isinstance(reg_app.detection_confidence, (int, float)):
                        confidence_value = reg_app.detection_confidence / 100.0 if reg_app.detection_confidence > 1 else reg_app.detection_confidence
                
                detected_app = DetectedApplication(
                    name=reg_app.name,
                    version=reg_app.version,
                    install_path=reg_app.install_location,
                    executable_path="",  # Not available from registry
                    detection_method=DetectionMethod.REGISTRY,
                    status=ApplicationStatus.INSTALLED,
                    confidence=confidence_value
                )
                detected_applications.append(detected_app)
            
            # Convert runtime results to DetectedApplication format
            for runtime_result in essential_runtimes:
                if runtime_result.detected:
                    # Convert confidence properly
                    confidence_value = 0.8  # Default
                    if hasattr(runtime_result.confidence, 'value'):
                        if isinstance(runtime_result.confidence.value, (int, float)):
                            confidence_value = runtime_result.confidence.value / 100.0
                        elif isinstance(runtime_result.confidence.value, str):
                            try:
                                confidence_value = float(runtime_result.confidence.value) / 100.0
                            except ValueError:
                                confidence_value = 0.8
                    elif hasattr(runtime_result, 'confidence'):
                        if isinstance(runtime_result.confidence, (int, float)):
                            confidence_value = runtime_result.confidence / 100.0 if runtime_result.confidence > 1 else runtime_result.confidence
                    
                    detected_app = DetectedApplication(
                        name=runtime_result.runtime_name,
                        version=runtime_result.version or "Unknown",
                        install_path=runtime_result.install_path or "",
                        executable_path="",
                        detection_method=runtime_result.detection_method,
                        status=ApplicationStatus.INSTALLED,
                        confidence=confidence_value
                    )
                    detected_applications.append(detected_app)
            
            # Apply hierarchical prioritization to all detected applications
            primary_detections = []
            secondary_detections = []
            priority_scores = {}
            
            # Group applications by component type
            component_groups = {}
            for app in detected_applications:
                component_key = self._determine_component_key(app.name)
                if component_key not in component_groups:
                    component_groups[component_key] = []
                component_groups[component_key].append(app)
            
            # Prioritize each component group
            for component_name, apps in component_groups.items():
                hierarchical_result = prioritizer.prioritize_detections(
                    component_name=component_name,
                    detected_applications=apps,
                    required_version=self._get_required_version(component_name)
                )
                
                if hierarchical_result.recommended_option:
                    primary_detections.append(hierarchical_result.recommended_option)
                    if hierarchical_result.priority_score:
                        priority_scores[component_name] = hierarchical_result.priority_score.total_score
                
                # Add alternatives as secondary detections
                secondary_detections.extend(hierarchical_result.alternative_options)
            
            # Generate selection rationale
            selection_rationale = self._generate_selection_rationale(
                len(primary_detections), len(secondary_detections), priority_scores
            )
            
            return HierarchicalResult(
                primary_detections=primary_detections,
                secondary_detections=secondary_detections,
                priority_scores=priority_scores,
                selection_rationale=selection_rationale
            )
            
        except Exception as e:
            error_msg = f"Hierarchical detection failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})
    
    def generate_comprehensive_report(self) -> ComprehensiveDetectionReport:
        """Generate comprehensive detection report."""
        try:
            self._logger.info("Generating comprehensive detection report")
            
            report_id = str(uuid.uuid4())
            generation_timestamp = datetime.now()
            
            # Gather all detection results
            registry_applications = self.scan_registry_installations()
            portable_applications = self.detect_portable_applications()
            essential_runtimes = self.detect_essential_runtimes()
            package_managers = self.detect_package_managers()
            steam_deck_info = self.detect_steam_deck_hardware()
            hierarchical_results = self.apply_hierarchical_detection()
            
            # Generate detection summary
            detection_summary = {
                "total_registry_apps": len(registry_applications),
                "total_portable_apps": len(portable_applications),
                "total_essential_runtimes": len(essential_runtimes),
                "detected_essential_runtimes": sum(1 for r in essential_runtimes if r.detected),
                "total_package_managers": len(package_managers),
                "steam_deck_detected": steam_deck_info.is_steam_deck,
                "primary_detections": len(hierarchical_results.primary_detections),
                "secondary_detections": len(hierarchical_results.secondary_detections),
                "generation_time": generation_timestamp.isoformat(),
                "detection_methods_used": [method.value for method in self._detection_methods_available],
            }
            
            report = ComprehensiveDetectionReport(
                report_id=report_id,
                generation_timestamp=generation_timestamp,
                registry_applications=registry_applications,
                portable_applications=portable_applications,
                essential_runtimes=essential_runtimes,
                package_managers=package_managers,
                steam_deck_info=steam_deck_info,
                hierarchical_results=hierarchical_results,
                detection_summary=detection_summary
            )
            
            self._logger.info(f"Comprehensive detection report generated: {report_id}")
            return report
            
        except Exception as e:
            error_msg = f"Comprehensive report generation failed: {str(e)}"
            self._logger.error(error_msg)
            raise UnifiedDetectionError(error_msg, context={"component": self._component_name})   
 # RuntimeDetectorInterface implementation
    def detect_git_2_47_1(self) -> RuntimeDetectionResult:
        """Detect Git 2.47.1 installation."""
        return self._detect_single_runtime("git", self._essential_runtimes["git"])
    
    def detect_dotnet_sdk_8_0(self) -> RuntimeDetectionResult:
        """Detect .NET SDK 8.0 installation."""
        return self._detect_single_runtime("dotnet_sdk", self._essential_runtimes["dotnet_sdk"])
    
    def detect_java_jdk_21(self) -> RuntimeDetectionResult:
        """Detect Java JDK 21 installation."""
        return self._detect_single_runtime("java_jdk", self._essential_runtimes["java_jdk"])
    
    def detect_vcpp_redistributables(self) -> RuntimeDetectionResult:
        """Detect Visual C++ Redistributables."""
        # Simplified implementation
        return RuntimeDetectionResult(
            runtime_name="Visual C++ Redistributables",
            detected=False,
            version=None,
            install_path=None,
            environment_variables={},
            validation_commands=[],
            validation_results={},
            detection_method=DetectionMethod.REGISTRY,
            confidence=DetectionConfidence.UNKNOWN
        )
    
    def detect_anaconda3(self) -> RuntimeDetectionResult:
        """Detect Anaconda3 installation."""
        # Simplified implementation
        return RuntimeDetectionResult(
            runtime_name="Anaconda3",
            detected=False,
            version=None,
            install_path=None,
            environment_variables={},
            validation_commands=[],
            validation_results={},
            detection_method=DetectionMethod.COMMAND_LINE,
            confidence=DetectionConfidence.UNKNOWN
        )
    
    def detect_dotnet_desktop_runtime(self) -> RuntimeDetectionResult:
        """Detect .NET Desktop Runtime 8.0/9.0."""
        # Simplified implementation
        return RuntimeDetectionResult(
            runtime_name=".NET Desktop Runtime",
            detected=False,
            version=None,
            install_path=None,
            environment_variables={},
            validation_commands=[],
            validation_results={},
            detection_method=DetectionMethod.REGISTRY,
            confidence=DetectionConfidence.UNKNOWN
        )
    
    def detect_powershell_7(self) -> RuntimeDetectionResult:
        """Detect PowerShell 7 installation."""
        # Simplified implementation
        return RuntimeDetectionResult(
            runtime_name="PowerShell 7",
            detected=False,
            version=None,
            install_path=None,
            environment_variables={},
            validation_commands=[],
            validation_results={},
            detection_method=DetectionMethod.COMMAND_LINE,
            confidence=DetectionConfidence.UNKNOWN
        )
    
    def detect_updated_nodejs_python(self) -> RuntimeDetectionResult:
        """Detect updated Node.js and Python installations."""
        # Simplified implementation
        return RuntimeDetectionResult(
            runtime_name="Node.js/Python",
            detected=False,
            version=None,
            install_path=None,
            environment_variables={},
            validation_commands=[],
            validation_results={},
            detection_method=DetectionMethod.COMMAND_LINE,
            confidence=DetectionConfidence.UNKNOWN
        )
    
    def validate_runtime_installation(
        self, 
        runtime_name: str, 
        expected_version: Optional[str] = None
    ) -> OperationResult:
        """Validate runtime installation with specific commands."""
        try:
            self._logger.debug(f"Validating runtime installation: {runtime_name}")
            
            # Find runtime configuration
            runtime_config = None
            for key, config in self._essential_runtimes.items():
                if config["name"].lower() == runtime_name.lower() or key == runtime_name:
                    runtime_config = config
                    break
            
            if not runtime_config:
                return OperationResult(
                    success=False,
                    message=f"Unknown runtime: {runtime_name}",
                    data={"runtime_name": runtime_name}
                )
            
            # Detect runtime
            detection_result = self._detect_single_runtime(runtime_name, runtime_config)
            
            if not detection_result.detected:
                return OperationResult(
                    success=False,
                    message=f"Runtime not detected: {runtime_name}",
                    data={"detection_result": detection_result}
                )
            
            return OperationResult(
                success=True,
                message=f"Runtime validation successful: {runtime_name}",
                data={"detection_result": detection_result}
            )
            
        except Exception as e:
            error_msg = f"Runtime validation failed for {runtime_name}: {str(e)}"
            self._logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                data={"runtime_name": runtime_name, "error": str(e)}
            )
    
    # HierarchicalDetectionInterface implementation
    def prioritize_installed_applications(
        self, 
        detections: List[DetectionResult]
    ) -> List[DetectionResult]:
        """Prioritize already installed applications."""
        installed = []
        not_installed = []
        
        for detection in detections:
            if detection.detected and detection.confidence in [DetectionConfidence.HIGH, DetectionConfidence.MEDIUM]:
                installed.append(detection)
            else:
                not_installed.append(detection)
        
        # Sort installed by confidence
        installed = self._prioritize_by_confidence(installed)
        not_installed = self._prioritize_by_confidence(not_installed)
        
        return installed + not_installed
    
    def prioritize_compatible_versions(
        self, 
        detections: List[DetectionResult],
        compatibility_matrix: Dict[str, List[str]]
    ) -> List[DetectionResult]:
        """Prioritize compatible versions."""
        # Simplified implementation
        return detections
    
    def prioritize_standard_locations(
        self, 
        detections: List[DetectionResult]
    ) -> List[DetectionResult]:
        """Prioritize applications in standard system locations."""
        # Simplified implementation
        return detections
    
    def prioritize_custom_configurations(
        self, 
        detections: List[DetectionResult],
        user_preferences: Dict[str, Any]
    ) -> List[DetectionResult]:
        """Prioritize based on custom user configurations."""
        # Simplified implementation
        return detections
    
    def _determine_component_key(self, app_name: str) -> str:
        """Determine component key from application name."""
        app_name_lower = app_name.lower()
        
        # Map application names to component keys
        component_mappings = {
            "git": ["git"],
            "dotnet": [".net", "dotnet", "microsoft .net"],
            "java": ["java", "jdk", "jre", "openjdk"],
            "python": ["python"],
            "node": ["node", "nodejs"],
            "powershell": ["powershell"],
            "anaconda": ["anaconda", "conda"],
            "vcpp": ["visual c++", "microsoft visual c++", "vc++"]
        }
        
        for component_key, patterns in component_mappings.items():
            if any(pattern in app_name_lower for pattern in patterns):
                return component_key
        
        # Default to the application name if no mapping found
        return app_name_lower.replace(" ", "_")
    
    def _get_required_version(self, component_name: str) -> Optional[str]:
        """Get required version for a component."""
        required_versions = {
            "git": "2.47.1",
            "dotnet": "8.0",
            "java": "21",
            "python": "3.12",
            "node": "20.0",
            "powershell": "7.0"
        }
        
        return required_versions.get(component_name)
    
    def _generate_selection_rationale(
        self, 
        primary_count: int, 
        secondary_count: int, 
        priority_scores: Dict[str, float]
    ) -> str:
        """Generate rationale for hierarchical selection."""
        rationale_parts = []
        
        rationale_parts.append(f"Hierarchical prioritization completed")
        rationale_parts.append(f"Primary detections: {primary_count}")
        rationale_parts.append(f"Secondary detections: {secondary_count}")
        
        if priority_scores:
            avg_score = sum(priority_scores.values()) / len(priority_scores)
            rationale_parts.append(f"Average priority score: {avg_score:.2f}")
            
            # Identify highest priority component
            highest_component = max(priority_scores.items(), key=lambda x: x[1])
            rationale_parts.append(f"Highest priority: {highest_component[0]} ({highest_component[1]:.2f})")
        
        return "; ".join(rationale_parts)