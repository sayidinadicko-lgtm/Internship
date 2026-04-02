"""Structured logging factory."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    from ledeclicmental.config import settings  # late import to avoid circular

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stdout handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # File handlers (create dirs if missing)
    logs_dir: Path = settings.data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    app_fh = RotatingFileHandler(logs_dir / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    app_fh.setLevel(logging.DEBUG)
    app_fh.setFormatter(fmt)
    logger.addHandler(app_fh)

    err_fh = RotatingFileHandler(logs_dir / "error.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    err_fh.setLevel(logging.ERROR)
    err_fh.setFormatter(fmt)
    logger.addHandler(err_fh)

    return logger
