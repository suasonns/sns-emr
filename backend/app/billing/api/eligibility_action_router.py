# backend/app/billing/api/eligibility_action_router.py
"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Phases A-E operational actions on top of Phases 1-7's
read-only foundation.

Everything here is additive to `eligibility_check_router.py` (which stays
read-only): this router is where an eligibility document actually gets
uploaded, a reverification actually gets recorded, an RN actually acts on
a benefit-period determination, and a biller actually escalates/annotates
a case -- each one auditable via the shared ReadinessWorkflowEvent trail
(Deliverable 9) and, where relevant, triggering a fresh billing-readiness
evaluation (Phase C -- "a reverification event must trigger downstream
evaluation, not silent storage").

Tenant scoping matches every other billing endpoint exactly:
resolve_billing_scope_tenant_id + require_automated_billing.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.billing.models.eligibility_source_document import (
    ELIGIBILITY_DOCUMENT_TYPES,
    EligibilitySourceDocument,
)
from app.billing.security import require_automated_billing
from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.services.eligibility_workflow_service import (
    RN_REVIEW_ACTIONS,
    apply_rn_review_action,
    evaluate_admission_gate,
    get_latest_eligibility_verification,
    record_eligibility_source_document,
    record_eligibility_verification,
    record_benefit_period_determination,
    record_eligibility_workflow_event,
)
from app.billing.services.readiness_workflow_service import upsert_follow_up
from app.billing.schemas.billing_schema import (
    AddBillingNoteRequest,
    BenefitPeriodDeterminationActionResponse,
    BillingImpactSummary,
    CreateBenefitPeriodDeterminationRequest,
    CreateEligibilityVerificationRequest,
    EligibilityActionAckResponse,
    EligibilityDocumentActionResponse,
    EligibilityVerificationActionResponse,
    EscalateEligibilityIssueRequest,
    RequestDocumentReviewRequest,
    RnReviewActionRequest,
)
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.document_record import DocumentRecord
from app.models.patient import Patient
from app.services.document_storage import (
    DocumentStorageConfigurationError,
    DocumentStorageError,
    DocumentUploadTooLarge,
    build_document_key,
    get_document_storage,
    max_upload_bytes_from_env,
    normalize_document_mime_type,
)

router = APIRouter(prefix="/billing", tags=["Billing Eligibility Actions"])

ESCALATION_ISSUE_TYPES = {"COVERAGE", "MSP", "MA"}


def _actor_id(user) -> str:
    return str(getattr(user, "user_id", None) or getattr(user, "id", ""))


def _parse_date(value: Optional[str], *, field_name: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {value}")


def _get_patient(db: Session, tenant_id: str, patient_id: str) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .one_or_none()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found for this tenant")
    return patient


def _patient_is_admitted(db: Session, tenant_id: str, patient_id: str) -> bool:
    from app.models.admission import Admission as _Admission

    return (
        db.query(_Admission)
        .filter(
            _Admission.tenant_id == tenant_id,
            _Admission.patient_id == patient_id,
            _Admission.status == "ADMITTED",
        )
        .first()
        is not None
    )


def _apply_billing_impact(db: Session, *, tenant_id: str, patient_id: str) -> BillingImpactSummary:
    """
    Phase C -- the eligibility change impact engine. Re-runs the
    admission gate immediately (always -- it's a cheap read), and, only
    for an ADMITTED patient (Phase 6 scope: billing readiness never
    evaluates referral/intake-hold/admission-hold records), triggers a
    real, persisted billing-readiness re-evaluation via the exact same
    `check_patient_billing_readiness` Sprint-1 entrypoint every other
    caller uses -- never a parallel/shortcut evaluation path.
    """
    gate = evaluate_admission_gate(db, tenant_id=tenant_id, patient_id=patient_id)

    if not _patient_is_admitted(db, tenant_id=tenant_id, patient_id=patient_id):
        return BillingImpactSummary(
            admission_gate_status=gate.gate_status,
            billing_readiness_reevaluated=False,
        )

    from app.billing.services.readiness_workflow_service import derive_readiness_status

    result = check_patient_billing_readiness(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        service_date=date.today(),
        triggered_by="ELIGIBILITY_CHANGE",
    )
    return BillingImpactSummary(
        admission_gate_status=gate.gate_status,
        billing_readiness_reevaluated=True,
        readiness_status=derive_readiness_status(
            blockers=result.blockers, warnings=result.warnings
        ),
        blockers=result.blockers,
        warnings=result.warnings,
    )


# =========================================================
# PHASE A -- DOCUMENT UPLOAD WORKFLOW
# =========================================================

@router.post(
    "/eligibility/{patient_id}/documents",
    response_model=EligibilityDocumentActionResponse,
)
async def upload_eligibility_document(
    patient_id: str,
    document_type: str = Form(...),
    payer_coverage_id: Optional[str] = Form(None),
    verification_date: Optional[str] = Form(None),
    service_date_from: Optional[str] = Form(None),
    service_date_to: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    supersedes_document_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    tenant_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    storage=Depends(get_document_storage),
):
    """
    Phase A. Uploads a new eligibility source document (or a new version
    superseding a prior one) -- reuses the exact same document-storage
    pipeline as `POST /documents/` (app.services.document_storage +
    app.models.document_record.DocumentRecord), just without the
    clinical-document AI-harvest step, which has no meaning for an
    eligibility response/portal PDF. Append-only: a supersession marks
    the prior EligibilitySourceDocument SUPERSEDED, never deletes it.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    if document_type not in ELIGIBILITY_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"document_type must be one of {sorted(ELIGIBILITY_DOCUMENT_TYPES)}",
        )

    if supersedes_document_id:
        prior_doc = (
            db.query(EligibilitySourceDocument)
            .filter(
                EligibilitySourceDocument.id == supersedes_document_id,
                EligibilitySourceDocument.tenant_id == scoped_tenant_id,
                EligibilitySourceDocument.patient_id == patient.id,
            )
            .one_or_none()
        )
        if prior_doc is None:
            raise HTTPException(
                status_code=404, detail="supersedes_document_id not found for this patient"
            )

    try:
        content_type = normalize_document_mime_type(file.content_type, filename=file.filename)
        max_upload_bytes = max_upload_bytes_from_env()
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except DocumentStorageConfigurationError as exc:
        raise HTTPException(status_code=500, detail="Document storage is misconfigured") from exc

    await file.seek(0)
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_upload_bytes:
            raise HTTPException(status_code=413, detail="Document exceeds maximum allowed size")
        chunks.append(chunk)
    raw_bytes = b"".join(chunks)
    if not raw_bytes:
        raise HTTPException(status_code=422, detail="Uploaded document was empty")

    document_id = uuid.uuid4()
    object_key = build_document_key(
        tenant_id=scoped_tenant_id,
        patient_id=str(patient.id),
        document_id=document_id,
        content_type=content_type,
    )

    try:
        size_bytes = await run_in_threadpool(
            storage.put,
            object_key,
            BytesIO(raw_bytes),
            content_type=content_type,
            max_bytes=max_upload_bytes,
        )
    except DocumentUploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail="Document storage operation failed") from exc

    doc_record = DocumentRecord(
        id=document_id,
        tenant_id=scoped_tenant_id,
        patient_id=patient.id,
        document_type=document_type,
        source="ELIGIBILITY",
        file_name=file.filename or f"{document_id}",
        file_path=object_key,
        content_hash=hashlib.sha256(raw_bytes).hexdigest(),
        uploaded_by=_actor_id(user),
        uploaded_at=datetime.now(timezone.utc),
        processing_status="COMPLETE",
    )
    db.add(doc_record)
    db.flush()

    try:
        source_doc = record_eligibility_source_document(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=str(patient.id),
            document_record_id=str(doc_record.id),
            document_type=document_type,
            uploaded_by_user_id=_actor_id(user),
            payer_coverage_id=payer_coverage_id,
            verification_date=_parse_date(verification_date, field_name="verification_date"),
            service_date_from=_parse_date(service_date_from, field_name="service_date_from"),
            service_date_to=_parse_date(service_date_to, field_name="service_date_to"),
            supersedes_document_id=supersedes_document_id,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="ELIGIBILITY_DOCUMENT",
        entity_id=str(source_doc.id),
        event_type="SUPERSEDED" if supersedes_document_id else "CREATED",
        actor_user_id=_actor_id(user),
        reason=notes,
        previous_value=(
            {"supersedes_document_id": supersedes_document_id} if supersedes_document_id else None
        ),
        new_value={
            "document_type": source_doc.document_type,
            "status": source_doc.status,
            "version": source_doc.version,
        },
    )
    db.commit()

    return EligibilityDocumentActionResponse(
        id=str(source_doc.id),
        patient_id=str(patient.id),
        document_type=source_doc.document_type,
        status=source_doc.status,
        version=source_doc.version,
        notes=source_doc.notes,
        document_record_id=str(source_doc.document_record_id),
        supersedes_document_id=(
            str(source_doc.supersedes_document_id) if source_doc.supersedes_document_id else None
        ),
        uploaded_at=source_doc.uploaded_at.isoformat(),
    )


# =========================================================
# PHASE B -- REVERIFICATION ACTION WORKFLOW
# =========================================================

@router.post(
    "/eligibility/{patient_id}/verifications",
    response_model=EligibilityVerificationActionResponse,
)
def create_eligibility_verification(
    patient_id: str,
    payload: CreateEligibilityVerificationRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Phase B. Records a new eligibility verification -- the FIRST
    verification for a patient, or a later reverification (never
    overwrites the prior row; record_eligibility_verification always
    appends and marks the prior superseded_at). Phase C then evaluates
    downstream impact immediately.
    """
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    prior = get_latest_eligibility_verification(
        db, tenant_id=scoped_tenant_id, patient_id=str(patient.id)
    )

    try:
        verification = record_eligibility_verification(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=str(patient.id),
            source_document_id=payload.source_document_id,
            verified_by_user_id=_actor_id(user),
            status=payload.status,
            payer_coverage_id=payload.payer_coverage_id,
            verification_date=_parse_date(payload.verification_date, field_name="verification_date"),
            verification_method=payload.verification_method,
            response_reference=payload.response_reference,
            effective_date=_parse_date(payload.effective_date, field_name="effective_date"),
            termination_date=_parse_date(payload.termination_date, field_name="termination_date"),
            entitlement_data=payload.entitlement_data,
            payment_routing_data=payload.payment_routing_data,
            hospice_utilization_data=payload.hospice_utilization_data,
            notes=payload.notes,
            coverage_change_flag=payload.coverage_change_flag,
            payer_change_flag=payload.payer_change_flag,
            msp_change_flag=payload.msp_change_flag,
            ma_change_flag=payload.ma_change_flag,
            overlap_concern_flag=payload.overlap_concern_flag,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="ELIGIBILITY_VERIFICATION",
        entity_id=str(verification.id),
        event_type="REVERIFIED" if prior is not None else "CREATED",
        actor_user_id=_actor_id(user),
        reason=payload.notes,
        previous_value={"status": prior.status} if prior is not None else None,
        new_value={
            "status": verification.status,
            "coverage_change_flag": verification.coverage_change_flag,
            "payer_change_flag": verification.payer_change_flag,
            "msp_change_flag": verification.msp_change_flag,
            "ma_change_flag": verification.ma_change_flag,
            "overlap_concern_flag": verification.overlap_concern_flag,
        },
    )
    db.commit()

    impact = _apply_billing_impact(db, tenant_id=scoped_tenant_id, patient_id=str(patient.id))

    return EligibilityVerificationActionResponse(
        id=str(verification.id),
        patient_id=str(patient.id),
        status=verification.status,
        verification_date=(
            verification.verification_date.isoformat() if verification.verification_date else None
        ),
        source_document_id=str(verification.source_document_id),
        notes=verification.notes,
        impact=impact,
    )


# =========================================================
# PHASE 3/D SUPPORT -- direct benefit-period determination creation
# (used by the biller/RN workspace for "update benefit period" outside
# the RN-review-action wrapper below, e.g. initial determination entry)
# =========================================================

@router.post(
    "/eligibility/{patient_id}/benefit-period-determinations",
    response_model=BenefitPeriodDeterminationActionResponse,
)
def create_benefit_period_determination(
    patient_id: str,
    payload: CreateBenefitPeriodDeterminationRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    try:
        determination = record_benefit_period_determination(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=str(patient.id),
            determination_status=payload.determination_status,
            admission_id=payload.admission_id,
            eligibility_verification_id=payload.eligibility_verification_id,
            source_document_id=payload.source_document_id,
            prior_hospice_episode_count=payload.prior_hospice_episode_count,
            benefit_periods_used=payload.benefit_periods_used,
            anticipated_benefit_period_number=payload.anticipated_benefit_period_number,
            anticipated_period_start_date=_parse_date(
                payload.anticipated_period_start_date, field_name="anticipated_period_start_date"
            ),
            anticipated_period_end_date=_parse_date(
                payload.anticipated_period_end_date, field_name="anticipated_period_end_date"
            ),
            face_to_face_applicability=payload.face_to_face_applicability,
            determined_by_user_id=_actor_id(user),
            review_notes=payload.review_notes,
            conflict_reason=payload.conflict_reason,
            supersedes_determination_id=payload.supersedes_determination_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="BENEFIT_PERIOD_DETERMINATION",
        entity_id=str(determination.id),
        event_type="CREATED",
        actor_user_id=_actor_id(user),
        reason=payload.review_notes,
        previous_value=(
            {"supersedes_determination_id": payload.supersedes_determination_id}
            if payload.supersedes_determination_id
            else None
        ),
        new_value={
            "determination_status": determination.determination_status,
            "anticipated_benefit_period_number": determination.anticipated_benefit_period_number,
        },
    )
    db.commit()

    impact = _apply_billing_impact(db, tenant_id=scoped_tenant_id, patient_id=str(patient.id))

    return BenefitPeriodDeterminationActionResponse(
        id=str(determination.id),
        patient_id=str(patient.id),
        determination_status=determination.determination_status,
        face_to_face_applicability=determination.face_to_face_applicability,
        anticipated_benefit_period_number=determination.anticipated_benefit_period_number,
        impact=impact,
    )


# =========================================================
# PHASE D -- RN REVIEW ACTIONS
# =========================================================

@router.post(
    "/eligibility/{patient_id}/rn-review-actions",
    response_model=BenefitPeriodDeterminationActionResponse,
)
def submit_rn_review_action(
    patient_id: str,
    payload: RnReviewActionRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Phase D. approve/reject/request-clarification/update-benefit-period/
    mark-F2F-required-or-not/place-or-release-admission-hold -- every
    action requires a reason (enforced in the service layer) and always
    creates a new, superseding BenefitPeriodDetermination row plus a
    ReadinessWorkflowEvent (both written by apply_rn_review_action).
    """
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    if payload.action not in RN_REVIEW_ACTIONS:
        raise HTTPException(
            status_code=400, detail=f"action must be one of {sorted(RN_REVIEW_ACTIONS)}"
        )

    try:
        determination = apply_rn_review_action(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=str(patient.id),
            action=payload.action,
            actor_user_id=_actor_id(user),
            reason=payload.reason,
            anticipated_benefit_period_number=payload.anticipated_benefit_period_number,
            anticipated_period_start_date=_parse_date(
                payload.anticipated_period_start_date, field_name="anticipated_period_start_date"
            ),
            anticipated_period_end_date=_parse_date(
                payload.anticipated_period_end_date, field_name="anticipated_period_end_date"
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    impact = _apply_billing_impact(db, tenant_id=scoped_tenant_id, patient_id=str(patient.id))

    return BenefitPeriodDeterminationActionResponse(
        id=str(determination.id),
        patient_id=str(patient.id),
        determination_status=determination.determination_status,
        face_to_face_applicability=determination.face_to_face_applicability,
        anticipated_benefit_period_number=determination.anticipated_benefit_period_number,
        impact=impact,
    )


# =========================================================
# PHASE E -- BILLER WORKSPACE ACTIONS
# (reverify-eligibility reuses the Phase B endpoint above; create-
# follow-up reuses the existing /billing/readiness-followups endpoint;
# track-resolution reuses the existing
# /billing/readiness-blockers/{id}/resolve endpoint -- neither is
# duplicated here, per the directive's own framing that biller actions
# should wire to what Phases 1-9 already built, not a new parallel
# mechanism.)
# =========================================================

@router.post(
    "/eligibility/{patient_id}/escalate",
    response_model=EligibilityActionAckResponse,
)
def escalate_eligibility_issue(
    patient_id: str,
    payload: EscalateEligibilityIssueRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    issue_type = payload.issue_type.upper().strip()
    if issue_type not in ESCALATION_ISSUE_TYPES:
        raise HTTPException(
            status_code=400, detail=f"issue_type must be one of {sorted(ESCALATION_ISSUE_TYPES)}"
        )

    # Escalation is operationally trackable, not just a log line -- it
    # opens/updates the same generic follow-up record the queue view and
    # dashboard already surface (Deliverable 5, reused, not duplicated).
    upsert_follow_up(
        db,
        tenant_id=scoped_tenant_id,
        patient_id=str(patient.id),
        actor_user_id=_actor_id(user),
        status="OPEN",
        follow_up_required=True,
        due_date=_parse_date(payload.due_date, field_name="due_date"),
        notes=f"ESCALATION[{issue_type}]: {payload.notes}",
        reason=payload.notes,
    )

    event = record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="BILLER_ESCALATION",
        entity_id=str(patient.id),
        event_type=f"ESCALATED_{issue_type}",
        actor_user_id=_actor_id(user),
        reason=payload.notes,
        new_value={"issue_type": issue_type, "notes": payload.notes},
    )
    db.commit()

    return EligibilityActionAckResponse(
        event_id=str(event.id), patient_id=str(patient.id), event_type=event.event_type
    )


@router.post(
    "/eligibility/{patient_id}/document-review-requests",
    response_model=EligibilityActionAckResponse,
)
def request_document_review(
    patient_id: str,
    payload: RequestDocumentReviewRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    source_doc = (
        db.query(EligibilitySourceDocument)
        .filter(
            EligibilitySourceDocument.id == payload.source_document_id,
            EligibilitySourceDocument.tenant_id == scoped_tenant_id,
            EligibilitySourceDocument.patient_id == patient.id,
        )
        .one_or_none()
    )
    if source_doc is None:
        raise HTTPException(status_code=404, detail="source_document_id not found for this patient")

    event = record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="ELIGIBILITY_DOCUMENT",
        entity_id=str(source_doc.id),
        event_type="REVIEW_REQUESTED",
        actor_user_id=_actor_id(user),
        reason=payload.notes,
        new_value={"document_type": source_doc.document_type},
    )
    db.commit()

    return EligibilityActionAckResponse(
        event_id=str(event.id), patient_id=str(patient.id), event_type=event.event_type
    )


@router.post(
    "/eligibility/{patient_id}/notes",
    response_model=EligibilityActionAckResponse,
)
def add_billing_note(
    patient_id: str,
    payload: AddBillingNoteRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)
    patient = _get_patient(db, scoped_tenant_id, patient_id)

    if not payload.note or not payload.note.strip():
        raise HTTPException(status_code=400, detail="note must not be empty")

    event = record_eligibility_workflow_event(
        db,
        tenant_id=scoped_tenant_id,
        entity_type="BILLER_NOTE",
        entity_id=str(patient.id),
        event_type="NOTE_ADDED",
        actor_user_id=_actor_id(user),
        reason=payload.note,
        new_value={"note": payload.note},
    )
    db.commit()

    return EligibilityActionAckResponse(
        event_id=str(event.id), patient_id=str(patient.id), event_type=event.event_type
    )
