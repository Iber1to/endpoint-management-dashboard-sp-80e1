import json
import re
from datetime import date
from typing import Any
from dateutil import parser as dp


def _parse_install_date(val: Any) -> date | None:
    if not val:
        return None
    s = str(val).strip()
    if re.match(r"^\d{8}$", s):
        try:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            return None
    try:
        return dp.parse(s).date()
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


def parse_software_json(raw: bytes) -> list[dict]:
    data = json.loads(raw)
    if not isinstance(data, list):
        data = [data]

    entries = []
    for item in data:
        if not item:
            continue
        entries.append({
            "computer_name": item.get("ComputerName") or "",
            "registry_date": item.get("RegistryDate"),
            "managed_device_id": item.get("ManagedDeviceID") or None,
            "managed_device_name": item.get("ManagedDeviceName") or None,
            "app_source": item.get("AppSource") or None,
            "app_type": item.get("AppType") or None,
            "software_name": item.get("AppName") or None,
            "software_version": item.get("AppVersion") or None,
            "install_date": _parse_install_date(item.get("AppInstallDate")),
            "publisher": item.get("AppPublisher") or None,
            "uninstall_string": item.get("AppUninstallString") or None,
            "uninstall_reg_path": item.get("AppUninstallRegPath") or None,
            "system_component": _to_bool(item.get("SystemComponent")),
            "windows_installer": _to_bool(item.get("WindowsInstaller")),
            "app_scope": item.get("AppScope") or None,
            "architecture": item.get("AppArchitecture") or None,
            "package_full_name": item.get("AppPackageFullName") or None,
            "package_family_name": item.get("AppPackageFamilyName") or None,
            "install_location": item.get("AppInstallLocation") or None,
            "is_framework": _to_bool(item.get("AppIsFramework")),
            "is_resource_package": _to_bool(item.get("AppIsResourcePackage")),
            "is_bundle": _to_bool(item.get("AppIsBundle")),
            "is_development_mode": _to_bool(item.get("AppIsDevelopmentMode")),
            "is_non_removable": _to_bool(item.get("AppNonRemovable")),
            "signature_kind": item.get("AppSignatureKind"),
        })
    return entries
