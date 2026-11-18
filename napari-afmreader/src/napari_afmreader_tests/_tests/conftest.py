"""Fixtures for Pytest."""

from collections.abc import Iterator, Mapping
from typing import Any

import napari
import pytest
from _pytest.logging import LogCaptureFixture
from napari import Viewer
from napari_afmreader._reader import logger
from pytestqt.qtbot import QtBot


@pytest.fixture()
def caplog(caplog: LogCaptureFixture) -> Iterator[LogCaptureFixture]:  # pylint: disable=redefined-outer-name
    """Instantiate the logging capture for loguru into caplog."""

    def filter_level(record: Mapping[str, Any]) -> bool:
        # Don't log messages containing **IGNORE**
        return record["level"].no >= caplog.handler.level

    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=filter_level,
        enqueue=False,
    )
    logger._core.handlers[handler_id]._is_caplog = True
    yield caplog
    logger.remove(handler_id)


@pytest.fixture(name="napari_viewer")
def napari_viewer_fixture(qtbot: QtBot) -> Viewer:
    """Create a Napari viewer with QtBot cleanup."""
    viewer = napari.Viewer(show=False)  # pylint: disable=not-callable
    qtbot.addWidget(viewer.window._qt_window)  # pylint: disable=protected-access

    return viewer
