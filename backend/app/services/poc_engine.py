from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable

from sqlalchemy.orm.attributes import flag_modified

from app.models.clinical_note import ClinicalNote

POC_ENGINE_VERSION = "3.0.0"


# =========================================================
# PUBLIC ENTRYPOINT
# =========================================================

def generate_pocs_from_note(note: ClinicalNote) -> None:
    """
    Generate or refresh draft POC suggestions inside note.plan_of_care_updates.
    This function is intentionally idempotent for repeated save/finalize flows.
    """
    _ensure_container(note)

    content_original = _extract_note_content(note)
    content_normalized = _normalize_text(content_original)

    if not content_original.strip():
        _set_meta(note)
        return

    builders: list[tuple[str, Callable[..., dict[str, Any]], Callable[[str], bool]]] = [
        ("PAIN", _build_pain_poc, _detect_pain),
        ("WOUND", _build_wound_poc, _detect_wound),
        ("RESPIRATORY", _build_respiratory_poc, _detect_respiratory),
        ("PSYCHOSOCIAL", _build_psychosocial_poc, _detect_psychosocial),
        ("SPIRITUAL", _build_spiritual_poc, _detect_spiritual),
    ]

    pocs: list[dict[str, Any]] = note.plan_of_care_updates["pocs"]
    changed = False

    for code, builder, detector in builders:
        if not detector(content_normalized):
            continue

        candidate = builder(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
        existing = _find_poc_by_code(pocs, code)

        if existing is None:
            pocs.append(candidate)
            changed = True
            continue

        _merge_poc(existing, candidate)
        changed = True

    if changed:
        _set_meta(note)
        flag_modified(note, "plan_of_care_updates")


# =========================================================
# DETECTION LAYER
# =========================================================

def _detect_pain(content: str) -> bool:
    pain_indicators = {
        "pain",
        "pain reported",
        "pain level",
        "pain score",
        "pain at",
        "pain is",
        "pain was",
        "/10",
    }
    return any(indicator in content for indicator in pain_indicators)


def _detect_wound(content: str) -> bool:
    wound_indicators = {
        "wound",
        "skin tear",
        "pressure ulcer",
        "pressure injury",
        "ulcer",
        "open area",
        "open wound",
        "sore",
        "bed sore",
        "bedsore",
        "decubitus",
        "drainage",
        "slough",
        "eschar",
        "unstageable",
        "deep tissue injury",
        "deep tissue pressure injury",
        "stage 1",
        "stage i",
        "stage 2",
        "stage ii",
        "stage 3",
        "stage iii",
        "stage 4",
        "stage iv",
    }
    return any(indicator in content for indicator in wound_indicators)


def _detect_respiratory(content: str) -> bool:
    respiratory_indicators = {
        "dyspnea",
        "shortness of breath",
        "short of breath",
        "sob",
        "respiratory distress",
        "resp distress",
        "labored breathing",
        "laboured breathing",
        "difficulty breathing",
        "trouble breathing",
        "wheezing",
        "wheeze",
        "oxygen",
        "o2",
        "oxygen dependent",
        "oxygen use",
        "on oxygen",
        "congestion",
        "lung congestion",
        "secretions",
        "increased secretions",
        "rhonchi",
        "crackles",
        "cyanosis",
        "cyanotic",
        "apnea",
        "apneic",
        "respirations",
        "respiratory rate",
        "rr ",
    }
    return any(indicator in content for indicator in respiratory_indicators)


def _detect_psychosocial(content: str) -> bool:
    psychosocial_indicators = {
        "psychosocial",
        "emotional distress",
        "distress",
        "anxiety",
        "anxious",
        "depression",
        "depressed",
        "sad",
        "tearful",
        "crying",
        "grief",
        "grieving",
        "coping difficulty",
        "difficulty coping",
        "poor coping",
        "caregiver stress",
        "caregiver strained",
        "caregiver overwhelmed",
        "family overwhelmed",
        "family stress",
        "family conflict",
        "lack of support",
        "limited support",
        "social isolation",
        "isolated",
        "lonely",
        "fear",
        "fearful",
        "unsafe home",
        "home safety concern",
        "financial concern",
        "financial stress",
        "insurance concern",
        "housing concern",
        "transportation concern",
        "unable to cope",
        "needs social worker",
        "msw needed",
        "msw referral",
        "social worker referral",
        "spouse overwhelmed",
        "daughter overwhelmed",
        "son overwhelmed",
        "caregiver unable",
        "caregiver burnout",
        "burnout",
    }
    return any(indicator in content for indicator in psychosocial_indicators)


def _detect_spiritual(content: str) -> bool:
    spiritual_indicators = {
        "spiritual",
        "spiritual distress",
        "spiritual concern",
        "spiritual support",
        "spiritual care",
        "chaplain",
        "chaplain requested",
        "chaplain needed",
        "chaplain referral",
        "prayer",
        "pray",
        "asked for prayer",
        "requested prayer",
        "faith",
        "faith concern",
        "religious concern",
        "religious support",
        "meaning",
        "meaning of life",
        "purpose",
        "peace",
        "not at peace",
        "unable to find peace",
        "forgiveness",
        "needs forgiveness",
        "fear of death",
        "afraid of dying",
        "fearful of dying",
        "end of life fear",
        "existential",
        "existential distress",
        "why is this happening",
        "questioning god",
        "questioning faith",
        "loss of faith",
        "hopeless",
        "hopelessness",
        "wants chaplain",
        "family requests chaplain",
        "patient requests chaplain",
        "needs spiritual support",
    }
    return any(indicator in content for indicator in spiritual_indicators)


# =========================================================
# POC BUILDERS
# =========================================================

def _build_pain_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=_problem_keywords("PAIN"),
    )
    severity = _classify_pain_severity(content_normalized)

    return _base_poc(
        note=note,
        code="PAIN",
        name="Pain",
        problem_type="PAIN_MANAGEMENT",
        severity=severity,
        summary=f"Pain concern detected from note content (severity={severity}).",
        evidence_value=evidence_value,
        interventions=[
            _intervention(
                discipline="RN",
                action="Assess pain using consistent scale and document response to interventions."
            ),
            _intervention(
                discipline="RN",
                action="Review medication effectiveness and notify provider for uncontrolled pain."
            ),
        ],
    )


