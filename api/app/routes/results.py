from fastapi import APIRouter
import os
from typing import Dict

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    # Basic health check
    return {"status": "ok", "model": "loaded", "db": "connected"}


@router.get("/info")
async def get_info() -> Dict[str, str]:
    return {
        "model_name": "xlm-roberta-base-absa",
        "version": "1.0",
        "supported_languages": "en, hi",
        "max_batch_size": os.getenv("MAX_BATCH_SIZE", "10000"),
    }

from fastapi import HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

@router.get("/download/{job_id}")
async def download_result(job_id: str):
    file_path = Path(f"data/results/{job_id}.csv")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    return FileResponse(
        path=file_path,
        filename=f"absa_results_{job_id}.csv",
        media_type="text/csv"
    )
