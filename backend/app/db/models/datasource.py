from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    source_type: Mapped[str] = mapped_column(String(50), default="azure_blob")
    account_url: Mapped[str | None] = mapped_column(Text)
    container_name: Mapped[str | None] = mapped_column(String(255))
    blob_prefix: Mapped[str | None] = mapped_column(String(500))
    sas_token_encrypted: Mapped[str | None] = mapped_column(Text)
    sas_token_hint: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_status: Mapped[str | None] = mapped_column(String(50))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inventory_files: Mapped[list["InventoryFile"]] = relationship(
        back_populates="data_source",
        cascade="all, delete-orphan",
    )


class InventoryFile(Base):
    __tablename__ = "inventory_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blob_name: Mapped[str] = mapped_column(Text, index=True)
    file_type: Mapped[str | None] = mapped_column(String(50))
    endpoint_name: Mapped[str | None] = mapped_column(String(255), index=True)
    blob_last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    etag: Mapped[str | None] = mapped_column(String(255))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)

    data_source: Mapped["DataSource"] = relationship(back_populates="inventory_files")
