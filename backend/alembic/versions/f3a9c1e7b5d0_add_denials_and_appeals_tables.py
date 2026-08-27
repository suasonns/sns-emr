"""add denials and appeals tables

Revision ID: f3a9c1e7b5d0
Revises: e1b7c9d4f8a2
Create Date: 2026-08-24

Real, persisted denial + appeal tracking. denials rows are created
automatically by app.services.payment_service.post_payments_from_835
whenever an 835 remittance line is detected as a hard denial (see
DENIAL_CARC_CODES). appeals rows track one or more appeal attempts
against a denial (first-level, second-level, ALJ/external review).

This is the real backing data for the Denials & Appeals sections shown
on both the Biller's Dashboard and the owner's Tenant Analytics
financials/billing mirror -- replacing the previously hardcoded mock
denial-code table in the legacy BillingDashboard.tsx.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f3a9c1e7b5d0"
down_revision = "e1b7c9d4f8a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "denials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("claims.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("carc_code", sa.String(length=8), nullable=True),
        sa.Column("reason_description", sa.Text(), nullable=True),
        sa.Column("denied_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("denial_date", sa.Date(), nullable=True),
        sa.Column("appeal_deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_denials_tenant_id", "denials", ["tenant_id"])
    op.create_index("ix_denials_claim_id", "denials", ["claim_id"])
    op.create_index("ix_denials_payment_id", "denials", ["payment_id"])
    op.create_index("ix_denials_carc_code", "denials", ["carc_code"])
    op.create_index("ix_denials_status", "denials", ["status"])
    op.create_index("ix_denial_tenant_status", "denials", ["tenant_id", "status"])

    op.create_table(
        "appeals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "denial_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("denials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("submitted_date", sa.Date(), nullable=True),
        sa.Column("submitted_by", sa.String(length=255), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("outcome_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_appeals_tenant_id", "appeals", ["tenant_id"])
    op.create_index("ix_appeals_denial_id", "appeals", ["denial_id"])
    op.create_index("ix_appeals_status", "appeals", ["status"])
    op.create_index("ix_appeal_tenant_status", "appeals", ["tenant_id", "status"])
    op.create_index("ix_appeal_denial_level", "appeals", ["denial_id", "level"])


def downgrade() -> None:
    op.drop_index("ix_appeal_denial_level", table_name="appeals")
    op.drop_index("ix_appeal_tenant_status", table_name="appeals")
    op.drop_index("ix_appeals_status", table_name="appeals")
    op.drop_index("ix_appeals_denial_id", table_name="appeals")
    op.drop_index("ix_appeals_tenant_id", table_name="appeals")
    op.drop_table("appeals")

    op.drop_index("ix_denial_tenant_status", table_name="denials")
    op.drop_index("ix_denials_status", table_name="denials")
    op.drop_index("ix_denials_carc_code", table_name="denials")
    op.drop_index("ix_denials_payment_id", table_name="denials")
    op.drop_index("ix_denials_claim_id", table_name="denials")
    op.drop_index("ix_denials_tenant_id", table_name="denials")
    op.drop_table("denials")
