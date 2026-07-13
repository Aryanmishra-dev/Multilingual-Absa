from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
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

# Allow the dashboard (and any origin in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, tags=["Predict"])
app.include_router(results.router, tags=["System"])

instrumentator.instrument(app).expose(app, endpoint="/metrics")

# ── Phase 2: Jinja2 / HTMX frontend ──────────────────────────────────────────
#
# WHY pages router is included AFTER instrumentator:
#   The instrumentator middleware wraps the entire ASGI app; order of
#   router inclusion does not affect which routes get instrumented.  Including
#   the pages router last is simply a readability convention — API routes first.
#
# WHY StaticFiles is mounted AFTER instrumentator:
#   app.mount() creates a sub-application.  Mounting after the instrumentator
#   call means the Prometheus middleware still wraps /static/* requests, but
#   since static files are not hot paths for an ML tool this is acceptable.
#   (Phase 7 cleanup will add /static to excluded_handlers in metrics.py.)

app.include_router(pages.router)  # include_in_schema=False is set on the router itself

# Resolve path relative to this file so it works regardless of CWD.
_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)  # idempotent safety guard
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
