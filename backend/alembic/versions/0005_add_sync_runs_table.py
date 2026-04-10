"""add sync runs table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=32), nullable=False),
        sa.Column("data_source_id", sa.Integer(), sa.ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("force", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("stats_json", sa.JSON(), nullable=True),
        sa.Column("sources_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_failed_json", sa.JSON(), nullable=True),
        sa.Column("evaluation_failed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sync_runs_run_id", "sync_runs", ["run_id"], unique=True)
    op.create_index("ix_sync_runs_data_source_id", "sync_runs", ["data_source_id"], unique=False)
    op.create_index("ix_sync_runs_status", "sync_runs", ["status"], unique=False)
    op.create_index("ix_sync_runs_requested_at", "sync_runs", ["requested_at"], unique=False)

    op.execute(
        """
        INSERT INTO sync_runs (
            run_id, data_source_id, force, status, requested_at, started_at, finished_at,
            duration_seconds, stats_json, sources_total, sources_failed_json, evaluation_failed, message
        )
        SELECT
            SUBSTRING(md5('backfill-' || ds.id::text || '-' || COALESCE(ds.last_sync_at::text, '')) FOR 32),
            ds.id,
            false,
            CASE
                WHEN ds.last_sync_status = 'success' THEN 'success'
                WHEN ds.last_sync_status = 'partial' THEN 'partial'
                WHEN ds.last_sync_status = 'error' THEN 'failed'
                ELSE 'success'
            END,
            ds.last_sync_at,
            ds.last_sync_at,
            ds.last_sync_at,
            0,
            json_build_object(
                'total', 0,
                'processed', 0,
                'errors', 0,
                'skipped', 0,
                'snapshots_created', 0,
                'snapshot_id_from', NULL,
                'snapshot_id_to', NULL,
                'by_type', json_build_object(
                    'hardware', json_build_object('discovered', 0, 'processed', 0, 'errors', 0, 'skipped', 0),
                    'software', json_build_object('discovered', 0, 'processed', 0, 'errors', 0, 'skipped', 0)
                )
            ),
            1,
            json_build_array(),
            false,
            COALESCE(ds.last_error, 'Backfilled from previous sync status')
        FROM data_sources ds
        WHERE ds.last_sync_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_sync_runs_requested_at", table_name="sync_runs")
    op.drop_index("ix_sync_runs_status", table_name="sync_runs")
    op.drop_index("ix_sync_runs_data_source_id", table_name="sync_runs")
    op.drop_index("ix_sync_runs_run_id", table_name="sync_runs")
    op.drop_table("sync_runs")