def _build_wound_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=_problem_keywords("WOUND"),
    )
    wound_type = _classify_wound_type(content_normalized)
    severity = _classify_wound_severity(content_normalized)

    return _base_poc(
        note=note,
        code="WOUND",
        name="Wound / Skin Integrity",
        problem_type=wound_type,
        severity=severity,
        summary=f"Wound or skin integrity concern detected (type={wound_type}, severity={severity}).",
        evidence_value=evidence_value,
        interventions=[
            _intervention(
                discipline="RN",
                action="Assess wound status, drainage, odor, staging, and surrounding skin."
            ),
            _intervention(
                discipline="RN",
                action="Reinforce wound care orders and escalate signs of infection or decline."
            ),
        ],
    )


def _build_respiratory_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=_problem_keywords("RESPIRATORY"),
    )
    respiratory_type = _classify_respiratory_type(content_normalized)
    severity = _classify_respiratory_severity(content_normalized)

    return _base_poc(
        note=note,
        code="RESPIRATORY",
        name="Respiratory",
        problem_type=respiratory_type,
        severity=severity,
        summary=f"Respiratory concern detected (type={respiratory_type}, severity={severity}).",
        evidence_value=evidence_value,
        interventions=[
            _intervention(
                discipline="RN",
                action="Assess dyspnea, oxygen use, lung sounds, secretions, and respiratory distress."
            ),
            _intervention(
                discipline="RN",
                action="Review comfort measures and notify provider for acute or worsening symptoms."
            ),
        ],
    )


