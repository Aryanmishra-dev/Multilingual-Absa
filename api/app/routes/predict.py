from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import os
import uuid
import tempfile
import time

from api.app.schemas.schemas import ReviewInput, PredictionResponse, BatchJobResponse
from api.app.schemas.db_models import Review, AspectResult, BatchJob
from api.app.middleware.dependencies import get_db
from api.app.services.absa_pipeline import pipeline
from api.app.tasks.batch_tasks import process_batch

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: ReviewInput, db: Session = Depends(get_db)):
    try:
        time.time()

        # Inference
        prediction = pipeline.predict(request.text, request.language)

        # Save to DB
        db_review = Review(
            text=prediction.text,
            language=prediction.language,
            processing_time_ms=prediction.processing_time_ms,
        )
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        for asp in prediction.aspects:
            db_aspect = AspectResult(
                review_id=db_review.id,
                aspect=asp.aspect,
                sentiment=asp.sentiment,
                confidence=asp.confidence,
                start_pos=asp.start,
                end_pos=asp.end,
            )
            db.add(db_aspect)
        db.commit()

        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")


@router.post("/batch", response_model=BatchJobResponse)
async def predict_batch(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only CSV files are allowed.")

    try:
        # Create temp file to read
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        df = pd.read_csv(tmp_path)
        if "text" not in df.columns:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=422, detail="CSV must contain a 'text' column."
            )

        if len(df) > 10000:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=422, detail="Max 10,000 rows allowed per batch."
            )

        job_id_obj = uuid.uuid4()
        job_id = str(job_id_obj)
        db_job = BatchJob(id=job_id_obj, status="queued", total=len(df), processed=0)
        db.add(db_job)
        db.commit()

        # Queue Celery task
        process_batch.delay(job_id, tmp_path)

        return BatchJobResponse(
            job_id=job_id, status="queued", total_reviews=len(df), processed=0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch processing failed: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=BatchJobResponse)
async def get_batch_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result_url = None
    if job.status == "completed":
        result_url = f"/results/download/{job_id}"

    return BatchJobResponse(
        job_id=str(job.id),
        status=job.status,
        total_reviews=job.total,
        processed=job.processed,
        result_url=result_url,
    )
