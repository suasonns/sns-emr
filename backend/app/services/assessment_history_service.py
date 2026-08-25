from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Iterable, Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.msw_ica_assessment import MswIcaAssessment
from app.models.rn_recert_assessment import RNRecertAssessment
from app.models.rnica_assessment import RnicaAssessment
from app.models.scica_assessment import ScicaAssessment
from app.services.hope_phase_b_engine import (
    TASK_TYPE_HUV1,
    TASK_TYPE_HUV2,
    validate_huv_visit_completion,
)

SortOrder = Literal["asc", "desc"]


@dataclass
class AssessmentHistoryFilters:
    discipline: str | None = None
    assessment_type: str | None = None
    status: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    limit: int = 200
    offset: int = 0
    sort_order: SortOrder = "asc"


@dataclass
class AssessmentHistoryItem:
    record_id: str
    source_table: str
    discipline: str
    assessment_type: str
    phase_hint: str | None
    visit_date: str | None
    status: str
    locked: bool
    locked_at: str | None
    locked_by: str | None
    created_at: str | None
    updated_at: str | None
    record_url_hint: dict


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _visit_date_from_form_data(form_data: dict | None, *, fallback: datetime | None = None) -> datetime | None:
    visit_meta = (form_data or {}).get("visitMeta") or {}
    visit_date = str(visit_meta.get("visitDate") or "").strip()
    if visit_date:
        try:
            return datetime.fromisoformat(f"{visit_date[:10]}T00:00:00+00:00")
        except ValueError:
            pass
    return fallback


def _normalized_status(*, locked: bool, status: str | None) -> str:
    if locked:
        return "LOCKED"
    raw = str(status or "").strip().upper()
    if raw in {"LOCKED", "FINALIZED", "COMPLETE", "COMPLETED"}:
        return "LOCKED"
    if raw in {"DRAFT", "IN_PROGRESS", "PENDING", "AMENDED"}:
        return raw
    return raw or "DRAFT"


def _latest_admission_for_patient(db: Session, *, patient_id: UUID, tenant_id: UUID | None) -> Admission | None:
    query = db.query(Admission).filter(Admission.patient_id == patient_id)
    if tenant_id is not None:
        query = query.filter(Admission.tenant_id == tenant_id)
    return query.order_by(Admission.created_at.desc()).first()


def _apply_optional_tenant_filter(query, model, tenant_id: UUID | None):
    if hasattr(model, "tenant_id"):
        if tenant_id is None:
            query = query.filter(model.tenant_id.is_(None))
        else:
            query = query.filter((model.tenant_id == tenant_id) | (model.tenant_id.is_(None)))
    return query


def _rn_phase_hint(row: RnicaAssessment, *, election_datetime: datetime | None, visit_datetime: datetime | None) -> str | None:
    assessment_type = str(row.assessment_type or "RNICA").upper()
    if assessment_type != "UPDATE" or not election_datetime or not visit_datetime:
        return None
    try:
        validate_huv_visit_completion(
            election_datetime=election_datetime,
            completed_visit_datetime=visit_datetime,
            discipline="RN",
            task_type_name=TASK_TYPE_HUV1,
        )
        return "HUV1"
    except ValueError:
        pass
    try:
        validate_huv_visit_completion(
            election_datetime=election_datetime,
            completed_visit_datetime=visit_datetime,
            discipline="RN",
            task_type_name=TASK_TYPE_HUV2,
        )
        return "HUV2"
    except ValueError:
        return None


def _serialize_rnica_row(row: RnicaAssessment, *, election_datetime: datetime | None) -> AssessmentHistoryItem:
    visit_datetime = _visit_date_from_form_data(row.form_data or {}, fallback=row.locked_at or row.updated_at or row.created_at)
    return AssessmentHistoryItem(
        record_id=str(row.id),
        source_table="rnica_assessments",
        discipline="RN",
        assessment_type=str(row.assessment_type or "RNICA").upper(),
        phase_hint=_rn_phase_hint(row, election_datetime=election_datetime, visit_datetime=visit_datetime),
        visit_date=visit_datetime.date().isoformat() if visit_datetime else None,
        status=_normalized_status(locked=bool(row.locked), status=row.status),
        locked=bool(row.locked),
        locked_at=_iso(row.locked_at),
        locked_by=None,
        created_at=_iso(row.created_at),
        updated_at=_iso(row.updated_at),
        record_url_hint={"section": "nursing-assessment", "assessment_id": str(row.id)},
    )


def _serialize_msw_row(row: MswIcaAssessment) -> AssessmentHistoryItem:
    visit_datetime = _visit_date_from_form_data(row.form_data or {}, fallback=row.locked_at or row.updated_at or row.created_at)
    return AssessmentHistoryItem(
        record_id=str(row.id),
        source_table="msw_ica_assessments",
        discipline="MSW",
        assessment_type=str(row.assessment_type or "MSWICA").upper(),
        phase_hint=None,
        visit_date=visit_datetime.date().isoformat() if visit_datetime else None,
        status=_normalized_status(locked=bool(row.locked), status=row.status),
        locked=bool(row.locked),
        locked_at=_iso(row.locked_at),
        locked_by=None,
        created_at=_iso(row.created_at),
        updated_at=_iso(row.updated_at),
        record_url_hint={"section": "psychosocial-assessment", "assessment_id": str(row.id)},
    )


