"""
Intelligent Storage Management Module

This module provides intelligent storage management capabilities for the Environment Dev
Deep Evaluation system, including space analysis, distribution algorithms, and compression.
"""

from .intelligent_storage_manager import IntelligentStorageManager
from .storage_analyzer import StorageAnalyzer
from .distribution_manager import DistributionManager
from .compression_manager import CompressionManager
from .models import (
    SpaceRequirement,
    SelectiveInstallationResult,
    CleanupResult,
    RemovalSuggestions,
    DistributionResult,
    CompressionResult,
    StorageAnalysisResult
)

__all__ = [
    'IntelligentStorageManager',
    'StorageAnalyzer',
    'DistributionManager',
    'CompressionManager',
    'SpaceRequirement',
    'SelectiveInstallationResult',
    'CleanupResult',
    'RemovalSuggestions',
    'DistributionResult',
    'CompressionResult',
    'StorageAnalysisResult'
]