from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InventoryFileOut(BaseModel):
    id: int
    blob_name: str
    file_type: Optional[str]
    endpoint_name: Optional[str]
    blob_last_modified: Optional[datetime]
    status: str
    error_message: Optional[str]
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SyncStatusResponse(BaseModel):
    data_source_id: int
    name: str
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_error: Optional[str]


class SyncRunResponse(BaseModel):
    success: bool
    stats: dict
    error: Optional[str] = None
