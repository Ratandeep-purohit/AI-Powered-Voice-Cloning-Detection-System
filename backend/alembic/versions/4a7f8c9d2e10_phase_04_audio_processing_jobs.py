"""Create audio processing jobs table for Phase 04.

Revision ID: 4a7f8c9d2e10
Revises: 2c9a7d4e61b3
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "4a7f8c9d2e10"
down_revision = "2c9a7d4e61b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audio_processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audio_input_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source_sample_rate", sa.Integer(), nullable=True),
        sa.Column("source_channels", sa.Integer(), nullable=True),
        sa.Column("source_duration_ms", sa.BigInteger(), nullable=True),
        sa.Column("processed_sample_rate", sa.Integer(), nullable=True),
        sa.Column("processed_channels", sa.Integer(), nullable=True),
        sa.Column("processed_duration_ms", sa.BigInteger(), nullable=True),
        sa.Column("processed_storage_key", sa.Text(), nullable=True),
        sa.Column("processed_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("processed_sha256", sa.Text(), nullable=True),
        sa.Column("normalization_applied", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED')", name="ck_audio_processing_jobs_status"),
        sa.CheckConstraint("source_sample_rate IS NULL OR source_sample_rate > 0", name="ck_audio_processing_source_rate_positive"),
        sa.CheckConstraint("processed_sample_rate IS NULL OR processed_sample_rate > 0", name="ck_audio_processing_processed_rate_positive"),
        sa.CheckConstraint("source_channels IS NULL OR source_channels > 0", name="ck_audio_processing_source_channels_positive"),
        sa.CheckConstraint("processed_channels IS NULL OR processed_channels > 0", name="ck_audio_processing_processed_channels_positive"),
        sa.CheckConstraint("source_duration_ms IS NULL OR source_duration_ms >= 0", name="ck_audio_processing_source_duration_non_negative"),
        sa.CheckConstraint("processed_duration_ms IS NULL OR processed_duration_ms >= 0", name="ck_audio_processing_processed_duration_non_negative"),
        sa.ForeignKeyConstraint(["audio_input_id"], ["audio_inputs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("processed_storage_key"),
    )
    op.create_index("ix_audio_processing_jobs_audio_input_id", "audio_processing_jobs", ["audio_input_id"])
    op.create_index("ix_audio_processing_jobs_status", "audio_processing_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_audio_processing_jobs_status", table_name="audio_processing_jobs")
    op.drop_index("ix_audio_processing_jobs_audio_input_id", table_name="audio_processing_jobs")
    op.drop_table("audio_processing_jobs")
