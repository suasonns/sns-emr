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
    "hospice_clinical_picture",
    "primary_hospice_drivers",
    "evidence_of_decline",
    "major_comorbidities",
    "recent_clinical_events",
    "clinical_risks",
    "open_operational_concerns",
)

# --------------------------------------------------------------------------
# Hospice diagnosis prioritization (heuristic, keyword-based; no new AI
# call, no new data source -- classifies the same diagnosis strings already
# gathered by patient_charts.py). This exists so the summary can lead with
# "why is this patient hospice-appropriate" instead of whichever diagnosis
# row happens to be first/newest in the database -- a plain diagnosis dump
# is not a hospice clinical picture.
# --------------------------------------------------------------------------

_HOSPICE_DRIVER_KEYWORDS = (
    "heart failure",
    "chf",
    "cardiomyopathy",
    "copd",
    "emphysema",
    "pulmonary fibrosis",
    "cancer",
    "carcinoma",
    "malignan",
    "dementia",
    "alzheimer",
    "end stage renal",
    "esrd",
    "cirrhosis",
    "amyotrophic",
    " als",
    "parkinson",
)

_DECLINE_EVIDENCE_KEYWORDS = (
    "malnutrition",
    "failure to thrive",
    "debility",
    "hemiplegia",
    "hemiparesis",
    "functional decline",
    "pressure ulcer",
    "pressure injury",
    "decubitus",
    "wound",
    "cachexia",
    "weight loss",
    "dysphagia",
    "immobility",
)

_MAJOR_COMORBIDITY_KEYWORDS = (
    "diabetes",
    "chronic kidney",
    "ckd",
    "stroke",
    "cva",
    "atrial fibrillation",
    "afib",
    "coronary artery disease",
    " cad",
    "anemia",
    "hypertension",
    "peripheral vascular",
)


def _classify_diagnoses(primary_diagnosis: str | None, secondary_diagnoses: list[str]) -> dict[str, list[str]]:
    """Buckets diagnosis strings by hospice relevance, not by insertion
    order/recency/alphabet. First keyword match wins, in priority order:
    hospice driver > evidence of decline > major comorbidity > minor/
    historical (folded into major_comorbidities so nothing is dropped --
    it is simply de-prioritized to later in the summary, never hidden).
    """
    all_dx = [d for d in ([primary_diagnosis] + list(secondary_diagnoses)) if d]
    seen: set[str] = set()
    drivers: list[str] = []
    decline: list[str] = []
    major: list[str] = []
    minor: list[str] = []

    for dx in all_dx:
        key = dx.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        if any(kw in key for kw in _HOSPICE_DRIVER_KEYWORDS):
            drivers.append(dx)
        elif any(kw in key for kw in _DECLINE_EVIDENCE_KEYWORDS):
            decline.append(dx)
        elif any(kw in key for kw in _MAJOR_COMORBIDITY_KEYWORDS):
            major.append(dx)
        else:
            minor.append(dx)

    return {
        "primary_hospice_drivers": drivers,
        "evidence_of_decline": decline,
        "major_comorbidities": major + minor,
    }


@dataclass(frozen=True)
class PatientAiSummary:
    hospice_clinical_picture: str
    primary_hospice_drivers: tuple[str, ...] = field(default_factory=tuple)
    evidence_of_decline: tuple[str, ...] = field(default_factory=tuple)
    major_comorbidities: tuple[str, ...] = field(default_factory=tuple)
    recent_clinical_events: tuple[str, ...] = field(default_factory=tuple)
    clinical_risks: tuple[str, ...] = field(default_factory=tuple)
    open_operational_concerns: tuple[str, ...] = field(default_factory=tuple)
    generated_at: str = ""
    model: str | None = None
    ai_generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "hospice_clinical_picture": self.hospice_clinical_picture,
            "primary_hospice_drivers": list(self.primary_hospice_drivers),
            "evidence_of_decline": list(self.evidence_of_decline),
            "major_comorbidities": list(self.major_comorbidities),
            "recent_clinical_events": list(self.recent_clinical_events),
            "clinical_risks": list(self.clinical_risks),
            "open_operational_concerns": list(self.open_operational_concerns),
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
compact set of already-verified facts about a single patient's chart -- diagnosis, a \
heuristic hospice-relevance classification of those same diagnoses, current benefit period, \
recent visits, recent documentation, open tasks, open billing alerts, and billing status -- \
and you produce a short, discussion-ready HOSPICE CLINICAL PICTURE from ONLY those facts.

This must read like a hospice EMR summary, not a database diagnosis dump. The very first \
thing a nurse, physician, DON, administrator, surveyor, or medical director reads must \
answer "why is this patient hospice-appropriate", never "what is the first diagnosis row".

Non-negotiable rules:
- You NEVER diagnose, invent, or infer any clinical fact not explicitly present in the input.
- You NEVER predict prognosis, and NEVER generate or imply an eligibility, certification, \
recertification, or discharge recommendation of any kind.
- You NEVER invent billing figures, alert details, or task details beyond what is given.
- The `diagnosis_classification` input (primary_hospice_drivers / evidence_of_decline / \
major_comorbidities) already ranks the same diagnoses by hospice relevance -- lead with \
primary_hospice_drivers and evidence_of_decline. Do NOT lead with whichever diagnosis the \
input happens to label "primary_diagnosis" if it is not also a hospice driver; the raw \
diagnosis list belongs later in the summary (major_comorbidities), not the opening sentence.
- If a section has no relevant input facts, return an empty list (or a short factual sentence \
for hospice_clinical_picture noting nothing was provided) rather than inventing filler content.
- Write in plain, concise, professional language suitable for a quick huddle discussion --
short phrases or short sentences, not clinical documentation prose.

