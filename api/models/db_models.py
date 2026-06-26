from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime, timezone

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processing_time_ms = Column(Float, nullable=False)

class AspectResult(Base):
    __tablename__ = "aspect_results"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(Uuid(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    aspect = Column(String(255), nullable=False)
    sentiment = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    start_pos = Column(Integer, nullable=False)
    end_pos = Column(Integer, nullable=False)

class BatchJob(Base):
    __tablename__ = "batch_jobs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, default="queued")
    total = Column(Integer, nullable=False)
    processed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
