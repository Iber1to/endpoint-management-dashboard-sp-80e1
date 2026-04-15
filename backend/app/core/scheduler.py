from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import logger
from app.db.session import engine

scheduler = AsyncIOScheduler()
_scheduler_lock_conn = None
_scheduler_lock_acquired = False


def _acquire_scheduler_lock() -> bool:
    global _scheduler_lock_conn, _scheduler_lock_acquired

    try:
        conn = engine.connect()
    except Exception:
        logger.exception("Could not connect to database for scheduler lock")
        return False

    if conn.dialect.name != "postgresql":
        logger.warning("PostgreSQL advisory locks are unavailable; scheduler lock is process-local only")
        _scheduler_lock_conn = conn
        _scheduler_lock_acquired = True
        return True

    try:
        locked = conn.execute(
            text("SELECT pg_try_advisory_lock(:lock_key)"),
            {"lock_key": settings.SCHEDULER_LOCK_KEY},
        ).scalar()
    except Exception:
        conn.close()
        logger.exception("Failed to acquire scheduler advisory lock")
        return False

    if not locked:
        conn.close()
        logger.info("Scheduler lock already held by another instance; skipping scheduler startup")
        return False

    _scheduler_lock_conn = conn
    _scheduler_lock_acquired = True
    return True


def _release_scheduler_lock() -> None:
    global _scheduler_lock_conn, _scheduler_lock_acquired

    if _scheduler_lock_conn is None:
        return

    try:
        if _scheduler_lock_conn.dialect.name == "postgresql" and _scheduler_lock_acquired:
            _scheduler_lock_conn.execute(
                text("SELECT pg_advisory_unlock(:lock_key)"),
                {"lock_key": settings.SCHEDULER_LOCK_KEY},
            )
    except Exception:
        logger.exception("Failed to release scheduler advisory lock cleanly")
    finally:
        _scheduler_lock_conn.close()
        _scheduler_lock_conn = None
        _scheduler_lock_acquired = False


def start_scheduler() -> None:
    from app.jobs.sync_patch_catalog_job import sync_patch_catalog
    from app.jobs.sync_inventory_job import sync_all_active_sources
    from app.jobs.evaluate_updates_job import evaluate_all_updates

    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled by configuration")
        return
    if scheduler.running:
        logger.info("Scheduler is already running")
        return
    if not _acquire_scheduler_lock():
        return

    try:
        scheduler.add_job(
            sync_all_active_sources,
            trigger=IntervalTrigger(minutes=settings.INVENTORY_SYNC_INTERVAL_MINUTES),
            id="sync_inventory",
            replace_existing=True,
            misfire_grace_time=300,
        )
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
    except Exception:
        _release_scheduler_lock()
        logger.exception("Scheduler failed to start")
        raise


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _release_scheduler_lock()
