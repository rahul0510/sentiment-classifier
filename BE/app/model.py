# model.py
# Calls the Groq API (Llama 3) for sentiment classification.
# No local model — inference runs on Groq's servers.

from __future__ import annotations

import json
import os
from typing import Any

import requests

from app.utils import setup_logger

logger = setup_logger("model")

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

# ──────────────────────────────────────────────────────────────────────────────
# System prompt — forces Llama 3 to return only structured JSON
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a sentiment analysis engine.
Classify the sentiment of the user's text and respond ONLY with a JSON object in this exact format:
{"sentiment": "<label>", "confidence": <score>}

Rules:
- sentiment must be exactly one of: Positive, Negative, Neutral
- confidence must be a float between 0.0 and 1.0
- Output ONLY the JSON object — no explanation, no markdown, no extra text."""


# ──────────────────────────────────────────────────────────────────────────────
# Inference
# ──────────────────────────────────────────────────────────────────────────────

def predict(text: str) -> dict[str, Any]:
    """
    Classify the sentiment of the given text using Groq (Llama 3).

    Returns:
        dict with keys:
          - sentiment (str): 'Positive', 'Neutral', or 'Negative'
          - confidence (float): confidence score in [0, 1]
    """
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Text: {text}"},
        ],
        "temperature": 0.0,
        "max_tokens": 60,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Groq API request timed out.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Groq API error {e.response.status_code}: {e.response.text}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Groq API connection error: {e}") from e

    raw_text: str = (
        response.json()["choices"][0]["message"]["content"].strip()
    )
    logger.info("Groq raw response: %s", raw_text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Non-JSON response from Groq: {raw_text!r}") from e

    sentiment  = str(result.get("sentiment", "Neutral")).capitalize()
    confidence = round(float(result.get("confidence", 0.0)), 4)

    if sentiment not in ("Positive", "Negative", "Neutral"):
        sentiment = "Neutral"

    logger.info("Prediction: %s (%.4f) for text: %.60r", sentiment, confidence, text)
    return {"sentiment": sentiment, "confidence": confidence}
