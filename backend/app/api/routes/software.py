from __future__ import annotations

import csv
import io
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, distinct, func
from sqlalchemy.orm import Session

from app.core.auth import require_admin, require_read
from app.db.models import Endpoint, EndpointSnapshot, InstalledSoftware
from app.db.models.software import EndpointSoftwareFinding, SoftwareComplianceRule
from app.db.session import get_db
from app.schemas.software import (
    SoftwareAggregatedItem,
    SoftwareAnalyticsItem,
    SoftwareAnalyticsResponse,
    SoftwareCatalogItem,
    SoftwareComplianceEndpointFindingItem,
    SoftwareComplianceEndpointFindingListResponse,
    SoftwareComplianceProfileSummary,
    SoftwareComplianceRuleOut,
    SoftwareComplianceSummaryResponse,
    SoftwareEndpointInstallItem,
    SoftwareEndpointInstallListResponse,
    SoftwareListResponse,
    SoftwareSettingsRuleCreate,
    SoftwareVersionItem,
    SoftwareVersionListResponse,
)
from app.services.compliance_service import reevaluate_current_snapshots
from app.services.software_normalization_service import normalize_name

router = APIRouter(prefix="/software", tags=["software"])


def _current_software_query(db: Session):
    return (
        db.query(InstalledSoftware)
        .join(EndpointSnapshot, EndpointSnapshot.id == InstalledSoftware.snapshot_id)
        .filter(
            EndpointSnapshot.is_current == True,  # noqa: E712
            InstalledSoftware.is_current == True,  # noqa: E712
        )
    )


