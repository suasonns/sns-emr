# services/idg_priority_rules_engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.idg_priority_rule import IDGPriorityRule


from app.constants.idg_enums import (
    IDGImpactLevel,
)

IMPACT_RANK = {
    IDGImpactLevel.ADMINISTRATIVE.value: 0,
    IDGImpactLevel.CLINICAL.value: 1,
    IDGImpactLevel.SIGNIFICANT.value: 2,
    IDGImpactLevel.IDG_REQUIRED.value: 3,
}

SOURCE_PRIORITY_MAP = {
    IDGImpactLevel.ADMINISTRATIVE.value: "LOW",
    IDGImpactLevel.CLINICAL.value: "NORMAL",
    IDGImpactLevel.SIGNIFICANT.value: "HIGH",
    IDGImpactLevel.IDG_REQUIRED.value: "HIGH",
}


@dataclass(frozen=True)
class IDGPriorityDecision:
    idg_impact_level: str
    source_priority: str
    category: Optional[str]
    requires_followup: bool
    requires_idg_discussion: bool
    clinical_escalation_required: bool
    activation_route: Optional[str]
    matched_rule_id: Optional[str]
    matched_keyword: Optional[str]


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).upper().strip()


def _build_search_text(
    *,
    event_type: Optional[str],
    focus_area: Optional[str],
    summary: Optional[str],
    details: Optional[dict],
) -> str:
    detail_values = []

    if isinstance(details, dict):
        for key in (
            "reported_source_type",
            "reported_by_name",
            "reported_by_role",
            "reported_by_discipline",
            "reporting_organization",
            "critical_result_summary",
            "facility_name",
            "hospital_name",
            "lab_name",
            "md_office_name",
        ):
            value = details.get(key)
            if value:
                detail_values.append(str(value))

    return " ".join(
        [
            _normalize_text(event_type),
            _normalize_text(focus_area),
            _normalize_text(summary),
            _normalize_text(" ".join(detail_values)),
        ]
    )


def _better_rule(
    current: Optional[IDGPriorityRule],
    candidate: IDGPriorityRule,
) -> IDGPriorityRule:
    if current is None:
        return candidate

    current_rank = IMPACT_RANK.get(current.idg_impact_level, 0)
    candidate_rank = IMPACT_RANK.get(candidate.idg_impact_level, 0)

    if candidate_rank > current_rank:
        return candidate

    if candidate_rank == current_rank and candidate.weight > current.weight:
        return candidate

    return current


def evaluate_idg_priority(
    *,
    db: Session,
    event_type: Optional[str],
    focus_area: Optional[str],
    summary: Optional[str],
    details: Optional[dict] = None,
    source_type: Optional[str] = "COMMUNICATION_LOG",
) -> IDGPriorityDecision:
    """
    Evaluates hospice IDG impact for a communication or reported event.

    This engine does not create a clinical finding.
    This engine does not create a diagnosis.
    This engine does not change the plan of care.

    It only classifies whether the item should be visible to IDG,
    followed up clinically, or treated as administrative.
    """

    search_text = _build_search_text(
        event_type=event_type,
        focus_area=focus_area,
        summary=summary,
        details=details,
    )

    rules = (
        db.query(IDGPriorityRule)
        .filter(IDGPriorityRule.active.is_(True))
        .all()
    )

    best_match: Optional[IDGPriorityRule] = None

    for rule in rules:
        if rule.source_type and source_type:
            if rule.source_type.upper() != source_type.upper():
                continue

        keyword = _normalize_text(rule.keyword)

        if keyword and keyword in search_text:
            best_match = _better_rule(best_match, rule)

    if best_match is None:
        # Default: patient-specific communication is clinically visible
        # but not automatically IDG-required unless a rule matches.
        return IDGPriorityDecision(
            idg_impact_level=(
                IDGImpactLevel.CLINICAL.value
            ),
            source_priority="NORMAL",
            category=focus_area,
            requires_followup=True,
            requires_idg_discussion=False,
            clinical_escalation_required=False,
            activation_route="CLINICIAN_REVIEW",
            matched_rule_id=None,
            matched_keyword=None,
        )

    impact = best_match.idg_impact_level

    source_priority = SOURCE_PRIORITY_MAP.get(
        impact,
        "NORMAL",
    )

    return IDGPriorityDecision(
        idg_impact_level=impact,
        source_priority=source_priority,
        category=best_match.category,
        requires_followup=bool(
            best_match.requires_followup
        ),
        requires_idg_discussion=bool(
            best_match.requires_idg_discussion
        ),
        clinical_escalation_required=bool(
            best_match.clinical_escalation_required
        ),
        activation_route=best_match.activation_route,
        matched_rule_id=str(best_match.id),
        matched_keyword=best_match.keyword,
    )