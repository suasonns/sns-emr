# app/api/visits.py
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Set, Generator, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security, status
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationInfo,)
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.core.visit_type_normalizer import normalize_visit_type
from app.models.enums import (
    TaskStatus,
    TaskType,
    VisitFormType,
    CompletionReferenceType,
    TaskOrigin,
    TaskRegulatoryBasis,)
from app.models.clinical_note import ClinicalNote
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.task import Task
from app.models.user import User
from app.models.visit import Visit
from app.models.med_reconciliation import MedReconciliationItem
from app.models.sfv_requirement import SFVRequirement
from app.models.admission import Admission
from app.models.chha_visit_outcome import CHHAVisitOutcome
from app.models.chha_visit_task_result import CHHAVisitTaskResult
from app.models.cc_hourly_narrative_entry import CCHourlyNarrativeEntry
from app.models.rnica_assessment import RnicaAssessment
from app.services import rnica_poc_adapter
from app.services.rnica_finalization_service import evaluate_finalization_readiness
from app.services import rnica_amendment_service
from app.models.msw_ica_assessment import MswIcaAssessment, merge_msw_ica_form_data
from app.models.scica_assessment import ScicaAssessment, merge_scica_form_data
from app.services.icd_intelligence import gather_patient_evidence
from app.services.rnica_intelligence import build_rnica_intelligence
from app.services.msw_ica_intelligence import build_msw_ica_intelligence
from app.services.chha_outcome_service import upsert_chha_outcome
from app.services.diagnosis_sync_service import sync_official_primary_diagnosis
from app.services.audit_logger import log_event
from app.services.bereavement_aggregation_engine import (
    BereavementAggregationEngine,
    BereavementNoteInput,)
from app.services.dynamic_condition_detection_engine import (
    DynamicConditionDetectionEngine,
    NoteInput,)
from app.services.refusal_engine import record_refusal
from app.services.task_completion import auto_complete_tasks_for_visit
from app.domain.forms.form_resolution_service import resolve_form_package
from app.services.visit_compliance_guards import (
    enforce_commlog_for_visit_status_change,)
from app.services.hope_phase_b_engine import (
    complete_sfv_requirement_from_visit,
    process_huv_finalize,
    process_initial_rn_ica_finalize,)
from app.services.clinical_reasoning_engine import ClinicalReasoningEngine
from app.services.reasoning_result_to_recommendation_service import (
    ReasoningResultToRecommendationService,)
from app.services import clinical_reasoning_bridge
from app.services.clinical_note_validation_engine import (
    validate_and_trigger_incident,)
from app.services.task_service import (
    create_abuse_neglect_exploitation_task,
    create_spiritual_care_suicide_risk_escalation_task,
    create_suicide_risk_escalation_task,)
logger = logging.getLogger(__name__)
def _flatten_rnica_primary_diagnosis(form_data: dict) -> str | None:
    primary = ((form_data or {}).get("diagnoses") or {}).get("primaryDiagnosis") or {}
    icd10 = str(primary.get("icd10") or "").strip()
    description = str(primary.get("description") or "").strip()
    if description and icd10:
        return f"{description} ({icd10})"
    return description or icd10 or None
def _flatten_rnica_list_items(items: list | None) -> list[str]:
    flattened: list[str] = []
    for item in items or []:
        if isinstance(item, str):
            text = item.strip()
            if text:
                flattened.append(text)
            continue
        if not isinstance(item, dict):
            continue
        icd10 = str(item.get("icd10") or item.get("code") or "").strip()
        description = str(item.get("description") or item.get("name") or item.get("label") or "").strip()
        reaction = str(item.get("reaction") or "").strip()
        text = ""
        if description and icd10:
            text = f"{description} ({icd10})"
        else:
            text = description or icd10
        if reaction and text:
            text = f"{text} — {reaction}"
        elif reaction:
            text = reaction
        if text:
            flattened.append(text)
    return flattened
def _build_rnica_secondary_summary(form_data: dict) -> str | None:
    diagnoses = (form_data or {}).get("diagnoses") or {}
    secondary = _flatten_rnica_list_items(diagnoses.get("secondaryDiagnoses"))
    comorbidities = _flatten_rnica_list_items(diagnoses.get("comorbidities"))
    sections: list[str] = []
    if secondary:
        sections.append(
            "Secondary Diagnoses:\n" + "\n".join(f"- {item}" for item in secondary)
        )
    if comorbidities:
        sections.append(
            "Comorbidities:\n" + "\n".join(f"- {item}" for item in comorbidities)
        )
    return "\n\n".join(sections) if sections else None
def _build_rnica_allergy_summary(form_data: dict) -> tuple[bool | None, str | None]:
    allergies = _flatten_rnica_list_items(
        ((form_data or {}).get("infection") or {}).get("allergies")
    )
    if not allergies:
        return False, None
    return True, "\n".join(f"- {item}" for item in allergies)
def _sync_facesheet_from_rnica(
    db: Session,
    *,
    tenant_id: uuid.UUID | None,
    patient_id: uuid.UUID,
    form_data: dict,) -> None:
    if tenant_id is None:
        logger.warning(
            "RNICA facesheet sync skipped: missing tenant_id for patient %s",
            patient_id,
        )
        return
    try:
        facesheet = (
            db.query(PatientFaceSheet)
            .filter(
                PatientFaceSheet.tenant_id == tenant_id,
                PatientFaceSheet.patient_id == patient_id,
            )
            .first()
        )
        if not facesheet:
            logger.warning(
                "RNICA facesheet sync skipped: facesheet missing for patient %s",
                patient_id,
            )
            return
        has_allergies, allergies_text = _build_rnica_allergy_summary(form_data)
        facesheet.primary_diagnosis = _flatten_rnica_primary_diagnosis(form_data)
        facesheet.secondary_diagnoses = _build_rnica_secondary_summary(form_data)
        facesheet.has_allergies = has_allergies
        facesheet.allergies = allergies_text
        facesheet.updated_at = datetime.now(timezone.utc)
        facesheet.updated_by = facesheet.updated_by or facesheet.created_by
        db.commit()
    except Exception:
        db.rollback()
        logger.warning(
            "RNICA facesheet sync failed for patient %s",
            patient_id,
            exc_info=True,
        )
def _resolve_current_user_display_name(db: Session, current_user: CurrentUser) -> str:
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if user:
        return str(user.display_name or user.full_name or current_user.email or current_user.user_id).strip()
    return str(current_user.email or current_user.user_id).strip()
def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()
def _is_msw_suicide_risk_indicated(form_data: dict[str, Any] | None) -> bool:
    payload = merge_msw_ica_form_data(form_data)
    patient_concerns = set(((payload.get("patientDistress") or {}).get("patientConcerns") or []))
    family_crisis = set(((payload.get("familyDistress") or {}).get("familyCrisis") or []))
    return "Suicide risks" in patient_concerns or "Suicide risks" in family_crisis
def _msw_suicide_notifications_complete(form_data: dict[str, Any] | None) -> bool:
    payload = merge_msw_ica_form_data(form_data)
    suicide = ((payload.get("patientDistress") or {}).get("suicideRisk") or {})
    return bool(
        suicide.get("notifiedCaseManagerSupervisor")
        and suicide.get("notifiedAttendingPhysician")
    )
def _msw_abuse_categories(form_data: dict[str, Any] | None) -> list[str]:
    payload = merge_msw_ica_form_data(form_data)
    abuse = ((payload.get("patientDistress") or {}).get("abuseNeglectExploitation") or {})
    return list(abuse.get("categories") or [])
def _prepare_msw_ica_form_data(
    db: Session,
    current_user: CurrentUser,
    form_data: dict[str, Any] | None,
    *,
    bind_signatures: bool = False,) -> dict[str, Any]:
    payload = merge_msw_ica_form_data(form_data)
    current_user_name = _resolve_current_user_display_name(db, current_user)
    abuse = payload["patientDistress"]["abuseNeglectExploitation"]
    if abuse.get("categories") or abuse.get("reportedTo") or abuse.get("reportDate") or abuse.get("reportReferenceCaseNumber"):
        abuse["reportedBy"] = current_user_name
        abuse["reportedByUserId"] = str(current_user.user_id)
    if bind_signatures:
        finalization = payload["finalization"]
        finalization["assessment_complete"] = True
        finalization["clinician_name"] = current_user_name
        finalization["clinician_user_id"] = str(current_user.user_id)
        if not finalization.get("signature_date"):
            finalization["signature_date"] = _today_iso()
        if finalization.get("countersign_required"):
            finalization["countersign_staff_name"] = current_user_name
            finalization["countersign_staff_user_id"] = str(current_user.user_id)
            if not finalization.get("countersign_signature_date"):
                finalization["countersign_signature_date"] = _today_iso()
    return payload
def _build_suicide_risk_summary(form_data: dict[str, Any]) -> str:
    suicide = ((form_data.get("patientDistress") or {}).get("suicideRisk") or {})
    selected: list[str] = []
    if suicide.get("ageSexRiskFactorsPresent"):
        selected.append("age/sex statistical risk factors")
    if suicide.get("earlyChildhoodLoss"):
        selected.append("early childhood loss")
    if suicide.get("currentAlcoholDrugAbuse"):
        selected.append("current alcohol/drug abuse")
    if suicide.get("recentIrreversibleLoss"):
        selected.append("recent irreversible loss")
    if suicide.get("specificSuicidePlanIdentified"):
        selected.append("specific suicide plan identified")
    if suicide.get("lethalityOfMethod"):
        selected.append(f"lethality {suicide.get('lethalityOfMethod')}")
    if suicide.get("meansAvailability"):
        selected.append(f"means availability {suicide.get('meansAvailability')}")
    if suicide.get("notes"):
        selected.append(f"notes: {str(suicide.get('notes')).strip()[:160]}")
    return ", ".join(selected) if selected else "Suicide risk selected in MSW ICA assessment"
def _sync_msw_ica_escalations(
    db: Session,
    *,
    assessment: MswIcaAssessment,
    patient: Patient,
    current_user: CurrentUser,
    previous_form_data: dict[str, Any] | None,
    next_form_data: dict[str, Any],) -> None:
    tenant_id = getattr(patient, "tenant_id", None)
    if tenant_id is None:
        logger.warning("MSW ICA escalation skipped: patient %s missing tenant_id", patient.id)
        return
    if _is_msw_suicide_risk_indicated(next_form_data) and (
        not _is_msw_suicide_risk_indicated(previous_form_data)
        or not _msw_suicide_notifications_complete(next_form_data)
    ):
        create_suicide_risk_escalation_task(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            assessment_id=assessment.id,
            created_by=current_user.user_id,
            risk_summary=_build_suicide_risk_summary(next_form_data),
        )
    abuse_categories = _msw_abuse_categories(next_form_data)
    if abuse_categories:
        create_abuse_neglect_exploitation_task(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            assessment_id=assessment.id,
            created_by=current_user.user_id,
            categories=abuse_categories,
        )
def _is_scica_suicide_risk_indicated(form_data: dict[str, Any] | None) -> bool:
    payload = merge_scica_form_data(form_data)
    patient_sources = set(((payload.get("patientDistress") or {}).get("sources") or []))
    caregiver_sources = set(((payload.get("caregiverDistress") or {}).get("sources") or []))
    return "Suicidal thoughts" in patient_sources or "Suicidal thoughts" in caregiver_sources
def _scica_suicide_notifications_complete(form_data: dict[str, Any] | None) -> bool:
    payload = merge_scica_form_data(form_data)
    patient = payload.get("patientDistress") or {}
    caregiver = payload.get("caregiverDistress") or {}
    def section_complete(section: dict[str, Any]) -> bool:
        suicide = section.get("suicideRisk") or {}
        return bool(
            suicide.get("notifiedCaseManagerSupervisor")
            and suicide.get("notifiedAttendingPhysician")
        )
    patient_selected = "Suicidal thoughts" in set(patient.get("sources") or [])
    caregiver_selected = "Suicidal thoughts" in set(caregiver.get("sources") or [])
    return (not patient_selected or section_complete(patient)) and (not caregiver_selected or section_complete(caregiver))
def _prepare_scica_form_data(
    db: Session,
    current_user: CurrentUser,
    form_data: dict[str, Any] | None,
    *,
    bind_signatures: bool = False,) -> dict[str, Any]:
    payload = merge_scica_form_data(form_data)
    current_user_name = _resolve_current_user_display_name(db, current_user)
    signature = payload["signature"]
    if bind_signatures:
        signature["signedByName"] = current_user_name
        signature["signedByUserId"] = str(current_user.user_id)
        signature["signedDate"] = _today_iso()
    elif signature.get("acknowledgement"):
        signature["signedByName"] = current_user_name
        signature["signedByUserId"] = str(current_user.user_id)
        if not signature.get("signedDate"):
            signature["signedDate"] = _today_iso()
    return payload
def _build_scica_suicide_risk_summary(form_data: dict[str, Any]) -> str:
    payload = merge_scica_form_data(form_data)
    summaries: list[str] = []
    def describe(section_key: str, label: str) -> None:
        section = payload.get(section_key) or {}
        if "Suicidal thoughts" not in set(section.get("sources") or []):
            return
        suicide = section.get("suicideRisk") or {}
        selected: list[str] = []
        if suicide.get("ageSexRiskFactorsPresent"):
            selected.append("age/sex statistical risk factors")
        if suicide.get("earlyChildhoodLoss"):
            selected.append("early childhood loss")
        if suicide.get("currentAlcoholDrugAbuse"):
            selected.append("current alcohol/drug abuse")
        if suicide.get("recentIrreversibleLoss"):
            selected.append("recent irreversible loss")
        if suicide.get("specificSuicidePlanIdentified"):
            selected.append("specific suicide plan identified")
        if suicide.get("lethalityOfMethod"):
            selected.append(f"lethality {suicide.get('lethalityOfMethod')}")
        if suicide.get("meansAvailability"):
            selected.append(f"means availability {suicide.get('meansAvailability')}")
        if suicide.get("notes"):
            selected.append(f"notes: {str(suicide.get('notes')).strip()[:160]}")
        summary = ", ".join(selected) if selected else "Suicidal thoughts selected"
        summaries.append(f"{label}: {summary}")
    describe("patientDistress", "Patient")
    describe("caregiverDistress", "Caregiver")
    return " | ".join(summaries) if summaries else "Suicide risk selected in SCICA assessment"
def _sync_scica_escalations(
    db: Session,
    *,
    assessment: ScicaAssessment,
    patient: Patient,
    current_user: CurrentUser,
    previous_form_data: dict[str, Any] | None,
    next_form_data: dict[str, Any],) -> None:
    tenant_id = getattr(patient, "tenant_id", None)
    if tenant_id is None:
        logger.warning("SCICA escalation skipped: patient %s missing tenant_id", patient.id)
        return
    if _is_scica_suicide_risk_indicated(next_form_data) and (
        not _is_scica_suicide_risk_indicated(previous_form_data)
        or not _scica_suicide_notifications_complete(next_form_data)
    ):
        create_spiritual_care_suicide_risk_escalation_task(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            assessment_id=assessment.id,
            created_by=current_user.user_id,
            risk_summary=_build_scica_suicide_risk_summary(next_form_data),
        )
def _rating_to_decimal(value: Any) -> Optional[Decimal]:
    """
    MSW/SC distress ratings are free-text/select fields (e.g. a 0-10
    numeric string, or a severity label like "Severe"/"Moderate"/"Mild").
    Normalize either shape to a 0-10 Decimal scale for the shared
    Clinical Reasoning Engine, which expects a numeric distress score.
    """
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        pass
    label = str(value).strip().lower()
    label_scale = {
        "severe": Decimal("9"),
        "high": Decimal("9"),
        "moderate": Decimal("6"),
        "mild": Decimal("3"),
        "low": Decimal("3"),
        "none": Decimal("0"),
    }
    return label_scale.get(label)
