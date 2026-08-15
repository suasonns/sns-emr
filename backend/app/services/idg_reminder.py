# services/idg_reminder.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.models.idg_review import IDGReview
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.services.audit_logger import log_event


IDG_LOOKBACK_DAYS = 15


def _build_patient_name(
    first_name: str | None,
    middle_name: str | None,
    last_name: str | None,
) -> str:
    parts = []
    for value in [first_name, middle_name, last_name]:
        if value is not None:
            cleaned = str(value).strip()
            if cleaned:
                parts.append(cleaned)

    if not parts:
        return "IDENTITY_MISSING"

    return " ".join(parts)


def get_idg_reminders(
    db: Session,
    *,
    tenant_id: UUID,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """
    Production-grade IDG reminder generator.

    Triggers reminders when:
    - No IDG review exists
    - IDG review not finalized
    - Missing POC linkage
    - Review is older than the configured lookback window

    Rules:
    - Tenant-scoped
    - Structured patient identity only (PatientFaceSheet)
    - Audit-logged
    - Avoids N+1 review queries
    """

    actor_tenant_id = getattr(user, "tenant_id", None)
    if actor_tenant_id is None:
        raise HTTPException(status_code=403, detail="Missing tenant context")

    if UUID(str(actor_tenant_id)) != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=IDG_LOOKBACK_DAYS)

    # ---------------------------------------------------------
    # Patients + structured identity
    # ---------------------------------------------------------
    patient_rows = (
        db.query(
            Patient.id.label("patient_id"),
            Patient.tenant_id.label("tenant_id"),
            Patient.status.label("status"),
            PatientFaceSheet.first_name.label("first_name"),
            PatientFaceSheet.middle_name.label("middle_name"),
            PatientFaceSheet.last_name.label("last_name"),
        )
        .outerjoin(
            PatientFaceSheet,
            PatientFaceSheet.patient_id == Patient.id,
        )
        .filter(
            Patient.tenant_id == tenant_id,
            Patient.status == "ACTIVE",
        )
        .all()
    )

    # ---------------------------------------------------------
    # Latest IDG review per patient (bulk-load)
    # ---------------------------------------------------------
    review_rows = (
        db.query(
            IDGReview.patient_id.label("patient_id"),
            IDGReview.review_date.label("review_date"),
            IDGReview.is_finalized.label("is_finalized"),
            IDGReview.plan_of_care_version_id.label("plan_of_care_version_id"),
        )
        .filter(IDGReview.tenant_id == tenant_id)
        .order_by(
            IDGReview.patient_id.asc(),
            IDGReview.review_date.desc().nullslast(),
        )
        .all()
    )

    latest_reviews: dict[UUID, Any] = {}
    for row in review_rows:
        if row.patient_id not in latest_reviews:
            latest_reviews[row.patient_id] = row

    reminders: list[dict[str, Any]] = []

    for patient in patient_rows:
        review = latest_reviews.get(patient.patient_id)

        reason: str | None = None

        if review is None:
            reason = "NO_IDG_REVIEW"
        elif not review.is_finalized:
            reason = "NOT_FINALIZED"
        elif not review.plan_of_care_version_id:
            reason = "NO_POC_LINK"
        elif review.review_date is not None and review.review_date < cutoff:
            reason = "OUTDATED"

        if reason:
            reminders.append(
                {
                    "patient_id": str(patient.patient_id),
                    "patient_name": _build_patient_name(
                        patient.first_name,
                        patient.middle_name,
                        patient.last_name,
                    ),
                    "last_review": review.review_date if review else None,
                    "reason": reason,
                }
            )

    # ---------------------------------------------------------
    # Priority ordering
    # ---------------------------------------------------------
    priority = {
        "NO_IDG_REVIEW": 1,
        "OUTDATED": 2,
        "NOT_FINALIZED": 3,
        "NO_POC_LINK": 4,
    }

    reminders.sort(
        key=lambda item: (
            priority.get(item["reason"], 99),
            item["patient_name"],
        )
    )

    # ---------------------------------------------------------
    # Audit logging
    # ---------------------------------------------------------
    user_id = getattr(user, "user_id", None)
    user_role = getattr(user, "role", None)

    if user_id and user_role:
        log_event(
            user_id=str(user_id),
            role=str(user_role),
            action="GENERATE_IDG_REMINDERS",
            entity_type="idg_reminder",
            entity_id=None,
            metadata={
                "tenant_id": str(tenant_id),
                "lookback_days": IDG_LOOKBACK_DAYS,
                "reminder_count": len(reminders),
            },
        )

    return reminders