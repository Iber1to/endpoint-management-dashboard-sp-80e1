from app.db.session import SessionLocal
from app.services.windows_patch_catalog_service import sync_patch_catalog as _sync_catalog
from app.core.logging import logger


async def sync_patch_catalog() -> None:
    db = SessionLocal()
    try:
        logger.info("Starting Windows patch catalog sync")
        result = _sync_catalog(db)
        logger.info(f"Patch catalog sync done: {result}")
    except Exception as e:
        logger.error(f"Patch catalog sync failed: {e}")
    finally:
        db.close()
