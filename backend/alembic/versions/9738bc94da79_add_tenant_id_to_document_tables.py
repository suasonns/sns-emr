"""add_tenant_id_to_document_tables

Revision ID: 9738bc94da79
Revises: 62cad5066584
Create Date: 2026-05-21 13:16:16.561379
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9738bc94da79"
down_revision: Union[str, Sequence[str], None] = "62cad5066584"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    """Rebuild-safe table existence check (public schema)."""
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:tbl) IS NOT NULL"),
            {"tbl": f"public.{table}"},
        ).scalar()
    )


def _has_column(table: str, column: str) -> bool:
    """Rebuild-safe column existence check. Returns False if table missing."""
    if not _table_exists(table):
        return False

    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema='public'
                      AND table_name=:t
                      AND column_name=:c
                )
                """
            ),
            {"t": table, "c": column},
        ).scalar()
    )


def _add_column_if_missing(table: str, column_sql: str, column_name: str) -> None:
    """Idempotent add column (only if table exists, only if column missing)."""
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema='public'
                          AND table_name=:t
                          AND column_name=:c
                    ) THEN
                        EXECUTE format('ALTER TABLE public.%I ADD COLUMN %s', :t, :sql);
                    END IF;
                END IF;
            END $$;
            """
        ).bindparams(t=table, c=column_name, sql=column_sql)
    )


def _create_fk_if_missing(constraint_name: str, ddl_sql: str) -> None:
    """Idempotent FK creation via pg_constraint check."""
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = :con) THEN
                    EXECUTE :ddl;
                END IF;
            END $$;
            """
        ).bindparams(con=constraint_name, ddl=ddl_sql)
    )


def upgrade() -> None:
    # We only operate on these tables if they exist in this rebuild path.
    dn_exists = _table_exists("document_notifications")
    dr_exists = _table_exists("document_records")
    dir_exists = _table_exists("document_idg_resolution")

    # 1) Add tenant_id columns (nullable first) — only if tables exist
    if dn_exists:
        _add_column_if_missing(
            "document_notifications",
            "tenant_id UUID NULL",
            "tenant_id",
        )

    if dir_exists:
        _add_column_if_missing(
            "document_idg_resolution",
            "tenant_id UUID NULL",
            "tenant_id",
        )

    # 2) Backfill tenant_id from document_records ONLY if both sides exist
    # (Backfill is safe to skip during rebuild when document_notifications doesn't exist yet.)
    if dn_exists and dr_exists and _has_column("document_notifications", "document_id") and _has_column("document_records", "tenant_id"):
        op.execute(
            sa.text(
                """
                UPDATE public.document_notifications dn
                SET tenant_id = dr.tenant_id
                FROM public.document_records dr
                WHERE dn.document_id = dr.id
                  AND dn.tenant_id IS NULL
                """
            )
        )

    if dir_exists and dr_exists and _has_column("document_idg_resolution", "document_id") and _has_column("document_records", "tenant_id"):
        op.execute(
            sa.text(
                """
                UPDATE public.document_idg_resolution r
                SET tenant_id = dr.tenant_id
                FROM public.document_records dr
                WHERE r.document_id = dr.id
                  AND r.tenant_id IS NULL
                """
            )
        )

    # 3) Enforce NOT NULL ONLY if table exists AND there are no NULLs remaining.
    # (Enterprise-safe: do not brick rebuilds when backfill cannot run yet.)
    if dn_exists and _has_column("document_notifications", "tenant_id"):
        remaining = op.get_bind().execute(
            sa.text("SELECT COUNT(*) FROM public.document_notifications WHERE tenant_id IS NULL")
        ).scalar()
        if remaining == 0:
            op.alter_column("document_notifications", "tenant_id", nullable=False, schema="public")

    if dir_exists and _has_column("document_idg_resolution", "tenant_id"):
        remaining = op.get_bind().execute(
            sa.text("SELECT COUNT(*) FROM public.document_idg_resolution WHERE tenant_id IS NULL")
        ).scalar()
        if remaining == 0:
            op.alter_column("document_idg_resolution", "tenant_id", nullable=False, schema="public")

    # 4) Add FK constraints only if the table exists and tenant_id exists
    if dn_exists and _has_column("document_notifications", "tenant_id"):
        _create_fk_if_missing(
            "fk_document_notifications_tenant",
            """
            ALTER TABLE public.document_notifications
              ADD CONSTRAINT fk_document_notifications_tenant
              FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
              ON DELETE CASCADE
            """,
        )
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_document_notifications_tenant_id "
                "ON public.document_notifications(tenant_id)"
            )
        )

    if dir_exists and _has_column("document_idg_resolution", "tenant_id"):
        _create_fk_if_missing(
            "fk_document_idg_resolution_tenant",
            """
            ALTER TABLE public.document_idg_resolution
              ADD CONSTRAINT fk_document_idg_resolution_tenant
              FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
              ON DELETE CASCADE
            """,
        )
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_document_idg_resolution_tenant_id "
                "ON public.document_idg_resolution(tenant_id)"
            )
        )

        # Unique index only if the table exists and columns exist
        if _has_column("document_idg_resolution", "document_id"):
            op.execute(
                sa.text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_document_idg_resolution_tenant_document "
                    "ON public.document_idg_resolution(tenant_id, document_id)"
                )
            )


def downgrade() -> None:
    # Conservative rollback (DEV-only). All operations guarded.

    if _table_exists("document_idg_resolution"):
        op.execute(sa.text("DROP INDEX IF EXISTS ux_document_idg_resolution_tenant_document"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_document_idg_resolution_tenant_id"))
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_idg_resolution_tenant') THEN
                    ALTER TABLE public.document_idg_resolution DROP CONSTRAINT fk_document_idg_resolution_tenant;
                  END IF;
                END $$;
                """
            )
        )
        if _has_column("document_idg_resolution", "tenant_id"):
            op.drop_column("document_idg_resolution", "tenant_id", schema="public")

    if _table_exists("document_notifications"):
        op.execute(sa.text("DROP INDEX IF EXISTS ix_document_notifications_tenant_id"))
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_notifications_tenant') THEN
                    ALTER TABLE public.document_notifications DROP CONSTRAINT fk_document_notifications_tenant;
                  END IF;
                END $$;
                """
            )
        )
        if _has_column("document_notifications", "tenant_id"):
            op.drop_column("document_notifications", "tenant_id", schema="public")