def _extract_msw_ica_reasoning_payload(form_data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Bridges MSW ICA form_data into the flat assessment_data dict the
    shared ClinicalReasoningEngine expects. Suicide risk / abuse-neglect
    are surfaced here too (in addition to their existing dedicated urgent
    Task escalation) so the whole care team has one shared source of
    intelligence.
    """
    payload = merge_msw_ica_form_data(form_data or {})
    patient_distress = payload.get("patientDistress") or {}
    family_distress = payload.get("familyDistress") or {}
    financial_legal = payload.get("financialLegal") or {}
    narrative = payload.get("narrative") or {}
    out: dict[str, Any] = {}
    if _is_msw_suicide_risk_indicated(payload):
        out["suicide_risk_identified"] = True
        out["suicide_risk_detail"] = _build_suicide_risk_summary(payload)
    abuse_categories = _msw_abuse_categories(payload)
    if abuse_categories:
        out["abuse_neglect_suspected"] = True
        out["abuse_neglect_detail"] = ", ".join(abuse_categories)
    patient_distress_score = _rating_to_decimal(patient_distress.get("distressRating"))
    if patient_distress_score is not None:
        out["patient_distress_score"] = patient_distress_score
    caregiver_distress_score = _rating_to_decimal(family_distress.get("pcgAnxietyRating"))
    if caregiver_distress_score is not None:
        out["caregiver_distress_score"] = caregiver_distress_score
    if (
        str(family_distress.get("abilityToProvideCare") or "").strip().lower() in {"unable", "no", "poor"}
        or str(family_distress.get("willingnessToProvideCare") or "").strip().lower() in {"unwilling", "no"}
        or family_distress.get("familyCrisis")
    ):
        out["caregiver_capacity_concern"] = True
        detail_parts = [
            part
            for part in [
                family_distress.get("abilityToProvideCare") and f"ability to provide care: {family_distress.get('abilityToProvideCare')}",
                family_distress.get("willingnessToProvideCare") and f"willingness to provide care: {family_distress.get('willingnessToProvideCare')}",
                family_distress.get("familyCrisis") and f"family crisis: {', '.join(family_distress.get('familyCrisis') or [])}",
            ]
            if part
        ]
        if detail_parts:
            out["caregiver_capacity_detail"] = "; ".join(detail_parts)
    if financial_legal.get("patientLacks") or financial_legal.get("needsAssistance"):
        out["unmet_needs_identified"] = True
        needs_parts = [
            part
            for part in [
                financial_legal.get("patientLacks") and f"lacks: {', '.join(financial_legal.get('patientLacks') or [])}",
                financial_legal.get("needsAssistance") and f"needs assistance: {', '.join(financial_legal.get('needsAssistance') or [])}",
            ]
            if part
        ]
        if needs_parts:
            out["unmet_needs_detail"] = "; ".join(needs_parts)
    narrative_notes = narrative.get("notes") or patient_distress.get("notes")
    if narrative_notes:
        out["psychosocial_narrative"] = str(narrative_notes)
    if out:
        out["source"] = "MSW"
    return out
def _extract_scica_reasoning_payload(form_data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Bridges Spiritual Care (SCICA) form_data into the flat assessment_data
    dict the shared ClinicalReasoningEngine expects. Suicide risk is
    surfaced here too (in addition to its existing dedicated urgent Task
    escalation) so the whole care team has one shared source of
    intelligence.
    """
    payload = merge_scica_form_data(form_data or {})
    patient_distress = payload.get("patientDistress") or {}
    caregiver_distress = payload.get("caregiverDistress") or {}
    narrative = payload.get("narrative") or {}
    spiritual = payload.get("spiritualCircumstances") or {}
    out: dict[str, Any] = {}
    if _is_scica_suicide_risk_indicated(payload):
        out["suicide_risk_identified"] = True
        out["suicide_risk_detail"] = _build_scica_suicide_risk_summary(payload)
    patient_distress_score = _rating_to_decimal(patient_distress.get("rating"))
    if patient_distress_score is not None:
        out["patient_distress_score"] = patient_distress_score
    caregiver_distress_score = _rating_to_decimal(caregiver_distress.get("rating"))
    if caregiver_distress_score is not None:
        out["caregiver_distress_score"] = caregiver_distress_score
    if spiritual.get("spiritualIssuesConcern") or spiritual.get("spiritualSupport"):
        out["spiritual_distress"] = True
    narrative_notes = narrative.get("note")
    if narrative_notes:
        out["psychosocial_narrative"] = str(narrative_notes)
    if out:
        out["source"] = "SC"
    return out
# =========================================================
# ROUTER
# =========================================================
router = APIRouter(prefix="/visits", tags=["visits"])
# =========================================================
# CONSTANTS
# =========================================================
ALLOWED_VISIT_TYPES: Set[str] = {
    "RN",
    "LVN",
    "NP",
    "PA",
    "MD",
    "SW",
    "CHAPLAIN",
    "AIDE",
    "ADMINISTRATIVE",}
ALLOWED_STATUS_CHANGES: Set[str] = {
    "MISSED",
    "RESCHEDULED",}
TELEPHONE_MODES: Set[str] = {
    "TELEPHONE",
    "PHONE",
    "TEL",
    "CALL",}
VISIT_CORRECTION_WINDOW_HOURS = 72
# Reopening a FINALIZED visit is a distinct, higher-bar action from
# approving/denying an amendment (see AMENDMENT_APPROVAL_ROLES below): per
# owner direction, rank-and-file staff may NEVER unlock a locked/finalized
# chart. Only Administrator, DPCS, DPCS Designee, Supervisor, or Case
# Manager may reopen finalized documentation. ("ADMIN"/"ADMINISTRATOR" are
# both accepted -- this codebase uses both spellings for the same role.)
ALLOWED_REOPEN_ROLES = {
    "ADMIN",
    "ADMINISTRATOR",
    "DPCS",
    "DPCS_DESIGNEE",
    "SUPERVISOR",
    "CASE_MANAGER",}
# SECTION 12 -- Amendment Infrastructure review authority. This governs who
# may approve/deny a *proposed* amendment record; it does NOT unlock or
# modify the original locked assessment (see ALLOWED_REOPEN_ROLES above,
# which has its own, separately-defined set of higher-bar roles). Per owner
# direction: DPCS is this system's name for the DON role. Case Manager and
# Supervisor may also review/decide amendments; QA/ADMIN/SYSTEM retain
# oversight parity.
AMENDMENT_APPROVAL_ROLES = {
    "DPCS",
    "DPCS_DESIGNEE",
    "CASE_MANAGER",
    "SUPERVISOR",
    "ADMIN",
    "QA",
    "SYSTEM",}
VISIT_TYPE_ALIASES: dict[str, str] = {
    "SN": "RN",
    "MSW": "SW",
    "BSW": "SW",
    "LCSW": "SW",
    "SC": "CHAPLAIN",
    "CHHA": "AIDE",}
ISSUE_EVENT_TYPES: Set[str] = {
    "CHANGE_OF_CONDITION",
    "NEW_ORDER",
    "UPDATE_ASSESSMENT",
    "RECERT",}
GENERIC_NOTE_TYPES: Set[str] = {
    "VISIT",
    "NOTE",
    "FORM",
    "CLINICAL_NOTE",}
ASSESSMENT_EVENT_FORM_TYPES: Set[str] = {
    VisitFormType.ASSESS.value,}
MODERATE_OR_SEVERE: Set[str] = {"MODERATE", "SEVERE"}
# =========================================================
# ENGINE SINGLETONS
# =========================================================condition_engine = DynamicConditionDetectionEngine()bereavement_engine = BereavementAggregationEngine()clinical_reasoning_engine = ClinicalReasoningEngine()reasoning_recommendation_service = ReasoningResultToRecommendationService()
# =========================================================
# DB DEPENDENCY
# =========================================================
def get_db(request: Request) -> Generator[Session, None, None]:
    db = SessionLocal()
    request.state.db = db
    try:
        yield db
    finally:
        db.close()
@router.post("/rnica/save")
def save_rnica_assessment(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    patient_id_raw = (payload or {}).get("patientId")
    form_data = (payload or {}).get("formData") or {}
    if not patient_id_raw:
        raise HTTPException(status_code=422, detail="patientId is required")
    try:
        patient_uuid = uuid.UUID(str(patient_id_raw))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="patientId must be a valid UUID") from None
    patient = get_authorized_patient(db, patient_uuid, current_user)
    assessment = RnicaAssessment(
        patient_id=patient_uuid,
        tenant_id=getattr(patient, "tenant_id", None),
        form_data=form_data,
        assessment_type="RNICA",
        status="DRAFT",
        locked=False,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    _sync_facesheet_from_rnica(
        db,
        tenant_id=getattr(patient, "tenant_id", None),
        patient_id=patient_uuid,
        form_data=form_data,
    )
    return {"assessmentId": str(assessment.id), "status": "saved"}
@router.get("/rnica/{assessment_id}")
def get_rnica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": record.form_data or {},
        "locked": record.locked,
        "lockedAt": record.locked_at.isoformat() if record.locked_at else None,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.get("/rnica/by-patient/{patient_id}")
def get_rnica_assessment_by_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None
    get_authorized_patient(db, patient_uuid, current_user)
    records = (
        db.query(RnicaAssessment)
        .filter(RnicaAssessment.patient_id == patient_uuid)
        .order_by(RnicaAssessment.created_at.desc())
        .all()
    )
    record = next((item for item in records if not item.locked), None) or (records[0] if records else None)
    if not record:
        return {"assessmentId": None}
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": record.form_data or {},
        "locked": record.locked,
        "lockedAt": record.locked_at.isoformat() if record.locked_at else None,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.put("/rnica/{assessment_id}")
def update_rnica_assessment(
    assessment_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    if record.locked:
        # SECTION 12 — a locked/signed RN ICA is immutable at the API layer,
        # not just in the UI. This is intentionally NOT the amendment
        # workflow itself (that infrastructure is not built yet) — it is
        # the documented future entry point: a distinct, traceable
        # correction/addendum path (see POST /rnica/{id}/correction-request)
        # will be layered in later without ever rewriting signed content.
        raise HTTPException(
            status_code=423,
            detail=(
                "This RN ICA assessment is locked and cannot be edited. "
                "Use the correction/amendment workflow (POST /rnica/{assessment_id}/correction-request) "
                "to request a traceable addendum instead of modifying signed content."
            ),
        )
    form_data = (payload or {}).get("formData") or record.form_data or {}
    record.form_data = form_data
    record.status = "DRAFT"
    db.commit()
    patient = (
        db.query(Patient)
        .filter(Patient.id == record.patient_id)
        .first()
    )
    _sync_facesheet_from_rnica(
        db,
        tenant_id=getattr(patient, "tenant_id", None) if patient else None,
        patient_id=record.patient_id,
        form_data=form_data,
    )
    return {
        "assessmentId": str(record.id),
        "status": "updated",
        "locked": record.locked,
    }
@router.post("/rnica/{assessment_id}/lock")
def lock_rnica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    if record.locked:
        # Idempotent: re-locking an already-locked assessment is a no-op,
        # not an error — it must not re-run readiness checks (which could
        # spuriously fail if reference data changed after signing) or emit
        # a duplicate audit event for the same signature.
        return {
            "assessmentId": str(record.id),
            "status": "locked",
            "locked": True,
            "lockedAt": record.locked_at.isoformat() if record.locked_at else None,
        }
    # SECTION 12 — the backend re-checks the *same* readiness rules the
    # Final Review Dashboard shows (see rnica_finalization_service /
    # GET .../finalization-readiness). A disabled Lock button in the UI is
    # a courtesy; this is the actual enforcement boundary, since the lock
    # endpoint can be called directly.
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    tenant_id = record.tenant_id or getattr(patient, "tenant_id", None)
    poc_problems: list = []
    if tenant_id is not None:
        poc_problems = rnica_poc_adapter.list_all_problems(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
        )
    readiness = evaluate_finalization_readiness(record.form_data or {}, poc_problems)
    if not readiness["ready"]:
        unmet = [check["label"] for check in readiness["checks"].values() if not check["ready"]]
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot lock: required Section 12 finalization checks have not passed.",
                "unmetChecks": unmet,
                "checks": readiness["checks"],
            },
        )
    record.locked = True
    record.status = "LOCKED"
    record.locked_at = datetime.now(timezone.utc)
    db.commit()
    # POC changes remain strictly clinician-initiated. Locking RN ICA must
    # only validate, sign/lock, and preserve assessment data — it must NOT
    # create, update, resolve, or silently apply any Plan of Care problem or
    # version. The existing POC-generation engine (poc_generation_service)
    # is intentionally NOT invoked here; it is only reachable through the
    # explicit "Add to POC" control (see app/api/routes/rnica_poc.py), which
    # requires an explicit clinician action.
    db.info["tenant_id"] = tenant_id
    _safe_log_event(
        db=db,
        user_id=getattr(current_user, "id", None) or getattr(current_user, "user_id", None),
        action="RNICA_ASSESSMENT_LOCKED",
        entity_type="rnica_assessment",
        entity_id=record.id,
        metadata={
            "patientId": str(record.patient_id),
            "signatureCertification": bool(((record.form_data or {}).get("finalization") or {}).get("signatureCertification")),
            "clinicianSignature": ((record.form_data or {}).get("finalization") or {}).get("clinicianSignature"),
            "lockedAt": record.locked_at.isoformat(),
        },
    )
    db.commit()
    return {
        "assessmentId": str(record.id),
        "status": "locked",
        "locked": True,
        "lockedAt": record.locked_at.isoformat(),
    }
class RnicaAmendmentRequest(BaseModel):
    section_reference: Optional[str] = None
    amendment_category: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    requested_change: str = Field(..., min_length=1)
    request_source: str = Field(default="STAFF")
    original_value_snapshot: Optional[Any] = None
    proposed_value: Optional[Any] = None
    @field_validator("requested_change")
    @classmethod
    def _requested_change_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("requested_change must not be blank")
        return v
class RnicaAmendmentApproveRequest(BaseModel):
    decision_reason: Optional[str] = None
class RnicaAmendmentDenyRequest(BaseModel):
    decision_reason: str = Field(..., min_length=1)
    @field_validator("decision_reason")
    @classmethod
    def _decision_reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_reason must not be blank")
        return v
def _load_locked_rnica_assessment_for_amendment(db: Session, assessment_id: str, current_user: CurrentUser) -> RnicaAssessment:
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    return record
@router.post("/rnica/{assessment_id}/correction-request")
def request_rnica_correction(
    assessment_id: str,
    payload: RnicaAmendmentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """SECTION 12 — Amendment Infrastructure. Submits a distinct,
    timestamped, attributable correction/addendum entry against an
    already-locked (signed) RN ICA assessment.
    A locked RN ICA is immutable (see `update_rnica_assessment`) — this
    endpoint NEVER modifies `record.form_data`. It only creates a new,
    separate `RnicaAmendment` row in PENDING status, awaiting review by
    an AMENDMENT_APPROVAL_ROLES reviewer via the approve/deny endpoints
    below. The original signed record remains fully preserved regardless
    of the amendment's eventual outcome.
    """
    record = _load_locked_rnica_assessment_for_amendment(db, assessment_id, current_user)
    if not record.locked:
        raise HTTPException(status_code=400, detail="Only a locked assessment can be corrected or amended.")
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    tenant_id = record.tenant_id or getattr(patient, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")
    user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    try:
        result = rnica_amendment_service.create_amendment(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            rnica_assessment_id=record.id,
            user_id=user_id,
            section_reference=payload.section_reference,
            amendment_category=payload.amendment_category,
            reason_code=payload.reason_code,
            requested_change=payload.requested_change,
            request_source=payload.request_source,
            original_value_snapshot=payload.original_value_snapshot,
            proposed_value=payload.proposed_value,
        )
    except rnica_amendment_service.RnicaAmendmentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"assessmentId": str(record.id), **result}
@router.get("/rnica/{assessment_id}/amendments")
def list_rnica_amendments(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """SECTION 12 — Amendment Infrastructure read-only list. Any authorized
    clinician with access to the patient may view amendment history,
    matching the read access already granted for the assessment itself.
    """
    record = _load_locked_rnica_assessment_for_amendment(db, assessment_id, current_user)
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    tenant_id = record.tenant_id or getattr(patient, "tenant_id", None)
    amendments = rnica_amendment_service.list_amendments(
        db,
        tenant_id=tenant_id,
        rnica_assessment_id=record.id,
    )
    return {"assessmentId": str(record.id), "amendments": amendments}
@router.post("/rnica/{assessment_id}/amendments/{amendment_id}/approve")
def approve_rnica_amendment(
    assessment_id: str,
    amendment_id: str,
    payload: RnicaAmendmentApproveRequest = RnicaAmendmentApproveRequest(),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """SECTION 12 — Amendment Infrastructure approval. Restricted to
    AMENDMENT_APPROVAL_ROLES (DPCS/DPCS Designee/Case Manager/Supervisor,
    plus Admin/QA/System for oversight parity with ALLOWED_REOPEN_ROLES).
    Approving an amendment records the decision only -- it never
    retroactively rewrites the original signed assessment content.
    """
    record = _load_locked_rnica_assessment_for_amendment(db, assessment_id, current_user)
    actor_role = str(getattr(current_user, "role", "SYSTEM")).strip().upper()
    if actor_role not in AMENDMENT_APPROVAL_ROLES:
        raise HTTPException(
            status_code=403,
            detail="DPCS, DPCS Designee, Case Manager, or Supervisor approval is required to decide an amendment.",
        )
    try:
        amendment_uuid = uuid.UUID(amendment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="amendment_id must be a valid UUID") from None
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    tenant_id = record.tenant_id or getattr(patient, "tenant_id", None)
    user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    try:
        result = rnica_amendment_service.approve_amendment(
            db,
            tenant_id=tenant_id,
            amendment_id=amendment_uuid,
            user_id=user_id,
            decision_reason=payload.decision_reason,
        )
    except rnica_amendment_service.RnicaAmendmentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"assessmentId": str(record.id), **result}
@router.post("/rnica/{assessment_id}/amendments/{amendment_id}/deny")
def deny_rnica_amendment(
    assessment_id: str,
    amendment_id: str,
    payload: RnicaAmendmentDenyRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """SECTION 12 — Amendment Infrastructure denial. Same review-authority
    restriction as approval; requires a non-blank `decision_reason` (CDPH
    written justification) so the decision itself stays traceable.
    """
    record = _load_locked_rnica_assessment_for_amendment(db, assessment_id, current_user)
    actor_role = str(getattr(current_user, "role", "SYSTEM")).strip().upper()
    if actor_role not in AMENDMENT_APPROVAL_ROLES:
        raise HTTPException(
            status_code=403,
            detail="DPCS, DPCS Designee, Case Manager, or Supervisor approval is required to decide an amendment.",
        )
    try:
        amendment_uuid = uuid.UUID(amendment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="amendment_id must be a valid UUID") from None
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    tenant_id = record.tenant_id or getattr(patient, "tenant_id", None)
    user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    try:
        result = rnica_amendment_service.deny_amendment(
            db,
            tenant_id=tenant_id,
            amendment_id=amendment_uuid,
            user_id=user_id,
            decision_reason=payload.decision_reason,
        )
    except rnica_amendment_service.RnicaAmendmentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"assessmentId": str(record.id), **result}
@router.get("/rnica/{assessment_id}/intelligence")
def get_rnica_intelligence(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    patient_id = str(record.patient_id) if record.patient_id else None
    patient_evidence = gather_patient_evidence(db, patient_id) if patient_id else {"text": "", "source_count": 0, "diagnosis_sources": [], "clinical_notes": []}
    intelligence = build_rnica_intelligence(
        record.form_data or {},
        patient_id=patient_id,
        patient_evidence=patient_evidence,
    )
    return intelligence
@router.post("/msw-ica/save")
def save_msw_ica_assessment(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    patient_id_raw = (payload or {}).get("patientId")
    incoming_form_data = (payload or {}).get("formData") or {}
    if not patient_id_raw:
        raise HTTPException(status_code=422, detail="patientId is required")
    try:
        patient_uuid = uuid.UUID(str(patient_id_raw))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="patientId must be a valid UUID") from None
    patient = get_authorized_patient(db, patient_uuid, current_user)
    form_data = _prepare_msw_ica_form_data(db, current_user, incoming_form_data)
    assessment = MswIcaAssessment(
        patient_id=patient_uuid,
        form_data=form_data,
        assessment_type="MSWICA",
        status="DRAFT",
        locked=False,
    )
    db.add(assessment)
    db.flush()
    _sync_msw_ica_escalations(
        db,
        assessment=assessment,
        patient=patient,
        current_user=current_user,
        previous_form_data=None,
        next_form_data=form_data,
    )
    db.commit()
    db.refresh(assessment)
    return {"assessmentId": str(assessment.id), "status": "saved"}
@router.get("/msw-ica/{assessment_id}")
def get_msw_ica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(MswIcaAssessment).filter(MswIcaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": merge_msw_ica_form_data(record.form_data or {}),
        "locked": record.locked,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.get("/msw-ica/by-patient/{patient_id}")
def get_msw_ica_assessment_by_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None
    get_authorized_patient(db, patient_uuid, current_user)
    records = (
        db.query(MswIcaAssessment)
        .filter(MswIcaAssessment.patient_id == patient_uuid)
        .order_by(MswIcaAssessment.created_at.desc())
        .all()
    )
    record = next((item for item in records if not item.locked), None) or (records[0] if records else None)
    if not record:
        return {"assessmentId": None}
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": merge_msw_ica_form_data(record.form_data or {}),
        "locked": record.locked,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.put("/msw-ica/{assessment_id}")
def update_msw_ica_assessment(
    assessment_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(MswIcaAssessment).filter(MswIcaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient = get_authorized_patient(db, record.patient_id, current_user)
    previous_form_data = merge_msw_ica_form_data(record.form_data or {})
    incoming_form_data = (payload or {}).get("formData") or record.form_data or {}
    form_data = _prepare_msw_ica_form_data(db, current_user, incoming_form_data)
    record.form_data = form_data
    record.status = "DRAFT"
    _sync_msw_ica_escalations(
        db,
        assessment=record,
        patient=patient,
        current_user=current_user,
        previous_form_data=previous_form_data,
        next_form_data=form_data,
    )
    db.commit()
    return {
        "assessmentId": str(record.id),
        "status": "updated",
        "locked": record.locked,
    }
@router.post("/msw-ica/{assessment_id}/lock")
def lock_msw_ica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(MswIcaAssessment).filter(MswIcaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    merged_form_data = merge_msw_ica_form_data(record.form_data or {})
    if _is_msw_suicide_risk_indicated(merged_form_data) and not _msw_suicide_notifications_complete(merged_form_data):
        raise HTTPException(
            status_code=422,
            detail="Suicide risk notifications to the Case Manager/Supervisor and Attending Physician must be documented before locking the MSW ICA assessment.",
        )
    record.form_data = _prepare_msw_ica_form_data(db, current_user, merged_form_data, bind_signatures=True)
    record.locked = True
    record.status = "LOCKED"
    record.locked_at = datetime.now(timezone.utc)
    reasoning_payload = _extract_msw_ica_reasoning_payload(record.form_data)
    _run_clinical_reasoning(
        db=db,
        patient_id=record.patient_id,
        tenant_id=current_user.tenant_id,
        episode_id=record.id,
        assessment_payload=reasoning_payload,
        request_id=str(uuid.uuid4()),
        log_label=f"msw_ica_id={record.id}",
    )
    db.commit()
    return {"assessmentId": str(record.id), "status": "locked", "locked": True}
@router.post("/scica/save")
def save_scica_assessment(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    patient_id_raw = (payload or {}).get("patientId")
    incoming_form_data = (payload or {}).get("formData") or {}
    if not patient_id_raw:
        raise HTTPException(status_code=422, detail="patientId is required")
    try:
        patient_uuid = uuid.UUID(str(patient_id_raw))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="patientId must be a valid UUID") from None
    patient = get_authorized_patient(db, patient_uuid, current_user)
    form_data = _prepare_scica_form_data(db, current_user, incoming_form_data)
    assessment = ScicaAssessment(
        patient_id=patient_uuid,
        form_data=form_data,
        assessment_type="SCICA",
        status="DRAFT",
        locked=False,
    )
    db.add(assessment)
    db.flush()
    _sync_scica_escalations(
        db,
        assessment=assessment,
        patient=patient,
        current_user=current_user,
        previous_form_data=None,
        next_form_data=form_data,
    )
    db.commit()
    db.refresh(assessment)
    return {"assessmentId": str(assessment.id), "status": "saved"}
@router.get("/scica/{assessment_id}")
def get_scica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(ScicaAssessment).filter(ScicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": merge_scica_form_data(record.form_data or {}),
        "locked": record.locked,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.get("/scica/by-patient/{patient_id}")
def get_scica_assessment_by_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None
    get_authorized_patient(db, patient_uuid, current_user)
    records = (
        db.query(ScicaAssessment)
        .filter(ScicaAssessment.patient_id == patient_uuid)
        .order_by(ScicaAssessment.created_at.desc())
        .all()
    )
    record = next((item for item in records if not item.locked), None) or (records[0] if records else None)
    if not record:
        return {"assessmentId": None}
    return {
        "assessmentId": str(record.id),
        "patientId": str(record.patient_id),
        "formData": merge_scica_form_data(record.form_data or {}),
        "locked": record.locked,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }
@router.put("/scica/{assessment_id}")
def update_scica_assessment(
    assessment_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(ScicaAssessment).filter(ScicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient = get_authorized_patient(db, record.patient_id, current_user)
    previous_form_data = merge_scica_form_data(record.form_data or {})
    incoming_form_data = (payload or {}).get("formData") or record.form_data or {}
    form_data = _prepare_scica_form_data(db, current_user, incoming_form_data)
    record.form_data = form_data
    record.status = "DRAFT"
    _sync_scica_escalations(
        db,
        assessment=record,
        patient=patient,
        current_user=current_user,
        previous_form_data=previous_form_data,
        next_form_data=form_data,
    )
    db.commit()
    return {
        "assessmentId": str(record.id),
        "status": "updated",
        "locked": record.locked,
    }
@router.post("/scica/{assessment_id}/lock")
def lock_scica_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(ScicaAssessment).filter(ScicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    merged_form_data = merge_scica_form_data(record.form_data or {})
    if _is_scica_suicide_risk_indicated(merged_form_data) and not _scica_suicide_notifications_complete(merged_form_data):
        raise HTTPException(
            status_code=422,
            detail="Suicide risk notifications to the Case Manager/Supervisor and Attending Physician must be documented before locking the SCICA assessment.",
        )
    record.form_data = _prepare_scica_form_data(db, current_user, merged_form_data, bind_signatures=True)
    record.locked = True
    record.status = "LOCKED"
    record.locked_at = datetime.now(timezone.utc)
    reasoning_payload = _extract_scica_reasoning_payload(record.form_data)
    _run_clinical_reasoning(
        db=db,
        patient_id=record.patient_id,
        tenant_id=current_user.tenant_id,
        episode_id=record.id,
        assessment_payload=reasoning_payload,
        request_id=str(uuid.uuid4()),
        log_label=f"scica_id={record.id}",
    )
    db.commit()
    return {"assessmentId": str(record.id), "status": "locked", "locked": True}
@router.get("/msw-ica/{assessment_id}/intelligence")
def get_msw_ica_intelligence(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None
    record = db.query(MswIcaAssessment).filter(MswIcaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    get_authorized_patient(db, record.patient_id, current_user)
    patient_id = str(record.patient_id) if record.patient_id else None
    patient_evidence = gather_patient_evidence(db, patient_id) if patient_id else {"text": "", "source_count": 0, "diagnosis_sources": [], "clinical_notes": []}
    return build_msw_ica_intelligence(
        merge_msw_ica_form_data(record.form_data or {}),
        patient_id=patient_id,
        patient_evidence=patient_evidence,
    )
# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================
class VisitStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        description="Allowed: MISSED, RESCHEDULED",
    )
    communications_log_id: Optional[uuid.UUID] = Field(
        None,
        description="Required when status is MISSED or RESCHEDULED",
    )
class VisitCreateRequest(BaseModel):
    """
    Enterprise-grade Visit Create Request
    Key Design:
    - service_type = WHAT (SN, MSW, CHAPLAIN)
    - visit_type = WHO (RN, LVN, SW, etc.)
    """
    # =========================================================
    # REQUIRED CORE
    # =========================================================
    patient_id: uuid.UUID = Field(
        ...,
        description="Patient identifier",
    )
    # ✅ WHO performed the visit
    visit_type: str = Field(
        ...,
        description="Discipline: RN, LVN, SW, CHAPLAIN, AIDE, MD, NP, PA, ADMINISTRATIVE",
    )
    # ✅ WHAT service category (CRITICAL FIX)
    service_type: Optional[str] = Field(
        default="SN",
        description="Service classification: SN (Skilled Nursing), MSW, CHAPLAIN, AIDE",
    )
    # =========================================================
    # WORKFLOW / FORM ENGINE
    # =========================================================
    form_type: Optional[str] = Field(
        None,
        description=(
            "Workflow selector: "
            "ASSESS, PRE_ADMIT_EVAL, SHORT_FORM, SUPV_VISIT_ONLY, "
            "ON_CALL_TRIAGE, MISSED_VISIT, DECLINED_VISIT, "
            "ANCILLARY_SUPPORT, VOLUNTEER_SUPPORT, RESPITE_RELIEF, "
            "BEREAVEMENT_VISIT, DEATH_VISIT, AFTER_DEATH, "
            "AFTER_HOURS, OFFICE_HOURS, WEEKENDS, ROUTINE_VISIT"
        ),
    )
    # =========================================================
    # CLINICAL CONTEXT
    # =========================================================
    level_of_care: Optional[str] = Field(
        None,
        description="Hospice LOC: RC, CC, IP, RSP (accepts CMS strings via normalization)",
    )
    visit_schedule_type: Optional[str] = Field(
        None,
        description="SCHEDULED or UNSCHEDULED",
    )
    event_type: Optional[str] = Field(
        None,
        description=(
            "Optional event trigger: "
            "CHANGE_OF_CONDITION, NEW_ORDER, UPDATE_ASSESSMENT, RECERT"
        ),
    )
    clinical_note: Optional[dict[str, Any]] = Field(
        default=None,
        description="Full ROS assessment structure including issues and POC",
    )
    # =========================================================
    # ✅ VALIDATIONS (ENTERPRISE CRITICAL)
    # =========================================================
    @field_validator("visit_type", mode="before")
    @classmethod
    def normalize_visit_type(cls, value: str) -> str:
        if not value:
            raise ValueError("visit_type is required")
        v = value.strip().upper()
        mapping = {
            "SN": "RN",
   # ⚠️ fallback only — will be validated below
            "NURSE": "RN",
            "REGISTERED_NURSE": "RN",
            "MSW": "SW",
            "LCSW": "SW",
            "BSW": "SW",
            "SC": "CHAPLAIN",
            "CHHA": "AIDE",
        }
        return mapping.get(v, v)
    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, value: Optional[str]) -> str:
        if not value:
            return "SN"
        v = value.strip().upper()
        mapping = {
            "SKILLED_NURSING": "SN",
            "NURSING": "SN",
            "SOCIAL_WORK": "MSW",
            "SPIRITUAL": "CHAPLAIN",
        }
        return mapping.get(v, v)
    @field_validator("level_of_care", mode="before")
    @classmethod
    def normalize_level_of_care(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        v = value.strip().upper()
        mapping = {
            "ROUTINE_HOME_CARE": "RC",
            "CONTINUOUS_HOME_CARE": "CC",
            "GENERAL_INPATIENT": "IP",
            "INPATIENT_RESPITE": "RSP",
        }
        return mapping.get(v, v)
    @field_validator("visit_schedule_type", mode="before")
    @classmethod
    def normalize_schedule(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        v = value.strip().upper()
        if v not in {"SCHEDULED", "UNSCHEDULED"}:
            raise ValueError(f"Invalid visit_schedule_type {value}")
        return v
    @field_validator("service_type")
    @classmethod
    def validate_service_vs_discipline(
        cls,
        value: str,
        info: ValidationInfo,
    ) -> str:
        discipline = info.data.get("visit_type")
        if value == "SN" and discipline not in {"RN", "LVN"}:
            raise ValueError(
                "Skilled Nursing (SN) visits must be RN or LVN"
            )
        return value
class CHHATaskResultItem(BaseModel):
    section_code: str
    task_code: str
    was_assigned: bool = True
    completed: bool = False
    refused: bool = False
    not_done: bool = False
    observation_code: Optional[str] = None
    result_note: Optional[str] = None
class CHHAOutcomeUpsertRequest(BaseModel):
    poc_reference_id: Optional[uuid.UUID] = None
    tolerance_to_care: str
    condition_during_visit: str
    skin_outcome: str
    pain_or_change_observed: bool = False
    rn_notification_required: bool = False
    rn_notified: bool = False
    rn_notified_name: Optional[str] = None
    caregiver_instruction_provided: bool = False
    caregiver_understanding_confirmed: bool = False
    exception_narrative: Optional[str] = None
    task_results: List[CHHATaskResultItem] = Field(default_factory=list)
    # Visit logistics / payroll tracking ("Visit Details")
    correction: bool = False
    type_of_visit: Optional[str] = None
    visit_kind: Optional[str] = None
    visit_kind_specify: Optional[str] = None
    reason_for_visit: Optional[str] = None
    visit_date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    duration: Optional[str] = None
    entered_by: Optional[str] = None
    staff_assigned: Optional[str] = None
    care_level: Optional[str] = None
class CCHourlyNarrativeEntryRequest(BaseModel):
    """
    One hourly (or per-shift) documentation entry for a patient at the
    Continuous Care (CC) level of care. Shared across RN, LVN, AIDE
    (CHHA), MSW, and Chaplain visits -- see app.domain.forms.form_registry
    (PRIMARY_CC_HOURLY_NARRATIVE / MOD_CC_ENTRY).
    """
    discipline: str = Field(..., description="RN, LVN, AIDE, MSW, or CHAPLAIN")
    entry_date: Optional[str] = None
    entry_time: Optional[str] = None
    # Vitals
    temperature: Optional[str] = None
    pulse: Optional[str] = None
    respirations: Optional[str] = None
    bp_systolic: Optional[str] = None
    bp_diastolic: Optional[str] = None
    o2_sat: Optional[str] = None
    # Pain
    pain_level: Optional[str] = None
    pain_location: Optional[str] = None
    pain_intervention: Optional[str] = None
    # Symptoms / care provided
    symptoms: Optional[str] = None
    care_provided: Optional[str] = None
    # Issue management
    issue_identified: bool = False
    issue_narrative: Optional[str] = None
    # POC update
    poc_update_narrative: Optional[str] = None
    # General narrative
    narrative: Optional[str] = None
    entered_by: Optional[str] = None
# =========================================================
# VISIT NOTES (RN / LVN) -- "Add New Visit" / "My Visit Notes" /
# "History of Visit Notes" module, modeled on the legacy HospiceMD Visit
# Notes screen. Content is stored as JSONB on the visit's primary
# ClinicalNote (see backend/app/models/clinical_note.py) -- no dedicated
# table is needed since ClinicalNote already provides a versioned,
# discipline-aware, finalize()-able JSONB note tied to a Visit.
# =========================================================
VISIT_NOTE_DISCIPLINES = {"RN", "LVN"}
# Form types that show the full clinical documentation body (Pain / Vitals
# & Measurements / Signs & Symptoms / Care Provided / Visit Check List).
# Every other VisitFormType collapses the body down to a narrative-only
# note, matching the legacy Form Type behavior.
VISIT_NOTE_FULL_BODY_FORM_TYPES = {"ASSESS", "ROUTINE_VISIT"}
VISIT_NOTE_BODY_SYSTEM_KEYS = {
    "neuro_mental_sensory",
    "cardiovascular",
    "respiratory",
    "immunological_infection",
    "gi_digestive",
    "nutrition",
    "endocrine",
    "gu_reproductive",
    "sleep_rest",
    "musculoskeletal",
    "integumentary_skin",
    "mobility",
    "adl_assessment",
    "fall_incidence",
    "safety_issues",}
class VisitNotePainRequest(BaseModel):
    controlled: Optional[str] = Field(None, description="Y, N, UNABLE, or N/A")
    pain_level: Optional[int] = Field(None, ge=0, le=10)
    other_observation: Optional[str] = None
class VisitNoteVitalsRequest(BaseModel):
    temperature: Optional[str] = None
    temperature_position: Optional[str] = None
  # ORAL / AXILLARY / TYMPANIC / RECTAL
    pulse: Optional[str] = None
    respirations: Optional[str] = None
    bp_systolic: Optional[str] = None
    bp_diastolic: Optional[str] = None
    bp_position: Optional[str] = None
  # SITTING / STANDING / LYING
    height: Optional[str] = None
    weight: Optional[str] = None
    mac: Optional[str] = None
    bmi: Optional[str] = None
    o2_sat: Optional[str] = None
    o2_delivery: Optional[str] = None
  # ROOM_AIR / NASAL_CANNULA / etc.
    unable_to_assess: bool = False
class VisitNoteBodySystemRequest(BaseModel):
    """
    One row of the 13-body-system Signs & Symptoms / Alteration in Status
    grid (Neuro/Mental/Sensory, Cardiovascular, Respiratory,
    Immunological/Infection, GI-Digestive, Nutrition, Endocrine,
    GU-Reproductive, Sleep/Rest, MusculoSkeletal, Integumentary-Skin,
    Mobility, ADL Assessment, Fall/Incidence, Safety Issues).
    """
    severity: Optional[str] = Field(None, description="NONE, MILD, MODERATE, or SEVERE")
    other_symptom: Optional[str] = None
    assessed_no_issues: bool = False
    other_observation: Optional[str] = None
    # Nutrition-specific
    diet: Optional[str] = None
    diet_specify: Optional[str] = None
    # GU-Reproductive-specific
    incontinent: Optional[str] = None
    last_bm: Optional[str] = None
    # Mobility-specific
    ambulatory_status: Optional[str] = None
  # AMBULATORY / NON_AMBULATORY
    endurance: Optional[str] = None
    # ADL Assessment-specific (0-3 dependence scale x 6 activities)
    adl_scores: Optional[Dict[str, int]] = None
    adl_total_score: Optional[int] = None
class VisitNoteCareProvidedRequest(BaseModel):
    physical_comfort_support: bool = False
    structural_functional_activity_support: bool = False
    emotional_support: bool = False
    spiritual_support: bool = False
    safety_instructions: bool = False
    interpersonal_relationship_support: bool = False
    environmental_needs: bool = False
    self_determination_preference_needs: bool = False
    knowledge_related_needs: bool = False
    language_communication_related_needs: bool = False
    other_needs: bool = False
    other_needs_text: Optional[str] = None
class VisitNoteChecklistRequest(BaseModel):
    updated_family_pcg: Optional[bool] = None
    updated_cm_md: Optional[bool] = None
    comfort_pack_med_checked: Optional[bool] = None
    dme_inspected: Optional[bool] = None
    foley_cath_checked: Optional[bool] = None
    foley_cath_last_changed: Optional[str] = None
    gi_tube_checked: Optional[bool] = None
    next_visit_confirmed: Optional[bool] = None
class VisitNoteContentRequest(BaseModel):
    """
    Full content payload for the RN/LVN Visit Notes module. The Visit
    Details block always applies; the clinical body only applies when
    form_type is one of VISIT_NOTE_FULL_BODY_FORM_TYPES and care_level is
    not Continuous Care (which swaps in the CC Hourly Narrative log
    instead -- see CCHourlyNarrativeEntry / ContinuousCareLogSection).
    """
    # ---- Visit Details (rendered first / topmost in the UI) ----
    correction: bool = False
    type_of_visit: Optional[str] = None
  # In-Person / Telephone / Video
    visit_kind: Optional[str] = None
  # Scheduled / Unscheduled
    form_type: Optional[str] = None
  # VisitFormType value
    care_level: Optional[str] = None
  # Routine Care / Continuous Care / General Inpatient / Respite Care
    visit_date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    duration: Optional[str] = None
    entered_by: Optional[str] = None
    staff_assigned: Optional[str] = None
    # ---- Clinical body ----
    pain: Optional[VisitNotePainRequest] = None
    vitals: Optional[VisitNoteVitalsRequest] = None
    signs_symptoms: Dict[str, VisitNoteBodySystemRequest] = Field(default_factory=dict)
    care_provided: Optional[VisitNoteCareProvidedRequest] = None
    visit_checklist: Optional[VisitNoteChecklistRequest] = None
    # ---- Death Visit only ----
    death_disposal_notes: Optional[str] = None
    # ---- Always present ----
    narrative: Optional[str] = None
    @field_validator("signs_symptoms")
    @classmethod
    def _validate_signs_symptoms_keys(cls, value: Dict[str, VisitNoteBodySystemRequest]):
        unknown = set(value.keys()) - VISIT_NOTE_BODY_SYSTEM_KEYS
        if unknown:
            raise ValueError(f"Unknown signs_symptoms system(s): {sorted(unknown)}")
        return value
    @field_validator("form_type")
    @classmethod
    def _validate_form_type(cls, value: Optional[str]):
        if value is None:
            return value
        try:
            return VisitFormType(value.strip().upper()).value
        except ValueError:
            raise ValueError(f"Unknown form_type: {value}")
class RefusalRequest(BaseModel):
    discipline: str = Field(
        ...,
        description="LVN, CHHA, MSW, SC, RN, MD, NP, PA",
    )
    reason: Optional[str] = Field(
        None,
        description="Optional free-text refusal reason",
    )
class VisitMutationResponse(BaseModel):
    status: str
    visit_id: str
    request_id: str
    completed_task_types: list[str] = Field(
        default_factory=list,
        description="Tasks completed as a result of this action",
    )
    new_status: Optional[str] = None
    communications_log_id: Optional[str] = None
class VisitReopenRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Reason for reopening visit",
    )
class VisitCreateResponse(BaseModel):
    visit_id: str
    visit_type: str
    form_type: Optional[str] = None
    form_family: Optional[str] = Field(
        None,
        description="CLINICAL, PSYCHOSOCIAL, SPIRITUAL, SUPPORT, ADMIN",
    )
    primary_form: Optional[str] = None
    attached_forms: List[str] = Field(
        default_factory=list,
        description="Auto-attached forms generated by form engine",
    )
    modules: List[str] = Field(
        default_factory=list,
        description="UI modules required for rendering this form",
    )
    resolved_by: Optional[str] = Field(
        None,
        description="Resolution source: db_engine, event_override, cc_override",
    )
    is_supervisory: bool = False
    supervisory_targets: List[str] = Field(default_factory=list)
    request_id: str
class RefusalResponse(BaseModel):
    status: str
    patient_id: str
    discipline: str
    reason: Optional[str] = None
    refused_at: Optional[str] = None
    request_id: str
# =========================================================
# INTERNAL HELPERS
# =========================================================
def _normalize_and_validate_form_type(raw: Optional[str]) -> str:
    if not raw:
        return VisitFormType.SHORT_FORM.value
    normalized = str(raw).strip().upper()
    try:
        return VisitFormType(normalized).value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid form_type '{raw}'. Allowed: {[e.value for e in VisitFormType]}",
        )
def _normalize_schedule_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    value = str(raw).strip().upper()
    allowed = {"SCHEDULED", "UNSCHEDULED"}
    if value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid visit_schedule_type '{raw}'. Allowed: {sorted(allowed)}",
        )
    return value
def _normalize_event_type_for_form(
    form_type: str,
    raw: Optional[str],) -> Optional[str]:
    if not raw:
        return None
    value = str(raw).strip().upper()
    from app.models.enums import VisitEventType
    try:
        return VisitEventType(value).value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid event_type '{raw}'. "
                f"Allowed: {[e.value for e in VisitEventType]}"
            ),
        )
    return value
def _normalize_and_validate_visit_type(raw: str) -> str:
    normalized = normalize_visit_type(raw or "")
    if normalized not in ALLOWED_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visit_type '{raw}'. Allowed: {sorted(ALLOWED_VISIT_TYPES)}",
        )
    return normalized
def _canonicalize_discipline(raw: str) -> str:
    candidate = str(raw or "").strip().upper()
    candidate = VISIT_TYPE_ALIASES.get(candidate, candidate)
    normalized = normalize_visit_type(candidate)
    normalized = VISIT_TYPE_ALIASES.get(normalized, normalized)
    if normalized not in ALLOWED_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid visit_type '{raw}'. Allowed: "
                f"{sorted(ALLOWED_VISIT_TYPES | set(VISIT_TYPE_ALIASES.keys()))}"
            ),
        )
    return normalized
def _guard_against_generic_note_type(note_type: Optional[str], request_id: str) -> str:
    value = (note_type or "").strip().upper()
    if not value or value in GENERIC_NOTE_TYPES:
        logger.critical(
            "FORM_ENGINE_RETURNED_GENERIC_NOTE_TYPE",
            extra={
                "note_type": note_type,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Form engine returned a generic note type; registry must be corrected.",
        )
    return value
def _enforce_form_selection_rules(
    *,
    discipline: str,
    form_type: str,
    visit_schedule_type: Optional[str],
    event_type: Optional[str],) -> None:
    """
    Enforce SNS hospice workflow reality.
    Clinical rules:
    - SW/MSW/BSW/LCSW -> always ROUTINE_VISIT (psychosocial routine form package)
    - RN/LVN SHORT_FORM -> PRN/UNSCHEDULED false alarm only (no issue/event)
    - RN + issue -> ASSESS + UPDATE_ASSESSMENT
    - LVN + issue -> ROUTINE_VISIT (routine SN), never SHORT_FORM
    - LVN change of condition must be escalated operationally (captured later in workflow)
    """
    discipline = _canonicalize_discipline(discipline)
    form_type = _normalize_and_validate_form_type(form_type)
    schedule = _normalize_schedule_type(visit_schedule_type)
    event = event_type
    issue_present = event in ISSUE_EVENT_TYPES
    is_prn = schedule == "UNSCHEDULED"
    if discipline == "SW":
        if form_type != VisitFormType.ROUTINE_VISIT.value:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SW/MSW/BSW/LCSW must use ROUTINE_VISIT. "
                    "The form engine will resolve ROUTINE_VISIT to the psychosocial routine SW form."
                ),
            )
        if issue_present:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SW psychosocial visits should not use nursing issue event types. "
                    "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."
                ),
            )
        return
    if form_type == VisitFormType.SHORT_FORM.value:
        if not is_prn:
            raise HTTPException(
                status_code=422,
                detail="SHORT_FORM is only allowed for unscheduled (PRN) visits.",
            )
        # ✅ CRITICAL FIX: AUTO-SWITCH BASED ON DISCIPLINE
        if issue_present:
            if discipline == "RN":
                # ✅ RN → COMPREHENSIVE ASSESSMENT
                return
  # let resolver switch to RN_ASSESS
            elif discipline == "LVN":
                # ✅ LVN → ROUTINE VISIT
                return
  # let resolver switch to LVN_ROUTINE
        return
    if discipline == "RN":
        if issue_present:
            # ✅ DO NOT BLOCK SHORT_FORM — resolver will convert it
            if form_type == VisitFormType.SHORT_FORM.value:
                return
            if form_type != VisitFormType.ASSESS.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "RN must use ASSESS when issues are present."
                    ),
                )
            if event != "UPDATE_ASSESSMENT":
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "RN issue-driven reassessment must use event_type=UPDATE_ASSESSMENT "
                        "so the plan of care update path is traceable."
                    ),
                )
            return
        return
    if discipline == "LVN":
        if issue_present:
            # ✅ allow SHORT_FORM → resolver converts
            if form_type == VisitFormType.SHORT_FORM.value:
                return
            if form_type != VisitFormType.ROUTINE_VISIT.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "LVN with issues must use ROUTINE_VISIT."
                    ),
                )
            return
        return
