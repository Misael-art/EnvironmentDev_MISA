"""
Main application window and layout for the EnvironmentDev_MISA GUI.
Defines the primary window structure, including menu, sidebar, central area, and status bar.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QToolBar, QStatusBar,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
# Import views
# Note: Absolute imports are used assuming the package structure and PYTHONPATH
from gui.views.dashboard_view import DashboardView
from gui.views.components_view import ComponentsView
# Future views to be imported as they are developed
# from gui.views.reports_view import ReportsView
# from gui.views.diagnostics_view import DiagnosticsView
# from gui.views.settings_view import SettingsView
# from gui.views.update_view import UpdateView

# Import BackendConnector
from gui.backend_connector import BackendConnector

class EnvironmentDevMISAGUI(QMainWindow):
    """Main application window for the GUI."""
    
    def __init__(self):
        super().__init__()
        self.backend_connector = BackendConnector()
        self.setWindowTitle("EnvironmentDev MISA")
        self.setGeometry(100, 100, 1200, 800) # Set a default size
        
        # Store references to views for later interaction
        self.views = {}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.create_menu_bar()
        self.create_toolbar()
        self.create_central_widget()
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('&View')
        toggle_theme_action = QAction('Toggle &Theme', self)
        toggle_theme_action.setStatusTip('Switch between light and dark themes')
        # Placeholder for theme toggle logic
        # toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')
        about_action = QAction('&About', self)
        about_action.setStatusTip('About EnvironmentDev MISA')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the main toolbar (sidebar)."""
        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24)) # Placeholder size, icons needed
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        
        # Add navigation buttons to the toolbar
        self.btn_dashboard = QAction(QIcon(), "Dashboard", self) # Placeholder icon
        self.btn_dashboard.triggered.connect(lambda: self.switch_view("dashboard"))
        self.toolbar.addAction(self.btn_dashboard)

        self.btn_components = QAction(QIcon(), "Components", self)
        self.btn_components.triggered.connect(lambda: self.switch_view("components"))
        self.toolbar.addAction(self.btn_components)

        # Future actions for other views
        # self.btn_reports = QAction(QIcon(), "Reports", self)
        # self.btn_reports.triggered.connect(lambda: self.switch_view("reports"))
        # self.toolbar.addAction(self.btn_reports)

        # self.btn_diagnostics = QAction(QIcon(), "Diagnostics", self)
        # self.btn_diagnostics.triggered.connect(lambda: self.switch_view("diagnostics"))
        # self.toolbar.addAction(self.btn_diagnostics)

        # self.btn_settings = QAction(QIcon(), "Settings", self)
        # self.btn_settings.triggered.connect(lambda: self.switch_view("settings"))
        # self.toolbar.addAction(self.btn_settings)

        # self.btn_updates = QAction(QIcon(), "Updates", self)
        # self.btn_updates.triggered.connect(lambda: self.switch_view("updates"))
        # self.toolbar.addAction(self.btn_updates)

    def create_central_widget(self):
        """Create the central widget area with a QStackedWidget for views."""
        # Create the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins

        # Create the main content area (stacked widget for different views)
        self.main_content = QStackedWidget()
        
        # Initialize and add views
        self.init_views()
        
        main_layout.addWidget(self.main_content)
        
    def init_views(self):
        """Initialize and add the different views to the stacked widget."""
        # --- Dashboard View ---
        self.views["dashboard"] = DashboardView(self.backend_connector, self)
        self.main_content.addWidget(self.views["dashboard"])
        
        # --- Components View ---
        self.views["components"] = ComponentsView(self.backend_connector, self)
        self.main_content.addWidget(self.views["components"])
        
        # --- Placeholder Views (To be implemented) ---
        # For now, we add placeholder labels. These will be replaced by actual view instances.
        
        # Reports View
        self.views["reports"] = QLabel("Reports View - Generate and view environment reports here.")
        self.views["reports"].setAlignment(Qt.AlignCenter)
        self.main_content.addWidget(self.views["reports"])
        
        # Diagnostics View
        self.views["diagnostics"] = QLabel("Diagnostics View - Run system diagnostics and view results here.")
        self.views["diagnostics"].setAlignment(Qt.AlignCenter)
        self.main_content.addWidget(self.views["diagnostics"])
        
        # Settings View
        self.views["settings"] = QLabel("Settings View - Configure application settings here.")
        self.views["settings"].setAlignment(Qt.AlignCenter)
        self.main_content.addWidget(self.views["settings"])
        
        # Updates View
        self.views["updates"] = QLabel("Updates View - Manage component updates and hash verification here.")
        self.views["updates"].setAlignment(Qt.AlignCenter)
        self.main_content.addWidget(self.views["updates"])
        
        # Initially show the dashboard
        self.switch_view("dashboard")
        
    def switch_view(self, view_name: str):
        """
        Switch the main content view based on the view name.

        Args:
            view_name (str): The name of the view to switch to.
        """
        if view_name in self.views:
            index = self.main_content.indexOf(self.views[view_name])
            if index != -1:
                self.main_content.setCurrentIndex(index)
                # Update status bar or other UI elements if needed based on view switch
                self.statusBar().showMessage(f"Switched to {view_name.capitalize()} view", 2000) # 2 seconds
            else:
                # This case should ideally not happen if views are added correctly
                self.statusBar().showMessage(f"Error: View '{view_name}' not found in stack.", 5000)
        else:
            self.statusBar().showMessage(f"Error: Unknown view '{view_name}'.", 5000)
            
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # Initial status message
        self.status_bar.showMessage("Ready", 5000) # Show for 5 seconds
        # Example of updating status based on backend checks (could be async)
        # self.update_status_from_backend()

    # --- Menu Action Handlers ---

    def show_about(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About EnvironmentDev MISA",
            "EnvironmentDev MISA GUI
Version 0.1.0

A tool to manage and configure development environments."
        )

    def toggle_theme(self):
        """Placeholder for theme toggling logic."""
        # This would involve applying a different stylesheet or palette
        # For now, just show a message
        current_msg = self.statusBar().currentMessage()
        self.statusBar().showMessage("Theme toggle is not implemented yet.", 3000)
        # Restore previous message after 3 seconds
        if current_msg:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.statusBar().showMessage(current_msg))

    # --- Utility Methods ---

    # def update_status_from_backend(self):
    #     """
    #     Example method to update the status bar based on backend status.
    #     This should ideally be called asynchronously.
    #     """
    #     # Example: Run a quick doctor check
    #     # result = self.backend_connector.run_doctor(json_output=True, verbose=False)
    #     # if result['success']:
    #     #     # Parse result['data'] and update status bar
    #     #     # e.g., self.status_bar.showMessage("System OK - RF005 Compliant")
    #     #     pass
    #     # else:
    #     #     self.status_bar.showMessage(f"System Check Error: {result['error'][:50]}...", 10000)
    #     pass

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
        app_instance.setApplicationName("EnvironmentDev MISA")
        app_instance.setApplicationVersion("0.1.0")
        return app_instance