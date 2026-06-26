from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from api.routes import predict, results
from api.middleware.metrics import instrumentator
from api.services.absa_pipeline import pipeline
from api.models.db_models import Base
from api.middleware.dependencies import engine

# Create DB tables (if using simple SQLite, otherwise use Alembic)
Base.metadata.create_all(bind=engine)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Loading Models...")
    pipeline.load_models()
    
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Multilingual ABSA API",
    description="Aspect-Based Sentiment Analysis for English and Hindi",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(predict.router, tags=["Predict"])
app.include_router(results.router, tags=["System"])

instrumentator.instrument(app).expose(app, endpoint="/metrics")