def _build_psychosocial_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=_problem_keywords("PSYCHOSOCIAL"),
    )
    psychosocial_type = _classify_psychosocial_type(content_normalized)
    severity = _classify_psychosocial_severity(content_normalized)

    return _base_poc(
        note=note,
        code="PSYCHOSOCIAL",
        name="Psychosocial Support",
        problem_type=psychosocial_type,
        severity=severity,
        summary=f"Psychosocial concern detected (type={psychosocial_type}, severity={severity}).",
        evidence_value=evidence_value,
        interventions=[
            _intervention(
                discipline="MSW",
                action="Assess coping, caregiver burden, support system, and resource barriers."
            ),
            _intervention(
                discipline="RN",
                action="Coordinate interdisciplinary follow-up for clinically significant psychosocial needs."
            ),
        ],
    )


def _build_spiritual_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=_problem_keywords("SPIRITUAL"),
    )
    spiritual_type = _classify_spiritual_type(content_normalized)
    severity = _classify_spiritual_severity(content_normalized)

    return _base_poc(
        note=note,
        code="SPIRITUAL",
        name="Spiritual Care",
        problem_type=spiritual_type,
        severity=severity,
        summary=f"Spiritual concern detected (type={spiritual_type}, severity={severity}).",
        evidence_value=evidence_value,
        interventions=[
            _intervention(
                discipline="SPIRITUAL_COUNSELOR",
                action="Offer chaplain/spiritual support assessment based on patient/family needs."
            ),
            _intervention(
                discipline="RN",
                action="Document requests for prayer, ritual, faith support, or existential counseling."
            ),
        ],
    )


# =========================================================
# CLASSIFICATION HELPERS
# =========================================================

def _classify_pain_severity(content: str) -> str:
    if any(token in content for token in ("8/10", "9/10", "10/10")):
        return "SEVERE"
    if any(token in content for token in ("4/10", "5/10", "6/10", "7/10")):
        return "MODERATE"
    if any(token in content for token in ("1/10", "2/10", "3/10")):
        return "MILD"
    return "UNSPECIFIED"


def _classify_wound_type(content: str) -> str:
    if "skin tear" in content:
        return "SKIN_TEAR"
    if "pressure ulcer" in content or "pressure injury" in content:
        return "PRESSURE_INJURY"
    if "deep tissue injury" in content or "deep tissue pressure injury" in content:
        return "DEEP_TISSUE_PRESSURE_INJURY"
    if "decubitus" in content or "bed sore" in content or "bedsore" in content:
        return "PRESSURE_INJURY"
    if "ulcer" in content:
        return "ULCER"
    if "open area" in content or "open wound" in content:
        return "OPEN_AREA"
    if "wound" in content:
        return "WOUND"
    return "UNSPECIFIED"


def _classify_wound_severity(content: str) -> str:
    if any(token in content for token in ("stage 4", "stage iv", "stage 3", "stage iii", "unstageable")):
        return "HIGH"
    if any(
        token in content
        for token in ("deep tissue injury", "deep tissue pressure injury", "slough", "eschar", "purulent", "foul odor", "infection", "infected")
    ):
        return "HIGH"
    if any(token in content for token in ("stage 2", "stage ii", "drainage", "open area", "open wound", "skin tear")):
        return "MODERATE"
    if any(token in content for token in ("stage 1", "stage i", "redness", "non-blanchable")):
        return "MILD"
    return "UNSPECIFIED"


def _classify_respiratory_type(content: str) -> str:
    if "oxygen" in content or "o2" in content:
        return "OXYGEN_USE_OR_REVIEW"
    if any(token in content for token in ("dyspnea", "shortness of breath", "short of breath", "sob")):
        return "DYSPNEA"
    if "wheezing" in content or "wheeze" in content:
        return "WHEEZING"
    if any(token in content for token in ("secretions", "congestion", "rhonchi", "crackles")):
        return "CONGESTION_OR_SECRETIONS"
    if "apnea" in content or "apneic" in content:
        return "APNEA"
    if any(token in content for token in ("respiratory distress", "labored breathing", "difficulty breathing")):
        return "RESPIRATORY_DISTRESS"
    return "RESPIRATORY_CONCERN"


