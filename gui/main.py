"""
Main entry point for the EnvironmentDev_MISA GUI application.
Initializes and launches the main window.

This script is designed to be run directly from the command line
within the project root directory, or via the installed console script.
e.g., `python -m gui.main` or `environment-dev-gui` (if installed)
"""

import sys
import os
import logging

# --- Configure Logging ---
# Basic configuration for the application logger
# In a full application, this would likely be more sophisticated,
# potentially involving configuration files.
logging.basicConfig(
    level=logging.DEBUG, # Set to INFO or WARNING in production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to console
        # logging.FileHandler('gui_app.log') # Also log to a file
    ]
)
logger = logging.getLogger(__name__)
logger.info("Starting EnvironmentDev_MISA GUI application.")

# --- Path Configuration ---
# Add the project root to the Python path so 'gui' package can be found
# This is especially important when running the script directly.
# When installed via pip, this might not be strictly necessary if the package is correctly installed.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.debug(f"Added project root to sys.path: {project_root}")

# --- Import Application ---
# Now that the path is set, we can import the main application class
try:
    from PySide6.QtWidgets import QApplication
    from gui.app import EnvironmentDevMISAGUI
    logger.debug("Successfully imported PySide6 and EnvironmentDevMISAGUI.")
except ImportError as e:
    logger.critical(f"Failed to import required modules: {e}")
    print(f"Critical Error: {e}")
    print("Please ensure PySide6 is installed. You can install it using 'pip install PySide6'.")
    sys.exit(1)

def main():
    """Main function to run the GUI application."""
    logger.info("Entering main function.")
    
    try:
        # Create the QApplication instance
        # The static method in EnvironmentDevMISAGUI handles potential multiple instances
        app = EnvironmentDevMISAGUI.create_app()
        logger.debug("QApplication instance created.")
        
        # Set application-wide properties
        app.setApplicationName("EnvironmentDev MISA")
        app.setApplicationVersion("0.1.0")
        # Set organization info if needed for QSettings
        # app.setOrganizationName("YourOrgName")
        # app.setOrganizationDomain("yourorg.com")
        logger.debug("Set application properties.")
        
        # Create and show the main window
        window = EnvironmentDevMISAGUI()
        window.show()
        logger.debug("Main window created and shown.")
        
        # Start the event loop
        logger.info("Starting QApplication event loop.")
        exit_code = app.exec()
        logger.info(f"QApplication event loop finished with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"An unexpected error occurred in main: {e}", exc_info=True)
        print(f"Critical Error in main application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()