# FILE: patient_assignment_service.py

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient_assignment import PatientAssignment
from app.models.enums import Discipline

logger = logging.getLogger("sns_emr")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_primary_rn(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: UUID,
    assigned_by: Optional[UUID] = None,
) -> PatientAssignment:
    """
    Ensures ONLY ONE active primary RN per patient.
    """

    # ✅ SIMPLE INPUT GUARD (NEW)
    if not tenant_id or not patient_id or not user_id:
        raise ValueError("tenant_id, patient_id, and user_id are required")

    try:
        now = _utcnow()

        # =====================================================
        # STEP 1: Lock + remove existing primary RN flag
        # =====================================================
        existing_primary = (
            db.query(PatientAssignment)
            .filter(
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.patient_id == patient_id,
                PatientAssignment.discipline == Discipline.RN,
                PatientAssignment.active.is_(True),
                PatientAssignment.is_primary.is_(True),
            )
            .with_for_update()
            .all()
        )

        for assignment in existing_primary:
            assignment.is_primary = False

            if hasattr(assignment, "updated_at"):
                assignment.updated_at = now
            if hasattr(assignment, "updated_by"):
                assignment.updated_by = assigned_by

        # =====================================================
        # STEP 2: Check if RN assignment already exists
        # =====================================================
        existing_assignment = (
            db.query(PatientAssignment)
            .filter(
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.patient_id == patient_id,
                PatientAssignment.user_id == user_id,
                PatientAssignment.discipline == Discipline.RN,
            )
            .with_for_update()
            .first()
        )

        if existing_assignment:
            existing_assignment.is_primary = True
            existing_assignment.active = True
            existing_assignment.status = "ASSIGNED"

            if hasattr(existing_assignment, "updated_at"):
                existing_assignment.updated_at = now
            if hasattr(existing_assignment, "updated_by"):
                existing_assignment.updated_by = assigned_by

            result = existing_assignment

        else:
            # =====================================================
            # STEP 3: Create new assignment
            # =====================================================
            new_assignment = PatientAssignment(
                tenant_id=tenant_id,
                patient_id=patient_id,
                user_id=user_id,
                discipline=Discipline.RN,
                is_primary=True,
                active=True,
                status="ASSIGNED",
                assigned_by=assigned_by,
            )

            if hasattr(new_assignment, "created_at"):
                new_assignment.created_at = now
            if hasattr(new_assignment, "updated_at"):
                new_assignment.updated_at = now
            if hasattr(new_assignment, "updated_by"):
                new_assignment.updated_by = assigned_by

            db.add(new_assignment)
            db.flush()

            result = new_assignment

        db.commit()
        db.refresh(result)

        logger.info(
            "PRIMARY_RN_SET tenant_id=%s patient_id=%s user_id=%s assignment_id=%s",
            str(tenant_id),
            str(patient_id),
            str(user_id),
            str(getattr(result, "id", None)),
        )

        return result

    except Exception:
        db.rollback()
        logger.exception(
            "PRIMARY_RN_SET_FAILED tenant_id=%s patient_id=%s user_id=%s",
            str(tenant_id),
            str(patient_id),
            str(user_id),
        )
        raise