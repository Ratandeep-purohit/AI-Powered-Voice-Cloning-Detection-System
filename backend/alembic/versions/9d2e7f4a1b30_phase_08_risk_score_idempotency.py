"""Phase 08 risk score idempotency constraint.

Revision ID: 9d2e7f4a1b30
Revises: 7c1d2e4f8a90
"""

from typing import Sequence, Union

from alembic import op


revision: str = "9d2e7f4a1b30"
down_revision: Union[str, None] = "7c1d2e4f8a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_risk_scores_voice_analysis_policy",
        "risk_scores",
        ["voice_analysis_id", "policy_version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_risk_scores_voice_analysis_policy",
        "risk_scores",
        type_="unique",
    )
