from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.hospitalization_prevention import (
    FamilyConcernItem,
    FamilyConcernCluster,
)
from app.models.idg_intelligence_item import IDGIntelligenceItem
from app.services.idg_priority_rules_engine import evaluate_idg_priority


# =========================================================
# FIELD-TEST SAFE CONSTANTS
# =========================================================
#
# These are not clinical conclusions.
# These are observed-pattern labels used to organize facts.
#
# Future hardening:
# Move these into tenant-configurable category tables.
# For field testing, these constants keep the behavior explicit
# and easy to review.


INTERNAL_STAFF_DISCIPLINES = {
    "RN",
    "LVN",
    "LPN",
    "MSW",
    "SC",
    "CHAPLAIN",
    "CHHA",
    "HHA",
    "AIDE",
    "VOLUNTEER",
    "MD",
    "NP",
    "PA",
    "DPCS",
    "ADMINISTRATOR",
    "ON_CALL",
    "ON-CALL",
    "STAFF",
}


HOSPITALIZATION_TERMS = (
    "hospital",
    "hospitalization",
    "take to hospital",
    "send to hospital",
    "go to hospital",
    "er",
    "emergency room",
    "911",
    "ambulance",
    "transfer",
    "send out",
)


AGGRESSIVE_TREATMENT_TERMS = (
    "iv fluids",
    "iv hydration",
    "hydration",
    "labs",
    "blood work",
    "antibiotic",
    "antibiotics",
    "insulin",
    "treatment",
    "treat this",
    "fix this",
)


POOR_INTAKE_TERMS = (
    "not eating",
    "not drinking",
    "poor intake",
    "no intake",
    "decreased intake",
    "refusing food",
    "refusing fluids",
    "not taking fluids",
    "loss of appetite",
    "appetite",
)


BLOOD_SUGAR_TERMS = (
    "blood sugar",
    "glucose",
    "sugar is high",
    "high sugar",
    "hyperglycemia",
    "diabetes",
    "diabetic",
    "insulin",
)


MEDICATION_UNDERSTANDING_TERMS = (
    "morphine",
    "comfort medication",
    "comfort meds",
    "opioid",
    "medication concern",
    "medication confusion",
    "not giving medication",
    "refusing medication",
    "afraid of medication",
    "medication is killing",
)


DISEASE_PROCESS_TERMS = (
    "does not understand hospice",
    "hospice is not helping",
    "why is hospice not doing",
    "why are we not treating",
    "wants treatment",
    "wants aggressive treatment",
    "wants everything done",
    "not ready",
    "not accepting",
)


CAREGIVER_STRESS_TERMS = (
    "caregiver overwhelmed",
    "family overwhelmed",
    "unable to care",
    "cannot manage",
    "can't manage",
    "burnout",
    "exhausted caregiver",
)


BEHAVIORAL_ESCALATION_TERMS = (
    "aggression",
    "aggressive",
    "violent",
    "hostile",
    "police",
    "5150",
    "facility unable to manage",
    "behavior",
    "behavioral",
)


CATEGORY_LABELS = {
    "HOSPITALIZATION_REQUEST": "Hospitalization Request",
    "ER_911_DISCUSSION": "ER / 911 Discussion",
    "COMORBIDITY_FOCUS_SHIFT": "Comorbidity Focus Shift",
    "TREATABLE_CONDITION_FOCUS": "Treatable Condition Focus",
    "POOR_INTAKE_WITH_FAMILY_CONCERN": "Poor Intake With Family Concern",
    "BLOOD_SUGAR_CONCERN": "Blood Sugar Concern",
    "HYDRATION_OR_NUTRITION_REQUEST": "Hydration / Nutrition Request",
    "MEDICATION_UNDERSTANDING_GAP": "Medication Understanding Gap",
    "DISEASE_PROCESS_UNDERSTANDING_GAP": "Disease Process Understanding Gap",
    "AGGRESSIVE_TREATMENT_REQUEST": "Aggressive Treatment Request",
    "CAREGIVER_UNABLE_TO_MANAGE": "Caregiver Unable To Manage",
    "BEHAVIORAL_ESCALATION": "Behavioral Escalation",
    "RECURRING_COMMON_CONCERN": "Recurring Common Concern",
    "UNCLASSIFIED_OBSERVED_PATTERN": "Unclassified Observed Pattern",
}


