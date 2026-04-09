"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "endpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint_key", sa.String(255), nullable=False),
        sa.Column("computer_name", sa.String(255), nullable=False),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("smbios_uuid", sa.String(255), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("system_sku", sa.String(255), nullable=True),
        sa.Column("firmware_type", sa.String(50), nullable=True),
        sa.Column("bios_version", sa.String(255), nullable=True),
        sa.Column("bios_release_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("install_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_endpoints_endpoint_key", "endpoints", ["endpoint_key"], unique=True)
    op.create_index("ix_endpoints_computer_name", "endpoints", ["computer_name"])

    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="azure_blob"),
        sa.Column("account_url", sa.Text(), nullable=True),
        sa.Column("container_name", sa.String(255), nullable=True),
        sa.Column("blob_prefix", sa.String(500), nullable=True),
        sa.Column("sas_token_encrypted", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sync_frequency_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "inventory_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("blob_name", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("endpoint_name", sa.String(255), nullable=True),
        sa.Column("blob_last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("etag", sa.String(255), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_files_blob_name", "inventory_files", ["blob_name"])
    op.create_index("ix_inventory_files_endpoint_name", "inventory_files", ["endpoint_name"])
    op.create_index("ix_inventory_files_data_source_id", "inventory_files", ["data_source_id"])

    op.create_table(
        "endpoint_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hardware_file_id", sa.Integer(), nullable=True),
        sa.Column("software_file_id", sa.Integer(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hardware_file_id"], ["inventory_files.id"]),
        sa.ForeignKeyConstraint(["software_file_id"], ["inventory_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_endpoint_snapshots_endpoint_id", "endpoint_snapshots", ["endpoint_id"])
    op.create_index("ix_endpoint_snapshots_snapshot_at", "endpoint_snapshots", ["snapshot_at"])
    op.create_index("ix_endpoint_snapshots_is_current", "endpoint_snapshots", ["is_current"])

    op.create_table(
        "endpoint_hardware",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("os_name", sa.String(255), nullable=True),
        sa.Column("windows_version", sa.String(50), nullable=True),
        sa.Column("os_build", sa.String(50), nullable=True),
        sa.Column("os_revision", sa.Integer(), nullable=True),
        sa.Column("full_build", sa.String(50), nullable=True),
        sa.Column("memory_bytes", sa.BigInteger(), nullable=True),
        sa.Column("cpu_manufacturer", sa.String(255), nullable=True),
        sa.Column("cpu_name", sa.String(255), nullable=True),
        sa.Column("cpu_cores", sa.Integer(), nullable=True),
        sa.Column("cpu_logical_processors", sa.Integer(), nullable=True),
        sa.Column("pc_system_type", sa.String(100), nullable=True),
        sa.Column("pc_system_type_ex", sa.String(100), nullable=True),
        sa.Column("last_boot", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uptime_days", sa.Float(), nullable=True),
        sa.Column("default_au_service", sa.String(255), nullable=True),
        sa.Column("au_metered", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id"),
    )
    op.create_index("ix_endpoint_hardware_snapshot_id", "endpoint_hardware", ["snapshot_id"])
    op.create_index("ix_endpoint_hardware_windows_version", "endpoint_hardware", ["windows_version"])
    op.create_index("ix_endpoint_hardware_full_build", "endpoint_hardware", ["full_build"])

    op.create_table(
        "endpoint_security",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("tpm_present", sa.Boolean(), nullable=True),
        sa.Column("tpm_ready", sa.Boolean(), nullable=True),
        sa.Column("tpm_enabled", sa.Boolean(), nullable=True),
        sa.Column("tpm_activated", sa.Boolean(), nullable=True),
        sa.Column("tpm_managed_auth_level", sa.Integer(), nullable=True),
        sa.Column("bitlocker_mount_point", sa.String(10), nullable=True),
        sa.Column("bitlocker_cipher", sa.Integer(), nullable=True),
        sa.Column("bitlocker_volume_status", sa.Integer(), nullable=True),
        sa.Column("bitlocker_protection_status", sa.Integer(), nullable=True),
        sa.Column("bitlocker_lock_status", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id"),
    )
    op.create_index("ix_endpoint_security_snapshot_id", "endpoint_security", ["snapshot_id"])

    op.create_table(
        "endpoint_network_adapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("interface_alias", sa.String(255), nullable=True),
        sa.Column("interface_description", sa.String(255), nullable=True),
        sa.Column("mac_address", sa.String(50), nullable=True),
        sa.Column("link_speed", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("net_profile_name", sa.String(255), nullable=True),
        sa.Column("ipv4_address", sa.String(50), nullable=True),
        sa.Column("ipv6_address", sa.String(100), nullable=True),
        sa.Column("ipv4_default_gateway", sa.String(50), nullable=True),
        sa.Column("dns_server", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_endpoint_network_adapters_snapshot_id", "endpoint_network_adapters", ["snapshot_id"])

    op.create_table(
        "endpoint_disks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(50), nullable=True),
        sa.Column("friendly_name", sa.String(255), nullable=True),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("bus_type", sa.String(50), nullable=True),
        sa.Column("health_status", sa.String(50), nullable=True),
        sa.Column("operational_status", sa.String(50), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("wear", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Integer(), nullable=True),
        sa.Column("temperature_max", sa.Integer(), nullable=True),
        sa.Column("read_errors_total", sa.BigInteger(), nullable=True),
        sa.Column("read_errors_uncorrected", sa.BigInteger(), nullable=True),
        sa.Column("write_errors_total", sa.BigInteger(), nullable=True),
        sa.Column("write_errors_uncorrected", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_endpoint_disks_snapshot_id", "endpoint_disks", ["snapshot_id"])

    op.create_table(
        "software_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("normalized_name", sa.String(500), nullable=False),
        sa.Column("display_name", sa.String(500), nullable=True),
        sa.Column("publisher", sa.String(500), nullable=True),
        sa.Column("product_family", sa.String(255), nullable=True),
        sa.Column("software_category", sa.String(100), nullable=True),
        sa.Column("vendor_category", sa.String(100), nullable=True),
        sa.Column("is_os_component", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_security_tool", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_browser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_collaboration_tool", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_remote_support_tool", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_allowed", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_index("ix_software_products_normalized_name", "software_products", ["normalized_name"])

    op.create_table(
        "software_product_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("software_product_id", sa.Integer(), nullable=False),
        sa.Column("version_raw", sa.String(255), nullable=True),
        sa.Column("version_normalized", sa.String(255), nullable=True),
        sa.Column("release_channel", sa.String(100), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("eol_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["software_product_id"], ["software_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_software_product_versions_software_product_id", "software_product_versions", ["software_product_id"])

    op.create_table(
        "software_compliance_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("product_match_pattern", sa.String(500), nullable=True),
        sa.Column("publisher_match_pattern", sa.String(500), nullable=True),
        sa.Column("scope", sa.String(50), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_forbidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("minimum_version", sa.String(100), nullable=True),
        sa.Column("maximum_version", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "installed_software",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.Column("software_name", sa.String(500), nullable=True),
        sa.Column("software_version", sa.String(255), nullable=True),
        sa.Column("publisher", sa.String(500), nullable=True),
        sa.Column("install_date", sa.Date(), nullable=True),
        sa.Column("architecture", sa.String(50), nullable=True),
        sa.Column("install_source", sa.String(500), nullable=True),
        sa.Column("detection_source", sa.String(100), nullable=True),
        sa.Column("app_type", sa.String(50), nullable=True),
        sa.Column("app_source", sa.String(50), nullable=True),
        sa.Column("app_scope", sa.String(50), nullable=True),
        sa.Column("managed_device_id", sa.String(255), nullable=True),
        sa.Column("managed_device_name", sa.String(255), nullable=True),
        sa.Column("uninstall_string", sa.Text(), nullable=True),
        sa.Column("uninstall_reg_path", sa.Text(), nullable=True),
        sa.Column("system_component", sa.Boolean(), nullable=True),
        sa.Column("windows_installer", sa.Boolean(), nullable=True),
        sa.Column("package_full_name", sa.String(500), nullable=True),
        sa.Column("package_family_name", sa.String(500), nullable=True),
        sa.Column("install_location", sa.Text(), nullable=True),
        sa.Column("is_framework", sa.Boolean(), nullable=True),
        sa.Column("is_resource_package", sa.Boolean(), nullable=True),
        sa.Column("is_bundle", sa.Boolean(), nullable=True),
        sa.Column("is_development_mode", sa.Boolean(), nullable=True),
        sa.Column("is_non_removable", sa.Boolean(), nullable=True),
        sa.Column("signature_kind", sa.Integer(), nullable=True),
        sa.Column("normalized_name", sa.String(500), nullable=True),
        sa.Column("normalized_publisher", sa.String(500), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("superseded_by_software_id", sa.Integer(), nullable=True),
        sa.Column("dedupe_hash", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by_software_id"], ["installed_software.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installed_software_snapshot_id", "installed_software", ["snapshot_id"])
    op.create_index("ix_installed_software_endpoint_id", "installed_software", ["endpoint_id"])
    op.create_index("ix_installed_software_normalized_name", "installed_software", ["normalized_name"])
    op.create_index("ix_installed_software_app_source", "installed_software", ["app_source"])
    op.create_index("ix_installed_software_app_type", "installed_software", ["app_type"])
    op.create_index("ix_installed_software_dedupe_hash", "installed_software", ["dedupe_hash"])

    op.create_table(
        "endpoint_software_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("software_product_id", sa.Integer(), nullable=True),
        sa.Column("finding_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["software_product_id"], ["software_products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_endpoint_software_findings_endpoint_id", "endpoint_software_findings", ["endpoint_id"])
    op.create_index("ix_endpoint_software_findings_snapshot_id", "endpoint_software_findings", ["snapshot_id"])

    op.create_table(
        "windows_patch_reference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("windows_version", sa.String(50), nullable=True),
        sa.Column("release_channel", sa.String(100), nullable=True),
        sa.Column("os_build", sa.String(50), nullable=True),
        sa.Column("os_revision", sa.Integer(), nullable=True),
        sa.Column("full_build", sa.String(50), nullable=True),
        sa.Column("kb_article", sa.String(50), nullable=True),
        sa.Column("patch_month", sa.String(20), nullable=True),
        sa.Column("patch_label", sa.String(255), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("is_security_update", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_preview", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_latest_for_branch", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("catalog_version", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_build", "kb_article", name="uq_patch_ref_build_kb"),
    )
    op.create_index("ix_windows_patch_reference_full_build", "windows_patch_reference", ["full_build"])
    op.create_index("ix_windows_patch_reference_windows_version", "windows_patch_reference", ["windows_version"])
    op.create_index("ix_windows_patch_reference_patch_month", "windows_patch_reference", ["patch_month"])

    op.create_table(
        "windows_update_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("windows_version", sa.String(50), nullable=True),
        sa.Column("os_build", sa.String(50), nullable=True),
        sa.Column("os_revision", sa.Integer(), nullable=True),
        sa.Column("full_build", sa.String(50), nullable=True),
        sa.Column("patch_month", sa.String(20), nullable=True),
        sa.Column("patch_label", sa.String(255), nullable=True),
        sa.Column("kb_article", sa.String(50), nullable=True),
        sa.Column("compliance_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("months_behind", sa.Integer(), nullable=True),
        sa.Column("inferred", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["endpoint_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint_id", "snapshot_id", name="uq_update_status_endpoint_snapshot"),
    )
    op.create_index("ix_windows_update_status_endpoint_id", "windows_update_status", ["endpoint_id"])
    op.create_index("ix_windows_update_status_snapshot_id", "windows_update_status", ["snapshot_id"])


def downgrade() -> None:
    op.drop_table("windows_update_status")
    op.drop_table("windows_patch_reference")
    op.drop_table("endpoint_software_findings")
    op.drop_table("installed_software")
    op.drop_table("software_compliance_rules")
    op.drop_table("software_product_versions")
    op.drop_table("software_products")
    op.drop_table("endpoint_disks")
    op.drop_table("endpoint_network_adapters")
    op.drop_table("endpoint_security")
    op.drop_table("endpoint_hardware")
    op.drop_table("endpoint_snapshots")
    op.drop_table("inventory_files")
    op.drop_table("data_sources")
    op.drop_table("endpoints")
