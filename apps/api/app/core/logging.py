"""Настройка логирования."""

from __future__ import annotations

import logging.config

_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def setup_logging() -> None:
    logging.config.dictConfig(_LOGGING_CONFIG)
