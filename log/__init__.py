import logging
from config import LOG_LEVEL, LOG_FORMAT

# Configure logger and its level
_logger = logging.getLogger("Goto IoT")
_logger.setLevel(getattr(logging, LOG_LEVEL))
# Sets stream handler for logger
_stream = logging.StreamHandler()
_stream.setLevel(getattr(logging, LOG_LEVEL))
# Configure log format as desired
_formatter = logging.Formatter(LOG_FORMAT)
_stream.setFormatter(_formatter)
# Add handler to logger
_logger.addHandler(_stream)


def error(message):
    _logger.error(message)


def warn(message):
    _logger.warn(message)


def info(message):
    _logger.info(message)


def debug(message):
    _logger.debug(message)
