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
    accepted: bool
    run_id: Optional[str] = None
    status: str
    message: Optional[str] = None
    retry_after_seconds: Optional[int] = None


class SyncTypeStats(BaseModel):
    discovered: int
    processed: int
    errors: int
    skipped: int


class SyncStatsOut(BaseModel):
    total: int
    processed: int
    errors: int
    skipped: int
    snapshots_created: int = 0
    snapshot_id_from: Optional[int] = None
    snapshot_id_to: Optional[int] = None
    by_type: dict[str, SyncTypeStats]


class SyncExecutionOut(BaseModel):
    run_id: str
    data_source_id: Optional[int]
    status: str
    requested_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    stats: SyncStatsOut
    sources_total: int
    sources_failed: list[str]
    evaluation_failed: bool
    message: Optional[str]
