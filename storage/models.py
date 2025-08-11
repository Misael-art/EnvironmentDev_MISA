"""
Data models for Intelligent Storage Management System
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class StorageUnit(Enum):
    """Storage unit enumeration"""
    BYTES = "bytes"
    KB = "KB"
    MB = "MB"
    GB = "GB"
    TB = "TB"


class CompressionType(Enum):
    """Compression type enumeration"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    ZSTD = "zstd"


class InstallationPriority(Enum):
    """Installation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


@dataclass
class DriveInfo:
    """Information about a storage drive"""
    drive_letter: str
    total_space: int  # in bytes
    available_space: int  # in bytes
    used_space: int  # in bytes
    file_system: str
    drive_type: str  # "fixed", "removable", "network", etc.
    is_system_drive: bool
    performance_score: float  # 0.0 to 1.0, higher is better


@dataclass
class ComponentSpaceRequirement:
    """Space requirement for a single component"""
    component_name: str
    download_size: int  # in bytes
    installation_size: int  # in bytes
    temporary_space: int  # in bytes
    total_required: int  # in bytes
    priority: InstallationPriority
    can_be_compressed: bool
    compression_ratio: float  # expected compression ratio (0.0 to 1.0)


@dataclass
class SpaceRequirement:
    """Overall space requirements for installation"""
    components: List[ComponentSpaceRequirement]
    total_download_size: int
    total_installation_size: int
    total_temporary_space: int
    total_required_space: int
    recommended_free_space: int  # includes buffer
    analysis_timestamp: datetime


@dataclass
class SelectiveInstallationResult:
    """Result of selective installation analysis"""
    installable_components: List[str]
    skipped_components: List[str]
    space_saved: int
    total_space_required: int
    installation_feasible: bool
    recommendations: List[str]


@dataclass
class CleanupResult:
    """Result of cleanup operations"""
    cleaned_files: List[str]
    space_freed: int
    cleanup_duration: float
    errors: List[str]
    success: bool


@dataclass
class RemovalSuggestion:
    """Suggestion for component removal"""
    component_name: str
    space_freed: int
    impact_level: str  # "low", "medium", "high"
    removal_safety: str  # "safe", "caution", "risky"
    description: str


@dataclass
class RemovalSuggestions:
    """Collection of removal suggestions"""
    suggestions: List[RemovalSuggestion]
    total_potential_space: int
    recommended_removals: List[str]
    analysis_timestamp: datetime


@dataclass
class DistributionPlan:
    """Plan for distributing installations across drives"""
    component_name: str
    target_drive: str
    installation_path: str
    space_required: int
    reason: str


@dataclass
class DistributionResult:
    """Result of intelligent distribution"""
    distribution_plans: List[DistributionPlan]
    total_components: int
    drives_used: List[str]
    space_optimization: float  # percentage of space optimization achieved
    distribution_feasible: bool
    warnings: List[str]


@dataclass
class CompressionCandidate:
    """Candidate for compression"""
    file_path: str
    original_size: int
    estimated_compressed_size: int
    compression_ratio: float
    last_accessed: datetime
    access_frequency: int
    compression_type: CompressionType


@dataclass
class CompressionResult:
    """Result of compression operations"""
    compressed_files: List[str]
    original_total_size: int
    compressed_total_size: int
    space_saved: int
    compression_ratio: float
    compression_duration: float
    errors: List[str]
    success: bool


@dataclass
class StorageAnalysisResult:
    """Comprehensive storage analysis result"""
    drives: List[DriveInfo]
    space_requirements: SpaceRequirement
    selective_installation: SelectiveInstallationResult
    removal_suggestions: RemovalSuggestions
    distribution_result: DistributionResult
    compression_opportunities: List[CompressionCandidate]
    overall_feasibility: bool
    recommendations: List[str]
    analysis_timestamp: datetime