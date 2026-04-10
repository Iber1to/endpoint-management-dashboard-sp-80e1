"""enforce min sync interval settings

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE data_sources SET sync_frequency_minutes = 480 WHERE sync_frequency_minutes < 480")
    op.alter_column(
        "data_sources",
        "sync_frequency_minutes",
        existing_type=sa.Integer(),
        server_default="1440",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "data_sources",
        "sync_frequency_minutes",
        existing_type=sa.Integer(),
        server_default="60",
        existing_nullable=False,
    )
