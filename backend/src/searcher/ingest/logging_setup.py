"""Shared file-logging setup for the ingestion pipeline.

`parse.py` and `ingest.py` both log skipped/malformed rows to the same
`backend/ingest.log` file (see CLAUDE.md's data-handling conventions), so
the handler-attaching logic lives here once instead of being duplicated in
each module.
"""

from __future__ import annotations

import logging
from pathlib import Path

# backend/ingest.log -- three levels up from this file (ingest/ -> searcher/ -> src/ -> backend/).
LOG_PATH = Path(__file__).resolve().parents[3] / "ingest.log"


def configure_file_logging(logger: logging.Logger) -> None:
    """Attach a file handler pointed at `LOG_PATH` to `logger`, once per process."""
    already_attached = any(
        isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == LOG_PATH
        for handler in logger.handlers
    )
    if already_attached:
        return

    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