def _serialize_sc_row(row: ScicaAssessment) -> AssessmentHistoryItem:
    visit_datetime = _visit_date_from_form_data(row.form_data or {}, fallback=row.locked_at or row.updated_at or row.created_at)
    return AssessmentHistoryItem(
        record_id=str(row.id),
        source_table="scica_assessments",
        discipline="SC",
        assessment_type=str(row.assessment_type or "SCICA").upper(),
        phase_hint=None,
        visit_date=visit_datetime.date().isoformat() if visit_datetime else None,
        status=_normalized_status(locked=bool(row.locked), status=row.status),
        locked=bool(row.locked),
        locked_at=_iso(row.locked_at),
        locked_by=None,
        created_at=_iso(row.created_at),
        updated_at=_iso(row.updated_at),
        record_url_hint={"section": "spiritual-assessment", "assessment_id": str(row.id)},
    )


def _serialize_legacy_rn_recert_row(row: RNRecertAssessment) -> AssessmentHistoryItem:
    visit_datetime = row.finalized_at or row.updated_at or row.created_at
    return AssessmentHistoryItem(
        record_id=str(row.id),
        source_table="rn_recert_assessments",
        discipline="RN",
        assessment_type="RN_RECERT_LEGACY",
        phase_hint=None,
        visit_date=visit_datetime.date().isoformat() if visit_datetime else None,
        status=_normalized_status(locked=bool(row.finalized_at), status=row.status),
        locked=bool(row.finalized_at),
        locked_at=_iso(row.finalized_at),
        locked_by=str(row.attesting_provider_user_id) if row.attesting_provider_user_id else None,
        created_at=_iso(row.created_at),
        updated_at=_iso(row.updated_at),
        record_url_hint={"section": "nursing-assessment", "assessment_id": str(row.id), "source_table": "rn_recert_assessments"},
    )


def _apply_filters(items: Iterable[AssessmentHistoryItem], filters: AssessmentHistoryFilters) -> list[AssessmentHistoryItem]:
    normalized_discipline = str(filters.discipline or "").strip().upper()
    normalized_assessment_type = str(filters.assessment_type or "").strip().upper()
    normalized_status = str(filters.status or "").strip().upper()
    filtered: list[AssessmentHistoryItem] = []
    for item in items:
        if normalized_discipline and item.discipline.upper() != normalized_discipline:
            continue
        if normalized_assessment_type and item.assessment_type.upper() != normalized_assessment_type:
            continue
        if normalized_status and item.status.upper() != normalized_status:
            continue
        item_date = date.fromisoformat(item.visit_date) if item.visit_date else None
        if filters.from_date and item_date and item_date < filters.from_date:
            continue
        if filters.from_date and item_date is None:
            continue
        if filters.to_date and item_date and item_date > filters.to_date:
            continue
        if filters.to_date and item_date is None:
            continue
        filtered.append(item)
    reverse = filters.sort_order == "desc"
    filtered.sort(key=lambda item: ((item.visit_date or ""), (item.created_at or ""), item.record_id), reverse=reverse)
    return filtered


def list_patient_assessment_history(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID | None,
    filters: AssessmentHistoryFilters | None = None,
) -> dict:
    applied = filters or AssessmentHistoryFilters()
    latest_admission = _latest_admission_for_patient(db, patient_id=patient_id, tenant_id=tenant_id)
    election_datetime = None
    if latest_admission is not None:
        election_datetime = (
            latest_admission.election_signed_at
            or latest_admission.soc_date
            or latest_admission.effective_date
            or latest_admission.admission_date
        )

    items: list[AssessmentHistoryItem] = []

    rnica_query = db.query(RnicaAssessment).filter(RnicaAssessment.patient_id == patient_id)
    rnica_rows = _apply_optional_tenant_filter(rnica_query, RnicaAssessment, tenant_id).all()
    items.extend(_serialize_rnica_row(row, election_datetime=election_datetime) for row in rnica_rows)

    legacy_rn_recert_query = db.query(RNRecertAssessment).filter(RNRecertAssessment.patient_id == patient_id)
    legacy_rn_recert_rows = _apply_optional_tenant_filter(legacy_rn_recert_query, RNRecertAssessment, tenant_id).all()
    items.extend(_serialize_legacy_rn_recert_row(row) for row in legacy_rn_recert_rows)

    msw_rows = db.query(MswIcaAssessment).filter(MswIcaAssessment.patient_id == patient_id).all()
    items.extend(_serialize_msw_row(row) for row in msw_rows)

    sc_rows = db.query(ScicaAssessment).filter(ScicaAssessment.patient_id == patient_id).all()
    items.extend(_serialize_sc_row(row) for row in sc_rows)

    filtered = _apply_filters(items, applied)
    total = len(filtered)
    paged = filtered[applied.offset: applied.offset + applied.limit]
    return {
        "items": [asdict(item) for item in paged],
        "total": total,
        "limit": applied.limit,
        "offset": applied.offset,
        "sort_order": applied.sort_order,
        "filters": {
            "discipline": applied.discipline,
            "assessment_type": applied.assessment_type,
            "status": applied.status,
            "from_date": applied.from_date.isoformat() if applied.from_date else None,
            "to_date": applied.to_date.isoformat() if applied.to_date else None,
        },
    }
