"""Azure OpenAI client wrapper for the AI Evidence Harvester.

Design contract (per UCIER non-negotiable rules):
    - This module NEVER raises. Any failure (missing config, network
      error, malformed model output) is logged and results in an empty
      signal list -- the caller always still preserves the original
      evidence record ("nothing observed is discarded").
    - This module NEVER auto-elevates a signal. It only proposes
      candidate signals for a human (RN/IDG) review queue.
    - Configuration is env-var driven, following the same plain
      os.getenv(...) pattern used in app/services/document_storage.py --
      no pydantic Settings class required.

Required environment variables (all optional -- the service is
inert/no-op if any are missing):
    AZURE_OPENAI_ENDPOINT     e.g. https://sns-hospice-openai.openai.azure.com/openai/v1
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_API_VERSION  e.g. 2024-08-01-preview
    AZURE_OPENAI_DEPLOYMENT   deployment name, e.g. gpt-5.4
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from app.services.evidence.structured_findings import concept_prompt_catalog, validate_findings

logger = logging.getLogger("sns_emr")

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_SOURCE_TEXT_CHARS = 12000  # generous ceiling; well within model context window


@dataclass(frozen=True)
class ExtractedSignal:
    signal_key: str
    signal_text: str
    original_text_excerpt: str
    trend: str | None
    confidence: float | None
    clinical_system: str | None
    requires_idg_review: bool
    requires_poc_review: bool
    # Concept-coded structured RNICA field findings (see
    # app.services.evidence.structured_findings) validated against the
    # shared, server-controlled CONCEPT_REGISTRY -- the model never emits a
    # raw field_path/value here; only a fixed concept_code.
    structured_findings: tuple[dict[str, Any], ...] = ()


def _azure_openai_config() -> dict[str, str] | None:
    """Return the Azure OpenAI config dict, or None if not fully configured."""

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not (endpoint and api_key and api_version and deployment):
        return None

    return {
        "endpoint": endpoint.rstrip("/"),
        "api_key": api_key,
        "api_version": api_version,
        "deployment": deployment,
    }


def is_configured() -> bool:
    """Whether Azure OpenAI credentials are present. Safe to call anytime."""

    return _azure_openai_config() is not None


_SYSTEM_PROMPT = """You are a clinical documentation evidence harvester for a hospice \
agency's EMR. You read one piece of already-written clinical documentation (a visit \
note, communication log entry, certification narrative, face-to-face encounter \
summary, incident report, etc.) and extract clinically meaningful OBSERVATIONS that a \
clinician documented but that may be easy to overlook when scattered across many \
notes and disciplines.

Non-negotiable rules:
- You NEVER diagnose. You NEVER decide a patient's problem list, plan of care, or \
  hospice eligibility. You only surface what was already documented.
- You NEVER fabricate content that is not present in the source text.
- Every signal you output must be directly supported by a short verbatim excerpt from \
  the source text.
- If the note contains no meaningful clinical observations worth surfacing, return an \
  empty "signals" array. Do not invent signals to fill space.
- Prioritize signs of clinical decline, new symptoms, functional/cognitive change, \
  safety concerns, caregiver/psychosocial concerns, and anything that could support or \
  undermine hospice eligibility (terminal decline) -- but only if actually documented.

Respond ONLY with a JSON object of this exact shape:
{
  "signals": [
    {
      "signal_key": "short_snake_case_label",
      "signal_text": "One sentence, plain-language summary of the observation.",
      "original_text_excerpt": "Verbatim short excerpt (<= 300 chars) from the source text that supports this.",
      "trend": "UP" | "DOWN" | "STABLE" | "UNKNOWN",
      "confidence": 0.0-1.0,
      "clinical_system": "e.g. cardiopulmonary, neuro, functional, nutrition, psychosocial, safety, skin, pain",
      "requires_idg_review": true | false,
      "requires_poc_review": true | false,
      "structured_findings": [
        {
          "concept_code": "<EXACT_CODE_FROM_CONCEPT_CATALOG>",
          "value": "<true|false|number, only if the concept has a value_slot>",
          "source_excerpt": "<verbatim quote supporting this, required>",
          "confidence": 0.0-1.0,
          "assertion_status": "CURRENT|HISTORICAL|NEGATED|UNCERTAIN",
          "subject": "PATIENT|FAMILY|OTHER"
        }
      ]
    }
  ]
}

