"""phase2_a_audit_fields

Adds audit fields in a controlled, compliance-safe manner.

- created_at  (TIMESTAMPTZ, nullable, default now())
- updated_at  (TIMESTAMPTZ, nullable, default now())
- created_by  (UUID, nullable, NO FK to avoid cycles)

Scope: ONLY ORM-managed tables (24-table boundary)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2611c820fc34"
down_revision: Union[str, Sequence[str], None] = "c06467c1e1cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -------------------------------------------------------------------
# ORM TABLE SCOPE (INTENTIONAL)
# -------------------------------------------------------------------
TARGET_TABLES = [
    "assessment_discrepancies",
    "assessment_references",
    "assessments",
    "benefit_periods",
    "document_idg_resolution",
    "document_notifications",
    "document_records",
    "drug_aliases",
    "dx_primary_policies",
    "eligibility_assessments",
    "eligibility_decisions",
    "eligibility_rulesets",
    "idg_md_attestations",
    "idg_notes",
    "idg_reviews",
    "idg_signatures",
    "interfaces",
    "patients",
    "roles",
    "survey_access",
    "tasks",
    "tenants",
    "users",
    "visits",
]


# -------------------------------------------------------------------
# Helpers (PostgreSQL-safe, idempotent, rebuild-safe)
# -------------------------------------------------------------------
def _add_column_if_missing(table_name: str, column_sql: str, column_name: str) -> None:
    """
    Enterprise-grade, rebuild-safe:
    - Only alters if the table exists in this rebuild path
    - Only adds column if missing
    """
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                -- Table must exist
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    -- Column must be missing
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name   = :t
                          AND column_name  = :c
                    ) THEN
                        EXECUTE format(
                            'ALTER TABLE public.%I ADD COLUMN %s',
                            :t,
                            :sql
                        );
                    END IF;
                END IF;
            END $$;
            """
        ).bindparams(t=table_name, c=column_name, sql=column_sql)
    )


def _create_index_if_missing(index_name: str, table_name: str, column_name: str) -> None:
    """
    Enterprise-grade, rebuild-safe:
    - Only creates index if table exists
    - Only creates index if missing
    """
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                -- Table must exist
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                          AND indexname  = :ix
                    ) THEN
                        EXECUTE format(
                            'CREATE INDEX %I ON public.%I (%I)',
                            :ix,
                            :t,
                            :c
                        );
                    END IF;
                END IF;
            END $$;
            """
        ).bindparams(ix=index_name, t=table_name, c=column_name)
    )


# -------------------------------------------------------------------
# Upgrade
# -------------------------------------------------------------------
def upgrade() -> None:
    created_at_sql = "created_at TIMESTAMPTZ NULL DEFAULT now()"
    updated_at_sql = "updated_at TIMESTAMPTZ NULL DEFAULT now()"
    created_by_sql = "created_by UUID NULL"

    for table in TARGET_TABLES:
        _add_column_if_missing(table, created_at_sql, "created_at")
        _add_column_if_missing(table, updated_at_sql, "updated_at")
        _add_column_if_missing(table, created_by_sql, "created_by")

        _create_index_if_missing(
            f"ix_{table}_created_by",
            table,
            "created_by",
        )


# -------------------------------------------------------------------
# Downgrade
# -------------------------------------------------------------------
def downgrade() -> None:
    # Forward-only by design.
    pass