def _get_request_id(request: Request, response: Optional[Response] = None) -> str:
    existing = (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
    )
    request_id = str(existing or uuid.uuid4())
    request.state.request_id = request_id
    if response is not None:
        response.headers["X-Request-ID"] = request_id
    return request_id
def _extract_user_id_from_request(request: Request) -> Optional[uuid.UUID]:
    candidate_values = [
        getattr(request.state, "user_id", None),
        getattr(getattr(request.state, "user", None), "id", None),
        request.headers.get("X-User-Id"),
    ]
    for candidate in candidate_values:
        if not candidate:
            continue
        try:
            return candidate if isinstance(candidate, uuid.UUID) else uuid.UUID(str(candidate))
        except (TypeError, ValueError):
            continue
    return None
def _resolve_actor_user_id(db: Session, request: Request) -> uuid.UUID:
    authenticated_user_id = _extract_user_id_from_request(request)
    if authenticated_user_id:
        return authenticated_user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated user context is required",
    )
def _set_db_context(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    request_id: str,) -> None:
    db.info["tenant_id"] = tenant_id
    db.info["user_id"] = user_id
    db.info["request_id"] = request_id
def _normalized_mode_from_visit(visit: Visit) -> str:
    raw_mode = None
    for attr in ("visit_mode", "mode", "encounter_mode", "contact_mode"):
        if hasattr(visit, attr):
            raw_mode = getattr(visit, attr)
            if raw_mode is not None:
                break
    return (str(raw_mode) if raw_mode else "").upper()
