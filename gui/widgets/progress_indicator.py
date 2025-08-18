"""
Progress Indicator Widget for the EnvironmentDev_MISA GUI.

This widget provides a visual indication of an ongoing process.
It can be a simple animated spinner or a more detailed progress bar.
"""

import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer

# Logger for this module
logger = logging.getLogger(__name__)

class ProgressIndicator(QWidget):
    """
    A widget to show progress of an operation.
    Can be an indeterminate spinner or a determinate progress bar.
    """

    def __init__(self, label_text="Processing...", parent=None):
        """
        Initializes the ProgressIndicator.

        Args:
            label_text (str): The text to display above the progress bar/spinner.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.label_text = label_text
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.label = QLabel(self.label_text)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Indeterminate progress bar (acts like a spinner)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Makes it indeterminate
        self.progress_bar.setTextVisible(False) # Hide percentage text for spinner
        layout.addWidget(self.progress_bar)

        # Optional: Determinate progress bar (0-100%)
        # Uncomment the lines below and comment the ones above to switch modes
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setRange(0, 100)
        # self.progress_bar.setValue(0)
        # layout.addWidget(self.progress_bar)

        # Optional: A cancel button
        # self.btn_cancel = QPushButton("Cancel")
        # layout.addWidget(self.btn_cancel)

    def set_label_text(self, text):
        """
        Update the label text.

        Args:
            text (str): The new text for the label.
        """
        self.label.setText(text)

    def start(self, label_text=None):
        """
        Start the progress indication.

        Args:
            label_text (str, optional): New label text to set before starting. Defaults to None.
        """
        if label_text:
            self.set_label_text(label_text)
        self.logger.debug(f"Starting progress indicator with label: '{self.label.text()}'")
        self.setVisible(True)
        # If using a timer for animation in a custom spinner, start it here
        # self.timer.start(100) # Example for a 100ms timer

    def stop(self):
        """Stop the progress indication."""
        self.logger.debug("Stopping progress indicator.")
        self.setVisible(False)
        # If using a timer, stop it here
        # self.timer.stop()
        
    def is_running(self):
        """
        Check if the progress indicator is currently visible/running.

        Returns:
            bool: True if the indicator is visible, False otherwise.
        """
        return self.isVisible()