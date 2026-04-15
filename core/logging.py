import logging
from enum import Enum


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


RESET = "\033[0m"
DARK_GRAY = "\033[90m"
WHITE = "\033[37m"

LEVEL_COLORS = {
    LogLevel.DEBUG: "\033[35m",
    LogLevel.INFO: "\033[34m",
    LogLevel.WARNING: "\033[33m",
    LogLevel.ERROR: "\033[31m",
    LogLevel.CRITICAL: "\033[41m",
}


class ColoredFormatter(logging.Formatter):
    format_str = "%(asctime)s %(levelname)s     %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        formatter = logging.Formatter(
            self.format_str,
            "%Y-%m-%d %H:%M:%S",
        )

        level = LogLevel(record.levelno)
        level_color = LEVEL_COLORS.get(level, RESET)

        original_levelname = record.levelname
        record.levelname = f"{level_color}{original_levelname}{RESET}"

        message = formatter.format(record)

        if hasattr(record, "asctime"):
            message = message.replace(
                record.asctime,
                f"{DARK_GRAY}{record.asctime}{RESET}",
                1,
            )

        record.levelname = original_levelname
        return message


def get_logger(name: str = "VoxStat", level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    return logger


logger: logging.Logger = get_logger()