"""convert admissions to SOC model (non-destructive)

Revision ID: 67dd37c268ec
Revises: 7d0f52b0485a
Create Date: 2026-07-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "67dd37c268ec"
down_revision: Union[str, Sequence[str], None] = "7d0f52b0485a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------
    # STEP 1 — ADD ONLY THE MISSING SOC / COMPLIANCE FIELDS
    # --------------------------------------------------
    op.add_column("admissions", sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("election_signed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("certification_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("physician_order_signed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("initial_assessment_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("discharged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("admissions", sa.Column("discharge_reason", sa.Text(), nullable=True))

    # --------------------------------------------------
    # STEP 2 — ADD INDEXES
    # --------------------------------------------------
    op.create_index("ix_admissions_patient_id", "admissions", ["patient_id"])
    op.create_index("ix_admissions_tenant_id", "admissions", ["tenant_id"])
    op.create_index("ix_admissions_status", "admissions", ["status"])
    op.create_index("ix_admissions_patient_tenant", "admissions", ["tenant_id", "patient_id"])

    # --------------------------------------------------
    # STEP 3 — BACKFILL EXISTING ADMISSIONS FROM PATIENTS
    # --------------------------------------------------
    op.execute("""
        UPDATE admissions a
        SET
            soc_date = COALESCE(a.soc_date, p.soc_date),
            effective_date = COALESCE(
                a.effective_date,
                p.soc_date::timestamp with time zone,
                p.hospice_election_date::timestamp with time zone
            ),
            election_signed_at = COALESCE(a.election_signed_at, p.election_signed_at),
            admission_date = COALESCE(a.admission_date, p.on_service_at::timestamp without time zone),
            discharge_reason = COALESCE(a.discharge_reason, p.discharge_reason),
            discharged_at = COALESCE(a.discharged_at, p.discharge_date::timestamp with time zone)
        FROM patients p
        WHERE a.patient_id = p.id
    """)

    # --------------------------------------------------
    # STEP 4 — CREATE ADMISSIONS FOR ADMITTED PATIENTS WHO DON'T HAVE ONE
    # --------------------------------------------------
    op.execute("""
        INSERT INTO admissions (
            id,
            tenant_id,
            patient_id,
            admission_date,
            status,
            created_at,
            created_by,
            effective_date,
            soc_date,
            election_signed_at,
            discharge_reason,
            discharged_at,
            admission_authorized_at,
            admission_authorized_by
        )
        SELECT
            gen_random_uuid(),
            p.tenant_id,
            p.id,
            COALESCE(p.on_service_at::timestamp without time zone, NOW()::timestamp without time zone),
            'ADMITTED',
            NOW()::timestamp without time zone,
            p.created_by,
            COALESCE(
                p.soc_date::timestamp with time zone,
                p.hospice_election_date::timestamp with time zone
            ),
            p.soc_date::timestamp with time zone,
            p.election_signed_at,
            p.discharge_reason,
            p.discharge_date::timestamp with time zone,
            p.admission_authorized_at,
            p.admission_authorized_by
        FROM patients p
        LEFT JOIN admissions a ON a.patient_id = p.id
        WHERE p.admission_status = 'ADMITTED'
          AND a.id IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_admissions_patient_tenant", table_name="admissions")
    op.drop_index("ix_admissions_status", table_name="admissions")
    op.drop_index("ix_admissions_tenant_id", table_name="admissions")
    op.drop_index("ix_admissions_patient_id", table_name="admissions")

    op.drop_column("admissions", "discharge_reason")
    op.drop_column("admissions", "discharged_at")
    op.drop_column("admissions", "initial_assessment_completed_at")
    op.drop_column("admissions", "physician_order_signed_at")
    op.drop_column("admissions", "certification_completed_at")
    op.drop_column("admissions", "election_signed_at")
    op.drop_column("admissions", "effective_date")
