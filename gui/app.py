"""
Main application window and layout for the EnvironmentDev_MISA GUI.
Defines the primary window structure, including menu/sidebar and central area.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget
from PySide6.QtCore import Qt

class EnvironmentDevMISAGUI(QMainWindow):
    """Main application window for the GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EnvironmentDev MISA")
        self.setGeometry(100, 100, 1200, 800) # Set a default size
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        # Create the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create the sidebar/menu
        self.create_sidebar(main_layout)
        
        # Create the main content area (stacked widget for different views)
        self.create_main_content(main_layout)
        
        # Connect sidebar buttons to switch views
        self.connect_sidebar_signals()
        
    def create_sidebar(self, parent_layout):
        """Create the sidebar with navigation buttons."""
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        
        # Add navigation buttons
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_components = QPushButton("Components")
        self.btn_reports = QPushButton("Reports")
        self.btn_diagnostics = QPushButton("Diagnostics")
        self.btn_settings = QPushButton("Settings")
        self.btn_updates = QPushButton("Updates")
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_components)
        sidebar_layout.addWidget(self.btn_reports)
        sidebar_layout.addWidget(self.btn_diagnostics)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addWidget(self.btn_updates)
        
        # Add some space at the bottom
        sidebar_layout.addStretch()
        
        parent_layout.addWidget(self.sidebar)
        
    def create_main_content(self, parent_layout):
        """Create the main content area using a QStackedWidget."""
        self.main_content = QStackedWidget()
        
        # Create placeholder widgets for each view
        # In a full implementation, these would be instances of the actual view classes
        self.dashboard_widget = QLabel("Dashboard View - Overview of the environment status will be shown here.")
        self.dashboard_widget.setAlignment(Qt.AlignCenter)
        self.components_widget = QLabel("Components View - Manage installed and available components here.")
        self.components_widget.setAlignment(Qt.AlignCenter)
        self.reports_widget = QLabel("Reports View - Generate and view environment reports here.")
        self.reports_widget.setAlignment(Qt.AlignCenter)
        self.diagnostics_widget = QLabel("Diagnostics View - Run system diagnostics and view results here.")
        self.diagnostics_widget.setAlignment(Qt.AlignCenter)
        self.settings_widget = QLabel("Settings View - Configure application settings here.")
        self.settings_widget.setAlignment(Qt.AlignCenter)
        self.updates_widget = QLabel("Updates View - Manage component updates and hash verification here.")
        self.updates_widget.setAlignment(Qt.AlignCenter)
        
        # Add widgets to the stacked widget
        self.main_content.addWidget(self.dashboard_widget)
        self.main_content.addWidget(self.components_widget)
        self.main_content.addWidget(self.reports_widget)
        self.main_content.addWidget(self.diagnostics_widget)
        self.main_content.addWidget(self.settings_widget)
        self.main_content.addWidget(self.updates_widget)
        
        parent_layout.addWidget(self.main_content)
        
    def connect_sidebar_signals(self):
        """Connect sidebar button clicks to switch the main content view."""
        self.btn_dashboard.clicked.connect(lambda: self.main_content.setCurrentIndex(0))
        self.btn_components.clicked.connect(lambda: self.main_content.setCurrentIndex(1))
        self.btn_reports.clicked.connect(lambda: self.main_content.setCurrentIndex(2))
        self.btn_diagnostics.clicked.connect(lambda: self.main_content.setCurrentIndex(3))
        self.btn_settings.clicked.connect(lambda: self.main_content.setCurrentIndex(4))
        self.btn_updates.clicked.connect(lambda: self.main_content.setCurrentIndex(5))
        
    @staticmethod
    def create_app():
        """
        Static method to create the QApplication instance.
        This helps manage the application lifecycle correctly.
        """
        # Check if an instance already exists to avoid creating multiple
        app_instance = QApplication.instance()
        if app_instance is None:
            app_instance = QApplication(sys.argv)
        # Set application properties like name, version, etc. here if needed
        # app_instance.setApplicationName("EnvironmentDev MISA")
        # app_instance.setApplicationVersion("0.1.0")
        return app_instance