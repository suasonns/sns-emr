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
    diagnoses: list[str] | None = None
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


def _extract_diagnoses(text: str) -> list[str]:
    diagnoses: list[str] = []
    # Non-greedy but spans newlines (DOTALL) since diagnosis descriptions can
    # word-wrap onto a second line in PDF-extracted text (e.g. "...STAGE\n3A...").
    pattern = r"Diagnosis:\s*(.+?)\s*Noted on:"
    for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
        value = _clean_whitespace(match.group(1))
        if value and value not in diagnoses:
            diagnoses.append(value)

    if not diagnoses:
        for line in text.splitlines():
            if "Diagnosis:" in line:
                value = line.split("Diagnosis:", 1)[1].strip()
                if value:
                    diagnoses.append(value)

    return diagnoses


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

    diagnoses = _extract_diagnoses(text)
    primary = diagnoses[0] if diagnoses else None

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
        diagnoses=diagnoses,
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
        "diagnoses": parsed.diagnoses or [],
    }
