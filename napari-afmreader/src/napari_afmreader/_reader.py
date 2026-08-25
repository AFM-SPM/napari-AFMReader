"""Use AFMReader to load Atomic Force Microscopy image files into Napari."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import napari
import numpy as np
from AFMReader import general_loader
from AFMReader.data_classes import AFMLoad, CurvesDataset
from loguru import logger
from magicgui.widgets import Combobox, create_widget
from napari import Viewer, current_viewer  # pylint: disable=no-name-in-module
from napari.layers import Image  # pylint: disable=no-name-in-module
from napari.utils.events import Event
from napari_afmreader._alerts import LoadingWidget
from qtpy.QtWidgets import (  # pylint: disable = no-name-in-module
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Global variable to give an id to each image layer loaded through this plugin
afmreader_id = 0
loaded_images: list[LoadedImage] = []
image_options_widget: ImageOptions | None = None

# Set to keep track of viewers that have already connected the layer cleanup
# callback to avoid duplicate connections between the potential for multiple viewers
layer_cleanup_connected_viewers: set[int] = set()

LayerData = list[tuple[np.ndarray, dict[str, Any], str]] | None
ReaderFunction = Callable[..., LayerData]


def napari_get_reader(path: list[str] | str) -> ReaderFunction | None:
    """
    Getter for the AFM file format reader.

    Parameters
    ----------
    path : str or list of str or Path
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    if not path.lower().endswith(
        (
            ".asd",
            ".ardf",
            ".gwy",
            ".ibw",
            ".jpk",
            ".spm",
            ".stp",
            ".top",
            ".topostats",
            ".h5-jpk",
            ".jpk-qi-image",
            ".jpk-qi-data",
            ".jpk-force-map",
            ".bin",
        )
    ):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(
    path: str | list[str], channel: str | None = None
) -> LayerData:
    """
    Read the AFM file formats.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.
    channel : str, optional
        The channel to load from the AFM file. If None, a dialog will prompt the user to select a channel.

    Returns
    -------
    list[tuple]
        A list of a single LayerData tuple where each tuple in the list contains
        (data, metadata, layer_type="image"), where 'data' is a numpy array,
        'metadata' is a dict the filepath and pixel to nanometre scaling ratio.
    """
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements,global-statement
    # Global afmreader_id used to assign a unique id to each loaded image layer for tracking in the plugin
    global afmreader_id, image_options_widget
    # Handle both a string and a list of strings
    paths = [Path(path)] if isinstance(path, str) else [Path(p) for p in path]

    # Create a loader instance for the first file path using AFMReader's general_loader
    loader = general_loader.LoadFile(paths[0], None)
    loading_widget = LoadingWidget(current_viewer())
    loading_widget.start(f"Opening {paths[0].stem}.")
    try:
        # Get any additional required parameters for loading the file from the loader
        additional_params = loader.get_additional_params()
    finally:
        loading_widget.stop()
    if additional_params:
        dialog = DynamicKwargsDialog(additional_params, filename=paths[0].name)

        # This opens the window and waits
        if dialog.exec():
            # User clicked OK
            params = dialog.get_values()
            additional_params.update(params)
            if "save_as_h5" in additional_params and additional_params["save_as_h5"]:
                loading_widget.start(f"Saving {paths[0].stem} as h5 file.")
                try:
                    loader.save_to_h5()
                finally:
                    loading_widget.stop()

    if channel:
        # No need to prompt user to select a channel, load the specified channel directly
        loaded_image = LoadedImage(loader, afmreader_id, required_kwargs=additional_params)
        image, metadata, pixel_to_nanometre_scaling = loaded_image.get_image_data(channel=channel)
    else:
        # If a channel isn't selected, open an input dialog so the user can select one
        loading_widget.start(f"Fetching channels from {paths[0].stem} and processing parameters.")
        try:
            available_channels = loader.get_available_channels(kwargs=additional_params)
        finally:
            loading_widget.stop()

        available_channels = available_channels.keys() if isinstance(available_channels, dict) else available_channels

        # Create a LoadedImage instance to manage the loaded image, its channels, and associated metadata
        loaded_image = LoadedImage(
            loader, afmreader_id, available_channels=available_channels, required_kwargs=additional_params
        )

        if available_channels != []:
            # If there are channels available for the file, prompt the user to select
            # a channel to load with an input dialog
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
                # The user canceled the dialog, so we return None to avoid loading any image data
                return None

            # Load the image data for the selected channel using the get_image_data method of the LoadedImage instance
            image, metadata, pixel_to_nanometre_scaling = loaded_image.get_image_data(user_input)
        else:
            # If no channels are available, no need to ask the user to select a channel, load the image data directly
            image, metadata, pixel_to_nanometre_scaling = loaded_image.get_image_data()

    # Add the loaded image to the list and update the running id
    loaded_images.append(loaded_image)
    afmreader_id += 1

    # Create a dock widget for channel selection if it doesn't already exist in the viewer
    viewer = current_viewer()
    if viewer is None:
        logger.error("Could not find current viewer")
    else:
        connect_layer_cleanup(viewer)
        if "Change channel" not in viewer.window.dock_widgets:
            image_options_widget = ImageOptions(viewer)
            viewer.window.add_dock_widget(image_options_widget, name="Change channel")

    # Add kwargs to the the layer with metadata and scale
    add_kwargs = {
        "metadata": metadata,
        "scale": [pixel_to_nanometre_scaling, pixel_to_nanometre_scaling],
    }
    layer_type = "image"

    # Return layer data to napari
    return [(image, add_kwargs, layer_type)]


