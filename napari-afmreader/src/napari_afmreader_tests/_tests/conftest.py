"""Fixtures for Pytest."""

import pytest
from napari_afmreader._reader import logger
from _pytest.logging import LogCaptureFixture


@pytest.fixture()
def caplog(caplog: LogCaptureFixture):  # pylint: disable=redefined-outer-name
    """Instantiate the logging capture for loguru into caplog."""
    def filter(record):
        # Don't log messages containing **IGNORE**
        return record["level"].no >= caplog.handler.level

    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=filter,
        enqueue=False,
    )
    logger._core.handlers[handler_id]._is_caplog = True
    yield caplog
    logger.remove(handler_id)