@dataclass(frozen=True)
class FamilyConcernHarvestResult:
    concern_item: FamilyConcernItem
    concern_cluster: FamilyConcernCluster
    idg_intelligence_item: IDGIntelligenceItem
    created_new_concern: bool
    created_new_cluster: bool
    observed_pattern_category: str
    clinician_review_status: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized(value: Any) -> str:
    return _safe_text(value).upper()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _is_internal_staff_source(
    *,
    source_discipline: Optional[str],
    reported_source_type: Optional[str],
) -> bool:
    discipline = _normalized(source_discipline)
    source_type = _normalized(reported_source_type)

    if discipline in INTERNAL_STAFF_DISCIPLINES:
        return True

    if source_type in INTERNAL_STAFF_DISCIPLINES:
        return True

    return False


def _review_status_for_source(
    *,
    source_discipline: Optional[str],
    reported_source_type: Optional[str],
) -> str:
    if _is_internal_staff_source(
        source_discipline=source_discipline,
        reported_source_type=reported_source_type,
    ):
        return "VERIFIED_STAFF_DOCUMENTATION"

    return "REPORTED_PENDING_PROTOCOL_REVIEW"


def _detect_observed_pattern_category(
    *,
    concern_text: str,
    source_excerpt: Optional[str],
    diagnosis_context: Optional[dict[str, Any]],
) -> str:
    combined = " ".join(
        part
        for part in [
            _safe_text(concern_text),
            _safe_text(source_excerpt),
            _safe_text(diagnosis_context),
        ]
        if part
    )

    has_hospital_term = _contains_any(
        combined,
        HOSPITALIZATION_TERMS,
    )

    has_aggressive_treatment = _contains_any(
        combined,
        AGGRESSIVE_TREATMENT_TERMS,
    )

    has_poor_intake = _contains_any(
        combined,
        POOR_INTAKE_TERMS,
    )

    has_blood_sugar = _contains_any(
        combined,
        BLOOD_SUGAR_TERMS,
    )

    has_medication_understanding = _contains_any(
        combined,
        MEDICATION_UNDERSTANDING_TERMS,
    )

    has_disease_process_gap = _contains_any(
        combined,
        DISEASE_PROCESS_TERMS,
    )

    has_caregiver_stress = _contains_any(
        combined,
        CAREGIVER_STRESS_TERMS,
    )

    has_behavioral_escalation = _contains_any(
        combined,
        BEHAVIORAL_ESCALATION_TERMS,
    )

    if "911" in combined or "emergency room" in combined.lower():
        return "ER_911_DISCUSSION"

    if has_hospital_term and has_blood_sugar:
        return "COMORBIDITY_FOCUS_SHIFT"

    if has_hospital_term:
        return "HOSPITALIZATION_REQUEST"

    if has_blood_sugar and has_poor_intake:
        return "POOR_INTAKE_WITH_FAMILY_CONCERN"

    if has_blood_sugar:
        return "BLOOD_SUGAR_CONCERN"

    if has_poor_intake or "hydration" in combined.lower():
        return "HYDRATION_OR_NUTRITION_REQUEST"

    if has_medication_understanding:
        return "MEDICATION_UNDERSTANDING_GAP"

    if has_aggressive_treatment:
        return "AGGRESSIVE_TREATMENT_REQUEST"

    if has_disease_process_gap:
        return "DISEASE_PROCESS_UNDERSTANDING_GAP"

    if has_caregiver_stress:
        return "CAREGIVER_UNABLE_TO_MANAGE"

    if has_behavioral_escalation:
        return "BEHAVIORAL_ESCALATION"

    return "UNCLASSIFIED_OBSERVED_PATTERN"


def _cluster_title_for_category(category: str) -> str:
    return CATEGORY_LABELS.get(
        category,
        "Observed Hospitalization Prevention Pattern",
    )


def _find_existing_concern_from_same_source(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    source_table: Optional[str],
    source_record_id: Optional[UUID],
    concern_category: str,
) -> Optional[FamilyConcernItem]:
    if not source_table or not source_record_id:
        return None

    return (
        db.query(FamilyConcernItem)
        .filter(
            FamilyConcernItem.tenant_id == tenant_id,
            FamilyConcernItem.patient_id == patient_id,
            FamilyConcernItem.source_table == source_table,
            FamilyConcernItem.source_record_id == source_record_id,
            FamilyConcernItem.concern_category == concern_category,
        )
        .first()
    )


