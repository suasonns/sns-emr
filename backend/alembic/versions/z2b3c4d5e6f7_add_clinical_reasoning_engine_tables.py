"""add clinical reasoning engine tables (records, findings, significant
change events, interpretations, interpretation findings, interpretation
rules + criteria) and seed the default rule set

The ClinicalReasoningEngine service (app/services/clinical_reasoning_engine.py)
was wired into finalize_visit (RN/LVN), MSW/SC ICA lock, and F2F finalize
without these supporting tables ever being migrated -- only its output
table (clinical_reasoning_results) existed. This left every finalize call
that reached the engine failing with UndefinedTable. This migration adds
the 6 missing supporting tables plus a default interpretation_rules set
covering RN/LVN physical findings, MSW/SC psychosocial findings (including
suicide risk / abuse-neglect, which also flow into the shared IDG
intelligence stream in addition to their existing dedicated Task
escalation), and MD/NP F2F decline findings.

Revision ID: z2b3c4d5e6f7
Revises: y1a2b3c4d5e6
Create Date: 2026-08-23 21:20:00.000000

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = "z2b3c4d5e6f7"
down_revision = "y1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_reasoning_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("requires_poc_update", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_physician_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_idg_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_clinical_reasoning_records_patient_episode_status",
        "clinical_reasoning_records",
        ["patient_id", "episode_id", "status"],
    )
    op.create_index(
        "ix_clinical_reasoning_records_episode_id",
        "clinical_reasoning_records",
        ["episode_id"],
    )

    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "reasoning_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_reasoning_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("finding_type", sa.String(100), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_numeric", sa.Numeric(), nullable=True),
        sa.Column("previous_value_text", sa.Text(), nullable=True),
        sa.Column("previous_value_numeric", sa.Numeric(), nullable=True),
        sa.Column("trend", sa.String(50), nullable=True),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="UNKNOWN"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_significant_change", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_findings_reasoning_record_id", "findings", ["reasoning_record_id"])
    op.create_index("ix_findings_finding_type", "findings", ["finding_type"])

    op.create_table(
        "significant_change_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "reasoning_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_reasoning_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requires_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("physician_notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("representative_notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_significant_change_events_reasoning_record_id",
        "significant_change_events",
        ["reasoning_record_id"],
    )
    op.create_index(
        "ix_significant_change_events_finding_id",
        "significant_change_events",
        ["finding_id"],
    )

    op.create_table(
        "clinical_interpretations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "reasoning_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_reasoning_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interpretation_code", sa.String(100), nullable=False),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("confidence", sa.String(50), nullable=True),
        sa.Column("generated_by", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "reasoning_record_id",
            "interpretation_code",
            name="uq_clinical_interpretations_record_code",
        ),
    )
    op.create_index(
        "ix_clinical_interpretations_reasoning_record_id",
        "clinical_interpretations",
        ["reasoning_record_id"],
    )

    op.create_table(
        "interpretation_findings",
        sa.Column(
            "interpretation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_interpretations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("interpretation_id", "finding_id", name="pk_interpretation_findings"),
    )

    op.create_table(
        "interpretation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_name", sa.String(255), nullable=False),
        sa.Column("interpretation_code", sa.String(100), nullable=False, unique=True),
        sa.Column("interpretation_text", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "interpretation_rule_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpretation_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("required_finding_type", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_interpretation_rule_criteria_rule_id",
        "interpretation_rule_criteria",
        ["rule_id"],
    )

    _seed_default_rules()


# ---------------------------------------------------------------------
# Default rule set. Each entry is (interpretation_code, rule_name,
# interpretation_text, severity, [required_finding_types]).
# This is a v1 default set intended for clinical review/tuning by the
# hospice's IDG/clinical leadership, not a final word on thresholds.
# ---------------------------------------------------------------------
_DEFAULT_RULES: list[tuple[str, str, str, str, list[str]]] = [
    # ---- RN / LVN physical assessment ----
    ("WEIGHT_LOSS", "Unintentional Weight Loss", "Unintentional weight loss identified since the prior assessment.", "moderate", ["weight_loss"]),
    ("WEIGHT_GAIN", "Weight Gain / Possible Fluid Retention", "Weight gain identified since the prior assessment; consider fluid retention.", "low", ["weight_gain"]),
    ("MAC_DECLINE", "Declining Mid-Arm Circumference", "Mid-arm circumference has declined, consistent with nutritional decline.", "moderate", ["mac_decline"]),
    ("POOR_APPETITE", "Poor Appetite", "Poor or absent appetite documented.", "low", ["poor_appetite"]),
    ("SIGNIFICANT_APPETITE_CHANGE", "Significant Appetite Change", "A significant decline in appetite was identified.", "moderate", ["significant_change_appetite"]),
    ("PAIN_ESCALATION", "Pain Escalation", "Pain has escalated since the prior assessment and requires review.", "severe", ["pain"]),
    ("SIGNIFICANT_PAIN_CHANGE", "Significant Pain Change", "A significant increase in pain was identified.", "moderate", ["significant_change_pain"]),
    ("WEAKNESS_INCREASE", "Increasing Weakness", "Increased weakness documented since the prior assessment.", "low", ["weakness"]),
    ("MOBILITY_DECLINE", "Mobility Decline", "Decline in mobility documented since the prior assessment.", "moderate", ["mobility_decline"]),
    ("TRANSFER_DEPENDENCE_INCREASE", "Increasing Transfer Dependence", "Increased assistance required for transfers.", "moderate", ["transfer_dependence"]),
    ("FALL_RISK_EVENT", "Fall Occurred", "A fall was documented and requires safety review.", "severe", ["fall"]),
    ("CAREGIVER_DISTRESS", "Caregiver Distress", "Caregiver distress observed and may require support services.", "moderate", ["caregiver_distress"]),
    ("CAREGIVER_OVERWHELMED", "Caregiver Overwhelmed", "Caregiver reported feeling overwhelmed.", "moderate", ["caregiver_overwhelmed"]),
    ("TACHYPNEA", "Tachypnea", "Elevated respiratory rate documented.", "moderate", ["tachypnea"]),
    ("ACCESSORY_MUSCLE_USE", "Accessory Muscle Use", "Use of accessory muscles for breathing observed.", "moderate", ["accessory_muscle_use"]),
    ("OXYGEN_REQUIREMENT_INCREASE", "Oxygen Requirement Increase", "Oxygen requirement has increased since the prior assessment.", "severe", ["oxygen_increase"]),
    ("EDEMA", "Edema Present", "Edema observed on assessment.", "low", ["edema"]),
    ("ORTHOPNEA", "Orthopnea", "Orthopnea reported or observed.", "moderate", ["orthopnea"]),
    ("CARDIAC_DECOMPENSATION", "Possible Cardiac Decompensation", "Edema and orthopnea together suggest possible cardiac decompensation.", "severe", ["edema", "orthopnea"]),
    ("RESPIRATORY_DISTRESS", "Respiratory Distress", "Tachypnea with accessory muscle use suggests respiratory distress.", "severe", ["tachypnea", "accessory_muscle_use"]),
    ("COGNITIVE_DECLINE", "Cognitive Decline", "Cognitive decline documented since the prior assessment.", "moderate", ["cognitive_decline"]),
    ("BEHAVIOR_CHANGE", "Behavior Change", "A behavior change was documented since the prior assessment.", "moderate", ["behavior_change"]),
    ("SPIRITUAL_DISTRESS", "Spiritual Distress", "Spiritual distress identified; consider chaplain referral.", "low", ["spiritual_distress"]),
    ("FEAR_OF_DYING", "Fear of Dying", "Patient expressed fear of dying.", "moderate", ["fear_of_dying"]),
    ("HOPELESSNESS_RISK", "Hopelessness", "Patient expressed feelings of hopelessness.", "moderate", ["hopelessness"]),

    # ---- MSW / SC psychosocial + spiritual ----
    ("SUICIDE_RISK_IDENTIFIED", "Suicide Risk Identified", "Suicide risk was identified during assessment and requires immediate physician/IDG awareness in addition to the dedicated urgent task escalation.", "severe", ["suicide_risk_identified"]),
    ("ABUSE_NEGLECT_SUSPECTED", "Abuse, Neglect, or Exploitation Suspected", "Suspected abuse, neglect, or exploitation was identified and requires IDG awareness in addition to the dedicated urgent task escalation.", "severe", ["abuse_neglect_suspected"]),
    ("PATIENT_DISTRESS_ELEVATED", "Elevated Patient Psychosocial/Spiritual Distress", "Patient-reported psychosocial or spiritual distress rating is elevated.", "moderate", ["patient_distress_elevated"]),
    ("CAREGIVER_DISTRESS_ELEVATED", "Elevated Caregiver Psychosocial/Spiritual Distress", "Caregiver-reported psychosocial or spiritual distress rating is elevated.", "moderate", ["caregiver_distress_elevated"]),
    ("CAREGIVER_CAPACITY_CONCERN", "Caregiver Capacity Concern", "Concerns identified about caregiver ability or willingness to provide care.", "moderate", ["caregiver_capacity_concern"]),
    ("UNMET_NEEDS_IDENTIFIED", "Unmet Needs Identified", "Unmet financial, legal, or practical needs were identified.", "low", ["unmet_needs_identified"]),

    # ---- MD / NP F2F decline ----
    ("PPS_DECLINE", "PPS Decline", "Palliative Performance Scale score has declined since the prior encounter.", "moderate", ["pps_decline"]),
    ("ECOG_DECLINE", "ECOG Performance Status Decline", "ECOG performance status has worsened since the prior encounter.", "moderate", ["ecog_decline"]),
    ("OXYGEN_REQUIREMENT_INCREASE_F2F", "Oxygen Requirement Increase (F2F)", "Oxygen requirement has increased since the prior F2F encounter.", "severe", ["f2f_oxygen_increase"]),
    ("FUNCTIONAL_DECLINE_ADL", "Functional / ADL Decline", "Increased ADL dependency or bedbound status documented at F2F.", "moderate", ["functional_decline_adl"]),
    ("RECENT_HOSPITALIZATION", "Recent Hospitalization", "Hospitalization(s) within the past 30 days documented at F2F.", "moderate", ["recent_hospitalization"]),
    ("DYSPHAGIA_PRESENT", "Dysphagia Present", "Dysphagia documented at F2F.", "moderate", ["dysphagia_present"]),
    ("WEIGHT_LOSS_F2F", "Weight Loss (F2F)", "Documented weight loss at F2F encounter.", "moderate", ["weight_loss_f2f"]),
]


def _seed_default_rules() -> None:
    bind = op.get_bind()

    rules_table = table(
        "interpretation_rules",
        column("id", postgresql.UUID(as_uuid=True)),
        column("rule_name", sa.String),
        column("interpretation_code", sa.String),
        column("interpretation_text", sa.Text),
        column("severity", sa.String),
        column("active", sa.Boolean),
    )
    criteria_table = table(
        "interpretation_rule_criteria",
        column("id", postgresql.UUID(as_uuid=True)),
        column("rule_id", postgresql.UUID(as_uuid=True)),
        column("required_finding_type", sa.String),
    )

    for interpretation_code, rule_name, interpretation_text, severity, required_types in _DEFAULT_RULES:
        rule_id = uuid.uuid4()
        bind.execute(
            rules_table.insert().values(
                id=rule_id,
                rule_name=rule_name,
                interpretation_code=interpretation_code,
                interpretation_text=interpretation_text,
                severity=severity,
                active=True,
            )
        )
        for required_type in required_types:
            bind.execute(
                criteria_table.insert().values(
                    id=uuid.uuid4(),
                    rule_id=rule_id,
                    required_finding_type=required_type,
                )
            )


def downgrade() -> None:
    op.drop_table("interpretation_rule_criteria")
    op.drop_table("interpretation_rules")
    op.drop_table("interpretation_findings")
    op.drop_index("ix_clinical_interpretations_reasoning_record_id", table_name="clinical_interpretations")
    op.drop_table("clinical_interpretations")
    op.drop_index("ix_significant_change_events_finding_id", table_name="significant_change_events")
    op.drop_index("ix_significant_change_events_reasoning_record_id", table_name="significant_change_events")
    op.drop_table("significant_change_events")
    op.drop_index("ix_findings_finding_type", table_name="findings")
    op.drop_index("ix_findings_reasoning_record_id", table_name="findings")
    op.drop_table("findings")
    op.drop_index("ix_clinical_reasoning_records_episode_id", table_name="clinical_reasoning_records")
    op.drop_index("ix_clinical_reasoning_records_patient_episode_status", table_name="clinical_reasoning_records")
    op.drop_table("clinical_reasoning_records")
