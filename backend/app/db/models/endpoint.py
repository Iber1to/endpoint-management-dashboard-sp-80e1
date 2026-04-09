from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    computer_name: Mapped[str] = mapped_column(String(255), index=True)
    serial_number: Mapped[str | None] = mapped_column(String(255))
    smbios_uuid: Mapped[str | None] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(255))
    system_sku: Mapped[str | None] = mapped_column(String(255))
    firmware_type: Mapped[str | None] = mapped_column(String(50))
    bios_version: Mapped[str | None] = mapped_column(String(255))
    bios_release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    install_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    snapshots: Mapped[list["EndpointSnapshot"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")  # noqa: F821
    update_statuses: Mapped[list["WindowsUpdateStatus"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")  # noqa: F821
    software_findings: Mapped[list["EndpointSoftwareFinding"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")  # noqa: F821