def _resolve_actor_role(request: Request) -> str:
    candidate_values = [
        getattr(request.state, "role", None),
        getattr(getattr(request.state, "user", None), "role", None),
        request.headers.get("X-User-Role"),
    ]
    for candidate in candidate_values:
        if candidate:
            return str(candidate).strip().upper()
    return "SYSTEM"
def _visit_has_early_lock(visit: Visit) -> tuple[bool, Optional[str]]:
    for attr in ("signed_at", "reviewed_at", "approved_at", "cosigned_at", "locked_at"):
        if getattr(visit, attr, None) is not None:
            return True, attr
    return False, None
def _visit_is_within_correction_window(visit: Visit, now: datetime) -> bool:
    finalized_at = getattr(visit, "finalized_at", None)
    if finalized_at is None:
        return False
    if finalized_at.tzinfo is None:
        finalized_at = finalized_at.replace(tzinfo=timezone.utc)
    return now <= finalized_at + timedelta(hours=VISIT_CORRECTION_WINDOW_HOURS)
def _apply_reopen_metadata(
    *,
    visit: Visit,
    user_id: uuid.UUID,
    reason: str,
    now: datetime,) -> None:
    if hasattr(visit, "updated_at"):
        visit.updated_at = now
    if hasattr(visit, "updated_by"):
        visit.updated_by = user_id
    if hasattr(visit, "status"):
        visit.status = "REOPENED"
    if hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}
        details["reopened_at"] = now.isoformat()
        details["reopened_by"] = str(user_id)
        details["reopen_reason"] = reason
        details["superseded_finalized_at"] = (
            getattr(visit, "finalized_at", None).isoformat()
            if getattr(visit, "finalized_at", None) is not None
            else None
        )
        visit.details = details
def _safe_log_event(
    db: Session,
    user_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    request_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,) -> None:
    try:
        log_event(
            db=db,
            user_id=str(user_id),
            role="SYSTEM",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            commit=False,
        )
    except Exception:
        logger.exception(
            "Audit log failed",
            extra={
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "request_id": request_id,
                **(metadata or {}),
            },
        )
def _load_visit_for_update(db: Session, visit_id: uuid.UUID) -> Visit:
    visit = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(Visit.id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit
def _load_patient_for_update(db: Session, patient_id: uuid.UUID) -> Patient:
    patient = (
        db.query(Patient)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
def _normalize_level_of_care(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    value = raw.strip().upper()
    mapping = {
        "ROUTINE_HOME_CARE": "RC",
        "CONTINUOUS_HOME_CARE": "CC",
        "GENERAL_INPATIENT": "IP",
        "INPATIENT_RESPITE": "RSP",
    }
    return mapping.get(value, value)
# =========================================================
# SUPERVISORY LOGIC HELPERS
# =========================================================
def _get_patient_refusal_flag(patient: Patient, service_key: str) -> bool:
    key = service_key.strip().upper()
    if key == "CHHA":
        return bool(
            getattr(patient, "chha_refused", False)
            or getattr(patient, "aide_refused", False)
        )
    if key == "LVN":
        return bool(getattr(patient, "lvn_refused", False))
    return False
def _patient_has_active_staff(patient: Patient, service_key: str) -> bool:
    key = service_key.strip().upper()
    if key == "CHHA":
        return bool(getattr(patient, "has_chha", False))
    if key == "LVN":
        return bool(getattr(patient, "has_lvn", False))
    return False
def _read_supervisory_targets_from_visit(visit: Visit) -> list[str]:
    """
    Extract supervisory target disciplines from visit.details.
    Returns:
        List[str] of normalized uppercase targets (e.g. ["LVN", "CHHA"]).
    Rules:
    - details must be a dict
    - supervisory_targets must be a list
    - values normalized to uppercase strings
    - empty/invalid values filtered out
    """
    details = getattr(visit, "details", None)
    if not isinstance(details, dict):
        return []
    targets = details.get("supervisory_targets")
    if not isinstance(targets, list):
        return []
    return [
        str(t).strip().upper()
        for t in targets
        if str(t).strip()
    ]
def _last_rn_supervisory_visit_for_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    target: str,) -> Optional[Visit]:
    target = target.strip().upper()
    visits = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Visit.tenant_id == tenant_id,
            Visit.patient_id == patient_id,
            Visit.visit_discipline == "RN",
        )
        .order_by(Visit.created_at.desc())
        .all()
    )
    for visit in visits:
        if not bool(getattr(visit, "is_supervisory", False)):
            continue
        if (getattr(visit, "status", "") or "").upper() != "FINALIZED":
            continue
        targets = _read_supervisory_targets_from_visit(visit)
        if target in targets:
            return visit
    return None
