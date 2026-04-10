from __future__ import annotations
from sqlalchemy import ForeignKey, String, Boolean, Integer, Date, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from app.db.base import Base


class InstalledSoftware(Base):
    __tablename__ = "installed_software"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id", ondelete="CASCADE"), index=True)
    software_name: Mapped[str | None] = mapped_column(String(500))
    software_version: Mapped[str | None] = mapped_column(String(255))
    publisher: Mapped[str | None] = mapped_column(String(500))
    install_date: Mapped[date | None] = mapped_column(Date)
    architecture: Mapped[str | None] = mapped_column(String(50))
    install_source: Mapped[str | None] = mapped_column(String(500))
    detection_source: Mapped[str | None] = mapped_column(String(100))
    app_type: Mapped[str | None] = mapped_column(String(50), index=True)
    app_source: Mapped[str | None] = mapped_column(String(50), index=True)
    app_scope: Mapped[str | None] = mapped_column(String(50))
    managed_device_id: Mapped[str | None] = mapped_column(String(255))
    managed_device_name: Mapped[str | None] = mapped_column(String(255))
    uninstall_string: Mapped[str | None] = mapped_column(Text)
    uninstall_reg_path: Mapped[str | None] = mapped_column(Text)
    system_component: Mapped[bool | None] = mapped_column(Boolean)
    windows_installer: Mapped[bool | None] = mapped_column(Boolean)
    package_full_name: Mapped[str | None] = mapped_column(String(500))
    package_family_name: Mapped[str | None] = mapped_column(String(500))
    install_location: Mapped[str | None] = mapped_column(Text)
    is_framework: Mapped[bool | None] = mapped_column(Boolean)
    is_resource_package: Mapped[bool | None] = mapped_column(Boolean)
    is_bundle: Mapped[bool | None] = mapped_column(Boolean)
    is_development_mode: Mapped[bool | None] = mapped_column(Boolean)
    is_non_removable: Mapped[bool | None] = mapped_column(Boolean)
    signature_kind: Mapped[int | None] = mapped_column(Integer)
    normalized_name: Mapped[str | None] = mapped_column(String(500), index=True)
    normalized_publisher: Mapped[str | None] = mapped_column(String(500))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    superseded_by_software_id: Mapped[int | None] = mapped_column(ForeignKey("installed_software.id"))
    dedupe_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    snapshot: Mapped["EndpointSnapshot"] = relationship(back_populates="installed_software")  # noqa: F821


class SoftwareProduct(Base):
    __tablename__ = "software_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_name: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(500))
    product_family: Mapped[str | None] = mapped_column(String(255))
    software_category: Mapped[str | None] = mapped_column(String(100))
    vendor_category: Mapped[str | None] = mapped_column(String(100))
    is_os_component: Mapped[bool] = mapped_column(Boolean, default=False)
    is_security_tool: Mapped[bool] = mapped_column(Boolean, default=False)
    is_browser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_collaboration_tool: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote_support_tool: Mapped[bool] = mapped_column(Boolean, default=False)
    is_allowed: Mapped[bool | None] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)

    versions: Mapped[list["SoftwareProductVersion"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    findings: Mapped[list["EndpointSoftwareFinding"]] = relationship(back_populates="software_product", cascade="all, delete-orphan")


class SoftwareProductVersion(Base):
    __tablename__ = "software_product_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    software_product_id: Mapped[int] = mapped_column(ForeignKey("software_products.id", ondelete="CASCADE"), index=True)
    version_raw: Mapped[str | None] = mapped_column(String(255))
    version_normalized: Mapped[str | None] = mapped_column(String(255))
    release_channel: Mapped[str | None] = mapped_column(String(100))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    release_date: Mapped[date | None] = mapped_column(Date)
    eol_date: Mapped[date | None] = mapped_column(Date)

    product: Mapped["SoftwareProduct"] = relationship(back_populates="versions")


class SoftwareComplianceRule(Base):
    __tablename__ = "software_compliance_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    rule_type: Mapped[str] = mapped_column(String(50))
    product_match_pattern: Mapped[str | None] = mapped_column(String(500))
    publisher_match_pattern: Mapped[str | None] = mapped_column(String(500))
    scope: Mapped[str | None] = mapped_column(String(50))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_forbidden: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_version: Mapped[str | None] = mapped_column(String(100))
    maximum_version: Mapped[str | None] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class EndpointSoftwareFinding(Base):
    __tablename__ = "endpoint_software_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("endpoint_snapshots.id", ondelete="CASCADE"), index=True)
    software_product_id: Mapped[int | None] = mapped_column(ForeignKey("software_products.id"))
    finding_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    status: Mapped[str] = mapped_column(String(50), default="open")
    details: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[date | None] = mapped_column(Date)

    endpoint: Mapped["Endpoint"] = relationship(back_populates="software_findings")  # noqa: F821
    software_product: Mapped["SoftwareProduct | None"] = relationship(back_populates="findings")
