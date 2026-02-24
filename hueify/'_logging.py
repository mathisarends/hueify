import logging

LIBRARY_NAME = "hueify"

logging.getLogger(LIBRARY_NAME).addHandler(logging.NullHandler())


def configure_logging(level: str = "WARNING") -> None:
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logger = logging.getLogger(LIBRARY_NAME)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.setLevel(log_level)
    logger.addHandler(handler)
