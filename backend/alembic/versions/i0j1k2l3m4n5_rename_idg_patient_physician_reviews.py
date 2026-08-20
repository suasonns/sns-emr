"""rename idg_patient_physician_reviews to idg_meeting_patient_reviews

Aligns table/index/constraint naming with the SNS Hospice Solutions IDG
domain model: this table is entity #3, IDGMeetingPatientReview (the
in-meeting review workspace), distinct from PatientIDGReview
(idg_reviews table) and IDGMeeting (idg_meetings table).

Revision ID: i0j1k2l3m4n5
Revises: h8i9j0k1l2m3
Create Date: 2026-08-19
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "i0j1k2l3m4n5"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


RENAMES = [
    ("ix_idg_ppr_tenant_id", "ix_idg_mpr_tenant_id"),
    ("ix_idg_ppr_patient_id", "ix_idg_mpr_patient_id"),
    ("ix_idg_ppr_idg_meeting_id", "ix_idg_mpr_idg_meeting_id"),
    ("ix_idg_ppr_physician_user_id", "ix_idg_mpr_physician_user_id"),
    ("ix_idg_ppr_review_status", "ix_idg_mpr_review_status"),
    ("ix_idg_ppr_recorded_by_user_id", "ix_idg_mpr_recorded_by_user_id"),
]


def upgrade() -> None:
    op.rename_table("idg_patient_physician_reviews", "idg_meeting_patient_reviews")
    for old_name, new_name in RENAMES:
        op.execute(f'ALTER INDEX IF EXISTS "{old_name}" RENAME TO "{new_name}"')
    op.execute(
        "ALTER TABLE idg_meeting_patient_reviews "
        "RENAME CONSTRAINT uq_idg_patient_physician_review_session_patient "
        "TO uq_idg_meeting_patient_review_session_patient"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE idg_meeting_patient_reviews "
        "RENAME CONSTRAINT uq_idg_meeting_patient_review_session_patient "
        "TO uq_idg_patient_physician_review_session_patient"
    )
    for old_name, new_name in RENAMES:
        op.execute(f'ALTER INDEX IF EXISTS "{new_name}" RENAME TO "{old_name}"')
    op.rename_table("idg_meeting_patient_reviews", "idg_patient_physician_reviews")
