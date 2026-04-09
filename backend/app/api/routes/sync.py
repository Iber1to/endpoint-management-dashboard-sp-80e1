from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.datasource import DataSource, InventoryFile
from app.schemas.sync import SyncStatusResponse, SyncRunResponse, InventoryFileOut
from app.services.inventory_ingestion_service import run_sync

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
            stats = run_sync(db, source)
            if "error" in stats:
                source_errors.append(f"[{source.name}] {stats['error']}")
            for k in all_stats:
                all_stats[k] += stats.get(k, 0)
        except Exception as e:
            source_errors.append(f"[{source.name}] {e}")

    if source_errors:
        return SyncRunResponse(success=False, stats=all_stats, error="; ".join(source_errors))
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
