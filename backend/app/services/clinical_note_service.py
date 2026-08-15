# backend/app/services/clinical_note_service.py

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.domain.forms.form_resolution_service import resolve_form_package
from app.domain.tasks.task_form_rules import TASK_REQUIRED_FORMS
from app.models.clinical_note import ClinicalNote
from app.models.med_reconciliation import MedReconciliationItem
from app.models.task import Task
from app.models.visit import Visit
from app.services.workflow_resolver import resolve_workflow
from app.services.workflow_validation import validate_timepoint_safe
from app.services.clinical_note_validation_engine import (
    validate_and_trigger_incident,
)
from app.services.idg_completeness import validate_idg_completeness
from app.services.poc_engine import generate_poc_suggestions
from app.services.poc_review_gate import enforce_poc_review_gate
from app.services.task_auto_complete_engine import auto_complete_tasks_from_note
from app.services.task_engine import process_tasks_for_note
from app.domain.clinical.rn_ica_keys import (
    RN_ICA_ACCEPTED_KEYS,
    RN_ICA_CANONICAL_FORM_KEY,
    RN_ICA_CANONICAL_NOTE_TYPE,
    RN_ICA_DISPLAY_NAME,
    is_rn_ica_key,
    normalize_rn_ica_content,
    normalize_rn_ica_key,
)

logger = logging.getLogger("sns_emr")


# =========================================================
# TIME HELPERS
# =========================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


# =========================================================
# INTERNAL — REQUIRED FORM VALIDATION FOR TASKS
# =========================================================

def _normalize_task_type(value: Any) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value)).strip().upper()


def _validate_required_forms_for_tasks(db: Session, note: ClinicalNote) -> None:
    """
    Ensure required forms exist for active tasks relevant to this note.

    Behavior:
    - Prefer note-linked tasks when clinical_note_id exists
    - Otherwise fall back to active patient tasks
    - Validate required forms against the note's visit scope
    """
    visit_id = getattr(note, "visit_id", None)
    patient_id = getattr(note, "patient_id", None)

    if not visit_id or not patient_id:
        return

    task_query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.status.in_(["PENDING", "OVERDUE", "IN_PROGRESS"]))
    )

    if hasattr(Task, "clinical_note_id"):
        note_linked_tasks = task_query.filter(Task.clinical_note_id == note.id).all()
        tasks = note_linked_tasks if note_linked_tasks else task_query.all()
    else:
        tasks = task_query.all()

    if not tasks:
        return

    existing_notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.visit_id == visit_id)
        .all()
    )
    existing_form_keys = {
        n.form_key for n in existing_notes if getattr(n, "form_key", None)
    }

    violations: list[dict[str, str]] = []

    for task in tasks:
        task_type = _normalize_task_type(getattr(task, "task_type", None))
        required_forms = TASK_REQUIRED_FORMS.get(task_type, set())

        for required_form in required_forms:
            if required_form not in existing_form_keys:
                violations.append(
                    {
                        "task_type": task_type,
                        "missing_form": str(required_form),
                    }
                )

    if violations:
        raise ValueError(
            f"Missing required forms before task completion: {violations}"
        )


# =========================================================
# INTERNAL — CONTENT JSON HELPERS
# =========================================================

def _ensure_content_dict(note: ClinicalNote) -> None:
    if not isinstance(note.content, dict):
        note.content = {}

    flag_modified(note, "content")


def _ensure_observed_data(note: ClinicalNote) -> None:
    _ensure_content_dict(note)

    observed_data = note.content.get("observed_data")
    if not isinstance(observed_data, dict):
        observed_data = {}

    observed_data.setdefault("system", {})

    note.content["observed_data"] = observed_data
    flag_modified(note, "content")


def _ensure_audit_flags(note: ClinicalNote) -> None:
    _ensure_content_dict(note)

    audit_flags = note.content.get("audit_flags")
    if not isinstance(audit_flags, dict):
        audit_flags = {}

    note.content["audit_flags"] = audit_flags
    flag_modified(note, "content")
    
