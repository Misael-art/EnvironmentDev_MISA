"""
Main entry point for the EnvironmentDev_MISA GUI application.
Initializes and launches the main window.

This script is designed to be run directly from the command line
within the project root directory.
e.g., `python -m gui.main` or `python gui/main.py` (with adjusted imports)
"""

import sys
import os

# Add the project root to the Python path so 'gui' package can be found
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from gui.app import EnvironmentDevMISAGUI

def main():
    """Main function to run the GUI application."""
    app = QApplication(sys.argv)
    # Set application properties like name, version, etc. here if needed
    # app.setApplicationName("EnvironmentDev MISA")
    # app.setApplicationVersion("0.1.0")
    
    window = EnvironmentDevMISAGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()