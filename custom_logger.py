import logging
import sys


def get_custom_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s, %(levelname)s, %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
