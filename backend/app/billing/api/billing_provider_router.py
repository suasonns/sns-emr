from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from app.billing.models.billing_provider_agency_assignment import (
    BILLING_PROVIDER_ASSIGNMENT_STATUSES,
    BILLING_PROVIDER_SERVICE_SCOPES,
    BillingProviderAgencyAssignment,
    BillingProviderAgencyServiceScope,
)
from app.billing.models.billing_provider_organization import (
    BILLING_PROVIDER_ORGANIZATION_STATUSES,
    BillingProviderOrganization,
)
from app.core.database import get_db
from app.core.role_guards import require_owner
from app.core.security import CurrentUser, get_current_user
from app.models.tenant import Tenant
from app.services.audit_logger import log_event

router = APIRouter(prefix="/api/owner/billing-providers", tags=["Owner Billing Providers"])


def _require_platform_owner(user: CurrentUser) -> None:
    require_owner(user)


class BillingProviderOrganizationPayload(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    organization_type: str = Field(min_length=2, max_length=64)
    status: str = Field(default="ACTIVE")
    notes: str | None = None

    @field_validator("name", "organization_type")
    @classmethod
    def _trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value is required")
        return value

    @field_validator("status")
    @classmethod
    def _status_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in BILLING_PROVIDER_ORGANIZATION_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(BILLING_PROVIDER_ORGANIZATION_STATUSES)}"
            )
        return value


