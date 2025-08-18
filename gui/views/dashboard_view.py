"""
Dashboard View for the EnvironmentDev_MISA GUI.

This view provides an overview of the system's status, including health checks,
a summary of installed/missing components, and quick access to key actions.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame,
    QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# Import necessary widgets
from gui.widgets.progress_indicator import ProgressIndicator

# Logger for this module
logger = logging.getLogger(__name__)

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
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State variables for data
        self.system_health_data = None
        self.component_summary_data = None
        
        self.init_ui()
        # Load initial data asynchronously to avoid blocking the UI
        # QTimer.singleShot(0, self.load_data) # This is a simple way to defer execution
        # A better approach would be to use QThread or asyncio, but for simplicity, we'll load directly
        # In a production app, especially with network calls, async is crucial.
        self.load_data()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_label = QLabel("Dashboard")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)

        # Quick Actions Section (Place at the top for prominence)
        self.create_quick_actions_section(main_layout)

        # System Health Section
        self.create_health_section(main_layout)

        # Component Summary Section
        self.create_component_summary_section(main_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

    def create_quick_actions_section(self, parent_layout):
        """Create the quick actions section."""
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        actions_layout = QVBoxLayout(actions_frame)

        actions_title = QLabel("Quick Actions")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        actions_title.setFont(title_font)
        actions_layout.addWidget(actions_title)

        # Quick action buttons
        btn_layout = QHBoxLayout()
        
        self.btn_run_env_check = QPushButton("Run Environment Check")
        self.btn_run_env_check.clicked.connect(self.on_run_env_check_clicked)
        btn_layout.addWidget(self.btn_run_env_check)
        
        # Add placeholder for other quick actions
        # e.g., QPushButton("Generate Report Now"), QPushButton("Install Missing Components")
        btn_layout.addStretch()
        
        actions_layout.addLayout(btn_layout)
        
        # Progress indicator for quick actions
        self.quick_action_progress = ProgressIndicator("Running environment check...")
        self.quick_action_progress.setVisible(False) # Hidden by default
        actions_layout.addWidget(self.quick_action_progress)

        parent_layout.addWidget(actions_frame)

    def create_health_section(self, parent_layout):
        """Create the system health section."""
        health_frame = QFrame()
        health_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        health_layout = QVBoxLayout(health_frame)

        health_title = QLabel("System Health")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        health_title.setFont(title_font)
        health_layout.addWidget(health_title)

        # Placeholder for health status details
        self.health_status_label = QLabel("Click 'Run Environment Check' to diagnose system.")
        self.health_status_label.setWordWrap(True)
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
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        summary_title.setFont(title_font)
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

    # --- Data Loading and Handling ---

    def load_data(self):
        """
        Load data from the backend connector to populate the dashboard.
        This should ideally be done asynchronously to avoid blocking the UI.
        For simplicity, we call them sequentially. In a real-world scenario, consider concurrent loading.
        """
        # 1. Load Component Summary
        self.load_component_summary()
        # 2. Load System Health (triggered by user action, but we can preload basic info)
        # self.load_system_health() # This is triggered by the "Run Environment Check" button

    def load_system_health(self):
        """Load and display system health information."""
        self.logger.debug("Initiating system health check load.")
        self.health_progress.start()
        self.health_status_label.setText("Running diagnostics...")
        
        # In a real implementation, this would be asynchronous
        # For now, simulate a call and immediate callback
        # QTimer.singleShot(100, self._fetch_system_health) # Simulate async delay
        self._fetch_system_health()

    def _fetch_system_health(self):
        """Internal method to fetch system health from backend."""
        self.logger.debug("Fetching system health data from backend.")
        health_data_result = self.backend_connector.run_doctor(json_output=True, verbose=True)
        
        self.logger.debug(f"System health data fetched. Success: {health_data_result.get('success')}")
        self.on_health_data_loaded(health_data_result)

    def on_health_data_loaded(self, health_data_result):
        """Callback when system health data is loaded."""
        self.logger.debug("Processing loaded system health data.")
        self.health_progress.stop()
        
        if health_data_result.get("success"):
            health_data = health_data_result.get("data", {})
            self.system_health_data = health_data
            
            # Process health_data and update UI
            self._update_health_ui(health_data)
        else:
            error_msg = health_data_result.get("error", "Unknown error during health check.")
            self.logger.error(f"Failed to load system health: {error_msg}")
            self.health_status_label.setText(f"<span style='color:red;'>Health check failed:</span> {error_msg}")

    def _update_health_ui(self, health_data):
        """Update the UI elements with the health data."""
        # Example: Assume health_data is a dict with 'checks' list and 'summary' dict
        # This structure depends on the output of `doctor --json`
        # For demonstration, let's assume a simple structure
        try:
            summary = health_data.get("summary", {})
            checks = health_data.get("checks", [])
            
            # Simple overall status message
            overall_status = summary.get("status", "Unknown")
            issues_found = summary.get("issues_found", 0)
            
            if overall_status.lower() == "ok":
                status_text = f"<span style='color:green;'>System is healthy.</span> No issues detected."
            elif issues_found > 0:
                status_text = f"<span style='color:orange;'>{issues_found} issue(s) detected.</span> See details below."
            else:
                status_text = f"<span style='color:red;'>System check returned status: {overall_status}</span>"
                
            self.health_status_label.setText(status_text)
            
            # Optionally, display a brief log of checks in a QTextEdit
            # This is a simplified example. In practice, you might want a table or list view.
            # health_log = "\n".join([f"[{check.get('status', 'N/A')}] {check.get('name', 'Unnamed Check')}: {check.get('message', '')}" for check in checks[:5]]) # Show top 5
            # self.health_details_text_edit.setPlainText(health_log)
            
        except Exception as e:
            self.logger.exception("Error updating health UI")
            self.health_status_label.setText(f"<span style='color:red;'>Error displaying health data:</span> {str(e)}")

    def load_component_summary(self):
        """Load and display component summary information."""
        self.logger.debug("Initiating component summary load.")
        self.summary_progress.start()
        
        # In a real implementation, this would be asynchronous
        # QTimer.singleShot(100, self._fetch_component_summary) # Simulate async delay
        self._fetch_component_summary()

    def _fetch_component_summary(self):
        """Internal method to fetch component summary from backend."""
        self.logger.debug("Fetching component summary data from backend.")
        # Request list with gap analysis to distinguish installed/missing
        component_data_result = self.backend_connector.list_components(gap_analysis=True, json_output=True)
        
        self.logger.debug(f"Component summary data fetched. Success: {component_data_result.get('success')}")
        self.on_component_summary_loaded(component_data_result)

    def on_component_summary_loaded(self, component_data_result):
        """Callback when component summary data is loaded."""
        self.logger.debug("Processing loaded component summary data.")
        self.summary_progress.stop()
        
        if component_data_result.get("success"):
            component_data = component_data_result.get("data", [])
            self.component_summary_data = component_data
            
            # Process component_data and update UI
            self._update_summary_ui(component_data)
        else:
            error_msg = component_data_result.get("error", "Unknown error fetching component list.")
            self.logger.error(f"Failed to load component summary: {error_msg}")
            # Update labels to show error
            self.total_components_label.setText("Total Components: <span style='color:red;'>Error</span>")
            self.installed_components_label.setText("Installed: <span style='color:red;'>Error</span>")
            self.missing_components_label.setText("Missing: <span style='color:red;'>Error</span>")
            self.outdated_components_label.setText("Outdated: <span style='color:red;'>Error</span>")

    def _update_summary_ui(self, component_data):
        """Update the UI elements with the component summary data."""
        try:
            # Counters
            total = len(component_data)
            installed = sum(1 for c in component_data if c.get('status', '').lower() == 'installed')
            missing = sum(1 for c in component_data if c.get('status', '').lower() == 'missing')
            # Outdated count is trickier without specific version comparison logic in the backend
            # For now, assume 'partially installed' or a custom flag might indicate outdated.
            # This requires the backend (list-components --gap-analysis) to provide such info.
            # As a placeholder, let's say any non-'installed' and non-'missing' is "other" or potentially outdated/issue.
            other = total - installed - missing
            
            self.total_components_label.setText(f"Total Components: {total}")
            self.installed_components_label.setText(f"<span style='color:green;'>Installed:</span> {installed}")
            self.missing_components_label.setText(f"<span style='color:red;'>Missing:</span> {missing}")
            self.outdated_components_label.setText(f"Other States: {other}") # Improve this logic based on backend data
            
        except Exception as e:
            self.logger.exception("Error updating component summary UI")
            self.total_components_label.setText("Total Components: <span style='color:red;'>Parse Error</span>")
            self.installed_components_label.setText("<span style='color:red;'>Parse Error</span>")
            self.missing_components_label.setText("<span style='color:red;'>Parse Error</span>")
            self.outdated_components_label.setText("<span style='color:red;'>Parse Error</span>")

    # --- Event Handlers ---

    def on_run_env_check_clicked(self):
        """Handle the 'Run Environment Check' button click."""
        self.logger.info("'Run Environment Check' button clicked.")
        self.btn_run_env_check.setEnabled(False) # Prevent multiple clicks
        self.quick_action_progress.start()
        # Trigger the health check load
        self.load_system_health()
        # Re-enable button after a short delay or when health check finishes
        # A better way is to re-enable it in `on_health_data_loaded`
        # QTimer.singleShot(5000, lambda: self.btn_run_env_check.setEnabled(True)) # Enable after 5s as fallback