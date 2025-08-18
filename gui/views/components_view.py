"""
Components View for the EnvironmentDev_MISA GUI.

This view allows users to browse, search, and manage software components.
It displays a list or table of components, provides filtering options, and allows
installation/uninstallation.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QTextEdit,
    QAbstractItemView, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# Import necessary widgets
from gui.widgets.progress_indicator import ProgressIndicator

# Logger for this module
logger = logging.getLogger(__name__)

class ComponentsView(QWidget):
    """
    The view for managing software components.
    Displays a table of components with search, filter, and action capabilities.
    """

    def __init__(self, backend_connector, parent=None):
        """
        Initializes the ComponentsView.

        Args:
            backend_connector (BackendConnector): The backend connector instance.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.backend_connector = backend_connector
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State variables for data
        self.all_components_data = []
        self.displayed_components_data = [] # Data currently shown in the table
        
        self.init_ui()
        # Load initial data asynchronously to avoid blocking the UI
        # QTimer.singleShot(0, self.load_components)
        # A better approach would be to use QThread or asyncio, but for simplicity, we'll load directly
        self.load_components()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Header
        header_label = QLabel("Manage Components")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)

        # Search and Filter Bar
        self.create_search_filter_bar(main_layout)

        # Components Table
        self.create_components_table(main_layout)

        # Progress Indicator for component loading/actions
        self.components_progress = ProgressIndicator("Loading components...")
        self.components_progress.setVisible(False) # Hidden by default
        main_layout.addWidget(self.components_progress)

        # Action Buttons (placed below the table)
        self.create_action_buttons(main_layout)

    def create_search_filter_bar(self, parent_layout):
        """Create the search and filter bar."""
        bar_layout = QHBoxLayout()

        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search components...")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        bar_layout.addWidget(QLabel("Search:"), 0) # Label takes minimal space
        bar_layout.addWidget(self.search_box, 1) # Search box expands

        # Category Filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        # TODO: Populate categories dynamically from component data
        # self.category_filter.addItems(["Development Tools", "Editors", "Runtimes", ...])
        self.category_filter.currentTextChanged.connect(self.on_filters_changed)
        bar_layout.addWidget(QLabel("Category:"), 0)
        bar_layout.addWidget(self.category_filter, 0) # Fixed width based on content

        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        self.status_filter.addItems(["Installed", "Missing", "Partially Installed"]) # Add more as needed
        self.status_filter.currentTextChanged.connect(self.on_filters_changed)
        bar_layout.addWidget(QLabel("Status:"), 0)
        bar_layout.addWidget(self.status_filter, 0)

        # Confidence Filter
        self.confidence_filter = QComboBox()
        self.confidence_filter.addItem("All Confidences")
        self.confidence_filter.addItems(["HIGH", "MEDIUM", "LOW"])
        self.confidence_filter.currentTextChanged.connect(self.on_filters_changed)
        bar_layout.addWidget(QLabel("Confidence:"), 0)
        bar_layout.addWidget(self.confidence_filter, 0)

        # Refresh Button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_components)
        bar_layout.addWidget(self.btn_refresh)

        parent_layout.addLayout(bar_layout)

    def create_components_table(self, parent_layout):
        """Create the table to display components."""
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(6) # Name, Category, Version, Status, Confidence, Actions
        self.components_table.setHorizontalHeaderLabels(["Name", "Category", "Version", "Status", "Confidence", "Actions"])
        self.components_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Make cells non-editable
        self.components_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Select entire rows
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive) # Allow manual resizing
        # Initially set column widths (can be adjusted later)
        self.components_table.setColumnWidth(0, 200) # Name
        self.components_table.setColumnWidth(1, 150) # Category
        self.components_table.setColumnWidth(2, 100) # Version
        self.components_table.setColumnWidth(3, 100) # Status
        self.components_table.setColumnWidth(4, 100) # Confidence
        self.components_table.setColumnWidth(5, 150) # Actions (buttons)
        
        # Connect header signals for sorting if needed
        # self.components_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        parent_layout.addWidget(self.components_table)

    def create_action_buttons(self, parent_layout):
        """Create action buttons below the table."""
        actions_layout = QHBoxLayout()
        
        # Update All Hashes Button
        self.btn_update_hashes = QPushButton("Update All Hashes")
        self.btn_update_hashes.clicked.connect(self.on_update_hashes_clicked)
        actions_layout.addWidget(self.btn_update_hashes)
        
        # Install Selected Button (enabled/disabled based on selection and status)
        self.btn_install_selected = QPushButton("Install Selected")
        self.btn_install_selected.clicked.connect(self.on_install_selected_clicked)
        self.btn_install_selected.setEnabled(False) # Disabled by default
        actions_layout.addWidget(self.btn_install_selected)
        
        # Uninstall Selected Button
        self.btn_uninstall_selected = QPushButton("Uninstall Selected")
        self.btn_uninstall_selected.clicked.connect(self.on_uninstall_selected_clicked)
        self.btn_uninstall_selected.setEnabled(False) # Disabled by default
        actions_layout.addWidget(self.btn_uninstall_selected)
        
        actions_layout.addStretch() # Push buttons to the left
        
        parent_layout.addLayout(actions_layout)

    # --- Data Loading and Handling ---

    def load_components(self):
        """Load the list of components from the backend."""
        self.logger.debug("Initiating component list load.")
        self.components_progress.start()
        self.components_table.setRowCount(0) # Clear existing rows
        self.components_table.setSortingEnabled(False) # Disable sorting while loading
        
        # In a real implementation, this would be asynchronous
        # QTimer.singleShot(100, self._fetch_components) # Simulate async delay
        self._fetch_components()

    def _fetch_components(self):
        """Internal method to fetch components from backend."""
        self.logger.debug("Fetching component list data from backend.")
        # Request list with gap analysis to get status
        component_data_result = self.backend_connector.list_components(gap_analysis=True, json_output=True)
        
        self.logger.debug(f"Component list data fetched. Success: {component_data_result.get('success')}")
        self.on_components_loaded(component_data_result)

    def on_components_loaded(self, component_data_result):
        """Callback when component list data is loaded."""
        self.logger.debug("Processing loaded component list data.")
        self.components_progress.stop()
        self.components_table.setSortingEnabled(True) # Re-enable sorting
        
        if component_data_result.get("success"):
            component_data = component_data_result.get("data", [])
            self.all_components_data = component_data
            self.displayed_components_data = component_data[:] # Shallow copy
            
            # Update filters (categories, statuses) based on new data
            self.update_filters_from_data(component_data)
            
            # Populate the table with data
            self.populate_components_table(component_data)
        else:
            error_msg = component_data_result.get("error", "Unknown error fetching component list.")
            self.logger.error(f"Failed to load components: {error_msg}")
            # Show error in table or status bar
            self.components_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error loading components: {error_msg}")
            error_item.setFlags(Qt.ItemIsSelectable) # Non-editable
            self.components_table.setItem(0, 0, error_item)
            self.components_table.setSpan(0, 0, 1, self.components_table.columnCount()) # Span across all columns

    def update_filters_from_data(self, component_data):
        """Update the filter dropdowns based on the loaded component data."""
        # Update Category filter
        current_categories = [self.category_filter.itemText(i) for i in range(self.category_filter.count())]
        unique_categories = sorted(list(set(comp.get('category', 'Other') for comp in component_data)))
        # Add "All Categories" if not present or move it to the top
        if "All Categories" in current_categories:
            unique_categories.insert(0, "All Categories")
        else:
            unique_categories = ["All Categories"] + unique_categories
            
        # Block signals to prevent triggering filter change during update
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItems(unique_categories)
        self.category_filter.blockSignals(False)
        
        # The status and confidence filters are usually fixed, so no need to update them dynamically here.
        # Unless the backend introduces new statuses/confidences dynamically.

    def populate_components_table(self, component_data):
        """Populate the components table widget with data."""
        self.components_table.setRowCount(len(component_data))
        
        for row, component in enumerate(component_data):
            name = component.get('name', 'N/A')
            category = component.get('category', 'Other')
            version = component.get('version', 'N/A')
            status = component.get('status', 'Unknown')
            confidence = component.get('confidence', 'N/A') # Assuming backend provides this
            
            # Create items
            name_item = QTableWidgetItem(name)
            category_item = QTableWidgetItem(category)
            version_item = QTableWidgetItem(version)
            status_item = QTableWidgetItem(status)
            confidence_item = QTableWidgetItem(confidence)
            
            # Set flags to make items non-editable
            for item in [name_item, category_item, version_item, status_item, confidence_item]:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled) # Non-editable but selectable
            
            # Add items to the table
            self.components_table.setItem(row, 0, name_item)
            self.components_table.setItem(row, 1, category_item)
            self.components_table.setItem(row, 2, version_item)
            self.components_table.setItem(row, 3, status_item)
            self.components_table.setItem(row, 4, confidence_item)
            
            # Create action buttons for the row
            # This is a bit tricky with QTableWidget. A better approach is to use a custom delegate
            # or embed a widget in the cell. For simplicity, we'll add a single "Actions" button
            # that opens a context menu or dialog. Alternatively, we can add a widget to the cell.
            
            # Let's create a widget to hold the action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2) # Reduce margins
            actions_layout.setSpacing(5)
            
            btn_install = QPushButton("Install")
            btn_install.clicked.connect(lambda checked, n=name: self.on_install_component(n))
            btn_uninstall = QPushButton("Uninstall")
            btn_uninstall.clicked.connect(lambda checked, n=name: self.on_uninstall_component(n))
            btn_info = QPushButton("Info")
            btn_info.clicked.connect(lambda checked, n=name: self.on_show_component_info(n))
            
            # Disable/Enable buttons based on status
            if status.lower() == 'installed':
                btn_install.setEnabled(False)
                btn_uninstall.setEnabled(True)
            elif status.lower() == 'missing':
                btn_install.setEnabled(True)
                btn_uninstall.setEnabled(False)
            else: # Partially installed or other
                btn_install.setEnabled(True)
                btn_uninstall.setEnabled(True) # Might be force uninstall
            
            actions_layout.addWidget(btn_install)
            actions_layout.addWidget(btn_uninstall)
            actions_layout.addWidget(btn_info)
            actions_layout.addStretch() # Push buttons to the left
            
            # Set the widget in the table cell
            self.components_table.setCellWidget(row, 5, actions_widget)
            
        # Resize rows to fit content
        self.components_table.resizeRowsToContents()

    # --- Filtering Logic ---

    def on_search_text_changed(self):
        """Trigger filtering when search text changes."""
        self.apply_filters()

    def on_filters_changed(self):
        """Trigger filtering when any filter changes."""
        self.apply_filters()

    def apply_filters(self):
        """Apply all active filters to the component list."""
        search_text = self.search_box.text().lower()
        selected_category = self.category_filter.currentText()
        selected_status = self.status_filter.currentText()
        selected_confidence = self.confidence_filter.currentText()

        self.displayed_components_data = self.all_components_data[:]
        
        # Apply search filter
        if search_text:
            self.displayed_components_data = [
                c for c in self.displayed_components_data
                if search_text in c.get('name', '').lower() or search_text in c.get('description', '').lower()
            ]
            
        # Apply category filter
        if selected_category != "All Categories":
            self.displayed_components_data = [
                c for c in self.displayed_components_data
                if c.get('category', '') == selected_category
            ]
            
        # Apply status filter
        if selected_status != "All Statuses":
            self.displayed_components_data = [
                c for c in self.displayed_components_data
                if c.get('status', '').title() == selected_status # Ensure title case match
            ]
            
        # Apply confidence filter
        if selected_confidence != "All Confidences":
            self.displayed_components_data = [
                c for c in self.displayed_components_data
                if c.get('confidence', '').upper() == selected_confidence # Ensure upper case match
            ]
            
        # Repopulate the table with filtered data
        self.populate_components_table(self.displayed_components_data)

    # --- Event Handlers for Actions ---

    def on_install_component(self, component_name: str):
        """Handle the install action for a specific component."""
        self.logger.info(f"Install action requested for component: {component_name}")
        # This should ideally be a non-blocking operation with progress feedback
        # For now, we'll simulate it with a progress indicator
        
        # Find the row corresponding to the component
        row = None
        for i in range(self.components_table.rowCount()):
            item = self.components_table.item(i, 0) # Name column
            if item and item.text() == component_name:
                row = i
                break
                
        if row is not None:
            # Show progress in the row or globally
            self.components_progress.set_label_text(f"Installing {component_name}...")
            self.components_progress.start()
            
            # In a real implementation, this would be a background task
            # QTimer.singleShot(2000, lambda: self._finish_install_component(component_name, row)) # Simulate 2s delay
            self._finish_install_component(component_name, row)
        else:
            self.logger.warning(f"Component row not found for {component_name} during install action.")

    def _finish_install_component(self, component_name: str, row: int):
        """Finish the install process and update UI."""
        self.logger.debug(f"Finishing install for {component_name}")
        self.components_progress.stop()
        
        # Call backend to install
        install_result = self.backend_connector.install_component(component_name, silent=True)
        
        if install_result.get("success"):
            self.logger.info(f"Successfully installed {component_name}")
            # Update the table row status
            status_item = self.components_table.item(row, 3) # Status column
            if status_item:
                status_item.setText("Installed")
            # Disable install button, enable uninstall
            actions_widget = self.components_table.cellWidget(row, 5)
            if actions_widget:
                for i in range(actions_widget.layout().count()):
                    widget = actions_widget.layout().itemAt(i).widget()
                    if isinstance(widget, QPushButton):
                        if widget.text() == "Install":
                            widget.setEnabled(False)
                        elif widget.text() == "Uninstall":
                            widget.setEnabled(True)
                            
            # Show success message
            # self.window().statusBar().showMessage(f"Successfully installed {component_name}", 5000)
        else:
            error_msg = install_result.get("error", f"Failed to install {component_name}")
            self.logger.error(error_msg)
            # Show error message
            # self.window().statusBar().showMessage(error_msg, 10000)

    def on_uninstall_component(self, component_name: str):
        """Handle the uninstall action for a specific component."""
        self.logger.info(f"Uninstall action requested for component: {component_name}")
        # Similar logic to install
        row = None
        for i in range(self.components_table.rowCount()):
            item = self.components_table.item(i, 0)
            if item and item.text() == component_name:
                row = i
                break
                
        if row is not None:
            self.components_progress.set_label_text(f"Uninstalling {component_name}...")
            self.components_progress.start()
            
            # QTimer.singleShot(2000, lambda: self._finish_uninstall_component(component_name, row)) # Simulate delay
            self._finish_uninstall_component(component_name, row)
        else:
            self.logger.warning(f"Component row not found for {component_name} during uninstall action.")

    def _finish_uninstall_component(self, component_name: str, row: int):
        """Finish the uninstall process and update UI."""
        self.logger.debug(f"Finishing uninstall for {component_name}")
        self.components_progress.stop()
        
        # Call backend to uninstall
        uninstall_result = self.backend_connector.uninstall_component(component_name, force=False)
        
        if uninstall_result.get("success"):
            self.logger.info(f"Successfully uninstalled {component_name}")
            # Update the table row status
            status_item = self.components_table.item(row, 3)
            if status_item:
                status_item.setText("Missing")
            # Enable install button, disable uninstall
            actions_widget = self.components_table.cellWidget(row, 5)
            if actions_widget:
                for i in range(actions_widget.layout().count()):
                    widget = actions_widget.layout().itemAt(i).widget()
                    if isinstance(widget, QPushButton):
                        if widget.text() == "Install":
                            widget.setEnabled(True)
                        elif widget.text() == "Uninstall":
                            widget.setEnabled(False)
                            
            # Show success message
            # self.window().statusBar().showMessage(f"Successfully uninstalled {component_name}", 5000)
        else:
            error_msg = uninstall_result.get("error", f"Failed to uninstall {component_name}")
            self.logger.error(error_msg)
            # Show error message
            # self.window().statusBar().showMessage(error_msg, 10000)

    def on_show_component_info(self, component_name: str):
        """Handle showing detailed information for a component."""
        self.logger.info(f"Info action requested for component: {component_name}")
        # This would typically open a new dialog or a side panel with detailed info
        # For now, we'll just log that the action was requested
        # In a full implementation, you would call:
        # info_result = self.backend_connector.get_component_info(component_name, json_output=True)
        # And then display the `info_result['data']` in a new window/dialog.
        self.window().statusBar().showMessage(f"Showing info for {component_name} is not implemented yet.", 3000)

    def on_update_hashes_clicked(self):
        """Handle the 'Update All Hashes' button click."""
        self.logger.info("'Update All Hashes' button clicked.")
        self.btn_update_hashes.setEnabled(False)
        self.components_progress.set_label_text("Updating component hashes...")
        self.components_progress.start()
        
        # Call backend to update hashes
        # QTimer.singleShot(3000, self._finish_update_hashes) # Simulate delay
        self._finish_update_hashes()

    def _finish_update_hashes(self):
        """Finish the update hashes process."""
        self.logger.debug("Finishing update hashes process.")
        # Call backend
        update_result = self.backend_connector.update_hashes(only_hashes=True)
        
        self.components_progress.stop()
        self.btn_update_hashes.setEnabled(True)
        
        if update_result.get("success"):
            self.logger.info("Successfully updated component hashes.")
            self.window().statusBar().showMessage("Component hashes updated successfully.", 5000)
            # Reload the component list to reflect new hashes/statuses
            self.load_components()
        else:
            error_msg = update_result.get("error", "Failed to update component hashes.")
            self.logger.error(error_msg)
            self.window().statusBar().showMessage(f"Hash update failed: {error_msg}", 10000)

    def on_install_selected_clicked(self):
        """Handle the 'Install Selected' button click."""
        self.logger.info("'Install Selected' button clicked.")
        # Get selected rows
        selected_rows = self.components_table.selectionModel().selectedRows()
        if not selected_rows:
            self.window().statusBar().showMessage("No components selected for installation.", 3000)
            return
            
        component_names = []
        for index in selected_rows:
            row = index.row()
            name_item = self.components_table.item(row, 0)
            status_item = self.components_table.item(row, 3)
            if name_item and status_item and status_item.text().lower() == 'missing':
                component_names.append(name_item.text())
                
        if not component_names:
            self.window().statusBar().showMessage("No 'Missing' components selected for installation.", 3000)
            return
            
        self.logger.info(f"Installing selected components: {component_names}")
        # For simplicity, install the first one and show a message for others
        # A real implementation would queue installs or handle them concurrently
        if component_names:
            self.on_install_component(component_names[0])
            if len(component_names) > 1:
                self.window().statusBar().showMessage(f"Queued installation for {len(component_names)} components. Starting with {component_names[0]}.", 5000)

    def on_uninstall_selected_clicked(self):
        """Handle the 'Uninstall Selected' button click."""
        self.logger.info("'Uninstall Selected' button clicked.")
        # Similar logic to install selected
        selected_rows = self.components_table.selectionModel().selectedRows()
        if not selected_rows:
            self.window().statusBar().showMessage("No components selected for uninstallation.", 3000)
            return
            
        component_names = []
        for index in selected_rows:
            row = index.row()
            name_item = self.components_table.item(row, 0)
            status_item = self.components_table.item(row, 3)
            if name_item and status_item and status_item.text().lower() == 'installed':
                component_names.append(name_item.text())
                
        if not component_names:
            self.window().statusBar().showMessage("No 'Installed' components selected for uninstallation.", 3000)
            return
            
        self.logger.info(f"Uninstalling selected components: {component_names}")
        if component_names:
            self.on_uninstall_component(component_names[0])
            if len(component_names) > 1:
                self.window().statusBar().showMessage(f"Queued uninstallation for {len(component_names)} components. Starting with {component_names[0]}.", 5000)