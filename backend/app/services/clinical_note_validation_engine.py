# app/services/clinical_note_validation_engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.models.incident_report import IncidentReport


# =========================================================
# CONSTANTS
# =========================================================

NOTE_STATUS_DRAFT = "DRAFT"
NOTE_STATUS_SIGNED = "SIGNED"

INCIDENT_STATUS_NONE = "NONE"
INCIDENT_STATUS_PENDING = "PENDING"
INCIDENT_STATUS_COMPLETED = "COMPLETED"
INCIDENT_STATUS_WAIVED = "WAIVED"

INCIDENT_TYPE_FALL = "FALL"
INCIDENT_TYPE_ADVERSE_REACTION = "ADVERSE_REACTION"
INCIDENT_TYPE_SENTINEL_EVENT = "SENTINEL_EVENT"
INCIDENT_TYPE_OTHER = "OTHER"

INCIDENT_SEVERITY_STANDARD = "STANDARD"
INCIDENT_SEVERITY_SIGNIFICANT = "SIGNIFICANT"
INCIDENT_SEVERITY_SENTINEL = "SENTINEL"

DISCIPLINES_ALLOWED = {"RN", "LVN", "MSW", "SC", "HHA", "CHHA", "MD", "NP"}
CARE_LEVELS_ALLOWED = {"RC", "CC", "GIP", "RSP"}
ENCOUNTER_TYPES_ALLOWED = {"COMPREHENSIVE", "ROUTINE", "PRN", "IDG", "DISCIPLINE"}

REQUIRED_FULL_ROS_SECTIONS = {
    "neurological",
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "genitourinary",
    "musculoskeletal",
    "integumentary",
    "psychosocial",
    "spiritual",
}

REQUIRED_FOCUSED_ROS_SECTIONS = {
    "pain",
    "respiratory",
    "gastrointestinal",
    "neuro_behavior",
    "skin",
    "genitourinary",
}


# =========================================================
# RESULT DTO
# =========================================================

@dataclass
class ValidationResult:
    warnings: list[str]
    red_flags: list[str]
    audit_flags: list[str]
    needs_clarification: list[str]
    incident_required: bool
    incident_status: str
    incident_id: UUID | None


# =========================================================
# PUBLIC ENGINE
# =========================================================

