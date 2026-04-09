import json
from datetime import datetime
from dateutil import parser as dateparser
from typing import Any


def _parse_dt(val: Any) -> datetime | None:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return dateparser.parse(str(val))
    except Exception:
        return None


def _to_bool(val: Any) -> bool | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return None


def parse_hardware_json(raw: bytes) -> dict:
    data = json.loads(raw)

    os_build = str(data.get("OSBuild", "") or "").strip()
    os_revision = data.get("OSRevision")
    full_build = f"{os_build}.{os_revision}" if os_build and os_revision is not None else None

    endpoint = {
        "computer_name": data.get("ComputerName") or "",
        "serial_number": data.get("SerialNumber") or None,
        "smbios_uuid": data.get("SMBIOSUUID") or None,
        "manufacturer": data.get("Manufacturer") or None,
        "model": data.get("Model") or None,
        "system_sku": data.get("SystemSKU") or None,
        "firmware_type": data.get("FirmwareType") or None,
        "bios_version": data.get("BiosVersion") or None,
        "bios_release_date": _parse_dt(data.get("BiosReleaseDate")),
        "install_date": _parse_dt(data.get("InstallDate")),
        "last_seen_at": _parse_dt(data.get("RegistryDate")),
    }

    hardware = {
        "os_name": data.get("OSName") or None,
        "windows_version": data.get("WindowsVersion") or None,
        "os_build": os_build or None,
        "os_revision": os_revision,
        "full_build": full_build,
        "memory_bytes": data.get("MemoryBytes"),
        "cpu_manufacturer": data.get("CPUManufacturer") or None,
        "cpu_name": data.get("CPUName") or None,
        "cpu_cores": data.get("CPUCores"),
        "cpu_logical_processors": data.get("CPULogicalProcessors"),
        "pc_system_type": data.get("PCSystemType") or None,
        "pc_system_type_ex": data.get("PCSystemTypeEx") or None,
        "last_boot": _parse_dt(data.get("LastBoot")),
        "uptime_days": data.get("ComputerUpTimeDays"),
        "default_au_service": data.get("DefaultAUService") or None,
        "au_metered": _to_bool(data.get("AUMetered")),
    }

    security = {
        "tpm_present": _to_bool(data.get("TPMPresent")),
        "tpm_ready": _to_bool(data.get("TPMReady")),
        "tpm_enabled": _to_bool(data.get("TPMEnabled")),
        "tpm_activated": _to_bool(data.get("TPMActivated")),
        "tpm_managed_auth_level": data.get("TPMManagedAuthLevel"),
        "bitlocker_mount_point": data.get("BitLockerMountPoint") or None,
        "bitlocker_cipher": data.get("BitLockerCipher"),
        "bitlocker_volume_status": data.get("BitLockerVolumeStatus"),
        "bitlocker_protection_status": data.get("BitLockerProtectionStatus"),
        "bitlocker_lock_status": data.get("BitLockerLockStatus"),
    }

    network_adapters = []
    for na in data.get("NetworkAdapters") or []:
        if not na:
            continue
        network_adapters.append({
            "name": na.get("Name") or None,
            "interface_alias": na.get("InterfaceAlias") or None,
            "interface_description": na.get("InterfaceDescription") or None,
            "mac_address": na.get("MacAddress") or None,
            "link_speed": na.get("LinkSpeed") or None,
            "status": na.get("Status") or None,
            "net_profile_name": na.get("NetProfileName") or None,
            "ipv4_address": na.get("IPv4Address") or None,
            "ipv6_address": na.get("IPv6Address") or None,
            "ipv4_default_gateway": na.get("IPv4DefaultGateway") or None,
            "dns_server": na.get("DNSServer") or None,
        })

    disks = []
    for disk in data.get("DiskHealth") or []:
        if not disk:
            continue
        disks.append({
            "device_id": disk.get("DeviceId") or None,
            "friendly_name": disk.get("FriendlyName") or None,
            "serial_number": disk.get("SerialNumber") or None,
            "media_type": disk.get("MediaType") or None,
            "bus_type": disk.get("BusType") or None,
            "health_status": disk.get("HealthStatus") or None,
            "operational_status": disk.get("OperationalStatus") or None,
            "size_bytes": disk.get("SizeBytes"),
            "wear": disk.get("Wear"),
            "temperature": disk.get("Temperature"),
            "temperature_max": disk.get("TemperatureMax"),
            "read_errors_total": disk.get("ReadErrorsTotal"),
            "read_errors_uncorrected": disk.get("ReadErrorsUncorrected"),
            "write_errors_total": disk.get("WriteErrorsTotal"),
            "write_errors_uncorrected": disk.get("WriteErrorsUncorrected"),
        })

    registry_date = _parse_dt(data.get("RegistryDate"))

    return {
        "endpoint": endpoint,
        "hardware": hardware,
        "security": security,
        "network_adapters": network_adapters,
        "disks": disks,
        "registry_date": registry_date,
        "snapshot_at": registry_date,
    }
