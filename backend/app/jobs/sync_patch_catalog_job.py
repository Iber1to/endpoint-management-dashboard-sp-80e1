from app.db.session import SessionLocal
from app.services.windows_patch_catalog_service import sync_patch_catalog as _sync_catalog
from app.services.windows_update_evaluation_service import evaluate_all_updates as _evaluate
from app.core.logging import logger


async def sync_patch_catalog() -> None:
    db = SessionLocal()
    try:
        logger.info("Starting Windows patch catalog sync")
        sync_result = _sync_catalog(db)
        logger.info(f"Patch catalog sync done: {sync_result}")

        logger.info("Starting Windows update evaluation after patch catalog sync")
        eval_result = _evaluate(db)
        logger.info(f"Update evaluation done after patch catalog sync: {eval_result}")
    except Exception:
        logger.exception("Patch catalog sync job failed")
        raise
    finally:
        db.close()