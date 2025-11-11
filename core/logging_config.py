# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""Centralized logging configuration for Sofware-AI.

This module provides the setup_logging() function which configures a console handler
and a rotating file handler (data/logs/app.log). It also installs an exception hook
so uncaught exceptions are logged.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


DEFAULT_LOG_FILE = Path("data") / "logs" / "app.log"


def ensure_logs_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(log_file: Optional[str] = None, level: Optional[int] = None) -> None:
    """Configure the application's root logger.

    - RotatingFileHandler -> data/logs/app.log (max 5 MB, 5 backups)
    - StreamHandler -> console output (stdout)
    - Log level is taken from the `level` argument, then from the LOG_LEVEL
      environment variable, and falls back to INFO.
    """
    log_path = Path(log_file) if log_file else DEFAULT_LOG_FILE
    ensure_logs_dir(log_path)

    env_level = os.getenv("LOG_LEVEL")
    if level is None:
        if env_level:
            try:
                level = int(env_level)
            except Exception:
                level_name = env_level.upper()
                level = getattr(logging, level_name, logging.INFO)
        else:
            level = logging.INFO

    root = logging.getLogger()
    # Ensure 'level' is a valid logging level (int or string name)
    lvl = level
    if not isinstance(lvl, int):
        try:
            lvl = int(lvl)  # type: ignore[arg-type]
        except Exception:
            lvl = getattr(logging, str(lvl).upper(), logging.INFO)
    root.setLevel(lvl)

    # Remove existing handlers to avoid duplicate logging after reconfigure 
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(lvl)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        filename=str(log_path), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(lvl)
    fh.setFormatter(formatter)
    root.addHandler(fh)


def install_exception_hook() -> None:
    """Install a sys.excepthook that logs uncaught exceptions."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through for a clean exit
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger().exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


__all__ = ["setup_logging", "install_exception_hook"]