# =========================================================
# INTERNAL — ENSURE POC JSON ALWAYS EXISTS
# =========================================================

def _ensure_plan_of_care_updates(note: ClinicalNote) -> None:
    if isinstance(note.plan_of_care_updates, dict):
        return

    note.plan_of_care_updates = {
        "meta": {
            "version": "1.0",
            "generated_at": _utc_now_iso(),
            "note_id": str(note.id) if note.id else None,
            "patient_id": str(note.patient_id) if note.patient_id else None,
        },
        "pocs": [],
    }
    flag_modified(note, "plan_of_care_updates")


def _sync_plan_of_care_meta(note: ClinicalNote) -> None:
    if not isinstance(note.plan_of_care_updates, dict):
        note.plan_of_care_updates = {"meta": {}, "pocs": []}

    meta = note.plan_of_care_updates.get("meta", {}) or {}

    meta["version"] = meta.get("version") or "1.0"
    meta["generated_at"] = meta.get("generated_at") or _utc_now_iso()
    meta["note_id"] = str(note.id) if note.id else None
    meta["patient_id"] = str(note.patient_id) if note.patient_id else None

    note.plan_of_care_updates["meta"] = meta
    note.plan_of_care_updates.setdefault("pocs", [])

    flag_modified(note, "plan_of_care_updates")


# =========================================================
# TIMESTAMP SAFETY
# =========================================================

def _ensure_required_timestamps(note: ClinicalNote) -> None:
    """
    Ensure explicit timestamps exist for environments where ORM/server defaults
    may not populate before flush.
    """
    now = _utc_now()

    if getattr(note, "created_at", None) is None:
        note.created_at = now

    if getattr(note, "updated_at", None) is None:
        note.updated_at = now

    if getattr(note, "entered_at", None) is None:
        note.entered_at = now


# =========================================================
# CONTENT SAFETY (CRITICAL - PREVENT NOT NULL FAILURES)
# =========================================================

def _ensure_content(note: ClinicalNote) -> None:
    """
    Enforce NOT NULL and JSON-shape safety for clinical_notes.content.
    """
    if getattr(note, "content", None) is None:
        note.content = {}
        return

    if not isinstance(note.content, dict):
        note.content = {}


# =========================================================
# FORM ENGINE APPLICATION
# =========================================================

def _coerce_form_family_value(value: Any) -> Any:
    if value is None:
        return None
    return getattr(value, "value", value)


def _apply_form_engine(note: ClinicalNote, db: Session) -> dict[str, Any]:
    """
    Apply form resolution using visit-driven form_type.
    Production-safe, deterministic, audit-friendly.
    """
    visit = None
    if getattr(note, "visit_id", None):
        visit = db.query(Visit).filter(Visit.id == note.visit_id).first()

    resolved_form_type = getattr(visit, "form_type", None)

    logger.debug("FORM ENGINE EXECUTING")
    logger.debug("RAW DISCIPLINE: %r", note.discipline)
    logger.debug("RAW FORM TYPE: %r", resolved_form_type)

    if not resolved_form_type:
        raise ValueError("visit.form_type is required for form resolution")

    discipline_value = str(
        getattr(note.discipline, "value", note.discipline)
    ).strip().upper()
    
    # Visit engine already resolved the form type.
    # Do not re-resolve through ClinicalWorkflowMap.
    # ClinicalWorkflowMap is currently not populated and
    # ClinicalNote does not contain assessment_type.

    resolved_form_type = str(resolved_form_type).strip().upper()
    
    logger.debug(
        "FINAL INPUT: discipline=%r form_type=%r",
        getattr(note.discipline, "value", note.discipline),
        resolved_form_type,
    )

    form_package = resolve_form_package(
        discipline=discipline_value,
        form_type=resolved_form_type,
        level_of_care=getattr(note, "care_level", None),
        event_type=getattr(note, "event_type", None),
        care_setting=getattr(note, "care_setting", None),
    )

    note.form_family = _coerce_form_family_value(form_package.get("form_family"))
    note.form_key = form_package.get("primary_form")

    normalized_form_type = normalize_rn_ica_key(resolved_form_type)

    note.module_payload = {
        "modules": form_package.get("modules", []),
        "attached_forms": form_package.get("attached_forms", []),
        "resolved_by": form_package.get("resolved_by"),
        "form_type": normalized_form_type,
    }
    flag_modified(note, "module_payload")

    if getattr(note, "is_primary", None) is None:
        note.is_primary = True

    if note.is_primary:
        note.parent_note_id = None

    return form_package


