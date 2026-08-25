"""add claims and claim_edi_batches tables

Revision ID: d8a1f3c6e2b4
Revises: c2e8a5d1f4b6
Create Date: 2026-08-24

Replaces the in-memory app.billing.store mock CLAIMS list with a real,
persisted per-patient-per-billing-cycle claim record so claim lifecycle
status (READY/SENT/ACCEPTED/DENIED/PAID) survives restarts and is
queryable across agencies for the Biller's Dashboard and the new Claims
Management page.

claim_edi_batches tracks each 837I submission event and its 999/277CA
acknowledgment status (currently one claim per batch; a future
true multi-claim batch submit flow can add more claims to the same
batch_number).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d8a1f3c6e2b4"
down_revision = "c2e8a5d1f4b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "claim_edi_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("batch_number", sa.String(length=64), nullable=False),
        sa.Column("claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ack_status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("ack_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ack_raw_content", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("batch_number", name="uq_claim_edi_batches_batch_number"),
    )
    op.create_index(
        "ix_claim_edi_batches_tenant_id", "claim_edi_batches", ["tenant_id"]
    )
    op.create_index(
        "ix_claim_edi_batch_tenant_status", "claim_edi_batches", ["tenant_id", "ack_status"]
    )
    op.create_index(
        "ix_claim_edi_batches_batch_number", "claim_edi_batches", ["batch_number"]
    )
    op.create_index(
        "ix_claim_edi_batches_submitted_at", "claim_edi_batches", ["submitted_at"]
    )

    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "billing_cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("billing_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "edi_batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("claim_edi_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("payer_name", sa.String(length=255), nullable=True),
        sa.Column("service_date", sa.Date(), nullable=True),
        sa.Column("total_charge", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="READY"),
        sa.Column("last_status_reason", sa.Text(), nullable=True),
        sa.Column("claim_control_number", sa.String(length=64), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.UniqueConstraint(
            "patient_id", "billing_cycle_id", name="uq_claim_patient_cycle"
        ),
    )
    op.create_index("ix_claims_tenant_id", "claims", ["tenant_id"])
    op.create_index("ix_claims_patient_id", "claims", ["patient_id"])
    op.create_index("ix_claims_billing_cycle_id", "claims", ["billing_cycle_id"])
    op.create_index("ix_claims_edi_batch_id", "claims", ["edi_batch_id"])
    op.create_index("ix_claims_status", "claims", ["status"])
    op.create_index("ix_claims_claim_control_number", "claims", ["claim_control_number"])
    op.create_index("ix_claim_tenant_status", "claims", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_claim_tenant_status", table_name="claims")
    op.drop_index("ix_claims_claim_control_number", table_name="claims")
    op.drop_index("ix_claims_status", table_name="claims")
    op.drop_index("ix_claims_edi_batch_id", table_name="claims")
    op.drop_index("ix_claims_billing_cycle_id", table_name="claims")
    op.drop_index("ix_claims_patient_id", table_name="claims")
    op.drop_index("ix_claims_tenant_id", table_name="claims")
    op.drop_table("claims")

    op.drop_index("ix_claim_edi_batches_submitted_at", table_name="claim_edi_batches")
    op.drop_index("ix_claim_edi_batches_batch_number", table_name="claim_edi_batches")
    op.drop_index("ix_claim_edi_batch_tenant_status", table_name="claim_edi_batches")
    op.drop_index("ix_claim_edi_batches_tenant_id", table_name="claim_edi_batches")
    op.drop_table("claim_edi_batches")
