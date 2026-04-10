from app.db.session import SessionLocal
from app.db.models.datasource import DataSource
from app.services.inventory_ingestion_service import run_sync
from app.services.windows_update_evaluation_service import evaluate_all_updates as _evaluate
from app.core.logging import logger


async def sync_all_active_sources() -> None:
    db = SessionLocal()
    try:
        sources = db.query(DataSource).filter_by(is_active=True).all()

        total_processed = 0

        for source in sources:
            try:
                logger.info(f"Syncing data source: {source.name}")
                result = run_sync(db, source)
                logger.info(f"Sync complete for {source.name}: {result}")
                total_processed += result.get("processed", 0)
            except Exception:
                logger.exception(f"Sync failed for {source.name}")

        if total_processed > 0:
            logger.info("Starting Windows update evaluation after inventory sync job")
            eval_result = _evaluate(db)
            logger.info(f"Update evaluation done after inventory sync job: {eval_result}")
    finally:
        db.close()
        