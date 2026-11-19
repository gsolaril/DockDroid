"""Logging, set up once, used everywhere.

This mirrors how LTX-Python does it: loguru with one console sink and one file
sink, the same message shape in both, and the file sink always cheaper than the
console one (DEBUG goes to disk, INFO to the screen). The disk copy is what you
read after a run that failed at 03:00; the console copy is what you watch while
it happens.

    Log.info(...)      something a human wants to read
    Log.debug(...)     every step of the loop; off unless -v
    Log.error(...)     a failure we already understand
    Log.exception(...) a failure we do not
"""

from __future__ import annotations

import sys

from loguru import logger as Log

from .base import Config

LOG_FORMAT = {
    "stdout": "[<level>{time:HH:mm:ss.SSS} | /{module}.{function} @ L{line}</level>] {message}",
    "file": "[{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | /{module}.{function} @ L{line}] {message}",
}
LOGFILE_FORMAT = "{time:YYYYMMDD}.log"


def configure(level: str | None = None) -> None:
    """(Re)build the sinks. Called once at import, again if -v asks for DEBUG."""
    # `Config` is a NamedTuple *type*; its fields are only readable on an
    # instance. `Config.LOG_LEVEL` is a descriptor, not a string.
    config = Config()
    Log.remove()
    Log.add(
        sink=sys.stdout,
        level=level or config.LOG_LEVEL,
        colorize=True,
        backtrace=False,
        format=LOG_FORMAT["stdout"],
    )
    if config.LOG_TO_FILE:
        config.FOLDER_LOG.mkdir(parents=True, exist_ok=True)
        Log.add(
            sink=str(config.FOLDER_LOG / LOGFILE_FORMAT),
            level="DEBUG",
            colorize=False,
            format=LOG_FORMAT["file"],
            encoding="utf-8",
        )


configure()

__all__ = ["Log", "LOG_FORMAT", "LOGFILE_FORMAT", "configure"]
