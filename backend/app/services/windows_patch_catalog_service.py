import re
from datetime import datetime, timezone, date
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.db.models.updates import WindowsPatchReference
from app.core.logging import logger

MS_LEARN_URL = "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"

_MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

_VERSION_BLOCK_RE = re.compile(
    r"Version\s+([0-9]{2}H[12])\s+\(OS build\s+(\d{5})\)(.*?)(?=Version\s+[0-9]{2}H[12]\s+\(OS build\s+\d{5}\)|$)",
    re.IGNORECASE | re.DOTALL,
)

_ROW_RE = re.compile(
    r"^(?P<release_channel>.+?)\s+"
    r"(?:(?P<update_type>\d{4}-\d{2}(?:\s+(?:B|D|OOB))?)\s+)?"
    r"(?P<availability_date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<full_build>\d{5}\.\d+)"
    r"(?:\s+(?P<kb_article>KB\d{6,8}))?$",
    re.IGNORECASE,
)


def _parse_release_date(text: str) -> Optional[date]:
    text = (text or "").strip()

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


def _patch_month_from_update_type(text: str) -> Optional[str]:
    text = (text or "").strip()
    m = re.search(r"(\d{4})-(\d{2})", text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def _dedupe_entries(entries: list[dict]) -> list[dict]:
    unique: dict[tuple[str, str], dict] = {}

    for e in entries:
        full_build = (e.get("full_build") or "").strip()
        kb_article = (e.get("kb_article") or "").strip()

        if not full_build:
            continue

        dedupe_key = (full_build, kb_article or "__NO_KB__")
        unique[dedupe_key] = e

    return list(unique.values())


def _normalize_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    text = text.replace("\xa0", " ")
    text = text.replace("•", " • ")
    text = re.sub(r"\s+", " ", text)
    return text


def fetch_patch_catalog() -> list[dict]:
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(MS_LEARN_URL)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.error(f"Failed to fetch Windows patch catalog: {e}")
        return []

    text = _normalize_text(html)

    marker = "Windows 11 release history"
    start_idx = text.find(marker)
    if start_idx == -1:
        logger.warning("Release history section not found in Microsoft Learn page")
        return []

    release_history_text = text[start_idx:]

    version_block_re = re.compile(
        r"Version\s+([0-9]{2}H[12])\s+\(OS build\s+(\d{5})\)\s+"
        r"Servicing option\s+Update type\s+Availability date\s+Build\s+KB article\s+"
        r"(.*?)"
        r"(?=Version\s+[0-9]{2}H[12]\s+\(OS build\s+\d{5}\)|$)",
        re.IGNORECASE | re.DOTALL,
    )

    row_re = re.compile(
        r"(?P<release_channel>.+?)\s+"
        r"(?:(?P<update_type>\d{4}-\d{2}(?:\s+(?:B|D|OOB))?)\s+)?"
        r"(?P<availability_date>\d{4}-\d{2}-\d{2})\s+"
        r"(?P<full_build>\d{5}\.\d+)"
        r"(?:\s+(?P<kb_article>KB\d{6,8}))?",
        re.IGNORECASE,
    )

    entries: list[dict] = []

    for block_match in version_block_re.finditer(release_history_text):
        windows_version = block_match.group(1).upper()
        heading_os_build = block_match.group(2)
        block_text = block_match.group(3)

        for row_match in row_re.finditer(block_text):
            full_build = row_match.group("full_build")
            os_build, os_revision_str = full_build.split(".", 1)

            if os_build != heading_os_build:
                continue

            os_revision = int(os_revision_str)
            update_type = row_match.group("update_type")
            availability_date_text = row_match.group("availability_date")
            kb_article = row_match.group("kb_article")
            release_channel = row_match.group("release_channel").strip()

            release_date = _parse_release_date(availability_date_text)
            patch_month = _patch_month_from_update_type(update_type) or _date_to_patch_month(release_date)

            is_preview = bool(update_type and re.search(r"\bD\b", update_type, re.IGNORECASE))

            entries.append({
                "product_name": "Windows 11",
                "windows_version": windows_version,
                "release_channel": release_channel or None,
                "os_build": os_build,
                "os_revision": os_revision,
                "full_build": full_build,
                "kb_article": kb_article,
                "patch_month": patch_month,
                "patch_label": update_type or (f"{patch_month} Update" if patch_month else None),
                "release_date": release_date,
                "source_url": MS_LEARN_URL,
                "source_type": "microsoft_learn",
                "is_security_update": True,
                "is_preview": is_preview,
            })

    logger.info(f"Fetched {len(entries)} patch entries from Microsoft Learn")
    return entries


def sync_patch_catalog(db: Session) -> dict:
    entries = fetch_patch_catalog()
    if not entries:
        return {"synced": 0, "error": "No entries fetched"}

    entries = _dedupe_entries(entries)
    logger.info(f"Patch entries after dedupe: {len(entries)}")

    now = datetime.now(timezone.utc)
    catalog_version = now.strftime("%Y%m%d")
    synced = 0

    build_groups: dict[str, list[dict]] = {}
    for e in entries:
        key = f"{e.get('windows_version')}_{e.get('os_build')}"
        build_groups.setdefault(key, []).append(e)

    for group in build_groups.values():
        latest = max(group, key=lambda x: x["os_revision"])
        for e in group:
            e["is_latest_for_branch"] = (e["full_build"] == latest["full_build"])

    try:
        affected_branches = list({
            (e.get("windows_version"), e.get("os_build"))
            for e in entries
        })

        for wv, ob in affected_branches:
            db.query(WindowsPatchReference).filter(
                WindowsPatchReference.windows_version == wv,
                WindowsPatchReference.os_build == ob,
                WindowsPatchReference.is_latest_for_branch == True,  # noqa: E712
            ).update({"is_latest_for_branch": False})

        for entry in entries:
            existing = db.query(WindowsPatchReference).filter_by(
                full_build=entry["full_build"],
                kb_article=entry["kb_article"],
            ).first()

            if existing:
                existing.product_name = entry.get("product_name")
                existing.windows_version = entry.get("windows_version")
                existing.release_channel = entry.get("release_channel")
                existing.os_build = entry.get("os_build")
                existing.os_revision = entry.get("os_revision")
                existing.full_build = entry.get("full_build")
                existing.kb_article = entry.get("kb_article")
                existing.patch_month = entry.get("patch_month")
                existing.patch_label = entry.get("patch_label")
                existing.release_date = entry.get("release_date")
                existing.source_url = entry.get("source_url")
                existing.source_type = entry.get("source_type")
                existing.is_security_update = bool(entry.get("is_security_update", True))
                existing.is_preview = bool(entry.get("is_preview", False))
                existing.is_latest_for_branch = bool(entry.get("is_latest_for_branch", False))
                existing.scraped_at = now
                existing.catalog_version = catalog_version
            else:
                ref = WindowsPatchReference(
                    product_name=entry.get("product_name"),
                    windows_version=entry.get("windows_version"),
                    release_channel=entry.get("release_channel"),
                    os_build=entry.get("os_build"),
                    os_revision=entry.get("os_revision"),
                    full_build=entry.get("full_build"),
                    kb_article=entry.get("kb_article"),
                    patch_month=entry.get("patch_month"),
                    patch_label=entry.get("patch_label"),
                    release_date=entry.get("release_date"),
                    source_url=entry.get("source_url"),
                    source_type=entry.get("source_type"),
                    is_security_update=bool(entry.get("is_security_update", True)),
                    is_preview=bool(entry.get("is_preview", False)),
                    is_latest_for_branch=bool(entry.get("is_latest_for_branch", False)),
                    scraped_at=now,
                    catalog_version=catalog_version,
                )
                db.add(ref)

            synced += 1

        db.commit()
        logger.info(f"Patch catalog sync complete: {synced} entries")
        return {"synced": synced}

    except Exception:
        db.rollback()
        logger.exception("Patch catalog sync failed during database persistence")
        raise