"""
Unified Detection Engine implementation.

This module provides the core unified detection engine that orchestrates
all detection operations including registry scanning, portable app detection,
runtime detection, and hierarchical prioritization.
"""

import sys
try:
    import winreg  # type: ignore
except Exception:  # Non-Windows or restricted environments
    winreg = None  # type: ignore
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
    ComprehensiveDetectionReport,
    GapReport
)
from core.base import OperationResult
from core.exceptions import UnifiedDetectionError


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
            "nodejs": {
                "name": "Node.js",
                "target_version": "20.0",
                "commands": ["node --version"],
                "env_vars": ["NODE_HOME", "NODE_PATH"],
                "registry_patterns": [r"Node.*"],
                "executable_names": ["node.exe"],
            },
            "python": {
                "name": "Python",
                "target_version": "3.12",
                "commands": ["python --version", "py --version", "where python"],
                "env_vars": ["PYTHONHOME", "PYTHONPATH"],
                "registry_patterns": [r"Python.*"],
                "executable_names": ["python.exe", "py.exe"],
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
            "make": {
                "name": "Make",
                "target_version": "4.0",
                "commands": ["make --version", "where make"],
                "env_vars": [],
                "registry_patterns": [r"GnuWin.*Make", r"MSYS.*Make", r"Chocolatey.*make"],
                "executable_names": ["make.exe"],
            },
            "powershell_preview": {
                "name": "PowerShell Preview",
                "target_version": "7.4",
                "commands": ["pwsh-preview --version", "pwsh --version", "where pwsh-preview", "where pwsh"],
                "env_vars": [],
                "registry_patterns": [r"PowerShell.*Preview"],
                "executable_names": ["pwsh-preview.exe", "pwsh.exe"],
            },
            "vulkan_sdk": {
                "name": "Vulkan SDK",
                "target_version": "1.3",
                "commands": ["vulkaninfo --version", "where vulkaninfo"],
                "env_vars": ["VULKAN_SDK"],
                "registry_patterns": [r"Vulkan.*SDK"],
                "executable_names": ["vulkaninfo.exe"],
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
    
    def initialize(self) -> OperationResult:
        """Initialize the unified detection engine and return OperationResult."""
        try:
            self._logger.info("Initializing UnifiedDetectionEngine")
            # Perform any initialization tasks here
            self._logger.info("UnifiedDetectionEngine initialized successfully")
            return OperationResult(True, "UnifiedDetectionEngine initialized")
        except Exception as e:
            return OperationResult(False, f"Initialization failed: {e}", errors=[str(e)])
    
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

    def analyze_environment_gaps(self, expected_components: List[str]) -> GapReport:
        """Compara componentes esperados com o que a engine detecta no ambiente.

        A estratégia atual faz correspondência por nome (case-insensitive) com
        entradas do Registro do Windows. Futuras versões podem ampliar para FS/CLI.
        """
        try:
            registry_apps = self.scan_registry_installations()
            present_map = {app.name.lower(): app for app in registry_apps}

            # Complementar com detecção por CLI para runtimes essenciais
            runtime_results = self.detect_essential_runtimes()
            runtime_present_names: List[str] = []
            runtime_conf_map: Dict[str, DetectionConfidence] = {}
            for rr in runtime_results:
                if rr.detected:
                    key = (rr.runtime_name or "").lower()
                    if key:
                        runtime_present_names.append(key)
                        runtime_conf_map[key] = rr.confidence
                        # Adicionar sinônimos úteis para matching
                        if "node" in key:
                            for syn in ["node", "nodejs", "node.js"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence
                        if "java" in key:
                            for syn in ["java", "jdk", "java runtime", "java runtime environment", "jre"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence
                        if "python" in key:
                            for syn in ["python", "python 3", "python3", "python 3.12", "python 3.13"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence
                        if "make" in key:
                            for syn in ["make", "gnu make"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence
                        if "powershell" in key:
                            for syn in ["powershell", "powershell 7", "powershell preview", "pwsh", "pwsh-preview"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence
                        if "vulkan" in key:
                            for syn in ["vulkan", "vulkan sdk", "vulkaninfo"]:
                                runtime_present_names.append(syn)
                                runtime_conf_map[syn] = rr.confidence

            # Complementar com detecção genérica por CLI para outras categorias (build tools/compilers/editors)
            generic_cli_map: Dict[str, Dict[str, Any]] = {
                "cmake": {
                    "commands": [["cmake", "--version"], ["where", "cmake"]],
                "synonyms": ["cmake"],
                "fallback_names": ["cmake-gui.exe"],
                # Instalações típicas no Windows
                "known_paths": [
                    r"C:\\Program Files\\CMake\\bin\\cmake.exe",
                    r"C:\\Program Files (x86)\\CMake\\bin\\cmake.exe",
                ],
                "known_globs": [
                    r"C:\\Program Files\\CMake\\bin\\cmake.exe",
                    r"C:\\Program Files (x86)\\CMake\\bin\\cmake.exe",
                ],
                },
                "clang": {
                    "commands": [
                        ["clang", "--version"],
                        ["where", "clang"],
                        ["where", "clang-cl.exe"],
                        ["where", "clang++.exe"],
                        ["where", r"llvm\\bin\\clang.exe"],
                        ["where", r"LLVM\\bin\\clang.exe"],
                    ],
                    "synonyms": ["clang", "llvm clang"],
                    "fallback_names": ["clang-cl.exe", "clang++.exe", "llvm\\bin\\clang.exe"],
                },
                "gcc":   {
                    "commands": [["gcc", "--version"], ["where", "gcc"]],
                    "synonyms": ["gcc", "mingw", "mingw64"],
                    "fallback_names": ["g++.exe", "mingw32-make.exe"],
                "known_globs": [
                    r"C:\\Program Files\\mingw-w64\\*\\mingw64\\bin\\gcc.exe",
                    r"C:\\msys64\\mingw64\\bin\\gcc.exe",
                ],
                },
                "docker": {
                    "commands": [["docker", "--version"], ["where", "docker"]],
                "synonyms": ["docker", "docker desktop"],
                "known_paths": [
                    r"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",
                ],
                "known_globs": [
                    r"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",
                ],
                },
                "vscode": {
                    "commands": [["code", "--version"], ["where", "code"]],
                    "synonyms": ["visual studio code", "vscode", "code"],
                "fallback_names": ["Code.exe"],
                "known_paths": [
                    r"C:\\Program Files\\Microsoft VS Code\\Code.exe",
                    r"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                ],
                "known_globs": [
                    r"C:\\Program Files\\Microsoft VS Code\\Code.exe",
                    r"C:\\Users\\*\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                ],
                },
                # MSVC (Visual C++): mapear como compilers presentes
                "msvc": {
                    "commands": [["cl"], ["where", "cl.exe"]],
                    "synonyms": ["msvc", "visual c++", "visual studio c++", "cl", "compiler", "clang"],
                "fallback_names": ["cl.exe"],
                "known_globs": [
                    r"C:\\Program Files\\Microsoft Visual Studio\\*\\*\\VC\\Tools\\MSVC\\*\\bin\\Hostx64\\x64\\cl.exe",
                    r"C:\\Program Files (x86)\\Microsoft Visual Studio\\*\\*\\VC\\Tools\\MSVC\\*\\bin\\Hostx64\\x64\\cl.exe",
                ],
                },
                # Retro DevKits: detectar via toolchains e variáveis comuns
                "gba development kit (devkitarm)": {
                    "commands": [["arm-none-eabi-gcc", "--version"], ["where", "arm-none-eabi-gcc.exe"]],
                    "synonyms": ["gba development kit (devkitarm)", "devkitarm", "devkitpro"],
                    "fallback_names": ["arm-none-eabi-gcc.exe"],
                },
                "gbdk (game boy development kit)": {
                    "commands": [["cc65", "--version"], ["where", "cc65.exe"], ["gbdk", "--version"], ["where", "gbdk"],],
                    "synonyms": ["gbdk (game boy development kit)", "gbdk", "game boy development kit"],
                    "fallback_names": ["cc65.exe"],
                },
                "n64 development kit (libdragon)": {
                    "commands": [["mips64-elf-gcc", "--version"], ["where", "mips64-elf-gcc.exe"]],
                    "synonyms": ["n64 development kit (libdragon)", "libdragon", "nintendo 64 devkit"],
                    "fallback_names": ["mips64-elf-gcc.exe"],
                },
                "neo geo development kit (ngdevkit)": {
                    "commands": [["m68k-elf-gcc", "--version"], ["where", "m68k-elf-gcc.exe"]],
                    "synonyms": ["neo geo development kit (ngdevkit)", "ngdevkit", "neo geo devkit"],
                    "fallback_names": ["m68k-elf-gcc.exe"],
                },
                "psx development kit (psn00bsdk)": {
                    "commands": [["mipsel-none-elf-gcc", "--version"], ["where", "mipsel-none-elf-gcc.exe"], ["where", "mipsel-unknown-elf-gcc.exe"]],
                    "synonyms": ["psx development kit (psn00bsdk)", "psn00bsdk", "ps1 devkit"],
                    "fallback_names": ["mipsel-none-elf-gcc.exe", "mipsel-unknown-elf-gcc.exe"],
                },
                "sgdk (sega genesis development kit)": {
                    "commands": [["m68k-elf-gcc", "--version"], ["where", "m68k-elf-gcc.exe"]],
                    "synonyms": ["sgdk (sega genesis development kit)", "sgdk", "sega genesis devkit", "megadrive devkit"],
                    "fallback_names": ["m68k-elf-gcc.exe"],
                },
                "snes development kit (cc65)": {
                    "commands": [["cc65", "--version"], ["where", "cc65.exe"]],
                    "synonyms": ["snes development kit (cc65)", "snes devkit", "cc65"],
                    "fallback_names": ["cc65.exe"],
                },
                "sega saturn development kit (jo-engine + yaul)": {
                    "commands": [["sh-elf-gcc", "--version"], ["where", "sh-elf-gcc.exe"]],
                    "synonyms": ["sega saturn development kit (jo-engine + yaul)", "saturn devkit", "jo-engine", "yaul"],
                    "fallback_names": ["sh-elf-gcc.exe"],
                },
            }
            for canonical, spec in generic_cli_map.items():
                try:
                    present = False
                    for cmd in spec.get("commands", []):
                        output = self._execute_command_safely(cmd)
                        if output:
                            present = True
                            break
                    # fallback: tentar localizar executáveis comuns
                    if not present:
                        for exe in spec.get("fallback_names", []):
                            output = self._execute_command_safely(["where", exe])
                            if output:
                                present = True
                                break
                    # known_paths: checar caminhos padrão e globs comuns
                    if not present:
                        for p in spec.get("known_paths", []):
                            xp = os.path.expandvars(p)
                            if os.path.exists(xp):
                                present = True
                                break
                    if not present:
                        for gpat in spec.get("known_globs", []):
                            xg = os.path.expandvars(gpat)
                            # tentar expandir padrões simples com glob do shell (PowerShell/Windows)
                            try:
                                import glob
                                matches = glob.glob(xg)
                            except Exception:
                                matches = []
                            if any(os.path.exists(m) for m in matches):
                                present = True
                                break
                    if present:
                        runtime_present_names.append(canonical)
                        runtime_conf_map[canonical] = DetectionConfidence.MEDIUM
                        for syn in spec.get("synonyms", []):
                            runtime_present_names.append(syn)
                            runtime_conf_map[syn] = DetectionConfidence.MEDIUM
                except Exception:
                    continue

            present: List[str] = []
            missing: List[str] = []
            confidence_index: Dict[str, DetectionConfidence] = {}

            for expected in expected_components:
                key = expected.lower()
                found = None
                # match exata ou por inclusão para nomes próximos
                if key in present_map:
                    found = present_map[key]
                else:
                    for name, app in present_map.items():
                        if key in name or name in key:
                            found = app
                            break

                # Se não encontrado no registro, tentar pelos runtimes presentes
                if not found:
                    # matching por palavras-chave com os nomes detectados por CLI
                    for rname in runtime_present_names:
                        if rname in key or key in rname:
                            found = rname  # marcador não-nulo
                            break

                if found:
                    present.append(expected)
                    if hasattr(found, 'detection_confidence'):
                        confidence_index[expected] = getattr(found, 'detection_confidence', DetectionConfidence.UNKNOWN)
                    else:
                        # Resultado vindo de runtime CLI
                        # Escolher confiança reportada pelo runtime ou UNKNOWN
                        conf = runtime_conf_map.get(key)
                        if not conf:
                            # tentar casar com sinônimos
                            for rname in runtime_present_names:
                                if rname in key or key in rname:
                                    conf = runtime_conf_map.get(rname)
                                    if conf:
                                        break
                        confidence_index[expected] = conf or DetectionConfidence.MEDIUM
                else:
                    missing.append(expected)

            return GapReport(
                expected_count=len(expected_components),
                present_count=len(present),
                missing_count=len(missing),
                present=present,
                missing=missing,
                confidence_index=confidence_index,
            )
        except Exception as exc:
            # Em falha, reporta tudo como faltante para comportamento seguro
            return GapReport(
                expected_count=len(expected_components),
                present_count=0,
                missing_count=len(expected_components),
                present=[],
                missing=expected_components,
                confidence_index={},
            )
    
    def scan_registry_installations(self) -> List[RegistryApp]:
        """Scan Windows Registry for installed applications."""
        try:
            if sys.platform != "win32" or winreg is None:
                # Non-Windows: return empty list gracefully
                self._logger.debug("Registry scanning skipped: non-Windows platform")
                return []
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
            
            if winreg is None:
                return None
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
            
            # Simplified prioritization without external dependencies
            # (removido: imports inexistentes em core.*)
            
            # Get all detection results
            registry_apps = self.scan_registry_installations()
            essential_runtimes = self.detect_essential_runtimes()
            
            # Converter resultados a uma estrutura mínima baseada em DetectionResult
            detected_applications = []
            for reg_app in registry_apps:
                detected_applications.append(
                    self._create_detection_result(
                        detected=True,
                        method=DetectionMethod.REGISTRY,
                        details={
                            "name": reg_app.name,
                            "version": reg_app.version,
                            "install_path": reg_app.install_location,
                        },
                    )
                )
            
            # Convert runtime results to DetectedApplication format
            for runtime_result in essential_runtimes:
                if runtime_result.detected:
                    detected_applications.append(
                        self._create_detection_result(
                            detected=True,
                            method=runtime_result.detection_method,
                            details={
                                "name": runtime_result.runtime_name,
                                "version": runtime_result.version or "Unknown",
                                "install_path": runtime_result.install_path or "",
                            },
                        )
                    )
            
            # Heurística simples: itens detectados (confiança alta>média>baixa)
            primary_detections = self._prioritize_by_confidence(detected_applications)
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
            # Mantém agrupamento para possível extensão futura; hoje, já priorizados
            for component_name, apps in component_groups.items():
                _ = apps  # reservado para evolução
            
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