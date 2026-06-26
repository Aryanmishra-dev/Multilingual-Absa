from fastapi import APIRouter
import os
from typing import Dict

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, str]:
    # Basic health check
    return {
        "status": "ok",
        "model": "loaded",
        "db": "connected"
    }

@router.get("/info")
async def get_info() -> Dict[str, str]:
    return {
        "model_name": "xlm-roberta-base-absa",
        "version": "1.0",
        "supported_languages": "en, hi",
        "max_batch_size": os.getenv("MAX_BATCH_SIZE", "10000")
    }
