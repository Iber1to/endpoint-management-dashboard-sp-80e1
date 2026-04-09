from pydantic import BaseModel
from datetime import date
from typing import Optional


class InstalledSoftwareOut(BaseModel):
    id: int
    software_name: Optional[str]
    software_version: Optional[str]
    publisher: Optional[str]
    install_date: Optional[date]
    app_type: Optional[str]
    app_source: Optional[str]
    app_scope: Optional[str]
    system_component: Optional[bool]
    is_framework: Optional[bool]
    normalized_name: Optional[str]
    normalized_publisher: Optional[str]

    model_config = {"from_attributes": True}


class SoftwareAggregatedItem(BaseModel):
    normalized_name: Optional[str]
    display_name: Optional[str]
    publisher: Optional[str]
    version_count: int
    endpoint_count: int
    latest_version: Optional[str]
    app_type: Optional[str]
    app_source: Optional[str]


class SoftwareListResponse(BaseModel):
    items: list[SoftwareAggregatedItem]
    total: int
    page: int
    page_size: int


class SoftwareComplianceRuleCreate(BaseModel):
    name: str
    rule_type: str
    product_match_pattern: Optional[str] = None
    publisher_match_pattern: Optional[str] = None
    scope: Optional[str] = None
    is_required: bool = False
    is_forbidden: bool = False
    minimum_version: Optional[str] = None
    maximum_version: Optional[str] = None
    severity: str = "medium"
    is_active: bool = True


class SoftwareComplianceRuleOut(SoftwareComplianceRuleCreate):
    id: int
    model_config = {"from_attributes": True}