def _build_clinical_context(form_package: dict[str, Any]) -> dict[str, Any]:
    """
    Centralized clinical intelligence layer.
    """
    return {
        "form_resolution": form_package,
        "generated_at": _utc_now_iso(),
    }


# =========================================================
# COMPLIANCE EVALUATION (SOFT ENFORCEMENT)
# =========================================================

def _evaluate_clinical_compliance(form_package: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate compliance from the resolved package.
    DO NOT BLOCK here — only flag issues.
    """
    loc = form_package.get("level_of_care")
    requirements = form_package.get("loc_requirements", {}) or {}

    issues: list[str] = []

    if requirements.get("requires_daily_rn_visit"):
        issues.append("RN_DAILY_VISIT_REQUIRED")

    if requirements.get("requires_md_review"):
        issues.append("MD_REVIEW_REQUIRED")

    if requirements.get("requires_daily_assessment"):
        issues.append("DAILY_ASSESSMENT_REQUIRED")

    return {
        "level_of_care": loc,
        "issues": issues,
        "status": "needs_review" if issues else "compliant",
    }


# =========================================================
# TASK SIGNAL GENERATOR (COMPLIANCE -> TASKS)
# =========================================================

def _generate_compliance_task_signals(
    compliance: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Convert compliance issues into task signals.
    """
    signals: list[dict[str, str]] = []

    issues = compliance.get("issues", []) or []
    loc = compliance.get("level_of_care")

    if "RN_DAILY_VISIT_REQUIRED" in issues:
        signals.append(
            {
                "task_type": "RN_DAILY_VISIT",
                "priority": "HIGH",
                "reason": f"{loc} requires daily RN visit",
            }
        )

    if "DAILY_ASSESSMENT_REQUIRED" in issues:
        signals.append(
            {
                "task_type": "DAILY_ASSESSMENT",
                "priority": "HIGH",
                "reason": f"{loc} requires daily assessment",
            }
        )

    if "MD_REVIEW_REQUIRED" in issues:
        signals.append(
            {
                "task_type": "MD_REVIEW",
                "priority": "HIGH",
                "reason": "GIP requires MD continuation review",
            }
        )

    return signals

# =========================================================
# RN ICA FINALIZATION COMPLIANCE GATE
# =========================================================

RN_ICA_FORM_KEYS = RN_ICA_ACCEPTED_KEYS


def _note_content_dict(note: ClinicalNote) -> dict[str, Any]:
    if isinstance(getattr(note, "content", None), dict):
        return note.content

    return {}


def _validation_from_note_or_result(
    note: ClinicalNote,
    validation_result: Any,
) -> dict[str, Any]:
    if validation_result is not None:
        result_blockers = getattr(
            validation_result,
            "compliance_blocking_items",
            None,
        )
        result_allowed = getattr(
            validation_result,
            "finalization_allowed",
            None,
        )

        if result_blockers is not None or result_allowed is not None:
            return {
                "finalization_allowed": (
                    True if result_allowed is None else bool(result_allowed)
                ),
                "compliance_blocking_items": result_blockers or [],
                "warnings": getattr(validation_result, "warnings", []),
                "red_flags": getattr(validation_result, "red_flags", []),
            }

    content = _note_content_dict(note)
    validation = content.get("_validation", {})

    if isinstance(validation, dict):
        return validation

    return {}


def _is_rn_ica_note(note: ClinicalNote) -> bool:
    discipline = str(
        getattr(note, "discipline", "") or ""
    ).strip().upper()

    if discipline != "RN":
        return False

    return (
        is_rn_ica_key(getattr(note, "note_type", None))
        or is_rn_ica_key(getattr(note, "form_key", None))
    )


def _extract_rn_ica_blockers(
    validation: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_items = validation.get("compliance_blocking_items", [])

    if not isinstance(raw_items, list):
        return []

    blockers: list[dict[str, Any]] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        compliance_type = str(
            item.get("compliance_type") or ""
        ).strip().upper()

        if compliance_type == "RN_ICA_REQUIRED":
            blockers.append(item)

    return blockers

def _raise_if_rn_ica_compliance_incomplete(
    note: ClinicalNote,
    validation_result: Any,
) -> None:
    """
    Hard-stop RN ICA finalization when RN_ICA_REQUIRED
    compliance blockers exist.

    Includes:

    - Review Of Systems
    - Functional Assessment
    - Future RN ICA required sections
    """

    if not _is_rn_ica_note(note):
        return

    validation = _validation_from_note_or_result(
        note=note,
        validation_result=validation_result,
    )

    blockers = _extract_rn_ica_blockers(validation)

    if not blockers:
        return

    raise HTTPException(
        status_code=400,
        detail={
            "code": "RN_ICA_INCOMPLETE",
            "message": (
                "RN ICA cannot be finalized because required "
                "clinical assessment sections are incomplete."
            ),
            "finalization_allowed": False,
            "blocking_scope": "RN_ICA_REQUIRED",
            "blocking_items": blockers,
            "required_action": (
                "Complete all required RN ICA assessment "
                "sections before finalizing."
            ),
        },
    )

# =========================================================
# ATTACHED FORM SYNC
# =========================================================

def _sync_attached_forms(
    db: Session,
    *,
    note: ClinicalNote,
    form_package: dict[str, Any],
) -> None:
    """
    Create missing attached child forms for the primary note.

    Safe / idempotent behavior:
    - only runs for primary notes
    - only creates child forms that do not already exist
    """
    if not getattr(note, "is_primary", False):
        return

    attached_forms = form_package.get("attached_forms", []) or []
    if not attached_forms:
        return

    existing_children = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.parent_note_id == note.id)
        .all()
    )
    existing_keys = {
        normalize_rn_ica_key(child.form_key)
        for child in existing_children
        if getattr(child, "form_key", None)
    }

    for child_form_key in attached_forms:
        normalized_child_form_key = normalize_rn_ica_key(child_form_key)

        if normalized_child_form_key in existing_keys:
            continue

        normalized_child_form_key = normalize_rn_ica_key(child_form_key)

        child_note = ClinicalNote(
            id=uuid.uuid4(),
            tenant_id=note.tenant_id,
            patient_id=note.patient_id,
            visit_id=note.visit_id,
            author_id=note.author_id,
            created_by=note.created_by,
            updated_by_user_id=note.author_id,
            discipline=note.discipline,
            note_type=normalized_child_form_key,
            content={},
            form_family=note.form_family,
            form_key=normalized_child_form_key,
            module_payload={"modules": []},
            is_primary=False,
            parent_note_id=note.id,
            status=note.status,
            encounter_date=note.encounter_date,
        )

        _ensure_required_timestamps(child_note)
        _ensure_content(child_note)
        db.add(child_note)

