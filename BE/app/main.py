# main.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.model import predict, GROQ_MODEL
from app.schemas import PredictRequest, PredictResponse
from app.utils import setup_logger

logger = setup_logger("main")

app = FastAPI(
    title="Sentiment Analysis API",
    description="Classify text sentiment using Llama 3 via Groq API.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Sentiment Analysis API is running (Groq)."}


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "backend": "Groq API",
        "model": GROQ_MODEL,
    }


@app.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
    summary="Predict sentiment for the supplied text.",
)
async def predict_sentiment(request: PredictRequest):
    """Classify text as Positive, Negative, or Neutral using Llama 3 on Groq."""
    try:
        result = predict(request.text)
    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return PredictResponse(**result)
