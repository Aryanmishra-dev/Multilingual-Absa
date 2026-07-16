from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class ReviewInput(BaseModel):
    text: str = Field(..., max_length=10000, description="Review text to analyze")
    language: Optional[str] = Field(None, max_length=20, description="Language code (en, hi, hinglish, auto)")

    model_config = ConfigDict(from_attributes=True)


class AspectSentiment(BaseModel):
    aspect: str
    sentiment: str
    confidence: float
    start: int
    end: int

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    text: str
    language: str
    detected_language: str
    aspects: List[AspectSentiment]
    processing_time_ms: float

    model_config = ConfigDict(from_attributes=True)


class BatchJobResponse(BaseModel):
    job_id: str
    status: str
    total_reviews: int
    processed: int
    result_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
