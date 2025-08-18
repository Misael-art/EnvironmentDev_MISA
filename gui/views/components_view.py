"""
Components View for the EnvironmentDev_MISA GUI.

This view allows users to browse, search, and manage software components.
It displays a list of components, provides filtering options, and allows
installation/uninstallation.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QComboBox
from PySide6.QtCore import Qt
# Assuming we have a ComponentCard widget
from ..widgets.component_card import ComponentCard

class ComponentsView(QWidget):
    """
    The view for managing software components.
    Displays a list of components with search, filter, and action capabilities.
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
        self.all_components = [] # Store all components data
        self.filtered_components = [] # Store filtered components data
        self.component_cards = {} # Map component name to its card widget

        self.init_ui()
        self.load_components()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Manage Components")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Search and Filter Bar
        self.create_search_filter_bar(main_layout)

        # Components List
        self.components_list = QListWidget()
        # Allow custom widgets in the list
        self.components_list.setUniformItemSizes(False)
        self.components_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        main_layout.addWidget(self.components_list)

    def create_search_filter_bar(self, parent_layout):
        """Create the search and filter bar."""
        bar_layout = QHBoxLayout()

        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search components...")
        self.search_box.textChanged.connect(self.filter_components)
        bar_layout.addWidget(self.search_box)

        # Category Filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        # TODO: Populate categories dynamically from component data
        # self.category_filter.addItems(["Development Tools", "Editors", "Runtimes", ...])
        self.category_filter.currentTextChanged.connect(self.filter_components)
        bar_layout.addWidget(self.category_filter)

        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        self.status_filter.addItems(["Installed", "Missing", "Partially Installed"])
        self.status_filter.currentTextChanged.connect(self.filter_components)
        bar_layout.addWidget(self.status_filter)

        # Refresh Button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_components)
        bar_layout.addWidget(self.btn_refresh)

        parent_layout.addLayout(bar_layout)

    def load_components(self):
        """Load the list of components from the backend."""
        # In a real implementation, this would be asynchronous
        # components_data = self.backend_connector.list_components()
        # For now, use simulated data
        self.all_components = self.get_simulated_components()
        self.filtered_components = self.all_components.copy()
        self.populate_component_list()

    def get_simulated_components(self):
        """Generate simulated component data for testing."""
        # This is placeholder data
        return [
            {"name": "Python 3.11", "status": "Installed", "version": "3.11.0", "description": "The Python programming language.", "category": "Core"},
            {"name": "Git", "status": "Installed", "version": "2.40.0", "description": "Distributed version control system.", "category": "Development Tools"},
            {"name": "Visual Studio Code", "status": "Installed", "version": "1.85.0", "description": "Code editor redefined and optimized for building and debugging modern web and cloud applications.", "category": "Editors"},
            {"name": "Node.js", "status": "Missing", "version": "N/A", "description": "JavaScript runtime built on Chrome's V8 JavaScript engine.", "category": "Development Tools"},
            {"name": "Docker Desktop", "status": "Missing", "version": "N/A", "description": "Containerization platform.", "category": "Containers"},
            {"name": "Java JDK 17", "status": "Partially Installed", "version": "17.0.2", "description": "Java Development Kit for building Java applications.", "category": "Runtimes"},
        ]

    def populate_component_list(self):
        """Populate the components list widget with ComponentCard widgets."""
        self.components_list.clear()
        self.component_cards.clear()

        for component_data in self.filtered_components:
            # Create a QListWidgetItem
            item = QListWidgetItem(self.components_list)
            # Create a ComponentCard widget
            card = ComponentCard(component_data)
            # Connect signals from the card
            card.installRequested.connect(self.on_install_requested)
            card.uninstallRequested.connect(self.on_uninstall_requested)
            # Store reference to the card
            self.component_cards[component_data['name']] = card
            # Set the item's size hint to match the card's size
            item.setSizeHint(card.sizeHint())
            # Add the card to the list
            self.components_list.addItem(item)
            self.components_list.setItemWidget(item, card)

    def filter_components(self):
        """Filter the list of components based on search and filter criteria."""
        search_text = self.search_box.text().lower()
        selected_category = self.category_filter.currentText()
        selected_status = self.status_filter.currentText()

        self.filtered_components = []
        for component in self.all_components:
            # Check search text
            if search_text and search_text not in component['name'].lower() and search_text not in component['description'].lower():
                continue
            # Check category filter
            if selected_category != "All Categories" and component['category'] != selected_category:
                continue
            # Check status filter
            if selected_status != "All Statuses" and component['status'] != selected_status:
                continue
            # If all conditions pass, include the component
            self.filtered_components.append(component)

        self.populate_component_list()

    def on_install_requested(self, component_name):
        """
        Handle an install request from a ComponentCard.

        Args:
            component_name (str): The name of the component to install.
        """
        print(f"Install requested for: {component_name}")
        # In a real implementation:
        # 1. Show a confirmation dialog
        # 2. Call backend_connector.install_component(component_name) asynchronously
        # 3. Show progress indicator
        # 4. Update the component card status upon completion/failure

    def on_uninstall_requested(self, component_name):
        """
        Handle an uninstall request from a ComponentCard.

        Args:
            component_name (str): The name of the component to uninstall.
        """
        print(f"Uninstall requested for: {component_name}")
        # In a real implementation:
        # 1. Show a confirmation dialog
        # 2. Call backend_connector.uninstall_component(component_name) asynchronously
        # 3. Show progress indicator
        # 4. Update the component card status upon completion/failure