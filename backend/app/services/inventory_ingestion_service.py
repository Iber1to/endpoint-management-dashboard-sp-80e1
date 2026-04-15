from datetime import datetime, timedelta, timezone
from collections import Counter
from sqlalchemy.orm import Session
from app.db.models import (
    Endpoint, EndpointSnapshot, EndpointHardware, EndpointSecurity,
    EndpointNetworkAdapter, EndpointDisk, InstalledSoftware, DataSource, InventoryFile,
)
from app.services.hardware_parser_service import parse_hardware_json
from app.services.software_parser_service import parse_software_json
from app.services.software_normalization_service import (
    normalize_name, normalize_publisher, compute_dedupe_hash, classify_software
)
from app.services.compliance_service import evaluate_software_compliance
from app.services import blob_storage_service as bss
from app.core.security import decrypt_value
from app.core.logging import logger

INCREMENTAL_LOOKBACK_MINUTES = 5


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _compute_incremental_cutoff(last_sync_at: datetime | None) -> datetime | None:
    normalized_last_sync = _to_utc(last_sync_at)
    if normalized_last_sync is None:
        return None
    return normalized_last_sync - timedelta(minutes=INCREMENTAL_LOOKBACK_MINUTES)


def _is_blob_new_for_incremental(blob_last_modified: datetime | None, cutoff: datetime) -> bool:
    normalized_blob_time = _to_utc(blob_last_modified)
    if normalized_blob_time is None:
        return True
    return normalized_blob_time >= cutoff


def _get_or_create_endpoint(db: Session, endpoint_data: dict) -> Endpoint:
    computer_name = endpoint_data["computer_name"]
    endpoint_key = computer_name.upper()
    ep = db.query(Endpoint).filter_by(endpoint_key=endpoint_key).first()
    if not ep:
        ep = Endpoint(endpoint_key=endpoint_key, computer_name=computer_name)
        db.add(ep)
        db.flush()
    for field in ["serial_number", "smbios_uuid", "manufacturer", "model", "system_sku",
                  "firmware_type", "bios_version", "bios_release_date", "install_date"]:
        val = endpoint_data.get(field)
        if val is not None:
            setattr(ep, field, val)
    if endpoint_data.get("last_seen_at"):
        if not ep.last_seen_at or endpoint_data["last_seen_at"] > ep.last_seen_at:
            ep.last_seen_at = endpoint_data["last_seen_at"]
    return ep


def _normalize_endpoint_name(value: str | None) -> str:
    return (value or "").strip()


def _resolve_software_endpoint_name(entries: list[dict]) -> str | None:
    candidates: list[str] = []
    for entry in entries:
        computer_name = _normalize_endpoint_name(entry.get("computer_name"))
        managed_device_name = _normalize_endpoint_name(entry.get("managed_device_name"))
        if computer_name:
            candidates.append(computer_name)
            continue
        if managed_device_name:
            candidates.append(managed_device_name)

    if not candidates:
        return None

    counts = Counter(name.upper() for name in candidates)
    most_common_key, _ = counts.most_common(1)[0]
    for original in candidates:
        if original.upper() == most_common_key:
            return original
    return candidates[0]


def ingest_hardware_file(db: Session, inv_file: InventoryFile, raw: bytes) -> None:
    try:
        parsed = parse_hardware_json(raw)
    except Exception as e:
        _set_inventory_file_error(inv_file, f"Parse error: {e}")
        db.flush()
        return

    ep = _get_or_create_endpoint(db, parsed["endpoint"])
    content_endpoint_name = _normalize_endpoint_name(parsed["endpoint"].get("computer_name"))
    filename_endpoint_name = _normalize_endpoint_name(inv_file.endpoint_name)
    if content_endpoint_name:
        inv_file.endpoint_name = content_endpoint_name
    if filename_endpoint_name and content_endpoint_name and filename_endpoint_name.upper() != content_endpoint_name.upper():
        logger.warning(
            "Endpoint mismatch in hardware file %s: filename=%s content=%s",
            inv_file.blob_name,
            filename_endpoint_name,
            content_endpoint_name,
        )

    snapshot_at = parsed["snapshot_at"] or datetime.now(timezone.utc)
    snapshot = db.query(EndpointSnapshot).filter_by(
        endpoint_id=ep.id, hardware_file_id=inv_file.id
    ).first()
    if not snapshot:
        db.query(EndpointSnapshot).filter_by(endpoint_id=ep.id, is_current=True).update({"is_current": False})
        snapshot = EndpointSnapshot(
            endpoint_id=ep.id,
            snapshot_at=snapshot_at,
            registry_date=parsed["registry_date"],
            hardware_file_id=inv_file.id,
            is_current=True,
        )
        db.add(snapshot)
        db.flush()

    if not db.query(EndpointHardware).filter_by(snapshot_id=snapshot.id).first():
        hw = EndpointHardware(snapshot_id=snapshot.id, **parsed["hardware"])
        db.add(hw)

    if not db.query(EndpointSecurity).filter_by(snapshot_id=snapshot.id).first():
        sec = EndpointSecurity(snapshot_id=snapshot.id, **parsed["security"])
        db.add(sec)

    db.query(EndpointNetworkAdapter).filter_by(snapshot_id=snapshot.id).delete()
    for na_data in parsed["network_adapters"]:
        db.add(EndpointNetworkAdapter(snapshot_id=snapshot.id, **na_data))

    db.query(EndpointDisk).filter_by(snapshot_id=snapshot.id).delete()
    for disk_data in parsed["disks"]:
        db.add(EndpointDisk(snapshot_id=snapshot.id, **disk_data))

    inv_file.status = "processed"
    inv_file.processed_at = datetime.now(timezone.utc)
    db.flush()


