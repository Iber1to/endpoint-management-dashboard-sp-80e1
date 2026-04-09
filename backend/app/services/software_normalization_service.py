import hashlib
import re
from typing import Optional


_STRIP_PATTERNS = [
    re.compile(r"\s*\(x86\)", re.IGNORECASE),
    re.compile(r"\s*\(x64\)", re.IGNORECASE),
    re.compile(r"\s*64-bit", re.IGNORECASE),
    re.compile(r"\s*32-bit", re.IGNORECASE),
    re.compile(r"\s+v?\d+(\.\d+){1,3}$"),
]

_PUBLISHER_STRIP = re.compile(r"^(cn=|o=|l=|s=|c=)", re.IGNORECASE)

_SECURITY_TOOLS = {"crowdstrike", "netskope", "zscaler", "forticlient", "fortinet", "sentinel", "defender"}
_BROWSERS = {"edge", "chrome", "firefox", "chromium", "opera"}
_COLLABORATION = {"teams", "outlook", "onedrive", "slack", "zoom"}
_REMOTE_SUPPORT = {"citrix", "teamviewer", "anydesk", "rdp", "vnc", "avaya"}


def normalize_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = name.strip()
    for pat in _STRIP_PATTERNS:
        n = pat.sub("", n)
    return n.strip().lower()


def normalize_publisher(publisher: Optional[str]) -> Optional[str]:
    if not publisher:
        return None
    parts = publisher.split(",")
    first = parts[0].strip()
    m = re.match(r"CN=(.+)", first, re.IGNORECASE)
    if m:
        return m.group(1).strip().lower()
    return first.lower()


def compute_dedupe_hash(snapshot_id: int, software_name: Optional[str], software_version: Optional[str], app_source: Optional[str]) -> str:
    key = f"{snapshot_id}|{(software_name or '').lower()}|{(software_version or '').lower()}|{(app_source or '').lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:64]


def classify_software(entry: dict) -> dict:
    norm_name = normalize_name(entry.get("software_name")) or ""
    norm_pub = normalize_publisher(entry.get("publisher")) or ""

    is_security_tool = any(k in norm_name or k in norm_pub for k in _SECURITY_TOOLS)
    is_browser = any(k in norm_name for k in _BROWSERS)
    is_collaboration = any(k in norm_name for k in _COLLABORATION)
    is_remote_support = any(k in norm_name or k in norm_pub for k in _REMOTE_SUPPORT)
    is_os_component = bool(
        entry.get("system_component")
        or entry.get("is_framework")
        or entry.get("is_resource_package")
        or (entry.get("app_source") == "Appx" and entry.get("is_non_removable"))
    )

    return {
        "normalized_name": norm_name,
        "normalized_publisher": norm_pub,
        "is_security_tool": is_security_tool,
        "is_browser": is_browser,
        "is_collaboration_tool": is_collaboration,
        "is_remote_support_tool": is_remote_support,
        "is_os_component": is_os_component,
    }
