"""
Component Card Widget for the EnvironmentDev_MISA GUI.

This widget provides a standardized way to display information about a software component,
including its name, status, version, description, and action buttons (Install/Uninstall/Update).
It's designed to be used in lists or grids within the Components view.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

# Assuming we have a StatusIcon widget (to be created)
# from .status_icon import StatusIcon

class ComponentCard(QWidget):
    """
    A card widget to display component information.
    Emits signals when action buttons are clicked.
    """
    # Signals for actions
    installRequested = Signal(str)  # Emits component name
    uninstallRequested = Signal(str) # Emits component name
    updateRequested = Signal(str)   # Emits component name

    def __init__(self, component_data, parent=None):
        """
        Initializes the ComponentCard.

        Args:
            component_data (dict): A dictionary containing component information.
                Expected keys: 'name', 'status', 'version', 'description', 'category'
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.component_data = component_data
        self.name = component_data.get('name', 'Unknown')
        self.status = component_data.get('status', 'Unknown')
        self.version = component_data.get('version', 'N/A')
        self.description = component_data.get('description', 'No description available.')
        self.category = component_data.get('category', 'Other')

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface of the card."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Top row: Name, Status Icon, Version
        top_layout = QHBoxLayout()
        # Placeholder for StatusIcon
        # self.status_icon = StatusIcon(self.status)
        # top_layout.addWidget(self.status_icon)

        self.label_name = QLabel(f"<b>{self.name}</b>")
        top_layout.addWidget(self.label_name)

        top_layout.addStretch() # Push version to the right

        self.label_version = QLabel(f"v{self.version}")
        self.label_version.setAlignment(Qt.AlignRight)
        top_layout.addWidget(self.label_version)

        main_layout.addLayout(top_layout)

        # Description
        self.label_description = QLabel(self.description)
        self.label_description.setWordWrap(True)
        # Set a maximum height and make it elide if too long?
        # self.label_description.setMaximumHeight(40)
        main_layout.addWidget(self.label_description)

        # Category (optional, smaller font)
        self.label_category = QLabel(f"<i>{self.category}</i>")
        self.label_category.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.label_category)

        # Action buttons
        button_layout = QHBoxLayout()
        # Example logic for button visibility based on status
        if self.status.lower() == 'missing':
            self.btn_install = QPushButton("Install")
            self.btn_install.clicked.connect(lambda: self.installRequested.emit(self.name))
            button_layout.addWidget(self.btn_install)
        elif self.status.lower() == 'installed':
            self.btn_uninstall = QPushButton("Uninstall")
            self.btn_uninstall.clicked.connect(lambda: self.uninstallRequested.emit(self.name))
            button_layout.addWidget(self.btn_uninstall)
            # Add update button if there's a newer version available
            # if self.component_data.get('update_available', False):
            #     self.btn_update = QPushButton("Update")
            #     self.btn_update.clicked.connect(lambda: self.updateRequested.emit(self.name))
            #     button_layout.addWidget(self.btn_update)
        else: # For 'partially installed' or other states
            self.btn_action = QPushButton("Action") # Generic action button
            # Logic to determine action based on specific state
            self.btn_action.clicked.connect(lambda: self.handle_generic_action())
            button_layout.addWidget(self.btn_action)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def handle_generic_action(self):
        """Handle a generic action based on the component's state."""
        # This could be expanded to handle different states
        print(f"Generic action requested for {self.name} (Status: {self.status})")
        # For now, just emit the install signal as an example
        self.installRequested.emit(self.name)

    def update_data(self, new_data):
        """
        Update the card's data and UI.

        Args:
            new_data (dict): New component data to update the card with.
        """
        self.component_data.update(new_data)
        # Re-read the data
        self.name = self.component_data.get('name', self.name)
        self.status = self.component_data.get('status', self.status)
        self.version = self.component_data.get('version', self.version)
        self.description = self.component_data.get('description', self.description)
        self.category = self.component_data.get('category', self.category)

        # Update UI elements
        self.label_name.setText(f"<b>{self.name}</b>")
        self.label_version.setText(f"v{self.version}")
        self.label_description.setText(self.description)
        self.label_category.setText(f"<i>{self.category}</i>")
        # Update status icon if implemented
        # if hasattr(self, 'status_icon'):
        #     self.status_icon.update_status(self.status)
        # TODO: Logic to show/hide/update buttons based on new status