"""Use AFMReader to load Atomic Force Microscopy image files into Napari."""

from pathlib import Path
from AFMReader import general_loader
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
    if not path.endswith((".asd", ".gwy", ".ibw", ".jpk", ".spm", ".stp", ".top", ".topostats")):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path, channel=None):
    """
    Read the AFM file formats.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    list[tuple]
        A list of a single LayerData tuple where each tuple in the list contains
        (data, metadata, layer_type="image"), where 'data' is a numpy array,
        'metadata' is a dict the filepath and pixel to nanometre scaling ratio.
    """
    # handle both a string and a list of strings
    paths = [Path(path)] if isinstance(path, str) else Path(path)
    # load all files into array
    if channel:
        loader = general_loader.LoadFile(paths[0], channel)
    else:
        loader = general_loader.LoadFile(paths[0], "Ignore this error message")
    image, px2nm = loader.load()
    if px2nm is None:
        image = f"{image}"
        # remove rightmost channel info # remove channel info
        available_channels = list(dict.fromkeys(
            channel.replace('"', '').replace("'", "") for channel in image[image.rindex("[") + 1:image.rindex("]")].split(", ")
        ))
    while px2nm is None:
        print("Shouldn't be here")
        message = "Select a channel to load:"
        user_input, ok = QInputDialog.getItem(
            None,                      # parent widget
            message,          # dialog title
            "Available channels:",     # label
            available_channels,        # items in dropdown
            0,                         # default index
            True                      # editable? (True = user can type custom)
        )
        if not ok:
            return None
        loader = general_loader.LoadFile(paths[0], user_input)
        image, px2nm = loader.load()
        if px2nm is None:
            available_channels = f"{image}."

    # metadata should be the same for all images in a stack
    metadata = {
        "image_path": paths[0],
        "px2nm": px2nm,
    }

    # optional kwargs for the corresponding viewer.add_* method
    add_kwargs = {"metadata": metadata}

    layer_type = "image"  # optional, default is "image"
    return [(image, add_kwargs, layer_type)]