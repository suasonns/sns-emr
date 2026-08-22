"""add tenant_id to patient_code_statuses

Revision ID: e2a7b8c9d0f1
Revises: c4d5e6f7a8b9
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e2a7b8c9d0f1"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable first so any existing rows (e.g. smoke-test data) don't
    # break the ALTER, then backfill from the owning patient, then enforce
    # NOT NULL - matching the tenant-scoping pattern used by
    # patient_diagnoses / patient_allergies.
    op.add_column(
        "patient_code_statuses",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute(
        """
        UPDATE patient_code_statuses AS pcs
        SET tenant_id = p.tenant_id
        FROM patients AS p
        WHERE pcs.patient_id = p.id
          AND pcs.tenant_id IS NULL
        """
    )

    op.alter_column(
        "patient_code_statuses",
        "tenant_id",
        nullable=False,
    )

    op.create_foreign_key(
        "fk_patient_code_statuses_tenant_id",
        "patient_code_statuses",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_patient_code_statuses_tenant_id",
        "patient_code_statuses",
        ["tenant_id"],
        unique=False,
    )

    # --- Migration Strategy: backfill existing facesheet.code_status ---
    # For every patient with a non-blank legacy facesheet code_status and
    # NO existing patient_code_statuses row, create one is_current=true
    # record so history starts from the real prior value instead of
    # silently defaulting new patients to "no code status on file".
    op.execute(
        """
        INSERT INTO patient_code_statuses
            (id, tenant_id, patient_id, code_status, effective_date,
             source, notes, is_current, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            CASE
                WHEN pf.code_status ILIKE '%%dnr%%' OR pf.code_status ILIKE '%%dni%%'
                    THEN 'DNR_DNI'
                WHEN pf.code_status ILIKE '%%comfort%%'
                    THEN 'COMFORT_MEASURES_ONLY'
                WHEN pf.code_status ILIKE '%%full%%'
                    THEN 'FULL_CODE'
                ELSE 'OTHER'
            END,
            COALESCE(pf.updated_at::date, pf.created_at::date, CURRENT_DATE),
            'FACESHEET_MIGRATION',
            pf.code_status,
            true,
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.code_status IS NOT NULL
          AND btrim(pf.code_status) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_code_statuses AS pcs
              WHERE pcs.patient_id = pf.patient_id
          )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_patient_code_statuses_tenant_id", table_name="patient_code_statuses")
    op.drop_constraint(
        "fk_patient_code_statuses_tenant_id",
        "patient_code_statuses",
        type_="foreignkey",
    )
    op.drop_column("patient_code_statuses", "tenant_id")
