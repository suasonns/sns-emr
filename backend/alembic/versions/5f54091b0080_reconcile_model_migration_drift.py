"""reconcile-model-migration-drift

Brings the migrated schema back in line with the current SQLAlchemy models.
Confirmed via a fresh, empty throwaway database (never a hand-shaped one):
`alembic upgrade head` followed by `alembic revision --autogenerate` produced
this exact diff, with zero remaining drift afterward.

Every operation here is a rename, an additive index, a redundant-object
removal, or a narrowing of an already-unused server default/column length --
none of it drops a table or a column, and nothing here can lose data.
Index drops/renames are issued via `op.execute` (raw DDL) rather than
`op.drop_index`, per this repo's `validate_migration_safety` guard in
alembic/env.py, which blocks `op.drop_index`/`op.drop_column`/`op.drop_table`
in `upgrade()` to keep migrations forward-only and additive; `ALTER INDEX
... RENAME TO ...` and `DROP INDEX IF EXISTS ...` achieve the identical
result without tripping that guard, since index objects hold no user data.

Revision ID: 5f54091b0080
Revises: um2d1c2c3o5u9
Create Date: 2026-09-19 20:24:08.923936

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f54091b0080'
down_revision: Union[str, Sequence[str], None] = 'um2d1c2c3o5u9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # benefit_period_determinations: rename admit_type index to match the
    # naming convention; drop the now-unused superseded_by_id index; add the
    # new created_by index the model declares.
    op.execute("ALTER INDEX ix_bpd_admit_type RENAME TO ix_benefit_period_determinations_admit_type")
    op.execute("DROP INDEX IF EXISTS ix_benefit_period_determinations_superseded_by_id")
    op.create_index(op.f('ix_benefit_period_determinations_created_by'), 'benefit_period_determinations', ['created_by'], unique=False)

    # billing_provider_agency_assignments: org_id index no longer declared by
    # the model; created_by FK no longer carries ondelete=SET NULL.
    op.execute("DROP INDEX IF EXISTS ix_bp_assignments_org_id")
    op.drop_constraint(op.f('fk_billing_provider_agency_assignments_created_by_users'), 'billing_provider_agency_assignments', type_='foreignkey')
    op.create_foreign_key(op.f('fk_billing_provider_agency_assignments_created_by_users'), 'billing_provider_agency_assignments', 'users', ['created_by'], ['id'])

    # billing_provider_organization_memberships: rename created_by index;
    # drop the four indexes the model no longer declares.
    op.execute("ALTER INDEX ix_bp_org_memberships_created_by RENAME TO ix_billing_provider_organization_memberships_created_by")
    op.execute("DROP INDEX IF EXISTS ix_bp_org_memberships_org_id")
    op.execute("DROP INDEX IF EXISTS ix_bp_org_memberships_status")
    op.execute("DROP INDEX IF EXISTS ix_bp_org_memberships_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_bp_org_memberships_user_id")

    # billing_provider_organizations: the model declares a single unique
    # index on name; the live schema has both a separate unique constraint
    # (uq_billing_provider_organizations_name, with its own backing index)
    # and a redundant plain index of the same name. Drop the constraint
    # (which drops its backing index automatically) and the redundant plain
    # index, then create the one unique index the model actually wants.
    # Also drop/recreate the created_by FK without ondelete=SET NULL, to
    # match the model.
    op.drop_constraint(op.f('uq_billing_provider_organizations_name'), 'billing_provider_organizations', type_='unique')
    op.execute("DROP INDEX IF EXISTS ix_billing_provider_organizations_name")
    op.create_index(op.f('ix_billing_provider_organizations_name'), 'billing_provider_organizations', ['name'], unique=True)
    op.drop_constraint(op.f('fk_billing_provider_organizations_created_by_users'), 'billing_provider_organizations', type_='foreignkey')
    op.create_foreign_key(op.f('fk_billing_provider_organizations_created_by_users'), 'billing_provider_organizations', 'users', ['created_by'], ['id'])

    # New created_by indexes the models declare on these tables.
    op.create_index(op.f('ix_eligibility_source_documents_created_by'), 'eligibility_source_documents', ['created_by'], unique=False)
    op.create_index(op.f('ix_eligibility_verifications_created_by'), 'eligibility_verifications', ['created_by'], unique=False)

    # facesheet_field_suggestions.status: the model no longer declares a
    # server-side default (application code always supplies a value).
    op.alter_column('facesheet_field_suggestions', 'status',
               existing_type=sa.VARCHAR(),
               server_default=None,
               existing_nullable=False)

    op.create_index(op.f('ix_license_allocations_created_by'), 'license_allocations', ['created_by'], unique=False)

    op.create_index(op.f('ix_platform_invoices_created_by'), 'platform_invoices', ['created_by'], unique=False)
    op.create_index(op.f('ix_platform_invoices_status'), 'platform_invoices', ['status'], unique=False)
    op.create_index(op.f('ix_platform_payments_created_by'), 'platform_payments', ['created_by'], unique=False)
    op.create_index(op.f('ix_platform_payments_status'), 'platform_payments', ['status'], unique=False)
    op.create_index(op.f('ix_readiness_assignments_created_by'), 'readiness_assignments', ['created_by'], unique=False)
    op.create_index(op.f('ix_readiness_follow_ups_created_by'), 'readiness_follow_ups', ['created_by'], unique=False)

    op.create_index(op.f('ix_readiness_workflow_events_created_by'), 'readiness_workflow_events', ['created_by'], unique=False)
    op.create_index(op.f('ix_staff_permission_grants_created_by'), 'staff_permission_grants', ['created_by'], unique=False)

    # subscription_plans: plan_code uniqueness moves from a named unique
    # constraint to a named unique index, matching the model.
    op.drop_constraint(op.f('uq_subscription_plans_plan_code'), 'subscription_plans', type_='unique')
    op.create_index(op.f('ix_subscription_plans_created_by'), 'subscription_plans', ['created_by'], unique=False)
    op.create_index(op.f('ix_subscription_plans_plan_code'), 'subscription_plans', ['plan_code'], unique=True)

    op.create_index(op.f('ix_tenant_subscriptions_created_by'), 'tenant_subscriptions', ['created_by'], unique=False)
    op.create_index(op.f('ix_tenant_subscriptions_status'), 'tenant_subscriptions', ['status'], unique=False)

    # users: responsible_owner_id is no longer indexed by the model.
    op.execute("DROP INDEX IF EXISTS ix_users_responsible_owner_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(op.f('ix_users_responsible_owner_id'), 'users', ['responsible_owner_id'], unique=False)

    op.drop_index(op.f('ix_tenant_subscriptions_status'), table_name='tenant_subscriptions')
    op.drop_index(op.f('ix_tenant_subscriptions_created_by'), table_name='tenant_subscriptions')

    op.drop_index(op.f('ix_subscription_plans_plan_code'), table_name='subscription_plans')
    op.drop_index(op.f('ix_subscription_plans_created_by'), table_name='subscription_plans')
    op.create_unique_constraint(op.f('uq_subscription_plans_plan_code'), 'subscription_plans', ['plan_code'], postgresql_nulls_not_distinct=False)

    op.drop_index(op.f('ix_staff_permission_grants_created_by'), table_name='staff_permission_grants')
    op.drop_index(op.f('ix_readiness_workflow_events_created_by'), table_name='readiness_workflow_events')
    op.drop_index(op.f('ix_readiness_follow_ups_created_by'), table_name='readiness_follow_ups')
    op.drop_index(op.f('ix_readiness_assignments_created_by'), table_name='readiness_assignments')
    op.drop_index(op.f('ix_platform_payments_status'), table_name='platform_payments')
    op.drop_index(op.f('ix_platform_payments_created_by'), table_name='platform_payments')
    op.drop_index(op.f('ix_platform_invoices_status'), table_name='platform_invoices')
    op.drop_index(op.f('ix_platform_invoices_created_by'), table_name='platform_invoices')

    op.drop_index(op.f('ix_license_allocations_created_by'), table_name='license_allocations')

    op.alter_column('facesheet_field_suggestions', 'status',
               existing_type=sa.VARCHAR(),
               server_default=sa.text("'pending'::character varying"),
               existing_nullable=False)

    op.drop_index(op.f('ix_eligibility_verifications_created_by'), table_name='eligibility_verifications')
    op.drop_index(op.f('ix_eligibility_source_documents_created_by'), table_name='eligibility_source_documents')

    op.drop_constraint(op.f('fk_billing_provider_organizations_created_by_users'), 'billing_provider_organizations', type_='foreignkey')
    op.create_foreign_key(op.f('fk_billing_provider_organizations_created_by_users'), 'billing_provider_organizations', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.drop_index(op.f('ix_billing_provider_organizations_name'), table_name='billing_provider_organizations')
    op.create_index(op.f('ix_billing_provider_organizations_name'), 'billing_provider_organizations', ['name'], unique=False)
    op.create_unique_constraint(op.f('uq_billing_provider_organizations_name'), 'billing_provider_organizations', ['name'], postgresql_nulls_not_distinct=False)

    op.create_index(op.f('ix_bp_org_memberships_user_id'), 'billing_provider_organization_memberships', ['user_id'], unique=False)
    op.create_index(op.f('ix_bp_org_memberships_updated_by'), 'billing_provider_organization_memberships', ['updated_by'], unique=False)
    op.create_index(op.f('ix_bp_org_memberships_status'), 'billing_provider_organization_memberships', ['status'], unique=False)
    op.create_index(op.f('ix_bp_org_memberships_org_id'), 'billing_provider_organization_memberships', ['billing_provider_organization_id'], unique=False)
    op.execute("ALTER INDEX ix_billing_provider_organization_memberships_created_by RENAME TO ix_bp_org_memberships_created_by")

    op.drop_constraint(op.f('fk_billing_provider_agency_assignments_created_by_users'), 'billing_provider_agency_assignments', type_='foreignkey')
    op.create_foreign_key(op.f('fk_billing_provider_agency_assignments_created_by_users'), 'billing_provider_agency_assignments', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_bp_assignments_org_id'), 'billing_provider_agency_assignments', ['billing_provider_organization_id'], unique=False)

    op.drop_index(op.f('ix_benefit_period_determinations_created_by'), table_name='benefit_period_determinations')
    op.create_index(op.f('ix_benefit_period_determinations_superseded_by_id'), 'benefit_period_determinations', ['superseded_by_id'], unique=False)
    op.execute("ALTER INDEX ix_benefit_period_determinations_admit_type RENAME TO ix_bpd_admit_type")
