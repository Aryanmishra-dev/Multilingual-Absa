from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi.staticfiles import StaticFiles  # Phase 2: serves api/app/static/
from pathlib import Path                      # Phase 2: resolve static directory path

load_dotenv()

from api.app.routes import predict, results  # noqa: E402
from api.app.routes import pages             # noqa: E402  Phase 2: Jinja2 page routes
from api.app.middleware.metrics import instrumentator  # noqa: E402
from api.app.services.absa_pipeline import pipeline  # noqa: E402
from api.app.schemas.db_models import Base  # noqa: E402
from api.app.middleware.dependencies import engine  # noqa: E402


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
    lifespan=lifespan,
)



app.include_router(predict.router, tags=["Predict"])
app.include_router(results.router, tags=["System"])

instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Jinja2 / HTMX frontend routing and static files
# Note: StaticFiles is mounted after instrumentator so prometheus
# ignores it for /metrics, although this might still log /static requests.

app.include_router(pages.router)  # include_in_schema=False is set on the router itself

# Resolve path relative to this file so it works regardless of CWD.
_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)  # idempotent safety guard
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
