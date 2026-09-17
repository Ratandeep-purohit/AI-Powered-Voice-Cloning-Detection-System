"""Phase 09 alert engine constraints and idempotency.

Revision ID: b7e4f2a9c310
Revises: 9d2e7f4a1b30
"""

from alembic import op

revision = "b7e4f2a9c310"
down_revision = "9d2e7f4a1b30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_alerts_risk_score_type",
        "alerts",
        ["risk_score_id", "alert_type"],
    )
    op.create_index(
        "ix_alerts_organization_created_at",
        "alerts",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_alerts_organization_created_at", table_name="alerts")
    op.drop_constraint("uq_alerts_risk_score_type", "alerts", type_="unique")
