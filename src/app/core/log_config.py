import logging
from logging.config import dictConfig

from app.core.config import get_settings

settings = get_settings()

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging() -> None:
    level = "DEBUG" if settings.debug else "INFO"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": LOG_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "app": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
            },
            "root": {"handlers": ["console"], "level": "WARNING"},
        }
    )

    logging.getLogger("app").debug("Logging configured, level=%s", level)