def _ensure_note_audit_identity(note: ClinicalNote, user_id: UUID) -> None:
    """
    Enforce audit identity fields for note authorship/update tracking.

    Rules:
    - author_id is the single source of truth for authorship
    - created_by is maintained only for legacy compatibility
    - updated_by_user_id tracks the last modifier
    """
    if not getattr(note, "author_id", None):
        note.author_id = user_id

    if not getattr(note, "created_by", None):
        note.created_by = user_id

    note.updated_by_user_id = user_id


def _capture_raw_transcript(note: ClinicalNote) -> None:
    """
    Preserve original AI/voice/scribe source text in raw_transcript when present.
    """
    if getattr(note, "raw_transcript", None):
        return

    if not isinstance(getattr(note, "content", None), dict):
        return

    content = note.content

    raw = (
        content.get("raw_transcript")
        or content.get("voice_transcript")
        or content.get("dictation")
        or content.get("transcript")
    )

    if raw is not None:
        note.raw_transcript = raw
        
def _canonicalize_rn_ica_identity(note: ClinicalNote) -> None:
    """
    Production canonicalization for RN ICA identity.

    Database/source-of-truth storage:
    - note_type = RN_ASSESS
    - form_key = RN_ASSESS
    - content.note_type = RN_ASSESS
    - content.form_key = RN_ASSESS
    - content.display_note_type = RN ICA

    Accepted inbound aliases:
    - RN_ICA
    - INITIAL_RN_ICA
    - RN_ASSESS
    - RN_ASSESS_V1
    - RN_HOPE_ADMISSION
    """
    discipline = str(
        getattr(note, "discipline", "") or ""
    ).strip().upper()

    if discipline != "RN":
        return

    note_type_is_rn_ica = is_rn_ica_key(getattr(note, "note_type", None))
    form_key_is_rn_ica = is_rn_ica_key(getattr(note, "form_key", None))

    content = getattr(note, "content", None)
    content_is_rn_ica = False

    if isinstance(content, dict):
        content_is_rn_ica = (
            is_rn_ica_key(content.get("note_type"))
            or is_rn_ica_key(content.get("form_key"))
            or str(content.get("display_note_type") or "").strip().upper() == "RN ICA"
        )

    if not (note_type_is_rn_ica or form_key_is_rn_ica or content_is_rn_ica):
        return

    note.note_type = RN_ICA_CANONICAL_NOTE_TYPE
    note.form_key = RN_ICA_CANONICAL_FORM_KEY

    if not isinstance(note.content, dict):
        note.content = {}

    note.content = normalize_rn_ica_content(note.content)
    note.content["note_type"] = RN_ICA_CANONICAL_NOTE_TYPE
    note.content["form_key"] = RN_ICA_CANONICAL_FORM_KEY
    note.content["display_note_type"] = RN_ICA_DISPLAY_NAME

    flag_modified(note, "content")

