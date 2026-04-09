"""add sas_token_hint to data_sources

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("data_sources", sa.Column("sas_token_hint", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("data_sources", "sas_token_hint")
