# logging_config.py
import logging.config
import sys

# Log levels
# DEBUG, INFO, WARNING, ERROR, CRITICAL

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(levelname)s:%(name)s:%(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "uvicorn_access": {
            "format": "%(levelname)s:%(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": sys.stdout, # Direct logs to stdout
        },
    },
    "loggers": {
        # Root logger setup
        "": {
            "handlers": ["console"],
            "level": "INFO", # Default log level for your application code
            "propagate": True,
        },
        # Uvicorn loggers (can be configured separately)
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO", # Set to DEBUG to see all request logs
            "propagate": False,
        },
        # Your specific application logger
        "my_fastapi_app": {
            "handlers": ["console"],
            "level": "DEBUG", # Set to DEBUG for detailed debugging
            "propagate": False,
        },
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)