class BillingProviderAssignmentPayload(BaseModel):
    billing_provider_organization_id: UUID
    tenant_id: UUID
    relationship_status: str = Field(default="PENDING")
    effective_start_at: datetime
    effective_end_at: datetime | None = None
    financials_enabled: bool = False
    service_scope: list[str] = Field(default_factory=list)

    @field_validator("relationship_status")
    @classmethod
    def _relationship_status_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in BILLING_PROVIDER_ASSIGNMENT_STATUSES:
            raise ValueError(
                f"relationship_status must be one of {sorted(BILLING_PROVIDER_ASSIGNMENT_STATUSES)}"
            )
        return value

    @field_validator("service_scope")
    @classmethod
    def _service_scope_valid(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            scope = value.strip().upper()
            if scope not in BILLING_PROVIDER_SERVICE_SCOPES:
                raise ValueError(
                    f"service_scope entries must be within {sorted(BILLING_PROVIDER_SERVICE_SCOPES)}"
                )
            if scope not in seen:
                normalized.append(scope)
                seen.add(scope)
        return normalized

    @field_validator("effective_end_at")
    @classmethod
    def _effective_window_valid(cls, value: datetime | None, info):
        start = info.data.get("effective_start_at")
        if value is not None and start is not None and value < start:
            raise ValueError("effective_end_at must be on or after effective_start_at")
        return value


def _organization_to_dict(org: BillingProviderOrganization) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "organization_type": org.organization_type,
        "status": org.status,
        "notes": org.notes,
        "created_by": str(org.created_by) if org.created_by else None,
        "updated_by": str(org.updated_by) if org.updated_by else None,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


def _assignment_to_dict(assignment: BillingProviderAgencyAssignment) -> dict:
    provider = assignment.billing_provider_organization
    tenant = assignment.tenant
    return {
        "id": str(assignment.id),
        "billing_provider_organization_id": str(assignment.billing_provider_organization_id),
        "billing_provider_organization_name": provider.name if provider else None,
        "tenant_id": str(assignment.tenant_id),
        "tenant_display_name": tenant.display_name if tenant else None,
        "tenant_legal_name": tenant.legal_name if tenant else None,
        "relationship_status": assignment.relationship_status,
        "effective_start_at": assignment.effective_start_at.isoformat()
        if assignment.effective_start_at
        else None,
        "effective_end_at": assignment.effective_end_at.isoformat()
        if assignment.effective_end_at
        else None,
        "financials_enabled": bool(assignment.financials_enabled),
        "service_scope": [scope.scope for scope in assignment.service_scopes],
        "created_by": str(assignment.created_by) if assignment.created_by else None,
        "updated_by": str(assignment.updated_by) if assignment.updated_by else None,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None,
    }


@router.get("/organizations")
def list_billing_provider_organizations(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    rows = (
        db.query(BillingProviderOrganization)
        .order_by(BillingProviderOrganization.name.asc())
        .all()
    )
    return {"organizations": [_organization_to_dict(row) for row in rows]}


@router.post("/organizations", status_code=201)
def create_billing_provider_organization(
    payload: BillingProviderOrganizationPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    existing = (
        db.query(BillingProviderOrganization)
        .filter(BillingProviderOrganization.name == payload.name)
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A billing provider organization with this name already exists",
        )

    row = BillingProviderOrganization(
        name=payload.name,
        organization_type=payload.organization_type,
        status=payload.status,
        notes=payload.notes,
        created_by=user.user_id,
        updated_by=user.user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    log_event(
        db=db,
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        role=user.role,
        action="OWNER_CREATED_BILLING_PROVIDER_ORGANIZATION",
        entity_type="billing_provider_organization",
        entity_id=str(row.id),
        metadata={
            "name": row.name,
            "organization_type": row.organization_type,
            "status": row.status,
        },
        commit=True,
    )
    return _organization_to_dict(row)


@router.patch("/organizations/{organization_id}")
def update_billing_provider_organization(
    organization_id: UUID,
    payload: BillingProviderOrganizationPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    row = db.get(BillingProviderOrganization, organization_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Billing provider organization not found")
    conflicting = (
        db.query(BillingProviderOrganization)
        .filter(
            BillingProviderOrganization.name == payload.name,
            BillingProviderOrganization.id != organization_id,
        )
        .one_or_none()
    )
    if conflicting is not None:
        raise HTTPException(
            status_code=409,
            detail="A billing provider organization with this name already exists",
        )

    row.name = payload.name
    row.organization_type = payload.organization_type
    row.status = payload.status
    row.notes = payload.notes
    row.updated_by = user.user_id
    db.commit()
    db.refresh(row)

    log_event(
        db=db,
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        role=user.role,
        action="OWNER_UPDATED_BILLING_PROVIDER_ORGANIZATION",
        entity_type="billing_provider_organization",
        entity_id=str(row.id),
        metadata={
            "name": row.name,
            "organization_type": row.organization_type,
            "status": row.status,
        },
        commit=True,
    )
    return _organization_to_dict(row)


@router.get("/assignments")
def list_billing_provider_assignments(
    tenant_id: UUID | None = Query(None),
    billing_provider_organization_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    query = db.query(BillingProviderAgencyAssignment).options(
        joinedload(BillingProviderAgencyAssignment.billing_provider_organization),
        joinedload(BillingProviderAgencyAssignment.tenant),
        joinedload(BillingProviderAgencyAssignment.service_scopes),
    )
    if tenant_id is not None:
        query = query.filter(BillingProviderAgencyAssignment.tenant_id == tenant_id)
    if billing_provider_organization_id is not None:
        query = query.filter(
            BillingProviderAgencyAssignment.billing_provider_organization_id
            == billing_provider_organization_id
        )
    rows = query.order_by(BillingProviderAgencyAssignment.created_at.desc()).all()
    return {"assignments": [_assignment_to_dict(row) for row in rows]}


@router.post("/assignments", status_code=201)
def create_billing_provider_assignment(
    payload: BillingProviderAssignmentPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    if db.get(BillingProviderOrganization, payload.billing_provider_organization_id) is None:
        raise HTTPException(status_code=404, detail="Billing provider organization not found")
    if db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    row = BillingProviderAgencyAssignment(
        billing_provider_organization_id=payload.billing_provider_organization_id,
        tenant_id=payload.tenant_id,
        relationship_status=payload.relationship_status,
        effective_start_at=payload.effective_start_at,
        effective_end_at=payload.effective_end_at,
        financials_enabled=payload.financials_enabled,
        created_by=user.user_id,
        updated_by=user.user_id,
    )
    db.add(row)
    db.flush()
    for scope in payload.service_scope:
        db.add(BillingProviderAgencyServiceScope(assignment_id=row.id, scope=scope))
    db.commit()
    row = (
        db.query(BillingProviderAgencyAssignment)
        .options(
            joinedload(BillingProviderAgencyAssignment.billing_provider_organization),
            joinedload(BillingProviderAgencyAssignment.tenant),
            joinedload(BillingProviderAgencyAssignment.service_scopes),
        )
        .filter(BillingProviderAgencyAssignment.id == row.id)
        .one()
    )

    log_event(
        db=db,
        user_id=str(user.user_id),
        tenant_id=str(payload.tenant_id),
        role=user.role,
        action="OWNER_CREATED_BILLING_PROVIDER_ASSIGNMENT",
        entity_type="billing_provider_assignment",
        entity_id=str(row.id),
        metadata={
            "billing_provider_organization_id": str(payload.billing_provider_organization_id),
            "relationship_status": row.relationship_status,
            "financials_enabled": row.financials_enabled,
            "service_scope": payload.service_scope,
        },
        commit=True,
    )
    return _assignment_to_dict(row)


@router.patch("/assignments/{assignment_id}")
def update_billing_provider_assignment(
    assignment_id: UUID,
    payload: BillingProviderAssignmentPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)
    row = (
        db.query(BillingProviderAgencyAssignment)
        .options(joinedload(BillingProviderAgencyAssignment.service_scopes))
        .filter(BillingProviderAgencyAssignment.id == assignment_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Billing provider assignment not found")
    if db.get(BillingProviderOrganization, payload.billing_provider_organization_id) is None:
        raise HTTPException(status_code=404, detail="Billing provider organization not found")
    if db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    row.billing_provider_organization_id = payload.billing_provider_organization_id
    row.tenant_id = payload.tenant_id
    row.relationship_status = payload.relationship_status
    row.effective_start_at = payload.effective_start_at
    row.effective_end_at = payload.effective_end_at
    row.financials_enabled = payload.financials_enabled
    row.updated_by = user.user_id
    row.service_scopes[:] = [
        BillingProviderAgencyServiceScope(scope=scope) for scope in payload.service_scope
    ]
    db.commit()
    row = (
        db.query(BillingProviderAgencyAssignment)
        .options(
            joinedload(BillingProviderAgencyAssignment.billing_provider_organization),
            joinedload(BillingProviderAgencyAssignment.tenant),
            joinedload(BillingProviderAgencyAssignment.service_scopes),
        )
        .filter(BillingProviderAgencyAssignment.id == assignment_id)
        .one()
    )

    log_event(
        db=db,
        user_id=str(user.user_id),
        tenant_id=str(payload.tenant_id),
        role=user.role,
        action="OWNER_UPDATED_BILLING_PROVIDER_ASSIGNMENT",
        entity_type="billing_provider_assignment",
        entity_id=str(row.id),
        metadata={
            "billing_provider_organization_id": str(payload.billing_provider_organization_id),
            "relationship_status": row.relationship_status,
            "financials_enabled": row.financials_enabled,
            "service_scope": payload.service_scope,
        },
        commit=True,
    )
    return _assignment_to_dict(row)
