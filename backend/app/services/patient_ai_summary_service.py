"""AI-generated patient overview summary (Priority 3, small AI feature).

Design contract (same shape as app/services/evidence/note_draft_service.py
and app/services/evidence/ai_extraction_service.py -- reuses the existing
Azure OpenAI deployment, no new infrastructure):
    - NEVER raises. Any failure (not configured, network error, malformed
      model output) is logged and the function falls back to a
      deterministic, template-based summary built directly from the same
      already-gathered chart facts -- there is always something to show.
    - NEVER fabricates. The AI path is only ever given facts the caller
      already gathered from real records; the system prompt requires every
      sentence to be grounded in those facts, and the fallback path never
      invents anything beyond restating them.
    - NEVER writes anything. This is a read-only, on-demand summary --
      nothing here persists to the chart or triggers any downstream action.
    - Purely a discussion/demo aid: does not diagnose, does not recommend
      eligibility/certification/discharge decisions, does not predict
      prognosis. The system prompt explicitly forbids all of that.

Required environment variables (already used elsewhere -- shared Azure
OpenAI deployment, no additional configuration needed):
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_DEPLOYMENT
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("sns_emr")

DEFAULT_TIMEOUT_SECONDS = 20.0

_SECTION_KEYS = (
    "overview",
    "clinical_highlights",
    "open_concerns",
    "billing_concerns",
    "follow_up",
)


@dataclass(frozen=True)
class PatientAiSummary:
    overview: str
    clinical_highlights: tuple[str, ...] = field(default_factory=tuple)
    open_concerns: tuple[str, ...] = field(default_factory=tuple)
    billing_concerns: tuple[str, ...] = field(default_factory=tuple)
    follow_up: tuple[str, ...] = field(default_factory=tuple)
    generated_at: str = ""
    model: str | None = None
    ai_generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "overview": self.overview,
            "clinical_highlights": list(self.clinical_highlights),
            "open_concerns": list(self.open_concerns),
            "billing_concerns": list(self.billing_concerns),
            "follow_up": list(self.follow_up),
            "generated_at": self.generated_at,
            "model": self.model,
            "ai_generated": self.ai_generated,
        }


def _azure_openai_config() -> dict[str, str] | None:
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


def is_patient_ai_summary_configured() -> bool:
    return _azure_openai_config() is not None


_SYSTEM_PROMPT = """You are a hospice clinical/billing overview assistant. You are given a \
compact set of already-verified facts about a single patient's chart -- diagnosis, current \
benefit period, recent visits, recent documentation, open tasks, open billing alerts, and \
billing status -- and you produce a short discussion-ready overview from ONLY those facts.

Non-negotiable rules:
- You NEVER diagnose, invent, or infer any clinical fact not explicitly present in the input.
- You NEVER predict prognosis, and NEVER generate or imply an eligibility, certification, \
recertification, or discharge recommendation of any kind.
- You NEVER invent billing figures, alert details, or task details beyond what is given.
- If a section has no relevant input facts, return an empty list for it rather than inventing \
filler content.
- Write in plain, concise, professional language suitable for a quick huddle discussion --
short phrases or short sentences, not clinical documentation prose.

