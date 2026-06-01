# utils.py
# Shared utility helpers used across the application.

import logging
import sys


def setup_logger(name: str = "sentiment_api") -> logging.Logger:
    """Configure and return a named logger writing to stdout."""
    logger = logging.getLogger(name)

    if logger.handlers:
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


# ──────────────────────────────────────────────────────────────────────────────
# Label normalisation
# cardiffnlp/twitter-roberta-base-sentiment-latest returns lowercase labels:
#   "positive", "negative", "neutral"
# ──────────────────────────────────────────────────────────────────────────────

LABEL_MAP: dict[str, str] = {
    "positive": "Positive",
    "negative": "Negative",
    "neutral":  "Neutral",
    # fallback for older variant of the model
    "label_0":  "Negative",
    "label_1":  "Neutral",
    "label_2":  "Positive",
}


def map_label(raw_label: str) -> str:
    """Normalise a raw HuggingFace label to Positive / Neutral / Negative."""
    return LABEL_MAP.get(raw_label.lower(), raw_label.capitalize())
