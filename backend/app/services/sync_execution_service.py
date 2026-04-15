from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from sqlalchemy import func

from app.core.logging import logger
from app.db.models import DataSource, EndpointSnapshot, SyncRun
from app.db.session import SessionLocal
from app.services.inventory_ingestion_service import run_sync
from app.services.windows_patch_catalog_service import sync_patch_catalog
from app.services.windows_update_evaluation_service import evaluate_all_updates

MIN_MANUAL_SYNC_INTERVAL = timedelta(hours=8)
SYNC_TYPE_INVENTORY = "inventory"
SYNC_TYPE_PATCH_CATALOG = "patch_catalog"

_state_lock = Lock()
_active_run_ids: dict[str, str] = {}
_incomplete_runs_reconciled = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_stats() -> dict[str, Any]:
    return {
        "total": 0,
        "processed": 0,
        "errors": 0,
        "skipped": 0,
        "snapshots_created": 0,
        "snapshot_id_from": None,
        "snapshot_id_to": None,
        "by_type": {
            "hardware": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
            "software": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
        },
    }


def _normalize_stats(stats: dict[str, Any] | None) -> dict[str, Any]:
    merged = _default_stats()
    if not stats:
        return merged

    for key in ("total", "processed", "errors", "skipped", "snapshots_created"):
        if key in stats:
            merged[key] = int(stats.get(key) or 0)

    merged["snapshot_id_from"] = stats.get("snapshot_id_from")
    merged["snapshot_id_to"] = stats.get("snapshot_id_to")

    by_type = stats.get("by_type") or {}
    for file_type in ("hardware", "software"):
        source = by_type.get(file_type) or {}
        for key in ("discovered", "processed", "errors", "skipped"):
            merged["by_type"][file_type][key] = int(source.get(key) or 0)

    return merged


def _new_run_payload(
    data_source_id: int | None,
    force: bool,
    sync_type: str = SYNC_TYPE_INVENTORY,
) -> dict[str, Any]:
    return {
        "run_id": uuid4().hex,
        "sync_type": sync_type,
        "data_source_id": data_source_id,
        "force": force,
        "status": "queued",
        "requested_at": _utcnow(),
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
        "stats": _default_stats(),
        "sources_total": 0,
        "sources_failed": [],
        "evaluation_failed": False,
        "message": None,
    }


def _copy_run(run: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(run)


def _get_active_run_id(sync_type: str) -> str | None:
    return _active_run_ids.get(sync_type)


def _set_active_run_id(sync_type: str, run_id: str) -> None:
    _active_run_ids[sync_type] = run_id


def _clear_active_run_id(sync_type: str, run_id: str) -> None:
    if _active_run_ids.get(sync_type) == run_id:
        _active_run_ids.pop(sync_type, None)


def _db_row_to_payload(row: SyncRun) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "sync_type": row.sync_type or SYNC_TYPE_INVENTORY,
        "data_source_id": row.data_source_id,
        "force": row.force,
        "status": row.status,
        "requested_at": row.requested_at,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "duration_seconds": row.duration_seconds,
        "stats": _normalize_stats(row.stats_json or {}),
        "sources_total": row.sources_total,
        "sources_failed": list(row.sources_failed_json or []),
        "evaluation_failed": row.evaluation_failed,
        "message": row.message,
    }


def _persist_run_payload(run: dict[str, Any]) -> None:
    with SessionLocal() as db:
        row = db.query(SyncRun).filter_by(run_id=run["run_id"]).first()
        if not row:
            row = SyncRun(run_id=run["run_id"])
            db.add(row)

        row.sync_type = run.get("sync_type") or SYNC_TYPE_INVENTORY
        row.data_source_id = run.get("data_source_id")
        row.force = bool(run.get("force", False))
        row.status = run.get("status") or "queued"
        row.requested_at = run.get("requested_at") or _utcnow()
        row.started_at = run.get("started_at")
        row.finished_at = run.get("finished_at")
        row.duration_seconds = run.get("duration_seconds")
        row.stats_json = _normalize_stats(run.get("stats") or {})
        row.sources_total = int(run.get("sources_total") or 0)
        row.sources_failed_json = list(run.get("sources_failed") or [])
        row.evaluation_failed = bool(run.get("evaluation_failed", False))
        row.message = run.get("message")
        db.commit()


