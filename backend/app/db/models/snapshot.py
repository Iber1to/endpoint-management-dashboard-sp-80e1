from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base


class EndpointSnapshot(Base):
    __tablename__ = "endpoint_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id", ondelete="CASCADE"), index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    registry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hardware_file_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_files.id"))
    software_file_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_files.id"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    endpoint: Mapped["Endpoint"] = relationship(back_populates="snapshots")  # noqa: F821
    hardware: Mapped["EndpointHardware | None"] = relationship(back_populates="snapshot", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    security: Mapped["EndpointSecurity | None"] = relationship(back_populates="snapshot", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    network_adapters: Mapped[list["EndpointNetworkAdapter"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")  # noqa: F821
    disks: Mapped[list["EndpointDisk"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")  # noqa: F821
    installed_software: Mapped[list["InstalledSoftware"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")  # noqa: F821
    hardware_file: Mapped["InventoryFile | None"] = relationship(foreign_keys=[hardware_file_id])  # noqa: F821
    software_file: Mapped["InventoryFile | None"] = relationship(foreign_keys=[software_file_id])  # noqa: F821
