from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable, List, Dict

from app.models.clinical_note import ClinicalNote

POC_ENGINE_VERSION = "4.0.0"


# =========================================================
# PUBLIC ENTRYPOINT (✅ PURE FUNCTION)
# =========================================================

def generate_poc_suggestions(note: ClinicalNote) -> List[Dict[str, Any]]:
    """
    Generate Plan of Care suggestions from clinical note.
    ✅ PURE FUNCTION (no DB mutation)
    ✅ Used as suggestion engine only
    """

    content_original = _extract_note_content(note)
    content_normalized = _normalize_text(content_original)

    if not content_original.strip():
        return []

    builders: list[tuple[str, Callable[..., dict[str, Any]], Callable[[str], bool]]] = [
        ("PAIN", _build_pain_poc, _detect_pain),
        ("WOUND", _build_wound_poc, _detect_wound),
        ("RESPIRATORY", _build_respiratory_poc, _detect_respiratory),
        ("PSYCHOSOCIAL", _build_psychosocial_poc, _detect_psychosocial),
        ("SPIRITUAL", _build_spiritual_poc, _detect_spiritual),
    ]

    results: List[Dict[str, Any]] = []

    for code, builder, detector in builders:
        if not detector(content_normalized):
            continue

        candidate = builder(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )

        results.append(candidate)

    return results


# =========================================================
# DETECTION LAYER (unchanged)
# =========================================================

def _detect_pain(content: str) -> bool:
    return any(token in content for token in {"pain", "/10"})


def _detect_wound(content: str) -> bool:
    return any(token in content for token in {"wound", "pressure ulcer", "stage"})


def _detect_respiratory(content: str) -> bool:
    return any(token in content for token in {"dyspnea", "oxygen", "sob"})


def _detect_psychosocial(content: str) -> bool:
    return any(token in content for token in {"anxiety", "caregiver", "depressed"})


def _detect_spiritual(content: str) -> bool:
    return any(token in content for token in {"chaplain", "prayer", "faith"})


# =========================================================
# BUILDERS (unchanged – already strong)
# =========================================================

def _build_pain_poc(*, note, content_original, content_normalized):
    return _base_poc(note, "PAIN", "Pain Management", "MODERATE", content_original)


def _build_wound_poc(*, note, content_original, content_normalized):
    return _base_poc(note, "WOUND", "Wound Care", "HIGH", content_original)


def _build_respiratory_poc(*, note, content_original, content_normalized):
    return _base_poc(note, "RESP", "Respiratory", "MODERATE", content_original)


def _build_psychosocial_poc(*, note, content_original, content_normalized):
    return _base_poc(note, "PSYCH", "Psychosocial", "MODERATE", content_original)


def _build_spiritual_poc(*, note, content_original, content_normalized):
    return _base_poc(note, "SPIRIT", "Spiritual Care", "MODERATE", content_original)


# =========================================================
# CORE OBJECT BUILDER
# =========================================================

def _base_poc(note, code, name, severity, evidence):
    now = _utc_now_iso()

    return {
        "code": code,
        "name": name,
        "severity": severity,
        "evidence": evidence,
        "created_at": now,
        "engine_version": POC_ENGINE_VERSION,
    }


# =========================================================
# HELPERS
# =========================================================

def _extract_note_content(note: ClinicalNote) -> str:
    for field in ("content", "narrative", "body", "note_text"):
        value = getattr(note, field, None)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _normalize_text(value: str) -> str:
    return value.lower().strip() if value else ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()