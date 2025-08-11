#!/usr/bin/env python3
"""
Mecha Docs - Environment Dev Interactive Documentation

Main executable script for the Interactive Documentation system
of the Environment Dev Deep Evaluation project.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the interactive documentation
if __name__ == "__main__":
    try:
        from docs.interactive import main
        main()
    except ImportError as e:
        print(f"❌ Error importing documentation modules: {e}")
        print("Please ensure all dependencies are installed.")
        print("Run: python -m pip install rich")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Documentation session ended by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)