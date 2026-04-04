from __future__ import annotations

import logging
from pathlib import Path

from .utils import ensure_directory


def configure_logging(log_dir: Path) -> logging.Logger:
    ensure_directory(log_dir)
    logger = logging.getLogger("site_workflow")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_dir / "site_workflow.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
