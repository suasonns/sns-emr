"""create discharges and discharge_reasons with cms categories

Revision ID: 8f2b1249a9a8
Revises: 55f06e710b3e
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "8f2b1249a9a8"
down_revision: Union[str, Sequence[str], None] = "55f06e710b3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # -----------------------------
    # 1) discharge_reasons (seeded)
    # -----------------------------
    op.create_table(
        "discharge_reasons",
        sa.Column("code", sa.String(length=64), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("cms_category", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_check_constraint(
        "ck_discharge_reasons_cms_category",
        "discharge_reasons",
        "cms_category IN ('DEATH','TRANSFER','NO_LONGER_TERMINAL','DISCHARGE_FOR_CAUSE','REVOCATION')",
    )

    # -----------------------------
    # 2) discharges (event record)
    # -----------------------------
    op.create_table(
        "discharges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),

        sa.Column("discharge_reason_code", sa.String(length=64), sa.ForeignKey("discharge_reasons.code"), nullable=False),
        sa.Column("cms_category", sa.String(length=32), nullable=False),

        sa.Column("status", sa.String(length=16), nullable=False, server_default="DRAFT"),

        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),

        sa.Column("transfer_destination_type", sa.String(length=32), nullable=True),
        sa.Column("transfer_destination_name", sa.String(length=128), nullable=True),
        sa.Column("transfer_destination_notes", sa.Text(), nullable=True),

        sa.Column("physician_discharge_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supporting_clinical_note_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("documentation_note_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("remediation_attempts_documented", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("patient_notified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("medical_director_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("revocation_statement_signed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("initiated_by", sa.String(length=16), nullable=True),

        sa.Column("death_documentation_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("notes", sa.Text(), nullable=True),
    )

    # -----------------------------
    # 3) Base check constraints
    # -----------------------------
    op.create_check_constraint(
        "ck_discharges_status",
        "discharges",
        "status IN ('DRAFT','FINALIZED','VOIDED')",
    )

    op.create_check_constraint(
        "ck_discharges_cms_category",
        "discharges",
        "cms_category IN ('DEATH','TRANSFER','NO_LONGER_TERMINAL','DISCHARGE_FOR_CAUSE','REVOCATION')",
    )

    op.create_check_constraint(
        "ck_discharges_initiated_by",
        "discharges",
        "(initiated_by IS NULL) OR (initiated_by IN ('PATIENT','LEGAL_REP','HOSPICE','SYSTEM'))",
    )

    op.create_check_constraint(
        "ck_discharges_transfer_destination_type",
        "discharges",
        "(transfer_destination_type IS NULL) OR (transfer_destination_type IN "
        "('HOSPICE','PCP','SNF','HOSPITAL','REHAB','HOME_HEALTH','PALLIATIVE_CARE','OTHER'))",
    )

    # -----------------------------
    # 4) HARD CMS VALIDATIONS (Finalized only)
    # -----------------------------
    op.create_check_constraint(
        "ck_discharges_finalized_requires_effective_at_and_order",
        "discharges",
        "(status <> 'FINALIZED') OR (effective_at IS NOT NULL AND physician_discharge_order_id IS NOT NULL)",
    )

    op.create_check_constraint(
        "ck_discharges_for_cause_requires_docs",
        "discharges",
        "(status <> 'FINALIZED') OR (cms_category <> 'DISCHARGE_FOR_CAUSE') OR ("
        "documentation_note_id IS NOT NULL AND "
        "remediation_attempts_documented = true AND "
        "patient_notified = true AND "
        "medical_director_approval = true"
        ")",
    )

    op.create_check_constraint(
        "ck_discharges_revocation_requires_patient_initiation",
        "discharges",
        "(status <> 'FINALIZED') OR (cms_category <> 'REVOCATION') OR ("
        "revocation_statement_signed = true AND "
        "initiated_by IN ('PATIENT','LEGAL_REP')"
        ")",
    )

    op.create_check_constraint(
        "ck_discharges_transfer_requires_destination_type",
        "discharges",
        "(status <> 'FINALIZED') OR (cms_category <> 'TRANSFER') OR (transfer_destination_type IS NOT NULL)",
    )

    op.create_check_constraint(
        "ck_discharges_no_longer_terminal_requires_supporting_note",
        "discharges",
        "(status <> 'FINALIZED') OR (cms_category <> 'NO_LONGER_TERMINAL') OR (supporting_clinical_note_id IS NOT NULL)",
    )

    op.create_check_constraint(
        "ck_discharges_death_requires_death_documentation",
        "discharges",
        "(status <> 'FINALIZED') OR (cms_category <> 'DEATH') OR (death_documentation_present = true)",
    )

    # -----------------------------
    # 5) Helpful indexes
    # -----------------------------
    op.create_index("ix_discharges_patient_id", "discharges", ["patient_id"])
    op.create_index("ix_discharges_status", "discharges", ["status"])
    op.create_index("ix_discharges_effective_at", "discharges", ["effective_at"])

    # -----------------------------
    # 6) Link patient to current discharge
    # -----------------------------
    op.add_column("patients", sa.Column("current_discharge_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_patients_current_discharge",
        "patients",
        "discharges",
        ["current_discharge_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -----------------------------
    # 7) Seed discharge_reasons
    # -----------------------------
    op.bulk_insert(
        sa.table(
            "discharge_reasons",
            sa.column("code", sa.String),
            sa.column("label", sa.String),
            sa.column("cms_category", sa.String),
            sa.column("active", sa.Boolean),
        ),
        [
            {"code": "DEATH", "label": "Death", "cms_category": "DEATH", "active": True},

            {"code": "HOSPITALIZED", "label": "Hospitalized", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_ANOTHER_HOSPICE", "label": "Transferred to Another Hospice", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_SNF", "label": "Transfer to Skilled Nursing Facility", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_HOSPITAL", "label": "Transfer to Hospital", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_REHAB", "label": "Transfer to Rehab / Outpatient Rehab Facility", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_HOME_HEALTH", "label": "Transferred to Home Health", "cms_category": "TRANSFER", "active": True},
            {"code": "TRANSFER_TO_PALLIATIVE_CARE", "label": "Transferred to Palliative Care", "cms_category": "TRANSFER", "active": True},
            {"code": "REFERRED_BACK_TO_PCP", "label": "Referred Back to Primary Care Physician", "cms_category": "TRANSFER", "active": True},
            {"code": "MOVED_OUT_OF_AREA", "label": "Moved Out of Service Area", "cms_category": "TRANSFER", "active": True},

            {"code": "PROGNOSIS_EXTENDED", "label": "Prognosis Extended", "cms_category": "NO_LONGER_TERMINAL", "active": True},
            {"code": "STATUS_IMPROVED", "label": "Status Improved", "cms_category": "NO_LONGER_TERMINAL", "active": True},
            {"code": "SYMPTOMS_MANAGED", "label": "Symptoms Managed", "cms_category": "NO_LONGER_TERMINAL", "active": True},

            {"code": "REVOCATION_OF_HOSPICE", "label": "Revocation of Hospice", "cms_category": "REVOCATION", "active": True},
            {"code": "DECLINED_FURTHER_SERVICES", "label": "Declined Further Services", "cms_category": "REVOCATION", "active": True},
            {"code": "PATIENT_REFUSED_SERVICE", "label": "Patient Refused Services", "cms_category": "REVOCATION", "active": True},
            {"code": "CHANGE_IN_PAYER", "label": "Change in Payer", "cms_category": "REVOCATION", "active": True},

            {"code": "DISCHARGED_WITH_CAUSE", "label": "Discharged With Cause", "cms_category": "DISCHARGE_FOR_CAUSE", "active": True},
            {"code": "NON_COMPLIANT_WITH_POC", "label": "Non-Compliant with Treatment / Plan of Care", "cms_category": "DISCHARGE_FOR_CAUSE", "active": True},
            {"code": "UNSAFE_ENVIRONMENT_FOR_STAFF", "label": "Unsafe Environment for Staff", "cms_category": "DISCHARGE_FOR_CAUSE", "active": True},
            {"code": "UNABLE_TO_MEET_CARE_NEEDS", "label": "Unable to Meet Patient / Family Care Needs", "cms_category": "DISCHARGE_FOR_CAUSE", "active": True},
            {"code": "ADMINISTRATIVE_DISCHARGE", "label": "Administrative Discharge", "cms_category": "DISCHARGE_FOR_CAUSE", "active": True},
        ],
    )


def downgrade():
    op.drop_constraint("fk_patients_current_discharge", "patients", type_="foreignkey")
    op.drop_column("patients", "current_discharge_id")

    op.drop_index("ix_discharges_effective_at", table_name="discharges")
    op.drop_index("ix_discharges_status", table_name="discharges")
    op.drop_index("ix_discharges_patient_id", table_name="discharges")

    op.drop_table("discharges")
    op.drop_table("discharge_reasons")