ADDITIONAL RULE for "structured_findings": in addition to the free-text signal above, \
also identify any discrete clinical facts in this same excerpt that map to one of the \
fixed concept_code values in the catalog below -- these become candidate RNICA \
structured field values (checkboxes/dropdowns/numeric fields), not just narrative text. \
You may ONLY use a concept_code that appears verbatim in the catalog; never invent one, \
never guess the nearest match. Leave "structured_findings" as an empty list when nothing \
in this excerpt maps to the catalog.
- "assertion_status" is mandatory: CURRENT (true now), HISTORICAL (past/resolved, e.g. \
"history of...", "resolved", a past date), NEGATED (explicitly denied, e.g. "not using \
oxygen", "denies..."), UNCERTAIN (ambiguous or you cannot confidently tell).
- Only emit a concept when you can quote a real excerpt as source_excerpt -- never guess \
without one.
- Do not invent a numeric value (e.g. liters/minute) the source text doesn't state.
- When a concept has a free-text "value" (e.g. an anatomic location) and the source \
documents MULTIPLE distinct sites for the same concept (e.g. "left buttock and right \
foot wounds"), emit ONE separate structured_finding entry per site, each with a single \
site name in "value" -- never join multiple sites into one combined string (e.g. never \
"left buttock; right foot").
- history mentioned only in passing (e.g. "history of septic shock, resolved") is \
HISTORICAL, not CURRENT, even when it sounds clinically significant.
- When in doubt whether a finding qualifies, omit it entirely.

