"""add clinical notes and incident reports

Revision ID: e8ddd8217e52
Revises: 6a28adab8591
Create Date: 2026-06-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e8ddd8217e52"
down_revision: Union[str, Sequence[str], None] = "6a28adab8591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =========================================================
# HELPERS
# =========================================================

def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names(schema="public")


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    for idx in inspector.get_indexes(table_name, schema="public"):
        if idx.get("name") == index_name:
            return True
    return False


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    sql = sa.text(
        """
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
          AND t.relname = :table_name
          AND c.conname = :constraint_name
        LIMIT 1
        """
    )
    return bind.execute(
        sql,
        {
            "table_name": table_name,
            "constraint_name": constraint_name,
        },
    ).scalar() is not None


# =========================================================
# IMPORTANT ENTERPRISE RULE
# =========================================================
# DO NOT ALTER existing clinical_notes here.
# Reason:
# - current DB user is not table owner
# - ALTER TABLE on owner-owned existing table will fail
# - this migration must remain safe in development
#
# Therefore:
# - if clinical_notes does not exist, create it
# - if clinical_notes already exists, SKIP all modifications
#   and only create incident_reports safely
# =========================================================


def _create_clinical_notes_if_missing() -> None:
    if _table_exists("clinical_notes"):
        return

    op.create_table(
        "clinical_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Core classification
        sa.Column("care_level", sa.String(length=16), nullable=False),      # RC | CC | GIP | RSP
        sa.Column("visit_type", sa.String(length=32), nullable=False),      # ROUTINE | PRN | CRISIS | ADMISSION | RECERT | F2F | etc.
        sa.Column("visit_origin", sa.String(length=32), nullable=False),    # SCHEDULED | UNSCHEDULED | TRIAGE | PHONE_CALL
        sa.Column("note_category", sa.String(length=64), nullable=False),   # AFTER_HOURS | MISSED_VISIT | etc.
        sa.Column("encounter_type", sa.String(length=32), nullable=False),  # COMPREHENSIVE | ROUTINE | PRN | IDG | DISCIPLINE
        sa.Column("discipline", sa.String(length=32), nullable=False),      # RN | LVN | MSW | SC | HHA | CHHA | MD | NP

        # Lifecycle
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("encounter_date", sa.Date(), nullable=False),

        # Separated truth layers
        sa.Column("observed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("patient_reported", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("caregiver_reported", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Clinical content
        sa.Column("assessment", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("interventions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("plan_of_care_updates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Validation / compliance
        sa.Column("needs_clarification", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("red_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("audit_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Incident workflow
        sa.Column(
            "incident_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "incident_status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'NONE'"),
        ),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Signature / audit
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    constraints = {
        "ck_clinical_notes_care_level": "care_level IN ('RC', 'CC', 'GIP', 'RSP')",
        "ck_clinical_notes_visit_type": """
            visit_type IN (
                'ROUTINE',
                'PRN',
                'CRISIS',
                'ADMISSION',
                'RECERT',
                'FOLLOW_UP',
                'F2F',
                'DEATH',
                'BEREAVEMENT',
                'SUPERVISORY',
                'PRE_ADMIT'
            )
        """,
        "ck_clinical_notes_visit_origin": """
            visit_origin IN (
                'SCHEDULED',
                'UNSCHEDULED',
                'TRIAGE',
                'PHONE_CALL'
            )
        """,
        "ck_clinical_notes_note_category": """
            note_category IN (
                'AFTER_DEATH',
                'AFTER_HOURS',
                'ANCILLARY_SUPPORT',
                'ASSESS',
                'BEREAVEMENT_VISIT',
                'DEATH_VISIT',
                'DECLINED_VISIT',
                'MISSED_VISIT',
                'OFFICE_HOURS',
                'ON_CALL_TRIAGE',
                'RESPITE_RELIEF',
                'SUP_VISIT_ONLY',
                'VOLUNTEER_SUPPORT',
                'WEEKENDS',
                'SHORT_FORM',
                'PRE_ADMIT_EVAL'
            )
        """,
        "ck_clinical_notes_encounter_type": """
            encounter_type IN (
                'COMPREHENSIVE',
                'ROUTINE',
                'PRN',
                'IDG',
                'DISCIPLINE'
            )
        """,
        "ck_clinical_notes_discipline": """
            discipline IN (
                'RN',
                'LVN',
                'MSW',
                'SC',
                'HHA',
                'CHHA',
                'MD',
                'NP'
            )
        """,
        "ck_clinical_notes_status": "status IN ('DRAFT', 'SIGNED', 'VOIDED')",
        "ck_clinical_notes_incident_status": "incident_status IN ('NONE', 'PENDING', 'COMPLETED', 'WAIVED')",
        "ck_clinical_notes_signed_requires_fields": """
            status <> 'SIGNED'
            OR (
                signed_by IS NOT NULL
                AND signed_at IS NOT NULL
            )
        """,
    }

    for name, definition in constraints.items():
        op.create_check_constraint(name, "clinical_notes", definition)

    op.create_index("ix_clinical_notes_tenant_id", "clinical_notes", ["tenant_id"], unique=False)
    op.create_index("ix_clinical_notes_patient_id", "clinical_notes", ["patient_id"], unique=False)
    op.create_index("ix_clinical_notes_encounter_date", "clinical_notes", ["encounter_date"], unique=False)
    op.create_index("ix_clinical_notes_visit_type", "clinical_notes", ["visit_type"], unique=False)
    op.create_index("ix_clinical_notes_note_category", "clinical_notes", ["note_category"], unique=False)
    op.create_index("ix_clinical_notes_incident_required", "clinical_notes", ["incident_required"], unique=False)


def _create_incident_reports_if_missing() -> None:
    if _table_exists("incident_reports"):
        return

    op.create_table(
        "incident_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Optional logical link to clinical note
        # No FK here because existing legacy clinical_notes may be owner-protected
        sa.Column("clinical_note_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Incident classification
        sa.Column("incident_type", sa.String(length=32), nullable=False),
        sa.Column(
            "incident_severity",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'STANDARD'"),
        ),

        # Dates
        sa.Column("incident_date", sa.Date(), nullable=False),
        sa.Column("reported_date", sa.Date(), nullable=True),
        sa.Column("incident_time", sa.Time(), nullable=True),

        # Structured event details
        sa.Column("reported_by", sa.String(length=32), nullable=True),
        sa.Column("witnessed_by", sa.String(length=32), nullable=True),
        sa.Column("place", sa.String(length=16), nullable=True),
        sa.Column("area", sa.String(length=32), nullable=True),
        sa.Column("surface", sa.String(length=32), nullable=True),

        sa.Column("medication_used", sa.String(length=32), nullable=True),
        sa.Column("activity_at_time", sa.String(length=64), nullable=True),

        sa.Column("injury_level", sa.String(length=32), nullable=True),
        sa.Column("injury_type", sa.String(length=32), nullable=True),
        sa.Column("other_injury_text", sa.Text(), nullable=True),

        sa.Column("narrative", sa.Text(), nullable=True),

        # Signature / audit
        sa.Column("entered_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    constraints = {
        "ck_incident_reports_incident_type": """
            incident_type IN (
                'FALL',
                'ADVERSE_REACTION',
                'SENTINEL_EVENT',
                'OTHER'
            )
        """,
        "ck_incident_reports_incident_severity": """
            incident_severity IN (
                'STANDARD',
                'SIGNIFICANT',
                'SENTINEL'
            )
        """,
        "ck_incident_reports_reported_by": """
            reported_by IS NULL OR reported_by IN (
                'PATIENT',
                'PCG',
                'SPOUSE_PARTNER',
                'CHILD',
                'RELATIVE',
                'FRIEND',
                'FACILITY_STAFF',
                'OTHER'
            )
        """,
        "ck_incident_reports_witnessed_by": """
            witnessed_by IS NULL OR witnessed_by IN (
                'NOT_WITNESSED',
                'STAFF',
                'PCG',
                'SPOUSE_PARTNER',
                'CHILD',
                'RELATIVE',
                'FRIEND',
                'FACILITY_STAFF',
                'OTHER'
            )
        """,
        "ck_incident_reports_place": "place IS NULL OR place IN ('POS', 'OTHER')",
        "ck_incident_reports_area": """
            area IS NULL OR area IN (
                'PT_ROOM_BEDROOM',
                'HALLWAY',
                'BATHROOM',
                'STEPS',
                'KITCHEN',
                'OTHER'
            )
        """,
        "ck_incident_reports_surface": """
            surface IS NULL OR surface IN (
                'CARPET',
                'RUNNER',
                'THROW_AWAY_RUG',
                'SLAB',
                'WOOD',
                'OTHER'
            )
        """,
        "ck_incident_reports_medication_used": """
            medication_used IS NULL OR medication_used IN (
                'NONE',
                'ANALGESIC',
                'SEDATIVE',
                'OPIATE',
                'OTHER'
            )
        """,
        "ck_incident_reports_activity_at_time": """
            activity_at_time IS NULL OR activity_at_time IN (
                'REACHING_CHAIR_TO_BED',
                'REACHING_BED_TO_CHAIR',
                'AMBULATING',
                'TOILETING',
                'TRANSFERRING',
                'SITTING',
                'OTHER'
            )
        """,
        "ck_incident_reports_injury_level": """
            injury_level IS NULL OR injury_level IN (
                'NO_INJURY',
                'MINOR_INJURY',
                'MODERATE_INJURY',
                'HOSPITALIZATION_REQUIRED'
            )
        """,
        "ck_incident_reports_injury_type": """
            injury_type IS NULL OR injury_type IN (
                'NONE',
                'SKIN_TEAR',
                'LACERATION',
                'BRUISE',
                'FRACTURE',
                'OTHER'
            )
        """,
        "ck_incident_reports_signed_requires_fields": """
            signed_by IS NULL
            OR signed_at IS NOT NULL
        """,
    }

    for name, definition in constraints.items():
        op.create_check_constraint(name, "incident_reports", definition)

    op.create_index("ix_incident_reports_tenant_id", "incident_reports", ["tenant_id"], unique=False)
    op.create_index("ix_incident_reports_patient_id", "incident_reports", ["patient_id"], unique=False)
    op.create_index("ix_incident_reports_incident_date", "incident_reports", ["incident_date"], unique=False)
    op.create_index("ix_incident_reports_incident_type", "incident_reports", ["incident_type"], unique=False)
    op.create_index("ix_incident_reports_clinical_note_id", "incident_reports", ["clinical_note_id"], unique=False)


def upgrade() -> None:
    _create_clinical_notes_if_missing()
    _create_incident_reports_if_missing()


def downgrade() -> None:
    if _table_exists("incident_reports"):
        if _index_exists("incident_reports", "ix_incident_reports_clinical_note_id"):
            op.drop_index("ix_incident_reports_clinical_note_id", table_name="incident_reports")
        if _index_exists("incident_reports", "ix_incident_reports_incident_type"):
            op.drop_index("ix_incident_reports_incident_type", table_name="incident_reports")
        if _index_exists("incident_reports", "ix_incident_reports_incident_date"):
            op.drop_index("ix_incident_reports_incident_date", table_name="incident_reports")
        if _index_exists("incident_reports", "ix_incident_reports_patient_id"):
            op.drop_index("ix_incident_reports_patient_id", table_name="incident_reports")
        if _index_exists("incident_reports", "ix_incident_reports_tenant_id"):
            op.drop_index("ix_incident_reports_tenant_id", table_name="incident_reports")
        op.drop_table("incident_reports")

    # We do NOT drop clinical_notes if it pre-existed this environment.
    # This downgrade intentionally avoids destructive behavior on legacy owner-owned tables.