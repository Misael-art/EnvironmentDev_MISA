"""
CLI package for Environment Dev Deep Evaluation.

This package provides command-line interface functionality
for managing development environments.
"""

from .main import app as main_app
from .commands import ComponentManager
from .profiles import app as profiles_app

__all__ = ["main_app", "ComponentManager", "profiles_app"]