CONCEPT CATALOG (the only concept_code values structured_findings may ever use):
%%CONCEPT_CATALOG%%
"""

# Rendered once at import time (the registry is static) rather than
# recomputed on every chunk call.
_SYSTEM_PROMPT = _SYSTEM_PROMPT.replace("%%CONCEPT_CATALOG%%", concept_prompt_catalog())


def extract_signals(
    *,
    text: str,
    discipline: str | None = None,
    note_type: str | None = None,
    source_type: str,
) -> list[ExtractedSignal]:
    """Extract candidate clinical signals from a single piece of documentation.

    Never raises. Returns [] if unconfigured, on any network/API error, or if
    the model output cannot be parsed.
    """

    config = _azure_openai_config()
    if config is None:
        logger.info(
            "evidence_harvester: AI extraction skipped (Azure OpenAI not configured) "
            "source_type=%s",
            source_type,
        )
        return []

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return []

    truncated_text = cleaned_text[:MAX_SOURCE_TEXT_CHARS]

    user_context = (
        f"source_type: {source_type}\n"
        f"discipline: {discipline or 'unknown'}\n"
        f"note_type: {note_type or 'unknown'}\n"
        f"--- DOCUMENTATION TEXT ---\n{truncated_text}"
    )

    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_context},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        response = httpx.post(
            url,
            headers={"api-key": config["api_key"], "Content-Type": "application/json"},
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        raw_content = body["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
    except Exception:
        logger.exception(
            "evidence_harvester: AI extraction call failed source_type=%s", source_type
        )
        return []

    signals_raw = parsed.get("signals") if isinstance(parsed, dict) else None
    if not isinstance(signals_raw, list):
        return []

    finding_source_type = _resolve_finding_source_type(source_type, note_type)

    signals: list[ExtractedSignal] = []
    for item in signals_raw:
        try:
            signal = _parse_signal(item, finding_source_type=finding_source_type)
        except Exception:
            logger.warning(
                "evidence_harvester: skipping malformed signal item=%r", item
            )
            continue
        if signal is not None:
            signals.append(signal)

    return signals


# Every evidence source that reaches this module's `extract_signals()` is
# stamped with the PatientEvidenceRecord.source_type it was harvested from
# (clinical_notes, communications_log, patients.py's H&P intake,
# document_harvest_job.py's uploaded-document pipeline, certifications,
# F2F, etc). That value maps 1:1 onto the shared StructuredFinding
# contract's source_type enum except for the generic "DOCUMENT_UPLOAD" tag
# used for ad-hoc file uploads, which is disambiguated using the classified
# document type (H&P/referral vs anything else) so the same concept
# behaves identically regardless of which pipeline it arrived through.
_HNP_DOCUMENT_TYPES = {"H_AND_P", "HNP", "REFERRAL", "REFERRAL_HNP"}


def _resolve_finding_source_type(evidence_source_type: str, note_type: str | None) -> str:
    """Map a PatientEvidenceRecord.source_type (+ optional note_type/document
    classification) onto one of the 4 StructuredFinding source_type values.

    This is the single place that decides REFERRAL_HNP vs UPLOADED_DOCUMENT
    vs CLINICAL_NOTE so every adapter (transcript is handled separately in
    note_draft_service.py) stays consistent -- a concept extracted from an
    uploaded H&P PDF must validate and apply exactly the same way as one
    typed directly into the H&P intake textbox.
    """

    normalized_source = (evidence_source_type or "").strip().upper()
    normalized_note_type = (note_type or "").strip().upper()

    if normalized_source == "REFERRAL_HNP":
        return "REFERRAL_HNP"
    if normalized_source == "DOCUMENT_UPLOAD":
        return "REFERRAL_HNP" if normalized_note_type in _HNP_DOCUMENT_TYPES else "UPLOADED_DOCUMENT"
    # CLINICAL_NOTE, COMMUNICATION_LOG, ON_CALL_LOG, INCIDENT_REPORT,
    # IDG_NOTE, PLAN_OF_CARE_REVIEW, CERTIFICATION, F2F_ENCOUNTER,
    # VOLUNTEER_NOTE, FACILITY_NOTIFICATION -- all authored clinical
    # documentation, not an uploaded/scanned source document.
    return "CLINICAL_NOTE"


def _parse_signal(item: Any, *, finding_source_type: str = "CLINICAL_NOTE") -> ExtractedSignal | None:
    if not isinstance(item, dict):
        return None

    signal_key = str(item.get("signal_key") or "").strip()
    signal_text = str(item.get("signal_text") or "").strip()
    original_text_excerpt = str(item.get("original_text_excerpt") or "").strip()
    if not signal_key or not signal_text or not original_text_excerpt:
        return None

    confidence_raw = item.get("confidence")
    confidence: float | None
    try:
        confidence = float(confidence_raw) if confidence_raw is not None else None
        if confidence is not None:
            confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = None

    trend = item.get("trend")
    if trend not in ("UP", "DOWN", "STABLE", "UNKNOWN"):
        trend = None

    # structured_findings validated against the shared, server-controlled
    # CONCEPT_REGISTRY -- the model never emits a raw field_path/value;
    # only a fixed concept_code. `finding_source_type` is resolved once per
    # call by `_resolve_finding_source_type` from the real evidence source
    # (REFERRAL_HNP / DOCUMENT_UPLOAD->REFERRAL_HNP or UPLOADED_DOCUMENT /
    # CLINICAL_NOTE and siblings) so a concept applies identically no
    # matter which of those pipelines it came from.
    findings_raw = item.get("structured_findings")
    validated = validate_findings(findings_raw, source_type=finding_source_type)
    structured_findings = tuple(f.to_dict() for f in validated)

    return ExtractedSignal(
        signal_key=signal_key[:128],
        signal_text=signal_text,
        original_text_excerpt=original_text_excerpt[:2000],
        trend=trend,
        confidence=confidence,
        clinical_system=(str(item.get("clinical_system"))[:64] if item.get("clinical_system") else None),
        requires_idg_review=bool(item.get("requires_idg_review", False)),
        requires_poc_review=bool(item.get("requires_poc_review", False)),
        structured_findings=structured_findings,
    )
