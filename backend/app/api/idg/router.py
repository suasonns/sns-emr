# app/api/idg/router.py

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.db_request_dependency import get_db_tenant_with_request_state

from app.services.idg_engine import enforce_idg_readiness
from app.services import idg_physician_review_service as review_svc
from app.services import physician_order_service as order_svc
from app.services import idg_group_service as group_svc

router = APIRouter(prefix="/idg", tags=["IDG"])

# Any clinical role present at IDG (RN facilitator, MSW, chaplain, etc.)
# may record a physician's Reviewed/Deferred decision — this mirrors real
# practice where the physician participates verbally and the facilitator
# operates the screen. The physician of record is captured separately
# and reviewed_by_physician_directly is only set when the MD is the one
# actually logged in and clicking. Batch signing itself stays MD-only.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "Chaplain", "Surveyor"]
# "MD" is the legacy/live provider-discipline role; MEDICAL_DIRECTOR and
# ATTENDING_PHYSICIAN are the newer canonical prescriber roles used by the
# dashboard widget-visibility engine. Both are accepted so a real prescriber
# is recognized either way.
MD_ONLY = ["MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN"]
ADMIN_ROLES = ["ADMIN"]
# Everyone allowed to VIEW IDG rosters/PHI: clinical staff who actually
# attend/run IDG, plus agency admins. Deliberately excludes OWNER (the
# platform/vendor super-user account) and BILLER — neither has a clinical
# reason to see patient names, MRNs, or defer reasons here, and letting an
# authenticated-but-unauthorized role reach this data via direct URL/API
# call (bypassing only the nav) is a HIPAA minimum-necessary violation.
IDG_VIEW_ROLES = CLINICAL_ROLES + ADMIN_ROLES


class PatientReviewSet(BaseModel):
    review_status: str  # "PENDING" | "REVIEWED" | "DEFERRED"
    physician_user_id: UUID  # physician of record for this review
    defer_reason: Optional[str] = None
    defer_note: Optional[str] = None
    poc_reviewed: bool = False
    medication_list_reviewed: bool = False
    medication_reconciliation_reviewed: bool = False
    orders_reviewed: bool = False
    discussion_reviewed: bool = False
    notes: Optional[str] = None


class BatchSignRequest(BaseModel):
    patient_ids: Optional[list[UUID]] = None
    signature_method: str = "ELECTRONIC"


def _serialize_review(review) -> dict:
    return {
        "id": str(review.id),
        "patient_id": str(review.patient_id),
        "idg_meeting_id": str(review.idg_meeting_id),
        "physician_user_id": str(review.physician_user_id),
        "recorded_by_user_id": str(review.recorded_by_user_id) if review.recorded_by_user_id else None,
        "reviewed_by_physician_directly": review.reviewed_by_physician_directly,
        "review_source": review.review_source,
        "review_status": review.review_status,
        "defer_reason": review.defer_reason,
        "defer_note": review.defer_note,
        "poc_reviewed": review.poc_reviewed,
        "medication_list_reviewed": review.medication_list_reviewed,
        "medication_reconciliation_reviewed": review.medication_reconciliation_reviewed,
        "orders_reviewed": review.orders_reviewed,
        "discussion_reviewed": review.discussion_reviewed,
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
        "notes": review.notes,
        "batch_signed_at": review.batch_signed_at.isoformat() if review.batch_signed_at else None,
    }


# =========================================================
# ✅ IDG READINESS CHECK
# =========================================================

