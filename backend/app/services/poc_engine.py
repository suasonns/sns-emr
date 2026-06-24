# app/services/poc_engine.py

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm.attributes import flag_modified

from app.models.clinical_note import ClinicalNote


# =========================================================
# CONSTANTS
# =========================================================

POC_ENGINE_VERSION = "1.4"


# =========================================================
# PUBLIC ENTRYPOINT
# =========================================================

def generate_pocs_from_note(note: ClinicalNote) -> None:
    """
    ENTERPRISE POC ENGINE — HARDENED VERSION

    Guarantees:
    - Append OR update (never skip silently)
    - Deduplicates by problem_code
    - Updates timestamps on re-detection
    - Includes full audit trace (note_id, form_key)
    - Compatible with form engine
    """

    if note is None:
        return

    _ensure_container(note)

    container = note.plan_of_care_updates
    pocs = container.get("pocs")

    if not isinstance(pocs, list):
        container["pocs"] = []
        pocs = container["pocs"]

    content_original = note.content or ""
    content_normalized = content_original.lower().strip()

    if not content_normalized:
        flag_modified(note, "plan_of_care_updates")
        return

    now = _utc_now_iso()
    form_key = getattr(note, "form_key", None)

    # =========================================================
    # UPSERT HELPER
    # =========================================================

    def upsert_poc(problem_code: str, build_fn):
        existing = None

        for poc in pocs:
            if (
                isinstance(poc, dict)
                and poc.get("problem", {}).get("code") == problem_code
            ):
                existing = poc
                break

        if existing:
            # ✅ UPDATE (CRITICAL FIX)
            existing["last_updated_at"] = now

            evidence_list = existing.setdefault("evidence", [])
            evidence_list.append({
                "source_type": "NOTE_CONTENT",
                "reference": "content",
                "value": content_original,
                "note_id": str(note.id) if note.id else None,
                "form_key": form_key,
            })

            return

        # ✅ CREATE NEW
        new_poc = build_fn()
        new_poc["last_updated_at"] = now

        new_poc.setdefault("evidence", []).append({
            "source_type": "NOTE_CONTENT",
            "reference": "content",
            "value": content_original,
            "note_id": str(note.id) if note.id else None,
            "form_key": form_key,
        })

        pocs.append(new_poc)

    # =========================================================
    # DETECTIONS
    # =========================================================

    if _detect_pain(content_normalized):
        upsert_poc(
            "PAIN",
            lambda: _build_pain_poc(
                note=note,
                content_original=content_original,
                content_normalized=content_normalized,
            ),
        )

    if _detect_wound(content_normalized):
        upsert_poc(
            "WOUND",
            lambda: _build_wound_poc(
                note=note,
                content_original=content_original,
                content_normalized=content_normalized,
            ),
        )

    if _detect_respiratory(content_normalized):
        upsert_poc(
            "RESPIRATORY",
            lambda: _build_respiratory_poc(
                note=note,
                content_original=content_original,
                content_normalized=content_normalized,
            ),
        )

    if _detect_psychosocial(content_normalized):
        upsert_poc(
            "PSYCHOSOCIAL",
            lambda: _build_psychosocial_poc(
                note=note,
                content_original=content_original,
                content_normalized=content_normalized,
            ),
        )

    if _detect_spiritual(content_normalized):
        upsert_poc(
            "SPIRITUAL",
            lambda: _build_spiritual_poc(
                note=note,
                content_original=content_original,
                content_normalized=content_normalized,
            ),
        )

    flag_modified(note, "plan_of_care_updates")

    # -----------------------------------------------------
    # DETECTION PIPELINE
    # -----------------------------------------------------
    if _detect_pain(content_normalized):
        _ensure_pain_poc(
            note=note,
            pocs=pocs,
            content_original=content_original,
            content_normalized=content_normalized,
        )

    if _detect_wound(content_normalized):
        _ensure_wound_poc(
            note=note,
            pocs=pocs,
            content_original=content_original,
            content_normalized=content_normalized,
        )

    if _detect_respiratory(content_normalized):
        _ensure_respiratory_poc(
            note=note,
            pocs=pocs,
            content_original=content_original,
            content_normalized=content_normalized,
        )

    if _detect_psychosocial(content_normalized):
        _ensure_psychosocial_poc(
            note=note,
            pocs=pocs,
            content_original=content_original,
            content_normalized=content_normalized,
        )

    if _detect_spiritual(content_normalized):
        _ensure_spiritual_poc(
            note=note,
            pocs=pocs,
            content_original=content_original,
            content_normalized=content_normalized,
        )

    flag_modified(note, "plan_of_care_updates")