def ingest_software_file(db: Session, inv_file: InventoryFile, entries: list[dict], snapshot: EndpointSnapshot) -> None:
    db.query(InstalledSoftware).filter_by(snapshot_id=snapshot.id).delete()

    seen_hashes: set[str] = set()
    for entry in entries:
        classification = classify_software(entry)
        norm_name = normalize_name(entry.get("software_name"))
        norm_pub = normalize_publisher(entry.get("publisher"))
        dedupe_hash = compute_dedupe_hash(snapshot.id, entry.get("software_name"), entry.get("software_version"), entry.get("app_source"))

        if dedupe_hash in seen_hashes:
            continue
        seen_hashes.add(dedupe_hash)

        sw = InstalledSoftware(
            snapshot_id=snapshot.id,
            endpoint_id=snapshot.endpoint_id,
            software_name=entry.get("software_name"),
            software_version=entry.get("software_version"),
            publisher=entry.get("publisher"),
            install_date=entry.get("install_date"),
            architecture=entry.get("architecture"),
            app_type=entry.get("app_type"),
            app_source=entry.get("app_source"),
            app_scope=entry.get("app_scope"),
            managed_device_id=entry.get("managed_device_id"),
            managed_device_name=entry.get("managed_device_name"),
            uninstall_string=entry.get("uninstall_string"),
            uninstall_reg_path=entry.get("uninstall_reg_path"),
            system_component=entry.get("system_component"),
            windows_installer=entry.get("windows_installer"),
            package_full_name=entry.get("package_full_name"),
            package_family_name=entry.get("package_family_name"),
            install_location=entry.get("install_location"),
            is_framework=entry.get("is_framework"),
            is_resource_package=entry.get("is_resource_package"),
            is_bundle=entry.get("is_bundle"),
            is_development_mode=entry.get("is_development_mode"),
            is_non_removable=entry.get("is_non_removable"),
            signature_kind=entry.get("signature_kind"),
            normalized_name=norm_name,
            normalized_publisher=norm_pub,
            dedupe_hash=dedupe_hash,
            is_current=True,
        )
        db.add(sw)

    snapshot.software_file_id = inv_file.id
    evaluate_software_compliance(db, snapshot)
    inv_file.status = "processed"
    inv_file.processed_at = datetime.now(timezone.utc)
    db.flush()


def _set_inventory_file_error(inv_file: InventoryFile, message: str) -> None:
    inv_file.status = "error"
    inv_file.error_message = message
    inv_file.processed_at = datetime.now(timezone.utc)
    logger.warning(
        "Inventory file error (id=%s, blob=%s, endpoint=%s): %s",
        inv_file.id,
        inv_file.blob_name,
        inv_file.endpoint_name,
        message,
    )


