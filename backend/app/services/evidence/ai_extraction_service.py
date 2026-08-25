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
      "requires_poc_review": true | false
    }
  ]
}
"""


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

    signals: list[ExtractedSignal] = []
    for item in signals_raw:
        try:
            signal = _parse_signal(item)
        except Exception:
            logger.warning(
                "evidence_harvester: skipping malformed signal item=%r", item
            )
            continue
        if signal is not None:
            signals.append(signal)

    return signals


def _parse_signal(item: Any) -> ExtractedSignal | None:
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

    return ExtractedSignal(
        signal_key=signal_key[:128],
        signal_text=signal_text,
        original_text_excerpt=original_text_excerpt[:2000],
        trend=trend,
        confidence=confidence,
        clinical_system=(str(item.get("clinical_system"))[:64] if item.get("clinical_system") else None),
        requires_idg_review=bool(item.get("requires_idg_review", False)),
        requires_poc_review=bool(item.get("requires_poc_review", False)),
    )