# =========================================================
# DETECTION LAYER — PAIN
# =========================================================

def _detect_pain(content: str) -> bool:
    """
    Detect pain mention from free-text note content.

    Phase 2 rule-based logic:
    - Any meaningful pain mention should create a draft PAIN POC.
    """

    if "pain" not in content:
        return False

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


# =========================================================
# DETECTION LAYER — WOUNDS
# =========================================================

def _detect_wound(content: str) -> bool:
    """
    Detect wound-related concerns from free-text note content.

    This is intentionally conservative:
    - It creates a draft POC for clinician review.
    - It does not auto-finalize wound findings.
    """

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


# =========================================================
# DETECTION LAYER — RESPIRATORY
# =========================================================

def _detect_respiratory(content: str) -> bool:
    """
    Detect respiratory concerns from free-text note content.

    This creates a draft respiratory POC requiring clinician review.
    The engine does not diagnose; it identifies documentation that suggests
    a respiratory care planning need.
    """

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


# =========================================================
# DETECTION LAYER — PSYCHOSOCIAL
# =========================================================

def _detect_psychosocial(content: str) -> bool:
    """
    Detect psychosocial concerns from free-text note content.

    This creates a draft psychosocial POC requiring clinician or MSW review.

    Important:
    - This engine does not diagnose anxiety, depression, or psychiatric conditions.
    - It identifies documented psychosocial concern language that may require review.
    """

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


# =========================================================
# DETECTION LAYER — SPIRITUAL
# =========================================================

def _detect_spiritual(content: str) -> bool:
    """
    Detect spiritual or existential concerns from free-text note content.

    This creates a draft spiritual POC requiring clinician / chaplain review.

    Important:
    - This engine does not determine religious belief.
    - This engine does not diagnose spiritual distress.
    - This engine only identifies documented language suggesting spiritual,
      existential, meaning, peace, prayer, faith, or chaplain support needs.
    """

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
# POC ENSURE FUNCTIONS
# =========================================================

