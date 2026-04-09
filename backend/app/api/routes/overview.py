from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.db.models import Endpoint, EndpointSecurity, EndpointHardware, EndpointSnapshot, WindowsUpdateStatus

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("")
def get_overview(db: Session = Depends(get_db)):
    total_endpoints = db.query(Endpoint).count()

    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent_endpoints = db.query(Endpoint).filter(Endpoint.last_seen_at >= recent_cutoff).count()

    by_manufacturer = db.query(
        Endpoint.manufacturer, func.count().label("count")
    ).group_by(Endpoint.manufacturer).order_by(func.count().desc()).all()

    current_snapshots = db.query(EndpointSnapshot.id).filter_by(is_current=True).subquery()

    by_windows_version = db.query(
        EndpointHardware.windows_version, func.count().label("count")
    ).filter(EndpointHardware.snapshot_id.in_(current_snapshots)).group_by(
        EndpointHardware.windows_version
    ).order_by(func.count().desc()).all()

    total_sec = db.query(func.count(EndpointSecurity.id)).filter(
        EndpointSecurity.snapshot_id.in_(current_snapshots)
    ).scalar() or 0
    bitlocker_active = db.query(func.count(EndpointSecurity.id)).filter(
        EndpointSecurity.snapshot_id.in_(current_snapshots),
        EndpointSecurity.bitlocker_protection_status == 1,
    ).scalar() or 0
    tpm_active = db.query(func.count(EndpointSecurity.id)).filter(
        EndpointSecurity.snapshot_id.in_(current_snapshots),
        EndpointSecurity.tpm_present == True,  # noqa: E712
        EndpointSecurity.tpm_enabled == True,  # noqa: E712
    ).scalar() or 0

    total_updates = db.query(func.count(WindowsUpdateStatus.id)).scalar() or 0
    up_to_date = db.query(func.count(WindowsUpdateStatus.id)).filter(
        WindowsUpdateStatus.compliance_status == "up_to_date"
    ).scalar() or 0
    behind_1 = db.query(func.count(WindowsUpdateStatus.id)).filter(
        WindowsUpdateStatus.compliance_status == "behind_1_month"
    ).scalar() or 0
    behind_2plus = db.query(func.count(WindowsUpdateStatus.id)).filter(
        WindowsUpdateStatus.compliance_status == "behind_2_plus_months"
    ).scalar() or 0

    return {
        "total_endpoints": total_endpoints,
        "recent_endpoints": recent_endpoints,
        "by_manufacturer": [{"manufacturer": r.manufacturer or "Unknown", "count": r.count} for r in by_manufacturer],
        "by_windows_version": [{"windows_version": r.windows_version or "Unknown", "count": r.count} for r in by_windows_version],
        "security": {
            "total": total_sec,
            "bitlocker_active": bitlocker_active,
            "bitlocker_pct": round(bitlocker_active / total_sec * 100, 1) if total_sec else 0,
            "tpm_active": tpm_active,
            "tpm_pct": round(tpm_active / total_sec * 100, 1) if total_sec else 0,
        },
        "updates": {
            "total": total_updates,
            "up_to_date": up_to_date,
            "behind_1_month": behind_1,
            "behind_2_plus_months": behind_2plus,
            "up_to_date_pct": round(up_to_date / total_updates * 100, 1) if total_updates else 0,
        },
    }
