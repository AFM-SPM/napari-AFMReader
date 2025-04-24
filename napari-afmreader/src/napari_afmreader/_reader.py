"""
Use AFMReader to load Atomic Force Miscroscopy image files into Napari.
"""

from pathlib import Path

from qtpy.QtWidgets import QInputDialog
from AFMReader import general_loader


def napari_get_reader(path: list | str | Path):
    """
    Reader for the '.asd', '.gwy', '.ibw', '.jpk', '.spm', '.stp', '.top',
    '.topostats' file formats.

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
    if not path.endswith(
        (".asd", ".gwy", ".ibw", ".jpk", ".spm", ".stp", ".top", ".topostats")
    ):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path):
    """
    Take a path or list of paths and return a list of LayerData tuples.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list[tuple]
        A list of a single LayerData tuple where each tuple in the list contains
        (data, metadata, layer_type="image"), where 'data' is a numpy array,
        'metadata' is a dict the filepath and pixel to nanometre scaling ratio.
    """
    # handle both a string and a list of strings
    paths = [Path(path)] if isinstance(path, str) else Path(path)
    # load all files into array
    available_channels = None
    while True:
        if available_channels is None:
            message = "Channel Name: "
        else:
            message = f"Available channels: {available_channels}"
        # adds dialog box for channel input
        user_input, ok = QInputDialog.getText(None, "Input Channel", message)
        if not ok:
            return None
        loader = general_loader.LoadFile(paths[0], user_input)
        image, px2nm = loader.load()
        if px2nm is None:
            available_channels = f"{image}."
        else:
            break

    # metadata should be the same for all images in a stack
    metadata = {
        "image_path": paths[0],
        "px2nm": px2nm,
    }

    # optional kwargs for the corresponding viewer.add_* method
    add_kwargs = {"metadata": metadata}

    layer_type = "image"  # optional, default is "image"
    return [(image, add_kwargs, layer_type)]
