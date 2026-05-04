from collections import defaultdict
from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.models.drug_alias import DrugAlias
from app.models.medication import Medication
from app.models.patient import Patient
from app.services.audit_logger import log_event
from app.utils.med_normalization import normalize_dose, normalize_text

router = APIRouter(prefix="/medications", tags=["medications"])


def _build_alias_map(db: Session, raw_names: list[str]) -> dict[str, str]:
    """
    Build a dictionary for canonical name lookup in ONE DB roundtrip.
    Keys are normalized alias_text (normalize_text).
    Values are canonical_text.
    """
    keys = {normalize_text(n) for n in raw_names if n}
    keys.discard(None)  # safety if normalize_text returns None

    if not keys:
        return {}

    rows = (
        db.query(DrugAlias.alias_text, DrugAlias.canonical_text)
        .filter(DrugAlias.alias_text.in_(keys))
        .all()
    )
    return {a: c for a, c in rows}


def canonical_name_from_map(alias_map: dict[str, str], raw_name: str) -> str:
    """
    Resolve medication name to canonical generic using alias_map; fallback to normalized text.
    """
    key = normalize_text(raw_name) or ""
    return alias_map.get(key, key)


def _canonical_for_med_row(alias_map: dict[str, str], med: Medication) -> str:
    """
    Prefer stored canonical_name (if present), otherwise derive from alias_map.
    """
    if getattr(med, "canonical_name", None):
        return normalize_text(med.canonical_name) or ""
    return canonical_name_from_map(alias_map, med.medication_name or "")


@router.post(
    "/patients/{patient_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add a medication to a patient",
)
def add_medication(
    *,
    patient_id: uuid.UUID,
    medication_name: str,
    dosage: str,
    route: str,
    frequency: str,
    start_date: date,
    ordering_provider_role: str | None = None,  # optional for RN/NP/MD, required for LVN guardrail
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD"])),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Preserve clinician-entered values (audit integrity); only trim outer spaces
    med_name_raw = (medication_name or "").strip()
    dosage_raw = (dosage or "").strip()
    route_raw = (route or "").strip()
    freq_raw = (frequency or "").strip()

    # DB schema uses UUID for medications.patient_id -> keep UUID type (do NOT cast to str)
    pid = patient.id

    # ---- LVN phone/verbal order guardrail ----
    if user.role == "LVN":
        if not ordering_provider_role or ordering_provider_role not in ["NP", "MD"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "LVN medication entry requires a documented phone/verbal order "
                    "from an NP or MD."
                ),
            )

    # Candidate ACTIVE meds for same patient + start_date (fast filter)
    candidates = (
        db.query(Medication)
        .filter(
            Medication.patient_id == pid,
            Medication.start_date == start_date,
            Medication.end_date.is_(None),
        )
        .all()
    )

    # Build alias map for incoming + all candidate names in a single DB query
    alias_map = _build_alias_map(
        db,
        [med_name_raw] + [m.medication_name for m in candidates if m.medication_name],
    )

    # Canonical resolution for incoming (brand->generic if in alias table; else normalized text)
    incoming_canonical = canonical_name_from_map(alias_map, med_name_raw)

    # Normalize other components for duplicate detection
    incoming_dose_key = normalize_dose(dosage_raw)
    incoming_route = normalize_text(route_raw)
    incoming_freq = normalize_text(freq_raw)

    # Duplicate warning check (warning-only; do not block)
    is_duplicate = False
    for m in candidates:
        if _canonical_for_med_row(alias_map, m) != incoming_canonical:
            continue
        if normalize_dose(m.dosage or "") != incoming_dose_key:
            continue
        if normalize_text(m.route or "") != incoming_route:
            continue
        if normalize_text(m.frequency or "") != incoming_freq:
            continue

        is_duplicate = True
        break

    warnings: list[dict[str, str]] = []
    if is_duplicate:
        warnings.append(
            {
                "code": "DUPLICATE_ACTIVE_MED",
                "message": (
                    "An active medication with the same therapy, dose, route, "
                    "frequency, and start date already exists."
                ),
            }
        )

    # Always allow creation (do NOT block clinicians)
    medication = Medication(
        patient_id=pid,
        medication_name=med_name_raw,          # raw entered (audit)
        canonical_name=incoming_canonical,     # ✅ persisted canonical (normalization)
        dosage=dosage_raw,
        route=route_raw,
        frequency=freq_raw,
        start_date=start_date,
        end_date=None,
    )

    db.add(medication)
    db.commit()
    db.refresh(medication)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ADD_MEDICATION",
        entity_type="medication",
        entity_id=str(medication.id),
    )

    response: dict = {"medication_id": str(medication.id), "status": "active"}
    if warnings:
        response["warnings"] = warnings
        response["ui_hint"] = {"row_color": "warning"}

    return response


@router.get(
    "/patients/{patient_id}",
    summary="List medications for a patient",
)
def list_medications_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD", "Surveyor"])),
):
    # DB schema uses UUID for medications.patient_id -> keep UUID type
    pid = patient_id

    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == pid)
        .order_by(Medication.start_date.desc(), Medication.created_at.desc())
        .all()
    )

    # Build alias map once for all meds in this list (for rows that lack canonical_name)
    alias_map = _build_alias_map(db, [m.medication_name for m in meds if m.medication_name])

    # Group ACTIVE meds only to find duplicate therapy orders
    groups = defaultdict(list)
    for m in meds:
        if m.end_date is not None:
            continue

        key = (
            _canonical_for_med_row(alias_map, m),
            normalize_dose(m.dosage or ""),
            normalize_text(m.route or ""),
            normalize_text(m.frequency or ""),
            m.start_date,
        )
        groups[key].append(m.id)

    duplicate_ids = set()
    for ids in groups.values():
        if len(ids) > 1:
            duplicate_ids.update(ids)

    # Return enriched response with flags + UI hint for coloring
    return [
        {
            "medication_id": str(m.id),
            "medication_name": m.medication_name,
            "dosage": m.dosage,
            "route": m.route,
            "frequency": m.frequency,
            "start_date": m.start_date,
            "end_date": m.end_date,
            "status": "active" if m.end_date is None else "discontinued",
            "flags": ["DUPLICATE_ACTIVE_MED"]
            if (m.end_date is None and m.id in duplicate_ids)
            else [],
            "ui_hint": {"row_color": "warning"}
            if (m.end_date is None and m.id in duplicate_ids)
            else {},
        }
        for m in meds
    ]


@router.post(
    "/{medication_id}/discontinue",
    summary="Discontinue a medication",
)
def discontinue_medication(
    medication_id: uuid.UUID,
    end_date: date,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    if medication.end_date is not None:
        raise HTTPException(status_code=400, detail="Medication already discontinued")

    medication.end_date = end_date
    db.commit()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="DISCONTINUE_MEDICATION",
        entity_type="medication",
        entity_id=str(medication.id),
    )

    return {
        "medication_id": str(medication.id),
        "status": "discontinued",
        "end_date": medication.end_date,
    }
