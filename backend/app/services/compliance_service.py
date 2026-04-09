import re
from sqlalchemy.orm import Session
from app.db.models.software import SoftwareComplianceRule, EndpointSoftwareFinding, InstalledSoftware
from app.db.models.snapshot import EndpointSnapshot
from datetime import date


def _matches_pattern(pattern: str | None, value: str | None) -> bool:
    if not pattern or not value:
        return False
    try:
        return bool(re.search(pattern, value, re.IGNORECASE))
    except re.error:
        return pattern.lower() in (value or "").lower()


def evaluate_software_compliance(db: Session, snapshot: EndpointSnapshot) -> None:
    rules = db.query(SoftwareComplianceRule).filter_by(is_active=True).all()
    if not rules:
        return

    installed = db.query(InstalledSoftware).filter_by(snapshot_id=snapshot.id, is_current=True).all()
    today = date.today()

    db.query(EndpointSoftwareFinding).filter_by(snapshot_id=snapshot.id).delete()

    for rule in rules:
        matches = [
            sw for sw in installed
            if _matches_pattern(rule.product_match_pattern, sw.normalized_name)
            or _matches_pattern(rule.publisher_match_pattern, sw.normalized_publisher)
        ]

        if rule.is_required and not matches:
            db.add(EndpointSoftwareFinding(
                endpoint_id=snapshot.endpoint_id,
                snapshot_id=snapshot.id,
                finding_type="missing_required",
                severity=rule.severity,
                status="open",
                details=f"Required software '{rule.name}' not found",
                detected_at=today,
            ))

        for sw in matches:
            if rule.is_forbidden:
                db.add(EndpointSoftwareFinding(
                    endpoint_id=snapshot.endpoint_id,
                    snapshot_id=snapshot.id,
                    finding_type="forbidden_software",
                    severity=rule.severity,
                    status="open",
                    details=f"Forbidden software '{sw.software_name}' detected",
                    detected_at=today,
                ))

    db.flush()
