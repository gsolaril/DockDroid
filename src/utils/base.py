"""Base configuration: paths and settings shared by every module.

Same idea as LTX-Python's `src/utils/base.py`: one place that knows where the
repository lives, so no other module has to guess with `..` or `os.getcwd()`.
Settings come from the environment, not from a JSON file -- there is nothing to
configure yet that a shell one-liner cannot express, and fewer moving parts is
the point of lesson 0.x.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

_FOLDER_UTILS = Path(__file__).resolve().parent
_FOLDER_ROOT = _FOLDER_UTILS.parent.parent


class Config(NamedTuple):
    FOLDER_ROOT: Path = _FOLDER_ROOT
    FOLDER_SRC: Path = _FOLDER_ROOT / "src"
    FOLDER_LOG: Path = _FOLDER_ROOT / "log"
    LOG_TO_FILE: bool = True
    LOG_LEVEL: str = os.getenv("DOCKDROID_LOG_LEVEL", "INFO").upper()
    MODEL: str = os.getenv("DOCKDROID_MODEL", "claude-sonnet-4-5")

    def __repr__(self) -> str:
        return "\n => ".join(f"{key}: {value}" for key, value in self._asdict().items())
