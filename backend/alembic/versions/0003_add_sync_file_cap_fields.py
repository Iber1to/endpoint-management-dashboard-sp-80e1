"""add sync file cap fields to data_sources

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "data_sources",
        sa.Column("max_files_per_run", sa.Integer(), nullable=False, server_default="50000"),
    )
    op.add_column(
        "data_sources",
        sa.Column("max_files_per_run_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("data_sources", "max_files_per_run_enabled")
    op.drop_column("data_sources", "max_files_per_run")
