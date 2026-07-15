"""add diagnosis benefit period governance fields

Revision ID: 6f22bbf50b8b
Revises: 90a72b43c2f0
Create Date: 2026-07-08 13:10:34.593415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6f22bbf50b8b'
down_revision: Union[str, Sequence[str], None] = '90a72b43c2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "effective_benefit_period_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "resolved_benefit_period_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "idg_discussion_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "idg_discussed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "idg_discussed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "idg_meeting_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "idg_summary",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "hospital_records_reviewed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "diagnostic_results_reviewed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "specialist_documentation_reviewed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "specialist_name",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "specialist_documentation_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "prior_specialist_certification_present",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "supporting_evidence_summary",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "physician_signed_document_type",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "physician_signed_document_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "physician_signed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "physician_signature_notes",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column(
            "change_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_patient_diagnoses_idg_meeting_id",
        "patient_diagnoses",
        ["idg_meeting_id"],
    )

    op.create_index(
        "ix_patient_diagnoses_effective_benefit_period",
        "patient_diagnoses",
        ["patient_id", "effective_benefit_period_number"],
    )

    op.create_index(
        "ix_patient_diagnoses_idg_review",
        "patient_diagnoses",
        [
            "patient_id",
            "idg_discussion_required",
            "idg_discussed",
        ],
    )

    op.create_check_constraint(
        "ck_patient_diagnoses_resolved_benefit_after_effective",
        "patient_diagnoses",
        (
            "resolved_benefit_period_number IS NULL "
            "OR effective_benefit_period_number IS NULL "
            "OR resolved_benefit_period_number >= effective_benefit_period_number"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_patient_diagnoses_resolved_benefit_after_effective",
        "patient_diagnoses",
        type_="check",
    )

    op.drop_index(
        "ix_patient_diagnoses_idg_review",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_effective_benefit_period",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_idg_meeting_id",
        table_name="patient_diagnoses",
    )

    op.drop_column("patient_diagnoses", "change_reason")
    op.drop_column("patient_diagnoses", "physician_signature_notes")
    op.drop_column("patient_diagnoses", "physician_signed_at")
    op.drop_column("patient_diagnoses", "physician_signed_document_id")
    op.drop_column("patient_diagnoses", "physician_signed_document_type")
    op.drop_column("patient_diagnoses", "supporting_evidence_summary")
    op.drop_column("patient_diagnoses", "prior_specialist_certification_present")
    op.drop_column("patient_diagnoses", "specialist_documentation_date")
    op.drop_column("patient_diagnoses", "specialist_name")
    op.drop_column("patient_diagnoses", "specialist_documentation_reviewed")
    op.drop_column("patient_diagnoses", "diagnostic_results_reviewed")
    op.drop_column("patient_diagnoses", "hospital_records_reviewed")
    op.drop_column("patient_diagnoses", "idg_summary")
    op.drop_column("patient_diagnoses", "idg_meeting_id")
    op.drop_column("patient_diagnoses", "idg_discussed_at")
    op.drop_column("patient_diagnoses", "idg_discussed")
    op.drop_column("patient_diagnoses", "idg_discussion_required")
    op.drop_column("patient_diagnoses", "resolved_benefit_period_number")
    op.drop_column("patient_diagnoses", "effective_benefit_period_number")