from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class PatchReferenceOut(BaseModel):
    id: int
    windows_version: Optional[str]
    os_build: Optional[str]
    os_revision: Optional[int]
    full_build: Optional[str]
    kb_article: Optional[str]
    patch_month: Optional[str]
    patch_label: Optional[str]
    release_date: Optional[date]
    is_preview: bool
    is_latest_for_branch: bool

    model_config = {"from_attributes": True}


class UpdateStatusOut(BaseModel):
    endpoint_id: int
    computer_name: str
    windows_version: Optional[str]
    full_build: Optional[str]
    kb_article: Optional[str]
    patch_month: Optional[str]
    patch_label: Optional[str]
    compliance_status: str
    months_behind: Optional[int]
    inferred: bool
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class UpdateComplianceSummary(BaseModel):
    up_to_date: int
    behind_1_month: int
    behind_2_plus_months: int
    unknown: int
    total: int


class UpdateComplianceResponse(BaseModel):
    target_patch: Optional[str]
    summary: UpdateComplianceSummary
    items: list[UpdateStatusOut]
