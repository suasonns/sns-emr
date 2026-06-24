from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.med_reconciliation import (
    MedReconciliationImport,
    MedReconciliationItem,
)

from app.services.med_safety import evaluate_medication_safety

router = APIRouter(
    prefix="/med-reconciliation",
    tags=["med-reconciliation"],
)

VALID_SOURCE_TYPES = {"PDF", "CCD", "C-CDA", "SCANNED_DOC", "MANUAL"}
VALID_SOURCE_CONTEXTS = {"HOSPITAL_DISCHARGE", "ED_VISIT", "INPATIENT_STAY", "OTHER"}
VALID_LIST_TYPES = {"INPATIENT_HISTORY", "DISCHARGE_LIST"}
VALID_SEVERITY = {"MILD", "MODERATE", "SEVERE"}


# =====================================================
# SCHEMAS (Pydantic v2 CLEAN)
# =====================================================

class MedReconciliationImportCreate(BaseModel):
    tenant_id: str = Field(..., description="Tenant UUID")
    patient_id: str = Field(..., description="Patient UUID")
    source_type: str = Field(..., description="PDF | CCD | C-CDA | SCANNED_DOC | MANUAL")
    source_context: str = Field(..., description="HOSPITAL_DISCHARGE | ED_VISIT | INPATIENT_STAY | OTHER")
    source_file_name: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None)
    raw_summary: Optional[str] = Field(default=None)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationImportResponse(BaseModel):
    status: str
    import_id: str

    model_config = {"extra": "forbid"}


class MedReconciliationImportListItem(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    source_type: str
    source_context: str
    status: str
    source_file_name: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    parsed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    raw_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "extra": "forbid",
        "from_attributes": True,
    }


class MedReconciliationImportListResponse(BaseModel):
    count: int
    items: List[MedReconciliationImportListItem]

    model_config = {"extra": "forbid"}


class MedReconciliationItemCreate(BaseModel):
    import_id: str
    tenant_id: str
    patient_id: str
    list_type: str
    med_name_raw: str
    med_name_normalized: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    indication: Optional[str] = None
    reaction_description: Optional[str] = None
    severity: Optional[str] = None
    reaction_category_suggested: Optional[str] = None
    reaction_category_final: Optional[str] = None
    is_discharge_candidate: bool = False
    requires_immediate_review: bool = False
    is_critical_reaction: bool = False
    notes: Optional[str] = None

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationItemResponse(BaseModel):
    status: str
    item_id: str

    model_config = {"extra": "forbid"}


# =====================================================
# HELPERS
# =====================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


# =====================================================
# ROUTES
# =====================================================

@router.get("/health")
def med_reconciliation_health():
    return {"status": "ok"}


@router.post("/imports", response_model=MedReconciliationImportResponse)
def create_med_reconciliation_import(
    payload: MedReconciliationImportCreate,
    db: Session = Depends(get_db),
):
    if payload.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid source_type")

    if payload.source_context not in VALID_SOURCE_CONTEXTS:
        raise HTTPException(status_code=400, detail="Invalid source_context")

    tenant_uuid = _parse_uuid(payload.tenant_id, "tenant_id")
    patient_uuid = _parse_uuid(payload.patient_id, "patient_id")

    uploaded_by_uuid = (
        _parse_uuid(payload.uploaded_by, "uploaded_by") if payload.uploaded_by else None
    )

    now = _utcnow()

    try:
        record = MedReconciliationImport(
            id=uuid.uuid4(),
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            source_type=payload.source_type,
            source_context=payload.source_context,
            status="PENDING_REVIEW",
            source_file_name=payload.source_file_name,
            uploaded_by=uploaded_by_uuid,
            uploaded_at=now,
            raw_summary=payload.raw_summary,
            created_at=now,
            updated_at=now,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return MedReconciliationImportResponse(
            status="CREATED",
            import_id=str(record.id),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error")

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.get("/imports", response_model=MedReconciliationImportListResponse)
def list_med_reconciliation_imports(
    patient_id: Optional[str] = Query(default=None),
    tenant_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    query = db.query(MedReconciliationImport)

    if patient_id:
        query = query.filter(
            MedReconciliationImport.patient_id == _parse_uuid(patient_id, "patient_id")
        )

    if tenant_id:
        query = query.filter(
            MedReconciliationImport.tenant_id == _parse_uuid(tenant_id, "tenant_id")
        )

    if status:
        query = query.filter(MedReconciliationImport.status == status)

    records = (
        query.order_by(MedReconciliationImport.uploaded_at.desc())
        .limit(limit)
        .all()
    )

    items = [
        MedReconciliationImportListItem.model_validate(record)
        for record in records
    ]

    return MedReconciliationImportListResponse(count=len(items), items=items)


@router.post("/items", response_model=MedReconciliationItemResponse)
def create_med_reconciliation_item(
    payload: MedReconciliationItemCreate,
    db: Session = Depends(get_db),
):

    if payload.list_type not in VALID_LIST_TYPES:
        raise HTTPException(status_code=400, detail="Invalid list_type")

    if payload.severity and payload.severity not in VALID_SEVERITY:
        raise HTTPException(status_code=400, detail="Invalid severity")

    import_uuid = _parse_uuid(payload.import_id, "import_id")
    tenant_uuid = _parse_uuid(payload.tenant_id, "tenant_id")
    patient_uuid = _parse_uuid(payload.patient_id, "patient_id")

    parent_import = (
        db.query(MedReconciliationImport)
        .filter(MedReconciliationImport.id == import_uuid)
        .first()
    )

    if not parent_import:
        raise HTTPException(status_code=404, detail="Import not found")

    if parent_import.tenant_id != tenant_uuid:
        raise HTTPException(status_code=400, detail="tenant mismatch")

    if parent_import.patient_id != patient_uuid:
        raise HTTPException(status_code=400, detail="patient mismatch")

    now = _utcnow()

    try:
        item = MedReconciliationItem(
            id=uuid.uuid4(),
            import_id=import_uuid,
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            list_type=payload.list_type,
            med_name_raw=payload.med_name_raw,
            med_name_normalized=payload.med_name_normalized,
            dose=payload.dose,
            route=payload.route,
            frequency=payload.frequency,
            indication=payload.indication,
            reaction_description=payload.reaction_description,
            severity=payload.severity,
            reaction_category_suggested=payload.reaction_category_suggested,
            reaction_category_final=payload.reaction_category_final,
            is_discharge_candidate=payload.is_discharge_candidate,
            requires_immediate_review=False,
            is_critical_reaction=False,
            review_status="PENDING",
            notes=payload.notes,
            created_at=now,
            updated_at=now,
        )

        item = evaluate_medication_safety(item)

        db.add(item)
        db.commit()
        db.refresh(item)

        return MedReconciliationItemResponse(
            status="ITEM_CREATED",
            item_id=str(item.id),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error")

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error")