from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import app.db.models  # noqa: F401
from app.api.routes import endpoints, overview, rules, settings as settings_routes, software, sync, updates
from app.core.auth import require_read
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.metrics import METRICS_CONTENT_TYPE, metrics_payload, observe_http_request
from app.core.operational import security_warnings
from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Endpoint Management Dashboard API")
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


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = uuid4().hex
    start_time = perf_counter()
    status_code = 500
    response = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logger.exception(
            "Request failed (request_id=%s, method=%s, path=%s)",
            request_id,
            request.method,
            request.url.path,
        )
        raise
    finally:
        elapsed = perf_counter() - start_time
        route = request.scope.get("route")
        path_label = route.path if route else request.url.path

        observe_http_request(
            method=request.method,
            path=path_label,
            status_code=status_code,
            duration_seconds=elapsed,
        )
        logger.info(
            "Request completed (request_id=%s, method=%s, path=%s, status=%s, duration_ms=%.2f)",
            request_id,
            request.method,
            path_label,
            status_code,
            elapsed * 1000,
        )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


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


@app.get("/health/details")
def health_details(_auth=Depends(require_read)):
    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "security_warnings": security_warnings(),
    }


@app.get("/metrics")
def metrics(_auth=Depends(require_read)):
    return Response(content=metrics_payload(), media_type=METRICS_CONTENT_TYPE)
