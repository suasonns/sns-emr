"""phase2_b3_fk_realignment_core

Revision ID: 533c2ae752e8
Revises: 68f96969feb7
Create Date: 2026-05-27 12:19:42.606193

Adds safe FK integrity across ORM tables:
- tenant_id -> tenants.id
- created_by -> users.id

EXCLUDES tenants.created_by to avoid cycles.

Forward-only, guarded, enterprise-safe.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "533c2ae752e8"
down_revision: Union[str, Sequence[str], None] = "68f96969feb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORM_TABLES = [
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


def _column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    row = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :t
              AND column_name = :c
            """
        ),
        {"t": table_name, "c": column_name},
    ).first()
    return row is not None


def _add_fk_if_missing(
    table_name: str,
    constraint_name: str,
    column_name: str,
    ref_table: str,
    ref_column: str,
) -> None:
    if not _column_exists(table_name, column_name):
        return

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = :con) THEN
                    EXECUTE format(
                        'ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES public.%I (%I) ON DELETE RESTRICT',
                        :t, :con, :col, :rt, :rc
                    );
                END IF;
            END
            $$;
            """
        ).bindparams(con=constraint_name, t=table_name, col=column_name, rt=ref_table, rc=ref_column)
    )


def upgrade() -> None:
    # tenant_id -> tenants.id
    for t in ORM_TABLES:
        if t == "tenants":
            continue
        _add_fk_if_missing(t, f"fk_{t}_tenant_id", "tenant_id", "tenants", "id")

    # created_by -> users.id (EXCLUDE tenants to avoid cycle)
    for t in ORM_TABLES:
        if t == "tenants":
            continue
        _add_fk_if_missing(t, f"fk_{t}_created_by", "created_by", "users", "id")


def downgrade() -> None:
    # Forward-only by design.
    pass