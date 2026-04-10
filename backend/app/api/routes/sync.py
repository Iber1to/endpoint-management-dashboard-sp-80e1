from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_operator, require_read
from app.db.models.datasource import DataSource, InventoryFile
from app.db.session import get_db
from app.schemas.sync import (
    InventoryFileOut,
    SyncExecutionOut,
    SyncRunResponse,
    SyncStatusResponse,
)
from app.services.sync_execution_service import get_active_run, list_runs, start_sync_run

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/run", response_model=SyncRunResponse)
def run_sync_now(
    data_source_id: int | None = None,
    _auth=Depends(require_operator),
):
    run, error_message, retry_after_seconds = start_sync_run(data_source_id=data_source_id)
    if run:
        return SyncRunResponse(
            accepted=True,
            run_id=run["run_id"],
            status=run["status"],
            message="Sync execution started",
        )

    if retry_after_seconds is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": error_message,
                "retry_after_seconds": retry_after_seconds,
            },
        )

    if error_message == "A sync execution is already in progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_message)

    if error_message == "No active data sources found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message or "Unable to start sync")


@router.get("/runs/current", response_model=SyncExecutionOut | None)
def get_current_sync_run(_auth=Depends(require_read)):
    run = get_active_run()
    return SyncExecutionOut.model_validate(run) if run else None


@router.get("/runs", response_model=list[SyncExecutionOut])
def get_sync_runs(
    limit: int = Query(10, ge=1, le=50),
    _auth=Depends(require_read),
):
    return [SyncExecutionOut.model_validate(r) for r in list_runs(limit=limit)]


@router.get("/status", response_model=list[SyncStatusResponse])
def get_sync_status(db: Session = Depends(get_db), _auth=Depends(require_read)):
    sources = db.query(DataSource).all()
    return [
        SyncStatusResponse(
            data_source_id=s.id,
            name=s.name,
            last_sync_at=s.last_sync_at,
            last_sync_status=s.last_sync_status,
            last_error=s.last_error,
        )
        for s in sources
    ]


@router.get("/files", response_model=list[InventoryFileOut])
def list_inventory_files(
    db: Session = Depends(get_db),
    data_source_id: int | None = None,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    _auth=Depends(require_read),
):
    q = db.query(InventoryFile)
    if data_source_id:
        q = q.filter_by(data_source_id=data_source_id)
    if status:
        q = q.filter_by(status=status)
    q = q.order_by(InventoryFile.blob_last_modified.desc()).limit(limit)
    return [InventoryFileOut.model_validate(f) for f in q.all()]