@router.get("/{patient_id}/check")
def check_idg_status(
    patient_id: UUID,
    current_user=Depends(require_roles(IDG_VIEW_ROLES)),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Check if patient is ready for IDG review.
    """
    get_authorized_patient(db, patient_id, current_user)

    result = enforce_idg_readiness(
        db=db,
        patient_id=patient_id,
        tenant_id=current_user.tenant_id,
    )

    return {
        "blocked": result.blocked,
        "reasons": result.reasons,
    }


# =========================================================
# ✅ IDG PHYSICIAN REVIEW WORKFLOW
# (Review Status gate -> Batch Signature Queue -> batch sign)
# =========================================================

@router.get(
    "/sessions",
    summary="Tenant-wide list of IDG meeting dates (Aug 19, 32 patients, ...)",
)
def list_idg_sessions(
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(IDG_VIEW_ROLES)),
):
    return review_svc.list_idg_meeting_dates(db, tenant_id=user.tenant_id)


@router.get(
    "/sessions/by-date/{meeting_date}",
    summary="All patients scheduled for IDG on a shared meeting_date, with review status",
)
def get_idg_session_patients(
    meeting_date: str,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(IDG_VIEW_ROLES)),
):
    try:
        parsed_date = datetime.fromisoformat(meeting_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="meeting_date must be an ISO-8601 timestamp")
    try:
        return review_svc.list_patients_for_meeting_date(
            db, tenant_id=user.tenant_id, meeting_date=parsed_date
        )
    except review_svc.IDGPhysicianReviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/sessions/{idg_meeting_id}/reviews",
    summary="List every patient's physician review status for this IDG session",
)
def list_session_reviews(
    idg_meeting_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(IDG_VIEW_ROLES)),
):
    try:
        reviews = review_svc.list_reviews_for_session(
            db, tenant_id=user.tenant_id, idg_meeting_id=idg_meeting_id
        )
    except review_svc.IDGPhysicianReviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [_serialize_review(r) for r in reviews]


@router.get(
    "/sessions/{idg_meeting_id}/patients/{patient_id}/review",
    summary="Get a patient's physician review status for this IDG session",
)
def get_patient_review(
    idg_meeting_id: UUID,
    patient_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(IDG_VIEW_ROLES)),
):
    get_authorized_patient(db, patient_id, user)
    review = review_svc.get_review(
        db, tenant_id=user.tenant_id, idg_meeting_id=idg_meeting_id, patient_id=patient_id
    )
    if not review:
        return None
    return _serialize_review(review)


@router.post(
    "/sessions/{idg_meeting_id}/patients/{patient_id}/review",
    summary="Record a patient's IDG physician review decision (Pending/Reviewed/Deferred)",
)
def set_patient_review(
    idg_meeting_id: UUID,
    patient_id: UUID,
    payload: PatientReviewSet,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    get_authorized_patient(db, patient_id, user)
    # Only True when the physician of record is themselves the one logged
    # in and submitting — never inferred from role alone, per the audit
    # trail honesty rule (facilitator-recorded vs. physician-direct).
    reviewed_by_physician_directly = (
        user.role == "MD" and str(user.user_id) == str(payload.physician_user_id)
    )
    try:
        review = review_svc.set_review_status(
            db,
            tenant_id=user.tenant_id,
            idg_meeting_id=idg_meeting_id,
            patient_id=patient_id,
            physician_user_id=payload.physician_user_id,
            recorded_by_user_id=user.user_id,
            reviewed_by_physician_directly=reviewed_by_physician_directly,
            review_status=payload.review_status,
            defer_reason=payload.defer_reason,
            defer_note=payload.defer_note,
            poc_reviewed=payload.poc_reviewed,
            medication_list_reviewed=payload.medication_list_reviewed,
            medication_reconciliation_reviewed=payload.medication_reconciliation_reviewed,
            orders_reviewed=payload.orders_reviewed,
            discussion_reviewed=payload.discussion_reviewed,
            notes=payload.notes,
        )
    except review_svc.IDGPhysicianReviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_review(review)


@router.get(
    "/sessions/{idg_meeting_id}/batch-signature-queue",
    summary="MD-only: eligible Reviewed patients with pending orders ready for batch signature",
)
def get_batch_signature_queue(
    idg_meeting_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(MD_ONLY)),
):
    try:
        queue = review_svc.get_batch_signature_queue(
            db, tenant_id=user.tenant_id, idg_meeting_id=idg_meeting_id
        )
    except review_svc.IDGPhysicianReviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return [
        {
            "patient_id": entry["patient_id"],
            "review_id": entry["review_id"],
            "reviewed_at": entry["reviewed_at"],
            "physician_user_id": entry["physician_user_id"],
            "orders": [
                {
                    "id": str(o.id),
                    "order_text": o.order_text,
                    "order_category": o.order_category,
                    "source_type": o.source_type,
                    "ordered_by_provider_name": o.ordered_by_provider_name,
                    "ordered_by_provider_role": o.ordered_by_provider_role,
                    "ordered_at": o.ordered_at.isoformat() if o.ordered_at else None,
                    "status": o.status,
                }
                for o in entry["orders"]
            ],
        }
        for entry in queue
    ]


@router.post(
    "/sessions/{idg_meeting_id}/batch-sign",
    summary="MD-only: apply individual electronic signatures to all eligible Reviewed patients' pending orders",
)
def batch_sign_orders(
    idg_meeting_id: UUID,
    payload: BatchSignRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    # allow_clinical_admin=False: batch signing is a real signature action.
    # Administrator/DPCS may monitor the queue (GET above) but must never
    # gain signing authority via the administrative-role fallback.
    user: CurrentUser = Depends(require_roles(MD_ONLY, allow_clinical_admin=False)),
):
    try:
        result = review_svc.batch_sign(
            db,
            tenant_id=user.tenant_id,
            idg_meeting_id=idg_meeting_id,
            physician_user_id=user.user_id,
            patient_ids=payload.patient_ids,
            signature_method=payload.signature_method,
        )
    except review_svc.IDGPhysicianReviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return result


# =====================================================================
# IDG Group management (scheduling cohorts) + automatic generation
#
# NOTE: IDGGroup / IDGGroupScheduleRule are scheduling-support entities,
# NOT one of the 3 IDG domain entities. They exist purely so the
# automatic meeting generator knows which patients meet on which days.
# =====================================================================


def _serialize_group(group) -> dict:
    return {
        "id": str(group.id),
        "name": group.name,
        "sort_order": group.sort_order,
        "is_active": group.is_active,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


def _serialize_rule(rule) -> dict:
    return {
        "id": str(rule.id),
        "idg_group_id": str(rule.idg_group_id),
        "weekday": rule.weekday,
        "nth_occurrences": rule.nth_occurrences,
        "is_active": rule.is_active,
    }


class GroupCreateRequest(BaseModel):
    name: str
    sort_order: int = 0


class GroupActiveRequest(BaseModel):
    is_active: bool


class ScheduleRuleCreateRequest(BaseModel):
    weekday: int
    nth_occurrences: Optional[list[int]] = None


class AssignPatientsRequest(BaseModel):
    patient_ids: list[UUID]


class AutoSplitRequest(BaseModel):
    group_ids: list[UUID]


@router.get("/groups", summary="List all IDG scheduling groups for this tenant")
def list_groups(
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    groups = group_svc.list_groups(db, tenant_id=user.tenant_id)
    return [_serialize_group(g) for g in groups]


@router.post("/groups", summary="Create a new IDG scheduling group")
def create_group(
    payload: GroupCreateRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        group = group_svc.create_group(
            db,
            tenant_id=user.tenant_id,
            name=payload.name,
            sort_order=payload.sort_order,
            created_by=user.user_id,
        )
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_group(group)


@router.patch("/groups/{group_id}/active", summary="Activate or deactivate an IDG group")
def set_group_active(
    group_id: UUID,
    payload: GroupActiveRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        group = group_svc.set_group_active(
            db, tenant_id=user.tenant_id, group_id=group_id, is_active=payload.is_active
        )
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _serialize_group(group)


@router.get("/groups/{group_id}/schedule-rules", summary="List cadence rules for a group")
def list_schedule_rules(
    group_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    rules = group_svc.list_rules_for_group(db, tenant_id=user.tenant_id, group_id=group_id)
    return [_serialize_rule(r) for r in rules]


@router.post("/groups/{group_id}/schedule-rules", summary="Add a cadence rule to a group")
def add_schedule_rule(
    group_id: UUID,
    payload: ScheduleRuleCreateRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        rule = group_svc.add_schedule_rule(
            db,
            tenant_id=user.tenant_id,
            group_id=group_id,
            weekday=payload.weekday,
            nth_occurrences=payload.nth_occurrences,
            created_by=user.user_id,
        )
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_rule(rule)


@router.delete("/groups/schedule-rules/{rule_id}", summary="Deactivate a cadence rule")
def deactivate_schedule_rule(
    rule_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        rule = group_svc.deactivate_schedule_rule(db, tenant_id=user.tenant_id, rule_id=rule_id)
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _serialize_rule(rule)


@router.post("/groups/{group_id}/patients", summary="Assign patients to an IDG group")
def assign_patients(
    group_id: UUID,
    payload: AssignPatientsRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        count = group_svc.assign_patients_to_group(
            db, tenant_id=user.tenant_id, group_id=group_id, patient_ids=payload.patient_ids
        )
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"assigned_count": count}


@router.post(
    "/groups/auto-split-unassigned",
    summary="Evenly distribute all unassigned active patients across the given groups by MR# (Odd/Even style split)",
)
def auto_split_unassigned(
    payload: AutoSplitRequest,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    try:
        result = group_svc.auto_split_unassigned_patients(
            db, tenant_id=user.tenant_id, group_ids=payload.group_ids
        )
    except group_svc.IDGGroupError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return result


@router.post(
    "/groups/run-automatic-generation",
    summary="Manually trigger the automatic IDG meeting generation job (normally runs on a schedule)",
)
def run_automatic_generation(
    horizon_days: int = 14,
    db: Session = Depends(get_db_tenant_with_request_state),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    result = group_svc.run_automatic_idg_generation(
        db, tenant_id=user.tenant_id, horizon_days=horizon_days, created_by=user.user_id
    )
    return result
