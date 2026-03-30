LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "daily_rotating_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "resources/logs/django.log",
            "when": "midnight",
            "backupCount": 30,
            "formatter": "verbose",
        },
        "daily_rotating_file_error_log": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "resources/logs/error.log",
            "when": "midnight",
            "backupCount": 30,
            "formatter": "verbose",
        },

    },
    "loggers": {
        "django": {
            "handlers": ["daily_rotating_file"],
            "level": "INFO",
            "propagate": True,
        },
        "error": {
            "handlers": ['daily_rotating_file_error_log'],
            "level": "ERROR",
            "propagate": True,
        }
    },
}
