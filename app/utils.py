# utils.py
# Shared utility helpers used across the application.
# Keeping these here avoids circular imports and makes testing easier.

import logging
import sys


def setup_logger(name: str = "sentiment_api") -> logging.Logger:
    """
    Configure and return a named logger.

    Logs are written to stdout with a human-readable format so they appear
    cleanly in Docker container logs.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Avoid adding duplicate handlers if this is called more than once
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Label mapping: the cardiffnlp/twitter-roberta-base-sentiment model outputs
# integer ids 0, 1, 2 corresponding to these human-readable labels.
LABEL_MAP: dict[str, str] = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive",
}


def map_label(raw_label: str) -> str:
    """
    Convert a raw HuggingFace label string to a human-readable sentiment name.

    Args:
        raw_label: The label returned by the pipeline, e.g. 'LABEL_0'.

    Returns:
        One of 'Negative', 'Neutral', 'Positive', or the raw label if unknown.
    """
    return LABEL_MAP.get(raw_label, raw_label)
