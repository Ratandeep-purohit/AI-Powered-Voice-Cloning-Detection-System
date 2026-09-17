"""Create Phase 07 prevention decision history table.

Revision ID: 7c1d2e4f8a90
Revises: 4a7f8c9d2e10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "7c1d2e4f8a90"
down_revision: Union[str, None] = "4a7f8c9d2e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prevention_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_score_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_score", sa.Numeric(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("response_action", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_prevention_decisions_score_range"),
        sa.CheckConstraint(
            "risk_level IN ('SAFE','LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_prevention_decisions_risk_level",
        ),
        sa.CheckConstraint(
            "response_action IN ('ALLOW','MONITOR','FLAG','REQUIRE_REVIEW','RESTRICT','BLOCK')",
            name="ck_prevention_decisions_action",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["risk_score_id"], ["risk_scores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_score_id", "policy_version", name="uq_prevention_decision_risk_policy"),
    )
    op.create_index("ix_prevention_decisions_organization_id", "prevention_decisions", ["organization_id"])
    op.create_index("ix_prevention_decisions_call_id", "prevention_decisions", ["call_id"])
    op.create_index("ix_prevention_decisions_response_action", "prevention_decisions", ["response_action"])
    op.create_index("ix_prevention_decisions_created_at", "prevention_decisions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_prevention_decisions_created_at", table_name="prevention_decisions")
    op.drop_index("ix_prevention_decisions_response_action", table_name="prevention_decisions")
    op.drop_index("ix_prevention_decisions_call_id", table_name="prevention_decisions")
    op.drop_index("ix_prevention_decisions_organization_id", table_name="prevention_decisions")
    op.drop_table("prevention_decisions")