def _get_or_create_cluster(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    benefit_period_id: Optional[UUID],
    category: str,
    now: datetime,
    created_by: Optional[UUID],
) -> tuple[FamilyConcernCluster, bool]:
    cluster = (
        db.query(FamilyConcernCluster)
        .filter(
            FamilyConcernCluster.tenant_id == tenant_id,
            FamilyConcernCluster.patient_id == patient_id,
            FamilyConcernCluster.primary_category == category,
            FamilyConcernCluster.cluster_status.in_(
                [
                    "OPEN",
                    "UNRESOLVED",
                    "PENDING_PROTOCOL_REVIEW",
                    "ACTIVE",
                ]
            ),
        )
        .order_by(FamilyConcernCluster.updated_at.desc())
        .first()
    )

    if cluster:
        return cluster, False

    cluster = FamilyConcernCluster(
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        primary_category=category,
        cluster_title=_cluster_title_for_category(category),
        cluster_summary=None,
        cluster_status="OPEN",
        occurrence_count=0,
        discipline_count=0,
        first_concern_at=now,
        last_concern_at=now,
        created_by=created_by,
        created_at=now,
        updated_by=created_by,
        updated_at=now,
    )

    db.add(cluster)
    db.flush()

    return cluster, True


def _update_cluster_counts(
    db: Session,
    *,
    cluster: FamilyConcernCluster,
    tenant_id: UUID,
    patient_id: UUID,
    category: str,
    now: datetime,
    updated_by: Optional[UUID],
) -> None:
    concern_rows = (
        db.query(FamilyConcernItem)
        .filter(
            FamilyConcernItem.tenant_id == tenant_id,
            FamilyConcernItem.patient_id == patient_id,
            FamilyConcernItem.concern_category == category,
            FamilyConcernItem.concern_status.in_(
                [
                    "OPEN",
                    "UNRESOLVED",
                    "PENDING_PROTOCOL_REVIEW",
                    "ACTIVE",
                ]
            ),
        )
        .all()
    )

    disciplines = {
        _normalized(row.source_discipline)
        for row in concern_rows
        if row.source_discipline
    }

    cluster.occurrence_count = len(concern_rows)
    cluster.discipline_count = len(disciplines)
    cluster.last_concern_at = now
    cluster.updated_by = updated_by
    cluster.updated_at = now

    if not cluster.first_concern_at and concern_rows:
        dates = [
            row.source_note_date
            for row in concern_rows
            if row.source_note_date
        ]
        cluster.first_concern_at = min(dates) if dates else now

    if not cluster.cluster_summary:
        cluster.cluster_summary = (
            "Observed hospitalization-prevention concern pattern "
            "identified from documented source evidence."
        )


def _create_or_update_idg_visibility_item(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    benefit_period_id: Optional[UUID],
    cluster: FamilyConcernCluster,
    concern: FamilyConcernItem,
    category: str,
    now: datetime,
) -> IDGIntelligenceItem:
    item = (
        db.query(IDGIntelligenceItem)
        .filter(
            IDGIntelligenceItem.tenant_id == tenant_id,
            IDGIntelligenceItem.patient_id == patient_id,
            IDGIntelligenceItem.source_table
            == "family_concern_clusters",
            IDGIntelligenceItem.source_record_id == cluster.id,
        )
        .first()
    )

    title = (
        "Hospitalization Prevention Pattern - "
        f"{_cluster_title_for_category(category)}"
    )[:255]

    summary = (
        "Observed hospitalization-prevention pattern surfaced "
        "from documented source evidence. "
        "Review and routing must follow tenant protocol. "
        f"Latest source excerpt: {concern.source_excerpt or concern.concern_text}"
    )

    if item is None:
        item = IDGIntelligenceItem(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            source_type="HOSPITALIZATION_PREVENTION",
            source_table="family_concern_clusters",
            source_record_id=cluster.id,
            created_at=now,
        )
        db.add(item)

    decision = evaluate_idg_priority(
        db=db,
        event_type="HOSPITALIZATION_PREVENTION",
        focus_area=category,
        summary=summary,
        details={
            "concern_category": category,
            "cluster_id": str(cluster.id),
            "latest_concern_id": str(concern.id),
            "tenant_protocol_required": True,
            "system_makes_clinical_conclusion": False,
        },
        source_type="HOSPITALIZATION_PREVENTION",
    )

    item.source_date = concern.source_note_date or now
    item.source_discipline = concern.source_discipline
    item.source_author_id = concern.source_author_id
    item.title = title
    item.summary = summary
    item.original_excerpt = concern.source_excerpt or concern.concern_text
    item.category = category
    item.requires_idg_discussion = True
    item.discussion_status = item.discussion_status or "PENDING"

    item.idg_impact_level = (
        decision.idg_impact_level
        or "CLINICAL"
    )
    item.idg_reason_category = (
        decision.category
        or category
    )
    item.matched_priority_rule_id = decision.matched_rule_id
    item.matched_priority_keyword = decision.matched_keyword

    item.requires_followup = True
    item.source_priority = (
        decision.source_priority
        or "NORMAL"
    )

    item.clinical_escalation_required = bool(
        decision.clinical_escalation_required
    )

    item.activation_route = (
        decision.activation_route
        or "TENANT_PROTOCOL_OR_DEFAULT_REVIEW"
    )

    item.harvest_reason = (
        "Hospitalization prevention observed pattern requires "
        "IDG visibility and tenant-protocol review. "
        "SNS surfaced documented evidence only and did not "
        "assign ownership, determine clinical truth, resolve the "
        "concern, or implement a plan-of-care change."
    )

    item.updated_at = now

    return item


