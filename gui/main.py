"""
Main entry point for the EnvironmentDev_MISA GUI application.
Initializes and launches the main window.
"""

import sys
from PySide6.QtWidgets import QApplication
from .app import EnvironmentDevMISAGUI

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