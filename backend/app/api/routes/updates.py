from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.core.auth import require_operator, require_read
from app.db.session import get_db
from app.db.models import WindowsUpdateStatus, WindowsPatchReference, Endpoint
from app.schemas.updates import UpdateComplianceResponse, UpdateComplianceSummary, UpdateStatusOut, PatchReferenceOut
from app.services.sync_execution_service import execute_patch_catalog_run
from app.services.windows_update_evaluation_service import evaluate_all_updates
from app.core.logging import logger

router = APIRouter(prefix="/updates", tags=["updates"])


@router.get("/compliance", response_model=UpdateComplianceResponse)
def get_update_compliance(db: Session = Depends(get_db), _auth=Depends(require_read)):
    statuses = (
        db.query(WindowsUpdateStatus)
        .options(joinedload(WindowsUpdateStatus.endpoint))
        .all()
    )

    summary_counts = {"up_to_date": 0, "behind_1_month": 0, "behind_2_plus_months": 0, "unknown": 0}
    for s in statuses:
        key = s.compliance_status if s.compliance_status in summary_counts else "unknown"
        summary_counts[key] += 1

    latest_patch = db.query(WindowsPatchReference).filter_by(is_latest_for_branch=True, is_preview=False).order_by(
        WindowsPatchReference.release_date.desc()
    ).first()

    items = []
    for s in statuses:
        ep = s.endpoint
        items.append(UpdateStatusOut(
            endpoint_id=s.endpoint_id,
            computer_name=ep.computer_name if ep else str(s.endpoint_id),
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

    return UpdateComplianceResponse(
        target_patch=latest_patch.patch_month if latest_patch else None,
        summary=UpdateComplianceSummary(
            up_to_date=summary_counts["up_to_date"],
            behind_1_month=summary_counts["behind_1_month"],
            behind_2_plus_months=summary_counts["behind_2_plus_months"],
            unknown=summary_counts["unknown"],
            total=len(statuses),
        ),
        items=items,
    )


@router.get("/catalog", response_model=list[PatchReferenceOut])
def get_patch_catalog(
    db: Session = Depends(get_db),
    windows_version: str | None = None,
    latest_only: bool = False,
    _auth=Depends(require_read),
):
    q = db.query(WindowsPatchReference)
    if windows_version:
        q = q.filter_by(windows_version=windows_version)
    if latest_only:
        q = q.filter_by(is_latest_for_branch=True)
    q = q.order_by(WindowsPatchReference.release_date.desc())
    return [PatchReferenceOut.model_validate(r) for r in q.all()]


@router.get("/catalog/status")
def get_catalog_status(db: Session = Depends(get_db), _auth=Depends(require_read)):
    total = db.query(WindowsPatchReference).count()
    latest = db.query(WindowsPatchReference).order_by(WindowsPatchReference.scraped_at.desc()).first()
    return {
        "total_builds": total,
        "last_synced_at": latest.scraped_at if latest else None,
        "catalog_version": latest.catalog_version if latest else None,
    }


@router.post("/catalog/sync")
def trigger_catalog_sync(_auth=Depends(require_operator)):
    try:
        logger.info("Starting tracked manual patch catalog sync")
        sync_run = execute_patch_catalog_run(trigger="manual")

        return {
            "success": True,
            "result": {
                "run_id": sync_run["run_id"],
                "status": sync_run["status"],
                "stats": sync_run["stats"],
                "message": sync_run.get("message"),
            },
        }
    except Exception:
        logger.exception("Patch catalog sync or post-sync evaluation failed")
        raise HTTPException(status_code=500, detail="Patch catalog sync failed")


@router.post("/evaluate")
def trigger_update_evaluation(db: Session = Depends(get_db), _auth=Depends(require_operator)):
    try:
        result = evaluate_all_updates(db)
        return {"success": True, "result": result}
    except Exception:
        logger.exception("Manual update evaluation failed")
        raise HTTPException(status_code=500, detail="Update evaluation failed")


@router.get("/overview")
def get_updates_overview(db: Session = Depends(get_db), _auth=Depends(require_read)):
    total = db.query(WindowsUpdateStatus).count()
    by_status = db.query(
        WindowsUpdateStatus.compliance_status,
        func.count().label("count"),
    ).group_by(WindowsUpdateStatus.compliance_status).all()

    by_build = db.query(
        WindowsUpdateStatus.full_build,
        func.count().label("count"),
    ).group_by(WindowsUpdateStatus.full_build).order_by(func.count().desc()).limit(20).all()

    return {
        "total": total,
        "by_status": [{"status": r.compliance_status, "count": r.count} for r in by_status],
        "by_build": [{"full_build": r.full_build, "count": r.count} for r in by_build],
    }
    
