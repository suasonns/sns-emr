"""add patient_contacts

Revision ID: a1c2d3e4f5b6
Revises: f3b8c9d0e1a2
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1c2d3e4f5b6"
down_revision: Union[str, Sequence[str], None] = "f3b8c9d0e1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("relationship_to_patient", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="FACESHEET"),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("patient_id", "role", name="uq_patient_contact_role"),
    )

    op.create_index(
        "ix_patient_contacts_patient_id",
        "patient_contacts",
        ["patient_id"],
    )
    op.create_index(
        "ix_patient_contacts_tenant_id",
        "patient_contacts",
        ["tenant_id"],
    )
    op.create_index(
        "ix_patient_contacts_patient_role",
        "patient_contacts",
        ["patient_id", "role"],
    )

    # --- Migration Strategy: backfill existing facesheet contact columns ---
    # For every patient with non-blank legacy responsible-party/emergency-
    # contact free text and NO existing shared row for that role, create
    # one so RNICA/ACP immediately see the real prior values instead of
    # "no contact on file".
    op.execute(
        """
        INSERT INTO patient_contacts
            (id, tenant_id, patient_id, role, name, relationship_to_patient, phone,
             source, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            'RESPONSIBLE_PARTY',
            pf.responsible_party_name,
            pf.responsible_party_relationship,
            pf.responsible_party_phone,
            'FACESHEET_MIGRATION',
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.responsible_party_name IS NOT NULL
          AND btrim(pf.responsible_party_name) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_contacts AS pc
              WHERE pc.patient_id = pf.patient_id AND pc.role = 'RESPONSIBLE_PARTY'
          )
        """
    )

    op.execute(
        """
        INSERT INTO patient_contacts
            (id, tenant_id, patient_id, role, name, relationship_to_patient, phone,
             source, created_at)
        SELECT
            gen_random_uuid(),
            pf.tenant_id,
            pf.patient_id,
            'EMERGENCY_CONTACT',
            pf.emergency_contact_name,
            pf.emergency_contact_relationship,
            pf.emergency_contact_phone,
            'FACESHEET_MIGRATION',
            COALESCE(pf.updated_at, pf.created_at, now())
        FROM patient_facesheet AS pf
        WHERE pf.emergency_contact_name IS NOT NULL
          AND btrim(pf.emergency_contact_name) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM patient_contacts AS pc
              WHERE pc.patient_id = pf.patient_id AND pc.role = 'EMERGENCY_CONTACT'
          )
        """
    )


def downgrade() -> None:
    op.drop_table("patient_contacts")
