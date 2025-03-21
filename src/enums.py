from enum import IntEnum


class ExitCodeType(IntEnum):
    EXIT_OK = 0
    EXIT_ERROR = 1


class LogLevelType(IntEnum):
    """Log Level Name to Verbosity level."""

    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
