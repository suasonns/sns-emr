"""align poc physician approval schema

Revision ID: 9c4f2a7b6e31
Revises: 3d45bec984f9
Create Date: 2026-07-07

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9c4f2a7b6e31"
down_revision: Union[str, Sequence[str], None] = "3d45bec984f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # POC PHYSICIAN APPROVALS
    # Align deployed database table with production-grade model.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS attestation_version VARCHAR(100)
        NOT NULL DEFAULT 'POC_PHYSICIAN_ATTESTATION_V1'
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rejection_reason TEXT
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rejected_by_user_id UUID
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP WITH TIME ZONE
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rescission_reason TEXT
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rescinded_by_user_id UUID
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD COLUMN IF NOT EXISTS rescinded_at TIMESTAMP WITH TIME ZONE
        """
    )

    # ---------------------------------------------------------
    # Normalize old non-decision status before replacing constraint.
    # SIGNED_DOCUMENT_UPLOADED is a document/audit event,
    # not a physician approval decision status.
    # ---------------------------------------------------------

    op.execute(
        """
        UPDATE poc_physician_approvals
        SET approval_status = 'PENDING_PHYSICIAN_SIGNATURE'
        WHERE approval_status = 'SIGNED_DOCUMENT_UPLOADED'
        """
    )

    # ---------------------------------------------------------
    # Replace approval_status constraint.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approval_status
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_approval_status
        CHECK (
            approval_status IN (
                'PENDING_PHYSICIAN_SIGNATURE',
                'PHYSICIAN_APPROVED',
                'PHYSICIAN_REJECTED',
                'APPROVAL_RESCINDED',
                'VOIDED'
            )
        )
        """
    )

    # ---------------------------------------------------------
    # Approved records require physician approval date.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_approval_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_approved_requires_approval_date
        CHECK (
            approval_status != 'PHYSICIAN_APPROVED'
            OR approval_date IS NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Approved records require attestation text.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_attestation_text
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_approved_requires_attestation_text
        CHECK (
            approval_status != 'PHYSICIAN_APPROVED'
            OR attestation_text IS NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Approved records require attestation version.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_attestation_version
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_approved_requires_attestation_version
        CHECK (
            approval_status != 'PHYSICIAN_APPROVED'
            OR attestation_version IS NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Electronic signature approval requires authentication metadata.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_e_signature_requires_authentication
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_e_signature_requires_authentication
        CHECK (
            approval_method != 'ELECTRONIC_SIGNATURE'
            OR approval_status != 'PHYSICIAN_APPROVED'
            OR (
                electronic_signature_text IS NOT NULL
                AND electronically_signed_by_user_id IS NOT NULL
                AND system_authenticated_at IS NOT NULL
            )
        )
        """
    )

    # ---------------------------------------------------------
    # Physician rejection requires reason and timestamp.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_rejection_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_rejection_requires_reason
        CHECK (
            approval_status != 'PHYSICIAN_REJECTED'
            OR (
                rejection_reason IS NOT NULL
                AND rejected_at IS NOT NULL
            )
        )
        """
    )

    # ---------------------------------------------------------
    # Approval rescission requires reason and timestamp.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_rescission_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_rescission_requires_reason
        CHECK (
            approval_status != 'APPROVAL_RESCINDED'
            OR (
                rescission_reason IS NOT NULL
                AND rescinded_at IS NOT NULL
            )
        )
        """
    )

    # ---------------------------------------------------------
    # Voided records must be internally consistent.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_void_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_void_requires_reason
        CHECK (
            is_voided = FALSE
            OR (
                is_voided = TRUE
                AND approval_status = 'VOIDED'
                AND void_reason IS NOT NULL
                AND voided_at IS NOT NULL
            )
        )
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_void_status_requires_is_voided
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_void_status_requires_is_voided
        CHECK (
            approval_status != 'VOIDED'
            OR is_voided = TRUE
        )
        """
    )

    # ---------------------------------------------------------
    # Compliance alert timestamps require due date.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_reminder_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_reminder_requires_due_date
        CHECK (
            reminder_sent_at IS NULL
            OR approval_due_date IS NOT NULL
        )
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_warning_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_warning_requires_due_date
        CHECK (
            compliance_warning_at IS NULL
            OR approval_due_date IS NOT NULL
        )
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_high_alert_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_high_alert_requires_due_date
        CHECK (
            high_priority_alert_at IS NULL
            OR approval_due_date IS NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Indexes used by compliance dashboards and tenant lookup.
    # ---------------------------------------------------------

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_poc_physician_approvals_tenant_patient_version
        ON poc_physician_approvals (
            tenant_id,
            patient_id,
            poc_version_id
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_poc_physician_approvals_escalation_level
        ON poc_physician_approvals (
            escalation_level
        )
        """
    )


def downgrade() -> None:
    # ---------------------------------------------------------
    # Drop indexes added by this migration.
    # ---------------------------------------------------------

    op.execute(
        """
        DROP INDEX IF EXISTS ix_poc_physician_approvals_escalation_level
        """
    )

    op.execute(
        """
        DROP INDEX IF EXISTS ix_poc_physician_approvals_tenant_patient_version
        """
    )

    # ---------------------------------------------------------
    # Drop constraints added by this migration.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_high_alert_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_warning_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_reminder_requires_due_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_void_status_requires_is_voided
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_void_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_rescission_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_rejection_requires_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_e_signature_requires_authentication
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_attestation_version
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_attestation_text
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approved_requires_approval_date
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP CONSTRAINT IF EXISTS ck_poc_physician_approvals_approval_status
        """
    )

    # ---------------------------------------------------------
    # Restore older approval_status constraint.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        ADD CONSTRAINT ck_poc_physician_approvals_approval_status
        CHECK (
            approval_status IN (
                'PENDING_PHYSICIAN_SIGNATURE',
                'PHYSICIAN_APPROVED',
                'SIGNED_DOCUMENT_UPLOADED',
                'VOIDED'
            )
        )
        """
    )

    # ---------------------------------------------------------
    # Drop columns added by this migration.
    # ---------------------------------------------------------

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rescinded_at
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rescinded_by_user_id
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rescission_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rejected_at
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rejected_by_user_id
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS rejection_reason
        """
    )

    op.execute(
        """
        ALTER TABLE poc_physician_approvals
        DROP COLUMN IF EXISTS attestation_version
        """
    )