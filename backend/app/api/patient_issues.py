from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.patient_issue import PatientIssue
from app.services.audit_events import audit_event

router = APIRouter(prefix="/patient-issues", tags=["patient-issues"])

PATIENT_ISSUE_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "CHHA", "Surveyor"]
PATIENT_ISSUE_EDIT_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "CHHA"]
VALID_STATUSES = {"OPEN", "ONGOING", "RESOLVED"}


def _normalize_required_text(value: str, field_name: str) -> str:
    text_value = (value or "").strip()
    if not text_value:
        raise ValueError(f"{field_name} is required")
    return text_value


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text_value = value.strip()
    return text_value or None


def _normalize_status(value: str | None) -> str:
    status_value = (value or "OPEN").strip().upper()
    if status_value not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    return status_value


class PatientIssueCreate(BaseModel):
    patient_id: uuid.UUID
    category: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1)
    identified_date: date = Field(default_factory=date.today)
    identified_by: uuid.UUID | None = None
    status: str = "OPEN"
    outcome_notes: str | None = None
    resolved_date: date | None = None
    resolved_by: uuid.UUID | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        return _normalize_required_text(value, "category")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _normalize_required_text(value, "description")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: str | None) -> str:
        return _normalize_status(value)

    @field_validator("outcome_notes")
    @classmethod
    def validate_outcome_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PatientIssueUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, min_length=1)
    identified_date: date | None = None
    identified_by: uuid.UUID | None = None
    status: str | None = None
    outcome_notes: str | None = None
    resolved_date: date | None = None
    resolved_by: uuid.UUID | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_required_text(value, "category")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_required_text(value, "description")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_status(value)

    @field_validator("outcome_notes")
    @classmethod
    def validate_outcome_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PatientIssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    category: str
    description: str
    identified_date: date
    identified_by: uuid.UUID | None = None
    status: str
    outcome_notes: str | None = None
    resolved_date: date | None = None
    resolved_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=PatientIssueRead, status_code=status.HTTP_201_CREATED)
def create_patient_issue(
    payload: PatientIssueCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(PATIENT_ISSUE_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)
    issue = PatientIssue(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        category=payload.category,
        description=payload.description,
        identified_date=payload.identified_date,
        identified_by=payload.identified_by or user.user_id,
        status=payload.status,
        outcome_notes=payload.outcome_notes,
        resolved_date=payload.resolved_date,
        resolved_by=payload.resolved_by,
    )
    if issue.status == "RESOLVED":
        issue.resolved_date = issue.resolved_date or issue.identified_date
        issue.resolved_by = issue.resolved_by or user.user_id

    db.add(issue)
    db.flush()

    role = (user.role or "").strip().upper()
    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=role,
        action="PATIENT_ISSUE_CREATED",
        entity_type="PATIENT_ISSUE",
        entity_id=str(issue.id),
        meta={
            "patient_id": str(issue.patient_id),
            "category": issue.category,
            "status": issue.status,
        },
    )
    if issue.status == "RESOLVED":
        audit_event(
            db=db,
            tenant_id=str(user.tenant_id),
            user_id=str(user.user_id),
            role=role,
            action="PATIENT_ISSUE_RESOLVED",
            entity_type="PATIENT_ISSUE",
            entity_id=str(issue.id),
            meta={
                "patient_id": str(issue.patient_id),
                "resolved_date": issue.resolved_date.isoformat() if issue.resolved_date else None,
            },
        )

    db.commit()
    db.refresh(issue)
    return issue


@router.get("/patient/{patient_id}", response_model=list[PatientIssueRead])
def list_patient_issues(
    patient_id: uuid.UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(PATIENT_ISSUE_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    query = db.query(PatientIssue).filter(
        PatientIssue.tenant_id == patient.tenant_id,
        PatientIssue.patient_id == patient.id,
    )
    if status_filter:
        query = query.filter(PatientIssue.status == _normalize_status(status_filter))
    return query.order_by(PatientIssue.identified_date.desc(), PatientIssue.created_at.desc()).all()


@router.patch("/{issue_id}", response_model=PatientIssueRead)
def update_patient_issue(
    issue_id: uuid.UUID,
    payload: PatientIssueUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(PATIENT_ISSUE_EDIT_ROLES)),
):
    issue = (
        db.query(PatientIssue)
        .filter(PatientIssue.id == issue_id, PatientIssue.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Patient issue not found")

    get_authorized_patient(db, issue.patient_id, user)

    original_status = issue.status
    changes = payload.model_dump(exclude_unset=True)
    for field_name in ("category", "description", "identified_date", "identified_by", "outcome_notes"):
        if field_name in changes:
            setattr(issue, field_name, changes[field_name])
    if "status" in changes:
        issue.status = changes["status"]
    if "resolved_date" in changes:
        issue.resolved_date = changes["resolved_date"]
    if "resolved_by" in changes:
        issue.resolved_by = changes["resolved_by"]

    if issue.status == "RESOLVED":
        issue.resolved_date = issue.resolved_date or date.today()
        issue.resolved_by = issue.resolved_by or user.user_id
    elif original_status == "RESOLVED" and issue.status != "RESOLVED":
        issue.resolved_date = None
        issue.resolved_by = None

    issue.updated_at = datetime.now(timezone.utc)

    resolved_transition = original_status != "RESOLVED" and issue.status == "RESOLVED"
    if resolved_transition:
        audit_event(
            db=db,
            tenant_id=str(user.tenant_id),
            user_id=str(user.user_id),
            role=(user.role or "").strip().upper(),
            action="PATIENT_ISSUE_RESOLVED",
            entity_type="PATIENT_ISSUE",
            entity_id=str(issue.id),
            meta={
                "patient_id": str(issue.patient_id),
                "resolved_date": issue.resolved_date.isoformat() if issue.resolved_date else None,
            },
        )

    db.commit()
    db.refresh(issue)
    return issue
