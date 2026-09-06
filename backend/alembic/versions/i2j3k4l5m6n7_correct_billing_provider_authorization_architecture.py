"""correct billing provider authorization architecture

Revision ID: i2j3k4l5m6n7
Revises: h1i2j3k4l5m6
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
import uuid

revision: str = "i2j3k4l5m6n7"
down_revision: Union[str, Sequence[str], None] = "h1i2j3k4l5m6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_provider_organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "billing_provider_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("billing_provider_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "membership_role",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'MEMBER'"),
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("effective_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "membership_role IN ('MEMBER', 'ADMIN')",
            name="ck_billing_provider_membership_role_valid",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="ck_billing_provider_membership_status_valid",
        ),
        sa.CheckConstraint(
            "effective_end_at IS NULL OR effective_end_at >= effective_start_at",
            name="ck_billing_provider_membership_effective_window_valid",
        ),
    )
    op.create_index(
        "ix_bp_org_memberships_org_id",
        "billing_provider_organization_memberships",
        ["billing_provider_organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_user_id",
        "billing_provider_organization_memberships",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_status",
        "billing_provider_organization_memberships",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_created_by",
        "billing_provider_organization_memberships",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_updated_by",
        "billing_provider_organization_memberships",
        ["updated_by"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_org_status",
        "billing_provider_organization_memberships",
        ["billing_provider_organization_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_bp_org_memberships_user_status",
        "billing_provider_organization_memberships",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "uq_bp_org_memberships_active_pair",
        "billing_provider_organization_memberships",
        ["user_id", "billing_provider_organization_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    bind = op.get_bind()
    legacy_memberships = bind.execute(
        sa.text(
            """
            SELECT id, billing_provider_organization_id
            FROM users
            WHERE billing_provider_organization_id IS NOT NULL
            """
        )
    ).mappings()
    for row in legacy_memberships:
        bind.execute(
            sa.text(
                """
                INSERT INTO billing_provider_organization_memberships (
                    id,
                    billing_provider_organization_id,
                    user_id,
                    membership_role,
                    status,
                    effective_start_at,
                    created_at
                )
                VALUES (
                    :id,
                    :billing_provider_organization_id,
                    :user_id,
                    'MEMBER',
                    'ACTIVE',
                    now(),
                    now()
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "billing_provider_organization_id": str(
                    row["billing_provider_organization_id"]
                ),
                "user_id": str(row["id"]),
            },
        )

    op.drop_constraint(
        "ck_billing_provider_assignment_scope_valid",
        "billing_provider_agency_service_scopes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_billing_provider_assignment_scope_valid",
        "billing_provider_agency_service_scopes",
        "scope IN ('BILLING_READINESS', 'CLAIMS', 'NOE_TRACKING', 'ELIGIBILITY', 'AUTHORIZATION_TRACKING', 'PAYMENT_POSTING', 'PAYMENT_RECONCILIATION', 'FACILITY_COLLECTIONS', 'CREDIT_BALANCES', 'AGING_REPORT', 'DENIALS_APPEALS', 'EDI', 'BILLING_REPORTS', 'CAP_MONITORING', 'FINANCIAL_MONITORING')",
    )

    op.execute("DROP INDEX IF EXISTS ix_billing_provider_agency_assignments_financials_enabled")
    op.execute(
        "ALTER TABLE billing_provider_agency_assignments DROP COLUMN financials_enabled"
    )

    op.execute("DROP INDEX IF EXISTS ix_users_billing_provider_organization_id")
    op.drop_constraint(
        "fk_users_billing_provider_organization_id",
        "users",
        type_="foreignkey",
    )
    op.execute("ALTER TABLE users DROP COLUMN billing_provider_organization_id")

    op.execute("DROP INDEX IF EXISTS ix_tenants_financials_enabled")
    op.execute("ALTER TABLE tenants DROP COLUMN financials_enabled")


def downgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "financials_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        op.f("ix_tenants_financials_enabled"),
        "tenants",
        ["financials_enabled"],
        unique=False,
    )

    op.add_column(
        "users",
        sa.Column("billing_provider_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_billing_provider_organization_id",
        "users",
        "billing_provider_organizations",
        ["billing_provider_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_users_billing_provider_organization_id",
        "users",
        ["billing_provider_organization_id"],
        unique=False,
    )

    op.add_column(
        "billing_provider_agency_assignments",
        sa.Column(
            "financials_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_financials_enabled",
        "billing_provider_agency_assignments",
        ["financials_enabled"],
        unique=False,
    )

    op.drop_constraint(
        "ck_billing_provider_assignment_scope_valid",
        "billing_provider_agency_service_scopes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_billing_provider_assignment_scope_valid",
        "billing_provider_agency_service_scopes",
        "scope IN ('BILLING_READINESS', 'CLAIMS', 'PAYMENT_POSTING', 'PAYMENT_RECONCILIATION', 'FACILITY_COLLECTIONS', 'DENIALS_APPEALS', 'AUTHORIZATION', 'FINANCIAL_MONITORING', 'CAP_MONITORING')",
    )

    op.drop_index(
        "uq_bp_org_memberships_active_pair",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_user_status",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_org_status",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_updated_by",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_created_by",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_status",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_user_id",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_index(
        "ix_bp_org_memberships_org_id",
        table_name="billing_provider_organization_memberships",
    )
    op.drop_table("billing_provider_organization_memberships")
