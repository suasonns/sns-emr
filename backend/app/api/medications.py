from collections import defaultdict
from datetime import date
import re
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.drug_alias import DrugAlias
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.physician_order import PhysicianOrder
from app.models.user import User
from app.services.audit_logger import log_event
from app.services.drug_safety_service import check_new_medication_safety, get_class_group, get_drug_classes
from app.services import physician_order_service
from app.utils.med_normalization import normalize_dose, normalize_text
from app.constants.hospice_stock_formulary import lookup_stock_matches

router = APIRouter(prefix="/medications", tags=["medications"])

RXNORM_APPROXIMATE_TERM_URL = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
RXNORM_DRUGS_URL = "https://rxnav.nlm.nih.gov/REST/drugs.json"

_STRENGTH_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*(?:MG/ML|MCG/ML|MEQ/ML|MG/HR|MCG/HR|MG|MCG|GM|ML|MEQ|UNT|%))",
    re.IGNORECASE,
)

_ROUTE_KEYWORDS = [
    (re.compile(r"sublingual", re.IGNORECASE), "Sublingual"),
    (re.compile(r"transdermal|patch", re.IGNORECASE), "Transdermal"),
    (re.compile(r"topical", re.IGNORECASE), "Topical"),
    (re.compile(r"rectal", re.IGNORECASE), "Rectal"),
    (re.compile(r"ophthalmic", re.IGNORECASE), "Ophthalmic"),
    (re.compile(r"nasal", re.IGNORECASE), "Nasal"),
    (re.compile(r"injectable|injection|prefilled syringe|cartridge", re.IGNORECASE), "Injection"),
    (re.compile(r"oral|chewable|tablet|capsule|solution|suspension|powder|syrup", re.IGNORECASE), "PO"),
]


def _parse_drug_candidate(name: str, synonym: str | None = None) -> dict:
    """
    Parse an RxNorm SBD/SCD display name (e.g. "acetaminophen 500 MG Oral
    Tablet [Tylenol]") into its components so the frontend can auto-fill the
    Strength/Route fields instead of leaving them blank after picking a
    suggestion.
    """
    strength_match = _STRENGTH_RE.search(name)
    strength = strength_match.group(1).upper().replace(" ", "") if strength_match else None

    route = None
    for pattern, label in _ROUTE_KEYWORDS:
        if pattern.search(name):
            route = label
            break

    base_name = name
    brand_name = None
    bracket_idx = name.find("[")
    if bracket_idx != -1:
        base_name = name[:bracket_idx].strip()
        bracket_end = name.find("]", bracket_idx)
        brand_name = name[bracket_idx + 1 : bracket_end if bracket_end != -1 else None].strip() or None
    if strength_match:
        base_name = name[: strength_match.start()].strip()
    display_name = synonym.strip() if synonym else name

    # RxNorm's SBD (branded) concept name already leads with the generic
    # ingredient (e.g. "acetaminophen 500 MG Oral Tablet [Tylenol]") — so a
    # brand-name search (e.g. "Tylenol") naturally surfaces its generic
    # equivalent here. We additionally split out brand_name/generic_name so
    # the frontend can show "Acetaminophen (Tylenol)" explicitly rather than
    # leaving the brand buried in brackets.
    generic_name = base_name.split(" ")[0].strip().title() if base_name else None

    return {
        "name": display_name or name,
        "base_name": base_name or display_name or name,
        "generic_name": generic_name,
        "brand_name": brand_name,
        "strength": strength,
        "route": route,
    }


