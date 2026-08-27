# FILE: patient_assignment_service.py

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, aliased

from app.core.roles import normalize_role
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.enums import Discipline

logger = logging.getLogger("sns_emr")

_DISCIPLINE_INPUT_ALIASES = {
    "HA": "CHHA",
    "HHA": "CHHA",
    "CASE_MANAGER_RN": "CASE_MANAGER",
    "CASE_MANAGER_LVN": "CASE_MANAGER",
    "CASE_MANAGEMENT": "CASE_MANAGER",
    "CASE_MANAGER": "CASE_MANAGER",
    "CASE MANAGER": "CASE_MANAGER",
}

_PROFILE_DISCIPLINE_ALIASES = {
    "ADMN": None,
    "HA": "CHHA",
    "HHA": "CHHA",
    "VOL": None,
}

ASSIGNABLE_DISCIPLINES: tuple[Discipline, ...] = tuple(
    discipline
    for discipline in Discipline
    if discipline is not Discipline.ADMIN
)
ASSIGNABLE_DISCIPLINE_VALUES = {discipline.value for discipline in ASSIGNABLE_DISCIPLINES}


def _clean_token(value: str | None) -> str:
    return str(value or "").strip().upper().replace("-", "_")


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def normalize_assignment_discipline(value: str | None) -> Discipline:
    token = _clean_token(value).replace(" ", "_")
    token = _DISCIPLINE_INPUT_ALIASES.get(token, token)

    try:
        discipline = Discipline(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "discipline must be one of: "
                + ", ".join(sorted(ASSIGNABLE_DISCIPLINE_VALUES))
            ),
        ) from exc

    if discipline not in ASSIGNABLE_DISCIPLINES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"discipline '{discipline.value}' cannot be assigned",
        )

    return discipline


def _normalized_user_assignment_disciplines(staff_user: User) -> set[Discipline]:
    candidates: set[Discipline] = set()

    role_tokens = {
        _clean_token(staff_user.role),
        normalize_role(staff_user.role),
    }
    profile_token = _clean_token(getattr(staff_user, "discipline", None))
    profile_token = _PROFILE_DISCIPLINE_ALIASES.get(profile_token, profile_token)
    if profile_token:
        role_tokens.add(profile_token)

    for token in list(role_tokens):
        if not token:
            continue
        if token in Discipline._value2member_map_ and token in ASSIGNABLE_DISCIPLINE_VALUES:
            candidates.add(Discipline(token))

    role = _clean_token(staff_user.role)
    if role == "CHHA":
        candidates.add(Discipline.CHHA)
    elif role == "SW":
        candidates.add(Discipline.SW)
    elif role == "SC":
        candidates.add(Discipline.SC)
    elif role == "RN":
        candidates.add(Discipline.RN)
    elif role == "LVN":
        candidates.add(Discipline.LVN)
    elif role == "LPN":
        candidates.add(Discipline.LPN)

    return candidates


# Case Manager is not a separate clinical credential — it's an assignable
# administrative role the agency designates to one of its own RN or LVN/LPN
# staff. Any active RN or LVN/LPN can be assigned as Case Manager; the agency
# decides which one for a given patient.
CASE_MANAGER_ELIGIBLE_DISCIPLINES = {Discipline.RN, Discipline.LVN, Discipline.LPN}


def validate_staff_user_for_assignment(
    db: Session,
    *,
    tenant_id: UUID,
    staff_user_id: UUID,
    discipline: Discipline,
) -> User:
    staff_user = (
        db.query(User)
        .filter(
            User.id == staff_user_id,
            User.tenant_id == tenant_id,
            User.active.is_(True),
        )
        .first()
    )
    if not staff_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned staff user must be an active user in this tenant",
        )

    allowed_disciplines = _normalized_user_assignment_disciplines(staff_user)
    is_case_manager_match = (
        discipline == Discipline.CASE_MANAGER
        and bool(allowed_disciplines & CASE_MANAGER_ELIGIBLE_DISCIPLINES)
    )
    if discipline not in allowed_disciplines and not is_case_manager_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{staff_user.full_name or staff_user.email} cannot be assigned as "
                f"{discipline.value}. Eligible disciplines: "
                + ", ".join(sorted(item.value for item in allowed_disciplines))
                if allowed_disciplines
                else f"{staff_user.full_name or staff_user.email} does not have an assignable clinical discipline"
            ),
        )

    return staff_user