def validate_and_trigger_incident(
    db: Session,
    *,
    note: ClinicalNote,
    actor_user_id: UUID | None,
    actor_role: str = "SYSTEM_ENGINE",
) -> ValidationResult:
    """
    Non-blocking validation + incident auto-trigger engine.

    Behavior:
    - Reads observed_data, patient_reported, caregiver_reported, assessment,
      interventions, plan_of_care_updates
    - Writes warnings to note.red_flags / note.audit_flags / note.needs_clarification
    - Auto-creates incident_reports placeholder when incident criteria are met
    - Does NOT block signing; it surfaces issues and marks incident workflow pending
    """
    warnings: list[str] = []
    red_flags: list[str] = []
    audit_flags: list[str] = []
    needs_clarification: list[str] = []

    observed = _obj(note.observed_data)
    patient_reported = _obj(note.patient_reported)
    caregiver_reported = _obj(note.caregiver_reported)
    assessment = _obj(note.assessment)
    interventions = _obj(note.interventions)
    _ = _obj(note.plan_of_care_updates)

    _validate_core_classification(note, warnings, red_flags)
    _validate_truth_layers(observed, patient_reported, caregiver_reported, needs_clarification)
    _validate_required_ros(note, observed, assessment, warnings, audit_flags)
    _validate_symptom_interventions(observed, interventions, warnings)
    _validate_discipline_specific(note, observed, assessment, warnings)

    incident_decision = _detect_incident(
        note=note,
        observed=observed,
        patient_reported=patient_reported,
        caregiver_reported=caregiver_reported,
        assessment=assessment,
        interventions=interventions,
        warnings=warnings,
        red_flags=red_flags,
        needs_clarification=needs_clarification,
    )

    incident_id: UUID | None = None
    incident_status = INCIDENT_STATUS_NONE

    if incident_decision["required"]:
        incident_id = _ensure_incident_report(
            db=db,
            note=note,
            actor_user_id=actor_user_id,
            incident_type=incident_decision["incident_type"],
            incident_severity=incident_decision["incident_severity"],
            observed=observed,
            patient_reported=patient_reported,
            caregiver_reported=caregiver_reported,
            assessment=assessment,
            interventions=interventions,
        )
        incident_status = INCIDENT_STATUS_PENDING
        audit_flags.append(f"incident_triggered:{incident_decision['incident_type']}")

    note.needs_clarification = _merge_json_list(note.needs_clarification, needs_clarification)
    note.red_flags = _merge_json_list(note.red_flags, red_flags)
    note.audit_flags = _merge_json_list(note.audit_flags, audit_flags)
    note.incident_required = incident_decision["required"]
    note.incident_status = incident_status

    if incident_id and hasattr(note, "incident_id"):
        note.incident_id = incident_id

    _write_audit_log(
        db=db,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action="CLINICAL_NOTE_VALIDATED",
        entity_type="clinical_note",
        entity_id=note.id,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return ValidationResult(
        warnings=warnings,
        red_flags=red_flags,
        audit_flags=audit_flags,
        needs_clarification=needs_clarification,
        incident_required=incident_decision["required"],
        incident_status=incident_status,
        incident_id=incident_id,
    )


# =========================================================
# VALIDATION RULES
# =========================================================

def _validate_core_classification(note: ClinicalNote, warnings: list[str], red_flags: list[str]) -> None:
    if note.care_level not in CARE_LEVELS_ALLOWED:
        red_flags.append(f"invalid_care_level:{note.care_level}")

    if note.encounter_type not in ENCOUNTER_TYPES_ALLOWED:
        red_flags.append(f"invalid_encounter_type:{note.encounter_type}")

    if note.discipline not in DISCIPLINES_ALLOWED:
        red_flags.append(f"invalid_discipline:{note.discipline}")

    if note.visit_type in {"PRN", "CRISIS"} and note.visit_origin == "SCHEDULED":
        warnings.append("visit_type suggests unscheduled workflow but visit_origin is scheduled")


def _validate_truth_layers(
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    needs_clarification: list[str],
) -> None:
    if observed and not isinstance(observed, dict):
        needs_clarification.append("observed_data must be structured json object")

    if patient_reported and not isinstance(patient_reported, dict):
        needs_clarification.append("patient_reported must be structured json object")

    if caregiver_reported and not isinstance(caregiver_reported, dict):
        needs_clarification.append("caregiver_reported must be structured json object")


def _validate_required_ros(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
) -> None:
    ros = _obj(observed.get("review_of_systems") or assessment.get("review_of_systems"))

    if note.encounter_type == "COMPREHENSIVE":
        missing = sorted(section for section in REQUIRED_FULL_ROS_SECTIONS if section not in ros)
        if missing:
            warnings.append(f"comprehensive_missing_ros:{', '.join(missing)}")
            audit_flags.append("full_ros_incomplete")

    elif note.encounter_type in {"ROUTINE", "PRN"}:
        present = {section for section in REQUIRED_FOCUSED_ROS_SECTIONS if section in ros}
        if not present:
            warnings.append("routine_or_prn_note_missing_focused_ros")
            audit_flags.append("focused_ros_missing")


def _validate_symptom_interventions(
    observed: dict[str, Any],
    interventions: dict[str, Any],
    warnings: list[str],
) -> None:
    pain = _obj(observed.get("pain"))
    respiratory = _obj(observed.get("respiratory"))
    skin = _obj(observed.get("skin"))

    if _truthy(pain.get("pain_present")) or _numeric(pain.get("severity")) > 0:
        if not interventions.get("pain"):
            warnings.append("pain_present_without_documented_intervention")

    dyspnea_level = str(respiratory.get("dyspnea_level") or "").upper()
    if dyspnea_level in {"MODERATE", "SEVERE"} and not interventions.get("respiratory"):
        warnings.append("moderate_or_severe_dyspnea_without_intervention")

    if _truthy(skin.get("skin_tear")) and not interventions.get("skin"):
        warnings.append("skin_tear_documented_without_skin_intervention")


def _validate_discipline_specific(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
) -> None:
    if note.discipline in {"MSW", "SC"}:
        baseline_ref = assessment.get("rn_baseline_reference_id")
        if note.encounter_type == "COMPREHENSIVE" and not baseline_ref:
            warnings.append("msw_sc_comprehensive_note_missing_rn_baseline_reference")

    if note.discipline in {"HHA", "CHHA"}:
        adls = _obj(observed.get("adls"))
        if not adls:
            warnings.append("hha_note_missing_adl_observation")

    if note.discipline in {"MD", "NP"} and note.visit_type == "F2F":
        if not assessment.get("eligibility_justification"):
            warnings.append("f2f_note_missing_eligibility_justification")


# =========================================================
# INCIDENT DETECTION
# =========================================================

def _detect_incident(
    *,
    note: ClinicalNote,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
    warnings: list[str],
    red_flags: list[str],
    needs_clarification: list[str],
) -> dict[str, Any]:
    incident_required = False
    incident_type = INCIDENT_TYPE_OTHER
    incident_severity = INCIDENT_SEVERITY_STANDARD

    fall_reported = _truthy(caregiver_reported.get("fall_reported")) or _truthy(patient_reported.get("fall_reported"))
    fall_observed = _truthy(observed.get("fall")) or _truthy(_obj(observed.get("incident")).get("fall"))

    skin = _obj(observed.get("skin"))
    injury = _obj(observed.get("injury"))
    med_event = _obj(observed.get("medication_event"))
    disposition = _obj(assessment.get("disposition"))

    skin_tear = _truthy(skin.get("skin_tear")) or _truthy(injury.get("skin_tear"))
    bruise = _truthy(injury.get("bruise")) or _truthy(skin.get("bruising"))
    laceration = _truthy(injury.get("laceration"))
    fracture = _truthy(injury.get("fracture"))
    hospitalization_required = _truthy(injury.get("hospitalization_required")) or _truthy(
        disposition.get("hospitalization_required")
    )

    if fall_reported or fall_observed:
        incident_required = True
        incident_type = INCIDENT_TYPE_FALL

    if skin_tear or bruise or laceration or fracture:
        incident_required = True
        if incident_type != INCIDENT_TYPE_FALL:
            incident_type = INCIDENT_TYPE_OTHER

    if _truthy(med_event.get("adverse_reaction")):
        incident_required = True
        incident_type = INCIDENT_TYPE_ADVERSE_REACTION

    if hospitalization_required:
        incident_required = True
        incident_severity = INCIDENT_SEVERITY_SENTINEL
        if incident_type == INCIDENT_TYPE_OTHER:
            incident_type = INCIDENT_TYPE_SENTINEL_EVENT

    if any([skin_tear, laceration, fracture]) and incident_severity == INCIDENT_SEVERITY_STANDARD:
        incident_severity = INCIDENT_SEVERITY_SIGNIFICANT

    caregiver_no_injury = str(caregiver_reported.get("reported_injury") or "").strip().lower() in {
        "none",
        "no",
        "no injury",
    }
    injury_observed = any([skin_tear, bruise, laceration, fracture])

    if caregiver_no_injury and injury_observed:
        red_flags.append("reported_no_injury_but_clinician_observed_injury")
        needs_clarification.append("family/facility report of no injury differs from clinician findings")
        incident_required = True
        if incident_type == INCIDENT_TYPE_OTHER and (fall_reported or fall_observed):
            incident_type = INCIDENT_TYPE_FALL

    if incident_required and note.note_category == "MISSED_VISIT":
        warnings.append("incident flagged on note that appears to be a missed visit; review workflow context")

    return {
        "required": incident_required,
        "incident_type": incident_type,
        "incident_severity": incident_severity,
    }


# =========================================================
# INCIDENT PLACEHOLDER CREATION
# =========================================================

def _ensure_incident_report(
    db: Session,
    *,
    note: ClinicalNote,
    actor_user_id: UUID | None,
    incident_type: str,
    incident_severity: str,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
) -> UUID | None:
    existing = (
        db.query(IncidentReport)
        .filter(
            IncidentReport.tenant_id == note.tenant_id,
            IncidentReport.patient_id == note.patient_id,
            IncidentReport.clinical_note_id == note.id,
            IncidentReport.incident_type == incident_type,
        )
        .first()
    )
    if existing:
        return existing.id

    reported_by = _coerce_report_party(caregiver_reported) or _coerce_report_party(patient_reported)
    witnessed_by = _coerce_witness_party(caregiver_reported)
    place = _coerce_place(observed, assessment)
    area = _coerce_area(observed, assessment)
    surface = _coerce_surface(observed, assessment)
    medication_used = _coerce_medication_used(observed)
    activity_at_time = _coerce_activity(observed, caregiver_reported)
    injury_level = _coerce_injury_level(observed, assessment)
    injury_type = _coerce_injury_type(observed)
    other_injury_text = _coerce_other_injury_text(observed)
    narrative = _build_incident_narrative(note, observed, patient_reported, caregiver_reported)

    incident = IncidentReport(
        tenant_id=note.tenant_id,
        patient_id=note.patient_id,
        clinical_note_id=note.id,
        incident_type=incident_type,
        incident_severity=incident_severity,
        incident_date=note.encounter_date,
        reported_date=note.encounter_date,
        incident_time=getattr(note, "encounter_time", None),
        reported_by=reported_by,
        witnessed_by=witnessed_by,
        place=place,
        area=area,
        surface=surface,
        medication_used=medication_used,
        activity_at_time=activity_at_time,
        injury_level=injury_level,
        injury_type=injury_type,
        other_injury_text=other_injury_text,
        narrative=narrative,
        entered_by=actor_user_id,
    )
    db.add(incident)
    db.flush()

    _write_audit_log(
        db=db,
        actor_user_id=actor_user_id,
        actor_role="SYSTEM_ENGINE",
        action="INCIDENT_AUTO_CREATED",
        entity_type="incident_report",
        entity_id=incident.id,
    )

    return incident.id


# =========================================================
# AUDIT LOGGING (BEST EFFORT)
# =========================================================

def _write_audit_log(
    db: Session,
    *,
    actor_user_id: UUID | None,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
) -> None:
    if entity_id is None or actor_user_id is None:
        return

    try:
        db.execute(
            text(
                """
                INSERT INTO public.audit_logs (
                    id,
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    role,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :user_id,
                    :action,
                    :entity_type,
                    :entity_id,
                    :role,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "user_id": actor_user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "role": actor_role,
            },
        )
    except SQLAlchemyError:
        db.rollback()


# =========================================================
# HELPERS
# =========================================================

def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _merge_json_list(existing: Any, additions: list[str]) -> list[str]:
    base = existing if isinstance(existing, list) else []
    merged = list(dict.fromkeys([str(x) for x in base + additions if x]))
    return merged


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "y", "1", "present", "required"}
    return False


def _numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _coerce_report_party(data: dict[str, Any]) -> str | None:
    reported_by = str(data.get("reported_by") or "").strip().upper()
    if reported_by in {
        "PATIENT",
        "PCG",
        "SPOUSE_PARTNER",
        "CHILD",
        "RELATIVE",
        "FRIEND",
        "FACILITY_STAFF",
        "OTHER",
    }:
        return reported_by

    facility_hint = str(data.get("source") or data.get("facility_report") or "").strip().lower()
    if facility_hint:
        return "FACILITY_STAFF"

    return None


def _coerce_witness_party(data: dict[str, Any]) -> str | None:
    witnessed = str(data.get("witnessed_by") or "").strip().upper()
    if witnessed in {
        "NOT_WITNESSED",
        "STAFF",
        "PCG",
        "SPOUSE_PARTNER",
        "CHILD",
        "RELATIVE",
        "FRIEND",
        "FACILITY_STAFF",
        "OTHER",
    }:
        return witnessed

    if _truthy(data.get("unwitnessed")):
        return "NOT_WITNESSED"

    return None


def _coerce_place(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    place = str((observed.get("incident") or {}).get("place") or assessment.get("place") or "").strip().upper()
    return place if place in {"POS", "OTHER"} else None


def _coerce_area(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    area = str((observed.get("incident") or {}).get("area") or assessment.get("area") or "").strip().upper()
    approved = {"PT_ROOM_BEDROOM", "HALLWAY", "BATHROOM", "STEPS", "KITCHEN", "OTHER"}
    return area if area in approved else None


def _coerce_surface(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    surface = str((observed.get("incident") or {}).get("surface") or assessment.get("surface") or "").strip().upper()
    approved = {"CARPET", "RUNNER", "THROW_AWAY_RUG", "SLAB", "WOOD", "OTHER"}
    return surface if surface in approved else None


def _coerce_medication_used(observed: dict[str, Any]) -> str | None:
    med_used = str(_obj(observed.get("medication_event")).get("medication_used") or "").strip().upper()
    approved = {"NONE", "ANALGESIC", "SEDATIVE", "OPIATE", "OTHER"}
    return med_used if med_used in approved else None


def _coerce_activity(observed: dict[str, Any], caregiver_reported: dict[str, Any]) -> str | None:
    activity = str(
        _obj(observed.get("incident")).get("activity_at_time")
        or caregiver_reported.get("activity_at_time")
        or ""
    ).strip().upper()
    approved = {
        "REACHING_CHAIR_TO_BED",
        "REACHING_BED_TO_CHAIR",
        "AMBULATING",
        "TOILETING",
        "TRANSFERRING",
        "SITTING",
        "OTHER",
    }
    return activity if activity in approved else None


def _coerce_injury_level(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    injury = _obj(observed.get("injury"))
    if _truthy(injury.get("hospitalization_required")) or _truthy(_obj(assessment.get("disposition")).get("hospitalization_required")):
        return "HOSPITALIZATION_REQUIRED"
    if _truthy(injury.get("fracture")) or _truthy(injury.get("laceration")) or _truthy(injury.get("skin_tear")):
        return "MODERATE_INJURY"
    if _truthy(injury.get("bruise")):
        return "MINOR_INJURY"
    if injury:
        return "NO_INJURY"
    return None


def _coerce_injury_type(observed: dict[str, Any]) -> str | None:
    injury = _obj(observed.get("injury"))
    skin = _obj(observed.get("skin"))

    if _truthy(skin.get("skin_tear")) or _truthy(injury.get("skin_tear")):
        return "SKIN_TEAR"
    if _truthy(injury.get("laceration")):
        return "LACERATION"
    if _truthy(injury.get("bruise")) or _truthy(skin.get("bruising")):
        return "BRUISE"
    if _truthy(injury.get("fracture")):
        return "FRACTURE"
    if injury:
        return "OTHER"
    return None


def _coerce_other_injury_text(observed: dict[str, Any]) -> str | None:
    injury = _obj(observed.get("injury"))
    txt = str(injury.get("other_injury_text") or "").strip()
    return txt or None


def _build_incident_narrative(
    note: ClinicalNote,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
) -> str:
    pieces: list[str] = []

    if caregiver_reported:
        pieces.append(f"Caregiver/facility reported: {caregiver_reported}")

    if patient_reported:
        pieces.append(f"Patient reported: {patient_reported}")

    if observed:
        incident_obs = _obj(observed.get("incident"))
        injury_obs = _obj(observed.get("injury"))
        skin_obs = _obj(observed.get("skin"))
        pieces.append(
            f"Clinician observed: incident={incident_obs}, injury={injury_obs}, skin={skin_obs}"
        )

    pieces.append(f"Generated from clinical note {note.id}")
    return " | ".join(pieces)