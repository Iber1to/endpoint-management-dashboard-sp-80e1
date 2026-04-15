"""add software compliance metadata

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "software_compliance_rules",
        sa.Column("profile_name", sa.String(length=255), nullable=True),
    )
    op.execute("UPDATE software_compliance_rules SET profile_name = 'Default' WHERE profile_name IS NULL")
    op.alter_column("software_compliance_rules", "profile_name", nullable=False)
    op.create_index(
        "ix_software_compliance_rules_profile_name",
        "software_compliance_rules",
        ["profile_name"],
    )

    op.add_column("endpoint_software_findings", sa.Column("rule_id", sa.Integer(), nullable=True))
    op.add_column("endpoint_software_findings", sa.Column("profile_name", sa.String(length=255), nullable=True))
    op.add_column("endpoint_software_findings", sa.Column("rule_name", sa.String(length=255), nullable=True))
    op.add_column("endpoint_software_findings", sa.Column("software_name", sa.String(length=500), nullable=True))
    op.add_column("endpoint_software_findings", sa.Column("software_version", sa.String(length=255), nullable=True))
    op.add_column("endpoint_software_findings", sa.Column("minimum_version", sa.String(length=100), nullable=True))

    op.create_index(
        "ix_endpoint_software_findings_profile_name",
        "endpoint_software_findings",
        ["profile_name"],
    )
    op.create_foreign_key(
        "fk_endpoint_software_findings_rule_id",
        "endpoint_software_findings",
        "software_compliance_rules",
        ["rule_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_endpoint_software_findings_rule_id", "endpoint_software_findings", type_="foreignkey")
    op.drop_index("ix_endpoint_software_findings_profile_name", table_name="endpoint_software_findings")
    op.drop_column("endpoint_software_findings", "minimum_version")
    op.drop_column("endpoint_software_findings", "software_version")
    op.drop_column("endpoint_software_findings", "software_name")
    op.drop_column("endpoint_software_findings", "rule_name")
    op.drop_column("endpoint_software_findings", "profile_name")
    op.drop_column("endpoint_software_findings", "rule_id")

    op.drop_index("ix_software_compliance_rules_profile_name", table_name="software_compliance_rules")
    op.drop_column("software_compliance_rules", "profile_name")

