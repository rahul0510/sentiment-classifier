# schemas.py
# Pydantic models for request and response validation.
# FastAPI uses these to auto-validate incoming JSON and serialize outgoing JSON.

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Schema for the POST /predict request body."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The input text to analyse for sentiment.",
        examples=["I absolutely love this product, it works great!"],
    )


class PredictResponse(BaseModel):
    """Schema for the POST /predict response body."""
    sentiment: str = Field(
        ...,
        description="Predicted sentiment label: Positive, Negative, or Neutral.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0 and 1.",
    )
