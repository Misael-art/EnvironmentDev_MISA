"""
Environment Dev Deep Evaluation System

A comprehensive system for deep evaluation and reintegration of 
Environment Dev functionalities with robust architecture analysis,
unified detection, and intelligent dependency management.
"""

__version__ = "1.0.0"
__author__ = "Environment Dev Deep Evaluation Team"

from .core.exceptions import EnvironmentDevDeepEvaluationError
from .core.config import ConfigurationManager

__all__ = [
    "EnvironmentDevDeepEvaluationError",
    "ConfigurationManager",
]