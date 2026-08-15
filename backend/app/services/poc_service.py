from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc import POCProblem, POCGoal, POCIntervention
from app.models.poc_physician_approval import (
    PocPhysicianApproval,
    PocPhysicianApprovalAuditEvent,
)

logger = logging.getLogger("sns_emr")

USE_EXAMPLE_POC_FILE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXAMPLE_POC_PATH = os.path.join(BASE_DIR, "app", "examples", "poc_content_example.json")

PHYSICIAN_ATTESTATION_TEXT = """
I have reviewed the patient's clinical status,
hospice eligibility information, current problems,
goals, interventions, medications, and the Plan of Care.

I certify that the Plan of Care is appropriate for
the patient's current condition and hospice needs.

I approve this Plan of Care and authorize its
continued implementation and ongoing interdisciplinary
management.

Electronic signature or submission of a signed
approval document constitutes physician attestation
and approval of this Plan of Care version.
""".strip()

APPROVAL_RECORD_CREATED_EVENT_TYPE = "APPROVAL_RECORD_CREATED"
APPROVAL_RECORD_CREATED_DESCRIPTION = (
    "Physician approval record created for Plan of Care version."
)

ALLOWED_SOURCE_KINDS = {"ICA", "RN_UPDATE", "IDG_UPDATE", "SYSTEM"}
ALLOWED_DISCIPLINES = {"RN", "MSW", "SC", "LVN", "HHA", "MD", "IDG", "OTHER"}
ALLOWED_DIAGNOSIS_CONTEXTS = {
    "PRIMARY",
    "SECONDARY",
    "COMORBIDITY",
    "CONTRIBUTING_CONDITION",
    "MANUAL",
}
ALLOWED_PROBLEM_STATUSES = {"ACTIVE", "IMPROVING", "RESOLVED", "HISTORICAL", "SUPERSEDED"}
ALLOWED_GOAL_STATUSES = {"ACTIVE", "MET", "NOT_MET", "HISTORICAL", "SUPERSEDED"}
ALLOWED_INTERVENTION_STATUSES = {"ACTIVE", "COMPLETED", "CANCELED", "HISTORICAL", "SUPERSEDED"}


def _load_example_poc_content() -> dict[str, Any]:
    with open(EXAMPLE_POC_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("POC snapshot must be a dictionary")


def _validate_source_kind(source_kind: str) -> None:
    if source_kind not in ALLOWED_SOURCE_KINDS:
        raise ValueError(f"Invalid source_kind: {source_kind}")


def _get_patient_in_tenant(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
) -> Patient:
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id,
        )
        .first()
    )
    if not patient:
        raise ValueError("Patient not found in tenant")
    return patient


def _get_admission_for_patient_in_tenant(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: UUID,
) -> Admission:
    admission = (
        db.query(Admission)
        .filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id,
            Admission.patient_id == patient_id,
        )
        .first()
    )

    if not admission:
        raise ValueError(
            "Admission not found for this patient in this tenant"
        )

    return admission


def get_plan_of_care_by_admission(
    db: Session,
    *,
    tenant_id: UUID,
    admission_id: UUID,
) -> Optional[PlanOfCare]:
    return (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.tenant_id == tenant_id,
            PlanOfCare.admission_id == admission_id,
        )
        .first()
    )


def get_active_plan_of_care_version(
    db: Session,
    *,
    tenant_id: UUID,
    plan_of_care_id: UUID,
) -> Optional[PlanOfCareVersion]:
    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )

    if not poc:
        return None

    if poc.current_version_id:
        version = (
            db.query(PlanOfCareVersion)
            .filter(
                PlanOfCareVersion.id == poc.current_version_id,
                PlanOfCareVersion.tenant_id == tenant_id,
            )
            .first()
        )
        if version:
            return version

        logger.error(
            "POC_CURRENT_VERSION_POINTER_BROKEN tenant_id=%s plan_of_care_id=%s current_version_id=%s",
            str(tenant_id),
            str(plan_of_care_id),
            str(poc.current_version_id),
        )

    return (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.plan_of_care_id == plan_of_care_id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .order_by(PlanOfCareVersion.version_number.desc())
        .first()
    )


