#!/usr/bin/env python3
"""
Mecha TUI - Environment Dev Deep Evaluation Terminal User Interface

Main executable script for the Terminal User Interface of the 
Environment Dev Deep Evaluation system.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the TUI application
if __name__ == "__main__":
    try:
        from tui.main import main
        main()
    except ImportError as e:
        print(f"❌ Error importing TUI modules: {e}")
        print("Please ensure all dependencies are installed.")
        print("Run: python -m pip install textual")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 TUI application closed by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)