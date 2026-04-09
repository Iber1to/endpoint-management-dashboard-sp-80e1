from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BlobSettingsCreate(BaseModel):
    name: str = "default"
    account_url: str
    container_name: str
    sas_token: str
    blob_prefix: Optional[str] = ""
    sync_frequency_minutes: int = 60
    is_active: bool = True


class BlobSettingsOut(BaseModel):
    id: int
    name: str
    account_url: Optional[str]
    container_name: Optional[str]
    blob_prefix: Optional[str]
    sas_token_masked: Optional[str]
    sync_frequency_minutes: int
    is_active: bool
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_error: Optional[str]

    model_config = {"from_attributes": True}


class BlobTestRequest(BaseModel):
    account_url: str
    container_name: str
    sas_token: str
    blob_prefix: Optional[str] = ""


class BlobTestResponse(BaseModel):
    success: bool
    containers_visible: bool
    sample_blobs: list[str]
    error: Optional[str]