def get_current_plan_of_care_version_for_patient(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: Optional[UUID] = None,
) -> Optional[PlanOfCareVersion]:
    query = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.tenant_id == tenant_id,
            PlanOfCare.patient_id == patient_id,
        )
    )

    if admission_id is not None:
        query = query.filter(PlanOfCare.admission_id == admission_id)

    poc = query.order_by(PlanOfCare.created_at.desc()).first()
    if not poc:
        return None

    return get_active_plan_of_care_version(
        db,
        tenant_id=tenant_id,
        plan_of_care_id=poc.id,
    )


def create_plan_of_care(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: UUID,
    created_by_user_id: Optional[UUID],
    poc_content: dict[str, Any],
    source_kind: str = "ICA",
    change_reason: Optional[str] = "Initial POC creation",
    generated_from: Optional[dict[str, Any]] = None,
    create_physician_attestation: bool = False,
) -> PlanOfCare:
    """
    Create the PlanOfCare container and the first ACTIVE version.

    Enterprise behavior:
    - POC exists immediately.
    - Version 1 becomes ACTIVE and is linked as current_version_id.
    - Structured rows are materialized from snapshot_json when present.
    - Physician attestation remains a separate optional artifact.
    - Admission ownership is validated before POC creation.
    """
    if USE_EXAMPLE_POC_FILE:
        poc_content = _load_example_poc_content()

    _validate_snapshot(poc_content)
    _validate_source_kind(source_kind)

    try:
        now = _utcnow()

        _get_patient_in_tenant(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

        _get_admission_for_patient_in_tenant(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            admission_id=admission_id,
        )

        existing_poc = (
            db.query(PlanOfCare)
            .filter(
                PlanOfCare.tenant_id == tenant_id,
                PlanOfCare.admission_id == admission_id,
            )
            .with_for_update()
            .first()
        )
        if existing_poc:
            raise ValueError(
                "Plan of Care already exists for this admission in this tenant"
            )

        poc = PlanOfCare(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            admission_id=admission_id,
            status="ACTIVE",
            current_version_id=None,
            created_at=now,
            created_by_user_id=created_by_user_id,
            updated_at=now,
            updated_by_user_id=created_by_user_id,
        )
        db.add(poc)
        db.flush()

        version = PlanOfCareVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_of_care_id=poc.id,
            version_number=1,
            based_on_version_id=None,
            status="ACTIVE",
            source_kind=source_kind,
            change_reason=change_reason,
            generated_from=generated_from,
            reviewed_in_idg=False,
            idg_review_id=None,
            snapshot_json=poc_content,
            created_at=now,
            created_by_user_id=created_by_user_id,
            updated_at=now,
            updated_by_user_id=created_by_user_id,
        )
        db.add(version)
        db.flush()

        _materialize_version_structure(
            db=db,
            tenant_id=tenant_id,
            version=version,
            snapshot=poc_content,
            user_id=created_by_user_id,
        )

        poc.current_version_id = version.id
        poc.updated_at = now
        poc.updated_by_user_id = created_by_user_id

        if create_physician_attestation:
            _create_physician_attestation_record(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                poc_version_id=version.id,
                created_by_user_id=created_by_user_id,
            )

        db.commit()
        db.refresh(poc)

        logger.info(
            "POC_CREATED tenant_id=%s patient_id=%s admission_id=%s poc_id=%s version_id=%s",
            str(tenant_id),
            str(patient_id),
            str(admission_id),
            str(poc.id),
            str(version.id),
        )

        return poc

    except Exception:
        db.rollback()
        logger.exception(
            "POC_CREATE_FAILED tenant_id=%s patient_id=%s admission_id=%s",
            str(tenant_id),
            str(patient_id),
            str(admission_id),
        )
        raise


