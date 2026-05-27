"""repair tasks tenant_id to uuid

Revision ID: 55edc63b30d2
Revises: a0bb66070697
Create Date: 2026-05-26 20:26:51.573137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '55edc63b30d2'
down_revision: Union[str, Sequence[str], None] = 'a0bb66070697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()

    # ------------------------------------------------------------
    # Capture trigger definition (so we can recreate it after ALTER)
    # ------------------------------------------------------------
    trigger_def = None
    row = bind.execute(sa.text("""
        SELECT pg_get_triggerdef(t.oid, true) AS trgdef
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'tasks'
          AND n.nspname = 'public'
          AND t.tgname = 'trg_no_tenant_id_update_tasks'
          AND NOT t.tgisinternal
    """)).first()
    if row and row[0]:
        trigger_def = row[0]

    # ------------------------------------------------------------
    # Drop RLS policy + trigger that depend on tasks.tenant_id
    # ------------------------------------------------------------
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tasks ON tasks;")

    if trigger_def:
        op.execute("DROP TRIGGER IF EXISTS trg_no_tenant_id_update_tasks ON tasks;")

    # ------------------------------------------------------------
    # ALTER tenant_id type
    # ------------------------------------------------------------
    op.alter_column(
        "tasks",
        "tenant_id",
        existing_type=sa.String(),
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using="tenant_id::uuid",
        existing_nullable=True,
    )

    # ------------------------------------------------------------
    # Re-enable RLS + recreate policy (cast-safe for UUID column)
    # ------------------------------------------------------------
    op.execute("ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_tasks
        ON tasks
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
        """
    )

    # ------------------------------------------------------------
    # Recreate trigger (if it existed)
    # ------------------------------------------------------------
    if trigger_def:
        # pg_get_triggerdef returns CREATE TRIGGER ... statement
        op.execute(trigger_def)


def downgrade():
    bind = op.get_bind()

    # Capture trigger definition (optional)
    trigger_def = None
    row = bind.execute(sa.text("""
        SELECT pg_get_triggerdef(t.oid, true) AS trgdef
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'tasks'
          AND n.nspname = 'public'
          AND t.tgname = 'trg_no_tenant_id_update_tasks'
          AND NOT t.tgisinternal
    """)).first()
    if row and row[0]:
        trigger_def = row[0]

    # Drop policy + trigger prior to type change
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tasks ON tasks;")
    op.execute("DROP TRIGGER IF EXISTS trg_no_tenant_id_update_tasks ON tasks;")

    # Convert back uuid -> varchar
    op.alter_column(
        "tasks",
        "tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(),
        postgresql_using="tenant_id::text",
        existing_nullable=True,
    )

    # Re-enable RLS + recreate policy for varchar tenant_id
    op.execute("ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation_tasks
        ON tasks
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
        """
    )

    # Recreate trigger if we captured it
    if trigger_def:
        op.execute(trigger_def)