def _is_chha_supervision_due(
    db: Session,
    *,
    patient: Patient,
    now: datetime,) -> bool:
    if not _patient_has_active_staff(patient, "CHHA"):
        return False
    if _get_patient_refusal_flag(patient, "CHHA"):
        return False
    last_visit = _last_rn_supervisory_visit_for_target(
        db,
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        target="CHHA",
    )
    if last_visit is None:
        return True
    last_finalized_at = (
        getattr(last_visit, "finalized_at", None)
        or getattr(last_visit, "created_at", None)
    )
    if last_finalized_at is None:
        return True
    if last_finalized_at.tzinfo is None:
        last_finalized_at = last_finalized_at.replace(tzinfo=timezone.utc)
    return now >= (last_finalized_at + timedelta(days=14))
def _is_lvn_supervision_due(
    db: Session,
    *,
    patient: Patient,
    now: datetime,) -> bool:
    if not _patient_has_active_staff(patient, "LVN"):
        return False
    if _get_patient_refusal_flag(patient, "LVN"):
        return False
    last_visit = _last_rn_supervisory_visit_for_target(
        db,
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        target="LVN",
    )
    if last_visit is None:
        return True
    last_finalized_at = (
        getattr(last_visit, "finalized_at", None)
        or getattr(last_visit, "created_at", None)
    )
    if last_finalized_at is None:
        return True
    if last_finalized_at.tzinfo is None:
        last_finalized_at = last_finalized_at.replace(tzinfo=timezone.utc)
    return (
        last_finalized_at.year != now.year
        or last_finalized_at.month != now.month
    )
def _determine_supervisory_context(
    db: Session,
    *,
    patient: Patient,
    normalized_visit_type: str,
    validated_form_type: str,
    now: datetime,) -> tuple[bool, list[str]]:
    if normalized_visit_type != "RN":
        return False, []
    if validated_form_type != VisitFormType.ROUTINE_VISIT.value:
        return False, []
    targets: list[str] = []
    if _is_chha_supervision_due(
        db,
        patient=patient,
        now=now,
    ):
        targets.append("CHHA")
    if _is_lvn_supervision_due(
        db,
        patient=patient,
        now=now,
    ):
        targets.append("LVN")
    return (len(targets) > 0), targets
def _apply_supervisory_context_to_visit(
    *,
    visit: Visit,
    is_supervisory: bool,
    supervisory_targets: list[str],) -> None:
    if hasattr(visit, "is_supervisory"):
        visit.is_supervisory = is_supervisory
    if hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}
        details["is_supervisory"] = is_supervisory
        details["supervisory_targets"] = supervisory_targets
        visit.details = details
# =========================================================
# TASK COMPLETION HELPERS
# =========================================================
def _complete_task_with_visit(task: Task, visit: Visit, now: datetime) -> None:
    if not getattr(task, "tenant_id", None):
        raise ValueError("Task missing tenant_id")
    if not getattr(visit, "id", None):
        raise ValueError("Visit missing id")
    if task.status == TaskStatus.COMPLETED:
        return
    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completion_reference_type = (
        CompletionReferenceType.VISIT
        if hasattr(CompletionReferenceType, "VISIT")
        else "VISIT"
    )
    task.completion_reference_id = visit.id
    if hasattr(task, "updated_at"):
        task.updated_at = now
    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )
def _complete_initial_task_for_visit(
    db: Session,
    visit: Visit,) -> list[str]:
    if not getattr(visit, "tenant_id", None):
        raise ValueError("Visit missing tenant_id")
    visit_type = _normalize_and_validate_visit_type(
        getattr(visit, "visit_type", "") or ""
    )
    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or ""
    ).upper()
    target_task_type = None
    if visit_type == "RN" or discipline == "RN":
        target_task_type = TaskType.INITIAL_RN_ICA
    elif visit_type == "SW" or discipline == "SW":
        target_task_type = TaskType.INITIAL_MSW_ICA
    elif visit_type == "CHAPLAIN" or discipline == "CHAPLAIN":
        target_task_type = TaskType.INITIAL_SC_ICA
    if not target_task_type:
        return []
    # =====================================================
    # OPEN TASK
    # =====================================================
    task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.task_type == target_task_type,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.OVERDUE,
            ]),
        )
        .first()
    )
    if task:
        now = datetime.now(timezone.utc)
        _complete_task_with_visit(
            task,
            visit,
            now,
        )
        logger.info(
            "Completed initial task task_type=%s patient_id=%s via visit_id=%s",
            target_task_type.value,
            str(getattr(visit, "patient_id", None)),
            str(getattr(visit, "id", None)),
        )
        return [target_task_type.value]
    # =====================================================
    # ALREADY COMPLETED BY AUTO ENGINE
    # =====================================================
    completed_task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.task_type == target_task_type,
            Task.status == TaskStatus.COMPLETED,
            Task.completion_reference_id == visit.id,
        )
        .first()
    )
    if completed_task:
        logger.info(
            "Initial task already completed by automation task_type=%s visit_id=%s",
            target_task_type.value,
            str(visit.id),
        )
        return [target_task_type.value]
    return []
def _get_task_type_member(task_type_name: str):
    return getattr(TaskType, task_type_name, None)
def _create_condition_trigger_task_if_missing(
    db: Session,
    patient: Patient,
    user_id: uuid.UUID,
    now: datetime,
    task_type_name: str,
    discipline_value: str,) -> bool:
    if not getattr(patient, "tenant_id", None):
        raise ValueError("Patient missing tenant_id")
    task_type_member = _get_task_type_member(task_type_name)
    if task_type_member is None:
        logger.warning("Missing TaskType enum member: %s", task_type_name)
        return False
    existing = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            Task.tenant_id == patient.tenant_id,
            Task.patient_id == patient.id,
            Task.task_type == task_type_member,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.OVERDUE,
            ]),
        )
        .first()
    )
    if existing:
        return False
    task = Task(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        task_type=task_type_member,
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )
    if hasattr(task, "due_date"):
        task.due_date = now.date()
    if hasattr(task, "due_at"):
        task.due_at = now
    if hasattr(task, "origin"):
        task.origin = (
            TaskOrigin.SYSTEM
            if hasattr(TaskOrigin, "SYSTEM")
            else "SYSTEM"
        )
    if hasattr(task, "discipline"):
        task.discipline = discipline_value
    if hasattr(task, "regulatory_basis"):
        task.regulatory_basis = (
            TaskRegulatoryBasis.CONDITION_TRIGGER
            if hasattr(TaskRegulatoryBasis, "CONDITION_TRIGGER")
            else "CONDITION_TRIGGER"
        )
    if hasattr(task, "alert_reason"):
        task.alert_reason = task_type_name
    db.add(task)
    logger.info(
        "Created condition-trigger task task_type=%s patient_id=%s",
        task_type_name,
        str(patient.id),
    )
    return True
def _fetch_visit_related_notes(db: Session, visit: Visit) -> list[Any]:
    candidate_models: list[tuple[str, str]] = [
        ("app.models.note", "Note"),
        ("app.models.visit_note", "VisitNote"),
        ("app.models.clinical_note", "ClinicalNote"),
    ]
    for module_name, class_name in candidate_models:
        try:
            module = __import__(module_name, fromlist=[class_name])
            note_model = getattr(module, class_name, None)
            if note_model is None:
                continue
            query = db.query(note_model).execution_options(skip_tenant_filter=True)
            if hasattr(note_model, "tenant_id"):
                query = query.filter(note_model.tenant_id == visit.tenant_id)
            if hasattr(note_model, "visit_id"):
                query = query.filter(note_model.visit_id == visit.id)
            elif hasattr(note_model, "patient_id"):
                query = query.filter(note_model.patient_id == visit.patient_id)
            else:
                continue
            return query.all()
        except Exception:
            logger.debug(
                "Note model unavailable or query failed for %s.%s",
                module_name,
                class_name,
                exc_info=True,
            )
    return []
def _run_condition_detection_non_blocking(
    db: Session,
    visit: Visit,
    patient: Patient,
    user_id: uuid.UUID,
    now: datetime,
    request_id: str,) -> None:
    try:
        notes = _fetch_visit_related_notes(db, visit)
        note_inputs = [
            NoteInput(
                patient_id=patient.id,
                author_discipline=getattr(n, "discipline", ""),
                text=getattr(n, "text", "") or getattr(n, "note_text", ""),
                structured_flags=None,
            )
            for n in notes
        ]
        condition_result = condition_engine.detect(
            notes=note_inputs,
            assessments=None,
        )
        if condition_result.has_wounds and not getattr(patient, "has_wounds", False):
            setattr(patient, "has_wounds", True)
            if hasattr(patient, "updated_at"):
                patient.updated_at = now
        if condition_result.psychosocial_issue:
            _create_condition_trigger_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type_name="MSW_REOFFER",
                discipline_value="SW",
            )
        if condition_result.spiritual_distress:
            _create_condition_trigger_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type_name="CHAPLAIN_REOFFER",
                discipline_value="CHAPLAIN",
            )
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CONDITION_ENGINE_EVALUATED",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
        )
    except Exception:
        logger.exception(
            "Condition detection failed",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )
def _run_bereavement_aggregation_non_blocking(
    db: Session,
    visit: Visit,
    patient: Patient,
    user_id: uuid.UUID,
    request_id: str,) -> None:
    try:
        notes = _fetch_visit_related_notes(db, visit)
        bereavement_inputs = [
            BereavementNoteInput(
                patient_id=patient.id,
                note_id=getattr(n, "id", None),
                discipline=getattr(n, "discipline", ""),
                text=getattr(n, "text", "") or getattr(n, "note_text", ""),
            )
            for n in notes
            if getattr(n, "id", None) is not None
        ]
        result = bereavement_engine.detect(bereavement_inputs)
        if result.source_notes:
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="BEREAVEMENT_AGGREGATED",
                entity_type="patient",
                entity_id=patient.id,
                request_id=request_id,
            )
    except Exception:
        logger.exception(
            "Bereavement aggregation failed",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )
def _enforce_rn_supervisory_requirement(
    visit: Visit,
    patient: Patient,
    is_rn: bool,) -> None:
    if not is_rn:
        return
    if not getattr(visit, "is_supervisory", False):
        return
    details = getattr(visit, "details", None) or {}
    if not isinstance(details, dict):
        details = {}
    targets = details.get("supervisory_targets", [])
    if not isinstance(targets, list) or not targets:
        raise HTTPException(
            status_code=422,
            detail="Supervisory RN visit is missing supervisory_targets context",
        )
# =========================================================
# PHASE B / HOPE HELPERS
# =========================================================
def _severity_rank(value: Optional[str]) -> int:
    if not value:
        return 0
    code = str(value).strip().upper()
    if code == "SEVERE":
        return 3
    if code == "MODERATE":
        return 2
    if code == "MILD":
        return 1
    return 0
def _extract_j2051_impacts_from_notes(
    *,
    notes: list[ClinicalNote],
    visit_id: uuid.UUID,
    request_id: str,) -> tuple[Optional[str], Optional[str]]:
    """
    Extract Phase B trigger values for J2051 from structured note content.
    Returns:
    (
        pain_impact,
       # e.g. MODERATE / SEVERE / None
        non_pain_impact,
   # highest non-pain symptom impact if any
    )
    Supported pathways:
    - content["assessment"]["pain"]["severity"]
    - content["symptom_impact"] / content["symptomImpact"] dicts
    """
    pain_impact: Optional[str] = None
    non_pain_impact: Optional[str] = None
    logger.info(
        "PHASE_B_J2051_EXTRACT: ENTERED visit_id=%s request_id=%s note_count=%s",
        str(visit_id),
        request_id,
        len(notes),
    )
    for note in notes:
        raw_content = getattr(note, "content", None)
        logger.info(
            "PHASE_B_J2051_EXTRACT: RAW_CONTENT_TYPE "
            "visit_id=%s note_id=%s type=%s request_id=%s",
            str(visit_id),
            str(getattr(note, "id", None)),
            type(raw_content).__name__,
            request_id,
        )
        data: Any = None
        try:
            if raw_content is None:
                continue
            if isinstance(raw_content, dict):
                data = raw_content
            elif isinstance(raw_content, str):
                content_str = raw_content.strip()
                if not content_str:
                    continue
                data = json.loads(content_str)
                if isinstance(data, str):
                    data = json.loads(data)
            else:
                continue
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            logger.exception(
                "PHASE_B_J2051_EXTRACT: PARSE_FAILED visit_id=%s note_id=%s request_id=%s",
                str(visit_id),
                str(getattr(note, "id", None)),
                request_id,
            )
            continue
        if not isinstance(data, dict):
            continue
        assessment = data.get("assessment")
        if isinstance(assessment, dict):
            pain = assessment.get("pain")
            if isinstance(pain, dict):
                severity = pain.get("severity")
                if severity:
                    sev_code = str(severity).strip().upper()
                    if _severity_rank(sev_code) > _severity_rank(pain_impact):
                        pain_impact = sev_code
            for key, value in assessment.items():
                if str(key).strip().lower() == "pain":
                    continue
                if isinstance(value, dict):
                    severity = value.get("severity")
                    if severity:
                        sev_code = str(severity).strip().upper()
                        if _severity_rank(sev_code) > _severity_rank(non_pain_impact):
                            non_pain_impact = sev_code
        symptom_impact = data.get("symptom_impact") or data.get("symptomImpact")
        if isinstance(symptom_impact, dict):
            for key, value in symptom_impact.items():
                key_code = str(key).strip().lower()
                sev_code = str(value).strip().upper()
                if key_code == "pain":
                    if _severity_rank(sev_code) > _severity_rank(pain_impact):
                        pain_impact = sev_code
                else:
                    if _severity_rank(sev_code) > _severity_rank(non_pain_impact):
                        non_pain_impact = sev_code
    logger.info(
        "PHASE_B_J2051_EXTRACT: RESULT visit_id=%s pain_impact=%s non_pain_impact=%s request_id=%s",
        str(visit_id),
        pain_impact,
        non_pain_impact,
        request_id,
    )
    return pain_impact, non_pain_impact
def _extract_primary_diagnosis_from_notes(
    *,
    notes: list[ClinicalNote],) -> str | None:
    """
    Extract primary diagnosis from RN ICA clinical note content.
    RN ICA data is currently stored as:
        ClinicalNote.content
    Supported JSON shapes:
        {
            "primary_diagnosis": "C34.90"
        }
        {
            "primary_dx": "C34.90"
        }
        {
            "primary_dx_code": "C34.90"
        }
        {
            "diagnosis": {
                "primary_diagnosis": "C34.90"
            }
        }
        {
            "diagnosis": {
                "primary_dx": "C34.90"
            }
        }
        {
            "diagnosis": {
                "icd_code": "C34.90"
            }
        }
        {
            "diagnoses": {
                "primary_diagnosis": "C34.90"
            }
        }
        {
            "diagnoses": [
                {
                    "type": "PRIMARY",
                    "code": "C34.90"
                }
            ]
        }
    This helper is intentionally tolerant because RN ICA JSON structure
    is not yet locked into a dedicated schema/model.
    """
    for note in notes:
        content = getattr(note, "content", None) or {}
        if not isinstance(content, dict):
            continue
        # -------------------------------------------------
        # DIRECT ROOT-LEVEL KEYS
        # -------------------------------------------------
        direct_candidates = [
            content.get("primary_diagnosis"),
            content.get("primary_dx"),
            content.get("primary_dx_code"),
        ]
        for value in direct_candidates:
            if value is not None and str(value).strip():
                return str(value).strip()
        # -------------------------------------------------
        # diagnosis: {...}
        # -------------------------------------------------
        diagnosis = content.get("diagnosis")
        if isinstance(diagnosis, dict):
            nested_candidates = [
                diagnosis.get("primary_diagnosis"),
                diagnosis.get("primary_dx"),
                diagnosis.get("primary_dx_code"),
                diagnosis.get("icd_code"),
                diagnosis.get("code"),
            ]
            for value in nested_candidates:
                if value is not None and str(value).strip():
                    return str(value).strip()
        # -------------------------------------------------
        # diagnoses: {...}
        # -------------------------------------------------
        diagnoses = content.get("diagnoses")
        if isinstance(diagnoses, dict):
            diagnoses_candidates = [
                diagnoses.get("primary_diagnosis"),
                diagnoses.get("primary_dx"),
                diagnoses.get("primary_dx_code"),
                diagnoses.get("icd_code"),
                diagnoses.get("code"),
            ]
            for value in diagnoses_candidates:
                if value is not None and str(value).strip():
                    return str(value).strip()
        # -------------------------------------------------
        # diagnoses: [{...}]
        # -------------------------------------------------
        if isinstance(diagnoses, list):
            for item in diagnoses:
                if not isinstance(item, dict):
                    continue
                dx_type = str(
                    item.get("type")
                    or item.get("dx_type")
                    or item.get("diagnosis_type")
                    or ""
                ).strip().upper()
                if dx_type != "PRIMARY":
                    continue
                list_candidates = [
                    item.get("primary_diagnosis"),
                    item.get("primary_dx"),
                    item.get("primary_dx_code"),
                    item.get("icd_code"),
                    item.get("code"),
                    item.get("diagnosis"),
                ]
                for value in list_candidates:
                    if value is not None and str(value).strip():
                        return str(value).strip()
    return None
