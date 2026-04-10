from __future__ import annotations
from sqlalchemy import ForeignKey, String, Boolean, Integer, Date, DateTime, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from app.db.base import Base


class WindowsPatchReference(Base):
    __tablename__ = "windows_patch_reference"
    __table_args__ = (UniqueConstraint("full_build", "kb_article", name="uq_patch_ref_build_kb"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str | None] = mapped_column(String(255))
    windows_version: Mapped[str | None] = mapped_column(String(50), index=True)
    release_channel: Mapped[str | None] = mapped_column(String(100))
    os_build: Mapped[str | None] = mapped_column(String(50))
    os_revision: Mapped[int | None] = mapped_column(Integer)
    full_build: Mapped[str | None] = mapped_column(String(50), index=True)
    kb_article: Mapped[str | None] = mapped_column(String(50))
    patch_month: Mapped[str | None] = mapped_column(String(20), index=True)
    patch_label: Mapped[str | None] = mapped_column(String(255))
    release_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(String(50))
    is_security_update: Mapped[bool] = mapped_column(Boolean, default=True)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False)
    is_latest_for_branch: Mapped[bool] = mapped_column(Boolean, default=False)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    catalog_version: Mapped[str | None] = mapped_column(String(50))


class WindowsUpdateStatus(Base):
    __tablename__ = "windows_update_status"
    __table_args__ = (UniqueConstraint("endpoint_id", "snapshot_id", name="uq_update_status_endpoint_snapshot"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), index=True)
    windows_version: Mapped[str | None] = mapped_column(String(50))
    os_build: Mapped[str | None] = mapped_column(String(50))
    os_revision: Mapped[int | None] = mapped_column(Integer)
    full_build: Mapped[str | None] = mapped_column(String(50))
    patch_month: Mapped[str | None] = mapped_column(String(20))
    patch_label: Mapped[str | None] = mapped_column(String(255))
    kb_article: Mapped[str | None] = mapped_column(String(50))
    compliance_status: Mapped[str] = mapped_column(String(50), default="unknown")
    months_behind: Mapped[int | None] = mapped_column(Integer)
    inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    endpoint: Mapped["Endpoint"] = relationship(back_populates="update_statuses")  # noqa: F821