def create_new_version(
    db: Session,
    *,
    plan_of_care_id: UUID,
    tenant_id: UUID,
    updated_content: dict[str, Any],
    user_id: Optional[UUID],
    source_kind: str,
    change_reason: Optional[str] = None,
    generated_from: Optional[dict[str, Any]] = None,
    reviewed_in_idg: bool = False,
    idg_review_id: Optional[UUID] = None,
    create_physician_attestation: bool = False,
) -> PlanOfCareVersion:
    """
    Create a new ACTIVE version and supersede the current one.
    """
    _validate_snapshot(updated_content)
    _validate_source_kind(source_kind)

    try:
        now = _utcnow()

        plan_of_care = (
            db.query(PlanOfCare)
            .filter(
                PlanOfCare.id == plan_of_care_id,
                PlanOfCare.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )
        if not plan_of_care:
            raise ValueError("Plan of Care not found in tenant")

        _get_patient_in_tenant(
            db,
            tenant_id=tenant_id,
            patient_id=plan_of_care.patient_id,
        )

        current_version = (
            db.query(PlanOfCareVersion)
            .filter(
                PlanOfCareVersion.plan_of_care_id == plan_of_care.id,
                PlanOfCareVersion.tenant_id == tenant_id,
            )
            .order_by(PlanOfCareVersion.version_number.desc())
            .with_for_update()
            .first()
        )
        if not current_version:
            raise ValueError("Current version not found")

        if current_version.status == "ACTIVE":
            current_version.status = "SUPERSEDED"
            current_version.updated_at = now
            current_version.updated_by_user_id = user_id

        new_version = PlanOfCareVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_of_care_id=plan_of_care.id,
            version_number=current_version.version_number + 1,
            based_on_version_id=current_version.id,
            status="ACTIVE",
            source_kind=source_kind,
            change_reason=change_reason,
            generated_from=generated_from,
            reviewed_in_idg=reviewed_in_idg,
            idg_review_id=idg_review_id,
            snapshot_json=updated_content,
            created_at=now,
            created_by_user_id=user_id,
            updated_at=now,
            updated_by_user_id=user_id,
        )
        db.add(new_version)
        db.flush()

        _materialize_version_structure(
            db=db,
            tenant_id=tenant_id,
            version=new_version,
            snapshot=updated_content,
            user_id=user_id,
        )

        plan_of_care.current_version_id = new_version.id
        plan_of_care.status = "ACTIVE"
        plan_of_care.updated_at = now
        plan_of_care.updated_by_user_id = user_id

        if create_physician_attestation:
            _create_physician_attestation_record(
                db=db,
                tenant_id=tenant_id,
                patient_id=plan_of_care.patient_id,
                poc_version_id=new_version.id,
                created_by_user_id=user_id,
            )

        db.commit()
        db.refresh(new_version)

        logger.info(
            "POC_VERSION_CREATED tenant_id=%s plan_of_care_id=%s version_id=%s version_number=%s source_kind=%s",
            str(tenant_id),
            str(plan_of_care_id),
            str(new_version.id),
            str(new_version.version_number),
            source_kind,
        )

        return new_version

    except Exception:
        db.rollback()
        logger.exception(
            "POC_NEW_VERSION_FAILED tenant_id=%s plan_of_care_id=%s",
            str(tenant_id),
            str(plan_of_care_id),
        )
        raise


