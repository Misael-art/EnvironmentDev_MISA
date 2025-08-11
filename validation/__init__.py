"""
Validation module for dependency validation and conflict detection.
"""

from .interfaces import DependencyValidatorInterface, ConflictDetectorInterface
from .base import ValidationBase

__all__ = [
    "DependencyValidatorInterface",
    "ConflictDetectorInterface",
    "ValidationBase",
]