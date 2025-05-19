"""Fixtures for Pytest."""

import pytest
from AFMReader.logging import logger
from _pytest.logging import LogCaptureFixture


@pytest.fixture()
def caplog(caplog: LogCaptureFixture):  # pylint: disable=redefined-outer-name
    """Instantiate the logging capture for loguru into caplog."""
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)