def _classify_respiratory_severity(content: str) -> str:
    high_markers = {
        "severe dyspnea",
        "severe shortness of breath",
        "respiratory distress",
        "labored breathing",
        "difficulty breathing",
        "trouble breathing",
        "cyanosis",
        "cyanotic",
        "apnea",
        "apneic",
        "gasping",
        "unable to speak",
        "acute distress",
    }
    moderate_markers = {
        "moderate dyspnea",
        "shortness of breath",
        "short of breath",
        "sob",
        "wheezing",
        "increased secretions",
        "congestion",
        "oxygen",
        "o2",
    }
    mild_markers = {
        "mild dyspnea",
        "mild shortness of breath",
        "occasional cough",
    }

    if any(marker in content for marker in high_markers):
        return "HIGH"
    if any(marker in content for marker in moderate_markers):
        return "MODERATE"
    if any(marker in content for marker in mild_markers):
        return "MILD"
    return "UNSPECIFIED"


def _classify_psychosocial_type(content: str) -> str:
    if "caregiver burnout" in content or "burnout" in content:
        return "CAREGIVER_BURNOUT"
    if any(token in content for token in ("caregiver overwhelmed", "family overwhelmed", "unable to cope")):
        return "CAREGIVER_OVERWHELMED"
    if any(token in content for token in ("caregiver stress", "family stress", "caregiver strained")):
        return "CAREGIVER_STRESS"
    if any(token in content for token in ("anxiety", "anxious", "fear", "fearful")):
        return "ANXIETY_OR_FEAR"
    if any(token in content for token in ("depression", "depressed", "sad", "tearful", "crying")):
        return "MOOD_OR_EMOTIONAL_DISTRESS"
    if "grief" in content or "grieving" in content:
        return "GRIEF_OR_BEREAVEMENT_RELATED_DISTRESS"
    if any(token in content for token in ("social isolation", "isolated", "lonely", "lack of support", "limited support")):
        return "LIMITED_SUPPORT_OR_ISOLATION"
    if any(token in content for token in ("unsafe home", "home safety concern")):
        return "HOME_SAFETY_CONCERN"
    if any(token in content for token in ("financial", "housing", "transportation", "insurance")):
        return "RESOURCE_OR_ACCESS_CONCERN"
    if "msw" in content or "social worker" in content:
        return "MSW_REVIEW_REQUESTED"
    return "PSYCHOSOCIAL_CONCERN"


def _classify_psychosocial_severity(content: str) -> str:
    high_markers = {
        "unsafe home",
        "home safety concern",
        "caregiver unable",
        "unable to cope",
        "caregiver burnout",
        "burnout",
        "family conflict",
        "no support",
        "lack of support",
    }
    moderate_markers = {
        "caregiver overwhelmed",
        "family overwhelmed",
        "caregiver stress",
        "family stress",
        "emotional distress",
        "difficulty coping",
        "poor coping",
        "anxiety",
        "anxious",
        "depressed",
        "tearful",
        "crying",
        "financial concern",
        "transportation concern",
        "housing concern",
    }
    mild_markers = {
        "mild anxiety",
        "mild stress",
        "needs support",
        "limited support",
    }

    if any(marker in content for marker in high_markers):
        return "HIGH"
    if any(marker in content for marker in moderate_markers):
        return "MODERATE"
    if any(marker in content for marker in mild_markers):
        return "MILD"
    return "UNSPECIFIED"


def _classify_spiritual_type(content: str) -> str:
    if "chaplain" in content:
        return "CHAPLAIN_SUPPORT_REQUESTED"
    if "prayer" in content or "pray" in content:
        return "PRAYER_OR_RITUAL_SUPPORT"
    if any(token in content for token in ("fear of death", "afraid of dying", "fearful of dying")):
        return "FEAR_OF_DEATH_OR_DYING_PROCESS"
    if any(token in content for token in ("meaning", "purpose", "existential")):
        return "MEANING_OR_EXISTENTIAL_CONCERN"
    if any(token in content for token in ("peace", "not at peace", "unable to find peace")):
        return "PEACE_OR_ACCEPTANCE_CONCERN"
    if "forgiveness" in content:
        return "FORGIVENESS_CONCERN"
    if any(token in content for token in ("faith", "religious", "questioning god", "questioning faith", "loss of faith")):
        return "FAITH_OR_RELIGIOUS_CONCERN"
    if "hopeless" in content or "hopelessness" in content:
        return "HOPE_OR_MEANING_CONCERN"
    return "SPIRITUAL_CONCERN"


