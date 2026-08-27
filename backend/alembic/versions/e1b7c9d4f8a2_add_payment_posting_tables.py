"""add remittance_advices, payments, payment_adjustments tables

Revision ID: e1b7c9d4f8a2
Revises: d8a1f3c6e2b4
Create Date: 2026-08-24

Real, persisted ERA (835) payment posting data model. Replaces the
previously-broken app/services/edi_835_parser.py + payment_service.py +
app/api/billing_835.py, which imported a non-existent app.models.payment
.Payment class and were never registered as a router.

remittance_advices: one row per inbound 835 file/upload (header-level
payer + total-paid info).
payments: one row per claim-level payment line within a remittance
advice, optionally matched to a real `claims` row.
payment_adjustments: CAS (Claim Adjustment) segments -- CARC code +
group code + amount -- the real backing data for denial reasons.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e1b7c9d4f8a2"
down_revision = "d8a1f3c6e2b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "remittance_advices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payer_name", sa.String(length=255), nullable=True),
        sa.Column("total_paid_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("payment_date", sa.String(length=16), nullable=True),
        sa.Column("claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RECEIVED"),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_remittance_advices_tenant_id", "remittance_advices", ["tenant_id"]
    )
    op.create_index(
        "ix_remittance_advice_tenant_status", "remittance_advices", ["tenant_id", "status"]
    )
    op.create_index(
        "ix_remittance_advices_received_at", "remittance_advices", ["received_at"]
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "remittance_advice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("remittance_advices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("claims.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("claim_control_number", sa.String(length=64), nullable=True),
        sa.Column("patient_name", sa.String(length=255), nullable=True),
        sa.Column("billed_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("allowed_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("patient_responsibility", sa.Numeric(12, 2), nullable=True),
        sa.Column("payment_date", sa.String(length=16), nullable=True),
        sa.Column("is_denied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "match_status", sa.String(length=32), nullable=False, server_default="UNMATCHED"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index(
        "ix_payments_remittance_advice_id", "payments", ["remittance_advice_id"]
    )
    op.create_index("ix_payments_claim_id", "payments", ["claim_id"])
    op.create_index(
        "ix_payment_claim_control_number", "payments", ["claim_control_number"]
    )
    op.create_index(
        "ix_payment_tenant_match_status", "payments", ["tenant_id", "match_status"]
    )

    op.create_table(
        "payment_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("group_code", sa.String(length=4), nullable=True),
        sa.Column("carc_code", sa.String(length=8), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_payment_adjustments_payment_id", "payment_adjustments", ["payment_id"]
    )
    op.create_index("ix_payment_adjustment_carc", "payment_adjustments", ["carc_code"])


def downgrade() -> None:
    op.drop_index("ix_payment_adjustment_carc", table_name="payment_adjustments")
    op.drop_index("ix_payment_adjustments_payment_id", table_name="payment_adjustments")
    op.drop_table("payment_adjustments")

    op.drop_index("ix_payment_tenant_match_status", table_name="payments")
    op.drop_index("ix_payment_claim_control_number", table_name="payments")
    op.drop_index("ix_payments_claim_id", table_name="payments")
    op.drop_index("ix_payments_remittance_advice_id", table_name="payments")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_remittance_advices_received_at", table_name="remittance_advices")
    op.drop_index("ix_remittance_advice_tenant_status", table_name="remittance_advices")
    op.drop_index("ix_remittance_advices_tenant_id", table_name="remittance_advices")
    op.drop_table("remittance_advices")
