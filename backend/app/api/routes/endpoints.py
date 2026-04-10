from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.db.session import get_db
from app.db.models import Endpoint, EndpointSnapshot, EndpointHardware, EndpointSecurity, WindowsUpdateStatus, InstalledSoftware
from app.schemas.endpoint import EndpointListResponse, EndpointListItem, EndpointDetail, HardwareOut, SecurityOut, NetworkAdapterOut, DiskOut
from app.schemas.software import InstalledSoftwareOut
from app.schemas.updates import UpdateStatusOut

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


def _get_current_snapshot(db: Session, endpoint_id: int) -> EndpointSnapshot | None:
    return db.query(EndpointSnapshot).filter_by(endpoint_id=endpoint_id, is_current=True).first()


@router.get("", response_model=EndpointListResponse)
def list_endpoints(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    windows_version: Optional[str] = None,
    patch_status: Optional[str] = None,
):
    current_snapshot_sub = (
        db.query(
            EndpointSnapshot.endpoint_id.label("endpoint_id"),
            func.max(EndpointSnapshot.id).label("snapshot_id"),
        )
        .filter(EndpointSnapshot.is_current == True)  # noqa: E712
        .group_by(EndpointSnapshot.endpoint_id)
        .subquery()
    )
    latest_eval_sub = (
        db.query(
            WindowsUpdateStatus.endpoint_id.label("endpoint_id"),
            func.max(WindowsUpdateStatus.evaluated_at).label("max_eval"),
        )
        .group_by(WindowsUpdateStatus.endpoint_id)
        .subquery()
    )
    q = (
        db.query(
            Endpoint,
            EndpointHardware.os_name,
            EndpointHardware.windows_version,
            EndpointHardware.full_build,
            EndpointSecurity.bitlocker_protection_status,
            EndpointSecurity.tpm_present,
            WindowsUpdateStatus.compliance_status,
        )
        .outerjoin(current_snapshot_sub, current_snapshot_sub.c.endpoint_id == Endpoint.id)
        .outerjoin(EndpointSnapshot, EndpointSnapshot.id == current_snapshot_sub.c.snapshot_id)
        .outerjoin(EndpointHardware, EndpointHardware.snapshot_id == EndpointSnapshot.id)
        .outerjoin(EndpointSecurity, EndpointSecurity.snapshot_id == EndpointSnapshot.id)
        .outerjoin(latest_eval_sub, latest_eval_sub.c.endpoint_id == Endpoint.id)
        .outerjoin(
            WindowsUpdateStatus,
            (WindowsUpdateStatus.endpoint_id == latest_eval_sub.c.endpoint_id)
            & (WindowsUpdateStatus.evaluated_at == latest_eval_sub.c.max_eval),
        )
    )
    if search:
        q = q.filter(Endpoint.computer_name.ilike(f"%{search}%"))
    if manufacturer:
        q = q.filter(Endpoint.manufacturer.ilike(f"%{manufacturer}%"))
    if model:
        q = q.filter(Endpoint.model.ilike(f"%{model}%"))
    if windows_version:
        q = q.filter(EndpointHardware.windows_version == windows_version)
    if patch_status:
        q = q.filter(WindowsUpdateStatus.compliance_status == patch_status)

    total = q.with_entities(func.count(func.distinct(Endpoint.id))).scalar() or 0
    endpoints_page = q.order_by(Endpoint.computer_name.asc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for ep, os_name, endpoint_windows_version, full_build, bitlocker_status, tpm_present, compliance_status in endpoints_page:
        items.append(EndpointListItem(
            id=ep.id,
            computer_name=ep.computer_name,
            manufacturer=ep.manufacturer,
            model=ep.model,
            os_name=os_name,
            windows_version=endpoint_windows_version,
            full_build=full_build,
            last_seen_at=ep.last_seen_at,
            bitlocker_protection_status=bitlocker_status,
            tpm_present=tpm_present,
            patch_compliance_status=compliance_status,
        ))

    return EndpointListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{endpoint_id}", response_model=EndpointDetail)
def get_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    ep = db.query(Endpoint).filter_by(id=endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    snap = _get_current_snapshot(db, ep.id)
    hw = snap.hardware if snap else None
    sec = snap.security if snap else None
    network_adapters = snap.network_adapters if snap else []
    disks = snap.disks if snap else []
    software_count = db.query(InstalledSoftware).filter_by(snapshot_id=snap.id, is_current=True).count() if snap else 0
    update_status = db.query(WindowsUpdateStatus).filter_by(endpoint_id=ep.id).order_by(WindowsUpdateStatus.evaluated_at.desc()).first()

    return EndpointDetail(
        id=ep.id,
        computer_name=ep.computer_name,
        manufacturer=ep.manufacturer,
        model=ep.model,
        serial_number=ep.serial_number,
        smbios_uuid=ep.smbios_uuid,
        firmware_type=ep.firmware_type,
        bios_version=ep.bios_version,
        last_seen_at=ep.last_seen_at,
        hardware=HardwareOut.model_validate(hw) if hw else None,
        security=SecurityOut.model_validate(sec) if sec else None,
        network_adapters=[NetworkAdapterOut.model_validate(na) for na in network_adapters],
        disks=[DiskOut.model_validate(d) for d in disks],
        software_count=software_count,
        patch_compliance_status=update_status.compliance_status if update_status else None,
    )


@router.get("/{endpoint_id}/software", response_model=list[InstalledSoftwareOut])
def get_endpoint_software(
    endpoint_id: int,
    db: Session = Depends(get_db),
    app_source: Optional[str] = None,
    app_type: Optional[str] = None,
    hide_system: bool = False,
):
    ep = db.query(Endpoint).filter_by(id=endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    snap = _get_current_snapshot(db, ep.id)
    if not snap:
        return []

    q = db.query(InstalledSoftware).filter_by(snapshot_id=snap.id, is_current=True)
    if app_source:
        q = q.filter_by(app_source=app_source)
    if app_type:
        q = q.filter_by(app_type=app_type)
    if hide_system:
        q = q.filter(InstalledSoftware.system_component != True)  # noqa: E712

    return [InstalledSoftwareOut.model_validate(s) for s in q.all()]


@router.get("/{endpoint_id}/updates", response_model=list[UpdateStatusOut])
def get_endpoint_updates(endpoint_id: int, db: Session = Depends(get_db)):
    ep = db.query(Endpoint).filter_by(id=endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    statuses = db.query(WindowsUpdateStatus).filter_by(endpoint_id=ep.id).order_by(WindowsUpdateStatus.evaluated_at.desc()).all()
    result = []
    for s in statuses:
        result.append(UpdateStatusOut(
            endpoint_id=s.endpoint_id,
            computer_name=ep.computer_name,
            windows_version=s.windows_version,
            full_build=s.full_build,
            kb_article=s.kb_article,
            patch_month=s.patch_month,
            patch_label=s.patch_label,
            compliance_status=s.compliance_status,
            months_behind=s.months_behind,
            inferred=s.inferred,
            evaluated_at=s.evaluated_at,
        ))
    return result


@router.get("/{endpoint_id}/history")
def get_endpoint_history(endpoint_id: int, db: Session = Depends(get_db)):
    ep = db.query(Endpoint).filter_by(id=endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    snapshots = db.query(EndpointSnapshot).filter_by(endpoint_id=ep.id).order_by(EndpointSnapshot.snapshot_at.desc()).all()
    return [{"id": s.id, "snapshot_at": s.snapshot_at, "is_current": s.is_current, "registry_date": s.registry_date} for s in snapshots]
