# app/domain/clinical/rn_ica_keys.py

from __future__ import annotations
from typing import Any

RN_ICA_CANONICAL_NOTE_TYPE = "RN_ASSESS"
RN_ICA_CANONICAL_FORM_KEY = "RN_ASSESS"
RN_ICA_DISPLAY_NAME = "RN ICA"

RN_ICA_ACCEPTED_KEYS = {
    "RN_ASSESS",
    "RN_ASSESS_V1",
    "RN_HOPE_ADMISSION",
    "RN_ICA",
    "INITIAL_RN_ICA",
}

def normalize_rn_ica_key(value: Any) -> str:
    raw = str(getattr(value, "value", value) or "").strip().upper()
    if raw in RN_ICA_ACCEPTED_KEYS:
        return RN_ICA_CANONICAL_NOTE_TYPE
    return raw

def is_rn_ica_key(value: Any) -> bool:
    raw = str(getattr(value, "value", value) or "").strip().upper()
    return raw in RN_ICA_ACCEPTED_KEYS

def normalize_rn_ica_content(content: Any) -> dict:
    if not isinstance(content, dict):
        return {}

    normalized = dict(content)

    incoming_note_type = normalized.get("note_type")
    if is_rn_ica_key(incoming_note_type):
        normalized["note_type"] = RN_ICA_CANONICAL_NOTE_TYPE
        normalized["display_note_type"] = RN_ICA_DISPLAY_NAME

    incoming_form_key = normalized.get("form_key")
    if is_rn_ica_key(incoming_form_key):
        normalized["form_key"] = RN_ICA_CANONICAL_FORM_KEY

    return normalized