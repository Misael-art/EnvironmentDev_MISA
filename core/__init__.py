"""
Core module containing base classes, exceptions, and configuration management.
"""

from .exceptions import (
    EnvironmentDevDeepEvaluationError,
    ArchitectureAnalysisError,
    UnifiedDetectionError,
    DependencyValidationError,
    RobustDownloadError,
    AdvancedInstallationError,
    SteamDeckIntegrationError,
    IntelligentStorageError,
    PluginSystemError,
)
from .config import ConfigurationManager
from .base import SystemComponentBase

__all__ = [
    "EnvironmentDevDeepEvaluationError",
    "ArchitectureAnalysisError", 
    "UnifiedDetectionError",
    "DependencyValidationError",
    "RobustDownloadError",
    "AdvancedInstallationError",
    "SteamDeckIntegrationError",
    "IntelligentStorageError",
    "PluginSystemError",
    "ConfigurationManager",
    "SystemComponentBase",
]