def run_sync(db: Session, data_source: DataSource) -> dict:
    try:
        sas_token = decrypt_value(data_source.sas_token_encrypted or "")
    except Exception:
        msg = "SAS token decryption failed (key mismatch or missing encryption key)"
        data_source.last_sync_status = "error"
        data_source.last_error = msg
        db.commit()
        logger.exception("Failed to decrypt SAS token for data source %s", data_source.name)
        return {"error": msg}

    stats = {
        "total": 0,
        "processed": 0,
        "errors": 0,
        "skipped": 0,
        "by_type": {
            "hardware": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
            "software": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
        },
    }

    incremental_cutoff = _compute_incremental_cutoff(data_source.last_sync_at)

    try:
        blobs = bss.list_blobs(
            data_source.account_url,
            sas_token,
            data_source.container_name,
            data_source.blob_prefix or "",
        )
        if incremental_cutoff is not None:
            total_before_incremental = len(blobs)
            blobs = [b for b in blobs if _is_blob_new_for_incremental(b.last_modified, incremental_cutoff)]
            logger.info(
                "Incremental sync for source %s (cutoff=%s): selected %s of %s blobs",
                data_source.name,
                incremental_cutoff.isoformat(),
                len(blobs),
                total_before_incremental,
            )
        if data_source.max_files_per_run_enabled:
            blobs = blobs[: data_source.max_files_per_run]
            logger.info(
                "Sync run file cap enabled for source %s: processing up to %s blobs",
                data_source.name,
                data_source.max_files_per_run,
            )
    except Exception as exc:
        data_source.last_sync_status = "error"
        data_source.last_error = str(exc)
        db.commit()
        logger.exception("Failed to list blobs for data source %s", data_source.name)
        return {"error": "Failed to list blobs from data source"}

    for blob in blobs:
        if blob.file_type not in ("hardware", "software"):
            continue
        stats["total"] += 1
        stats["by_type"][blob.file_type]["discovered"] += 1

        existing = db.query(InventoryFile).filter_by(
            data_source_id=data_source.id, blob_name=blob.name, etag=blob.etag
        ).first()
        if existing and existing.status == "processed":
            stats["skipped"] += 1
            stats["by_type"][blob.file_type]["skipped"] += 1
            continue

        if not existing:
            inv_file = InventoryFile(
                data_source_id=data_source.id,
                blob_name=blob.name,
                file_type=blob.file_type,
                endpoint_name=blob.endpoint_name,
                blob_last_modified=blob.last_modified,
                etag=blob.etag,
                status="pending",
            )
            db.add(inv_file)
            db.flush()
        else:
            inv_file = existing
            inv_file.file_type = blob.file_type
            inv_file.endpoint_name = blob.endpoint_name
            inv_file.blob_last_modified = blob.last_modified

        inv_file.status = "processing"
        inv_file.error_message = None
        inv_file.processed_at = None
        db.commit()

        try:
            raw = bss.download_blob_json(data_source.account_url, sas_token, data_source.container_name, blob.name)
        except Exception as exc:
            _set_inventory_file_error(inv_file, f"Download error: {exc}")
            stats["errors"] += 1
            stats["by_type"][blob.file_type]["errors"] += 1
            db.commit()
            continue

        inv_file_id = inv_file.id
        try:
            if blob.file_type == "hardware":
                ingest_hardware_file(db, inv_file, raw)
            else:
                try:
                    entries = parse_software_json(raw)
                except Exception as e:
                    _set_inventory_file_error(inv_file, f"Parse error: {e}")
                else:
                    content_endpoint_name = _resolve_software_endpoint_name(entries)
                    if content_endpoint_name:
                        filename_endpoint_name = _normalize_endpoint_name(inv_file.endpoint_name)
                        inv_file.endpoint_name = content_endpoint_name
                        if (
                            filename_endpoint_name
                            and filename_endpoint_name.upper() != content_endpoint_name.upper()
                        ):
                            logger.warning(
                                "Endpoint mismatch in software file %s: filename=%s content=%s",
                                inv_file.blob_name,
                                filename_endpoint_name,
                                content_endpoint_name,
                            )
                        ep = db.query(Endpoint).filter_by(endpoint_key=content_endpoint_name.upper()).first()
                        if ep:
                            snapshot = db.query(EndpointSnapshot).filter_by(endpoint_id=ep.id, is_current=True).first()
                            if snapshot:
                                ingest_software_file(db, inv_file, entries, snapshot)
                            else:
                                _set_inventory_file_error(inv_file, "No current snapshot found for endpoint")
                        else:
                            _set_inventory_file_error(
                                inv_file,
                                f"Endpoint {content_endpoint_name} not found - process hardware first",
                            )
                    else:
                        _set_inventory_file_error(
                            inv_file,
                            "Unable to determine endpoint from software file content",
                        )
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("Failed to ingest blob %s", blob.name)
            failed_file = db.query(InventoryFile).filter_by(id=inv_file_id).first()
            if failed_file:
                _set_inventory_file_error(failed_file, f"Ingest error: {exc}")
                db.commit()

        current_file = db.query(InventoryFile).filter_by(id=inv_file_id).first()
        if current_file and current_file.status == "processed":
            stats["processed"] += 1
            stats["by_type"][blob.file_type]["processed"] += 1
        else:
            stats["errors"] += 1
            stats["by_type"][blob.file_type]["errors"] += 1

    data_source.last_sync_at = datetime.now(timezone.utc)
    data_source.last_sync_status = "success" if stats["errors"] == 0 else "partial"
    if stats["errors"] > 0:
        data_source.last_error = f"{stats['errors']} file(s) failed"
    else:
        data_source.last_error = None
    db.commit()

    return stats
