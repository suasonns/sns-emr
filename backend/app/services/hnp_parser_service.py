from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class HnpPatientRecord:
    first_name: str
    last_name: str
    mrn: str
    date_of_birth: date
    sex: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_diagnosis: str | None = None
    suggested_hospice_driver: str | None = None
    diagnoses: list[str] | None = None
    diagnosis_entries: list[dict[str, Any]] | None = None
    raw_text: str = ""


def _clean_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def _normalize_name(raw_name: str | None) -> tuple[str | None, str | None]:
    cleaned = _clean_whitespace(raw_name)
    if not cleaned:
        return None, None

    if "," in cleaned:
        last, first = [part.strip() for part in cleaned.split(",", 1)]
        return first, last

    parts = cleaned.split()
    if len(parts) == 1:
        return parts[0], None
    if len(parts) >= 2:
        # "First [Middle] Last" -- the surname is the last token; anything in
        # between (e.g. a middle initial) is folded into the first name.
        return " ".join(parts[:-1]), parts[-1]
    return None, None


def _normalize_sex(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip().lower()
    if value.startswith("m"):
        return "Male"
    if value.startswith("f"):
        return "Female"
    return raw.strip().title()


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    candidates = [
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%m-%d-%Y",
    ]
    cleaned = _clean_whitespace(raw)
    if not cleaned:
        return None
    for pattern in candidates:
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    return None


def _extract_first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return _clean_whitespace(match.group(1))


_NEGATED_DIAGNOSIS_PATTERNS = (
    "rule out ",
    "ruled out ",
    "denies ",
    "denied ",
    "no evidence of ",
    "without evidence of ",
)

_UNCERTAIN_DIAGNOSIS_PATTERNS = (
    "possible ",
    "possibly ",
    "probable ",
    "suspected ",
    "concern for ",
    "question of ",
)

_HISTORICAL_DIAGNOSIS_PATTERNS = (
    "history of ",
    "hx of ",
    "h/o ",
    "personal history of ",
    "old ",
)

_SYMPTOM_ONLY_TERMS = {
    "shortness of breath",
    "sob",
    "dyspnea",
    "chest pain",
    "pain",
    "fatigue",
    "weakness",
    "edema",
}


def _classify_diagnosis(value: str) -> dict[str, Any]:
    normalized = _clean_whitespace(value) or ""
    lowered = normalized.lower()
    lowered_without_code = re.sub(
        r"\s*\([a-z][a-z0-9]{1,6}(?:\.[a-z0-9]{1,4})?\)\s*$",
        "",
        lowered,
        flags=re.IGNORECASE,
    ).strip()
    is_negated = any(pattern in lowered for pattern in _NEGATED_DIAGNOSIS_PATTERNS)
    is_uncertain = any(pattern in lowered for pattern in _UNCERTAIN_DIAGNOSIS_PATTERNS)
    is_historical = any(lowered_without_code.startswith(pattern) for pattern in _HISTORICAL_DIAGNOSIS_PATTERNS)
    compact = re.sub(r"\s+", " ", lowered_without_code).strip(" .,:;")
    is_symptom_only = compact in _SYMPTOM_ONLY_TERMS
    return {
        "description": normalized,
        "status": (
            "negated"
            if is_negated
            else "uncertain"
            if is_uncertain
            else "historical"
            if is_historical
            else "symptom_only"
            if is_symptom_only
            else "current"
        ),
        "is_negated": is_negated,
        "is_uncertain": is_uncertain,
        "is_historical": is_historical,
        "is_symptom_only": is_symptom_only,
    }


# Deterministic, keyword-tiered hospice-relevance scorer used ONLY to rank
# which extracted diagnosis is offered as a *suggested* hospice driver. This
# is NOT clinical decision-making and NOT an AI/ML model -- it is a coarse,
# reviewable heuristic that replaces the previous "first diagnosis in the
# document" positional pick, which was discovered to select diagnoses
# alphabetically (an artifact of how some source systems order problem
# lists) rather than by any clinical significance. The value this produces
# is always a *suggestion* -- see persist_patient_from_hnp_extraction, which
# never applies it to an existing patient's confirmed primary diagnosis
# without routing through the standard facesheet-suggestion review queue.
_TIER3_HOSPICE_RELEVANCE_TERMS = (
    "heart failure",
    "chf",
    "cardiomyopathy",
    "copd",
    "chronic obstructive",
    "respiratory failure",
    "end-stage renal",
    "end stage renal",
    "esrd",
    "renal failure",
    "cancer",
    "carcinoma",
    "malignan",
    "metasta",
    "als",
    "amyotrophic",
    "dementia",
    "alzheimer",
    "cirrhosis",
    "liver failure",
    "hepatic failure",
    "stroke",
    "cva",
    "hemiplegia",
    "hemiparesis",
    "failure to thrive",
    "terminal",
)

_TIER2_HOSPICE_RELEVANCE_TERMS = (
    "malnutrition",
    "protein-calorie",
    "protein calorie",
    "diabetes",
    "dm 2",
    "dm2",
    "coronary artery disease",
    "chronic kidney disease",
    "ckd stage 4",
    "ckd stage 5",
    "functional decline",
    "weight loss",
    "pressure ulcer",
    "wound",
    "immobility",
    "dysphagia",
    "aspiration",
)


def _hospice_relevance_score(description: str) -> int:
    """Coarse clinical-relevance tier for a single diagnosis description.

    Higher is more hospice-relevant. This is deliberately simple and
    transparent (keyword-tier matching, no ML/AI) so it can be reviewed and
    adjusted by clinical staff -- its only job is to stop a diagnosis from
    being selected as the suggested hospice driver merely because of its
    position or alphabetical rank in the source document.
    """
    lowered = (description or "").lower()
    if any(term in lowered for term in _TIER3_HOSPICE_RELEVANCE_TERMS):
        return 30
    if any(term in lowered for term in _TIER2_HOSPICE_RELEVANCE_TERMS):
        return 20
    return 10


def _select_suggested_hospice_driver(diagnosis_entries: list[dict[str, Any]]) -> str | None:
    """Pick the extracted diagnosis to *suggest* as the hospice driver.

    Only considers entries classified as "current" (excludes negated,
    uncertain, historical, and symptom-only entries -- see
    _classify_diagnosis). Among current entries, picks the highest scoring
    by _hospice_relevance_score, breaking ties by document order. Falls
    back to the first extracted diagnosis (previous behavior) only if no
    entry is classified as "current", so callers always get a candidate
    when one exists.

    This function never decides a patient's clinical primary diagnosis --
    it only produces a suggestion for a human (or a downstream reconciled
    review-queue write) to confirm.
    """
    if not diagnosis_entries:
        return None

    current_entries = [e for e in diagnosis_entries if e.get("status") == "current"]
    candidates = current_entries or diagnosis_entries

    best_entry = max(
        candidates,
        key=lambda e: _hospice_relevance_score(str(e.get("description") or "")),
    )
    return str(best_entry.get("description") or "") or None


def _extract_diagnoses(text: str) -> tuple[list[str], list[dict[str, Any]]]:
    diagnoses: list[str] = []
    diagnosis_entries: list[dict[str, Any]] = []
    # Non-greedy but spans newlines (DOTALL) since diagnosis descriptions can
    # word-wrap onto a second line in PDF-extracted text (e.g. "...STAGE\n3A...").
    pattern = r"Diagnosis:\s*(.+?)\s*Noted on:\s*([0-9/\-]+)"
    for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
        value = _clean_whitespace(match.group(1))
        noted_on = _parse_date(match.group(2))
        if value and value not in diagnoses:
            diagnoses.append(value)
            diagnosis_entries.append(
                {
                    **_classify_diagnosis(value),
                    "noted_on": noted_on.isoformat() if noted_on else None,
                }
            )

    if not diagnoses:
        for line in text.splitlines():
            if "Diagnosis:" in line:
                value = line.split("Diagnosis:", 1)[1].strip()
                if value:
                    cleaned = _clean_whitespace(value)
                    if cleaned and cleaned not in diagnoses:
                        diagnoses.append(cleaned)
                        diagnosis_entries.append(
                            {
                                **_classify_diagnosis(cleaned),
                                "noted_on": None,
                            }
                        )

    return diagnoses, diagnosis_entries


def parse_hnp_text(raw_text: str) -> HnpPatientRecord | None:
    if not raw_text or not raw_text.strip():
        return None

    text = re.sub(r"\r+", "\n", raw_text)
    text = text.replace("\u00a0", " ")

    raw_name = _extract_first_match(r"Name:[ \t]*([A-Z][A-Za-z\.\'\-]*(?:[ \t]+[A-Z][A-Za-z\.\'\-]*)*)", text)
    if not raw_name:
        raw_name = _extract_first_match(r"KAISER PERMANENTE[ \t]+([A-Z][A-Za-z\-\',\s]+?)(?:\s+MRN:|\s+\(continued\))", text)
    if not raw_name:
        raw_name = _extract_first_match(r"Patient\s+Name\s*[:\-]?[ \t]*([A-Z][A-Za-z\.\'\-]*(?:[ \t]+[A-Z][A-Za-z\.\'\-]*)*)", text)
    if not raw_name:
        return None

    first_name, last_name = _normalize_name(raw_name)
    if not first_name or not last_name:
        return None

    mrn = _extract_first_match(r"MRN:\s*([A-Za-z0-9\-]+)", text) or _extract_first_match(r"MRN\s*[:\-]?\s*([A-Za-z0-9\-]+)", text)
    dob_raw = _extract_first_match(r"Date of birth:\s*([0-9/\-]+)", text) or _extract_first_match(r"DOB:\s*([0-9/\-]+)", text)
    sex = _normalize_sex(_extract_first_match(r"Sex:\s*(Male|Female|M|F)", text))
    if not sex:
        sex = _normalize_sex(_extract_first_match(r"Legal Sex\s*[:\-]?\s*(Male|Female|M|F)", text))

    address = _extract_first_match(r"Address:\s*([^\n]+)", text)
    phone = _extract_first_match(r"Home phone:\s*([0-9\-\(\)\s]+)", text) or _extract_first_match(r"Mobile:\s*([0-9\-\(\)\s]+)", text)
    email = _extract_first_match(r"Email:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text)

    diagnoses, diagnosis_entries = _extract_diagnoses(text)
    # NOTE: the previous implementation used `diagnoses[0]` -- whichever
    # diagnosis happened to appear first in the source document -- as the
    # patient's "primary diagnosis". That is a positional artifact, not a
    # clinical judgment (source systems may order problem lists
    # alphabetically, chronologically, or arbitrarily). We now compute a
    # clinically-scored *suggestion* instead; see
    # _select_suggested_hospice_driver and persist_patient_from_hnp_extraction
    # for how/when this suggestion is allowed to reach a patient record.
    suggested_hospice_driver = _select_suggested_hospice_driver(diagnosis_entries)
    primary = suggested_hospice_driver

    dob = _parse_date(dob_raw)
    if not mrn or not dob:
        raise ValueError("HNP record is missing MRN or DOB")

    return HnpPatientRecord(
        first_name=first_name,
        last_name=last_name,
        mrn=mrn,
        date_of_birth=dob,
        sex=sex,
        address=address,
        phone=phone,
        email=email,
        primary_diagnosis=primary,
        suggested_hospice_driver=suggested_hospice_driver,
        diagnoses=diagnoses,
        diagnosis_entries=diagnosis_entries,
        raw_text=text,
    )


def build_hnp_summary(payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(payload, str):
        parsed = parse_hnp_text(payload)
    else:
        parsed = parse_hnp_text(payload.get("raw_text") or "")
    if not parsed:
        raise ValueError("Unable to parse HNP content")

    return {
        "first_name": parsed.first_name,
        "last_name": parsed.last_name,
        "mrn": parsed.mrn,
        "date_of_birth": parsed.date_of_birth.isoformat(),
        "sex": parsed.sex,
        "address": parsed.address,
        "phone": parsed.phone,
        "email": parsed.email,
        "primary_diagnosis": parsed.primary_diagnosis,
        "suggested_hospice_driver": parsed.suggested_hospice_driver,
        "diagnoses": parsed.diagnoses or [],
        "diagnosis_entries": parsed.diagnosis_entries or [],
    }
