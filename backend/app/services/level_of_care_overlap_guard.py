# app/services/level_of_care_overlap_guard.py

from __future__ import annotations

from datetime import date
from typing import Type

from sqlalchemy.orm import Session

from app.billing.models.loc_events import (
    ContinuousCareEvent,
    GIPPeriod,
    HospiceServiceLevel,
    RespitePeriod,
)


ACTIVE_STATUSES = {"ACTIVE", "PENDING", "OPEN", "IN_PROGRESS", "OVERDUE"}


class LevelOfCareOverlapError(ValueError):
    """
    Raised when a new level-of-care period overlaps an existing active period
    for the same patient and same service level.
    """
    pass


def _model_for_service_level(service_level: str):
    normalized = str(service_level).strip().upper()

    mapping = {
        HospiceServiceLevel.GIP.value: GIPPeriod,
        HospiceServiceLevel.RESPITE.value: RespitePeriod,
        HospiceServiceLevel.CONTINUOUS_CARE.value: ContinuousCareEvent,
    }

    model = mapping.get(normalized)
    if model is None:
        raise ValueError(
            "service_level must be one of: GIP, RESPITE, CONTINUOUS_CARE"
        )
    return model


def _overlap_query(
    db: Session,
    *,
    model: Type,
    patient_id,
    start_date: date,
    end_date: date,
    tenant_id=None,
    exclude_id=None,
):
    query = db.query(model).filter(model.patient_id == patient_id)

    if tenant_id is not None and hasattr(model, "tenant_id"):
        query = query.filter(model.tenant_id == tenant_id)

    if hasattr(model, "status"):
        query = query.filter(model.status.in_(ACTIVE_STATUSES))

    if exclude_id is not None:
        query = query.filter(model.id != exclude_id)

    # overlap logic:
    # existing.start <= new.end AND existing.end >= new.start
    query = query.filter(model.start_date <= end_date).filter(model.end_date >= start_date)

    return query


def ensure_no_level_of_care_overlap(
    db: Session,
    *,
    patient_id,
    service_level: str,
    start_date: date,
    end_date: date,
    tenant_id=None,
    exclude_id=None,
) -> None:
    model = _model_for_service_level(service_level)

    existing = _overlap_query(
        db,
        model=model,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
        exclude_id=exclude_id,
    ).first()

    if existing:
        raise LevelOfCareOverlapError(
            f"Overlap detected for patient_id={patient_id} service_level={service_level} "
            f"with existing record id={getattr(existing, 'id', None)} "
            f"range={getattr(existing, 'start_date', None)}..{getattr(existing, 'end_date', None)}"
        )
