from __future__ import annotations
from sqlalchemy import ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EndpointSecurity(Base):
    __tablename__ = "endpoint_security"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), unique=True, index=True)
    tpm_present: Mapped[bool | None] = mapped_column(Boolean)
    tpm_ready: Mapped[bool | None] = mapped_column(Boolean)
    tpm_enabled: Mapped[bool | None] = mapped_column(Boolean)
    tpm_activated: Mapped[bool | None] = mapped_column(Boolean)
    tpm_managed_auth_level: Mapped[int | None] = mapped_column(Integer)
    bitlocker_mount_point: Mapped[str | None] = mapped_column(String(10))
    bitlocker_cipher: Mapped[int | None] = mapped_column(Integer)
    bitlocker_volume_status: Mapped[int | None] = mapped_column(Integer)
    bitlocker_protection_status: Mapped[int | None] = mapped_column(Integer)
    bitlocker_lock_status: Mapped[int | None] = mapped_column(Integer)

    snapshot: Mapped["EndpointSnapshot"] = relationship(back_populates="security")  # noqa: F821
