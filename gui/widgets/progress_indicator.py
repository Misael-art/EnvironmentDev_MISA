"""
Progress Indicator Widget for the EnvironmentDev_MISA GUI.

This widget provides a visual indication of an ongoing process.
It can be a simple animated spinner or a more detailed progress bar.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

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
        self.label_text = label_text
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.label = QLabel(self.label_text)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Indeterminate progress bar (acts like a spinner)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Makes it indeterminate
        self.progress_bar.setTextVisible(False) # Hide percentage text for spinner
        layout.addWidget(self.progress_bar)

        # Optional: Determinate progress bar (0-100%)
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

    def set_determinate(self, is_determinate=True, max_value=100):
        """
        Switch between indeterminate (spinner) and determinate (progress bar) mode.

        Args:
            is_determinate (bool): True for determinate mode, False for indeterminate.
            max_value (int): The maximum value for the determinate progress bar.
        """
        if is_determinate:
            self.progress_bar.setRange(0, max_value)
            self.progress_bar.setTextVisible(True)
        else:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setTextVisible(False)

    def set_value(self, value):
        """
        Set the value of the progress bar (only relevant in determinate mode).

        Args:
            value (int): The progress value.
        """
        if self.progress_bar.minimum() != self.progress_bar.maximum(): # Determinate mode
            self.progress_bar.setValue(value)

    def start(self):
        """Start the progress indication."""
        self.setVisible(True)
        # If using a timer for animation in a custom spinner, start it here
        # self.timer.start(100) # Example for a 100ms timer

    def stop(self):
        """Stop the progress indication."""
        self.setVisible(False)
        # If using a timer, stop it here
        # self.timer.stop()