#!/usr/bin/env python3
"""
Mecha - Environment Dev Deep Evaluation CLI Entry Point

Main executable script for the Environment Dev Deep Evaluation system.
Provides a unified command-line interface for all system operations.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the CLI application
if __name__ == "__main__":
    try:
        from cli.main import app
        app()
    except ImportError as e:
        print(f"❌ Error importing CLI modules: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)