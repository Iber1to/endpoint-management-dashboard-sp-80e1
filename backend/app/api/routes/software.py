from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from app.db.session import get_db
from app.db.models import InstalledSoftware
from app.schemas.software import SoftwareListResponse, SoftwareAggregatedItem, SoftwareComplianceRuleOut, SoftwareComplianceRuleCreate
from app.db.models.software import SoftwareComplianceRule

router = APIRouter(prefix="/software", tags=["software"])


@router.get("", response_model=SoftwareListResponse)
def list_software(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    app_source: Optional[str] = None,
    app_type: Optional[str] = None,
    hide_system: bool = False,
    hide_framework: bool = False,
    search: Optional[str] = None,
):
    q = db.query(
        InstalledSoftware.normalized_name,
        InstalledSoftware.normalized_publisher,
        InstalledSoftware.app_type,
        InstalledSoftware.app_source,
        func.count(distinct(InstalledSoftware.endpoint_id)).label("endpoint_count"),
        func.count(distinct(InstalledSoftware.software_version)).label("version_count"),
        func.max(InstalledSoftware.software_version).label("latest_version"),
    ).filter(InstalledSoftware.is_current == True)  # noqa: E712

    if app_source:
        q = q.filter(InstalledSoftware.app_source == app_source)
    if app_type:
        q = q.filter(InstalledSoftware.app_type == app_type)
    if hide_system:
        q = q.filter(InstalledSoftware.system_component != True)  # noqa: E712
    if hide_framework:
        q = q.filter(InstalledSoftware.is_framework != True)  # noqa: E712
    if search:
        q = q.filter(InstalledSoftware.normalized_name.ilike(f"%{search.lower()}%"))

    q = q.group_by(
        InstalledSoftware.normalized_name,
        InstalledSoftware.normalized_publisher,
        InstalledSoftware.app_type,
        InstalledSoftware.app_source,
    ).order_by(func.count(distinct(InstalledSoftware.endpoint_id)).desc())

    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        SoftwareAggregatedItem(
            normalized_name=r.normalized_name,
            display_name=r.normalized_name,
            publisher=r.normalized_publisher,
            version_count=r.version_count,
            endpoint_count=r.endpoint_count,
            latest_version=r.latest_version,
            app_type=r.app_type,
            app_source=r.app_source,
        )
        for r in rows
    ]
    return SoftwareListResponse(items=items, total=total, page=page, page_size=page_size)
