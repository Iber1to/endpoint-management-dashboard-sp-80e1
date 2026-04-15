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


class SoftwareAnalyticsItem(BaseModel):
    label: str
    endpoint_count: int


class SoftwareAnalyticsResponse(BaseModel):
    top_software: list[SoftwareAnalyticsItem]
    top_publishers: list[SoftwareAnalyticsItem]


class SoftwareVersionItem(BaseModel):
    software_version: Optional[str]
    endpoint_count: int


class SoftwareVersionListResponse(BaseModel):
    items: list[SoftwareVersionItem]
    total: int


class SoftwareEndpointInstallItem(BaseModel):
    endpoint_id: int
    computer_name: str
    software_name: Optional[str]
    software_version: Optional[str]
    publisher: Optional[str]
    app_type: Optional[str]
    app_source: Optional[str]


class SoftwareEndpointInstallListResponse(BaseModel):
    items: list[SoftwareEndpointInstallItem]
    total: int
    page: int
    page_size: int


class SoftwareCatalogItem(BaseModel):
    normalized_name: str
    display_name: str


class SoftwareComplianceRuleCreate(BaseModel):
    name: str
    profile_name: str = "Default"
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


class SoftwareSettingsRuleCreate(BaseModel):
    profile_name: str = "Default"
    software_name: str
    rule_kind: str  # "forbidden" | "minimum_version"
    minimum_version: Optional[str] = None
    severity: str = "medium"


class SoftwareComplianceProfileSummary(BaseModel):
    profile_name: str
    list_type: str
    total_endpoints: int
    compliant_endpoints: int
    non_compliant_endpoints: int
    forbidden_endpoints: int
    minimum_version_endpoints: int


class SoftwareComplianceSummaryResponse(BaseModel):
    items: list[SoftwareComplianceProfileSummary]


class SoftwareComplianceEndpointFindingItem(BaseModel):
    endpoint_id: int
    computer_name: str
    profile_name: Optional[str]
    finding_type: str
    severity: str
    rule_name: Optional[str]
    software_name: Optional[str]
    software_version: Optional[str]
    minimum_version: Optional[str]
    details: Optional[str]
    detected_at: Optional[date]


class SoftwareComplianceEndpointFindingListResponse(BaseModel):
    items: list[SoftwareComplianceEndpointFindingItem]
    total: int
    page: int
    page_size: int
