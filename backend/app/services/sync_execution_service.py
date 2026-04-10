from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from app.core.logging import logger
from app.db.models.datasource import DataSource
from app.db.session import SessionLocal
from app.services.inventory_ingestion_service import run_sync
from app.services.windows_update_evaluation_service import evaluate_all_updates

MIN_MANUAL_SYNC_INTERVAL = timedelta(hours=8)
_HISTORY_LIMIT = 30

_state_lock = Lock()
_runs: deque[dict[str, Any]] = deque(maxlen=_HISTORY_LIMIT)
_active_run_id: str | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_run_payload(data_source_id: int | None) -> dict[str, Any]:
    return {
        "run_id": uuid4().hex,
        "data_source_id": data_source_id,
        "status": "queued",
        "requested_at": _utcnow(),
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
        "stats": {
            "total": 0,
            "processed": 0,
            "errors": 0,
            "skipped": 0,
            "by_type": {
                "hardware": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
                "software": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
            },
        },
        "sources_total": 0,
        "sources_failed": [],
        "evaluation_failed": False,
        "message": None,
    }


def _copy_run(run: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(run)


def _get_run_ref(run_id: str) -> dict[str, Any] | None:
    for run in _runs:
        if run["run_id"] == run_id:
            return run
    return None


def get_active_run() -> dict[str, Any] | None:
    with _state_lock:
        if not _active_run_id:
            return None
        run = _get_run_ref(_active_run_id)
        return _copy_run(run) if run else None


def list_runs(limit: int = 10) -> list[dict[str, Any]]:
    with _state_lock:
        runs = list(_runs)[-limit:]
        runs.reverse()
        return [_copy_run(r) for r in runs]


def _compute_retry_after_seconds(last_sync_at: datetime) -> int:
    remaining = (last_sync_at + MIN_MANUAL_SYNC_INTERVAL) - _utcnow()
    return max(int(remaining.total_seconds()), 0)


def _find_interval_blocked_sources(sources: list[DataSource]) -> tuple[list[str], int]:
    blocked: list[str] = []
    retry_after = 0
    for source in sources:
        if source.last_sync_at is None:
            continue
        elapsed = _utcnow() - source.last_sync_at
        if elapsed < MIN_MANUAL_SYNC_INTERVAL:
            blocked.append(source.name)
            retry_after = max(retry_after, _compute_retry_after_seconds(source.last_sync_at))
    return blocked, retry_after


def start_sync_run(data_source_id: int | None = None) -> tuple[dict[str, Any] | None, str | None, int | None]:
    global _active_run_id

    with _state_lock:
        if _active_run_id:
            return None, "A sync execution is already in progress", None

        with SessionLocal() as db:
            q = db.query(DataSource).filter_by(is_active=True)
            if data_source_id:
                q = q.filter_by(id=data_source_id)
            sources = q.all()
            if not sources:
                return None, "No active data sources found", None

            blocked_sources, retry_after_seconds = _find_interval_blocked_sources(sources)
            if blocked_sources:
                blocked_list = ", ".join(sorted(blocked_sources))
                return None, f"Minimum interval not reached for: {blocked_list}", retry_after_seconds

        run = _new_run_payload(data_source_id=data_source_id)
        _runs.append(run)
        _active_run_id = run["run_id"]

    worker = Thread(target=_execute_sync_run, args=(run["run_id"],), daemon=True)
    worker.start()
    return _copy_run(run), None, None


def _mark_finished(run: dict[str, Any], status: str, message: str | None = None) -> None:
    now = _utcnow()
    run["status"] = status
    run["finished_at"] = now
    if run["started_at"]:
        run["duration_seconds"] = (now - run["started_at"]).total_seconds()
    if message:
        run["message"] = message


def _execute_sync_run(run_id: str) -> None:
    global _active_run_id

    with _state_lock:
        run = _get_run_ref(run_id)
        if not run:
            return
        run["status"] = "running"
        run["started_at"] = _utcnow()

    try:
        with SessionLocal() as db:
            q = db.query(DataSource).filter_by(is_active=True)
            if run["data_source_id"]:
                q = q.filter_by(id=run["data_source_id"])
            sources = q.all()
            run["sources_total"] = len(sources)

            if not sources:
                with _state_lock:
                    run_ref = _get_run_ref(run_id)
                    if run_ref:
                        _mark_finished(run_ref, "failed", "No active data sources found")
                return

            all_stats = run["stats"]
            failed_sources: list[str] = []

            for source in sources:
                try:
                    logger.info("Syncing source %s (run_id=%s)", source.name, run_id)
                    stats = run_sync(db, source)
                    if "error" in stats:
                        failed_sources.append(source.name)

                    for key in ("total", "processed", "errors", "skipped"):
                        all_stats[key] += int(stats.get(key, 0))

                    by_type = stats.get("by_type", {})
                    for file_type in ("hardware", "software"):
                        t_stats = by_type.get(file_type, {})
                        for key in ("discovered", "processed", "errors", "skipped"):
                            all_stats["by_type"][file_type][key] += int(t_stats.get(key, 0))
                except Exception:
                    logger.exception("Inventory sync failed for source %s (run_id=%s)", source.name, run_id)
                    failed_sources.append(source.name)

            evaluation_failed = False
            if all_stats.get("processed", 0) > 0:
                try:
                    logger.info("Starting update evaluation after inventory sync (run_id=%s)", run_id)
                    evaluate_all_updates(db)
                except Exception:
                    logger.exception("Update evaluation failed after inventory sync (run_id=%s)", run_id)
                    evaluation_failed = True

            with _state_lock:
                run_ref = _get_run_ref(run_id)
                if not run_ref:
                    return
                run_ref["sources_failed"] = sorted(set(failed_sources))
                run_ref["evaluation_failed"] = evaluation_failed
                if failed_sources or evaluation_failed:
                    message_parts: list[str] = []
                    if failed_sources:
                        message_parts.append(f"Sources failed: {', '.join(sorted(set(failed_sources)))}")
                    if evaluation_failed:
                        message_parts.append("Post-sync update evaluation failed")
                    _mark_finished(run_ref, "partial", "; ".join(message_parts))
                else:
                    _mark_finished(run_ref, "success", "Sync execution completed successfully")
    except Exception:
        logger.exception("Sync execution crashed unexpectedly (run_id=%s)", run_id)
        with _state_lock:
            run_ref = _get_run_ref(run_id)
            if run_ref:
                _mark_finished(run_ref, "failed", "Unexpected sync execution failure")
    finally:
        with _state_lock:
            if _active_run_id == run_id:
                _active_run_id = None
