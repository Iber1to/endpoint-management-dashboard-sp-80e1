import re
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import require_admin
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.software import SoftwareComplianceRule
from app.schemas.software import SoftwareComplianceRuleCreate, SoftwareComplianceRuleOut

router = APIRouter(prefix="/rules", tags=["rules"], dependencies=[Depends(require_admin)])


@router.get("/software", response_model=list[SoftwareComplianceRuleOut])
def list_software_rules(db: Session = Depends(get_db)):
    return [SoftwareComplianceRuleOut.model_validate(r) for r in db.query(SoftwareComplianceRule).all()]


@router.post("/software", response_model=SoftwareComplianceRuleOut)
def create_software_rule(payload: SoftwareComplianceRuleCreate, db: Session = Depends(get_db)):
    for field in ("product_match_pattern", "publisher_match_pattern"):
        pattern = getattr(payload, field, None)
        if pattern:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise HTTPException(status_code=422, detail=f"Invalid regex in {field}: {exc}")
    rule = SoftwareComplianceRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return SoftwareComplianceRuleOut.model_validate(rule)


@router.delete("/software/{rule_id}")
def delete_software_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(SoftwareComplianceRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"deleted": rule_id}
