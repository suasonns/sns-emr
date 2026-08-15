# services/idg_intelligence_service.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.idg_intelligence_item import IDGIntelligenceItem
from app.models.communications_log import CommunicationsLog
from app.services.idg_priority_rules_engine import evaluate_idg_priority


FOLLOWUP_KEYWORDS = (
    "CRITICAL",
    "FALL",
    "HOSPITAL",
    "ER ",
    "EMERGENCY",
    "SKIN",
    "WOUND",
    "PAIN",
    "MEDICATION",
    "CONFUSION",
    "DECLINE",
    "POOR INTAKE",
    "NOT EATING",
    "SHORTNESS OF BREATH",
    "SOB",
    "CHANGE IN CONDITION",
    "URGENT",
    "LAB",
    "ABNORMAL",
)

HIGH_PRIORITY_KEYWORDS = (
    "CRITICAL",
    "EMERGENCY",
    "HOSPITAL",
    "ER ",
    "911",
    "STAT",
    "SEVERE",
)

SOURCE_TYPE_KEYWORDS = (
    ("FAMILY", "FAMILY"),
    ("CAREGIVER", "CAREGIVER"),
    ("FACILITY", "FACILITY"),
    ("HOSPITAL", "HOSPITAL"),
    ("ER", "HOSPITAL"),
    ("PHYSICIAN", "MD_OFFICE"),
    ("DOCTOR", "MD_OFFICE"),
    ("MD OFFICE", "MD_OFFICE"),
    ("LAB", "LAB"),
    ("CRITICAL RESULT", "LAB"),
    ("CHHA", "STAFF"),
    ("AIDE", "STAFF"),
    ("HHA", "STAFF"),
    ("RN", "STAFF"),
    ("LVN", "STAFF"),
    ("MSW", "STAFF"),
    ("SC", "STAFF"),
)


def _safe_details(details: Any) -> dict:
    if isinstance(details, dict):
        return details
    return {}


def _combined_text(*values: Optional[str]) -> str:
    return " ".join(value or "" for value in values).upper()


def _infer_reported_source_type(entry: CommunicationsLog) -> str:
    details = _safe_details(entry.details)

    raw_source = (
        details.get("reported_source_type")
        or details.get("source_type")
        or details.get("caller_type")
        or details.get("reported_by_role")
        or ""
    )

    source = str(raw_source).strip().upper()

    if source:
        return source

    combined = _combined_text(
        entry.event_type,
        entry.summary,
    )

    for keyword, source_type in SOURCE_TYPE_KEYWORDS:
        if keyword in combined:
            return source_type

    return "OTHER"


def _requires_followup(entry: CommunicationsLog) -> bool:
    text = _combined_text(
        entry.event_type,
        entry.focus_area,
        entry.summary,
    )

    return any(keyword in text for keyword in FOLLOWUP_KEYWORDS)


def _source_priority(entry: CommunicationsLog) -> str:
    text = _combined_text(
        entry.event_type,
        entry.summary,
    )

    if any(keyword in text for keyword in HIGH_PRIORITY_KEYWORDS):
        return "HIGH"

    if _requires_followup(entry):
        return "NORMAL"

    return "LOW"


def create_or_update_from_communication_log(
    *,
    db: Session,
    entry: CommunicationsLog,
    received_by_name: Optional[str] = None,
    received_by_discipline: Optional[str] = None,
) -> IDGIntelligenceItem:
    """
    Harvest a patient-specific communication log into IDG intelligence.

    This does not create a clinical finding.
    This does not create a diagnosis.
    This does not modify the plan of care.
    This only creates an IDG-visible observation item.
    """

    if not entry.tenant_id:
        raise ValueError(
            "Cannot create IDG intelligence item without tenant_id."
        )

    if not entry.patient_id:
        raise ValueError(
            "Cannot create IDG intelligence item without patient_id."
        )

    details = _safe_details(entry.details)
    now = datetime.now(timezone.utc)

    item = (
        db.query(IDGIntelligenceItem)
        .filter(
            IDGIntelligenceItem.tenant_id == entry.tenant_id,
            IDGIntelligenceItem.patient_id == entry.patient_id,
            IDGIntelligenceItem.source_table == "communications_logs",
            IDGIntelligenceItem.source_record_id == entry.id,
        )
        .first()
    )

    title_parts = [entry.event_type or "Communication Log"]

    if entry.focus_area:
        title_parts.append(entry.focus_area)

    title = " - ".join(title_parts)[:255]

    if item is None:
        item = IDGIntelligenceItem(
            tenant_id=entry.tenant_id,
            patient_id=entry.patient_id,
            source_type="COMMUNICATION_LOG",
            source_table="communications_logs",
            source_record_id=entry.id,
            created_at=now,
        )
        db.add(item)

    item.source_date = entry.event_time
    item.source_author_id = entry.created_by
    item.title = title
    item.summary = entry.summary
    item.original_excerpt = entry.summary
    item.category = entry.focus_area

    if not item.discussion_status:
        item.discussion_status = "PENDING"

    item.communication_log_id = entry.id
    item.communication_event_type = entry.event_type
    item.communication_focus_area = entry.focus_area
    item.communication_event_time = entry.event_time
    item.communication_received_at = entry.created_at
    item.communication_status = entry.status
    item.communication_summary = entry.summary
    item.communication_details = details

    item.received_by_user_id = entry.created_by
    item.received_by_name = received_by_name
    item.received_by_discipline = received_by_discipline

    item.reported_by_name = (
        details.get("reported_by_name")
        or details.get("caller_name")
    )

    item.reported_by_role = (
        details.get("reported_by_role")
        or details.get("caller_role")
    )

    item.reported_by_discipline = details.get(
        "reported_by_discipline"
    )

    item.reported_source_type = _infer_reported_source_type(entry)

    item.reporting_organization = (
        details.get("reporting_organization")
        or details.get("facility_name")
        or details.get("hospital_name")
        or details.get("lab_name")
        or details.get("md_office_name")
    )

    item.is_critical_result = (
        "CRITICAL" in _combined_text(
            entry.event_type,
            entry.summary,
        )
        or bool(details.get("is_critical_result"))
    )

    item.critical_result_summary = details.get(
        "critical_result_summary"
    )

    item.harvest_reason = (
        "Communication log harvested for IDG visibility "
        "because it is a patient-specific report or concern "
        "requiring interdisciplinary availability."
    )

    decision = evaluate_idg_priority(
        db=db,
        event_type=entry.event_type,
        focus_area=entry.focus_area,
        summary=entry.summary,
        details=details,
        source_type="COMMUNICATION_LOG",
    )

    item.idg_impact_level = decision.idg_impact_level
    item.idg_reason_category = decision.category
    item.matched_priority_rule_id = decision.matched_rule_id
    item.matched_priority_keyword = decision.matched_keyword
    item.clinical_escalation_required = (
        decision.clinical_escalation_required
    )
    item.activation_route = decision.activation_route

    item.requires_followup = decision.requires_followup
    item.requires_idg_discussion = decision.requires_idg_discussion
    item.source_priority = decision.source_priority
    item.updated_at = now

    return item