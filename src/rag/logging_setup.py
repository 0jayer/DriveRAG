from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

NOISY_LOGGERS = (
    "googleapiclient.discovery_cache",
    "urllib3",
    "httpx",
    "httpcore",
)


def setup_logging(
    level: str | None = None,
    log_file: str | Path | None = None,
) -> None:
    """Configure application-wide logging for CLI entrypoints."""
    resolved_level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_level = getattr(logging, resolved_level_name, None)
    if not isinstance(resolved_level, int):
        raise ValueError(f"Invalid log level: {resolved_level_name!r}")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
        )

    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=resolved_level,
        handlers=handlers,
        force=True,
    )

    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

