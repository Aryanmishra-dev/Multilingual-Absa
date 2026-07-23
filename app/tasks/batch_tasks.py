from app.tasks import celery_app
from app.services.absa_pipeline import pipeline
from app.middleware.dependencies import SessionLocal
from app.schemas.db_models import BatchJob, AspectResult, Review
import pandas as pd
import os
import csv
from datetime import datetime, timezone


@celery_app.task(bind=True)
def process_batch(self, job_id: str, file_path: str):
    db = SessionLocal()
    try:
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # Load CSV
        df = pd.read_csv(file_path)
        if "text" not in df.columns:
            raise ValueError("CSV must contain a 'text' column.")

        texts = df["text"].tolist()
        batch_size = 32

        results_dir = "data/results"
        os.makedirs(results_dir, exist_ok=True)
        result_file = f"{results_dir}/{job_id}.csv"

        processed_count = 0

        with open(result_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "text",
                    "language",
                    "aspect",
                    "sentiment",
                    "confidence",
                    "start_pos",
                    "end_pos",
                    "processing_time_ms",
                ]
            )

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                predictions = pipeline.predict_batch(batch_texts)

                for pred in predictions:
                    # Save Review
                    db_review = Review(
                        text=pred.text,
                        language=pred.language,
                        processing_time_ms=pred.processing_time_ms,
                    )
                    db.add(db_review)
                    db.commit()
                    db.refresh(db_review)

                    # Save Aspects & CSV
                    for asp in pred.aspects:
                        db_aspect = AspectResult(
                            review_id=db_review.id,
                            aspect=asp.aspect,
                            sentiment=asp.sentiment,
                            confidence=asp.confidence,
                            start_pos=asp.start,
                            end_pos=asp.end,
                        )
                        db.add(db_aspect)
                        writer.writerow(
                            [
                                pred.text,
                                pred.language,
                                asp.aspect,
                                asp.sentiment,
                                asp.confidence,
                                asp.start,
                                asp.end,
                                pred.processing_time_ms,
                            ]
                        )

                    if not pred.aspects:
                        writer.writerow(
                            [
                                pred.text,
                                pred.language,
                                "",
                                "",
                                "",
                                "",
                                "",
                                pred.processing_time_ms,
                            ]
                        )

                db.commit()
                processed_count += len(batch_texts)

                if processed_count % 100 == 0 or processed_count == len(texts):
                    job.processed = processed_count
                    db.commit()

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception:
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if job:
            job.status = "failed"
            db.commit()
        import logging
        logging.exception("Batch processing failed for job %s", job_id)
    finally:
        # Clean up temp file
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            pass
        db.close()
