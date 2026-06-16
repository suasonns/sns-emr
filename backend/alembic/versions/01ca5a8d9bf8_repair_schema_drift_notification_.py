"""repair schema drift: notification, substance, coverage workflow columns

Revision ID: 01ca5a8d9bf8
Revises: 0b88fddadbe5
Create Date: 2026-06-04 21:10:02.363425
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "01ca5a8d9bf8"
down_revision: Union[str, Sequence[str], None] = "0b88fddadbe5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------
    # service_coverage_decisions
    # -------------------------
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS service_id UUID;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS coverage_intent VARCHAR;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS financial_responsibility VARCHAR;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS decision_source VARCHAR;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS decision_reason TEXT;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS evidence_reference_type VARCHAR;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS evidence_reference_id UUID;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS selected_payer_id UUID;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS decided_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS decided_by UUID;")
    op.execute("ALTER TABLE service_coverage_decisions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;")

    # -------------------------
    # external_substances
    # -------------------------
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS name VARCHAR;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS substance_type VARCHAR;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS initiated_by UUID;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS ordered_by_provider UUID;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS purpose TEXT;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS known_interactions TEXT;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS clinician_reviewed BOOLEAN;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS clinician_action VARCHAR;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS clinician_notes TEXT;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS coverage_intent VARCHAR;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS financial_responsibility VARCHAR;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS reviewed_by UUID;")
    op.execute("ALTER TABLE external_substances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;")

    # -------------------------
    # document_notifications
    # -------------------------
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS recipient_role VARCHAR;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS recipient_user_id UUID;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS notified_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS reminder_count INTEGER;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS resolution_status VARCHAR;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS resolution_note TEXT;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE document_notifications ADD COLUMN IF NOT EXISTS resolved_by UUID;")

    # -------------------------
    # communications_logs
    # -------------------------
    op.execute("ALTER TABLE communications_logs ADD COLUMN IF NOT EXISTS event_type VARCHAR;")
    op.execute("ALTER TABLE communications_logs ADD COLUMN IF NOT EXISTS focus_area VARCHAR;")
    op.execute("ALTER TABLE communications_logs ADD COLUMN IF NOT EXISTS event_time TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE communications_logs ADD COLUMN IF NOT EXISTS summary TEXT;")
    op.execute("ALTER TABLE communications_logs ADD COLUMN IF NOT EXISTS details TEXT;")

    # -------------------------
    # notifications
    # -------------------------
    op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS source_type VARCHAR;")
    op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS source_id UUID;")
    op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS message TEXT;")
    op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS seen_at TIMESTAMP WITHOUT TIME ZONE;")


def downgrade() -> None:
    """
    Downgrade intentionally omitted.
    Repair migrations are forward-only to avoid data loss.
    """
    pass