# =========================================================
# INTERNAL — NOTE ENRICHMENT PIPELINE
# =========================================================

def _prepare_note_common_state(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
) -> dict[str, Any]:

    _ensure_plan_of_care_updates(note)
    _ensure_required_timestamps(note)
    _ensure_content(note)
    _ensure_note_audit_identity(note, user_id)
    _capture_raw_transcript(note)
    _canonicalize_rn_ica_identity(note)

    # =========================================================
    # ✅ LOAD VISIT CONTEXT
    # =========================================================
    visit = None
    if getattr(note, "visit_id", None):
        visit = db.query(Visit).filter(Visit.id == note.visit_id).first()

    # =========================================================
    # ✅ CARE LEVEL SNAPSHOT (AUDIT SAFE)
    # =========================================================
    if visit and getattr(visit, "care_level", None):
        note.care_level_snapshot = visit.care_level

    form_package = _apply_form_engine(note, db)
    _canonicalize_rn_ica_identity(note)

    # ✅ TIMEPOINT VALIDATION (SAFE MODE)
    validation_result = validate_timepoint_safe(db, note)

    if validation_result and validation_result != "VALID":
        logger.warning(
            "TIMEPOINT_VALIDATION note_id=%s patient_id=%s result=%s",
            str(getattr(note, "id", None)),
            str(getattr(note, "patient_id", None)),
            validation_result,
        )

    clinical_context = _build_clinical_context(form_package)

    _ensure_observed_data(note)

    note.content["observed_data"]["system"]["clinical_context"] = (
        clinical_context
    )

    flag_modified(note, "content")

    compliance = _evaluate_clinical_compliance(form_package)
    compliance_payload = {
        **compliance,
        "evaluated_at": _utc_now_iso(),
        "version": "1.0",
    }

    _ensure_audit_flags(note)
    note.content["audit_flags"]["clinical_compliance"] = compliance_payload
    note.content["audit_flags"]["task_signals"] = (
        _generate_compliance_task_signals(compliance)
    )
    flag_modified(note, "content")

    return form_package