class DynamicKwargsDialog(QDialog):  # pylint: disable=too-few-public-methods
    """
    Dialog to dynamically generate input fields for required kwargs.

    Parameters
    ----------
    required_kwargs : dict
        A dictionary of required kwargs where keys are the kwarg names and values are their expected types or options.
    filename : str
        The name of the file for which the parameters are being requested.
    parent : QWidget, optional
        The parent widget for the dialog.
    """

    def __init__(self, required_kwargs: dict[str, Any], filename: str, parent: QWidget | None = None) -> None:
        """
        Initialize the dialog with dynamic input fields based on required kwargs.

        Parameters
        ----------
        required_kwargs : dict
            A dictionary of required kwargs where keys are the kwarg names and values are their expected
            types or options.
        filename : str
            The name of the file for which the parameters are being requested.
        parent : QWidget, optional
            The parent widget for the dialog.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Enter Required Parameters for {filename}")
        self.setLayout(QVBoxLayout())
        self.widgets: dict[str, tuple[QWidget, Any]] = {}

        # Build the UI dynamically
        for name, arg_type in required_kwargs.items():
            # Add a label for clarity
            self.layout().addWidget(QLabel(f"{name.replace('_', ' ').title()}:"))

            # Add a widget based on the argument type
            if isinstance(arg_type, tuple):
                w = Combobox(name=name, choices=list(arg_type[1]))
            elif arg_type is bool:
                w = create_widget(name="", widget_type="CheckBox")
            elif arg_type is int:
                w = create_widget(name=name, widget_type="SpinBox", options={"min": 0, "max": 1000000})
            elif arg_type is float:
                w = create_widget(name=name, widget_type="FloatSpinBox", options={"min": 0, "max": 1000000})
            else:  # str, list, etc.
                w = create_widget(name=name, widget_type="LineEdit")

            # Add the widget to the dialog
            native_widget = getattr(w, "native", w)
            self.layout().addWidget(native_widget)

            # Store the widget and its type for later retrieval of values
            self.widgets[name] = (native_widget, arg_type)

        # Add Standard OK/Cancel Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout().addWidget(self.button_box)

    def get_values(self) -> dict[str, Any]:
        """
        Extract values from the widgets, converting to the appropriate types.

        Returns
        -------
        dict
            A dictionary of parameter names and their corresponding values.
        """
        results: dict[str, Any] = {}
        for name, (widget, arg_type) in self.widgets.items():
            # Access the native widget if it's a magicgui wrapper
            # If it's already a native widget, getattr returns widget itself
            w = getattr(widget, "native", widget)

            # Extract the value based on the widget type and convert to the appropriate type
            if arg_type is bool:
                results[name] = w.isChecked()
            elif arg_type in [int, float]:
                results[name] = w.value()
            elif isinstance(arg_type, tuple):
                results[name] = w.currentText()
            else:  # Standard LineEdit/String
                results[name] = w.text()
        return results


def update_image_options_widget():
    """Update the channel selector widget with the available channels for the currently selected layer."""
    if image_options_widget is not None:
        image_options_widget.get_loaded_data(None)


def connect_layer_cleanup(viewer: Viewer):
    """
    Connect AFMReader lazy-file cleanup to a viewer layer list once.

    Parameters
    ----------
    viewer : Viewer
        The napari viewer whose layer list should be monitored for removals.
    """
    layer_list_id = id(viewer.layers)
    if layer_list_id in layer_cleanup_connected_viewers:
        return

    # This is one viewer-level callback for all removed layers.
    viewer.layers.events.removed.connect(close_unused_curves)
    layer_cleanup_connected_viewers.add(layer_list_id)


def close_unused_curves(event: Event):
    """
    Close curve data when the last layer for a loaded AFM image is removed.

    Parameters
    ----------
    event : Event
        The napari layer removal event containing the removed layer.
    """
    layer = getattr(event, "value", None)
    metadata = getattr(layer, "metadata", {})
    layer_id = metadata.get("afmreader_id") if metadata else None
    if layer_id is None:
        return

    remaining_layers = getattr(event, "source", None)
    if remaining_layers is None:
        viewer = current_viewer()
        remaining_layers = viewer.layers if viewer is not None else []

    for remaining_layer in remaining_layers:
        if remaining_layer is layer:
            continue
        remaining_metadata = getattr(remaining_layer, "metadata", {})
        if remaining_metadata and remaining_metadata.get("afmreader_id") == layer_id:
            return

    loaded_image = get_loaded_image(layer_id)
    if loaded_image is None or loaded_image.curves_data is None:
        return

    try:
        loaded_image.curves_data.close()
    except AttributeError:
        logger.error(f"Curves data for loaded image {layer_id} does not have a close method.")
        return

    loaded_image.curves_data = None


def get_loaded_image(layer_id: int | None) -> LoadedImage | None:
    """
    Retrieve the LoadedImage instance associated with the given layer ID.

    Parameters
    ----------
    layer_id : int | None
        The ID of the layer for which to retrieve the LoadedImage instance.

    Returns
    -------
    LoadedImage or None
        The LoadedImage instance associated with the given layer ID, or None if not found.
    """
    if layer_id is None:
        logger.error("Layer ID is None, cannot retrieve loaded image.")
        return None

    if len(loaded_images) > layer_id and loaded_images[layer_id].layer_id == layer_id:
        return loaded_images[layer_id]
    for img in loaded_images:
        if img.layer_id == layer_id:
            return img
    logger.error(f"Could not find loaded image with id {layer_id}")
    return None


class LoadedImage:  # pylint: disable=too-many-instance-attributes
    """
    Class to manage loaded AFM images, their channels, and associated metadata.

    Parameters
    ----------
    loader : AFMReader general_loader.LoadFile instance
        The loader instance used to load AFM files.
    layer_id : int
        The ID of the layer associated with this loaded image.
    available_channels : list of str, optional
        A list of available channel names for the image. If not provided, it will be fetched from the loader.
    required_kwargs : dict, optional
        A dictionary of required keyword arguments for loading the image.
    flip_image : bool, optional
        Whether to flip the image vertically when loading. Defaults to True.
    """

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        loader: general_loader.LoadFile,
        layer_id: int,
        available_channels: Iterable[str] | dict[str, Any] | None = None,
        required_kwargs: dict[str, Any] | None = None,
        flip_image: bool = True,
    ):
        """
        Initialize the LoadedImage instance.

        Parameters
        ----------
        loader : general_loader.LoadFile
            The loader object used to load image data.
        layer_id : int
            The ID of the layer associated with this loaded image.
        available_channels : list of str, optional
            A list of available channel names.
        required_kwargs : dict, optional
            A dictionary of required keyword arguments for loading the image.
        flip_image : bool, optional
            Whether to flip the image vertically when loading. Defaults to True.
        """
        self.loader: general_loader.LoadFile = loader
        self.viewer: Viewer | None = current_viewer()

        # Set layer id (used for tracking in loaded images)
        self.layer_id: int = layer_id
        self.path: Path = self.loader.filepath
        self.flip_image: bool = flip_image
        self.loading_widget: LoadingWidget = LoadingWidget(self.viewer)
        self.available_channels: list[str] | None = self.fetch_available_channels(
            available_channels=available_channels, headless=True
        )

        # Initialize state variables for the LoadedImage instance
        self.current_channel: str | None = None
        self.image_channels: dict[str, AFMLoad] = {}
        self.curves_data: CurvesDataset | None = None
        self.required_kwargs: dict[str, Any] | None = required_kwargs

    def init_from_loader(
        self,
        available_channels: Iterable[str] | dict[str, Any] | None = None,
        required_kwargs: dict[str, Any] | None = None,
        flip_image: bool = True,
        headless: bool = False,
    ):
        """
        Initialise image state from the AFMReader loader.

        This allows the LoadedImage instance to be re-initialized with a new loader, without recreating
        the whole object.

        Parameters
        ----------
        available_channels : Iterable of str or dict of str to Any, optional
            Available channel names or a mapping of channel metadata.
        required_kwargs : dict, optional
            Additional keyword arguments required when loading image data.
        flip_image : bool, optional
            Whether to flip the image vertically when loading.
        headless : bool, optional
            Whether to suppress loading widget updates.
        """
        # Get relevant information from the loader to initialize the LoadedImage instance
        self.path = self.loader.filepath
        self.flip_image = flip_image
        self.loading_widget = LoadingWidget(self.viewer)
        self.available_channels = self.fetch_available_channels(
            available_channels=available_channels, headless=headless
        )

        # Initialize state variables for the LoadedImage instance
        self.current_channel: str | None = None
        self.image_channels: dict[str, AFMLoad] = {}
        self.curves_data: CurvesDataset | None = None
        self.required_kwargs: dict[str, Any] | None = required_kwargs

    def fetch_available_channels(
        self,
        available_channels: Iterable[str] | dict[str, Any] | None = None,
        headless: bool = False,
    ) -> list[str]:
        """
        Fetch available channels from the AFMReader loader.

        Parameters
        ----------
        available_channels : Iterable of str or dict of str to Any, optional
            Available channel names or a mapping of channel metadata.
        headless : bool, optional
            Whether to suppress loading widget updates.

        Returns
        -------
        list of str
            A list of available channel names.
        """
        if not headless:
            self.loading_widget.start(f"Fetching channels from {self.path.stem}.")
        try:
            self.available_channels = (
                available_channels if available_channels is not None else self.loader.get_available_channels()
            )
        finally:
            if not headless:
                self.loading_widget.stop()

        return (
            list(self.available_channels.keys())
            if isinstance(self.available_channels, dict)
            else list(self.available_channels)
        )

    def add_channel_image(self, channel: str | None, headless: bool = False):
        """
        Load the specified channel's image data and store it along with metadata.

        Parameters
        ----------
        channel : str or None
            The name of the channel to load.
        headless : bool, optional
            Whether to suppress loading widget updates.
        """
        if self.viewer is None:
            self.viewer = current_viewer()

        # Start the loading widget as loading from AFMReader can take some time if lots of curve data
        if not headless:
            self.loading_widget.start(f"Loading {self.path.stem}. This may take a moment.")
        try:
            loaded_data = self.loader.load(channel=channel, kwargs=self.required_kwargs)
        finally:
            if not headless:
                self.loading_widget.stop()

        # Default the channel name if no channels exist for the file so clear to user
        if channel is None:
            channel = "default"

        if loaded_data.curves_dataset is not None:
            self.curves_data = loaded_data.curves_dataset
            loaded_data.curves_dataset = None

        self.image_channels[channel] = loaded_data

    def add_custom_channel(self, channel_name: str, image_data: np.ndarray, z_units: str | None = None):
        """
        Add a custom channel with the specified name and image data.

        Parameters
        ----------
        channel_name : str
            The name of the custom channel to add.
        image_data : numpy.ndarray
            The image data for the custom channel.
        z_units : str, optional
            The units for the z-axis of the custom channel. If None, the units of the current channel are used.
        """
        if channel_name in self.image_channels:
            logger.warning(f"Channel '{channel_name}' already exists. Overwriting existing channel.")
        z_units = (
            z_units
            if z_units is not None
            else (self.image_channels[self.current_channel].z_units if self.current_channel else None)
        )
        pixel_to_nanometre_scaling = (
            self.image_channels[self.current_channel].pixel_to_nanometre_scaling if self.current_channel else 1
        )
        # pylint: disable-next=fixme
        # TODO do we want to add all the other parameters like timestamps, metadata, curves_dataset?
        # May lead to large memory usage? however aligns with the rest of the current channels
        self.image_channels[channel_name] = AFMLoad(
            image=image_data,
            pixel_to_nanometre_scaling=pixel_to_nanometre_scaling,
            z_units=z_units,
        )
        if channel_name not in self.available_channels:
            self.available_channels.append(channel_name)
        update_image_options_widget()

    def get_available_channels(self) -> list[str]:
        """
        Get the available channels for this image.

        Returns
        -------
        list of str
            A list of available channel names.
        """
        return self.available_channels

    def select_channel_image(self, channel: str, headless: bool = False):
        """
        Set the current channel's image data.

        Parameters
        ----------
        channel : str
            The name of the channel to display.
        headless : bool, optional
            Whether to skip viewer lookup when no viewer is already set.
        """
        if not self.viewer and not headless:
            self.viewer = current_viewer()
        self.current_channel = channel

    def get_map(self, channel: str | None = None) -> tuple[np.ndarray | None, float | None, str | None]:
        """
        Get the image data for the specified channel, loading it if it hasn't been loaded yet.

        Parameters
        ----------
        channel : str, optional
            The name of the channel to retrieve.

        Returns
        -------
        tuple
            A tuple containing the image data, pixel-to-nanometer scaling factor, and z-axis units for the channel.
        """
        # If the requested channel's image data hasn't been loaded yet, load it with AFMReader
        if channel not in self.image_channels and (channel is not None or "default" not in self.image_channels):
            self.add_channel_image(channel)
        return_image = self.image_channels[channel].image if channel in self.image_channels else None
        pixel_to_nanometre_scaling = (
            self.image_channels[channel].pixel_to_nanometre_scaling if channel in self.image_channels else None
        )
        return_z_units = self.image_channels[channel].z_units if channel in self.image_channels else None
        return return_image, pixel_to_nanometre_scaling, return_z_units

    def get_image_data(self, channel: str | None = None) -> tuple[np.ndarray, dict[str, Any], float]:
        """
        Retrieve the image data and metadata for the specified channel.

        Parameters
        ----------
        channel : str, optional
            The name of the channel to retrieve. If None (no channels exist for the file), the default channel is used.

        Returns
        -------
        tuple
            A tuple containing the image data, metadata dictionary, pixel-to-nanometer scaling factor, and z-axis units.
        """
        # If the requested channel's image data hasn't been loaded yet, load it with AFMReader
        if channel not in self.image_channels and (channel is not None or "default" not in self.image_channels):
            self.add_channel_image(channel)

        # Update the current channel with selected channel
        self.select_channel_image(channel)

        # If the channel is still None (no channels exist for the file), set it to "default" so lack of channels
        # is handled gracefully and user can see that image file has only one mode
        if channel is None:
            channel = "default"

        # Construct metadata dictionary for the layer.
        metadata = {
            "image_path": self.path,
            "px2nm": self.image_channels[channel].pixel_to_nanometre_scaling,
            "channel": channel,
            "afmreader_id": self.layer_id,
            "available_channels": self.available_channels,
            "z_units": self.image_channels[channel].z_units,
        }

        return (
            self.image_channels[channel].image,
            metadata,
            self.image_channels[channel].pixel_to_nanometre_scaling,
        )

    def set_required_kwargs(self, required_kwargs: dict[str, Any]):
        """
        Set the required kwargs for loading the image data.

        Parameters
        ----------
        required_kwargs : dict
            A dictionary of required keyword arguments for loading the image data.
        """
        self.required_kwargs = required_kwargs

    def get_current_channel(self) -> str | None:
        """
        Get the name of the currently selected channel.

        Returns
        -------
        str or None
            The name of the currently selected channel, or None if no channel has been selected.
        """
        return self.current_channel

    def get_current_load(self) -> AFMLoad | None:
        """
        Get the AFMLoad instance for the currently selected channel.

        Returns
        -------
        AFMLoad
            The AFMLoad instance for the currently selected channel.
        """
        if self.current_channel in self.image_channels:
            return self.image_channels[self.current_channel]
        return None


class ImageOptions(QWidget):
    """
    A dock widget for selecting channels from loaded AFM images.

    Parameters
    ----------
    viewer : napari.Viewer
        The napari viewer instance to interact with.
    """

    def __init__(self, viewer: Viewer):
        """
        Initialize the ImageOptions widget.

        Parameters
        ----------
        viewer : napari.Viewer
            The napari viewer instance to interact with.
        """
        super().__init__()
        self.viewer = viewer
        layout = QHBoxLayout(self)
        self.label = QLabel("Select a layer loaded with afmreader plugin to view available channels")

        # Keep long layer names readable without allowing this compact dock widget
        # to grow vertically beyond two lines of text.
        self.label.setWordWrap(True)
        self.label.setMaximumHeight(self.label.fontMetrics().lineSpacing() * 2)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.label)
        layout.addStretch()

        # Initialize state variables
        self.selected_channel: str | None = None
        self.available_channels: list[str] = []
        self.loaded_image: LoadedImage | None = None
        self.channel_selector = QComboBox()
        self.channel_selector.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.selected_layer: napari.layers.Layer | None = None

        # Call get_loaded_data once to initialize the widget based on the current
        # selection (if any) when the widget is created
        self.get_loaded_data(None)

        layout.addWidget(self.channel_selector)
        self.channel_selector.currentTextChanged.connect(self.set_channel)

        # The contents only need a single control row (or at most two wrapped
        # label lines), so do not consume otherwise unused dock height.
        content_height = max(self.label.maximumHeight(), self.channel_selector.sizeHint().height())
        margins = layout.contentsMargins()
        self.setMaximumHeight(content_height + margins.top() + margins.bottom())
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Run get_loaded_data whenever the layer selection changes in the viewer to update the available channels
        viewer.layers.selection.events.connect(self.get_loaded_data)

    def get_loaded_data(self, event: Event | None):
        """
        Get the currently selected layer in the viewer and update the channel selector.

        Parameters
        ----------
        event : napari.utils.events.Event
            The event object containing information about the layer selection change.
        """
        # pylint: disable=unused-argument
        # Get the currently selected layer in the viewer
        self.selected_layer = self.viewer.layers.selection.active
        temp_selected_channel = self.selected_channel

        # If deselected layer, simply clear the channel selector and return
        if self.selected_layer is None:
            self.channel_selector.clear()
            return

        # Update the label to show which layer is selected
        label_text = f"Change channel for layer '{self.selected_layer.name}'"
        self.label.setText(label_text)
        self.label.setToolTip(label_text)
        current_id = self.selected_layer.metadata.get("afmreader_id")

        if current_id is not None:
            # Try to find the loaded image with the corresponding id in loaded_images
            try:
                self.loaded_image = loaded_images[current_id]
            except IndexError as e:
                logger.error(f"Could not find layer with id {current_id} in loaded images with error: {e}")
                return

            # Retrieve available channels for the selected layer's image
            self.available_channels = self.loaded_image.get_available_channels()

            # Disconnect signal temporarily to avoid triggering set_channel during population
            self.channel_selector.blockSignals(True)

            # Update the channel selector with available channels for the selected layer
            self.channel_selector.clear()
            self.channel_selector.addItems(self.available_channels)
            self.channel_selector.setCurrentText(self.loaded_image.current_channel)

            # Reconnect the signal after population
            self.channel_selector.blockSignals(False)

        if temp_selected_channel and temp_selected_channel in self.available_channels:
            # If the previously selected channel is still available for the newly selected layer, keep it selected
            self.channel_selector.setCurrentText(temp_selected_channel)

    def update_layer(self):
        """Update the currently selected layer in the viewer with the image data from the selected channel."""
        if not self.loaded_image:
            return

        # Gets the image data and metadata for the currently selected channel from the loaded image.
        # This will trigger loading the image data for the selected channel with AFMReader if it hasn't been loaded yet.
        image, metadata, _ = self.loaded_image.get_image_data(channel=self.selected_channel)

        if self.selected_layer is not None:
            # Update the selected layer's data and metadata with the new image and metadata for the selected channel.
            self.selected_layer.data = image
            self.selected_layer.metadata = metadata

            if isinstance(self.selected_layer, Image):
                # Reset the contrast limits of the layer to fit the new image data
                self.selected_layer.reset_contrast_limits()
        else:
            logger.debug("Selected layer is None, cannot update layer.")

    def set_channel(self, text: str):
        """
        Set the selected channel and update the layer.

        Parameters
        ----------
        text : str
            The name of the channel selected in the channel selector.
        """
        if not text:
            return
        self.selected_channel = text
        self.update_layer()
