"""Pytest configuration to ensure project root is importable.

This adds the project root to sys.path so that top-level packages
like 'validation' can be imported by tests regardless of how pytest
sets up the working directory and import paths.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)