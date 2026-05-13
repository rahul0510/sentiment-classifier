# model.py
# Responsible for loading the HuggingFace model exactly once at startup and
# exposing a single predict() function consumed by the API routes.
#
# We use a module-level singleton (_pipeline) so the model is loaded into
# memory only once per process, keeping inference latency low.

from __future__ import annotations

from functools import lru_cache
from typing import Any

from transformers import pipeline

from app.utils import map_label, setup_logger

logger = setup_logger("model")

# ──────────────────────────────────────────────────────────────────────────────
# Model configuration
# ──────────────────────────────────────────────────────────────────────────────

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"

# HuggingFace Pipelines are NOT thread-safe by default.
# Setting device=-1 forces CPU inference which is safe for concurrent requests
# without needing CUDA streams.  Swap to device=0 if a GPU is available.
DEVICE = -1  # -1 = CPU, 0 = first GPU


# ──────────────────────────────────────────────────────────────────────────────
# Singleton loader
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_pipeline() -> Any:
    """
    Load and cache the sentiment analysis pipeline.

    lru_cache ensures the model is only downloaded and loaded once for the
    entire lifetime of the process, regardless of how many requests arrive.
    """
    logger.info("Loading model: %s  (this may take a moment on first run)", MODEL_NAME)
    sentiment_pipeline = pipeline(
        task="sentiment-analysis",
        model=MODEL_NAME,
        device=DEVICE,
    )
    logger.info("Model loaded successfully.")
    return sentiment_pipeline


# ──────────────────────────────────────────────────────────────────────────────
# Public inference function
# ──────────────────────────────────────────────────────────────────────────────

def predict(text: str) -> dict[str, Any]:
    """
    Run sentiment inference on a single piece of text.

    Args:
        text: Raw input string from the user.

    Returns:
        A dict with keys:
          - sentiment (str): 'Positive', 'Neutral', or 'Negative'
          - confidence (float): Model confidence score in [0, 1]

    Raises:
        RuntimeError: If the pipeline returns an unexpected result structure.
    """
    nlp = get_pipeline()

    # truncation=True silently truncates texts longer than the model's max
    # token length (512 for RoBERTa) instead of raising an error.
    results: list[dict] = nlp(text, truncation=True)

    if not results:
        raise RuntimeError("Model returned an empty result.")

    top_result = results[0]
    raw_label: str = top_result["label"]
    score: float = round(float(top_result["score"]), 4)

    sentiment = map_label(raw_label)

    logger.info("Prediction: %s (%.4f) for text snippet: %.60r", sentiment, score, text)

    return {"sentiment": sentiment, "confidence": score}