def finalize_plan_of_care_version(
    db: Session,
    *,
    tenant_id: UUID,
    version_id: UUID,
    user_id: Optional[UUID],
) -> PlanOfCareVersion:
    """
    Finalize a specific version.

    Note:
    - This is version lifecycle finalization only.
    - It is NOT physician approval gating.
    """
    try:
        now = _utcnow()

        version = (
            db.query(PlanOfCareVersion)
            .filter(
                PlanOfCareVersion.id == version_id,
                PlanOfCareVersion.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )
        if not version:
            raise ValueError("Version not found in tenant")

        version.status = "FINALIZED"
        version.updated_at = now
        version.updated_by_user_id = user_id

        db.commit()
        db.refresh(version)

        logger.info(
            "POC_VERSION_FINALIZED tenant_id=%s version_id=%s",
            str(tenant_id),
            str(version_id),
        )

        return version

    except Exception:
        db.rollback()
        logger.exception(
            "POC_VERSION_FINALIZE_FAILED tenant_id=%s version_id=%s",
            str(tenant_id),
            str(version_id),
        )
        raise


def _materialize_version_structure(
    db: Session,
    *,
    tenant_id: UUID,
    version: PlanOfCareVersion,
    snapshot: dict[str, Any],
    user_id: Optional[UUID],
) -> None:
    """
    Materialize snapshot_json into first-class clinical rows.
    """
    if not isinstance(snapshot, dict):
        raise ValueError("POC snapshot must be a dictionary")

    problems_payload = snapshot.get("problems")
    if not problems_payload:
        logger.warning(
            "POC_STRUCTURE_NOT_MATERIALIZED tenant_id=%s version_id=%s reason=no_problems_in_snapshot",
            str(tenant_id),
            str(version.id),
        )
        return

    if not isinstance(problems_payload, list):
        raise ValueError("POC snapshot problems must be a list")

    logger.info(
        "POC_STRUCTURE_PROCESSING tenant_id=%s version_id=%s problem_count=%s",
        str(tenant_id),
        str(version.id),
        str(len(problems_payload)),
    )

    now = _utcnow()

    for p_index, raw_problem in enumerate(problems_payload, start=1):
        if not isinstance(raw_problem, dict):
            raise ValueError("Each problem entry must be a dictionary")

        diagnosis_context = str(raw_problem.get("diagnosis_context", "MANUAL")).upper()
        if diagnosis_context not in ALLOWED_DIAGNOSIS_CONTEXTS:
            diagnosis_context = "MANUAL"

        severity = str(raw_problem.get("severity", "UNKNOWN")).upper()
        if severity not in {"LOW", "MODERATE", "HIGH", "CRITICAL", "UNKNOWN"}:
            severity = "UNKNOWN"

        problem_status = str(raw_problem.get("status", "ACTIVE")).upper()
        if problem_status not in ALLOWED_PROBLEM_STATUSES:
            problem_status = "ACTIVE"

        problem_source_kind = str(raw_problem.get("source_kind", "RULE_GENERATED")).upper()
        if problem_source_kind not in {
            "RULE_GENERATED",
            "MANUAL",
            "RN_UPDATE",
            "IDG_UPDATE",
            "SYSTEM",
        }:
            problem_source_kind = "RULE_GENERATED"

        problem_code = raw_problem.get("problem_code") or raw_problem.get("code")
        label = raw_problem.get("label")

        if not problem_code:
            raise ValueError("Problem missing problem_code/code")
        if not label:
            raise ValueError("Problem missing label")

        problem = POCProblem(
            id=uuid4(),
            tenant_id=tenant_id,
            poc_version_id=version.id,
            source_diagnosis_code=raw_problem.get("source_diagnosis_code"),
            source_condition=raw_problem.get("source_condition"),
            diagnosis_context=diagnosis_context,
            rule_key=raw_problem.get("rule_key"),
            problem_code=str(problem_code),
            label=str(label),
            description=raw_problem.get("description"),
            severity=severity,
            source_kind=problem_source_kind,
            is_rule_generated=(problem_source_kind == "RULE_GENERATED"),
            status=problem_status,
            sort_order=int(raw_problem.get("sort_order", p_index * 100)),
            created_at=now,
            created_by_user_id=user_id,
            updated_at=now,
            updated_by_user_id=user_id,
        )
        db.add(problem)
        db.flush()

        goals_payload = raw_problem.get("goals", [])
        if not isinstance(goals_payload, list):
            raise ValueError("Problem goals must be a list")

        for g_index, raw_goal in enumerate(goals_payload, start=1):
            if isinstance(raw_goal, str):
                raw_goal = {"goal_text": raw_goal}

            if not isinstance(raw_goal, dict):
                raise ValueError("Each goal entry must be a string or dictionary")

            goal_text = raw_goal.get("goal_text") or raw_goal.get("text")
            if not goal_text:
                raise ValueError("Goal missing goal_text/text")

            goal_status = str(raw_goal.get("status", "ACTIVE")).upper()
            if goal_status not in ALLOWED_GOAL_STATUSES:
                goal_status = "ACTIVE"

            goal_source_kind = str(raw_goal.get("source_kind", "RULE_GENERATED")).upper()
            if goal_source_kind not in {
                "RULE_GENERATED",
                "MANUAL",
                "RN_UPDATE",
                "IDG_UPDATE",
                "SYSTEM",
            }:
                goal_source_kind = "RULE_GENERATED"

            goal = POCGoal(
                id=uuid4(),
                tenant_id=tenant_id,
                problem_id=problem.id,
                goal_text=str(goal_text),
                measurable_outcome=raw_goal.get("measurable_outcome"),
                target_timeframe=raw_goal.get("target_timeframe"),
                source_kind=goal_source_kind,
                is_rule_generated=(goal_source_kind == "RULE_GENERATED"),
                status=goal_status,
                sort_order=int(raw_goal.get("sort_order", g_index * 100)),
                created_at=now,
                created_by_user_id=user_id,
                updated_at=now,
                updated_by_user_id=user_id,
            )
            db.add(goal)
            db.flush()

            interventions_payload = raw_goal.get("interventions", [])
            if not isinstance(interventions_payload, list):
                raise ValueError("Goal interventions must be a list")

            for i_index, raw_intervention in enumerate(interventions_payload, start=1):
                if not isinstance(raw_intervention, dict):
                    raise ValueError("Each intervention entry must be a dictionary")

                discipline = str(raw_intervention.get("discipline", "OTHER")).upper()
                if discipline not in ALLOWED_DISCIPLINES:
                    discipline = "OTHER"

                intervention_text = raw_intervention.get("intervention_text") or raw_intervention.get("text")
                if not intervention_text:
                    raise ValueError("Intervention missing intervention_text/text")

                intervention_status = str(raw_intervention.get("status", "ACTIVE")).upper()
                if intervention_status not in ALLOWED_INTERVENTION_STATUSES:
                    intervention_status = "ACTIVE"

                intervention_source_kind = str(raw_intervention.get("source_kind", "RULE_GENERATED")).upper()
                if intervention_source_kind not in {
                    "RULE_GENERATED",
                    "MANUAL",
                    "RN_UPDATE",
                    "IDG_UPDATE",
                    "SYSTEM",
                }:
                    intervention_source_kind = "RULE_GENERATED"

                intervention = POCIntervention(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    goal_id=goal.id,
                    discipline=discipline,
                    intervention_text=str(intervention_text),
                    frequency=raw_intervention.get("frequency"),
                    instructions=raw_intervention.get("instructions"),
                    source_kind=intervention_source_kind,
                    is_rule_generated=(intervention_source_kind == "RULE_GENERATED"),
                    status=intervention_status,
                    sort_order=int(raw_intervention.get("sort_order", i_index * 100)),
                    created_at=now,
                    created_by_user_id=user_id,
                    updated_at=now,
                    updated_by_user_id=user_id,
                )
                db.add(intervention)
                db.flush()

    db.flush()


def _create_physician_attestation_record(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    poc_version_id: UUID,
    created_by_user_id: Optional[UUID],
) -> PocPhysicianApproval:
    """
    Separate physician attestation workflow artifact.

    This does NOT determine whether the POC version exists.
    It only creates a pending physician attestation record.
    """
    approval = PocPhysicianApproval(
        tenant_id=tenant_id,
        patient_id=patient_id,
        poc_version_id=poc_version_id,
        physician_name="PENDING",
        physician_role="ATTENDING_PHYSICIAN",
        approval_method="ELECTRONIC_SIGNATURE",
        approval_status="PENDING_PHYSICIAN_SIGNATURE",
        attestation_text=PHYSICIAN_ATTESTATION_TEXT,
        created_by_user_id=created_by_user_id,
    )
    db.add(approval)
    db.flush()

    audit = PocPhysicianApprovalAuditEvent(
        tenant_id=tenant_id,
        poc_physician_approval_id=approval.id,
        patient_id=patient_id,
        poc_version_id=poc_version_id,
        event_type=APPROVAL_RECORD_CREATED_EVENT_TYPE,
        event_description=APPROVAL_RECORD_CREATED_DESCRIPTION,
        performed_by_user_id=created_by_user_id,
    )
    db.add(audit)
    db.flush()

    logger.info(
        "POC_PHYSICIAN_ATTESTATION_CREATED tenant_id=%s patient_id=%s poc_version_id=%s",
        str(tenant_id),
        str(patient_id),
        str(poc_version_id),
    )

    return approval