def _ensure_pain_poc(
    *,
    note: ClinicalNote,
    pocs: list[dict[str, Any]],
    content_original: str,
    content_normalized: str,
) -> None:
    if _poc_exists(pocs, "PAIN"):
        return

    pocs.append(
        _build_pain_poc(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
    )


def _ensure_wound_poc(
    *,
    note: ClinicalNote,
    pocs: list[dict[str, Any]],
    content_original: str,
    content_normalized: str,
) -> None:
    if _poc_exists(pocs, "WOUND"):
        return

    pocs.append(
        _build_wound_poc(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
    )


def _ensure_respiratory_poc(
    *,
    note: ClinicalNote,
    pocs: list[dict[str, Any]],
    content_original: str,
    content_normalized: str,
) -> None:
    if _poc_exists(pocs, "RESPIRATORY"):
        return

    pocs.append(
        _build_respiratory_poc(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
    )


def _ensure_psychosocial_poc(
    *,
    note: ClinicalNote,
    pocs: list[dict[str, Any]],
    content_original: str,
    content_normalized: str,
) -> None:
    if _poc_exists(pocs, "PSYCHOSOCIAL"):
        return

    pocs.append(
        _build_psychosocial_poc(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
    )


def _ensure_spiritual_poc(
    *,
    note: ClinicalNote,
    pocs: list[dict[str, Any]],
    content_original: str,
    content_normalized: str,
) -> None:
    if _poc_exists(pocs, "SPIRITUAL"):
        return

    pocs.append(
        _build_spiritual_poc(
            note=note,
            content_original=content_original,
            content_normalized=content_normalized,
        )
    )


# =========================================================
# POC BUILDERS — PAIN
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
        keywords=("pain",),
    )

    return {
        "poc_id": str(uuid4()),
        "engine": _engine_meta(),
        "status": "DRAFT",
        "problem": {
            "code": "PAIN",
            "display": "Pain",
            "category": "SYMPTOM",
        },
        "clinical_summary": {
            "detected_problem": "Pain concern detected from note content.",
            "severity": _classify_pain_severity(content_normalized),
            "requires_review": True,
        },
        "goals": [
            {
                "goal_id": str(uuid4()),
                "description": "Pain is assessed, monitored, and managed according to patient goals and ordered interventions.",
                "status": "DRAFT",
            }
        ],
        "interventions": [
            {
                "intervention_id": str(uuid4()),
                "description": "Review pain assessment, current medications, non-pharmacologic interventions, and need for provider notification.",
                "discipline": "RN",
                "status": "DRAFT",
            }
        ],
        "review": _review_required(),
        "evidence": [_note_content_evidence(evidence_value)],
        "created_at": _utc_now_iso(),
        "created_by": str(note.author_id) if note.author_id else None,
    }


# =========================================================
# POC BUILDERS — WOUND
# =========================================================

def _build_wound_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=(
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
    )

    return {
        "poc_id": str(uuid4()),
        "engine": _engine_meta(),
        "status": "DRAFT",
        "problem": {
            "code": "WOUND",
            "display": "Wound / Skin Integrity Concern",
            "category": "SKIN_INTEGRITY",
        },
        "clinical_summary": {
            "detected_problem": "Wound or skin integrity concern detected from note content.",
            "wound_type": _classify_wound_type(content_normalized),
            "severity": _classify_wound_severity(content_normalized),
            "requires_review": True,
        },
        "goals": [
            {
                "goal_id": str(uuid4()),
                "description": "Wound or skin integrity concern is assessed, monitored, and managed with appropriate interventions.",
                "status": "DRAFT",
            }
        ],
        "interventions": [
            {
                "intervention_id": str(uuid4()),
                "description": "Review wound location, measurements, wound bed, drainage, peri-wound condition, pain, infection signs, and current treatment orders.",
                "discipline": "RN",
                "status": "DRAFT",
            },
            {
                "intervention_id": str(uuid4()),
                "description": "Confirm whether wound documentation requires measurement, photo policy review, treatment order update, supply coordination, or provider notification.",
                "discipline": "RN",
                "status": "DRAFT",
            },
        ],
        "review": _review_required(),
        "evidence": [_note_content_evidence(evidence_value)],
        "created_at": _utc_now_iso(),
        "created_by": str(note.author_id) if note.author_id else None,
    }


# =========================================================
# POC BUILDERS — RESPIRATORY
# =========================================================

def _build_respiratory_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=(
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
    )

    return {
        "poc_id": str(uuid4()),
        "engine": _engine_meta(),
        "status": "DRAFT",
        "problem": {
            "code": "RESPIRATORY",
            "display": "Respiratory Concern",
            "category": "RESPIRATORY",
        },
        "clinical_summary": {
            "detected_problem": "Respiratory concern detected from note content.",
            "respiratory_type": _classify_respiratory_type(content_normalized),
            "severity": _classify_respiratory_severity(content_normalized),
            "requires_review": True,
        },
        "goals": [
            {
                "goal_id": str(uuid4()),
                "description": "Respiratory symptoms are assessed, monitored, and managed according to patient goals and ordered interventions.",
                "status": "DRAFT",
            }
        ],
        "interventions": [
            {
                "intervention_id": str(uuid4()),
                "description": "Review respiratory assessment, breathing pattern, dyspnea level, oxygen use, lung sounds, secretions, comfort measures, and need for provider notification.",
                "discipline": "RN",
                "status": "DRAFT",
            },
            {
                "intervention_id": str(uuid4()),
                "description": "Confirm whether respiratory symptoms require medication review, oxygen order review, supply coordination, increased visit frequency, or escalation.",
                "discipline": "RN",
                "status": "DRAFT",
            },
        ],
        "review": _review_required(),
        "evidence": [_note_content_evidence(evidence_value)],
        "created_at": _utc_now_iso(),
        "created_by": str(note.author_id) if note.author_id else None,
    }


# =========================================================
# POC BUILDERS — PSYCHOSOCIAL
# =========================================================

def _build_psychosocial_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=(
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
    )

    return {
        "poc_id": str(uuid4()),
        "engine": _engine_meta(),
        "status": "DRAFT",
        "problem": {
            "code": "PSYCHOSOCIAL",
            "display": "Psychosocial Concern",
            "category": "PSYCHOSOCIAL",
        },
        "clinical_summary": {
            "detected_problem": "Psychosocial concern detected from note content.",
            "psychosocial_type": _classify_psychosocial_type(content_normalized),
            "severity": _classify_psychosocial_severity(content_normalized),
            "requires_review": True,
        },
        "goals": [
            {
                "goal_id": str(uuid4()),
                "description": "Psychosocial needs are assessed, monitored, and addressed with appropriate interdisciplinary support.",
                "status": "DRAFT",
            }
        ],
        "interventions": [
            {
                "intervention_id": str(uuid4()),
                "description": "Review psychosocial concern, coping status, family or caregiver needs, safety concerns, support system, and need for MSW involvement.",
                "discipline": "MSW",
                "status": "DRAFT",
            },
            {
                "intervention_id": str(uuid4()),
                "description": "Confirm whether psychosocial documentation requires MSW referral, caregiver support, resource coordination, IDG discussion, or follow-up assessment.",
                "discipline": "MSW",
                "status": "DRAFT",
            },
        ],
        "review": _review_required(),
        "evidence": [_note_content_evidence(evidence_value)],
        "created_at": _utc_now_iso(),
        "created_by": str(note.author_id) if note.author_id else None,
    }


# =========================================================
# POC BUILDERS — SPIRITUAL
# =========================================================

def _build_spiritual_poc(
    *,
    note: ClinicalNote,
    content_original: str,
    content_normalized: str,
) -> dict[str, Any]:
    evidence_value = _extract_relevant_sentence(
        content_original=content_original,
        content_normalized=content_normalized,
        keywords=(
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
    )

    return {
        "poc_id": str(uuid4()),
        "engine": _engine_meta(),
        "status": "DRAFT",
        "problem": {
            "code": "SPIRITUAL",
            "display": "Spiritual / Existential Concern",
            "category": "SPIRITUAL",
        },
        "clinical_summary": {
            "detected_problem": "Spiritual or existential concern detected from note content.",
            "spiritual_type": _classify_spiritual_type(content_normalized),
            "severity": _classify_spiritual_severity(content_normalized),
            "requires_review": True,
        },
        "goals": [
            {
                "goal_id": str(uuid4()),
                "description": "Spiritual or existential needs are assessed, monitored, and addressed with appropriate interdisciplinary support.",
                "status": "DRAFT",
            }
        ],
        "interventions": [
            {
                "intervention_id": str(uuid4()),
                "description": "Review spiritual or existential concern, patient/family preferences, support system, meaning/peace concerns, and need for chaplain involvement.",
                "discipline": "SC",
                "status": "DRAFT",
            },
            {
                "intervention_id": str(uuid4()),
                "description": "Confirm whether spiritual documentation requires chaplain referral, spiritual counseling, prayer support, IDG discussion, or follow-up assessment.",
                "discipline": "SC",
                "status": "DRAFT",
            },
        ],
        "review": _review_required(),
        "evidence": [_note_content_evidence(evidence_value)],
        "created_at": _utc_now_iso(),
        "created_by": str(note.author_id) if note.author_id else None,
    }


# =========================================================
# CLASSIFICATION HELPERS — PAIN
# =========================================================

def _classify_pain_severity(content: str) -> str:
    if any(token in content for token in ("8/10", "9/10", "10/10")):
        return "SEVERE"

    if any(token in content for token in ("4/10", "5/10", "6/10", "7/10")):
        return "MODERATE"

    if any(token in content for token in ("1/10", "2/10", "3/10")):
        return "MILD"

    return "UNSPECIFIED"


# =========================================================
# CLASSIFICATION HELPERS — WOUND
# =========================================================

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
    if any(token in content for token in ("stage 4", "stage iv")):
        return "HIGH"

    if any(token in content for token in ("stage 3", "stage iii")):
        return "HIGH"

    if "unstageable" in content:
        return "HIGH"

    if "deep tissue injury" in content or "deep tissue pressure injury" in content:
        return "HIGH"

    if any(token in content for token in ("slough", "eschar", "purulent", "foul odor", "infection", "infected")):
        return "HIGH"

    if any(token in content for token in ("stage 2", "stage ii", "drainage", "open area", "open wound", "skin tear")):
        return "MODERATE"

    if any(token in content for token in ("stage 1", "stage i", "redness", "non-blanchable")):
        return "MILD"

    return "UNSPECIFIED"


# =========================================================
# CLASSIFICATION HELPERS — RESPIRATORY
# =========================================================

def _classify_respiratory_type(content: str) -> str:
    if "oxygen" in content or "o2" in content:
        return "OXYGEN_USE_OR_REVIEW"

    if "dyspnea" in content or "shortness of breath" in content or "short of breath" in content or "sob" in content:
        return "DYSPNEA"

    if "wheezing" in content or "wheeze" in content:
        return "WHEEZING"

    if "secretions" in content or "congestion" in content or "rhonchi" in content or "crackles" in content:
        return "CONGESTION_OR_SECRETIONS"

    if "apnea" in content or "apneic" in content:
        return "APNEA"

    if "respiratory distress" in content or "labored breathing" in content or "difficulty breathing" in content:
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


# =========================================================
# CLASSIFICATION HELPERS — PSYCHOSOCIAL
# =========================================================

def _classify_psychosocial_type(content: str) -> str:
    if "caregiver burnout" in content or "burnout" in content:
        return "CAREGIVER_BURNOUT"

    if "caregiver overwhelmed" in content or "family overwhelmed" in content or "unable to cope" in content:
        return "CAREGIVER_OVERWHELMED"

    if "caregiver stress" in content or "family stress" in content or "caregiver strained" in content:
        return "CAREGIVER_STRESS"

    if "anxiety" in content or "anxious" in content or "fear" in content or "fearful" in content:
        return "ANXIETY_OR_FEAR"

    if "depression" in content or "depressed" in content or "sad" in content or "tearful" in content or "crying" in content:
        return "MOOD_OR_EMOTIONAL_DISTRESS"

    if "grief" in content or "grieving" in content:
        return "GRIEF_OR_BEREAVEMENT_RELATED_DISTRESS"

    if "social isolation" in content or "isolated" in content or "lonely" in content or "lack of support" in content or "limited support" in content:
        return "LIMITED_SUPPORT_OR_ISOLATION"

    if "unsafe home" in content or "home safety concern" in content:
        return "HOME_SAFETY_CONCERN"

    if "financial" in content or "housing" in content or "transportation" in content or "insurance" in content:
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


# =========================================================
# CLASSIFICATION HELPERS — SPIRITUAL
# =========================================================

def _classify_spiritual_type(content: str) -> str:
    if "chaplain" in content:
        return "CHAPLAIN_SUPPORT_REQUESTED"

    if "prayer" in content or "pray" in content:
        return "PRAYER_OR_RITUAL_SUPPORT"

    if "fear of death" in content or "afraid of dying" in content or "fearful of dying" in content:
        return "FEAR_OF_DEATH_OR_DYING_PROCESS"

    if "meaning" in content or "purpose" in content or "existential" in content:
        return "MEANING_OR_EXISTENTIAL_CONCERN"

    if "peace" in content or "not at peace" in content or "unable to find peace" in content:
        return "PEACE_OR_ACCEPTANCE_CONCERN"

    if "forgiveness" in content:
        return "FORGIVENESS_CONCERN"

    if "faith" in content or "religious" in content or "questioning god" in content or "questioning faith" in content or "loss of faith" in content:
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
# SHARED STRUCTURE HELPERS
# =========================================================

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
    }


def _note_content_evidence(value: str) -> dict[str, Any]:
    return {
        "source_type": "NOTE_CONTENT",
        "reference": "content",
        "value": value,
    }


def _poc_exists(pocs: list[dict[str, Any]], code: str) -> bool:
    for item in pocs:
        if not isinstance(item, dict):
            continue

        problem = item.get("problem")
        if not isinstance(problem, dict):
            continue

        if problem.get("code") == code:
            return True

    return False


def _extract_relevant_sentence(
    *,
    content_original: str,
    content_normalized: str,
    keywords: tuple[str, ...],
) -> str:
    original = content_original.strip()
    normalized = content_normalized.strip()

    if not original:
        return ""

    sentence_candidates = _split_sentences(original)

    for sentence in sentence_candidates:
        sentence_normalized = sentence.lower()
        if any(keyword in sentence_normalized for keyword in keywords):
            return sentence.strip()

    if normalized:
        return original

    return ""


def _split_sentences(value: str) -> list[str]:
    if not value:
        return []

    normalized = value.replace("\n", " ").strip()

    for delimiter in ("!", "?"):
        normalized = normalized.replace(delimiter, ".")

    parts = [item.strip() for item in normalized.split(".") if item.strip()]
    return parts


def _ensure_container(note: ClinicalNote) -> None:
    if not isinstance(note.plan_of_care_updates, dict):
        note.plan_of_care_updates = {
            "meta": {},
            "pocs": [],
        }
        flag_modified(note, "plan_of_care_updates")
        return

    if "pocs" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["pocs"], list):
        note.plan_of_care_updates["pocs"] = []
        flag_modified(note, "plan_of_care_updates")


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()