from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "absa_tasks",
    broker=redis_url,
    backend=redis_url.replace("/0", "/1")
)

celery_app.conf.update(
    task_serializer="json",
    result_expires=3600,
)
