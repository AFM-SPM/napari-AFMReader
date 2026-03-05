import sys
from pathlib import Path

from AFMReader import general_loader
from loguru import logger
from qtpy.QtWidgets import QInputDialog, QComboBox, QVBoxLayout, QLabel, QWidget  # pylint: disable = no-name-in-module
from ._alerts import LoadingWidget

from napari import current_viewer

afmreader_id = 0
loaded_images = []


def napari_get_reader(path: list | str):
    if isinstance(path, list):
        path = path[0]

    if not path.endswith((".asd", ".gwy", ".ibw", ".jpk", ".spm", ".stp", ".top", ".topostats", ".h5-jpk", ".jpk-qi-image", ".jpk-qi-data")):
        return None

    return reader_function


def reader_function(path, channel=None):
    global afmreader_id
    paths = [Path(path)] if isinstance(path, str) else Path(path)

    loader = general_loader.LoadFile(paths[0], None)

    loaded_image = LoadedImage(loader, afmreader_id)

    if channel:
        image, metadata = loaded_image.get_image_data(channel=channel)
    else:
        available_channels = loader.get_available_channels()

        label = "Available channels:"
        message = "Select a channel to load:"
        dialog = QInputDialog(None)
        dialog.setWindowTitle(message)
        dialog.setLabelText(label)
        dialog.setComboBoxItems(available_channels)
        dialog.setStyleSheet("QWidget { font-size: 9px; }")

        if dialog.exec():
            user_input = dialog.textValue()
        else:
            return None

        image, metadata = loaded_image.get_image_data(user_input)
    loaded_images.append(loaded_image)
    afmreader_id += 1

    viewer = current_viewer()
    if viewer is None:
        print(f"[DEBUG] CRITICAL: current_viewer() returned None!")

    if "Change channel" not in viewer.window.dock_widgets:
        image_options_widget = ImageOptions(viewer)
        viewer.window.add_dock_widget(image_options_widget, name="Change channel")

    add_kwargs = {"metadata": metadata}
    layer_type = "image"

    return [(image, add_kwargs, layer_type)]


class LoadedImage:
    def add_channel_image(self, channel):
        if self.viewer is None:
            self.viewer = current_viewer()

        loading_widget = LoadingWidget(self.viewer)
        loading_widget.start(f"Loading {self.path.stem}. This may take a moment.")

        loaded_data = self.loader.load(channel=channel)
        loading_widget.stop()

        if len(loaded_data) == 3:
            image, px2nm, self.curves_data = loaded_data
        elif len(loaded_data) == 2:
            image, px2nm = loaded_data
        else:
            print(f"[DEBUG] UNEXPECTED data length returned from loader: {len(loaded_data)}")

        self.image_channels[channel] = {"image": image, "px2nm": px2nm}

    def __init__(self, loader, id):
        global loaded_images
        self.loader = loader
        self.path = loader.filepath
        self.image_channels = {}
        self.curves_data = None
        self.available_channels = loader.get_available_channels()
        self.id = id
        self.current_channel = None
        self.viewer = None

    def select_channel_image(self, channel):
        if not self.viewer:
            self.viewer = current_viewer()
        self.current_channel = channel

    def get_image_data(self, channel):
        if channel not in self.image_channels:
            self.add_channel_image(channel)

        metadata = {
            "image_path": self.path,
            "px2nm": self.image_channels[channel]["px2nm"],
            "afmreader_id": self.id
        }
        if self.curves_data:
            metadata["force_curves"] = self.curves_data[0]
            metadata["force_curves_units"] = self.curves_data[1]
            metadata["available_channels"] = self.available_channels

        return self.image_channels[channel]["image"], metadata


class ImageOptions(QWidget):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.setLayout(QVBoxLayout())
        self.label = QLabel("Select a layer loaded with afmreader plugin to view available channels")
        self.label.setWordWrap(True)
        self.layout().addWidget(self.label)
        self.selected_channel = None
        self.available_channels = []
        self.loaded_image = None
        self.channel_selector = QComboBox()
        self.selected_layer = None

        self.get_loaded_data(None)

        self.layout().addWidget(self.channel_selector)
        self.channel_selector.currentTextChanged.connect(self.set_channel)
        viewer.layers.selection.events.connect(self.get_loaded_data)

    def get_loaded_data(self, event):
        self.selected_layer = self.viewer.layers.selection.active
        temp_selected_channel = self.selected_channel

        if self.selected_layer is None:
            self.channel_selector.clear()
            return
        self.label.setText(f"Change channel for layer '{self.selected_layer.name}'")

        current_id = self.selected_layer.metadata.get("afmreader_id")

        if current_id is not None:
            try:
                self.loaded_image = loaded_images[current_id]
            except IndexError as e:
                print(f"[DEBUG] ERROR: IndexError accessing loaded_images list: {e}")
                return

            self.available_channels = self.loaded_image.available_channels

            # Disconnect signal temporarily to avoid triggering set_channel during population
            self.channel_selector.blockSignals(True)
            self.channel_selector.clear()
            self.channel_selector.addItems(self.available_channels)
            self.channel_selector.blockSignals(False)

        if temp_selected_channel and temp_selected_channel in self.available_channels:
            self.channel_selector.setCurrentText(temp_selected_channel)

    def update_layer(self):
        if not self.loaded_image:
            return

        image, metadata = self.loaded_image.get_image_data(channel=self.selected_channel)

        if self.selected_layer is not None:
            self.selected_layer.data = image
            self.selected_layer.metadata = metadata
            self.selected_layer.reset_contrast_limits()
        else:
            print("[DEBUG] Selected layer is None, cannot update layer.")

    def set_channel(self, text):
        if not text:
            return
        self.selected_channel = text
        self.update_layer()