def _display_full_name(user: User | None) -> str | None:
    if user is None:
        return None
    return (
        getattr(user, "display_name", None)
        or getattr(user, "full_name", None)
        or getattr(user, "email", None)
    )


def serialize_assignment(
    assignment: PatientAssignment,
    *,
    staff_user: User | None = None,
    assigned_by_user: User | None = None,
) -> dict[str, Any]:
    return {
        "id": str(assignment.id),
        "patient_id": str(assignment.patient_id),
        "tenant_id": str(assignment.tenant_id),
        "discipline": _enum_value(assignment.discipline),
        "user_id": str(assignment.user_id),
        "staff_name": _display_full_name(staff_user),
        "staff_full_name": getattr(staff_user, "full_name", None),
        "staff_role": getattr(staff_user, "role", None),
        "staff_discipline": getattr(staff_user, "discipline", None),
        "staff_job_title": getattr(staff_user, "job_title", None),
        "is_primary": bool(assignment.is_primary),
        "active": bool(assignment.active),
        "status": assignment.status,
        "service_area": assignment.service_area,
        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        "assigned_by_user_id": str(assignment.assigned_by) if assignment.assigned_by else None,
        "assigned_by_name": _display_full_name(assigned_by_user),
        "note": assignment.note,
        "deactivated_at": assignment.deactivated_at.isoformat() if assignment.deactivated_at else None,
    }


def list_patient_assignments(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    assigned_by_alias = aliased(User)
    rows = (
        db.query(PatientAssignment, User, assigned_by_alias)
        .join(User, User.id == PatientAssignment.user_id)
        .outerjoin(assigned_by_alias, assigned_by_alias.id == PatientAssignment.assigned_by)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
        )
        .order_by(
            PatientAssignment.active.desc(),
            PatientAssignment.is_primary.desc(),
            PatientAssignment.assigned_at.desc(),
        )
    )

    if not include_inactive:
        rows = rows.filter(PatientAssignment.active.is_(True))

    return [
        serialize_assignment(
            assignment,
            staff_user=staff_user,
            assigned_by_user=assigned_by_user,
        )
        for assignment, staff_user, assigned_by_user in rows.all()
    ]


def assign_patient_staff(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    staff_user_id: UUID,
    discipline: Discipline,
    assigned_by: UUID,
    service_area: str | None = None,
    note: str | None = None,
    is_primary: bool = True,
) -> dict[str, Any]:
    staff_user = validate_staff_user_for_assignment(
        db,
        tenant_id=tenant_id,
        staff_user_id=staff_user_id,
        discipline=discipline,
    )
    now = _utcnow()

    active_same_discipline = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.discipline == discipline,
            PatientAssignment.active.is_(True),
        )
        .with_for_update()
        .all()
    )

    current_assignment = None
    for assignment in active_same_discipline:
        if assignment.user_id == staff_user_id:
            current_assignment = assignment
            continue
        assignment.deactivate()
        assignment.status = "REASSIGNED"
        assignment.is_primary = False

    if current_assignment is None:
        current_assignment = (
            db.query(PatientAssignment)
            .filter(
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.patient_id == patient_id,
                PatientAssignment.user_id == staff_user_id,
                PatientAssignment.discipline == discipline,
            )
            .order_by(PatientAssignment.assigned_at.desc())
            .with_for_update()
            .first()
        )

    if current_assignment is None:
        current_assignment = PatientAssignment(
            tenant_id=tenant_id,
            patient_id=patient_id,
            user_id=staff_user_id,
            discipline=discipline,
        )
        db.add(current_assignment)

    current_assignment.active = True
    current_assignment.status = "ASSIGNED"
    current_assignment.is_primary = is_primary
    current_assignment.assigned_by = assigned_by
    current_assignment.assigned_at = now
    current_assignment.service_area = service_area
    current_assignment.note = note
    current_assignment.deactivated_at = None

    db.commit()
    db.refresh(current_assignment)
    assigned_by_user = db.query(User).filter(User.id == assigned_by).first()
    return serialize_assignment(
        current_assignment,
        staff_user=staff_user,
        assigned_by_user=assigned_by_user,
    )


def deactivate_assignment(
    db: Session,
    *,
    assignment: PatientAssignment,
    note: str | None = None,
) -> PatientAssignment:
    assignment.deactivate()
    if note is not None:
        assignment.note = note
    assignment.is_primary = False
    db.commit()
    db.refresh(assignment)
    return assignment


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