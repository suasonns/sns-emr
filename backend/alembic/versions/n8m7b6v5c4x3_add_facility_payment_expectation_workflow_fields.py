"""add facility payment expectation workflow fields

Revision ID: n8m7b6v5c4x3
Revises: i2j3k4l5m6n7
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "n8m7b6v5c4x3"
down_revision: Union[str, Sequence[str], None] = "i2j3k4l5m6n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "facility_payment_expectations",
        sa.Column(
            "due_date_source",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'SYSTEM_FALLBACK'"),
        ),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column(
            "payment_term_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column("contract_reference", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column(
            "cancelled_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column(
            "row_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "facility_payment_expectations",
        sa.Column("client_request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "facility_payment_allocations",
        sa.Column(
            "flagged_for_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "facility_payment_allocations",
        sa.Column("flagged_reason", sa.Text(), nullable=True),
    )

    op.execute(
        """
        UPDATE facility_payment_expectations
        SET due_date = CASE
                WHEN due_date IS NULL AND service_period_end IS NOT NULL THEN service_period_end + 30
                ELSE due_date
            END,
            due_date_source = CASE
                WHEN due_date IS NOT NULL THEN 'AUTHORIZED_MANUAL_ENTRY'
                WHEN service_period_end IS NOT NULL THEN 'SYSTEM_FALLBACK'
                ELSE 'SYSTEM_FALLBACK'
            END,
            payment_term_verified = CASE
                WHEN due_date IS NOT NULL THEN true
                ELSE false
            END
        """
    )
    op.execute(
        """
        UPDATE facility_payment_expectations
        SET source = CASE
            WHEN source = 'MANUAL' THEN 'AUTHORIZED_MANUAL_ENTRY'
            WHEN source IN (
                'VERIFIED_PAYER_RULE',
                'VERIFIED_CONTRACT',
                'VERIFIED_AUTHORIZATION',
                'VERIFIED_FACILITY_ARRANGEMENT',
                'AUTHORIZED_MANUAL_ENTRY',
                'VERIFIED_IMPORT',
                'NOT_VERIFIED'
            ) THEN source
            ELSE 'NOT_VERIFIED'
        END
        """
    )

    op.alter_column(
        "facility_payment_expectations",
        "status",
        existing_type=sa.String(length=32),
        server_default=sa.text("'DRAFT'"),
    )
    op.alter_column(
        "facility_payment_expectations",
        "source",
        existing_type=sa.String(length=32),
        server_default=sa.text("'NOT_VERIFIED'"),
    )

    op.create_check_constraint(
        "ck_facility_payment_expectation_status_valid",
        "facility_payment_expectations",
        "status IN ('DRAFT', 'ACTIVE', 'PARTIALLY_PAID', 'PAID', 'OVERPAID', 'NOT_VERIFIED', 'SUPERSEDED', 'CANCELLED', 'CLOSED')",
    )
    op.create_check_constraint(
        "ck_facility_payment_expectation_source_valid",
        "facility_payment_expectations",
        "source IN ('VERIFIED_PAYER_RULE', 'VERIFIED_CONTRACT', 'VERIFIED_AUTHORIZATION', 'VERIFIED_FACILITY_ARRANGEMENT', 'AUTHORIZED_MANUAL_ENTRY', 'VERIFIED_IMPORT', 'NOT_VERIFIED')",
    )
    op.create_check_constraint(
        "ck_facility_payment_expectation_due_date_source_valid",
        "facility_payment_expectations",
        "due_date_source IN ('VERIFIED_PAYER_RULE', 'VERIFIED_CONTRACT', 'VERIFIED_AUTHORIZATION', 'TENANT_CONFIGURED_TERM', 'AUTHORIZED_MANUAL_ENTRY', 'SYSTEM_FALLBACK')",
    )
    op.create_index(
        "ix_facility_payment_expectation_tenant_patient_client_request",
        "facility_payment_expectations",
        ["tenant_id", "patient_id", "client_request_id"],
        unique=True,
        postgresql_where=sa.text("client_request_id IS NOT NULL"),
    )


def downgrade() -> None:
    raise NotImplementedError("Forward-only migration.")
