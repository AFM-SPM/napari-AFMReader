"""Module used for providing error alerts in the gui and show/ handle loading messages"""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
)

class LoadingWidget(QWidget):
    """A semi-transparent overlay for napari viewer."""

    def __init__(self, viewer):
        # Parent to the main napari window so it covers everything
        super().__init__(viewer.window._qt_window)
        self.viewer = viewer

        # Make overlay semi-transparent
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")

        # Center layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Create container with rounded background
        loading_container = QWidget()
        loading_container.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 240);
                border-radius: 15px;
                padding: 30px;
            }
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel()
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)

        loading_layout.addWidget(self.loading_label)
        loading_container.setLayout(loading_layout)

        layout.addWidget(loading_container)
        self.setLayout(layout)

        self.message = ""

        self.hide()

    def start(self, message="Loading"):
        """Show the dialog with a message."""
        self.message = message
        self.loading_label.setText(f"{self.message}")

        # Cover the entire napari window
        self.setGeometry(self.parent().rect())

        self.show()
        self.raise_()  # Bring to front
        QApplication.processEvents()

    def stop(self):
        """Hide the widget."""
        self.hide()
        QApplication.processEvents()

    def resizeEvent(self, event):
        """Keep overlay covering the parent when window resizes."""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
