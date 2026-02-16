"""Use AFMReader to load Atomic Force Microscopy image files into Napari."""

import sys
from pathlib import Path

from AFMReader import general_loader
from loguru import logger
from qtpy.QtWidgets import QInputDialog  # pylint: disable = no-name-in-module


def napari_get_reader(path: list | str):
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

    # if we know we cannot read the file, we immediately return None.
    if not path.endswith((".asd", ".gwy", ".ibw", ".jpk", ".spm", ".stp", ".top", ".topostats", ".h5-jpk", ".jpk-qi-image")):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def suppress_ignorable_logging():
    """Suppress loguru logging messages containing '**IGNORE**'."""
    # Identify sinks you want to remove
    for hid, handler in list(logger._core.handlers.items()):
        if getattr(handler, "_is_caplog", False):
            continue  # keep caplog

        logger.remove(hid)

    # Add handler with a filter function
    def filter_ignore_errors(record):
        """
        Filter out 'not in channel list' error messages.

        Parameters
        ----------
        record : dict
            The log record.

        Returns
        -------
        bool
            True if the record should be logged, False otherwise.
        """
        return "**IGNORE**" not in record["message"]

    logger.add(
        sys.stderr,
        colorize=True,
        format="<blue>{time:HH:mm:ss}</blue> | <level>{level}</level> |"
        "<magenta>{file}</magenta>:<magenta>{module}</magenta>:<magenta>"
        "{function}</magenta>:<magenta>{line}</magenta> | <level>{message}</level>",
        filter=filter_ignore_errors,
    )


def reader_function(path, channel=None):
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
    suppress_ignorable_logging()
    # handle both a string and a list of strings
    paths = [Path(path)] if isinstance(path, str) else Path(path)
    # load all files into array
    if channel:
        loader = general_loader.LoadFile(paths[0], channel)
        image, px2nm = loader.load()
    else:
        loader = general_loader.LoadFile(paths[0], None)
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
        loader = general_loader.LoadFile(paths[0], user_input)
        image, px2nm = loader.load()

    # metadata should be the same for all images in a stack
    metadata = {
        "image_path": paths[0],
        "px2nm": px2nm,
    }

    # optional kwargs for the corresponding viewer.add_* method
    add_kwargs = {"metadata": metadata}

    layer_type = "image"  # optional, default is "image"
    return [(image, add_kwargs, layer_type)]
