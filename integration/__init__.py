"""
Integration module for platform-specific integrations and plugin management.
"""

from .interfaces import PlatformIntegrationInterface, PluginManagerInterface
from .base import IntegrationBase

__all__ = [
    "PlatformIntegrationInterface",
    "PluginManagerInterface",
    "IntegrationBase",
]