@router.get("/drug-search", summary="Search RxNorm for medication name suggestions (typeahead)")
def drug_search(
    query: str,
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "PA", "MD", "Surveyor"])),
):
    """
    Proxies NLM's public RxNorm APIs so the frontend can offer typeahead
    suggestions — including strength and route, so picking a suggestion can
    auto-fill those fields — while typing a medication name. Not used/required
    for compounded or off-market medications — those are entered as free text
    and will never appear here since they aren't in RxNorm.
    """
    query = (query or "").strip()
    if len(query) < 3:
        return {"query": query, "suggestions": []}

    suggestions: list[dict] = []
    seen: set[str] = set()

    # Stock hospice comfort-kit medications go first — nudges clinicians toward
    # the strength/route the agency actually stocks (e.g. Morphine Sulfate /
    # Roxanol 20 MG/ML sublingual) instead of an arbitrary RxNorm strength.
    for entry in lookup_stock_matches(query):
        key = entry["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append({
            "name": entry["name"],
            "base_name": entry["name"],
            "generic_name": entry.get("generic_name"),
            "brand_name": entry.get("brand_name"),
            "strength": entry["strength"],
            "route": entry["route"],
            "recommended_dosing": entry.get("recommended_dosing"),
            "rxcui": None,
            "is_stock": True,
        })

    # First try /drugs.json — it groups by term type (SBD/SCD = branded/generic
    # "clinical drug" concepts that carry strength + dose form in the name),
    # which is what lets us surface strength/route to the frontend.
    try:
        resp = httpx.get(RXNORM_DRUGS_URL, params={"name": query}, timeout=4.0)
        resp.raise_for_status()
        data = resp.json()
        for group in (data.get("drugGroup") or {}).get("conceptGroup") or []:
            if group.get("tty") not in ("SBD", "SCD"):
                continue
            for prop in group.get("conceptProperties") or []:
                name = (prop.get("name") or "").strip()
                if not name:
                    continue
                parsed = _parse_drug_candidate(name, prop.get("synonym"))
                key = parsed["name"].lower()
                if key in seen:
                    continue
                seen.add(key)
                suggestions.append({**parsed, "recommended_dosing": None, "rxcui": prop.get("rxcui")})
                if len(suggestions) >= 15:
                    break
            if len(suggestions) >= 15:
                break
    except (httpx.HTTPError, ValueError):
        pass  # fall through to approximateTerm below

    # Fallback (or supplement) — approximateTerm matches more loosely and
    # covers brand/ingredient-only names that drugs.json might miss, but has
    # no strength/route info.
    if len(suggestions) < 10:
        try:
            resp = httpx.get(
                RXNORM_APPROXIMATE_TERM_URL,
                params={"term": query, "maxEntries": 20},
                timeout=4.0,
            )
            resp.raise_for_status()
            data = resp.json()
            for c in (data.get("approximateGroup") or {}).get("candidate") or []:
                name = (c.get("name") or "").strip()
                if not name:
                    continue
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                suggestions.append({"name": name, "base_name": name, "generic_name": None, "brand_name": None, "strength": None, "route": None, "recommended_dosing": None, "rxcui": c.get("rxcui")})
                if len(suggestions) >= 15:
                    break
        except (httpx.HTTPError, ValueError):
            pass  # RxNorm unreachable/slow — fail soft, frontend falls back to free text.

    return {"query": query, "suggestions": suggestions[:15]}


@router.get(
    "/drug-family",
    summary="Same-therapeutic-family alternatives for a medication, cheapest-first, with pharmacy availability",
)
def drug_family(
    drug_name: str,
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "PA", "MD", "Surveyor"])),
):
    """
    Given a medication name (brand or generic), return other stock formulary
    medications that share a drug class — e.g. searching "Roxanol" surfaces
    other opioids the agency stocks (Hydromorphone/Dilaudid). Sorted cheapest
    to most expensive (`relative_cost_rank` ascending). Also reports whether
    the queried medication itself is currently marked available in the
    pharmacy, so the frontend can prompt "not available — recommended
    alternatives" when it isn't.

    Read-only reference data only — does not restrict what can be ordered.
    """
    from app.constants.hospice_stock_formulary import get_therapeutic_alternatives

    return get_therapeutic_alternatives(drug_name)



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