def _find_oldest_open_sfv_requirement_for_patient(
    *,
    db: Session,
    patient_id: uuid.UUID,) -> Optional[SFVRequirement]:
    return (
        db.query(SFVRequirement)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            SFVRequirement.patient_id == patient_id,
            SFVRequirement.status == "OPEN",
        )
        .order_by(SFVRequirement.due_at.asc())
        .first()
    )
def _get_completed_huv_task_type_for_visit(
    *,
    db: Session,
    visit: Visit,) -> Optional[str]:
    completed = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.status == TaskStatus.COMPLETED,
            Task.completion_reference_id == visit.id,
            Task.task_type.in_([TaskType.HUV1, TaskType.HUV2]),
        )
        .order_by(Task.completed_at.desc())
        .first()
    )
    if not completed:
        return None
    return completed.task_type.value if hasattr(completed.task_type, "value") else str(completed.task_type)
def _maybe_complete_open_sfv_for_visit(
    *,
    db: Session,
    visit: Visit,
    request_id: str,) -> Optional[SFVRequirement]:
    open_requirement = _find_oldest_open_sfv_requirement_for_patient(
        db=db,
        patient_id=visit.patient_id,
    )
    if not open_requirement:
        logger.info(
            "PHASE_B_SFV_COMPLETE: NO_OPEN_REQUIREMENT visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        return None
    try:
        completed_requirement = complete_sfv_requirement_from_visit(
            db=db,
            sfv_requirement_id=open_requirement.id,
            completing_visit_id=visit.id,
            completing_visit_datetime=visit.visit_datetime,
            discipline=visit.visit_discipline,
            visit_mode=getattr(visit, "visit_mode", None),
        )
        logger.info(
            "PHASE_B_SFV_COMPLETE: COMPLETED requirement_id=%s visit_id=%s request_id=%s",
            str(completed_requirement.id),
            str(visit.id),
            request_id,
        )
        return completed_requirement
    except ValueError as exc:
        logger.info(
            "PHASE_B_SFV_COMPLETE: NOT_ELIGIBLE visit_id=%s requirement_id=%s reason=%s request_id=%s",
            str(visit.id),
            str(open_requirement.id),
            str(exc),
            request_id,
        )
        return None
def _run_phase_b_finalize_hooks(
    *,
    db: Session,
    visit: Visit,
    completed_task_types: list[str],
    notes: list[ClinicalNote],
    request_id: str,) -> None:
    pain_impact, non_pain_impact = _extract_j2051_impacts_from_notes(
        notes=notes,
        visit_id=visit.id,
        request_id=request_id,
    )
    _maybe_complete_open_sfv_for_visit(
        db=db,
        visit=visit,
        request_id=request_id,
    )
    if "INITIAL_RN_ICA" in completed_task_types:
        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_TRIGGER visit_id=%s patient_id=%s request_id=%s",
            str(visit.id),
            str(visit.patient_id),
            request_id,
        )
        result = process_initial_rn_ica_finalize(
            db=db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            initial_rn_ica_visit_id=visit.id,
            election_datetime=visit.visit_datetime,
            j2051_pain_impact=pain_impact,
            j2051_non_pain_impact=non_pain_impact,
        )
        rn_ica_primary_diagnosis = _extract_primary_diagnosis_from_notes(
            notes=notes,
        )
        diagnosis_sync_result = sync_official_primary_diagnosis(
            db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            primary_diagnosis=rn_ica_primary_diagnosis,
            source="RN_ICA",
            updated_by=(
                getattr(visit, "finalized_by", None)
                or getattr(visit, "updated_by", None)
                or getattr(visit, "created_by", None)
            ),
        )
        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_DIAGNOSIS_SYNC visit_id=%s result=%s request_id=%s",
            str(visit.id),
            diagnosis_sync_result,
            request_id,
        )
        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_RESULT visit_id=%s result=%s request_id=%s",
            str(visit.id),
            result,
            request_id,
        )
    completed_huv_type = _get_completed_huv_task_type_for_visit(
        db=db,
        visit=visit,
    )
    if completed_huv_type in {"HUV1", "HUV2"}:
        logger.info(
            "PHASE_B_HOOK: HUV_TRIGGER visit_id=%s huv_type=%s patient_id=%s request_id=%s",
            str(visit.id),
            completed_huv_type,
            str(visit.patient_id),
            request_id,
        )
        result = process_huv_finalize(
            db=db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            huv_task_type=completed_huv_type,
            huv_visit_id=visit.id,
            election_datetime=visit.visit_datetime,
            completed_visit_datetime=visit.visit_datetime,
            discipline=visit.visit_discipline,
            j2051_pain_impact=pain_impact,
            j2051_non_pain_impact=non_pain_impact,
        )
        logger.info(
            "PHASE_B_HOOK: HUV_RESULT visit_id=%s result=%s request_id=%s",
            str(visit.id),
            result,
            request_id,
        )
# =========================================================
# VISIT STATUS CHANGE
# =========================================================
@router.patch("/{visit_id}/status", response_model=VisitMutationResponse)
def update_visit_status(
    visit_id: uuid.UUID,
    payload: VisitStatusUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    new_status = (payload.status or "").strip().upper()
    if not new_status:
        raise HTTPException(status_code=422, detail="status is required")
    if new_status not in ALLOWED_STATUS_CHANGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. Allowed: {sorted(ALLOWED_STATUS_CHANGES)}",
        )
    already_finalized = (visit.status or "").upper() == "FINALIZED"
    if already_finalized:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot change status of a FINALIZED visit. "
                "Create a new visit or document variance in Communications Log."
            ),
        )
    enforce_commlog_for_visit_status_change(
        db=db,
        visit=visit,
        new_status=new_status,
        communications_log_id=payload.communications_log_id,
    )
    now = datetime.now(timezone.utc)
    visit.status = new_status
    if hasattr(visit, "updated_at"):
        visit.updated_at = now
    if hasattr(visit, "communications_log_id"):
        visit.communications_log_id = payload.communications_log_id
    elif hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}
        details["communications_log_id"] = (
            str(payload.communications_log_id)
            if payload.communications_log_id
            else None
        )
        visit.details = details
    try:
        db.flush()
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="UPDATE_VISIT_STATUS",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={"new_status": new_status},
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Visit status update failed",
            extra={
                "visit_id": str(visit.id),
                "new_status": new_status,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit status update failed: {exc}",
        )
    return VisitMutationResponse(
        status="updated",
        visit_id=str(visit.id),
        request_id=request_id,
        completed_task_types=[],
        new_status=new_status,
        communications_log_id=(
            str(payload.communications_log_id)
            if payload.communications_log_id
            else None
        ),
    )
# =========================================================
# CREATE VISIT
# =========================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VisitCreateResponse,)
def create_visit(
    payload: VisitCreateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    # =========================================================
    # LOAD PATIENT + CONTEXT
    # =========================================================
    patient = _load_patient_for_update(db, payload.patient_id)
    get_authorized_patient(db, patient.id, current_user)
    _set_db_context(db, patient.tenant_id, user_id, request_id)
    # =========================================================
    # VALIDATION / NORMALIZATION
    # =========================================================
    normalized = _canonicalize_discipline(payload.visit_type)
    validated_form_type = _normalize_and_validate_form_type(payload.form_type)
    validated_schedule_type = _normalize_schedule_type(payload.visit_schedule_type)
    validated_event_type = _normalize_event_type_for_form(
        validated_form_type,
        payload.event_type,
    )
    _enforce_form_selection_rules(
        discipline=normalized,
        form_type=validated_form_type,
        visit_schedule_type=validated_schedule_type,
        event_type=validated_event_type,
    )
    now = datetime.now(timezone.utc)
    # =========================================================
    # RESOLVE ACTIVE ADMISSION FOR THIS VISIT
    # =========================================================
    resolved_admission = (
        db.query(Admission)
        .filter(
            Admission.patient_id == patient.id,
            Admission.tenant_id == patient.tenant_id,
            Admission.status == "ADMITTED",
        )
        .order_by(Admission.created_at.desc())
        .first()
    )
    if not resolved_admission:
        raise HTTPException(
            status_code=400,
            detail="Patient must have an active admitted admission before creating a SOC visit",
        )
    # =========================================================
    # SUPERVISORY CONTEXT
    # =========================================================
    is_supervisory, supervisory_targets = _determine_supervisory_context(
        db=db,
        patient=patient,
        normalized_visit_type=normalized,
        validated_form_type=validated_form_type,
        now=now,
    )
    # =========================================================
    # INIT VISIT
    # =========================================================
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        admission_id=resolved_admission.id,
        patient_id=patient.id,
        provider_id=user_id,
        visit_type=normalized,
        visit_discipline=normalized,
        visit_mode="IN_PERSON",
        status="DRAFT",
        visit_datetime=now,
        acuity_state_at_visit=getattr(patient, "acuity_state", None),
        form_type=validated_form_type,
        is_supervisory=is_supervisory,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )
    try:
        # =========================================================
        # SAVE VISIT
        # =========================================================
        db.add(visit)
        db.flush()
        # 🚨 CRITICAL GUARD
        if not visit.admission_id:
            raise HTTPException(
                status_code=500,
                detail="Visit created without admission_id — system error",
            )
        _apply_supervisory_context_to_visit(
            visit=visit,
            is_supervisory=is_supervisory,
            supervisory_targets=supervisory_targets,
        )
        # =========================================================
        # FORM RESOLUTION
        # =========================================================
        form_config = resolve_form_package(
            discipline=normalized,
            form_type=validated_form_type,
            level_of_care=_normalize_level_of_care(payload.level_of_care),
            event_type=validated_event_type,
        )
        resolved_primary_form = (
            form_config.get("primary_form")
            or form_config.get("form_key")
        )
        resolved_attached_forms = (
            form_config.get("attached_forms")
            or form_config.get("attached_form_keys")
            or []
        )
        resolved_modules = (
            form_config.get("modules")
            or form_config.get("primary_modules")
            or []
        )
        if not form_config or not resolved_primary_form:
            raise HTTPException(
                status_code=422,
                detail="Unable to resolve form package",
            )
        primary_form = _guard_against_generic_note_type(
            resolved_primary_form,
            request_id=request_id,
        )
        attached_forms = [
            _guard_against_generic_note_type(name, request_id=request_id)
            for name in list(resolved_attached_forms)
        ]
        resolved_form_family = form_config.get("form_family")
        form_family = (
            resolved_form_family.value
            if hasattr(resolved_form_family, "value")
            else resolved_form_family
        )
        modules = list(resolved_modules)
        resolved_by = form_config.get("resolved_by")
        resolved_form_type = form_config.get("form_type") or validated_form_type
        # =========================================================
        # ✅ POC TRIGGER DETECTION (KEEP — CRITICAL)
        # =========================================================
        note = payload.clinical_note or {}
        assessment = note.get("assessment", {})
        poc_update_required = False
        pain_score = assessment.get("pain_score")
        psychosocial = assessment.get("psychosocial")
        spiritual = assessment.get("spiritual")
        if pain_score is not None and pain_score >= 5:
            poc_update_required = True
        if psychosocial:
            poc_update_required = True
        if spiritual:
            poc_update_required = True
        logger.info(
            "POC_TRIGGER_DETECTION visit_id=%s pain=%s psychosocial=%s spiritual=%s result=%s request_id=%s",
            str(visit.id),
            pain_score,
            psychosocial,
            spiritual,
            poc_update_required,
            request_id,
        )
        if poc_update_required:
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="POC_TRIGGER_DETECTED",
                entity_type="visit",
                entity_id=visit.id,
                request_id=request_id,
            )
        # =========================================================
        # PRIMARY NOTE
        # =========================================================
        primary_note = ClinicalNote(
            id=uuid.uuid4(),
            visit_id=visit.id,
            author_id=user_id,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            note_type=primary_form,
            discipline=visit.visit_discipline,
            form_family=form_family,
            form_key=primary_form,
            module_payload={
                "modules": modules,
                "attached_forms": attached_forms,
                "resolved_by": resolved_by,
                "form_type": resolved_form_type,
            },
            is_primary_form=True,
            parent_form_id=None,
            status="DRAFT",
            encounter_date=now.date(),
            content=(payload.clinical_note or {}),
            plan_of_care_updates={
                "meta": {
                    "version": "1.0",
                    "generated_at": now.isoformat(),
                    "note_id": None,
                    "patient_id": str(visit.patient_id),
                },
                "pocs": [],
            },
            created_by=user_id,
            created_at=now,
            updated_at=now,
            updated_by_user_id=user_id,
            entered_at=now,
            care_level_snapshot=_normalize_level_of_care(payload.level_of_care),
            is_late_entry=False,
        )
        db.add(primary_note)
        db.flush()
        validate_and_trigger_incident(
            db=db,
            note=primary_note,
            actor_user_id=user_id,
            actor_role="CLINICIAN",
        )
        # =========================================================
        # ATTACHED NOTES
        # =========================================================
        for form_key in attached_forms:
            attached_note = ClinicalNote(
                id=uuid.uuid4(),
                visit_id=visit.id,
                author_id=user_id,
                tenant_id=visit.tenant_id,
                patient_id=visit.patient_id,
                note_type=form_key,
                discipline=visit.visit_discipline,
                form_family=form_family,
                form_key=form_key,
                module_payload={
                    "modules": [],
                    "attached_forms": [],
                    "resolved_by": resolved_by,
                    "form_type": resolved_form_type,
                },
                is_primary_form=False,
                parent_form_id=primary_note.id,
                status="DRAFT",
                encounter_date=now.date(),
                content={},
                plan_of_care_updates={
                    "meta": {
                        "version": "1.0",
                        "generated_at": now.isoformat(),
                        "note_id": None,
                        "patient_id": str(visit.patient_id),
                    },
                    "pocs": [],
                },
                created_by=user_id,
                created_at=now,
                updated_at=now,
                updated_by_user_id=user_id,
                entered_at=now,
                care_level_snapshot=_normalize_level_of_care(payload.level_of_care),
                is_late_entry=False,
            )
            db.add(attached_note)
        # =========================================================
        # AUDIT LOG
        # =========================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CREATE_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "VISIT_CREATE_FAILED",
            extra={
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit creation failed: {exc}",
        )
    # =========================================================
    # FINAL RETURN (CRITICAL — NEVER SKIP)
    # =========================================================
    return VisitCreateResponse(
        visit_id=str(visit.id),
        visit_type=normalized,
        form_type=resolved_form_type,
        form_family=form_family,
        primary_form=primary_form,
        attached_forms=attached_forms,
        modules=modules,
        resolved_by=resolved_by,
        is_supervisory=is_supervisory,
        supervisory_targets=supervisory_targets,
        request_id=request_id,
    )
@router.post("/{visit_id}/reopen")
def reopen_visit(
    visit_id: uuid.UUID,
    payload: VisitReopenRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    actor_role = str(getattr(current_user, "role", "SYSTEM")).strip().upper()
    # =========================================================
    # LOAD VISIT
    # =========================================================
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    # =========================================================
    # 🚨 CRITICAL: ADMISSION GUARD
    # =========================================================
    if not getattr(visit, "admission_id", None):
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission — invalid chart state",
        )
    logger.info(
        "REOPEN: VISIT_LOADED visit_id=%s patient_id=%s status=%s role=%s request_id=%s",
        str(visit.id),
        str(visit.patient_id),
        getattr(visit, "status", None),
        actor_role,
        request_id,
    )
    # =========================================================
    # STATUS VALIDATION
    # =========================================================
    current_status = (getattr(visit, "status", "") or "").upper()
    if current_status != "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Only FINALIZED visits can be reopened.",
        )
    # =========================================================
    # ROLE VALIDATION
    # =========================================================
    if actor_role not in ALLOWED_REOPEN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Administrator, DPCS, DPCS Designee, Supervisor, or Case Manager approval is required to reopen finalized documentation.",
        )
    # =========================================================
    # TIME CONTEXT
    # =========================================================
    now = datetime.now(timezone.utc)
    # =========================================================
    # LOCKED STATE CHECK
    # =========================================================
    early_lock, early_lock_reason = _visit_has_early_lock(visit)
    if early_lock:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This documentation is locked because '{early_lock_reason}' is present. "
                "Add an amendment instead of modifying the original record."
            ),
        )
    # =========================================================
    # CORRECTION WINDOW CHECK
    # =========================================================
    if not _visit_is_within_correction_window(visit, now):
        raise HTTPException(
            status_code=409,
            detail=(
                "This documentation is outside the 72-hour correction window. "
                "Add an amendment instead of modifying the original record."
            ),
        )
    # =========================================================
    # APPLY REOPEN
    # =========================================================
    try:
        _apply_reopen_metadata(
            visit=visit,
            user_id=user_id,
            reason=payload.reason,
            now=now,
        )
        db.flush()
        # =====================================================
        # AUDIT LOG (ENHANCED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="REOPEN_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "reason": payload.reason,
                "previous_status": "FINALIZED",
                "new_status": "REOPENED",
                "admission_id": str(visit.admission_id),
                "actor_role": actor_role,
            },
        )
        db.commit()
        logger.info(
            "REOPEN: SUCCESS visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "REOPEN_VISIT_FAILED",
            extra={
                "visit_id": str(visit.id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit reopen failed: {exc}",
        )
    # =========================================================
    # RESPONSE
    # =========================================================
    return {
        "status": "reopened",
        "visit_id": str(visit.id),
        "request_id": request_id,
        "message": (
            "Visit reopened. Update the documentation and finalize again within the 72-hour correction window."
        ),
    }
@router.post("/{visit_id}/chha-outcome")
def upsert_chha_visit_outcome(
    visit_id: uuid.UUID,
    payload: CHHAOutcomeUpsertRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    # =========================================================
    # LOAD VISIT
    # =========================================================
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    # =========================================================
    # 🚨 CRITICAL: ADMISSION GUARD
    # =========================================================
    if not getattr(visit, "admission_id", None):
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission — invalid state",
        )
    # =========================================================
    # DISCIPLINE VALIDATION
    # =========================================================
    discipline = (getattr(visit, "visit_discipline", "") or "").upper()
    if discipline not in {"AIDE"}:
        raise HTTPException(
            status_code=422,
            detail="CHHA outcome can only be recorded for AIDE/CHHA visits",
        )
    # =========================================================
    # VISIT STATUS GUARD
    # =========================================================
    visit_status = (getattr(visit, "status", "") or "").upper()
    if visit_status == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Cannot modify outcome on finalized visit",
        )
    # =========================================================
    # RESOLVE ADMISSION (FOR AUDIT CONTEXT)
    # =========================================================
    resolved_admission_id = str(visit.admission_id)
    # =========================================================
    # UPSERT OUTCOME
    # =========================================================
    try:
        outcome = upsert_chha_outcome(
            db=db,
            visit=visit,
            user_id=user_id,
            payload=payload,
        )
        # =====================================================
        # AUDIT LOG (REQUIRED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="UPSERT_CHHA_OUTCOME",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "admission_id": resolved_admission_id,
                "discipline": discipline,
            },
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "CHHA_OUTCOME_SAVE_FAILED",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"CHHA outcome save failed: {exc}",
        )
    # =========================================================
    # RESPONSE
    # =========================================================
    return {
        "status": "saved",
        "visit_id": str(visit.id),
        "outcome_id": str(outcome.id),
        "request_id": request_id,
    }
