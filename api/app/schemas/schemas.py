from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ReviewInput(BaseModel):
    text: str
    language: Optional[str] = None

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
