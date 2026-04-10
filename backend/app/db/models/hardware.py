from __future__ import annotations
from sqlalchemy import ForeignKey, String, BigInteger, DateTime, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base


class EndpointHardware(Base):
    __tablename__ = "endpoint_hardware"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), unique=True, index=True)
    os_name: Mapped[str | None] = mapped_column(String(255))
    windows_version: Mapped[str | None] = mapped_column(String(50), index=True)
    os_build: Mapped[str | None] = mapped_column(String(50))
    os_revision: Mapped[int | None] = mapped_column(Integer)
    full_build: Mapped[str | None] = mapped_column(String(50), index=True)
    memory_bytes: Mapped[int | None] = mapped_column(BigInteger)
    cpu_manufacturer: Mapped[str | None] = mapped_column(String(255))
    cpu_name: Mapped[str | None] = mapped_column(String(255))
    cpu_cores: Mapped[int | None] = mapped_column(Integer)
    cpu_logical_processors: Mapped[int | None] = mapped_column(Integer)
    pc_system_type: Mapped[str | None] = mapped_column(String(100))
    pc_system_type_ex: Mapped[str | None] = mapped_column(String(100))
    last_boot: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uptime_days: Mapped[float | None] = mapped_column(Float)
    default_au_service: Mapped[str | None] = mapped_column(String(255))
    au_metered: Mapped[bool | None] = mapped_column(Boolean)

    snapshot: Mapped["EndpointSnapshot"] = relationship(back_populates="hardware")  # noqa: F821


class EndpointNetworkAdapter(Base):
    __tablename__ = "endpoint_network_adapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    interface_alias: Mapped[str | None] = mapped_column(String(255))
    interface_description: Mapped[str | None] = mapped_column(String(255))
    mac_address: Mapped[str | None] = mapped_column(String(50))
    link_speed: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(50))
    net_profile_name: Mapped[str | None] = mapped_column(String(255))
    ipv4_address: Mapped[str | None] = mapped_column(String(50))
    ipv6_address: Mapped[str | None] = mapped_column(String(100))
    ipv4_default_gateway: Mapped[str | None] = mapped_column(String(50))
    dns_server: Mapped[str | None] = mapped_column(String(255))

    snapshot: Mapped["EndpointSnapshot"] = relationship(back_populates="network_adapters")  # noqa: F821


class EndpointDisk(Base):
    __tablename__ = "endpoint_disks"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str | None] = mapped_column(String(50))
    friendly_name: Mapped[str | None] = mapped_column(String(255))
    serial_number: Mapped[str | None] = mapped_column(String(255))
    media_type: Mapped[str | None] = mapped_column(String(50))
    bus_type: Mapped[str | None] = mapped_column(String(50))
    health_status: Mapped[str | None] = mapped_column(String(50))
    operational_status: Mapped[str | None] = mapped_column(String(50))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    wear: Mapped[int | None] = mapped_column(Integer)
    temperature: Mapped[int | None] = mapped_column(Integer)
    temperature_max: Mapped[int | None] = mapped_column(Integer)
    read_errors_total: Mapped[int | None] = mapped_column(BigInteger)
    read_errors_uncorrected: Mapped[int | None] = mapped_column(BigInteger)
    write_errors_total: Mapped[int | None] = mapped_column(BigInteger)
    write_errors_uncorrected: Mapped[int | None] = mapped_column(BigInteger)

    snapshot: Mapped["EndpointSnapshot"] = relationship(back_populates="disks")  # noqa: F821
