from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DiskOut(BaseModel):
    id: int
    device_id: Optional[str]
    friendly_name: Optional[str]
    media_type: Optional[str]
    bus_type: Optional[str]
    health_status: Optional[str]
    operational_status: Optional[str]
    size_bytes: Optional[int]
    wear: Optional[int]
    temperature: Optional[int]
    temperature_max: Optional[int]

    model_config = {"from_attributes": True}


class NetworkAdapterOut(BaseModel):
    id: int
    name: Optional[str]
    interface_alias: Optional[str]
    interface_description: Optional[str]
    mac_address: Optional[str]
    link_speed: Optional[str]
    status: Optional[str]
    net_profile_name: Optional[str]
    ipv4_address: Optional[str]
    ipv6_address: Optional[str]
    ipv4_default_gateway: Optional[str]
    dns_server: Optional[str]

    model_config = {"from_attributes": True}


class HardwareOut(BaseModel):
    os_name: Optional[str]
    windows_version: Optional[str]
    os_build: Optional[str]
    os_revision: Optional[int]
    full_build: Optional[str]
    memory_bytes: Optional[int]
    cpu_manufacturer: Optional[str]
    cpu_name: Optional[str]
    cpu_cores: Optional[int]
    cpu_logical_processors: Optional[int]
    pc_system_type: Optional[str]
    last_boot: Optional[datetime]
    uptime_days: Optional[float]
    default_au_service: Optional[str]
    au_metered: Optional[bool]

    model_config = {"from_attributes": True}


class SecurityOut(BaseModel):
    tpm_present: Optional[bool]
    tpm_ready: Optional[bool]
    tpm_enabled: Optional[bool]
    tpm_activated: Optional[bool]
    tpm_managed_auth_level: Optional[int]
    bitlocker_mount_point: Optional[str]
    bitlocker_cipher: Optional[int]
    bitlocker_volume_status: Optional[int]
    bitlocker_protection_status: Optional[int]
    bitlocker_lock_status: Optional[int]

    model_config = {"from_attributes": True}


class EndpointListItem(BaseModel):
    id: int
    computer_name: str
    manufacturer: Optional[str]
    model: Optional[str]
    os_name: Optional[str]
    windows_version: Optional[str]
    full_build: Optional[str]
    last_seen_at: Optional[datetime]
    bitlocker_protection_status: Optional[int]
    tpm_present: Optional[bool]
    patch_compliance_status: Optional[str]

    model_config = {"from_attributes": True}


class EndpointListResponse(BaseModel):
    items: list[EndpointListItem]
    total: int
    page: int
    page_size: int


class EndpointDetail(BaseModel):
    id: int
    computer_name: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    smbios_uuid: Optional[str]
    firmware_type: Optional[str]
    bios_version: Optional[str]
    last_seen_at: Optional[datetime]
    hardware: Optional[HardwareOut]
    security: Optional[SecurityOut]
    network_adapters: list[NetworkAdapterOut]
    disks: list[DiskOut]
    software_count: int
    patch_compliance_status: Optional[str]

    model_config = {"from_attributes": True}
