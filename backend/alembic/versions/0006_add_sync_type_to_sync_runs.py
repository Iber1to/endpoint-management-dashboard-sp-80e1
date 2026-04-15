"""add sync type to sync runs

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sync_runs",
        sa.Column("sync_type", sa.String(length=32), nullable=False, server_default="inventory"),
    )
    op.create_index("ix_sync_runs_sync_type", "sync_runs", ["sync_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sync_runs_sync_type", table_name="sync_runs")
    op.drop_column("sync_runs", "sync_type")
