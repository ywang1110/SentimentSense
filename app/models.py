"""
Pydantic data model definitions
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class SentimentRequest(BaseModel):
    """Single text sentiment analysis request model"""
    text: str = Field(..., min_length=1, max_length=512, description="Text to analyze")

    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()


class BatchSentimentRequest(BaseModel):
    """Batch text sentiment analysis request model"""
    texts: List[str] = Field(..., min_items=1, max_items=10, description="List of texts to analyze")

    @validator('texts')
    def validate_texts(cls, v):
        if not v:
            raise ValueError('Text list cannot be empty')

        validated_texts = []
        for text in v:
            if not text.strip():
                raise ValueError('Text cannot be empty')
            if len(text) > 512:
                raise ValueError('Single text length cannot exceed 512 characters')
            validated_texts.append(text.strip())

        return validated_texts


class SentimentResponse(BaseModel):
    """Sentiment analysis response model"""
    text: str = Field(..., description="Original text")
    sentiment: str = Field(..., description="Sentiment label (POSITIVE/NEGATIVE)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    processing_time: float = Field(..., ge=0.0, description="Processing time (seconds)")


class BatchSentimentResponse(BaseModel):
    """Batch sentiment analysis response model"""
    results: List[SentimentResponse] = Field(..., description="List of analysis results")
    total_count: int = Field(..., ge=0, description="Total number of processed texts")
    total_processing_time: float = Field(..., ge=0.0, description="Total processing time (seconds)")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., ge=0.0, description="Uptime (seconds)")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
