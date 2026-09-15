"""Create audio-input metadata table for Phase 03.

Revision ID: 2c9a7d4e61b3
Revises: 8f6b2d9c1a40
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2c9a7d4e61b3"
down_revision: Union[str, None] = "8f6b2d9c1a40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audio_inputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("detected_format", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("intake_status", sa.Text(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "intake_status IN ('PENDING','VALIDATED','REJECTED','FAILED')",
            name="ck_audio_inputs_intake_status",
        ),
        sa.CheckConstraint("size_bytes > 0", name="ck_audio_inputs_size_positive"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_audio_inputs_call_id", "audio_inputs", ["call_id"])
    op.create_index("ix_audio_inputs_sha256", "audio_inputs", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_audio_inputs_sha256", table_name="audio_inputs")
    op.drop_index("ix_audio_inputs_call_id", table_name="audio_inputs")
    op.drop_table("audio_inputs")