def _csv_response(content: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _simplify_publisher(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    # Handles distinguished-name style values such as:
    # CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, ...
    if "=" in value and "," in value:
        parts = [part.strip() for part in value.split(",")]
        mapping: dict[str, str] = {}
        for part in parts:
            key, _, part_value = part.partition("=")
            if key and part_value:
                mapping[key.strip().upper()] = part_value.strip()
        if mapping.get("O"):
            return mapping["O"]
        if mapping.get("CN"):
            return mapping["CN"]
    return value


@router.get("/catalog", response_model=list[SoftwareCatalogItem])
def list_software_catalog(
    db: Session = Depends(get_db),
    search: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    _auth=Depends(require_read),
):
    query = (
        _current_software_query(db)
        .with_entities(
            InstalledSoftware.normalized_name.label("normalized_name"),
            func.max(InstalledSoftware.software_name).label("display_name"),
        )
        .filter(InstalledSoftware.normalized_name.isnot(None))
    )
    if search:
        search_term = search.strip().lower()
        query = query.filter(InstalledSoftware.normalized_name.ilike(f"%{search_term}%"))

    rows = (
        query.group_by(InstalledSoftware.normalized_name)
        .order_by(func.count(InstalledSoftware.id).desc())
        .limit(limit)
        .all()
    )
    return [
        SoftwareCatalogItem(
            normalized_name=row.normalized_name,
            display_name=row.display_name or row.normalized_name,
        )
        for row in rows
    ]


@router.get("/analytics", response_model=SoftwareAnalyticsResponse)
def get_software_analytics(
    db: Session = Depends(get_db),
    _auth=Depends(require_read),
):
    top_software_rows = (
        _current_software_query(db)
        .filter(func.lower(InstalledSoftware.app_source) == "registry")
        .filter(InstalledSoftware.normalized_name.isnot(None))
        .with_entities(
            InstalledSoftware.normalized_name.label("label"),
            func.count(distinct(InstalledSoftware.endpoint_id)).label("endpoint_count"),
        )
        .group_by(InstalledSoftware.normalized_name)
        .order_by(func.count(distinct(InstalledSoftware.endpoint_id)).desc())
        .limit(10)
        .all()
    )

    top_publishers_rows = (
        _current_software_query(db)
        .filter(func.lower(InstalledSoftware.app_source) == "registry")
        .filter(InstalledSoftware.normalized_publisher.isnot(None))
        .with_entities(
            InstalledSoftware.normalized_publisher.label("label"),
            func.count(distinct(InstalledSoftware.endpoint_id)).label("endpoint_count"),
        )
        .group_by(InstalledSoftware.normalized_publisher)
        .order_by(func.count(distinct(InstalledSoftware.endpoint_id)).desc())
        .limit(10)
        .all()
    )

    return SoftwareAnalyticsResponse(
        top_software=[
            SoftwareAnalyticsItem(label=row.label, endpoint_count=row.endpoint_count)
            for row in top_software_rows
        ],
        top_publishers=[
            SoftwareAnalyticsItem(label=row.label, endpoint_count=row.endpoint_count)
            for row in top_publishers_rows
        ],
    )


@router.get("/endpoints", response_model=SoftwareEndpointInstallListResponse)
def list_software_endpoints(
    normalized_name: str,
    software_version: str | None = None,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    _auth=Depends(require_read),
):
    normalized = normalize_name(normalized_name)
    if not normalized:
        raise HTTPException(status_code=422, detail="normalized_name is required")

    q = (
        _current_software_query(db)
        .join(Endpoint, Endpoint.id == InstalledSoftware.endpoint_id)
        .filter(InstalledSoftware.normalized_name == normalized)
    )

    if software_version:
        q = q.filter(InstalledSoftware.software_version == software_version)

    total = q.with_entities(func.count(InstalledSoftware.id)).scalar() or 0

    rows = (
        q.with_entities(
            Endpoint.id.label("endpoint_id"),
            Endpoint.computer_name.label("computer_name"),
            InstalledSoftware.software_name.label("software_name"),
            InstalledSoftware.software_version.label("software_version"),
            InstalledSoftware.publisher.label("publisher"),
            InstalledSoftware.app_type.label("app_type"),
            InstalledSoftware.app_source.label("app_source"),
        )
        .order_by(Endpoint.computer_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SoftwareEndpointInstallListResponse(
        items=[
            SoftwareEndpointInstallItem(
                endpoint_id=row.endpoint_id,
                computer_name=row.computer_name,
                software_name=row.software_name,
                software_version=row.software_version,
                publisher=_simplify_publisher(row.publisher),
                app_type=row.app_type,
                app_source=row.app_source,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/endpoints/export")
def export_software_endpoints_csv(
    normalized_name: str,
    software_version: str | None = None,
    db: Session = Depends(get_db),
    _auth=Depends(require_read),
):
    payload = list_software_endpoints(
        normalized_name=normalized_name,
        software_version=software_version,
        db=db,
        page=1,
        page_size=1000000,
    )

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["endpoint_name", "application_name", "application_version", "publisher", "app_type", "app_source"])
    for row in payload.items:
        writer.writerow(
            [
                row.computer_name,
                row.software_name or normalized_name,
                row.software_version or "",
                _simplify_publisher(row.publisher) or "",
                row.app_type or "",
                row.app_source or "",
            ]
        )

    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", normalized_name)[:80] or "software"
    suffix = f"_{software_version}" if software_version else ""
    return _csv_response(stream.getvalue(), f"software_{safe_name}{suffix}_endpoints.csv")


@router.get("/versions", response_model=SoftwareVersionListResponse)
def list_software_versions(
    normalized_name: str,
    db: Session = Depends(get_db),
    _auth=Depends(require_read),
):
    normalized = normalize_name(normalized_name)
    if not normalized:
        raise HTTPException(status_code=422, detail="normalized_name is required")

    q = (
        _current_software_query(db)
        .filter(InstalledSoftware.normalized_name == normalized)
        .with_entities(
            InstalledSoftware.software_version.label("software_version"),
            func.count(distinct(InstalledSoftware.endpoint_id)).label("endpoint_count"),
        )
        .group_by(InstalledSoftware.software_version)
        .order_by(func.count(distinct(InstalledSoftware.endpoint_id)).desc())
    )

    rows = q.all()
    return SoftwareVersionListResponse(
        items=[
            SoftwareVersionItem(
                software_version=row.software_version,
                endpoint_count=row.endpoint_count,
            )
            for row in rows
        ],
        total=len(rows),
    )


@router.get("/settings/profiles", response_model=list[str])
def list_compliance_profiles(db: Session = Depends(get_db), _auth=Depends(require_read)):
    rows = (
        db.query(SoftwareComplianceRule.profile_name)
        .distinct()
        .order_by(SoftwareComplianceRule.profile_name.asc())
        .all()
    )
    profiles = [row.profile_name for row in rows if row.profile_name]
    return profiles or ["Default"]


@router.get("/settings/rules", response_model=list[SoftwareComplianceRuleOut])
def list_compliance_rules(
    db: Session = Depends(get_db),
    profile_name: str | None = None,
    _auth=Depends(require_read),
):
    query = db.query(SoftwareComplianceRule)
    if profile_name:
        query = query.filter(SoftwareComplianceRule.profile_name == profile_name)
    query = query.order_by(SoftwareComplianceRule.profile_name.asc(), SoftwareComplianceRule.name.asc())
    return [SoftwareComplianceRuleOut.model_validate(row) for row in query.all()]


@router.post("/settings/rules", response_model=SoftwareComplianceRuleOut)
def create_compliance_rule(
    payload: SoftwareSettingsRuleCreate,
    db: Session = Depends(get_db),
    _auth=Depends(require_admin),
):
    profile_name = payload.profile_name.strip() or "Default"
    software_name = payload.software_name.strip()
    if not software_name:
        raise HTTPException(status_code=422, detail="software_name is required")

    rule_kind = payload.rule_kind.strip().lower()
    if rule_kind not in ("forbidden", "minimum_version"):
        raise HTTPException(status_code=422, detail="rule_kind must be 'forbidden' or 'minimum_version'")

    if rule_kind == "minimum_version" and not (payload.minimum_version or "").strip():
        raise HTTPException(status_code=422, detail="minimum_version is required for minimum_version rules")

    normalized_name = normalize_name(software_name)
    escaped_pattern = f"^{re.escape(normalized_name)}$"

    base_name = f"{profile_name}:{rule_kind}:{normalized_name}"
    candidate_name = base_name
    suffix = 1
    while db.query(SoftwareComplianceRule).filter(SoftwareComplianceRule.name == candidate_name).first():
        suffix += 1
        candidate_name = f"{base_name}:{suffix}"

    rule = SoftwareComplianceRule(
        name=candidate_name,
        profile_name=profile_name,
        rule_type=rule_kind,
        product_match_pattern=escaped_pattern,
        publisher_match_pattern=None,
        scope="endpoint",
        is_required=rule_kind == "minimum_version",
        is_forbidden=rule_kind == "forbidden",
        minimum_version=(payload.minimum_version or "").strip() or None,
        maximum_version=None,
        severity=payload.severity,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    reevaluate_current_snapshots(db)
    db.commit()
    return SoftwareComplianceRuleOut.model_validate(rule)


@router.delete("/settings/rules/{rule_id}")
def delete_compliance_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _auth=Depends(require_admin),
):
    rule = db.query(SoftwareComplianceRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    reevaluate_current_snapshots(db)
    db.commit()
    return {"deleted": rule_id}


@router.get("/compliance/summary", response_model=SoftwareComplianceSummaryResponse)
def get_software_compliance_summary(
    db: Session = Depends(get_db),
    profile_name: str | None = None,
    _auth=Depends(require_read),
):
    total_endpoints = (
        db.query(func.count(distinct(EndpointSnapshot.endpoint_id)))
        .filter(EndpointSnapshot.is_current == True)  # noqa: E712
        .scalar()
        or 0
    )

    rules_by_profile_rows = (
        db.query(
            SoftwareComplianceRule.profile_name.label("profile_name"),
            func.sum(case((SoftwareComplianceRule.is_forbidden == True, 1), else_=0)).label("forbidden_rules"),  # noqa: E712
            func.sum(case((SoftwareComplianceRule.is_required == True, 1), else_=0)).label("required_rules"),  # noqa: E712
        )
        .group_by(SoftwareComplianceRule.profile_name)
        .all()
    )
    rules_by_profile = {
        row.profile_name: {
            "forbidden_rules": int(row.forbidden_rules or 0),
            "required_rules": int(row.required_rules or 0),
        }
        for row in rules_by_profile_rows
    }

    profiles_query = db.query(SoftwareComplianceRule.profile_name).distinct()
    if profile_name:
        profiles_query = profiles_query.filter(SoftwareComplianceRule.profile_name == profile_name)
    profile_names = [row.profile_name for row in profiles_query.order_by(SoftwareComplianceRule.profile_name.asc()).all()]

    findings_base = (
        db.query(EndpointSoftwareFinding)
        .join(EndpointSnapshot, EndpointSnapshot.id == EndpointSoftwareFinding.snapshot_id)
        .filter(
            EndpointSnapshot.is_current == True,  # noqa: E712
            EndpointSoftwareFinding.status == "open",
        )
    )

    items: list[SoftwareComplianceProfileSummary] = []
    for current_profile in profile_names:
        by_profile = findings_base.filter(EndpointSoftwareFinding.profile_name == current_profile)
        forbidden_endpoints = (
            by_profile.filter(EndpointSoftwareFinding.finding_type == "forbidden_software")
            .with_entities(func.count(distinct(EndpointSoftwareFinding.endpoint_id)))
            .scalar()
            or 0
        )
        minimum_version_endpoints = (
            by_profile.filter(
                EndpointSoftwareFinding.finding_type.in_(["missing_required", "minimum_version_not_met"])
            )
            .with_entities(func.count(distinct(EndpointSoftwareFinding.endpoint_id)))
            .scalar()
            or 0
        )

        profile_rules = rules_by_profile.get(current_profile, {"forbidden_rules": 0, "required_rules": 0})
        if profile_rules["forbidden_rules"] > 0 and profile_rules["required_rules"] > 0:
            list_type = "mixed"
            non_compliant_endpoints = (
                by_profile.with_entities(func.count(distinct(EndpointSoftwareFinding.endpoint_id))).scalar() or 0
            )
        elif profile_rules["forbidden_rules"] > 0:
            list_type = "blacklist"
            non_compliant_endpoints = forbidden_endpoints
        else:
            list_type = "compliance_list"
            non_compliant_endpoints = minimum_version_endpoints

        items.append(
            SoftwareComplianceProfileSummary(
                profile_name=current_profile,
                list_type=list_type,
                total_endpoints=total_endpoints,
                compliant_endpoints=max(total_endpoints - non_compliant_endpoints, 0),
                non_compliant_endpoints=non_compliant_endpoints,
                forbidden_endpoints=forbidden_endpoints,
                minimum_version_endpoints=minimum_version_endpoints,
            )
        )

    return SoftwareComplianceSummaryResponse(items=items)


@router.get("/compliance/endpoints", response_model=SoftwareComplianceEndpointFindingListResponse)
def get_software_compliance_endpoints(
    profile_name: str,
    mode: str = Query("all", description="all | forbidden | minimum_version"),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    _auth=Depends(require_read),
):
    mode_normalized = mode.strip().lower()
    if mode_normalized not in ("all", "forbidden", "minimum_version"):
        raise HTTPException(status_code=422, detail="mode must be all, forbidden, or minimum_version")

    q = (
        db.query(EndpointSoftwareFinding, Endpoint.computer_name)
        .join(EndpointSnapshot, EndpointSnapshot.id == EndpointSoftwareFinding.snapshot_id)
        .join(Endpoint, Endpoint.id == EndpointSoftwareFinding.endpoint_id)
        .filter(
            EndpointSnapshot.is_current == True,  # noqa: E712
            EndpointSoftwareFinding.status == "open",
            EndpointSoftwareFinding.profile_name == profile_name,
        )
    )

    if mode_normalized == "forbidden":
        q = q.filter(EndpointSoftwareFinding.finding_type == "forbidden_software")
    elif mode_normalized == "minimum_version":
        q = q.filter(EndpointSoftwareFinding.finding_type.in_(["missing_required", "minimum_version_not_met"]))

    total = q.with_entities(func.count(EndpointSoftwareFinding.id)).scalar() or 0
    rows = (
        q.order_by(Endpoint.computer_name.asc(), EndpointSoftwareFinding.detected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SoftwareComplianceEndpointFindingListResponse(
        items=[
            SoftwareComplianceEndpointFindingItem(
                endpoint_id=finding.endpoint_id,
                computer_name=computer_name,
                profile_name=finding.profile_name,
                finding_type=finding.finding_type,
                severity=finding.severity,
                rule_name=finding.rule_name,
                software_name=finding.software_name,
                software_version=finding.software_version,
                minimum_version=finding.minimum_version,
                details=finding.details,
                detected_at=finding.detected_at,
            )
            for finding, computer_name in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/compliance/endpoints/export")
def export_software_compliance_csv(
    profile_name: str,
    mode: str = Query("all", description="all | forbidden | minimum_version"),
    db: Session = Depends(get_db),
    _auth=Depends(require_read),
):
    payload = get_software_compliance_endpoints(
        profile_name=profile_name,
        mode=mode,
        db=db,
        page=1,
        page_size=1000000,
    )
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "endpoint_name",
            "profile_name",
            "finding_type",
            "rule_name",
            "software_name",
            "software_version",
            "minimum_version",
            "severity",
            "details",
        ]
    )
    for row in payload.items:
        writer.writerow(
            [
                row.computer_name,
                row.profile_name or "",
                row.finding_type,
                row.rule_name or "",
                row.software_name or "",
                row.software_version or "",
                row.minimum_version or "",
                row.severity,
                row.details or "",
            ]
        )
    safe_profile = re.sub(r"[^a-zA-Z0-9_-]+", "_", profile_name)[:80] or "default"
    return _csv_response(stream.getvalue(), f"software_compliance_{safe_profile}_{mode}.csv")


@router.get("", response_model=SoftwareListResponse)
def list_software(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    app_source: Optional[str] = None,
    publisher: Optional[str] = None,
    app_type: Optional[str] = None,
    hide_system: bool = False,
    hide_framework: bool = False,
    search: Optional[str] = None,
    _auth=Depends(require_read),
):
    q = (
        _current_software_query(db)
        .with_entities(
            InstalledSoftware.normalized_name,
            InstalledSoftware.normalized_publisher,
            InstalledSoftware.app_type,
            InstalledSoftware.app_source,
            func.count(distinct(InstalledSoftware.endpoint_id)).label("endpoint_count"),
            func.count(distinct(InstalledSoftware.software_version)).label("version_count"),
            func.max(InstalledSoftware.software_version).label("latest_version"),
        )
    )

    if app_source:
        q = q.filter(InstalledSoftware.app_source == app_source)
    if publisher:
        q = q.filter(InstalledSoftware.normalized_publisher.ilike(f"%{publisher.lower()}%"))
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
            normalized_name=row.normalized_name,
            display_name=row.normalized_name,
            publisher=row.normalized_publisher,
            version_count=row.version_count,
            endpoint_count=row.endpoint_count,
            latest_version=row.latest_version,
            app_type=row.app_type,
            app_source=row.app_source,
        )
        for row in rows
    ]
    return SoftwareListResponse(items=items, total=total, page=page, page_size=page_size)
