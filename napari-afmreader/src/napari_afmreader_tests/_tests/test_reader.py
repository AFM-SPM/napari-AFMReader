"""Tests for the AFMReader reader."""

from pathlib import Path
from unittest.mock import patch

import pytest
from napari_afmreader._reader import napari_get_reader

BASE_DIR = Path.cwd()
RESOURCES = BASE_DIR / "napari-afmreader" / "src" / "napari_afmreader_tests" / "_tests" / "resources"


@pytest.mark.parametrize(
    ("filepath", "side_effect", "expected_messages", "additional_reader_kwargs"),
    [
        pytest.param(
            str(RESOURCES / "file.asd"),
            [("TP", True)],
            ["Extracted image"],
            {},
            id="load asd valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.gwy"),
            [("ZSensor", True)],
            ["Extracted image"],
            {},
            id="load gwy valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.ibw"),
            [("HeightTracee", True)],
            ["Extracted image"],
            {},
            id="load ibw valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.jpk"),
            [("height_trace", True)],
            ["Extracted image"],
            {},
            id="load jpk valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.spm"),
            [("Height", True)],
            ["Extracted channel Height"],
            {},
            id="load spm valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.stp"),
            [("Height", True)],
            ["Extracted image"],
            {},
            id="load stp single-pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.top"),
            [("Height", True)],
            ["Extracted image"],
            {},
            id="load top single-pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.topostats"),
            [("image_original", True)],
            ["Extracted .topostats dictionary"],
            {},
            id="load topostats image_original valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.topostats"),
            [("image", True)],
            ["Extracted .topostats dictionary"],
            {},
            id="load topostats image valid pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.spm"),
            [("Height", True)], 
            ["Extracted channel Height"],
            {"channel": "Height"},
            id="load spm valid pass with channel kwarg.",
        ),
    ],
)
def test_get_reader_returns_callable(
    caplog: pytest.LogCaptureFixture,
    filepath: str,
    side_effect: list,
    expected_messages: list,
    additional_reader_kwargs: dict,
):
    """Calling get_reader on numpy file returns callable."""
    messages_seen = []

    def get_text_side_effect(*args, **_kwargs):
        # Capture the message shown in the dialogue
        _, message = args[1], args[2]
        messages_seen.append(message)
        # Second call returns the test's desired input
        return side_effect[0]

    # simulate QtPy dialogue box as this causes pytest to crash - need to add patch to where it is called
    with patch(
        "napari_afmreader._reader.QInputDialog.getItem",
        side_effect=get_text_side_effect,
    ):
        # try to read it in
        reader = napari_get_reader(filepath)

        assert callable(reader)
        layer_data_list = reader(filepath, **additional_reader_kwargs)

    # reads terminal output - wrong channel msg and completion msg
    for expected_message in expected_messages:
        assert expected_message in caplog.text
    # reads dialogue box messages
    expected_messages_box = [
        "Available channels:",
        *expected_messages[:-1],
    ]  # upto final expected message
    for expected_message_box, message_seen in zip(expected_messages_box, messages_seen):
        print(expected_message_box)
        print(expected_messages_box)
        assert expected_message_box in message_seen

    assert isinstance(layer_data_list, list)
    assert len(layer_data_list) > 0

    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple)
    assert layer_data_tuple[2] == "image"


@pytest.mark.parametrize(
    ("filepath"),
    [
        pytest.param(str(RESOURCES / "file.asd"), id="Cancelled dialogue box."),
    ],
)
def test_get_reader_cancel_box(filepath: str):
    """Cancel dialogue box returns None."""
    # simulate QtPy dialogue box as this causes pytest to crash - need to add patch to where it is called
    with patch(
        "napari_afmreader._reader.QInputDialog.getItem",
        side_effect=[("TP", False)],
    ):
        # try to read it in
        reader = napari_get_reader(filepath)
        assert reader(filepath) is None


@pytest.mark.parametrize(
    ("filepath"),
    [
        pytest.param(str(RESOURCES / "file.xxx"), id="Not supported extension."),
    ],
)
def test_get_reader_unsupported(filepath: str):
    """Unsupported file format returns None."""
    # simulate QtPy dialogue box as this causes pytest to crash - need to add patch to where it is called
    with patch(
        "napari_afmreader._reader.QInputDialog.getItem",
        side_effect=[("TP", False)],
    ):
        # try to read it in
        assert napari_get_reader(filepath) is None
