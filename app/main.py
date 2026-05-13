# main.py
# FastAPI application entry point.
#
# Responsibilities:
#   - Create the FastAPI app instance
#   - Register CORS middleware
#   - Define the lifespan event that pre-warms the model at startup
#   - Mount all routes

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.model import get_pipeline, predict
from app.schemas import PredictRequest, PredictResponse
from app.utils import setup_logger

logger = setup_logger("main")


# ──────────────────────────────────────────────────────────────────────────────
# Lifespan: pre-warm the model when the server boots
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executed once at startup (before accepting requests) and once at shutdown.
    Pre-loading the model here means the first real request is not penalised
    by a cold-start download delay.
    """
    logger.info("Starting up — pre-warming the sentiment model …")
    get_pipeline()          # warm the lru_cache; model is downloaded if needed
    logger.info("Server ready.")
    yield
    # ── shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down.")


# ──────────────────────────────────────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sentiment Analysis API",
    description=(
        "Analyse the sentiment of a piece of text using the "
        "cardiffnlp/twitter-roberta-base-sentiment model."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────────────────────
# CORS middleware
# Allows the Streamlit frontend (and any browser-based client) to call the API.
# In production, replace allow_origins=["*"] with your real frontend domain.
# ──────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Health-check endpoint — confirms the server is running."""
    return {"status": "ok", "message": "Sentiment Analysis API is running."}


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check — also verifies the model is loaded."""
    return {"status": "ok", "model": "cardiffnlp/twitter-roberta-base-sentiment"}


@app.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
    summary="Predict sentiment for the supplied text.",
)
async def predict_sentiment(request: PredictRequest):
    """
    Analyse the sentiment of the supplied text.

    - **text**: The input string (1–5000 characters).

    Returns a **sentiment** label (Positive / Neutral / Negative) and a
    **confidence** score between 0 and 1.
    """
    try:
        result = predict(request.text)
    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model inference failed: {exc}",
        ) from exc

    return PredictResponse(**result)
