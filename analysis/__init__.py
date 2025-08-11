"""
Analysis module for architecture analysis and gap detection.
"""

from .interfaces import ArchitectureAnalysisInterface, GapAnalysisInterface
from .base import AnalysisBase

__all__ = [
    "ArchitectureAnalysisInterface",
    "GapAnalysisInterface", 
    "AnalysisBase",
]