def _classify_spiritual_severity(content: str) -> str:
    high_markers = {
        "spiritual distress",
        "existential distress",
        "fear of death",
        "afraid of dying",
        "fearful of dying",
        "loss of faith",
        "hopeless",
        "hopelessness",
        "unable to find peace",
    }
    moderate_markers = {
        "chaplain requested",
        "chaplain needed",
        "family requests chaplain",
        "patient requests chaplain",
        "prayer requested",
        "requested prayer",
        "questioning faith",
        "questioning god",
        "not at peace",
        "needs spiritual support",
    }
    mild_markers = {
        "spiritual support",
        "prayer",
        "faith concern",
        "religious support",
    }

    if any(marker in content for marker in high_markers):
        return "HIGH"
    if any(marker in content for marker in moderate_markers):
        return "MODERATE"
    if any(marker in content for marker in mild_markers):
        return "MILD"
    return "UNSPECIFIED"


# =========================================================
# SHARED HELPERS
# =========================================================

def _problem_keywords(problem_code: str) -> tuple[str, ...]:
    mapping: dict[str, tuple[str, ...]] = {
        "PAIN": ("pain",),
        "WOUND": (
            "wound",
            "skin tear",
            "pressure ulcer",
            "pressure injury",
            "ulcer",
            "open area",
            "drainage",
            "slough",
            "eschar",
            "unstageable",
            "deep tissue",
            "stage",
        ),
        "RESPIRATORY": (
            "dyspnea",
            "shortness of breath",
            "short of breath",
            "sob",
            "respiratory",
            "labored",
            "wheezing",
            "oxygen",
            "o2",
            "congestion",
            "secretions",
            "cyanosis",
            "apnea",
            "respirations",
        ),
        "PSYCHOSOCIAL": (
            "psychosocial",
            "emotional",
            "distress",
            "anxiety",
            "depression",
            "depressed",
            "tearful",
            "crying",
            "grief",
            "coping",
            "caregiver",
            "family",
            "support",
            "isolation",
            "isolated",
            "financial",
            "housing",
            "transportation",
            "unsafe",
            "social worker",
            "msw",
            "burnout",
        ),
        "SPIRITUAL": (
            "spiritual",
            "chaplain",
            "prayer",
            "pray",
            "faith",
            "religious",
            "meaning",
            "purpose",
            "peace",
            "forgiveness",
            "fear of death",
            "afraid of dying",
            "existential",
            "questioning god",
            "questioning faith",
            "loss of faith",
            "hopeless",
            "hopelessness",
        ),
    }
    return mapping.get(problem_code, (problem_code.lower(),))


def _base_poc(
    *,
    note: ClinicalNote,
    code: str,
    name: str,
    problem_type: str,
    severity: str,
    summary: str,
    evidence_value: str,
    interventions: list[dict[str, Any]],
) -> dict[str, Any]:
    now = _utc_now_iso()
    return {
        "poc_id": _stable_poc_id(note, code),
        "status": "DRAFT",
        "problem": {
            "code": code,
            "name": name,
            "type": problem_type,
        },
        "clinical_summary": {
            "severity": severity,
            "summary": summary,
        },
        "review": _review_required(),
        "evidence": [
            _note_content_evidence(
                value=evidence_value,
                note_id=_safe_str(getattr(note, "id", None)),
                form_key=_safe_str(getattr(note, "form_key", None)),
            )
        ],
        "interventions": interventions,
        "engine": _engine_meta(),
        "source_note_id": _safe_str(getattr(note, "id", None)),
        "form_key": _safe_str(getattr(note, "form_key", None)),
        "created_at": now,
        "last_updated_at": now,
    }