@router.get("/patient/{patient_id}/aide")
def list_aide_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """
    Lists this patient's Home Health Aide (CHHA) visits, most recent first, so
    the aide/RN can pick which visit to document a CHHA Visit Note for.
    Includes whether a structured outcome has already been recorded, so the
    UI can distinguish "start a note" from "resume/edit the note already
    saved" instead of risking an accidental overwrite.
    """
    get_authorized_patient(db, patient_id, current_user)
    visits = (
        db.query(Visit)
        .filter(
            Visit.patient_id == patient_id,
            Visit.visit_discipline == "AIDE",
            Visit.deleted_at.is_(None),
        )
        .order_by(Visit.visit_datetime.desc())
        .limit(50)
        .all()
    )
    if not visits:
        return []
    visit_ids = [v.id for v in visits]
    outcome_by_visit = {
        o.visit_id: o
        for o in db.query(CHHAVisitOutcome).filter(CHHAVisitOutcome.visit_id.in_(visit_ids)).all()
    }
    return [
        {
            "visit_id": str(v.id),
            "visit_datetime": v.visit_datetime,
            "status": v.status,
            "has_outcome": v.id in outcome_by_visit,
            "rn_notification_required": (
                outcome_by_visit[v.id].rn_notification_required if v.id in outcome_by_visit else False
            ),
        }
        for v in visits
    ]
@router.get("/{visit_id}/chha-outcome")
def get_chha_visit_outcome(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """
    Fetches the structured CHHA Visit Note already saved for a visit (if
    any), including its task results, so the UI can resume/edit an
    in-progress note instead of starting blank and silently overwriting a
    prior submission on save.
    """
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    get_authorized_patient(db, visit.patient_id, current_user)
    outcome = (
        db.query(CHHAVisitOutcome)
        .filter(CHHAVisitOutcome.visit_id == visit_id)
        .first()
    )
    if not outcome:
        return None
    task_results = (
        db.query(CHHAVisitTaskResult)
        .filter(CHHAVisitTaskResult.outcome_id == outcome.id)
        .all()
    )
    return {
        "outcome_id": str(outcome.id),
        "visit_id": str(outcome.visit_id),
        "poc_reference_id": str(outcome.poc_reference_id) if outcome.poc_reference_id else None,
        "tolerance_to_care": outcome.tolerance_to_care,
        "condition_during_visit": outcome.condition_during_visit,
        "skin_outcome": outcome.skin_outcome,
        "pain_or_change_observed": outcome.pain_or_change_observed,
        "rn_notification_required": outcome.rn_notification_required,
        "rn_notified": outcome.rn_notified,
        "rn_notified_at": outcome.rn_notified_at,
        "rn_notified_name": outcome.rn_notified_name,
        "caregiver_instruction_provided": outcome.caregiver_instruction_provided,
        "caregiver_understanding_confirmed": outcome.caregiver_understanding_confirmed,
        "exception_narrative": outcome.exception_narrative,
        "correction": outcome.correction,
        "type_of_visit": outcome.type_of_visit,
        "visit_kind": outcome.visit_kind,
        "visit_kind_specify": outcome.visit_kind_specify,
        "reason_for_visit": outcome.reason_for_visit,
        "visit_date": outcome.visit_date,
        "time_in": outcome.time_in,
        "time_out": outcome.time_out,
        "duration": outcome.duration,
        "entered_by": outcome.entered_by,
        "staff_assigned": outcome.staff_assigned,
        "care_level": outcome.care_level,
        "updated_at": outcome.updated_at,
        "task_results": [
            {
                "section_code": t.section_code,
                "task_code": t.task_code,
                "was_assigned": t.was_assigned,
                "completed": t.completed,
                "refused": t.refused,
                "not_done": t.not_done,
                "observation_code": t.observation_code,
                "result_note": t.result_note,
            }
            for t in task_results
        ],
    }
# =========================================================
# CONTINUOUS CARE (CC) HOURLY NARRATIVE
# =========================================================
# Shared hourly documentation form used across RN, LVN, AIDE (CHHA), MSW,
# and Chaplain visits whenever the patient's care level is Continuous
# Care. Entries are scoped to a single visit; a visit accumulates one row
# per hour (or per check-in) for the duration of that CC shift/visit.
def _cc_entry_to_dict(entry: CCHourlyNarrativeEntry) -> dict:
    return {
        "id": str(entry.id),
        "visit_id": str(entry.visit_id),
        "discipline": entry.discipline,
        "entry_date": entry.entry_date,
        "entry_time": entry.entry_time,
        "temperature": entry.temperature,
        "pulse": entry.pulse,
        "respirations": entry.respirations,
        "bp_systolic": entry.bp_systolic,
        "bp_diastolic": entry.bp_diastolic,
        "o2_sat": entry.o2_sat,
        "pain_level": entry.pain_level,
        "pain_location": entry.pain_location,
        "pain_intervention": entry.pain_intervention,
        "symptoms": entry.symptoms,
        "care_provided": entry.care_provided,
        "issue_identified": entry.issue_identified,
        "issue_narrative": entry.issue_narrative,
        "poc_update_narrative": entry.poc_update_narrative,
        "narrative": entry.narrative,
        "entered_by": entry.entered_by,
        "created_at": entry.created_at,
    }
@router.get("/{visit_id}/cc-entries")
def list_cc_hourly_narrative_entries(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    get_authorized_patient(db, visit.patient_id, current_user)
    entries = (
        db.query(CCHourlyNarrativeEntry)
        .filter(CCHourlyNarrativeEntry.visit_id == visit_id)
        .order_by(CCHourlyNarrativeEntry.created_at.asc())
        .all()
    )
    return [_cc_entry_to_dict(e) for e in entries]
@router.post("/{visit_id}/cc-entries", status_code=status.HTTP_201_CREATED)
def create_cc_hourly_narrative_entry(
    visit_id: uuid.UUID,
    payload: CCHourlyNarrativeEntryRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    visit_status = (getattr(visit, "status", "") or "").upper()
    if visit_status == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Cannot add continuous care entries to a finalized visit",
        )
    entry = CCHourlyNarrativeEntry(
        tenant_id=visit.tenant_id,
        patient_id=visit.patient_id,
        visit_id=visit.id,
        discipline=payload.discipline,
        entry_date=payload.entry_date,
        entry_time=payload.entry_time,
        temperature=payload.temperature,
        pulse=payload.pulse,
        respirations=payload.respirations,
        bp_systolic=payload.bp_systolic,
        bp_diastolic=payload.bp_diastolic,
        o2_sat=payload.o2_sat,
        pain_level=payload.pain_level,
        pain_location=payload.pain_location,
        pain_intervention=payload.pain_intervention,
        symptoms=payload.symptoms,
        care_provided=payload.care_provided,
        issue_identified=payload.issue_identified,
        issue_narrative=payload.issue_narrative,
        poc_update_narrative=payload.poc_update_narrative,
        narrative=payload.narrative,
        entered_by=payload.entered_by,
        created_by=user_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    _safe_log_event(
        db=db,
        user_id=user_id,
        action="CREATE_CC_HOURLY_NARRATIVE_ENTRY",
        entity_type="visit",
        entity_id=visit.id,
        request_id=request_id,
        metadata={"visit_id": str(visit.id), "patient_id": str(visit.patient_id)},
    )
    return _cc_entry_to_dict(entry)
@router.delete("/{visit_id}/cc-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cc_hourly_narrative_entry(
    visit_id: uuid.UUID,
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    get_authorized_patient(db, visit.patient_id, current_user)
    entry = (
        db.query(CCHourlyNarrativeEntry)
        .filter(CCHourlyNarrativeEntry.id == entry_id, CCHourlyNarrativeEntry.visit_id == visit_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Continuous care entry not found")
    db.delete(entry)
    db.commit()
    return None
# =========================================================
# VISIT NOTES (RN / LVN)
# =========================================================
def _visit_note_to_dict(visit: Visit, note: ClinicalNote) -> dict:
    module_payload = note.module_payload or {}
    return {
        "visit_id": str(visit.id),
        "patient_id": str(visit.patient_id),
        "note_id": str(note.id),
        "discipline": visit.visit_discipline,
        "form_type": module_payload.get("form_type") or visit.form_type,
        "status": note.status,
        "visit_status": visit.status,
        "finalized_at": note.finalized_at,
        "finalized_by": str(note.finalized_by) if note.finalized_by else None,
        "visit_datetime": visit.visit_datetime,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "content": note.content or {},
    }
@router.get("/{visit_id}/visit-note")
def get_visit_note(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """
    Returns the Visit Details bar + full clinical documentation body for
    the RN/LVN "Visit Notes" module (backed by the visit's primary
    ClinicalNote).
    """
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    get_authorized_patient(db, visit.patient_id, current_user)
    discipline = (getattr(visit, "visit_discipline", "") or "").upper()
    if discipline not in VISIT_NOTE_DISCIPLINES:
        raise HTTPException(
            status_code=422,
            detail="Visit Notes are only available for RN and LVN visits",
        )
    primary_note = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.visit_id == visit_id,
            ClinicalNote.is_primary_form.is_(True),
        )
        .order_by(ClinicalNote.created_at.asc())
        .first()
    )
    if not primary_note:
        raise HTTPException(
            status_code=404,
            detail="No clinical note found for this visit",
        )
    return _visit_note_to_dict(visit, primary_note)
@router.put("/{visit_id}/visit-note")
def update_visit_note(
    visit_id: uuid.UUID,
    payload: VisitNoteContentRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """
    Updates the RN/LVN Visit Note content: Visit Details, and -- unless
    care_level is Continuous Care (in which case documentation happens via
    the CC Hourly Narrative log instead, see CCHourlyNarrativeEntry /
    ContinuousCareLogSection) -- Pain / Vitals & Measurements / Signs &
    Symptoms / Care Provided / Visit Check List / Narrative. Content is
    persisted as JSONB on the visit's primary ClinicalNote.
    """
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    discipline = (getattr(visit, "visit_discipline", "") or "").upper()
    if discipline not in VISIT_NOTE_DISCIPLINES:
        raise HTTPException(
            status_code=422,
            detail="Visit Notes are only available for RN and LVN visits",
        )
    visit_status = (getattr(visit, "status", "") or "").upper()
    if visit_status == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Cannot modify a finalized visit",
        )
    primary_note = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.visit_id == visit_id,
            ClinicalNote.is_primary_form.is_(True),
        )
        .with_for_update()
        .order_by(ClinicalNote.created_at.asc())
        .first()
    )
    if not primary_note:
        raise HTTPException(
            status_code=404,
            detail="No clinical note found for this visit",
        )
    if primary_note.finalized_at:
        raise HTTPException(
            status_code=409,
            detail="Cannot modify a finalized visit note",
        )
    validated_form_type = (
        VisitFormType(payload.form_type) if payload.form_type else None
    )
    try:
        content_dict = payload.model_dump(exclude={"form_type"})
        content_dict["form_type"] = validated_form_type.value if validated_form_type else None
        # Non-Assess/Routine form types collapse the documentation body
        # down to a narrative-only note in the legacy workflow -- clear any
        # stray clinical-body data so switching Form Type doesn't silently
        # retain (and later resurface) pain/vitals/signs-and-symptoms data
        # entered under a different form type.
        is_full_body = (
            validated_form_type is None
            or validated_form_type.value in VISIT_NOTE_FULL_BODY_FORM_TYPES
        )
        if not is_full_body:
            content_dict["pain"] = None
            content_dict["vitals"] = None
            content_dict["signs_symptoms"] = {}
            content_dict["care_provided"] = None
            content_dict["visit_checklist"] = None
        now = datetime.now(timezone.utc)
        primary_note.content = content_dict
        primary_note.updated_at = now
        primary_note.updated_by_user_id = user_id
        if validated_form_type is not None:
            visit.form_type = validated_form_type.value
            module_payload = dict(primary_note.module_payload or {})
            module_payload["form_type"] = validated_form_type.value
            primary_note.module_payload = module_payload
        if payload.care_level:
            primary_note.care_level_snapshot = _normalize_level_of_care(payload.care_level)
        if hasattr(visit, "updated_at"):
            visit.updated_at = now
        if hasattr(visit, "updated_by"):
            visit.updated_by = user_id
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="UPDATE_VISIT_NOTE",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "discipline": discipline,
                "form_type": validated_form_type.value if validated_form_type else None,
                "care_level": payload.care_level,
            },
        )
        db.commit()
        db.refresh(primary_note)
        db.refresh(visit)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "VISIT_NOTE_UPDATE_FAILED",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit note update failed: {exc}",
        )
    return _visit_note_to_dict(visit, primary_note)
