"""add patient_physician_assignments

Revision ID: f3b8c9d0e1a2
Revises: e2a7b8c9d0f1
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f3b8c9d0e1a2"
down_revision: Union[str, Sequence[str], None] = "e2a7b8c9d0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_physician_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("physician_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("physicians.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("fax", sa.String(length=64), nullable=True),
        sa.Column("npi", sa.String(length=32), nullable=True),
        sa.Column("will_follow_in_hospice", sa.Boolean(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="FACESHEET"),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("patient_id", "role", name="uq_patient_physician_role"),
    )

    op.create_index(
        "ix_patient_physician_assignments_patient_id",
        "patient_physician_assignments",
        ["patient_id"],
    )
    op.create_index(
        "ix_patient_physician_assignments_tenant_id",
        "patient_physician_assignments",
        ["tenant_id"],
    )
    op.create_index(
        "ix_patient_physician_assignments_patient_role",
        "patient_physician_assignments",
        ["patient_id", "role"],
    )

    # --- Migration Strategy: backfill existing facesheet physician columns ---
    # For every patient with non-blank legacy attending/medical-director/
    # associate-medical-director free text and NO existing shared row for
    # that role, create one so Orders/CTI/Care Overview immediately see the
    # real prior values instead of "no physician on file".
    op.execute(
        """
        INSERT INTO patient_physician_assignments
            (id, tenant_id, patient_id, role, name, address, phone, fax, npi,
             will_follow_in_hospice, source, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            'ATTENDING',
            pf.attending_physician_name,
            pf.attending_physician_address,
            pf.attending_physician_phone,
            pf.attending_physician_fax,
            pf.attending_physician_npi,
            pf.attending_physician_following,
            'FACESHEET_MIGRATION',
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.attending_physician_name IS NOT NULL
          AND btrim(pf.attending_physician_name) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_physician_assignments AS ppa
              WHERE ppa.patient_id = pf.patient_id AND ppa.role = 'ATTENDING'
          )
        """
    )

    op.execute(
        """
        INSERT INTO patient_physician_assignments
            (id, tenant_id, patient_id, role, name, address, phone, fax, npi,
             source, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            'MEDICAL_DIRECTOR',
            pf.medical_director_name,
            pf.medical_director_address,
            pf.medical_director_phone,
            pf.medical_director_fax,
            pf.medical_director_npi,
            'FACESHEET_MIGRATION',
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.medical_director_name IS NOT NULL
          AND btrim(pf.medical_director_name) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_physician_assignments AS ppa
              WHERE ppa.patient_id = pf.patient_id AND ppa.role = 'MEDICAL_DIRECTOR'
          )
        """
    )

    op.execute(
        """
        INSERT INTO patient_physician_assignments
            (id, tenant_id, patient_id, role, name, npi, source, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            'ASSOCIATE_MEDICAL_DIRECTOR',
            pf.associate_medical_director_name,
            pf.associate_medical_director_npi,
            'FACESHEET_MIGRATION',
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.associate_medical_director_name IS NOT NULL
          AND btrim(pf.associate_medical_director_name) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_physician_assignments AS ppa
              WHERE ppa.patient_id = pf.patient_id AND ppa.role = 'ASSOCIATE_MEDICAL_DIRECTOR'
          )
        """
    )


def downgrade() -> None:
    op.drop_table("patient_physician_assignments")