@router.get(
    "/patients/{patient_id}/safety-check",
    summary="Real-time allergy + drug interaction check for a medication name being entered",
)
def check_medication_safety(
    patient_id: uuid.UUID,
    drug_name: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "PA", "MD", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    if not (drug_name or "").strip():
        return {"canonical_name": "", "allergy_alerts": [], "interaction_alerts": []}

    return check_new_medication_safety(db, patient.id, drug_name)


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
    # Who is the prescribing physician/NP/PA for this order? This is the
    # ONLY guardrail — any clinical role (LVN/RN/NP/MD) may document a
    # medication order (these are almost always telephone orders or orders
    # given during IDG), but the prescriber's name + role must always be on
    # file so the order is fully attributable and can be routed to the MD
    # for signature. Whether an agency requires read-back confirmation for
    # phone orders, etc. is an agency-policy setting layered on top.
    ordering_provider_name: str,
    ordering_provider_role: str,  # MD, NP, or PA
    source_type: str = "WRITTEN",  # WRITTEN | VERBAL_PHONE | IDG | ELECTRONIC
    phone_readback_confirmed: bool | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "PA", "MD"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    # Preserve clinician-entered values (audit integrity); only trim outer spaces
    med_name_raw = (medication_name or "").strip()
    dosage_raw = (dosage or "").strip()
    route_raw = (route or "").strip()
    freq_raw = (frequency or "").strip()

    # DB schema uses UUID for medications.patient_id -> keep UUID type (do NOT cast to str)
    pid = patient.id

    # ---- Prescribing-provider guardrail (applies to every role) ----
    provider_name = (ordering_provider_name or "").strip()
    provider_role = (ordering_provider_role or "").strip().upper()
    if not provider_name or provider_role not in physician_order_service.VALID_PROVIDER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Documenting a medication order requires the prescribing "
                "physician/NP/PA's name and role (MD, NP, or PA) — e.g. for "
                "telephone orders or orders given during IDG."
            ),
        )

    src_type = (source_type or "WRITTEN").strip().upper()
    if src_type not in physician_order_service.VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"source_type must be one of {sorted(physician_order_service.VALID_SOURCE_TYPES)}",
        )
    if src_type == "VERBAL_PHONE" and not phone_readback_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Telephone orders require a confirmed read-back before they can be submitted.",
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

    # ---- Create the signed order first (MEDICATION category) so it's
    # visible to the MD in Orders Hub for approval/signature — this is the
    # single source of truth for "who gave the order" + approval status. ----
    order_text_parts = [med_name_raw]
    if dosage_raw:
        order_text_parts.append(dosage_raw)
    if route_raw:
        order_text_parts.append(route_raw)
    if freq_raw:
        order_text_parts.append(freq_raw)
    order_text = " — ".join(order_text_parts)

    draft = physician_order_service.create_draft(
        db,
        tenant_id=user.tenant_id,
        patient_id=pid,
        order_text=order_text,
        order_category="MEDICATION",
        source_type=src_type,
        ordered_by_provider_name=provider_name,
        ordered_by_provider_role=provider_role,
        ordered_at=None,
        prescriber_authenticated=True,
        phone_readback_confirmed=phone_readback_confirmed,
        created_by=user.user_id,
    )
    order = physician_order_service.submit_for_approval(db, order=draft, submitted_by=user.user_id)

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
        created_by=user.user_id,
        physician_order_id=order.id,
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

    # Allergy + interaction safety check (never blocks; flags for review)
    safety = check_new_medication_safety(db, pid, med_name_raw)
    for alert in safety.get("allergy_alerts", []):
        warnings.append(
            {
                "code": "ALLERGY_ALERT",
                "message": (
                    f"Patient has a documented allergy to '{alert['allergen']}' "
                    f"which may match this medication ({alert['matched_on']})."
                ),
                "severity": alert["severity"],
            }
        )
    for alert in safety.get("interaction_alerts", []):
        warnings.append(
            {
                "code": "DRUG_INTERACTION",
                "message": (
                    f"Potential interaction with active medication '{alert['with_medication']}': "
                    f"{alert['effect']}. {alert['management']}"
                ),
                "severity": alert["severity"],
            }
        )

    response: dict = {
        "medication_id": str(medication.id),
        "status": "active",
        "physician_order_id": str(order.id),
        "order_status": order.status,
    }
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
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "PA", "MD", "Surveyor"])),
):
    get_authorized_patient(db, patient_id, user)
    # DB schema uses UUID for medications.patient_id -> keep UUID type
    pid = patient_id

    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == pid)
        .order_by(Medication.start_date.desc(), Medication.created_at.desc())
        .all()
    )

    # Resolve the linked PhysicianOrder (signature/approval status) + the
    # entering staff member's name, in two batched queries, so the Current
    # Medications list can show real MD sign-off status instead of implying
    # every row is already approved just because it says "active".
    order_ids = {m.physician_order_id for m in meds if m.physician_order_id}
    orders_by_id = {}
    if order_ids:
        for o in db.query(PhysicianOrder).filter(PhysicianOrder.id.in_(order_ids)).all():
            orders_by_id[o.id] = o

    user_ids = {m.created_by for m in meds if m.created_by}
    for o in orders_by_id.values():
        if o.signed_by_user_id:
            user_ids.add(o.signed_by_user_id)
    names_by_id = {}
    if user_ids:
        for row in db.query(User.id, User.full_name, User.display_name).filter(User.id.in_(user_ids)).all():
            names_by_id[row[0]] = row[2] or row[1] or "Unknown"

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
    results = []
    for m in meds:
        order = orders_by_id.get(m.physician_order_id) if m.physician_order_id else None
        results.append(
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
                # Audit / signature transparency: who entered it, and what the
                # linked physician order's sign-off status is (if any order
                # is linked — legacy quick-add rows predating this feature
                # won't have one, and are surfaced as "no signed order").
                "entered_by_name": names_by_id.get(m.created_by),
                "order_status": order.status if order else None,
                "ordered_by_provider_name": order.ordered_by_provider_name if order else None,
                "ordered_by_provider_role": order.ordered_by_provider_role if order else None,
                "signed_by_name": names_by_id.get(order.signed_by_user_id) if order and order.signed_by_user_id else None,
                "signed_at": order.signed_at.isoformat() if order and order.signed_at else None,
                "physician_order_id": str(order.id) if order else None,
            }
        )
    return results


