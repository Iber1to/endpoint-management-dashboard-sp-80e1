from app.db.session import SessionLocal
from app.db.models.datasource import DataSource
from app.services.inventory_ingestion_service import run_sync
from app.core.logging import logger


async def sync_all_active_sources() -> None:
    db = SessionLocal()
    try:
        sources = db.query(DataSource).filter_by(is_active=True).all()
        for source in sources:
            try:
                logger.info(f"Syncing data source: {source.name}")
                result = run_sync(db, source)
                logger.info(f"Sync complete for {source.name}: {result}")
            except Exception as e:
                logger.error(f"Sync failed for {source.name}: {e}")
    finally:
        db.close()
