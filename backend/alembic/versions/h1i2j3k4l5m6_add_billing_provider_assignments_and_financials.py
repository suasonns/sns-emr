"""add billing provider assignments and financials toggle

Revision ID: h1i2j3k4l5m6
Revises: g1h2i3j4k5l6
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, Sequence[str], None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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

    op.create_table(
        "billing_provider_organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("organization_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_billing_provider_organization_status_valid",
        ),
        sa.UniqueConstraint("name", name="uq_billing_provider_organizations_name"),
    )
    op.create_index(
        "ix_billing_provider_organizations_name",
        "billing_provider_organizations",
        ["name"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_organizations_organization_type",
        "billing_provider_organizations",
        ["organization_type"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_organizations_status",
        "billing_provider_organizations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_org_type_status",
        "billing_provider_organizations",
        ["organization_type", "status"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_organizations_created_by",
        "billing_provider_organizations",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_organizations_updated_by",
        "billing_provider_organizations",
        ["updated_by"],
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

    op.create_table(
        "billing_provider_agency_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "billing_provider_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("billing_provider_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "relationship_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("effective_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "financials_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
            "relationship_status IN ('ACTIVE', 'SUSPENDED', 'TERMINATED', 'PENDING')",
            name="ck_billing_provider_assignment_relationship_status_valid",
        ),
        sa.CheckConstraint(
            "effective_end_at IS NULL OR effective_end_at >= effective_start_at",
            name="ck_billing_provider_assignment_effective_window_valid",
        ),
    )
    op.create_index(
        "ix_bp_assignments_org_id",
        "billing_provider_agency_assignments",
        ["billing_provider_organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_tenant_id",
        "billing_provider_agency_assignments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_relationship_status",
        "billing_provider_agency_assignments",
        ["relationship_status"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_financials_enabled",
        "billing_provider_agency_assignments",
        ["financials_enabled"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_assignment_tenant_status",
        "billing_provider_agency_assignments",
        ["tenant_id", "relationship_status"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_assignment_org_status",
        "billing_provider_agency_assignments",
        ["billing_provider_organization_id", "relationship_status"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_created_by",
        "billing_provider_agency_assignments",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_assignments_updated_by",
        "billing_provider_agency_assignments",
        ["updated_by"],
        unique=False,
    )

    op.create_table(
        "billing_provider_agency_service_scopes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("billing_provider_agency_assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "scope IN ('BILLING_READINESS', 'CLAIMS', 'PAYMENT_POSTING', 'PAYMENT_RECONCILIATION', 'FACILITY_COLLECTIONS', 'DENIALS_APPEALS', 'AUTHORIZATION', 'FINANCIAL_MONITORING', 'CAP_MONITORING')",
            name="ck_billing_provider_assignment_scope_valid",
        ),
        sa.UniqueConstraint("assignment_id", "scope", name="uq_billing_provider_assignment_scope"),
    )
    op.create_index(
        "ix_billing_provider_agency_service_scopes_assignment_id",
        "billing_provider_agency_service_scopes",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_agency_service_scopes_scope",
        "billing_provider_agency_service_scopes",
        ["scope"],
        unique=False,
    )
    op.create_index(
        "ix_billing_provider_scope_assignment_scope",
        "billing_provider_agency_service_scopes",
        ["assignment_id", "scope"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_provider_scope_assignment_scope",
        table_name="billing_provider_agency_service_scopes",
    )
    op.drop_index(
        "ix_billing_provider_agency_service_scopes_scope",
        table_name="billing_provider_agency_service_scopes",
    )
    op.drop_index(
        "ix_billing_provider_agency_service_scopes_assignment_id",
        table_name="billing_provider_agency_service_scopes",
    )
    op.drop_table("billing_provider_agency_service_scopes")

    op.drop_index(
        "ix_billing_provider_agency_assignments_updated_by",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_agency_assignments_created_by",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_assignment_org_status",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_assignment_tenant_status",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_agency_assignments_financials_enabled",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_agency_assignments_relationship_status",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_billing_provider_agency_assignments_tenant_id",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_index(
        "ix_bp_assignments_org_id",
        table_name="billing_provider_agency_assignments",
    )
    op.drop_table("billing_provider_agency_assignments")

    op.drop_index("ix_users_billing_provider_organization_id", table_name="users")
    op.drop_constraint(
        "fk_users_billing_provider_organization_id",
        "users",
        type_="foreignkey",
    )
    op.drop_column("users", "billing_provider_organization_id")

    op.drop_index(
        "ix_billing_provider_organizations_updated_by",
        table_name="billing_provider_organizations",
    )
    op.drop_index(
        "ix_billing_provider_organizations_created_by",
        table_name="billing_provider_organizations",
    )
    op.drop_index(
        "ix_billing_provider_org_type_status",
        table_name="billing_provider_organizations",
    )
    op.drop_index(
        "ix_billing_provider_organizations_status",
        table_name="billing_provider_organizations",
    )
    op.drop_index(
        "ix_billing_provider_organizations_organization_type",
        table_name="billing_provider_organizations",
    )
    op.drop_index(
        "ix_billing_provider_organizations_name",
        table_name="billing_provider_organizations",
    )
    op.drop_table("billing_provider_organizations")

    op.drop_index(op.f("ix_tenants_financials_enabled"), table_name="tenants")
    op.drop_column("tenants", "financials_enabled")
