from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.logging import logger

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    from app.jobs.sync_patch_catalog_job import sync_patch_catalog
    from app.jobs.evaluate_updates_job import evaluate_all_updates
    from app.core.config import settings

    scheduler.add_job(
        sync_patch_catalog,
        trigger=IntervalTrigger(minutes=settings.PATCH_CATALOG_SYNC_INTERVAL_MINUTES),
        id="sync_patch_catalog",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        evaluate_all_updates,
        trigger=IntervalTrigger(minutes=settings.INVENTORY_SYNC_INTERVAL_MINUTES),
        id="evaluate_updates",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