def _load_run_payload(run_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = db.query(SyncRun).filter_by(run_id=run_id).first()
        return _db_row_to_payload(row) if row else None


def _reconcile_incomplete_runs_once() -> None:
    global _incomplete_runs_reconciled

    with _state_lock:
        if _incomplete_runs_reconciled:
            return
        _incomplete_runs_reconciled = True

    with SessionLocal() as db:
        stale_runs = db.query(SyncRun).filter(SyncRun.status.in_(["queued", "running"])).all()
        if not stale_runs:
            return

        now = _utcnow()
        for run in stale_runs:
            run.status = "failed"
            run.finished_at = now
            if run.started_at:
                run.duration_seconds = max((now - run.started_at).total_seconds(), 0.0)
            run.message = "Sync execution interrupted by backend restart"
        db.commit()


def get_active_run(sync_type: str = SYNC_TYPE_INVENTORY) -> dict[str, Any] | None:
    _reconcile_incomplete_runs_once()

    with SessionLocal() as db:
        active_run_id = _get_active_run_id(sync_type)
        if active_run_id:
            row = db.query(SyncRun).filter_by(run_id=active_run_id).first()
            if row and row.status in ("queued", "running"):
                return _db_row_to_payload(row)

        row = (
            db.query(SyncRun)
            .filter(
                SyncRun.status.in_(["queued", "running"]),
                SyncRun.sync_type == sync_type,
            )
            .order_by(SyncRun.requested_at.desc())
            .first()
        )
        return _db_row_to_payload(row) if row else None


def list_runs(limit: int = 10, sync_type: str | None = None) -> list[dict[str, Any]]:
    _reconcile_incomplete_runs_once()

    with SessionLocal() as db:
        query = db.query(SyncRun)
        if sync_type:
            query = query.filter(SyncRun.sync_type == sync_type)
        rows = query.order_by(SyncRun.requested_at.desc()).limit(limit).all()
        return [_db_row_to_payload(r) for r in rows]


def list_run_types() -> list[str]:
    _reconcile_incomplete_runs_once()

    with SessionLocal() as db:
        rows = (
            db.query(SyncRun.sync_type)
            .filter(SyncRun.sync_type.is_not(None))
            .distinct()
            .all()
        )
    return sorted({r[0] for r in rows if r[0]})


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


def start_sync_run(
    data_source_id: int | None = None,
    force: bool = False,
    enforce_min_interval: bool = True,
) -> tuple[dict[str, Any] | None, str | None, int | None]:
    _reconcile_incomplete_runs_once()

    with _state_lock:
        if _get_active_run_id(SYNC_TYPE_INVENTORY):
            return None, "A sync execution is already in progress", None

        with SessionLocal() as db:
            q = db.query(DataSource).filter_by(is_active=True)
            if data_source_id:
                q = q.filter_by(id=data_source_id)
            sources = q.all()
            if not sources:
                return None, "No active data sources found", None

            if enforce_min_interval and not force:
                blocked_sources, retry_after_seconds = _find_interval_blocked_sources(sources)
                if blocked_sources:
                    blocked_list = ", ".join(sorted(blocked_sources))
                    return None, f"Minimum interval not reached for: {blocked_list}", retry_after_seconds

        run = _new_run_payload(
            data_source_id=data_source_id,
            force=force,
            sync_type=SYNC_TYPE_INVENTORY,
        )
        _persist_run_payload(run)
        _set_active_run_id(SYNC_TYPE_INVENTORY, run["run_id"])

    if force:
        logger.warning("Manual sync guardrail bypass requested (run_id=%s)", run["run_id"])

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
    run = _load_run_payload(run_id)
    if not run:
        with _state_lock:
            _clear_active_run_id(SYNC_TYPE_INVENTORY, run_id)
        return

    run["status"] = "running"
    run["started_at"] = _utcnow()
    _persist_run_payload(run)

    try:
        with SessionLocal() as db:
            q = db.query(DataSource).filter_by(is_active=True)
            if run["data_source_id"]:
                q = q.filter_by(id=run["data_source_id"])
            sources = q.all()
            max_snapshot_before = db.query(func.max(EndpointSnapshot.id)).scalar() or 0
            run["sources_total"] = len(sources)

            if not sources:
                _mark_finished(run, "failed", "No active data sources found")
                _persist_run_payload(run)
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

            max_snapshot_after = db.query(func.max(EndpointSnapshot.id)).scalar() or 0
            snapshots_created = max(max_snapshot_after - max_snapshot_before, 0)
            all_stats["snapshots_created"] = snapshots_created
            all_stats["snapshot_id_from"] = (max_snapshot_before + 1) if snapshots_created > 0 else None
            all_stats["snapshot_id_to"] = max_snapshot_after if snapshots_created > 0 else None

            run["sources_failed"] = sorted(set(failed_sources))
            run["evaluation_failed"] = evaluation_failed
            has_file_errors = int(all_stats.get("errors", 0)) > 0

            if failed_sources or evaluation_failed or has_file_errors:
                message_parts: list[str] = []
                if failed_sources:
                    message_parts.append(f"Sources failed: {', '.join(sorted(set(failed_sources)))}")
                if has_file_errors:
                    message_parts.append(f"{all_stats['errors']} file(s) failed")
                if evaluation_failed:
                    message_parts.append("Post-sync update evaluation failed")
                _mark_finished(run, "partial", "; ".join(message_parts))
            else:
                _mark_finished(run, "success", "Sync execution completed successfully")

            _persist_run_payload(run)
    except Exception:
        logger.exception("Sync execution crashed unexpectedly (run_id=%s)", run_id)
        run = _load_run_payload(run_id) or run
        _mark_finished(run, "failed", "Unexpected sync execution failure")
        _persist_run_payload(run)
    finally:
        with _state_lock:
            _clear_active_run_id(SYNC_TYPE_INVENTORY, run_id)


def start_scheduled_inventory_sync_run() -> tuple[dict[str, Any] | None, str | None]:
    run, error_message, _ = start_sync_run(force=False, enforce_min_interval=False)
    if run:
        return run, None
    return None, error_message


def execute_patch_catalog_run(trigger: str = "manual") -> dict[str, Any]:
    _reconcile_incomplete_runs_once()

    with _state_lock:
        if _get_active_run_id(SYNC_TYPE_PATCH_CATALOG):
            raise RuntimeError("A patch catalog sync execution is already in progress")

        run = _new_run_payload(
            data_source_id=None,
            force=False,
            sync_type=SYNC_TYPE_PATCH_CATALOG,
        )
        run["status"] = "running"
        run["started_at"] = _utcnow()
        run["message"] = f"Patch catalog sync started ({trigger})"
        _persist_run_payload(run)
        _set_active_run_id(SYNC_TYPE_PATCH_CATALOG, run["run_id"])

    try:
        with SessionLocal() as db:
            sync_result = sync_patch_catalog(db)
            synced_entries = int(sync_result.get("synced", 0) or 0)
            sync_error = sync_result.get("error")

            run["sources_total"] = 1
            run["stats"]["total"] = synced_entries
            run["stats"]["processed"] = synced_entries
            run["stats"]["errors"] = 1 if sync_error else 0
            run["stats"]["skipped"] = 0

            evaluation_failed = False
            try:
                evaluate_all_updates(db)
            except Exception:
                logger.exception("Update evaluation failed after patch catalog sync (run_id=%s)", run["run_id"])
                evaluation_failed = True

            run["evaluation_failed"] = evaluation_failed

            if sync_error:
                _mark_finished(run, "partial", f"Patch catalog sync failed: {sync_error}")
            elif evaluation_failed:
                _mark_finished(run, "partial", "Patch catalog synced but post-sync update evaluation failed")
            else:
                _mark_finished(run, "success", "Patch catalog sync completed successfully")
            _persist_run_payload(run)
    except Exception:
        logger.exception("Patch catalog sync execution crashed unexpectedly (run_id=%s)", run["run_id"])
        run = _load_run_payload(run["run_id"]) or run
        _mark_finished(run, "failed", "Unexpected patch catalog sync failure")
        _persist_run_payload(run)
        raise
    finally:
        with _state_lock:
            _clear_active_run_id(SYNC_TYPE_PATCH_CATALOG, run["run_id"])

    return _copy_run(run)
