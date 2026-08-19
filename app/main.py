import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import Base, SessionLocal, engine, get_db

# Create tables on startup. Fine for SQLite/demo purposes; a real Postgres
# deployment would use migrations (e.g. Alembic) instead.
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(settings.APP_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s version=%s", settings.APP_NAME, settings.APP_VERSION)
    yield


app = FastAPI(title="Task Manager API", version=settings.APP_VERSION, lifespan=lifespan)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of HTTP requests currently in progress",
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    # /metrics itself is excluded to avoid the endpoint measuring its own scrape.
    if request.url.path == "/metrics":
        return await call_next(request)

    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    try:
        response = await call_next(request)
    finally:
        ACTIVE_REQUESTS.dec()

    duration = time.time() - start_time
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(
        duration
    )
    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    ).inc()
    return response


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Health / version
# ---------------------------------------------------------------------------
@app.get("/health", response_model=schemas.HealthResponse)
def health():
    # Intentionally does NOT touch the database. Kubernetes liveness/readiness
    # probes should be fast and cheap; a DB-backed check here risks the
    # kubelet restarting a perfectly healthy pod during a transient DB hiccup.
    # If you want a "deep" readiness check later, add a separate endpoint
    # (e.g. /ready) rather than overloading /health.
    return {"status": "healthy"}


@app.get("/version", response_model=schemas.VersionResponse)
def version():
    return {"version": settings.APP_VERSION}


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------
@app.get("/tasks", response_model=list[schemas.TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return crud.get_tasks(db)


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    created = crud.create_task(db, task)
    logger.info("Created task id=%s title=%r", created.id, created.title)
    return created


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = crud.update_task(db, db_task, task_update)
    logger.info("Updated task id=%s", updated.id)
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, db_task)
    logger.info("Deleted task id=%s", task_id)
    return None

