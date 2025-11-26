"""Fixtures for Pytest."""

import pytest
from _pytest.logging import LogCaptureFixture
from napari_afmreader._reader import logger


@pytest.fixture()
def caplog(caplog: LogCaptureFixture):  # pylint: disable=redefined-outer-name
    """Instantiate the logging capture for loguru into caplog."""

    def filter_level(record):
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
