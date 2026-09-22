"""Widen clinical_outcome_audit_events event_type check constraint to add
IDG_COMMUNICATION_RECORDED

Revision ID: d3e4f5a6b7c8
Revises: c8a1f0d92b3e
Create Date: 2026-09-23

PR-review audit-coverage finding: record_idg_communication() mutates
clinical_outcome_records.idg_communicated/idg_communicated_at/idg_review_id
but had no corresponding audit event. This migration widens the
ck_clinical_outcome_audit_events_type check constraint to allow a new
IDG_COMMUNICATION_RECORDED event_type so the service layer can audit that
mutation like every other one.
"""

from __future__ import annotations

from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c8a1f0d92b3e"
branch_labels = None
depends_on = None

OLD_CONSTRAINT = (
    "event_type IN ("
    "'OUTCOME_CREATED','INTERVENTION_RECORDED','PATIENT_RESPONSE_RECORDED',"
    "'OUTCOME_STATUS_CHANGED','REMAINING_NEED_RECORDED','IDG_FOLLOW_UP_REQUIRED',"
    "'OUTCOME_CORRECTED','OUTCOME_FINALIZED','OUTCOME_REOPENED'"
    ")"
)

NEW_CONSTRAINT = (
    "event_type IN ("
    "'OUTCOME_CREATED','INTERVENTION_RECORDED','PATIENT_RESPONSE_RECORDED',"
    "'OUTCOME_STATUS_CHANGED','REMAINING_NEED_RECORDED','IDG_FOLLOW_UP_REQUIRED',"
    "'OUTCOME_CORRECTED','OUTCOME_FINALIZED','OUTCOME_REOPENED',"
    "'IDG_COMMUNICATION_RECORDED'"
    ")"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_clinical_outcome_audit_events_type", "clinical_outcome_audit_events", type_="check"
    )
    op.create_check_constraint(
        "ck_clinical_outcome_audit_events_type", "clinical_outcome_audit_events", NEW_CONSTRAINT
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_clinical_outcome_audit_events_type", "clinical_outcome_audit_events", type_="check"
    )
    op.create_check_constraint(
        "ck_clinical_outcome_audit_events_type", "clinical_outcome_audit_events", OLD_CONSTRAINT
    )
