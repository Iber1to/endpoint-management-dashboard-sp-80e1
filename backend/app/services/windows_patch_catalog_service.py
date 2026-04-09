import re
from datetime import datetime, timezone, date
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.updates import WindowsPatchReference
from app.core.logging import logger

MS_LEARN_URL = "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"

_MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def _parse_release_date(text: str) -> Optional[date]:
    text = text.strip()
    m = re.search(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if m:
        month_name, day, year = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        month = _MONTH_MAP.get(month_name)
        if month:
            try:
                return date(year, int(month), day)
            except ValueError:
                pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def _date_to_patch_month(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    return d.strftime("%Y-%m")


def _extract_kb(text: str) -> Optional[str]:
    m = re.search(r"KB\s*(\d{6,8})", text, re.IGNORECASE)
    return f"KB{m.group(1)}" if m else None


def fetch_patch_catalog() -> list[dict]:
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(MS_LEARN_URL)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.error(f"Failed to fetch Windows patch catalog: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    entries = []

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not any("build" in h for h in headers):
            continue

        col_build = next((i for i, h in enumerate(headers) if "build" in h), None)
        col_kb = next((i for i, h in enumerate(headers) if "kb" in h), None)
        col_date = next((i for i, h in enumerate(headers) if "date" in h or "availab" in h), None)

        if col_build is None:
            continue

        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(filter(lambda x: x is not None, [col_build, col_kb or 0, col_date or 0])):
                continue

            build_text = cells[col_build].get_text(strip=True)
            m = re.match(r"(\d{5})\.(\d+)", build_text)
            if not m:
                continue

            os_build = m.group(1)
            os_revision = int(m.group(2))
            full_build = f"{os_build}.{os_revision}"

            kb_text = cells[col_kb].get_text(strip=True) if col_kb is not None and col_kb < len(cells) else ""
            kb_article = _extract_kb(kb_text) or _extract_kb(build_text)

            date_text = cells[col_date].get_text(strip=True) if col_date is not None and col_date < len(cells) else ""
            release_date = _parse_release_date(date_text)
            patch_month = _date_to_patch_month(release_date)

            windows_version = _infer_windows_version(os_build)

            entries.append({
                "product_name": "Windows 11",
                "windows_version": windows_version,
                "os_build": os_build,
                "os_revision": os_revision,
                "full_build": full_build,
                "kb_article": kb_article,
                "patch_month": patch_month,
                "patch_label": f"{patch_month} Update" if patch_month else None,
                "release_date": release_date,
                "source_url": MS_LEARN_URL,
                "source_type": "microsoft_learn",
                "is_security_update": True,
                "is_preview": "preview" in build_text.lower() or "preview" in kb_text.lower(),
            })

    logger.info(f"Fetched {len(entries)} patch entries from Microsoft Learn")
    return entries


def _infer_windows_version(os_build: str) -> Optional[str]:
    version_map = {
        "22000": "21H2",
        "22621": "22H2",
        "22631": "23H2",
        "26100": "24H2",
        "26200": "25H2",
    }
    return version_map.get(os_build)


def sync_patch_catalog(db: Session) -> dict:
    entries = fetch_patch_catalog()
    if not entries:
        return {"synced": 0, "error": "No entries fetched"}

    now = datetime.now(timezone.utc)
    catalog_version = now.strftime("%Y%m%d")
    synced = 0

    build_groups: dict[str, list[dict]] = {}
    for e in entries:
        key = f"{e['windows_version']}_{e['os_build']}"
        build_groups.setdefault(key, []).append(e)

    for group in build_groups.values():
        non_preview = [e for e in group if not e["is_preview"]]
        if non_preview:
            latest = max(non_preview, key=lambda x: x["os_revision"])
            for e in group:
                e["is_latest_for_branch"] = (e["full_build"] == latest["full_build"] and not e["is_preview"])

    affected_branches = list({(e["windows_version"], e["os_build"]) for e in entries if not e.get("is_preview")})
    for wv, ob in affected_branches:
        db.query(WindowsPatchReference).filter(
            WindowsPatchReference.windows_version == wv,
            WindowsPatchReference.os_build == ob,
            WindowsPatchReference.is_latest_for_branch == True,  # noqa: E712
        ).update({"is_latest_for_branch": False})

    for entry in entries:
        existing = db.query(WindowsPatchReference).filter_by(
            full_build=entry["full_build"], kb_article=entry["kb_article"]
        ).first()

        if existing:
            for k, v in entry.items():
                if v is not None:
                    setattr(existing, k, v)
            existing.scraped_at = now
            existing.catalog_version = catalog_version
        else:
            ref = WindowsPatchReference(
                **entry,
                scraped_at=now,
                catalog_version=catalog_version,
            )
            db.add(ref)
        synced += 1

    db.commit()
    logger.info(f"Patch catalog sync complete: {synced} entries")
    return {"synced": synced}
