from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import AzureError
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class BlobInfo:
    name: str
    last_modified: object
    etag: str
    size: int
    file_type: Optional[str] = None
    endpoint_name: Optional[str] = None
    snapshot_ts: Optional[str] = None


HARDWARE_PATTERN = re.compile(r"hardware_([^_]+(?:_[^_]+)*)_(\d{8}_\d{6})\.json$", re.IGNORECASE)
SOFTWARE_PATTERN = re.compile(r"software_([^_]+(?:_[^_]+)*)_(\d{8}_\d{6})\.json$", re.IGNORECASE)


def _classify_blob(name: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    basename = name.split("/")[-1]
    m = HARDWARE_PATTERN.match(basename)
    if m:
        return "hardware", m.group(1), m.group(2)
    m = SOFTWARE_PATTERN.match(basename)
    if m:
        return "software", m.group(1), m.group(2)
    return None, None, None


def get_container_client(account_url: str, sas_token: str, container_name: str) -> ContainerClient:
    service = BlobServiceClient(
        account_url=account_url.rstrip("/"),
        credential=sas_token.lstrip("?"),
    )
    return service.get_container_client(container_name)


def test_connection(account_url: str, sas_token: str, container_name: str, blob_prefix: str = "") -> dict:
    try:
        container = get_container_client(account_url, sas_token, container_name)
        blobs = list(container.list_blobs(name_starts_with=blob_prefix or None, max_results=10))
        sample = [b.name for b in blobs[:5]]
        return {"success": True, "containers_visible": True, "sample_blobs": sample, "error": None}
    except AzureError as e:
        return {"success": False, "containers_visible": False, "sample_blobs": [], "error": str(e)}
    except Exception as e:
        return {"success": False, "containers_visible": False, "sample_blobs": [], "error": str(e)}


def list_blobs(account_url: str, sas_token: str, container_name: str, blob_prefix: str = "") -> list[BlobInfo]:
    container = get_container_client(account_url, sas_token, container_name)
    result = []
    for blob in container.list_blobs(name_starts_with=blob_prefix or None):
        file_type, endpoint_name, snapshot_ts = _classify_blob(blob.name)
        result.append(BlobInfo(
            name=blob.name,
            last_modified=blob.last_modified,
            etag=blob.etag,
            size=blob.size,
            file_type=file_type,
            endpoint_name=endpoint_name,
            snapshot_ts=snapshot_ts,
        ))
    return result


def download_blob_json(account_url: str, sas_token: str, container_name: str, blob_name: str) -> bytes:
    container = get_container_client(account_url, sas_token, container_name)
    blob_client = container.get_blob_client(blob_name)
    return blob_client.download_blob().readall()
