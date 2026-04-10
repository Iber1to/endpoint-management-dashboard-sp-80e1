from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import EndpointSnapshot, EndpointHardware, WindowsPatchReference, WindowsUpdateStatus, Endpoint
from app.core.logging import logger


COMPLIANCE_STATUSES = {
    "up_to_date", "behind_1_month", "behind_2_plus_months",
    "preview_build", "unsupported_branch", "unknown"
}


def _months_diff(patch_month: str, latest_month: str) -> int:
    try:
        pm_year, pm_mon = int(patch_month[:4]), int(patch_month[5:7])
        lm_year, lm_mon = int(latest_month[:4]), int(latest_month[5:7])
        return (lm_year - pm_year) * 12 + (lm_mon - pm_mon)
    except Exception:
        return -1


def evaluate_endpoint_snapshot(db: Session, snapshot: EndpointSnapshot) -> None:
    hw = snapshot.hardware
    if not hw or not hw.os_build:
        return

    full_build = hw.full_build
    if not full_build:
        return

    patch_ref = db.query(WindowsPatchReference).filter_by(full_build=full_build).filter(
        WindowsPatchReference.is_preview == False  # noqa: E712
    ).first()

    inferred = False
    if not patch_ref:
        patch_ref = db.query(WindowsPatchReference).filter(
            WindowsPatchReference.os_build == hw.os_build,
            WindowsPatchReference.os_revision <= (hw.os_revision or 0),
            WindowsPatchReference.is_preview == False,  # noqa: E712
        ).order_by(WindowsPatchReference.os_revision.desc()).first()
        inferred = True

    if not patch_ref:
        compliance_status = "unknown"
        months_behind = None
        kb_article = None
        patch_month = None
        patch_label = None
    else:
        latest_for_branch = db.query(WindowsPatchReference).filter(
            WindowsPatchReference.os_build == hw.os_build,
            WindowsPatchReference.is_latest_for_branch == True,  # noqa: E712
            WindowsPatchReference.is_preview == False,  # noqa: E712
        ).first()

        kb_article = patch_ref.kb_article
        patch_month = patch_ref.patch_month
        patch_label = patch_ref.patch_label

        if latest_for_branch and patch_month and latest_for_branch.patch_month:
            months_behind = _months_diff(patch_month, latest_for_branch.patch_month)
            if months_behind == 0:
                compliance_status = "up_to_date"
            elif months_behind == 1:
                compliance_status = "behind_1_month"
            else:
                compliance_status = "behind_2_plus_months"
        else:
            months_behind = None
            compliance_status = "unknown"

    existing = db.query(WindowsUpdateStatus).filter_by(
        endpoint_id=snapshot.endpoint_id, snapshot_id=snapshot.id
    ).first()

    status_data = {
        "endpoint_id": snapshot.endpoint_id,
        "snapshot_id": snapshot.id,
        "windows_version": hw.windows_version,
        "os_build": hw.os_build,
        "os_revision": hw.os_revision,
        "full_build": full_build,
        "patch_month": patch_month,
        "patch_label": patch_label,
        "kb_article": kb_article,
        "compliance_status": compliance_status,
        "months_behind": months_behind,
        "inferred": inferred,
        "evaluated_at": datetime.now(timezone.utc),
    }

    if existing:
        for k, v in status_data.items():
            setattr(existing, k, v)
    else:
        db.add(WindowsUpdateStatus(**status_data))

    db.flush()


def evaluate_all_updates(db: Session) -> dict:
    snapshots = db.query(EndpointSnapshot).filter_by(is_current=True).all()
    evaluated = 0
    errors = 0

    for snap in snapshots:
        try:
            evaluate_endpoint_snapshot(db, snap)
            evaluated += 1
        except Exception:
            logger.exception(f"Error evaluating snapshot {snap.id}")
            errors += 1

    db.commit()
    return {"evaluated": evaluated, "errors": errors}
