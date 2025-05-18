"""Tests for the AFMReader reader."""

from pathlib import Path
from unittest.mock import patch

import pytest
from napari_afmreader._reader import napari_get_reader

BASE_DIR = Path.cwd()
RESOURCES = BASE_DIR / "napari-afmreader" / "src" / "napari_afmreader_tests" / "_tests" / "resources"


@pytest.mark.parametrize(
    ("filepath", "side_effect", "expected_messages"),
    [
        pytest.param(
            str(RESOURCES / "file.asd"),
            [("WrongChannel_asd", True), ("TP", True)],
            [
                "'WrongChannel_asd' not found .asd channel list: TP, PH",
                "Extracted image",
            ],
            id="load asd file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.gwy"),
            [("WrongChannel_gwy", True), ("ZSensor", True)],
            [
                "'WrongChannel_gwy' not found in .gwy channel list: {'ZSensor': '0', 'Peak Force Error': '1', "
                "'Stiffness': '2', 'LogStiffness': '3', 'Adhesion': '4', 'Deformation': '5', 'Dissipation': '6', "
                "'Height': '7'}",
                "Extracted image",
            ],
            id="load gwy file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.ibw"),
            [("WrongChannel_ibw", True), ("HeightTracee", True)],
            [
                "'WrongChannel_ibw' not in .ibw channel list: ['HeightTracee', 'HeightRetrace', 'ZSensorTrace', "
                "'ZSensorRetrace', 'UserIn0Trace', 'UserIn0Retrace', 'UserIn1Trace', 'UserIn1Retrace']",
                "Extracted image",
            ],
            id="load ibw file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.jpk"),
            [("WrongChannel_jpk", True), ("height_trace", True)],
            [
                "'WrongChannel_jpk' not in .jpk channel list: {'height_retrace': 1, 'measuredHeight_retrace': 2, "
                "'amplitude_retrace': 3, 'phase_retrace': 4, 'error_retrace': 5, 'height_trace': 6, "
                "'measuredHeight_trace': 7, 'amplitude_trace': 8, 'phase_trace': 9, 'error_trace': 10}",
                "Extracted image",
            ],
            id="load jpk file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.spm"),
            [("WrongChannel_spm", True), ("Height", True)],
            [
                "'WrongChannel_spm' not in .spm channel list: ['Height Sensor', 'Peak Force Error', 'DMTModulus', "
                "'LogDMTModulus', 'Adhesion', 'Deformation', 'Dissipation', 'Height']",
                "Extracted channel Height",
            ],
            id="load spm file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.stp"),
            [("fslkgnags", True)],
            [
                "Extracted image",
            ],
            id="load stp file 1st pass - can't fail due to channel as there's only 1 channel.",
        ),
        pytest.param(
            str(RESOURCES / "file.top"),
            [("sljbns", True)],
            [
                "Extracted image",
            ],
            id="load top file 1st pass - can't fail due to channel as there's only 1 channel.",
        ),
        pytest.param(
            str(RESOURCES / "file.topostats"),
            [("WrongChannel_topostats", True), ("image_original", True)],
            [
                "WrongChannel_topostats' not in available image keys: ['image', 'image_original']",
                "Extracted .topostats dictionary",
            ],
            id="load topostats image_original file 2nd pass.",
        ),
        pytest.param(
            str(RESOURCES / "file.topostats"),
            [("WrongChannel_topostats", True), ("image", True)],
            [
                "WrongChannel_topostats' not in available image keys: ['image', 'image_original']",
                "Extracted .topostats dictionary",
            ],
            id="load topostats image file 2nd pass.",
        ),
    ],
)
def test_get_reader_returns_callable(
    caplog: pytest.LogCaptureFixture,
    filepath: str,
    side_effect: list,
    expected_messages: list,
):
    """Calling get_reader on numpy file returns callable."""
    messages_seen = []

    def get_text_side_effect(*args, **_kwargs):
        # Capture the message shown in the dialogue
        _, message = args[1], args[2]
        messages_seen.append(message)

        # First call returns a wrong channel
        if len(messages_seen) == 1:
            return side_effect[0]
        # Second call returns the test's desired input
        return side_effect[1]

    # simulate QtPy dialogue box as this causes pytest to crash - need to add patch to where it is called
    with patch(
        "napari_afmreader._reader.QInputDialog.getText",
        side_effect=get_text_side_effect,
    ):
        # try to read it in
        reader = napari_get_reader(filepath)

        assert callable(reader)
        layer_data_list = reader(filepath)

    # reads terminal output - wrong channel msg and completion msg
    for expected_message in expected_messages:
        assert expected_message in caplog.text
    # reads dialogue box messages
    expected_messages_box = [
        "Channel Name: ",
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
        "napari_afmreader._reader.QInputDialog.getText",
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
        "napari_afmreader._reader.QInputDialog.getText",
        side_effect=[("TP", False)],
    ):
        # try to read it in
        assert napari_get_reader(filepath) is None
