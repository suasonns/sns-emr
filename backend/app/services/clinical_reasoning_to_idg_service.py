# services/clinical_reasoning_to_idg_service.py

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.clinical_reasoning_result import (
    ClinicalReasoningResult,
)

from app.models.idg_intelligence_item import (
    IDGIntelligenceItem,
)

from app.services.idg_priority_rules_engine import (
    evaluate_idg_priority,
)


def create_or_update_from_reasoning_result(
    *,
    db: Session,
    reasoning: ClinicalReasoningResult,
):
    """
    Harvest Clinical Reasoning results into
    IDG Intelligence.
    """

    if not reasoning.requires_idg_review:
        return None

    now = datetime.now(timezone.utc)

    item = (
        db.query(IDGIntelligenceItem)
        .filter(
            IDGIntelligenceItem.source_table
            == "clinical_reasoning_results",
            IDGIntelligenceItem.source_record_id
            == reasoning.id,
        )
        .first()
    )

    if item is None:
        item = IDGIntelligenceItem(
            tenant_id=reasoning.tenant_id,
            patient_id=reasoning.patient_id,
            source_type="CLINICAL_REASONING",
            source_table="clinical_reasoning_results",
            source_record_id=reasoning.id,
            created_at=now,
        )

        db.add(item)

    decision = evaluate_idg_priority(
        db=db,
        event_type=reasoning.reasoning_category,
        focus_area=reasoning.reasoning_category,
        summary=(
            reasoning.clinical_summary
            or reasoning.rationale
            or reasoning.interpretation_key
        ),
        details={},
        source_type="CLINICAL_REASONING",
    )

    item.title = reasoning.interpretation_key

    item.summary = (
        reasoning.clinical_summary
        or reasoning.rationale
        or reasoning.interpretation_key
    )

    item.original_excerpt = reasoning.rationale

    item.source_date = reasoning.created_at

    item.category = reasoning.reasoning_category

    item.discussion_status = "PENDING"

    item.requires_followup = (
        decision.requires_followup
    )

    item.requires_idg_discussion = (
        reasoning.requires_idg_review
    )

    item.source_priority = (
        decision.source_priority
    )

    item.idg_impact_level = (
        decision.idg_impact_level
    )

    item.idg_reason_category = (
        decision.category
    )

    item.matched_priority_rule_id = (
        decision.matched_rule_id
    )

    item.matched_priority_keyword = (
        decision.matched_keyword
    )

    item.clinical_escalation_required = (
        reasoning.requires_md_review
        or decision.clinical_escalation_required
    )

    item.activation_route = (
        decision.activation_route
    )

    item.harvest_reason = (
        "Clinical reasoning flagged for "
        "IDG review."
    )

    item.updated_at = now

    return item