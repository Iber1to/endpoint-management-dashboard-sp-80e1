from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from app.db.models.snapshot import EndpointSnapshot
from app.db.models.software import EndpointSoftwareFinding, InstalledSoftware, SoftwareComplianceRule


def _matches_pattern(pattern: str | None, value: str | None) -> bool:
    if not pattern:
        return True
    if not value:
        return False
    try:
        return bool(re.search(pattern, value, re.IGNORECASE))
    except re.error:
        return pattern.lower() in value.lower()


def _matches_rule(rule: SoftwareComplianceRule, sw: InstalledSoftware) -> bool:
    name_match = _matches_pattern(rule.product_match_pattern, sw.normalized_name or sw.software_name)
    publisher_match = _matches_pattern(rule.publisher_match_pattern, sw.normalized_publisher or sw.publisher)
    return name_match and publisher_match


def _version_key(raw: str | None) -> tuple[int, ...]:
    if not raw:
        return tuple()
    parts = re.findall(r"\d+", raw)
    return tuple(int(part) for part in parts)


def _compare_versions(a: str | None, b: str | None) -> int:
    a_key = _version_key(a)
    b_key = _version_key(b)
    max_len = max(len(a_key), len(b_key))
    padded_a = a_key + (0,) * (max_len - len(a_key))
    padded_b = b_key + (0,) * (max_len - len(b_key))
    if padded_a < padded_b:
        return -1
    if padded_a > padded_b:
        return 1
    return 0


def _profile_name(value: str | None) -> str:
    normalized = (value or "").strip()
    return normalized or "Default"


def _add_finding(
    db: Session,
    *,
    snapshot: EndpointSnapshot,
    rule: SoftwareComplianceRule,
    finding_type: str,
    details: str,
    software_name: str | None = None,
    software_version: str | None = None,
    minimum_version: str | None = None,
) -> None:
    db.add(
        EndpointSoftwareFinding(
            endpoint_id=snapshot.endpoint_id,
            snapshot_id=snapshot.id,
            rule_id=rule.id,
            profile_name=_profile_name(rule.profile_name),
            rule_name=rule.name,
            finding_type=finding_type,
            severity=rule.severity,
            status="open",
            details=details,
            software_name=software_name,
            software_version=software_version,
            minimum_version=minimum_version,
            detected_at=date.today(),
        )
    )


def evaluate_software_compliance(db: Session, snapshot: EndpointSnapshot) -> None:
    rules = db.query(SoftwareComplianceRule).filter_by(is_active=True).all()
    db.query(EndpointSoftwareFinding).filter_by(snapshot_id=snapshot.id).delete()
    if not rules:
        db.flush()
        return

    installed = db.query(InstalledSoftware).filter_by(snapshot_id=snapshot.id, is_current=True).all()

    for rule in rules:
        matches = [sw for sw in installed if _matches_rule(rule, sw)]

        if rule.is_forbidden:
            for sw in matches:
                software_name = sw.software_name or sw.normalized_name or "Unknown software"
                _add_finding(
                    db,
                    snapshot=snapshot,
                    rule=rule,
                    finding_type="forbidden_software",
                    details=f"Forbidden software detected: {software_name}",
                    software_name=sw.software_name or sw.normalized_name,
                    software_version=sw.software_version,
                )

        if rule.is_required:
            if not matches:
                _add_finding(
                    db,
                    snapshot=snapshot,
                    rule=rule,
                    finding_type="missing_required",
                    details=f"Required software missing for rule '{rule.name}'",
                    minimum_version=rule.minimum_version,
                )
                continue

            if rule.minimum_version:
                best_match = max(matches, key=lambda sw: _version_key(sw.software_version))
                if _compare_versions(best_match.software_version, rule.minimum_version) < 0:
                    _add_finding(
                        db,
                        snapshot=snapshot,
                        rule=rule,
                        finding_type="minimum_version_not_met",
                        details=f"Installed version '{best_match.software_version or 'unknown'}' is below required '{rule.minimum_version}'",
                        software_name=best_match.software_name or best_match.normalized_name,
                        software_version=best_match.software_version,
                        minimum_version=rule.minimum_version,
                    )

    db.flush()


def reevaluate_current_snapshots(db: Session) -> int:
    snapshots = db.query(EndpointSnapshot).filter_by(is_current=True).all()
    for snapshot in snapshots:
        evaluate_software_compliance(db, snapshot)
    db.flush()
    return len(snapshots)

