from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.base import Base
from app.db.session import engine
import app.db.models  # noqa: F401
from app.api.routes import endpoints, software, updates, settings as settings_routes, sync, rules, overview


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Endpoint Management Dashboard API")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Could not auto-create tables (run alembic instead): {e}")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Endpoint Management Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(endpoints.router, prefix="/api")
app.include_router(software.router, prefix="/api")
app.include_router(updates.router, prefix="/api")
app.include_router(settings_routes.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(rules.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
