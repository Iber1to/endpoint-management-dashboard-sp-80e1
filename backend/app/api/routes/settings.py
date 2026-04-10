from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.auth import require_admin
from app.core.logging import logger
from app.db.session import get_db
from app.db.models import DataSource, EndpointSnapshot, InventoryFile
from app.schemas.settings import BlobSettingsCreate, BlobSettingsOut, BlobTestRequest, BlobTestResponse
from app.services import blob_storage_service as bss
from app.core.security import encrypt_value, mask_token

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_admin)])


def _to_out(ds: DataSource) -> BlobSettingsOut:
    return BlobSettingsOut(
        id=ds.id,
        name=ds.name,
        account_url=ds.account_url,
        container_name=ds.container_name,
        blob_prefix=ds.blob_prefix,
        sas_token_masked=ds.sas_token_hint,
        sync_frequency_minutes=ds.sync_frequency_minutes,
        max_files_per_run=ds.max_files_per_run,
        max_files_per_run_enabled=ds.max_files_per_run_enabled,
        is_active=ds.is_active,
        last_sync_at=ds.last_sync_at,
        last_sync_status=ds.last_sync_status,
        last_error=ds.last_error,
    )


@router.get("/blob", response_model=list[BlobSettingsOut])
def get_blob_settings(db: Session = Depends(get_db)):
    return [_to_out(s) for s in db.query(DataSource).all()]


@router.post("/blob", response_model=BlobSettingsOut)
def create_or_update_blob_settings(payload: BlobSettingsCreate, db: Session = Depends(get_db)):
    try:
        encrypted_token = encrypt_value(payload.sas_token)
    except RuntimeError:
        logger.exception("Failed to encrypt SAS token while saving blob settings")
        raise HTTPException(status_code=500, detail="Server encryption is not configured correctly")

    hint = mask_token(payload.sas_token)
    existing = db.query(DataSource).filter_by(name=payload.name).first()

    if existing:
        existing.account_url = payload.account_url
        existing.container_name = payload.container_name
        existing.blob_prefix = payload.blob_prefix
        existing.sas_token_encrypted = encrypted_token
        existing.sas_token_hint = hint
        existing.sync_frequency_minutes = payload.sync_frequency_minutes
        existing.max_files_per_run = payload.max_files_per_run
        existing.max_files_per_run_enabled = payload.max_files_per_run_enabled
        existing.is_active = payload.is_active
        db.commit()
        db.refresh(existing)
        return _to_out(existing)

    ds = DataSource(
        name=payload.name,
        source_type="azure_blob",
        account_url=payload.account_url,
        container_name=payload.container_name,
        blob_prefix=payload.blob_prefix,
        sas_token_encrypted=encrypted_token,
        sas_token_hint=hint,
        sync_frequency_minutes=payload.sync_frequency_minutes,
        max_files_per_run=payload.max_files_per_run,
        max_files_per_run_enabled=payload.max_files_per_run_enabled,
        is_active=payload.is_active,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return _to_out(ds)


@router.post("/blob/test", response_model=BlobTestResponse)
def test_blob_connection(payload: BlobTestRequest):
    result = bss.test_connection(
        payload.account_url,
        payload.sas_token,
        payload.container_name,
        payload.blob_prefix or "",
    )
    if not result.get("success") and result.get("error"):
        logger.warning("Blob connection test failed: %s", result["error"])
        result["error"] = "Could not connect to Azure Blob Storage with the provided settings"
    return BlobTestResponse(**result)


@router.delete("/blob/{source_id}", status_code=204)
def delete_blob_settings(source_id: int, db: Session = Depends(get_db)):
    existing = db.query(DataSource).filter_by(id=source_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Data source not found")

    inventory_file_ids = select(InventoryFile.id).where(InventoryFile.data_source_id == source_id)

    try:
        db.query(EndpointSnapshot).filter(
            EndpointSnapshot.hardware_file_id.in_(inventory_file_ids)
        ).update(
            {EndpointSnapshot.hardware_file_id: None},
            synchronize_session=False,
        )
        db.query(EndpointSnapshot).filter(
            EndpointSnapshot.software_file_id.in_(inventory_file_ids)
        ).update(
            {EndpointSnapshot.software_file_id: None},
            synchronize_session=False,
        )

        db.delete(existing)
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("Failed to delete data source %s due to related records", source_id)
        raise HTTPException(status_code=409, detail="Data source cannot be deleted due to dependent records")
