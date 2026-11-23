"""Module used for providing error alerts in the gui and show/ handle loading messages."""

from napari import Viewer
from qtpy.QtCore import Qt
from qtpy.QtGui import QResizeEvent
from qtpy.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
)


def _viewer_window_widget(viewer: Viewer | None) -> QWidget | None:
    """
    Return the napari Qt main window widget, if one is available.

    Parameters
    ----------
    viewer : napari.Viewer or None
        The napari viewer instance to inspect.

    Returns
    -------
    QWidget or None
        The Qt main window widget when it is available.
    """
    if viewer is None:
        return None
    window = getattr(viewer, "window", None)
    if window is None:
        return None
    return getattr(window, "_qt_window", None)


class LoadingWidget(QWidget):
    """
    A semi-transparent overlay for napari viewer.

    Parameters
    ----------
    viewer : napari.Viewer
        The napari viewer instance to attach the overlay to.
    """

    def __init__(self, viewer: Viewer | None):
        """
        Initialize the LoadingWidget.

        Parameters
        ----------
        viewer : napari.Viewer
            The napari viewer instance to attach the overlay to.
        """
        # Parent to the main napari window so it covers everything
        super().__init__(_viewer_window_widget(viewer))
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

    def start(self, message: str = "Loading"):
        """
        Show the dialog with a message.

        Parameters
        ----------
        message : str, optional
            The message to display in the loading overlay. Defaults to "Loading".
        """
        self.message = message
        self.loading_label.setText(f"{self.message}")

        parent = self.parentWidget()
        if parent is None:
            parent = _viewer_window_widget(self.viewer)
            if parent is not None:
                self.setParent(parent)

        # Cover the entire napari window when possible. If the viewer window is
        # unavailable, show a standalone loading widget instead of crashing.
        if parent is not None:
            self.setGeometry(parent.rect())
        else:
            self.adjustSize()

        self.show()
        self.raise_()  # Bring to front
        QApplication.processEvents()

    def stop(self):
        """Hide the widget."""
        self.hide()
        QApplication.processEvents()

    def resizeEvent(self, event: QResizeEvent):
        """
        Keep overlay covering the parent when window resizes.

        Parameters
        ----------
        event : QResizeEvent
            The resize event from Qt.
        """
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
