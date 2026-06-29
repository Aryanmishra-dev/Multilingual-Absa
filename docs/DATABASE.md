# Database Design — Multilingual ABSA

## ER Diagram

```mermaid
erDiagram
    Review {
        uuid id PK
        text text
        string language
        datetime created_at
        float processing_time_ms
    }
    AspectResult {
        uuid id PK
        uuid review_id FK
        string aspect
        string sentiment
        float confidence
        int start_pos
        int end_pos
    }
    BatchJob {
        uuid id PK
        string status
        int total
        int processed
        datetime created_at
        datetime completed_at
    }

    Review ||--o{ AspectResult : "has aspects"
```

## Schema

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    language VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processing_time_ms FLOAT NOT NULL
);

CREATE TABLE aspect_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id),
    aspect VARCHAR(255) NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL
);

CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    total INTEGER NOT NULL,
    processed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

## Recommended Indexes (Production)

```sql
CREATE INDEX idx_aspect_results_review_id ON aspect_results(review_id);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);
CREATE INDEX idx_reviews_language ON reviews(language);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
```

## Connection Configuration

```python
# Development (SQLite)
DATABASE_URL = "sqlite:///absa.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Production (PostgreSQL)
DATABASE_URL = "postgresql://user:pass@host:5432/absa_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

## ORM Models

```python
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
```