def _persist_note_and_children(
    db: Session,
    *,
    note: ClinicalNote,
    form_package: dict[str, Any],
    user_id: Any,
) -> None:
    """
    Persist the primary note first, then sync attached child forms.
    """
    _sync_plan_of_care_meta(note)
    db.add(note)
    db.flush()

    _sync_attached_forms(
        db,
        note=note,
        form_package=form_package,
    )
    db.flush()

    # =========================================================
    # ✅ RULE ENGINE (DRY RUN ONLY — SAFE FOR TESTING)
    # =========================================================
    from app.services.rules_dry_run import dry_run_rules
    from app.rules.base import RuleContext

    ctx = RuleContext(
        tenant_id=str(note.tenant_id) if note.tenant_id else None,
        patient_id=str(note.patient_id) if note.patient_id else None,
        document_id=str(note.id) if note.id else None,
        document_type="CLINICAL_NOTE",
        meta={
            "visit_id": str(note.visit_id) if note.visit_id else None,
            "note_id": str(note.id) if note.id else None,
        },
    )

    rule_report = dry_run_rules(ctx, db=db)

    _ensure_audit_flags(note)
    note.content["audit_flags"]["rule_engine"] = rule_report
    flag_modified(note, "content")

    logger.info(
        "RULE_ENGINE_RESULT note_id=%s summary=%s",
        str(note.id),
        rule_report["summary"],
    )

    # =========================================================
    # ✅ EXISTING FLOW CONTINUES (UNCHANGED)
    # =========================================================

    validation_result = validate_and_trigger_incident(
        db=db,
        note=note,
        actor_user_id=user_id,
        actor_role="CLINICIAN",
    )    

    _ensure_plan_of_care_updates(note)

    generated_pocs = generate_poc_suggestions(note)

    if generated_pocs:
        note.plan_of_care_updates["pocs"] = generated_pocs
    else:
        note.plan_of_care_updates.setdefault("pocs", [])

    flag_modified(note, "plan_of_care_updates")

    logger.info(
        "POC generated for clinical note note_id=%s patient_id=%s count=%s",
        str(note.id),
        str(note.patient_id),
        len(note.plan_of_care_updates.get("pocs", [])),
    )

    pocs = note.plan_of_care_updates.get("pocs", [])

    if pocs:
        logger.warning(
            "POC task generation skipped. "
            "Legacy process_pocs_to_tasks no longer exists and "
            "POC version architecture is required."
        )

    _sync_plan_of_care_meta(note)
    flag_modified(note, "plan_of_care_updates")

    db.add(note)
    db.flush()

    return validation_result


# =========================================================
# INTERNAL — VISIT / RECON HELPERS
# =========================================================

def _get_visit_required(db: Session, note: ClinicalNote) -> Visit:
    visit = db.query(Visit).filter(Visit.id == note.visit_id).first()
    if not visit:
        raise ValueError("Visit not found for clinical note")
    return visit


def _get_blocking_reconciliation_items(
    db: Session,
    *,
    patient_id: UUID,
) -> list[MedReconciliationItem]:
    return (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.patient_id == patient_id)
        .filter(MedReconciliationItem.review_status == "PENDING")
        .order_by(MedReconciliationItem.created_at.asc())
        .all()
    )