Respond ONLY with JSON of the exact shape:
{"hospice_clinical_picture": "<2-3 sentence plain-language narrative answering why this patient \
is hospice-appropriate, leading with hospice drivers and decline evidence, not a diagnosis list>", \
"primary_hospice_drivers": ["<short phrase>", ...], \
"evidence_of_decline": ["<short phrase>", ...], \
"major_comorbidities": ["<short phrase>", ...], \
"recent_clinical_events": ["<short phrase>", ...], \
"clinical_risks": ["<short phrase>", ...], \
"open_operational_concerns": ["<short phrase>", ...]}
"""


def _fallback_summary(context: dict[str, Any]) -> PatientAiSummary:
    """Deterministic, template-based summary built directly from the same
    facts given to the AI path. Always available, even with no Azure
    OpenAI configuration -- guarantees the feature has something to show.
    Leads with the same hospice-relevance classification used to steer the
    AI path, so the fallback never regresses to a diagnosis dump either.
    """
    name = context.get("full_name") or "This patient"
    primary_dx = context.get("primary_diagnosis")
    secondary_dxs = context.get("secondary_diagnoses") or []
    benefit_period = context.get("benefit_period") or {}

    classification = _classify_diagnoses(primary_dx, secondary_dxs)
    drivers = classification["primary_hospice_drivers"]
    decline = classification["evidence_of_decline"]
    major_comorbidities = classification["major_comorbidities"]

    picture_parts: list[str] = []
    if drivers:
        picture_parts.append(
            f"{name} is a hospice patient with a clinical picture driven primarily by {', '.join(drivers).lower()}."
        )
    elif primary_dx:
        picture_parts.append(f"{name}'s hospice-relevant clinical picture is centered on {primary_dx}.")
    else:
        picture_parts.append(f"{name} overview generated from current chart data.")
    if decline:
        picture_parts.append(f"Evidence of decline includes {', '.join(decline).lower()}.")
    if major_comorbidities:
        picture_parts.append(f"Managed alongside {len(major_comorbidities)} additional comorbidity/ies on file.")
    if benefit_period.get("period_number"):
        picture_parts.append(
            f"Currently in benefit period {benefit_period['period_number']} ({benefit_period.get('benefit_type') or 'benefit period'})."
        )
    else:
        picture_parts.append("No current benefit period on file.")
    hospice_clinical_picture = " ".join(picture_parts)

    recent_clinical_events: list[str] = []
    visits = context.get("recent_visits") or []
    if visits:
        latest = visits[0]
        recent_clinical_events.append(
            f"Most recent visit: {latest.get('visit_type') or 'visit'} on {latest.get('visit_datetime') or 'unknown date'}"
        )
    notes = context.get("recent_notes") or []
    if notes:
        recent_clinical_events.append(f"{len(notes)} recent note(s) on file")

    clinical_risks: list[str] = []
    if not benefit_period:
        clinical_risks.append("No current benefit period on file -- verify benefit period status.")
    if not visits:
        clinical_risks.append("No recent visit activity on file.")

    open_operational_concerns: list[str] = []
    for task in context.get("open_tasks") or []:
        label = task.get("task_type") or "Task"
        due = task.get("due_date")
        open_operational_concerns.append(f"[Task] {label}" + (f" (due {due})" if due else ""))
    for alert in context.get("open_alerts") or []:
        alert_type = alert.get("alert_type") or "Alert"
        severity = alert.get("severity")
        outstanding = alert.get("outstanding_amount")
        piece = f"[Billing] {alert_type} alert" + (f" ({severity})" if severity else "")
        if outstanding is not None:
            piece += f" -- ${outstanding} outstanding"
        open_operational_concerns.append(piece)
    if not open_operational_concerns:
        open_operational_concerns.append("No open tasks or billing alerts identified from current chart data.")

    return PatientAiSummary(
        hospice_clinical_picture=hospice_clinical_picture,
        primary_hospice_drivers=tuple(drivers),
        evidence_of_decline=tuple(decline),
        major_comorbidities=tuple(major_comorbidities),
        recent_clinical_events=tuple(recent_clinical_events),
        clinical_risks=tuple(clinical_risks),
        open_operational_concerns=tuple(open_operational_concerns),
        generated_at=datetime.now(timezone.utc).isoformat(),
        model=None,
        ai_generated=False,
    )


def _call_azure_openai(context: dict[str, Any], config: dict[str, str]) -> PatientAiSummary | None:
    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )
    # Compute the same heuristic hospice-relevance classification the
    # fallback path uses and hand it to the model as a grounded hint, so
    # the AI narrative leads with hospice drivers/decline evidence instead
    # of whichever diagnosis the raw context happens to label "primary".
    classification = _classify_diagnoses(
        context.get("primary_diagnosis"), context.get("secondary_diagnoses") or []
    )
    ai_context = {**context, "diagnosis_classification": classification}
    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(ai_context, default=str)},
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

    hospice_clinical_picture = str(parsed.get("hospice_clinical_picture") or "").strip()
    if not hospice_clinical_picture:
        return None

    def _string_list(key: str) -> tuple[str, ...]:
        raw = parsed.get(key)
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    return PatientAiSummary(
        hospice_clinical_picture=hospice_clinical_picture,
        primary_hospice_drivers=_string_list("primary_hospice_drivers"),
        evidence_of_decline=_string_list("evidence_of_decline"),
        major_comorbidities=_string_list("major_comorbidities"),
        recent_clinical_events=_string_list("recent_clinical_events"),
        clinical_risks=_string_list("clinical_risks"),
        open_operational_concerns=_string_list("open_operational_concerns"),
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