@router.post(
    "/{medication_id}/discontinue",
    summary="Discontinue a medication",
)
def discontinue_medication(
    medication_id: uuid.UUID,
    end_date: date,
    discontinue_reason: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "PA", "MD"])),
):
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    get_authorized_patient(db, medication.patient_id, user)

    if medication.end_date is not None:
        raise HTTPException(status_code=400, detail="Medication already discontinued")

    medication.end_date = end_date
    medication.is_active = False
    medication.discontinued_at = date.today()
    medication.discontinued_by = user.user_id
    medication.discontinue_reason = (discontinue_reason or "").strip() or None
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
        "discontinue_reason": medication.discontinue_reason,
    }


@router.get(
    "/patients/{patient_id}/history",
    summary="Query medication history (discontinued/active courses) for a patient, with optional date-range and drug-class filtering",
)
def get_medication_history(
    patient_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    drug_class: str | None = None,
    status_filter: str = "all",
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "PA", "MD", "MSW", "Surveyor"])),
):
    """
    status_filter: "all" | "active" | "discontinued"

    Examples:
    - All meds discontinued in a given month for a patient:
        ?status_filter=discontinued&start_date=2026-08-01&end_date=2026-08-31
    - How many times a patient was on antibiotics during the length of service:
        ?drug_class=ANTIBIOTICS
    - Antibiotic courses within a specific window:
        ?drug_class=ANTIBIOTICS&start_date=2026-01-01&end_date=2026-06-30
    """
    patient = get_authorized_patient(db, patient_id, user)

    status_filter_clean = (status_filter or "all").strip().lower()
    if status_filter_clean not in {"all", "active", "discontinued"}:
        raise HTTPException(status_code=400, detail="status_filter must be one of: all, active, discontinued")

    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == patient.id)
        .order_by(Medication.start_date.desc())
        .all()
    )

    if status_filter_clean == "active":
        meds = [m for m in meds if m.end_date is None]
    elif status_filter_clean == "discontinued":
        meds = [m for m in meds if m.end_date is not None]

    # Date-range filter: course must OVERLAP the requested window (not just start within it)
    if start_date is not None:
        meds = [m for m in meds if m.end_date is None or m.end_date >= start_date]
    if end_date is not None:
        meds = [m for m in meds if m.start_date <= end_date]

    target_classes = get_class_group(drug_class) if drug_class else None
    alias_map = _build_alias_map(db, [m.medication_name for m in meds if m.medication_name])

    items = []
    for m in meds:
        canonical = _canonical_for_med_row(alias_map, m)
        classes = sorted(get_drug_classes(canonical))

        if target_classes is not None and not (target_classes & set(classes)):
            continue

        items.append(
            {
                "medication_id": str(m.id),
                "medication_name": m.medication_name,
                "canonical_name": canonical,
                "classes": classes,
                "dosage": m.dosage,
                "route": m.route,
                "frequency": m.frequency,
                "start_date": m.start_date,
                "end_date": m.end_date,
                "status": "active" if m.end_date is None else "discontinued",
                "discontinued_at": m.discontinued_at,
                "discontinue_reason": m.discontinue_reason,
            }
        )

    return {
        "patient_id": str(patient.id),
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "drug_class": drug_class,
            "status_filter": status_filter_clean,
        },
        "count": len(items),
        "items": items,
    }