def _raise_if_reconciliation_pending(
    db: Session,
    *,
    visit: Visit,
) -> None:
    blocking_recon_items = _get_blocking_reconciliation_items(
        db,
        patient_id=visit.patient_id,
    )

    logger.info(
        "FINALIZE: RECON_CHECK visit_id=%s pending_items=%s N/A=%s",
        str(visit.id),
        len(blocking_recon_items),
        "N/A",
    )

    if not blocking_recon_items:
        return

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

    logger.warning(
        "FINALIZE: BLOCKED_RECON_PENDING visit_id=%s count=%s N/A=%s items=%s",
        str(visit.id),
        len(blocking_payload),
        "N/A",
        blocking_payload,
    )

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


def _raise_if_idg_incomplete(
    db: Session,
    *,
    note: ClinicalNote,
) -> None:
    if not getattr(note, "idg_review_id", None):
        return

    missing = validate_idg_completeness(
        db,
        idg_review_id=note.idg_review_id,
        tenant_id=note.tenant_id,
    )

    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "IDG_INCOMPLETE",
                "missing": missing,
            },
        )


# =========================================================
# SAVE DRAFT
# =========================================================

def save_clinical_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
) -> tuple[ClinicalNote, dict[str, Any]]:
    """
    Save a draft clinical note and run the standard note engines.
    """
    try:
        form_package = _prepare_note_common_state(
            db,
            note=note,
            user_id=user_id,
        )
        
        validation_result = _persist_note_and_children(
            db,
            note=note,
            form_package=form_package,
            user_id=user_id,
        )

        process_tasks_for_note(
            db=db,
            note=note,
            user_id=user_id,
        )
        
        # =========================================================
        # ✅ SAVE AUDIT SAFETY
        # =========================================================
        note.updated_by_user_id = user_id
        
        db.add(note)
        db.commit()
        db.refresh(note)

        return note, validation_result

    except Exception as e:
        db.rollback()
        logger.exception("Failed to save clinical note: %s", str(e))
        raise


# =========================================================
# FINALIZE SIGN
# =========================================================

def finalize_clinical_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
) -> tuple[ClinicalNote, dict[str, Any]]:
    """
    Finalize a clinical note with downstream enforcement and automation.

    Production safeguards:
    - rollback on failure
    - explicit return contract
    - persisted state before response
    """
    try:
        form_package = _prepare_note_common_state(
            db,
            note=note,
            user_id=user_id,
        )

        validation_result = _persist_note_and_children(
            db,
            note=note,
            form_package=form_package,
            user_id=user_id,
        )

        _raise_if_rn_ica_compliance_incomplete(
            note=note,
            validation_result=validation_result,
        )

        _raise_if_idg_incomplete(db, note=note)
        enforce_poc_review_gate(note)

        visit = _get_visit_required(db, note)
        _raise_if_reconciliation_pending(db, visit=visit)

        # First pass: create / update downstream tasks based on current note state
        process_tasks_for_note(
            db=db,
            note=note,
            user_id=user_id,
        )

        # Finalize note state
        note.finalize(user_id=user_id)

        # =========================================================
        # ✅ FINALIZE AUDIT SAFETY
        # =========================================================
        now = _utc_now()

        if not note.signed_by:
            note.signed_by = user_id

        if not note.signed_at:
            note.signed_at = now

        note.updated_by_user_id = user_id

        # Validate forms required for task completion before final commit
        _validate_required_forms_for_tasks(db, note)

        # Second pass: task transitions after finalized state
        process_tasks_for_note(
            db=db,
            note=note,
            user_id=user_id,
        )

        auto_complete_tasks_from_note(
            db=db,
            note=note,
            user_id=user_id,
        )
        
        db.add(note)
        db.commit()
        db.refresh(note)

        return note, validation_result

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to finalize clinical note note_id=%s patient_id=%s visit_id=%s",
            str(getattr(note, "id", None)) if getattr(note, "id", None) else None,
            str(getattr(note, "patient_id", None)) if getattr(note, "patient_id", None) else None,
            str(getattr(note, "visit_id", None)) if getattr(note, "visit_id", None) else None,
        )
        raise