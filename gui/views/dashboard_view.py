"""
Dashboard View for the EnvironmentDev_MISA GUI.

This view provides an overview of the system's status, including health checks,
a summary of installed/missing components, and quick access to key actions.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt
# Assuming we have a StatusIcon widget (to be created)
# from ..widgets.status_icon import StatusIcon
# Assuming we have a ProgressIndicator widget
from ..widgets.progress_indicator import ProgressIndicator

class DashboardView(QWidget):
    """
    The main dashboard view for the application.
    Displays system status, component summary, and quick actions.
    """

    def __init__(self, backend_connector, parent=None):
        """
        Initializes the DashboardView.

        Args:
            backend_connector (BackendConnector): The backend connector instance.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.backend_connector = backend_connector
        self.init_ui()
        # Load initial data
        self.load_data()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_label = QLabel("Dashboard")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header_label)

        # System Health Section
        self.create_health_section(main_layout)

        # Component Summary Section
        self.create_component_summary_section(main_layout)

        # Quick Actions Section (Placeholder)
        self.create_quick_actions_section(main_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

    def create_health_section(self, parent_layout):
        """Create the system health section."""
        health_frame = QFrame()
        health_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        health_layout = QVBoxLayout(health_frame)

        health_title = QLabel("System Health")
        health_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        health_layout.addWidget(health_title)

        # Placeholder for health status details
        # In a real implementation, this would be populated with data from backend_connector.get_system_status()
        self.health_status_label = QLabel("Checking system health...")
        health_layout.addWidget(self.health_status_label)

        # Progress indicator for health check
        self.health_progress = ProgressIndicator("Running diagnostics...")
        self.health_progress.setVisible(False) # Hidden by default
        health_layout.addWidget(self.health_progress)

        parent_layout.addWidget(health_frame)

    def create_component_summary_section(self, parent_layout):
        """Create the component summary section."""
        summary_frame = QFrame()
        summary_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        summary_layout = QVBoxLayout(summary_frame)

        summary_title = QLabel("Component Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        summary_layout.addWidget(summary_title)

        # Grid layout for summary cards
        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(10)

        # Placeholder labels for summary
        self.total_components_label = QLabel("Total Components: -")
        self.installed_components_label = QLabel("Installed: -")
        self.missing_components_label = QLabel("Missing: -")
        self.outdated_components_label = QLabel("Outdated: -")

        self.summary_grid.addWidget(self.total_components_label, 0, 0)
        self.summary_grid.addWidget(self.installed_components_label, 0, 1)
        self.summary_grid.addWidget(self.missing_components_label, 1, 0)
        self.summary_grid.addWidget(self.outdated_components_label, 1, 1)

        summary_layout.addLayout(self.summary_grid)

        # Progress indicator for component analysis
        self.summary_progress = ProgressIndicator("Analyzing components...")
        self.summary_progress.setVisible(False) # Hidden by default
        summary_layout.addWidget(self.summary_progress)

        parent_layout.addWidget(summary_frame)

    def create_quick_actions_section(self, parent_layout):
        """Create the quick actions section."""
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        actions_layout = QVBoxLayout(actions_frame)

        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Placeholder for quick action buttons
        # e.g., QPushButton("Run Full Diagnostics"), QPushButton("Install All Missing")
        placeholder_label = QLabel("Quick action buttons will be added here.")
        actions_layout.addWidget(placeholder_label)

        parent_layout.addWidget(actions_frame)

    def load_data(self):
        """
        Load data from the backend connector to populate the dashboard.
        This should ideally be done asynchronously to avoid blocking the UI.
        """
        # 1. Load System Health
        self.load_system_health()
        # 2. Load Component Summary
        self.load_component_summary()

    def load_system_health(self):
        """Load and display system health information."""
        self.health_progress.start()
        self.health_status_label.setText("Running diagnostics...")
        # In a real implementation, you would call:
        # health_data = self.backend_connector.get_system_status()
        # Then update the UI with health_data
        # For now, simulate completion
        # QTimer.singleShot(2000, self.on_health_data_loaded) # Simulate 2s delay
        self.on_health_data_loaded()

    def on_health_data_loaded(self, health_data=None):
        """Callback when system health data is loaded."""
        self.health_progress.stop()
        if health_data:
            # Process health_data and update UI
            # Example:
            # status = health_data.get('overall_status', 'Unknown')
            # message = health_data.get('message', 'No details available.')
            # self.health_status_label.setText(f"Status: {status} - {message}")
            self.health_status_label.setText("System health check completed. All systems nominal.")
        else:
            # Simulated data
            self.health_status_label.setText("System health check completed. All systems nominal.")

    def load_component_summary(self):
        """Load and display component summary information."""
        self.summary_progress.start()
        # In a real implementation, you would call:
        # component_data = self.backend_connector.list_components(gap_analysis=True)
        # Then update the UI with component_data
        # For now, simulate completion
        # QTimer.singleShot(1500, self.on_component_summary_loaded) # Simulate 1.5s delay
        self.on_component_summary_loaded()

    def on_component_summary_loaded(self, component_data=None):
        """Callback when component summary data is loaded."""
        self.summary_progress.stop()
        if component_data:
            # Process component_data and update UI
            # Example:
            # total = len(component_data)
            # installed = sum(1 for c in component_data if c['status'] == 'Installed')
            # missing = sum(1 for c in component_data if c['status'] == 'Missing')
            # self.total_components_label.setText(f"Total Components: {total}")
            # self.installed_components_label.setText(f"Installed: {installed}")
            # self.missing_components_label.setText(f"Missing: {missing}")
            pass # Update with real data
        else:
            # Simulated data
            self.total_components_label.setText("Total Components: 50")
            self.installed_components_label.setText("Installed: 45")
            self.missing_components_label.setText("Missing: 5")
            self.outdated_components_label.setText("Outdated: 2")