@router.get("/patient/{patient_id}/visit-notes")
def list_visit_notes_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    """
    Combined "Visit Notes" timeline for a patient: RN/LVN visit notes
    (Visit + primary ClinicalNote) merged with the patient's MSW ICA and
    SC ICA assessments, per product requirement -- when MSW or SC complete
    their own existing assessment forms, those records surface in this
    same shared timeline (read-only here; MSW/SC continue to author their
    notes through MSWICA.jsx / SCICA.jsx, not this module).
    """
    get_authorized_patient(db, patient_id, current_user)
    entries: List[dict] = []
    # ---- RN / LVN visit notes ----
    rn_lvn_visits = (
        db.query(Visit)
        .filter(
            Visit.patient_id == patient_id,
            Visit.visit_discipline.in_(list(VISIT_NOTE_DISCIPLINES)),
            Visit.deleted_at.is_(None),
        )
        .order_by(Visit.visit_datetime.desc())
        .limit(200)
        .all()
    )
    if rn_lvn_visits:
        visit_ids = [v.id for v in rn_lvn_visits]
        notes_by_visit = {
            n.visit_id: n
            for n in (
                db.query(ClinicalNote)
                .filter(
                    ClinicalNote.visit_id.in_(visit_ids),
                    ClinicalNote.is_primary_form.is_(True),
                )
                .all()
            )
        }
        for v in rn_lvn_visits:
            note = notes_by_visit.get(v.id)
            content = (note.content or {}) if note else {}
            narrative = content.get("narrative") or ""
            module_payload = (note.module_payload or {}) if note else {}
            entries.append(
                {
                    "source": "VISIT_NOTE",
                    "id": str(note.id) if note else str(v.id),
                    "visit_id": str(v.id),
                    "patient_id": str(patient_id),
                    "discipline": v.visit_discipline,
                    "form_type": module_payload.get("form_type") or v.form_type,
                    "care_level": content.get("care_level"),
                    "visit_date": v.visit_datetime,
                    "status": note.status if note else v.status,
                    "narrative_preview": (narrative[:200] if narrative else None),
                    "created_at": note.created_at if note else v.created_at,
                }
            )
    # ---- MSW ICA assessments (migrated into the shared timeline) ----
    msw_assessments = (
        db.query(MswIcaAssessment)
        .filter(MswIcaAssessment.patient_id == patient_id)
        .order_by(MswIcaAssessment.created_at.desc())
        .limit(200)
        .all()
    )
    for a in msw_assessments:
        form_data = a.form_data or {}
        visit_meta = form_data.get("visitMeta") or {}
        narrative = form_data.get("narrative") or visit_meta.get("narrative") or ""
        entries.append(
            {
                "source": "MSW_ICA",
                "id": str(a.id),
                "visit_id": str(a.visit_id) if a.visit_id else None,
                "patient_id": str(patient_id),
                "discipline": "MSW",
                "form_type": a.assessment_type,
                "care_level": visit_meta.get("careLevel"),
                "visit_date": a.created_at,
                "status": a.status,
                "narrative_preview": (narrative[:200] if narrative else None),
                "created_at": a.created_at,
            }
        )
    # ---- SC ICA assessments (migrated into the shared timeline) ----
    scica_assessments = (
        db.query(ScicaAssessment)
        .filter(ScicaAssessment.patient_id == patient_id)
        .order_by(ScicaAssessment.created_at.desc())
        .limit(200)
        .all()
    )
    for a in scica_assessments:
        form_data = a.form_data or {}
        visit_meta = form_data.get("visitMeta") or {}
        narrative = form_data.get("narrative") or visit_meta.get("narrative") or ""
        entries.append(
            {
                "source": "SC_ICA",
                "id": str(a.id),
                "visit_id": str(a.visit_id) if a.visit_id else None,
                "patient_id": str(patient_id),
                "discipline": "SC",
                "form_type": a.assessment_type,
                "care_level": visit_meta.get("careLevel"),
                "visit_date": a.created_at,
                "status": a.status,
                "narrative_preview": (narrative[:200] if narrative else None),
                "created_at": a.created_at,
            }
        )
    entries.sort(
        key=lambda e: e["visit_date"] or e["created_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return entries
# =========================================================
# REFUSAL / RE-OFFER
# =========================================================
@router.post(
    "/patients/{patient_id}/refuse",
    status_code=status.HTTP_201_CREATED,
    response_model=RefusalResponse,)
def refuse_service(
    patient_id: uuid.UUID,
    payload: RefusalRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    # =========================================================
    # LOAD PATIENT
    # =========================================================
    patient = _load_patient_for_update(db, patient_id)
    get_authorized_patient(db, patient.id, current_user)
    _set_db_context(db, patient.tenant_id, user_id, request_id)
    # =========================================================
    # NORMALIZE + VALIDATE DISCIPLINE
    # =========================================================
    discipline = (payload.discipline or "").strip().upper()
    ALLOWED_DISCIPLINES = {
        "RN",
        "LVN",
        "SW",
        "CHAPLAIN",
        "AIDE",
        "MD",
        "NP",
        "PA",
    }
    if discipline not in ALLOWED_DISCIPLINES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid discipline '{payload.discipline}'",
        )
    # =========================================================
    # OPTIONAL: RESOLVE ACTIVE ADMISSION
    # =========================================================
    resolved_admission = (
        db.query(Admission)
        .filter(
            Admission.patient_id == patient.id,
            Admission.tenant_id == patient.tenant_id,
            Admission.status == "ADMITTED",
        )
        .order_by(Admission.created_at.desc())
        .first()
    )
    # (Not blocking — refusal can exist without admission,
    # but we log if present)
    # =========================================================
    # RECORD REFUSAL
    # =========================================================
    try:
        refusal = record_refusal(
            db=db,
            patient=patient,
            user_id=user_id,
            discipline=discipline,
            reason=payload.reason,
        )
        # =====================================================
        # AUDIT LOG (ENHANCED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="RECORD_REFUSAL",
            entity_type="patient",
            entity_id=patient.id,
            request_id=request_id,
            metadata={
                "discipline": discipline,
                "reason": payload.reason,
                "admission_id": str(resolved_admission.id)
                if resolved_admission
                else None,
            },
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "REFUSAL_RECORDING_FAILED",
            extra={
                "patient_id": str(patient.id),
                "discipline": discipline,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Refusal recording failed: {exc}",
        )
    # =========================================================
    # RESPONSE
    # =========================================================
    return RefusalResponse(
        status="refusal recorded",
        patient_id=str(patient.id),
        discipline=refusal.discipline,
        reason=refusal.reason,
        refused_at=(
            refusal.refused_at.isoformat()
            if getattr(refusal, "refused_at", None)
            else None
        ),
        request_id=request_id,
    )
# =========================================================
# CLINICAL REASONING HELPERS
# =========================================================
def _content_to_dict(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}
def _extract_clinical_reasoning_payload_from_notes(
    notes: list[ClinicalNote],
    source: str = "RN",) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    allowed_keys = [
        "weight",
        "previous_weight",
        "mac",
        "previous_mac",
        "appetite",
        "previous_appetite",
        "appetite_decline",
        "pain_score",
        "previous_pain_score",
        "pain_increase",
        "pain_location",
        "pain_quality",
        "pain_cause_category",
        "pain_cause_text",
        "pain_cause_source",
        "cause_determination",
        "associated_diagnosis_text",
        "associated_diagnosis_type",
        "terminal_diagnosis",
        "primary_diagnosis",
        "assessment_summary",
        "nursing_summary",
        "weakness_increased",
        "mobility_decline",
        "transfer_assistance_increased",
        "fall_count",
        "caregiver_tearful",
        "caregiver_overwhelmed",
        "respiratory_rate",
        "previous_respiratory_rate",
        "accessory_muscle_use",
        "oxygen_increase",
        "edema_present",
        "edema_worsening",
        "orthopnea",
        "cognitive_decline",
        "behavior_change",
        "spiritual_distress",
        "fear_of_dying",
        "hopelessness",
    ]
    for note in notes:
        content = _content_to_dict(getattr(note, "content", None))
        if not content:
            continue
        assessment = _content_to_dict(content.get("assessment"))
        observed = _content_to_dict(content.get("observed") or content.get("observations"))
        vitals = _content_to_dict(content.get("vitals"))
        pain = _content_to_dict(content.get("pain") or assessment.get("pain"))
        respiratory = _content_to_dict(content.get("respiratory") or assessment.get("respiratory"))
        nutrition = _content_to_dict(content.get("nutrition") or assessment.get("nutrition"))
        functional = _content_to_dict(content.get("functional") or assessment.get("functional"))
        caregiver = _content_to_dict(content.get("caregiver") or assessment.get("caregiver"))
        spiritual = _content_to_dict(content.get("spiritual") or assessment.get("spiritual"))
        sources = [
            content,
            assessment,
            observed,
            vitals,
            pain,
            respiratory,
            nutrition,
            functional,
            caregiver,
            spiritual,
        ]
        for source_dict in sources:
            for key in allowed_keys:
                if key in source_dict and key not in payload:
                    payload[key] = source_dict[key]
        # Common EMR aliases
        if "muac" in payload and "mac" not in payload:
            payload["mac"] = payload["muac"]
        if "current_weight" in payload and "weight" not in payload:
            payload["weight"] = payload["current_weight"]
        if "prior_weight" in payload and "previous_weight" not in payload:
            payload["previous_weight"] = payload["prior_weight"]
        if "current_mac" in payload and "mac" not in payload:
            payload["mac"] = payload["current_mac"]
        if "previous_muac" in payload and "previous_mac" not in payload:
            payload["previous_mac"] = payload["previous_muac"]
    if payload:
        payload["source"] = source
        logger.info(
            "CLINICAL_REASONING_EXTRACTED_PAYLOAD_KEYS keys=%s",
            sorted(payload.keys()),
        )
    return payload
def _get_or_create_clinical_reasoning_record_for_visit(
    db: Session,
    visit: Visit,) -> uuid.UUID:
    return clinical_reasoning_bridge.get_or_create_clinical_reasoning_record(
        db=db,
        patient_id=visit.patient_id,
        episode_id=visit.id,
    )
def _run_clinical_reasoning(
    db: Session,
    patient_id: uuid.UUID,
    tenant_id: uuid.UUID,
    episode_id: uuid.UUID,
    assessment_payload: dict[str, Any],
    request_id: str,
    log_label: str,) -> None:
    """
    Shared engine-invocation path used by RN/LVN visit finalize, MSW/SC
    ICA lock, and MD/NP F2F finalize -- one source of clinical
    intelligence for the whole care team regardless of discipline. Thin
    wrapper over app.services.clinical_reasoning_bridge so this module's
    existing call sites don't need to change.
    """
    clinical_reasoning_bridge.run_clinical_reasoning(
        db=db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        episode_id=episode_id,
        assessment_payload=assessment_payload,
        request_id=request_id,
        log_label=log_label,
    )
def _run_clinical_reasoning_for_visit(
    db: Session,
    visit: Visit,
    notes: list[ClinicalNote],
    request_id: str,) -> None:
    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or getattr(visit, "visit_type", "") or ""
    ).upper()
    source_label = discipline if discipline in ("RN", "LVN") else "RN"
    assessment_payload = _extract_clinical_reasoning_payload_from_notes(notes, source=source_label)
    logger.info(
        "CLINICAL_REASONING_PAYLOAD_KEYS visit_id=%s payload_keys=%s request_id=%s",
        str(visit.id),
        sorted(list(assessment_payload.keys())),
        request_id,
    )
    _run_clinical_reasoning(
        db=db,
        patient_id=visit.patient_id,
        tenant_id=visit.tenant_id,
        episode_id=visit.id,
        assessment_payload=assessment_payload,
        request_id=request_id,
        log_label=f"visit_id={visit.id}",
    )
# =========================================================
# FINALIZE VISIT
# =========================================================
@router.post("/{visit_id}/finalize", response_model=VisitMutationResponse)
def finalize_visit(
    visit_id: uuid.UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    logger.warning(
        "FINALIZE ROUTE ENTERED user_id=%s",
        current_user.user_id,
    )
    visit = _load_visit_for_update(db, visit_id)
    get_authorized_patient(db, visit.patient_id, current_user)
    _set_db_context(db, visit.tenant_id, user_id, request_id)
    if not getattr(visit, "admission_id", None):
        logger.critical(
            "FINALIZE: BLOCKED_NO_ADMISSION visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission - invalid chart state",
        )
    mode = _normalized_mode_from_visit(visit)
    if mode in TELEPHONE_MODES:
        logger.warning(
            "FINALIZE: BLOCKED_TELEPHONE_MODE visit_id=%s mode=%s request_id=%s",
            str(visit.id),
            mode,
            request_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Telephone interactions are not visits",
        )
    if (visit.status or "").upper() == "FINALIZED":
        logger.info(
            "FINALIZE: ALREADY_FINALIZED visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        return VisitMutationResponse(
            status="already_finalized",
            visit_id=str(visit.id),
            request_id=request_id,
            completed_task_types=[],
        )
    now = datetime.now(timezone.utc)
    visit_type = _normalize_and_validate_visit_type(
        getattr(visit, "visit_type", "") or ""
    )
    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or ""
    ).upper()
    form_type = getattr(visit, "form_type", None)
    logger.info(
        "FINALIZE: VISIT_CONTEXT visit_id=%s visit_type=%s discipline=%s form_type=%s request_id=%s",
        str(visit.id),
        visit_type,
        discipline,
        form_type,
        request_id,
    )
    is_admin = visit_type == "ADMINISTRATIVE" or discipline == "ADMINISTRATIVE"
    is_rn = visit_type == "RN" or discipline == "RN"
    is_lvn = visit_type == "LVN" or discipline == "LVN"
    # Visit Notes (skilled physical assessment) covers both RN and LVN
    # visits, so the Clinical Reasoning Engine must process both -- the
    # is_rn flag above is left untouched since it also gates the
    # RN-specific supervisory-visit requirement, which does not apply to
    # LVN visits.
    runs_clinical_reasoning = is_rn or is_lvn
    if is_admin:
        try:
            visit.status = "FINALIZED"
            if hasattr(visit, "finalized_at"):
                visit.finalized_at = now
            if hasattr(visit, "finalized_by"):
                visit.finalized_by = user_id
            if hasattr(visit, "updated_at"):
                visit.updated_at = now
            db.flush()
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="FINALIZE_VISIT",
                entity_type="visit",
                entity_id=visit.id,
                request_id=request_id,
                metadata={
                    "form_type": form_type,
                    "discipline": discipline,
                    "administrative_bypass": True,
                    "admission_id": str(visit.admission_id),
                },
            )
            db.commit()
            return VisitMutationResponse(
                status="finalized",
                visit_id=str(visit.id),
                request_id=request_id,
                completed_task_types=[],
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.exception(
                "FINALIZE: ADMIN_FAILED visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Administrative visit finalization failed: {exc}",
            )
    if not form_type:
        logger.warning(
            "FINALIZE: BLOCKED_MISSING_FORM_TYPE visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=422,
            detail="Visit cannot be finalized without form_type",
        )
    patient = _load_patient_for_update(db, visit.patient_id)
    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.visit_id == visit.id,
            ClinicalNote.tenant_id == visit.tenant_id,
        )
        .all()
    )
    logger.info(
        "FINALIZE: NOTES_LOADED visit_id=%s note_count=%s request_id=%s",
        str(visit.id),
        len(notes),
        request_id,
    )
    if not notes:
        raise HTTPException(
            status_code=422,
            detail="Cannot finalize visit without clinical documentation",
        )
    primary_notes = [note for note in notes if note.note_type]
    if not primary_notes:
        raise HTTPException(
            status_code=422,
            detail="Visit must contain at least one valid clinical form",
        )
    _enforce_rn_supervisory_requirement(
        visit=visit,
        patient=patient,
        is_rn=is_rn,
    )
    blocking_recon_items = (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.patient_id == visit.patient_id)
        .filter(MedReconciliationItem.review_status == "PENDING")
        .order_by(MedReconciliationItem.created_at.asc())
        .all()
    )
    if blocking_recon_items:
        blocking_payload = [
            {
                "item_id": str(item.id),
                "import_id": str(item.import_id) if getattr(item, "import_id", None) else None,
                "med_name_raw": item.med_name_raw,
                "med_name_normalized": getattr(item, "med_name_normalized", None),
                "dose": getattr(item, "dose", None),
                "route": getattr(item, "route", None),
                "frequency": getattr(item, "frequency", None),
                "review_status": item.review_status,
                "comparison_review_reason": getattr(item, "comparison_review_reason", None),
                "requires_immediate_review": getattr(item, "requires_immediate_review", False),
                "is_critical_reaction": getattr(item, "is_critical_reaction", False),
            }
            for item in blocking_recon_items
        ]
        raise HTTPException(
            status_code=400,
            detail={
                "code": "RECON_PENDING",
                "message": (
                    "Cannot finalize visit until all pending medication reconciliation "
                    "items have been reviewed."
                ),
                "count": len(blocking_payload),
                "blocking_items": blocking_payload,
            },
        )
    completed_task_types: list[str] = []
    try:
        visit.status = "FINALIZED"
        if hasattr(visit, "finalized_at"):
            visit.finalized_at = now
        if hasattr(visit, "finalized_by"):
            visit.finalized_by = user_id
        if hasattr(visit, "updated_at"):
            visit.updated_at = now
        db.flush()
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="FINALIZE_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "form_type": form_type,
                "discipline": discipline,
                "clinical_note_count": len(notes),
                "admission_id": str(visit.admission_id),
            },
        )
        logger.info(
            "CLINICAL_REASONING_GATE_CHECK "
            "visit_id=%s visit_type=%s discipline=%s "
            "runs_clinical_reasoning=%s note_count=%s request_id=%s",
            str(visit.id),
            visit_type,
            discipline,
            runs_clinical_reasoning,
            len(notes),
            request_id,
        )
        if runs_clinical_reasoning:
            logger.info(
                "FINALIZE: BEFORE_CLINICAL_REASONING visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )
            _run_clinical_reasoning_for_visit(
                db=db,
                visit=visit,
                notes=notes,
                request_id=request_id,
            )
            logger.info(
                "FINALIZE: AFTER_CLINICAL_REASONING visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )
        logger.info(
            "FINALIZE: BEFORE_POC_POLICY visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy
        on_visit_finalized_apply_poc_policy(
            db=db,
            visit=visit,
            patient=patient,
            finalized_by_user_id=user_id,
        )
        auto_complete_tasks_for_visit(
            db=db,
            visit=visit,
            user_id=user_id,
        )
        completed_task_types = _complete_initial_task_for_visit(
            db=db,
            visit=visit,
        )
        _run_condition_detection_non_blocking(
            db=db,
            visit=visit,
            patient=patient,
            user_id=user_id,
            now=now,
            request_id=request_id,
        )
        _run_bereavement_aggregation_non_blocking(
            db=db,
            visit=visit,
            patient=patient,
            user_id=user_id,
            request_id=request_id,
        )
        _run_phase_b_finalize_hooks(
            db=db,
            visit=visit,
            completed_task_types=completed_task_types,
            notes=notes,
            request_id=request_id,
        )
        db.commit()
        logger.info(
            "FINALIZE: SUCCESS visit_id=%s request_id=%s completed_task_types=%s",
            str(visit.id),
            request_id,
            completed_task_types,
        )
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        logger.exception(
            "FINALIZE: VALUE_ERROR_ROLLBACK visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        db.rollback()
        logger.exception(
            "FINALIZE: FAILED_ROLLBACK visit_id=%s patient_id=%s request_id=%s",
            str(visit.id),
            str(visit.patient_id),
            request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit finalization failed: {exc}",
        )
    return VisitMutationResponse(
        status="finalized",
        visit_id=str(visit.id),
        request_id=request_id,
        completed_task_types=completed_task_types,
    )
# =========================================================
# Pydantic model rebuild (REQUIRED FOR FASTAPI + V2)
# =========================================================VisitStatusUpdate.model_rebuild()VisitCreateRequest.model_rebuild()RefusalRequest.model_rebuild()VisitMutationResponse.model_rebuild()VisitReopenRequest.model_rebuild()VisitCreateResponse.model_rebuild()RefusalResponse.model_rebuild()