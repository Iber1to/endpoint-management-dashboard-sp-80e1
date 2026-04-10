from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.datasource import DataSource, InventoryFile
from app.schemas.sync import SyncStatusResponse, SyncRunResponse, InventoryFileOut
from app.services.inventory_ingestion_service import run_sync
from app.services.windows_update_evaluation_service import evaluate_all_updates
from app.core.logging import logger

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/run", response_model=SyncRunResponse)
def run_sync_now(db: Session = Depends(get_db), data_source_id: int | None = None):
    q = db.query(DataSource).filter_by(is_active=True)
    if data_source_id:
        q = q.filter_by(id=data_source_id)

    sources = q.all()
    if not sources:
        raise HTTPException(status_code=404, detail="No active data sources found")

    all_stats: dict = {"total": 0, "processed": 0, "errors": 0, "skipped": 0}
    source_errors: list[str] = []

    for source in sources:
        try:
            logger.info(f"Syncing source {source.name}")
            stats = run_sync(db, source)
            if "error" in stats:
                source_errors.append(f"[{source.name}] {stats['error']}")
            for k in all_stats:
                all_stats[k] += stats.get(k, 0)
        except Exception as e:
            logger.exception(f"Inventory sync failed for source {source.name}")
            source_errors.append(f"[{source.name}] {e}")

    evaluation_error = None
    evaluation_ran = False

    if all_stats.get("processed", 0) > 0:
        try:
            logger.info("Starting update evaluation after inventory sync")
            evaluate_all_updates(db)
            evaluation_ran = True
        except Exception as e:
            logger.exception("Update evaluation failed after inventory sync")
            evaluation_error = str(e)

    if source_errors or evaluation_error:
        parts = []
        if source_errors:
            parts.append("; ".join(source_errors))
        if evaluation_error:
            parts.append(f"[evaluation] {evaluation_error}")
        return SyncRunResponse(success=False, stats=all_stats, error="; ".join(parts))

    return SyncRunResponse(success=True, stats=all_stats)


@router.get("/status", response_model=list[SyncStatusResponse])
def get_sync_status(db: Session = Depends(get_db)):
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
    limit: int = 100,
):
    q = db.query(InventoryFile)
    if data_source_id:
        q = q.filter_by(data_source_id=data_source_id)
    if status:
        q = q.filter_by(status=status)
    q = q.order_by(InventoryFile.blob_last_modified.desc()).limit(limit)
    return [InventoryFileOut.model_validate(f) for f in q.all()]