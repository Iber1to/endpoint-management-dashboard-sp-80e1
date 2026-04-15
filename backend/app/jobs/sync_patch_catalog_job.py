from app.core.logging import logger
from app.services.sync_execution_service import execute_patch_catalog_run


async def sync_patch_catalog() -> None:
    try:
        logger.info("Starting scheduled tracked patch catalog sync")
        run = execute_patch_catalog_run(trigger="scheduler")
        logger.info("Scheduled patch catalog sync finished (run_id=%s, status=%s)", run["run_id"], run["status"])
    except Exception:
        logger.exception("Patch catalog sync job failed")
        raise