Respond ONLY with JSON of the exact shape:
{"overview": "<1-2 sentence plain-language overview>", "clinical_highlights": ["<short phrase>", ...], \
"open_concerns": ["<short phrase>", ...], "billing_concerns": ["<short phrase>", ...], \
"follow_up": ["<short phrase>", ...]}
"""


def _fallback_summary(context: dict[str, Any]) -> PatientAiSummary:
    """Deterministic, template-based summary built directly from the same
    facts given to the AI path. Always available, even with no Azure
    OpenAI configuration -- guarantees the feature has something to show.
    """
    name = context.get("full_name") or "This patient"
    primary_dx = context.get("primary_diagnosis")
    benefit_period = context.get("benefit_period") or {}

    overview_parts = [f"{name} overview generated from current chart data."]
    if primary_dx:
        overview_parts.append(f"Primary diagnosis: {primary_dx}.")
    if benefit_period.get("period_number"):
        overview_parts.append(
            f"Currently in benefit period {benefit_period['period_number']} ({benefit_period.get('benefit_type') or 'benefit period'})."
        )
    overview = " ".join(overview_parts)

    clinical_highlights: list[str] = []
    if primary_dx:
        clinical_highlights.append(f"Primary diagnosis: {primary_dx}")
    for dx in context.get("secondary_diagnoses") or []:
        clinical_highlights.append(f"Secondary diagnosis: {dx}")
    visits = context.get("recent_visits") or []
    if visits:
        latest = visits[0]
        clinical_highlights.append(
            f"Most recent visit: {latest.get('visit_type') or 'visit'} on {latest.get('visit_datetime') or 'unknown date'}"
        )
    notes = context.get("recent_notes") or []
    if notes:
        clinical_highlights.append(f"{len(notes)} recent note(s) on file")

    open_concerns: list[str] = []
    for task in context.get("open_tasks") or []:
        label = task.get("task_type") or "Task"
        due = task.get("due_date")
        open_concerns.append(f"Open task: {label}" + (f" (due {due})" if due else ""))

    billing_concerns: list[str] = []
    for alert in context.get("open_alerts") or []:
        alert_type = alert.get("alert_type") or "Alert"
        severity = alert.get("severity")
        outstanding = alert.get("outstanding_amount")
        piece = f"{alert_type} alert" + (f" ({severity})" if severity else "")
        if outstanding is not None:
            piece += f" -- ${outstanding} outstanding"
        billing_concerns.append(piece)

    follow_up: list[str] = []
    if open_concerns:
        follow_up.append("Review open tasks listed above.")
    if billing_concerns:
        follow_up.append("Review open billing alerts listed above.")
    if not benefit_period:
        follow_up.append("No current benefit period on file -- verify benefit period status.")
    if not follow_up:
        follow_up.append("No immediate follow-up items identified from current chart data.")

    return PatientAiSummary(
        overview=overview,
        clinical_highlights=tuple(clinical_highlights),
        open_concerns=tuple(open_concerns),
        billing_concerns=tuple(billing_concerns),
        follow_up=tuple(follow_up),
        generated_at=datetime.now(timezone.utc).isoformat(),
        model=None,
        ai_generated=False,
    )


def _call_azure_openai(context: dict[str, Any], config: dict[str, str]) -> PatientAiSummary | None:
    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )
    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, default=str)},
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
        logger.exception("patient_ai_summary_service: AI summary generation call failed")
        return None

    if not isinstance(parsed, dict):
        return None

    overview = str(parsed.get("overview") or "").strip()
    if not overview:
        return None

    def _string_list(key: str) -> tuple[str, ...]:
        raw = parsed.get(key)
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    return PatientAiSummary(
        overview=overview,
        clinical_highlights=_string_list("clinical_highlights"),
        open_concerns=_string_list("open_concerns"),
        billing_concerns=_string_list("billing_concerns"),
        follow_up=_string_list("follow_up"),
        generated_at=datetime.now(timezone.utc).isoformat(),
        model=config["deployment"],
        ai_generated=True,
    )


def generate_patient_ai_summary(context: dict[str, Any]) -> PatientAiSummary:
    """Generate a patient overview summary from an already-gathered facts
    dict. Tries the Azure OpenAI path first when configured; always falls
    back to a deterministic template summary on any failure or when not
    configured. Never raises.
    """
    config = _azure_openai_config()
    if config is not None:
        try:
            ai_summary = _call_azure_openai(context, config)
        except Exception:
            logger.exception("patient_ai_summary_service: unexpected error generating AI summary")
            ai_summary = None
        if ai_summary is not None:
            return ai_summary

    return _fallback_summary(context)
