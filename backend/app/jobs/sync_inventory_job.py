from app.core.logging import logger
from app.services.sync_execution_service import start_scheduled_inventory_sync_run


async def sync_all_active_sources() -> None:
    run, error_message = start_scheduled_inventory_sync_run()
    if run:
        logger.info("Scheduled inventory sync execution queued (run_id=%s)", run["run_id"])
        return
    logger.warning("Scheduled inventory sync not started: %s", error_message or "unknown reason")