def create_or_update_family_concern_from_source(
    *,
    db: Session,
    tenant_id: UUID,
    patient_id: UUID,
    concern_text: str,
    benefit_period_id: Optional[UUID] = None,
    source_type: Optional[str] = None,
    source_table: Optional[str] = None,
    source_record_id: Optional[UUID] = None,
    source_discipline: Optional[str] = None,
    source_author_id: Optional[UUID] = None,
    source_note_date: Optional[datetime] = None,
    source_excerpt: Optional[str] = None,
    reported_source_type: Optional[str] = None,
    diagnosis_context: Optional[dict[str, Any]] = None,
    created_by: Optional[UUID] = None,
    commit: bool = False,
) -> FamilyConcernHarvestResult:
    """
    Create or update a family concern item from a documented source.

    This function is intentionally fact-based.

    It does not:
    - decide clinical truth
    - decide preventability
    - assign staff
    - route to hard-coded roles
    - auto-resolve
    - auto-finalize
    - update the plan of care
    - close tasks

    It does:
    - preserve source evidence
    - identify observed pattern category
    - create/update FamilyConcernItem
    - create/update FamilyConcernCluster
    - surface IDG visibility through IDGIntelligenceItem
    - leave routing to tenant protocol or agency default rule
    """

    text_value = _safe_text(concern_text)

    if not tenant_id:
        raise ValueError(
            "tenant_id is required for hospitalization prevention harvest."
        )

    if not patient_id:
        raise ValueError(
            "patient_id is required for hospitalization prevention harvest."
        )

    if not text_value:
        raise ValueError(
            "concern_text is required for hospitalization prevention harvest."
        )

    now = _now()

    observed_category = _detect_observed_pattern_category(
        concern_text=text_value,
        source_excerpt=source_excerpt,
        diagnosis_context=diagnosis_context,
    )

    clinician_review_status = _review_status_for_source(
        source_discipline=source_discipline,
        reported_source_type=reported_source_type,
    )

    existing = _find_existing_concern_from_same_source(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        source_table=source_table,
        source_record_id=source_record_id,
        concern_category=observed_category,
    )

    created_new_concern = False

    if existing:
        concern = existing
        concern.concern_text = text_value
        concern.source_excerpt = source_excerpt or source_excerpt
        concern.source_discipline = source_discipline
        concern.source_author_id = source_author_id
        concern.source_note_date = source_note_date or concern.source_note_date
        concern.harvest_method = "RULE_BASED_OBSERVED_PATTERN"
        concern.confidence = "SOURCE_DOCUMENTED"
        concern.clinician_review_status = clinician_review_status
        concern.updated_by = created_by
        concern.updated_at = now
    else:
        concern = FamilyConcernItem(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            concern_category=observed_category,
            concern_text=text_value,
            concern_status="OPEN",
            source_type=source_type,
            source_table=source_table,
            source_record_id=source_record_id,
            source_discipline=source_discipline,
            source_author_id=source_author_id,
            source_note_date=source_note_date or now,
            source_excerpt=source_excerpt or text_value,
            harvest_method="RULE_BASED_OBSERVED_PATTERN",
            confidence="SOURCE_DOCUMENTED",
            clinician_review_status=clinician_review_status,
            created_by=created_by,
            created_at=now,
            updated_by=created_by,
            updated_at=now,
        )
        db.add(concern)
        db.flush()
        created_new_concern = True

    cluster, created_new_cluster = _get_or_create_cluster(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        category=observed_category,
        now=now,
        created_by=created_by,
    )

    _update_cluster_counts(
        db,
        cluster=cluster,
        tenant_id=tenant_id,
        patient_id=patient_id,
        category=observed_category,
        now=now,
        updated_by=created_by,
    )

    idg_item = _create_or_update_idg_visibility_item(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        cluster=cluster,
        concern=concern,
        category=observed_category,
        now=now,
    )

    if commit:
        db.commit()
        db.refresh(concern)
        db.refresh(cluster)
        db.refresh(idg_item)

    return FamilyConcernHarvestResult(
        concern_item=concern,
        concern_cluster=cluster,
        idg_intelligence_item=idg_item,
        created_new_concern=created_new_concern,
        created_new_cluster=created_new_cluster,
        observed_pattern_category=observed_category,
        clinician_review_status=clinician_review_status,
    )