import logging

from src.enums import LogLevelType


def init_logging(level: LogLevelType) -> None:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
    logging.basicConfig(format=log_format, level=level)
    logging.getLogger('paramiko').setLevel(logging.WARNING)