def _intervention(*, discipline: str, action: str) -> dict[str, Any]:
    return {
        "discipline": discipline,
        "action": action,
        "status": "PROPOSED",
    }


def _merge_poc(existing: dict[str, Any], candidate: dict[str, Any]) -> None:
    """
    Refresh an existing generated POC while preserving review history when possible.
    """
    existing["problem"] = candidate["problem"]
    existing["clinical_summary"] = candidate["clinical_summary"]
    existing["interventions"] = candidate["interventions"]
    existing["engine"] = candidate["engine"]
    existing["last_updated_at"] = candidate["last_updated_at"]

    review = existing.get("review")
    if not isinstance(review, dict):
        existing["review"] = _review_required()

    existing_evidence = existing.get("evidence")
    if not isinstance(existing_evidence, list):
        existing_evidence = []
        existing["evidence"] = existing_evidence

    for item in candidate.get("evidence", []):
        _append_evidence_if_missing(existing_evidence, item)


def _append_evidence_if_missing(
    evidence_list: list[dict[str, Any]],
    payload: dict[str, Any],
) -> None:
    for existing in evidence_list:
        if not isinstance(existing, dict):
            continue
        if (
            existing.get("source_type") == payload.get("source_type")
            and existing.get("reference") == payload.get("reference")
            and existing.get("value") == payload.get("value")
        ):
            return
    evidence_list.append(payload)


def _find_poc_by_code(pocs: list[dict[str, Any]], code: str) -> dict[str, Any] | None:
    for item in pocs:
        if not isinstance(item, dict):
            continue
        problem = item.get("problem")
        if not isinstance(problem, dict):
            continue
        if problem.get("code") == code:
            return item
    return None


def _engine_meta() -> dict[str, Any]:
    return {
        "name": "POC_ENGINE",
        "version": POC_ENGINE_VERSION,
        "generated_at": _utc_now_iso(),
    }


def _review_required() -> dict[str, Any]:
    return {
        "required": True,
        "reviewed": False,
        "reviewed_by": None,
        "reviewed_at": None,
        "decision": None,
        "comment": None,
    }


def _note_content_evidence(value: str, note_id: str | None, form_key: str | None) -> dict[str, Any]:
    return {
        "source_type": "NOTE_CONTENT",
        "reference": "content",
        "value": value,
        "note_id": note_id,
        "form_key": form_key,
    }


def _extract_relevant_sentence(
    *,
    content_original: str,
    content_normalized: str,
    keywords: tuple[str, ...],
) -> str:
    original_sentences = _split_sentences(content_original)
    normalized_sentences = _split_sentences(content_normalized)

    for normalized, original in zip(normalized_sentences, original_sentences):
        if any(keyword in normalized for keyword in keywords):
            return original.strip()

    return content_original.strip()[:500]


def _split_sentences(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", value) if part.strip()]


def _ensure_container(note: ClinicalNote) -> None:
    if not isinstance(note.plan_of_care_updates, dict):
        note.plan_of_care_updates = {
            "meta": _engine_meta(),
            "pocs": [],
        }
        flag_modified(note, "plan_of_care_updates")
        return

    if "meta" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["meta"], dict):
        note.plan_of_care_updates["meta"] = _engine_meta()
        flag_modified(note, "plan_of_care_updates")

    if "pocs" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["pocs"], list):
        note.plan_of_care_updates["pocs"] = []
        flag_modified(note, "plan_of_care_updates")


def _set_meta(note: ClinicalNote) -> None:
    _ensure_container(note)
    note.plan_of_care_updates["meta"] = _engine_meta()
    flag_modified(note, "plan_of_care_updates")


def _extract_note_content(note: ClinicalNote) -> str:
    candidate_fields = (
        "content",
        "narrative",
        "body",
        "note_text",
        "raw_text",
    )
    for field in candidate_fields:
        value = getattr(note, field, None)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _normalize_text(value: str) -> str:
    return value.lower().strip() if value else ""


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _stable_poc_id(note: ClinicalNote, code: str) -> str:
    note_id = _safe_str(getattr(note, "id", None)) or "note"
    return f"{note_id}:{code}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()