"""add idg priority rules

Revision ID: d5e9b8a683d7
Revises: 166f835f4ab8
Create Date: 2026-07-31 14:30:03.740962

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd5e9b8a683d7'
down_revision: Union[str, Sequence[str], None] = '166f835f4ab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idg_priority_rules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),

        sa.Column("rule_key", sa.String(length=150), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),

        # Hospice-specific IDG impact, not hospital acuity.
        sa.Column("idg_impact_level", sa.String(length=50), nullable=False),

        # Separate from IDG impact.
        sa.Column(
            "clinical_escalation_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "requires_idg_discussion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "requires_followup",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        # Suggested activation route.
        # Examples:
        # CLINICIAN
        # CLINICIAN_MD_REPORT
        # ADMIN_REPORT
        # MSW_SC_AS_NEEDED
        # IDG_REVIEW_ONLY
        sa.Column("activation_route", sa.String(length=100), nullable=True),

        # Optional source scoping.
        # Keep NULL for all source types.
        sa.Column("source_type", sa.String(length=100), nullable=True),

        # Higher number wins when multiple rules match.
        sa.Column(
            "weight",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("50"),
        ),

        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column("notes", sa.Text(), nullable=True),

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

        sa.CheckConstraint(
            "idg_impact_level IN "
            "('ADMINISTRATIVE', 'CLINICAL', 'SIGNIFICANT', 'IDG_REQUIRED')",
            name="ck_idg_priority_rules_impact_level",
        ),

        sa.UniqueConstraint(
            "rule_key",
            name="uq_idg_priority_rules_rule_key",
        ),
    )

    op.create_index(
        "ix_idg_priority_rules_active",
        "idg_priority_rules",
        ["active"],
    )

    op.create_index(
        "ix_idg_priority_rules_keyword",
        "idg_priority_rules",
        ["keyword"],
    )

    op.create_index(
        "ix_idg_priority_rules_category",
        "idg_priority_rules",
        ["category"],
    )

    op.create_index(
        "ix_idg_priority_rules_impact",
        "idg_priority_rules",
        ["idg_impact_level"],
    )

    # Optional but recommended: store the rule match on the harvested item.
    op.add_column(
        "idg_intelligence_items",
        sa.Column("idg_impact_level", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "idg_intelligence_items",
        sa.Column("idg_reason_category", sa.String(length=100), nullable=True),
    )

    op.add_column(
        "idg_intelligence_items",
        sa.Column("matched_priority_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.add_column(
        "idg_intelligence_items",
        sa.Column("matched_priority_keyword", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "idg_intelligence_items",
        sa.Column(
            "clinical_escalation_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "idg_intelligence_items",
        sa.Column("activation_route", sa.String(length=100), nullable=True),
    )

    op.create_index(
        "ix_idg_intelligence_impact_level",
        "idg_intelligence_items",
        ["tenant_id", "idg_impact_level"],
    )

    op.create_index(
        "ix_idg_intelligence_reason_category",
        "idg_intelligence_items",
        ["tenant_id", "idg_reason_category"],
    )

    # Seed rules.
    op.execute(
        """
        INSERT INTO idg_priority_rules (
            rule_key,
            keyword,
            category,
            idg_impact_level,
            clinical_escalation_required,
            requires_idg_discussion,
            requires_followup,
            activation_route,
            weight,
            notes
        )
        VALUES
        -- =====================================================
        -- IDG_REQUIRED + clinical escalation
        -- =====================================================
        (
            'critical_laboratory_value',
            'critical lab',
            'LAB',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Critical lab callback requires clinician awareness and IDG visibility.'
        ),
        (
            'critical_laboratory_result',
            'critical laboratory',
            'LAB',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Critical laboratory report requires clinician awareness and IDG visibility.'
        ),
        (
            '911_activation',
            '911',
            'SAFETY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'ADMIN_CLINICIAN_REPORT',
            100,
            '911 activation requires administrative and clinical awareness.'
        ),
        (
            'uncontrolled_bleeding',
            'uncontrolled bleeding',
            'SAFETY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Active uncontrolled bleeding requires clinician activation and MD report.'
        ),
        (
            'medication_error_harm',
            'medication error causing harm',
            'MEDICATION',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Medication error with harm requires clinician review and IDG visibility.'
        ),
        (
            'sentinel_event',
            'sentinel event',
            'SAFETY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_ADMIN_MD_REPORT',
            100,
            'Sentinel event requires clinician, administrator, and MD awareness.'
        ),
        (
            'suicidal_statement',
            'suicidal',
            'PSYCHOSOCIAL',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MSW_SC_AS_NEEDED',
            100,
            'Suicidal statement requires clinician/MSW/SC review as needed.'
        ),
        (
            'homicidal_statement',
            'homicidal',
            'PSYCHOSOCIAL',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MSW_SC_AS_NEEDED',
            100,
            'Homicidal statement requires clinician/MSW/SC review as needed.'
        ),
        (
            'abuse_allegation',
            'abuse',
            'SAFETY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MSW_SC_AS_NEEDED',
            100,
            'Abuse allegation requires clinician/MSW/SC review as needed.'
        ),
        (
            'immediate_safety_threat',
            'immediate safety threat',
            'SAFETY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MSW_SC_AS_NEEDED',
            100,
            'Immediate safety threat requires clinician/MSW/SC review as needed.'
        ),
        (
            'respiratory_distress_now',
            'respiratory distress',
            'RESPIRATORY',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Respiratory distress reported now requires clinician activation and MD report.'
        ),
        (
            'uncontrolled_pain_crisis',
            'uncontrolled pain',
            'PAIN',
            'IDG_REQUIRED',
            true,
            true,
            true,
            'CLINICIAN_MD_REPORT',
            100,
            'Uncontrolled pain crisis requires clinician activation and MD report.'
        ),

        -- =====================================================
        -- IDG_REQUIRED but not automatically clinical emergency
        -- =====================================================
        (
            'hospital_admission',
            'hospital admission',
            'HOSPITALIZATION',
            'IDG_REQUIRED',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            90,
            'Hospital admission is IDG-required because it may indicate change in condition, utilization, symptom burden, or care-plan implications.'
        ),
        (
            'er_visit',
            'er visit',
            'HOSPITALIZATION',
            'IDG_REQUIRED',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            90,
            'ER visit should be visible to IDG but is not automatically a clinician emergency in hospice.'
        ),
        (
            'emergency_room',
            'emergency room',
            'HOSPITALIZATION',
            'IDG_REQUIRED',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            90,
            'Emergency room utilization should be visible for IDG review.'
        ),

        -- =====================================================
        -- SIGNIFICANT hospice decline indicators
        -- =====================================================
        (
            'poor_intake',
            'poor intake',
            'NUTRITION',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            80,
            'Poor intake is a hospice decline indicator and should be visible to IDG.'
        ),
        (
            'not_eating',
            'not eating',
            'NUTRITION',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            80,
            'Not eating supports nutrition/decline review.'
        ),
        (
            'decreased_appetite',
            'decreased appetite',
            'NUTRITION',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            80,
            'Decreased appetite supports nutrition/decline review.'
        ),
        (
            'weight_loss',
            'weight loss',
            'NUTRITION',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            80,
            'Weight loss is significant for hospice decline documentation.'
        ),
        (
            'sleeping_more',
            'sleeping more',
            'DECLINE',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            75,
            'Increased sleeping may contribute to decline picture.'
        ),
        (
            'increased_sleeping',
            'increased sleeping',
            'DECLINE',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            75,
            'Increased sleeping may contribute to decline picture.'
        ),
        (
            'functional_decline',
            'functional decline',
            'FUNCTIONAL',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            85,
            'Functional decline supports IDG and POC review.'
        ),
        (
            'transfer_difficulty',
            'transfer difficulty',
            'FUNCTIONAL',
            'SIGNIFICANT',
            false,
            true,
            true,
            'IDG_REVIEW_ONLY',
            80,
            'Transfer difficulty may reflect functional decline.'
        ),
        (
            'fall',
            'fall',
            'SAFETY',
            'SIGNIFICANT',
            false,
            true,
            true,
            'CLINICIAN_REVIEW',
            80,
            'Fall requires clinical review and IDG visibility.'
        ),
        (
            'skin_breakdown',
            'skin breakdown',
            'SKIN',
            'SIGNIFICANT',
            false,
            true,
            true,
            'CLINICIAN_REVIEW',
            80,
            'Skin breakdown should be surfaced for clinical and IDG review.'
        ),
        (
            'pressure_injury',
            'pressure injury',
            'SKIN',
            'SIGNIFICANT',
            false,
            true,
            true,
            'CLINICIAN_REVIEW',
            80,
            'Pressure injury should be surfaced for clinical and IDG review.'
        ),
        (
            'caregiver_burnout',
            'caregiver burnout',
            'CAREGIVER',
            'SIGNIFICANT',
            false,
            true,
            true,
            'MSW_REVIEW',
            75,
            'Caregiver burnout may affect safety and plan of care.'
        ),

        -- =====================================================
        -- CLINICAL but not automatic IDG-required
        -- =====================================================
        (
            'medication_clarification',
            'medication clarification',
            'MEDICATION',
            'CLINICAL',
            false,
            false,
            true,
            'CLINICIAN_REVIEW',
            50,
            'Routine medication clarification needs follow-up but not automatic IDG discussion.'
        ),
        (
            'family_concern',
            'family concern',
            'CAREGIVER',
            'CLINICAL',
            false,
            false,
            true,
            'CLINICIAN_OR_MSW_REVIEW',
            50,
            'Family concern should be followed up but may not require automatic IDG discussion.'
        ),

        -- =====================================================
        -- ADMINISTRATIVE
        -- =====================================================
        (
            'fax_received',
            'fax received',
            'ADMINISTRATIVE',
            'ADMINISTRATIVE',
            false,
            false,
            false,
            'ADMIN_ONLY',
            10,
            'Administrative communication.'
        ),
        (
            'medical_records_request',
            'medical records request',
            'ADMINISTRATIVE',
            'ADMINISTRATIVE',
            false,
            false,
            false,
            'ADMIN_ONLY',
            10,
            'Administrative communication.'
        ),
        (
            'scheduling_update',
            'scheduling',
            'ADMINISTRATIVE',
            'ADMINISTRATIVE',
            false,
            false,
            false,
            'ADMIN_ONLY',
            10,
            'Administrative communication.'
        )
        ON CONFLICT (rule_key) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_idg_intelligence_reason_category", table_name="idg_intelligence_items")
    op.drop_index("ix_idg_intelligence_impact_level", table_name="idg_intelligence_items")

    op.drop_column("idg_intelligence_items", "activation_route")
    op.drop_column("idg_intelligence_items", "clinical_escalation_required")
    op.drop_column("idg_intelligence_items", "matched_priority_keyword")
    op.drop_column("idg_intelligence_items", "matched_priority_rule_id")
    op.drop_column("idg_intelligence_items", "idg_reason_category")
    op.drop_column("idg_intelligence_items", "idg_impact_level")

    op.drop_index("ix_idg_priority_rules_impact", table_name="idg_priority_rules")
    op.drop_index("ix_idg_priority_rules_category", table_name="idg_priority_rules")
    op.drop_index("ix_idg_priority_rules_keyword", table_name="idg_priority_rules")
    op.drop_index("ix_idg_priority_rules_active", table_name="idg_priority_rules")
    op.drop_table("idg_priority_rules")
