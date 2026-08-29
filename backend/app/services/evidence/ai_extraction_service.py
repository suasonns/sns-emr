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
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.services.evidence.structured_findings import concept_prompt_catalog, validate_findings

logger = logging.getLogger("sns_emr")

DEFAULT_TIMEOUT_SECONDS = 90.0
# 30s was found (2026-08-29) to be too short in practice for this model on
# a real chunked-document call, causing the same class of silent failure
# fixed in note_draft_service.py: a slow-but-successful model response is
# indistinguishable from "not configured" once it times out, so a chunk
# can silently produce zero signals with no visible error.
# Per-call ceiling sent to the model. NOTE: this used to be applied as a
# single hard truncation of the WHOLE source text (`text[:12000]`), which
# silently discarded everything past character 12,000 -- for a real,
# multi-encounter document export (tens of thousands of characters), that
# is the majority of the document, dropped with no signal to anyone. Real
# case: a 63KB H&P/referral export where an explicit wound-care order
# ("wound care order for L side of buttocks and R foot") sat at character
# offset ~58,735 -- structurally unreachable under the old single-slice
# call, on every run, forever. `_split_into_chunks` below now walks the
# FULL text in windows of this size instead of throwing the rest away.
MAX_SOURCE_TEXT_CHARS = 12000


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
- SEPARATELY from the above narrative-worthiness rule, you have a SECOND, INDEPENDENT \
  job: systematically scan the ENTIRE source text -- not just the parts that triggered \
  a narrative signal above -- for every discrete clinical fact, of ANY acuity \
  (routine/stable/normal findings count exactly the same as declining/abnormal ones), \
  that maps to one of the fixed concept_code values in the catalog below. A patient \
  documented as "alert and oriented x4" or "gait steady, no assistive device" is just \
  as extractable as one documented as obtunded or unsteady -- normal/stable findings \
  are RN-documented facts too, and must not be silently skipped just because they \
  aren't clinically noteworthy. If a routine/stable fact maps to a catalog concept but \
  has no accompanying narrative signal, still emit a minimal signal entry for it \
  (signal_text can be a short factual restatement, e.g. "Patient documented as alert \
  and oriented x4") so its structured_findings are captured -- do not drop a \
  catalog-mappable fact merely because it would not otherwise clear the bar for a \
  decline-focused narrative signal.

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
in this excerpt maps to the catalog. Remember: this catalog-matching duty applies to \
EVERY signal you emit, including the minimal "routine fact" signals described above --
it is not limited to signals about decline or new problems.
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


@dataclass(frozen=True)
class ExtractionDiagnostics:
    """Raw-vs-validated structured_findings counts for one extract_signals()
    call. Used by structured_findings_reprocess_service to report how many
    model-proposed findings were discarded by validate_findings() (unknown
    concept_code, out-of-range value, malformed shape, etc) -- observability
    that plain `extract_signals()` callers (harvest_service) don't need.
    """

    raw_findings_count: int = 0
    rejected_findings_count: int = 0
    # False when the call could not actually be evaluated by the model at
    # all (missing Azure OpenAI config, network/HTTP error, unparsable
    # response) -- as opposed to a genuine "model ran, found nothing"
    # result, which is `succeeded=True` with 0 signals/findings. Callers
    # that need to distinguish a real failure from a legitimate empty
    # result (structured_findings_reprocess_service) must check this.
    succeeded: bool = True
    error: str | None = None

    # ── Full-document coverage audit ─────────────────────────────────────
    # The document is walked in full via `_split_into_chunks` -- these
    # counts are the receipt that 100% of the source text was actually
    # sent to the model, not silently discarded past a hard-coded
    # truncation limit (see MAX_SOURCE_TEXT_CHARS). `succeeded` is set
    # False and `error` records which chunks failed whenever ANY chunk
    # could not be processed -- completion is never reported as clean when
    # coverage was partial, even if some chunks did succeed.
    total_chars: int = 0
    chunk_count: int = 0
    chunks_processed: int = 0
    chunks_skipped: int = 0


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

    signals, _diagnostics = _extract_signals_impl(
        text=text, discipline=discipline, note_type=note_type, source_type=source_type
    )
    return signals


def extract_signals_with_diagnostics(
    *,
    text: str,
    discipline: str | None = None,
    note_type: str | None = None,
    source_type: str,
) -> tuple[list[ExtractedSignal], ExtractionDiagnostics]:
    """Same as `extract_signals`, but also returns raw-vs-validated
    structured_findings counts. Never raises -- see `extract_signals`.
    """

    return _extract_signals_impl(
        text=text, discipline=discipline, note_type=note_type, source_type=source_type
    )


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split `text` into consecutive windows of at most `max_chars`, covering
    100% of the input (unlike the old single `text[:max_chars]` truncation).
    Prefers to break at a paragraph or sentence boundary near the end of a
    window so a single clinical statement isn't split mid-sentence, but
    always makes forward progress even if no such boundary exists.
    """

    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            candidate = text.rfind("\n\n", start, end)
            if candidate == -1 or candidate <= start + max_chars // 2:
                candidate = text.rfind(". ", start, end)
            if candidate != -1 and candidate > start + max_chars // 2:
                end = candidate + 1
        chunks.append(text[start:end])
        start = end
    return chunks


def _call_model(
    chunk_text: str, *, discipline: str | None, note_type: str | None, source_type: str
) -> tuple[list[Any] | None, str | None]:
    """Call the model for one chunk. Returns (signals_raw list, error) --
    signals_raw is None only on failure (never raises)."""

    config = _azure_openai_config()
    if config is None:
        return None, "Azure OpenAI not configured"

    user_context = (
        f"source_type: {source_type}\n"
        f"discipline: {discipline or 'unknown'}\n"
        f"note_type: {note_type or 'unknown'}\n"
        f"--- DOCUMENTATION TEXT ---\n{chunk_text}"
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
    except Exception as exc:
        logger.exception("evidence_harvester: AI extraction call failed source_type=%s", source_type)
        return None, str(exc)[:500]

    signals_raw = parsed.get("signals") if isinstance(parsed, dict) else None
    if not isinstance(signals_raw, list):
        return None, "Model response missing a 'signals' list"
    return signals_raw, None


def _extract_signals_impl(
    *,
    text: str,
    discipline: str | None,
    note_type: str | None,
    source_type: str,
) -> tuple[list[ExtractedSignal], ExtractionDiagnostics]:
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        # Nothing to extract from -- a legitimate (not a failure) empty result.
        return [], ExtractionDiagnostics()

    finding_source_type = _resolve_finding_source_type(source_type, note_type)

    config = _azure_openai_config()
    signals: list[ExtractedSignal] = []
    seen_signal_keys: set[str] = set()
    seen_finding_keys: set[tuple[str, str]] = set()
    raw_findings_count = 0
    validated_findings_count = 0
    any_chunk_succeeded = False
    last_error: str | None = None

    total_chars = len(cleaned_text)
    chunks = _split_into_chunks(cleaned_text, MAX_SOURCE_TEXT_CHARS)
    chunk_count = len(chunks)
    chunks_processed = 0
    chunks_skipped = 0
    skipped_chunk_errors: list[str] = []

    if config is None:
        # The LLM pass is unavailable, but the deterministic safety net
        # below must NOT depend on it -- explicit wound-care language is
        # still detected without any model call at all. Every chunk counts
        # as skipped -- coverage was NOT achieved, and this must not be
        # reported as a clean completion.
        logger.info(
            "evidence_harvester: AI extraction skipped (Azure OpenAI not configured) "
            "source_type=%s -- deterministic safety net still runs",
            source_type,
        )
        last_error = "Azure OpenAI not configured"
        chunks_skipped = chunk_count
        skipped_chunk_errors.append(last_error)
    else:
        for chunk in chunks:
            signals_raw, error = _call_model(
                chunk, discipline=discipline, note_type=note_type, source_type=source_type
            )
            if signals_raw is None:
                last_error = error
                chunks_skipped += 1
                skipped_chunk_errors.append(error or "unknown error")
                logger.error(
                    "evidence_harvester: chunk skipped (coverage incomplete) "
                    "source_type=%s chunk_chars=%d error=%s",
                    source_type,
                    len(chunk),
                    error,
                )
                continue
            chunks_processed += 1
            any_chunk_succeeded = True

            for item in signals_raw:
                if isinstance(item, dict) and isinstance(item.get("structured_findings"), list):
                    raw_findings_count += len(item["structured_findings"])
                try:
                    signal = _parse_signal(item, finding_source_type=finding_source_type)
                except Exception:
                    logger.warning("evidence_harvester: skipping malformed signal item=%r", item)
                    continue
                if signal is None:
                    continue
                # De-dupe repeated signals across chunks/boilerplate (e.g. the
                # same demographic header or a fact restated in multiple visit
                # notes concatenated into one document) by signal_key, keeping
                # only the first occurrence's structured_findings.
                if signal.signal_key in seen_signal_keys:
                    continue
                seen_signal_keys.add(signal.signal_key)
                signals.append(signal)
                for f in signal.structured_findings:
                    fkey = (f.get("concept_code"), str(f.get("value")))
                    if fkey not in seen_finding_keys:
                        seen_finding_keys.add(fkey)
                        validated_findings_count += 1

    # Deterministic wound-language safety net -- runs on the FULL,
    # untruncated original text regardless of chunking/model coverage/
    # configuration, so explicit clinical wound-care language can never be
    # silently dropped again (see MAX_SOURCE_TEXT_CHARS comment above for
    # the real incident this fixes). Only ever adds a candidate when the
    # LLM pass(es) above did not already surface the same concept+location.
    deterministic_signals = _detect_deterministic_wound_signals(
        cleaned_text, finding_source_type=finding_source_type, seen_finding_keys=seen_finding_keys
    )
    for signal in deterministic_signals:
        if signal.signal_key in seen_signal_keys:
            continue
        seen_signal_keys.add(signal.signal_key)
        signals.append(signal)
        for f in signal.structured_findings:
            fkey = (f.get("concept_code"), str(f.get("value")))
            seen_finding_keys.add(fkey)
        raw_findings_count += len(signal.structured_findings)
        validated_findings_count += len(signal.structured_findings)

    # Hospice-priority deterministic pre-scan (falls, oxygen, weight loss,
    # dysphagia, infections backstop -- see section docstring for the full
    # 13-category priority list and disclosed gaps for categories with no
    # existing chart destination).
    priority_signals = _detect_priority_deterministic_signals(
        cleaned_text, finding_source_type=finding_source_type, seen_finding_keys=seen_finding_keys
    )
    for signal in priority_signals:
        if signal.signal_key in seen_signal_keys:
            continue
        seen_signal_keys.add(signal.signal_key)
        signals.append(signal)
        for f in signal.structured_findings:
            fkey = (f.get("concept_code"), str(f.get("value")))
            seen_finding_keys.add(fkey)
        raw_findings_count += len(signal.structured_findings)
        validated_findings_count += len(signal.structured_findings)

    # Refuse to report clean completion when coverage was partial. Findings
    # already extracted (from successful chunks and/or the deterministic
    # safety net) are ALWAYS still returned -- partial coverage must never
    # cause already-found evidence to be discarded, only the "everything
    # was checked" claim to be withheld.
    coverage_complete = config is not None and chunks_skipped == 0 and chunk_count > 0
    if not any_chunk_succeeded and not deterministic_signals and not priority_signals and not coverage_complete:
        return [], ExtractionDiagnostics(
            succeeded=False,
            error=last_error,
            total_chars=total_chars,
            chunk_count=chunk_count,
            chunks_processed=chunks_processed,
            chunks_skipped=chunks_skipped,
        )

    diagnostics = ExtractionDiagnostics(
        raw_findings_count=raw_findings_count,
        rejected_findings_count=max(0, raw_findings_count - validated_findings_count),
        succeeded=coverage_complete,
        error=None if coverage_complete else "; ".join(skipped_chunk_errors)[:500] or last_error,
        total_chars=total_chars,
        chunk_count=chunk_count,
        chunks_processed=chunks_processed,
        chunks_skipped=chunks_skipped,
    )
    return signals, diagnostics


# ═══════════════════════ Deterministic wound safety net ═══════════════════
# The LLM extraction above is the primary path, but it is a probabilistic
# model and must never be the ONLY thing standing between explicit,
# unambiguous clinical wound-care language and a structured finding. This
# section is a small, rule-based (non-LLM) scanner that runs on every
# extraction call and independently detects the same small set of
# unambiguous wound-related terms every time, with no model variance.
#
# It deliberately does the bare minimum: SKIN_WOUND_PRESENT + a
# source-supported anatomic location, nothing else. It never invents
# stage/type/dimensions/drainage/odor/treatment -- those remain blank for
# RN assessment, exactly like the LLM path.

_WOUND_TRIGGER_RE = re.compile(
    r"wound[\s-]*care|pressure\s*injur\w*|pressure\s*ulcer\w*|skin\s*ulcer\w*|decubitus|\bwound\b",
    re.IGNORECASE,
)

# Ordered (most specific first) anatomic-site patterns. Written to tolerate
# real-world OCR/EHR-export text where words are glued together with no
# whitespace (e.g. "L sideof buttocksandRfoot" for "L side of buttocks and
# R foot") -- `\s*` matches zero-or-more spaces at each junction so the same
# pattern matches both normally-spaced and glued text.
# (regex, location_label, family) -- `family` groups patterns that describe
# the same anatomic region at different specificity (e.g. "left buttock"
# vs. the bare "buttock" fallback) so only the FIRST (most specific) match
# per family is kept per trigger window -- otherwise a single documented
# site (e.g. "left buttock") would also fire the generic "buttock"
# fallback and create a second, redundant wound candidate for the same
# site.
_SITE_PATTERNS: tuple[tuple[re.Pattern, str, str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), location, family)
    for pattern, location, family in [
        (r"\bL\s*side\s*of\s*buttock\w*", "left buttock", "buttock"),
        (r"\bR\s*side\s*of\s*buttock\w*", "right buttock", "buttock"),
        (r"\bleft\s*(?:side\s*of\s*)?buttock\w*", "left buttock", "buttock"),
        (r"\bright\s*(?:side\s*of\s*)?buttock\w*", "right buttock", "buttock"),
        (r"and\s*R\s*foot\b", "right foot", "foot"),
        (r"and\s*L\s*foot\b", "left foot", "foot"),
        (r"\bright\s*foot\b|\bR\s*foot\b", "right foot", "foot"),
        (r"\bleft\s*foot\b|\bL\s*foot\b", "left foot", "foot"),
        (r"\bright\s*heel\b|\bR\s*heel\b", "right heel", "heel"),
        (r"\bleft\s*heel\b|\bL\s*heel\b", "left heel", "heel"),
        (r"\bsacrum\b", "sacrum", "sacrum"),
        (r"\bcoccyx\b", "coccyx", "coccyx"),
        (r"\bright\s*ankle\b", "right ankle", "ankle"),
        (r"\bleft\s*ankle\b", "left ankle", "ankle"),
        (r"\bbuttock\w*", "buttock", "buttock"),
        (r"\bfoot\b|\bfeet\b", "foot", "foot"),
    ]
)

_NEGATION_TERMS = ("denies", "no wound", "without wound", "not present", "no evidence of", "ruled out")
_HISTORICAL_TERMS = ("history of", "resolved", "healed", "previously had", "prior wound", "old wound")
_UNCERTAIN_TERMS = ("possible", "suspect", "questionable", "uncertain", "?wound", "rule out")


def _classify_assertion(window_lower: str) -> str:
    if any(t in window_lower for t in _NEGATION_TERMS):
        return "NEGATED"
    if any(t in window_lower for t in _HISTORICAL_TERMS):
        return "HISTORICAL"
    if any(t in window_lower for t in _UNCERTAIN_TERMS):
        return "UNCERTAIN"
    return "CURRENT"


@dataclass(frozen=True)
class WoundCandidate:
    location: str | None  # None when trigger language found but no site identified
    assertion_status: str
    source_excerpt: str
    outcome: str  # diagnostic outcome, see module docstring item 8 in the fix request


def detect_wound_candidates(text: str) -> list[WoundCandidate]:
    """Scan `text` for explicit wound-related clinical language and return
    one candidate per distinct (location, assertion_status) pair found.
    Every candidate ends in a recorded outcome -- nothing is silently
    dropped. Never raises; returns [] for empty/None text.
    """

    if not text:
        return []

    candidates: dict[tuple[str | None, str], WoundCandidate] = {}
    for trigger in _WOUND_TRIGGER_RE.finditer(text):
        window_start = max(0, trigger.start() - 80)
        window_end = min(len(text), trigger.end() + 250)
        window = text[window_start:window_end]
        assertion = _classify_assertion(window.lower())

        found_any_site = False
        matched_families: set[str] = set()
        for site_re, location, family in _SITE_PATTERNS:
            if family in matched_families:
                continue
            m = site_re.search(window)
            if not m:
                continue
            found_any_site = True
            matched_families.add(family)
            key = (location, assertion)
            if key in candidates:
                continue
            excerpt_start = max(0, window_start + m.start() - 40)
            excerpt_end = min(len(text), window_start + m.end() + 40)
            excerpt = text[excerpt_start:excerpt_end].strip()
            outcome = "STRUCTURED_FINDING_CREATED" if assertion == "CURRENT" else f"REJECTED_{assertion}"
            candidates[key] = WoundCandidate(
                location=location,
                assertion_status=assertion,
                source_excerpt=excerpt[:300],
                outcome=outcome,
            )

        if not found_any_site:
            key = (None, assertion)
            if key not in candidates:
                candidates[key] = WoundCandidate(
                    location=None,
                    assertion_status=assertion,
                    source_excerpt=window.strip()[:300],
                    outcome="REJECTED_NO_DESTINATION",
                )

    return list(candidates.values())


def _detect_deterministic_wound_signals(
    text: str,
    *,
    finding_source_type: str,
    seen_finding_keys: set[tuple[str, str]],
) -> list[ExtractedSignal]:
    signals: list[ExtractedSignal] = []
    for candidate in detect_wound_candidates(text):
        if candidate.location is None or candidate.assertion_status != "CURRENT":
            # Explicit wound language exists but is negated/historical/
            # uncertain, or has no identifiable site -- logged via
            # `candidate.outcome` for diagnostics, never silently dropped,
            # but does NOT create a chart write (nothing invented).
            logger.info(
                "evidence_harvester: deterministic wound scan outcome=%s assertion=%s "
                "excerpt=%r",
                candidate.outcome,
                candidate.assertion_status,
                candidate.source_excerpt,
            )
            continue

        fkey = ("SKIN_WOUND_PRESENT", candidate.location)
        if fkey in seen_finding_keys:
            logger.info(
                "evidence_harvester: deterministic wound candidate location=%r already "
                "found by model pass -- DUPLICATE_SUPPRESSED",
                candidate.location,
            )
            continue

        raw_finding = {
            "concept_code": "SKIN_WOUND_PRESENT",
            "value": candidate.location,
            "source_excerpt": candidate.source_excerpt,
            "confidence": 0.9,
            "assertion_status": "CURRENT",
            "subject": "PATIENT",
        }
        validated = validate_findings([raw_finding], source_type=finding_source_type)
        if not validated:
            continue

        location_slug = re.sub(r"[^a-z0-9]+", "_", candidate.location.lower()).strip("_")
        signals.append(
            ExtractedSignal(
                signal_key=f"deterministic_wound_{location_slug}"[:128],
                signal_text=(
                    f"Deterministic wound-care language detected for {candidate.location} "
                    "(rule-based safety net, independent of the AI model pass)."
                ),
                original_text_excerpt=candidate.source_excerpt,
                trend=None,
                confidence=0.9,
                clinical_system="skin",
                requires_idg_review=True,
                requires_poc_review=False,
                structured_findings=tuple(f.to_dict() for f in validated),
            )
        )
    return signals


# ═══════════════ Hospice-priority deterministic pre-scan ═══════════════
# Not all clinical content is equally decision-critical for hospice. This
# section runs a small set of rule-based (non-LLM) detectors for the
# categories that most directly affect eligibility/plan-of-care and are
# too clinically important to depend solely on an LLM's coverage of a
# large multi-page document. They run BEFORE/alongside the model pass, on
# the FULL untruncated text, in this priority order:
#   1 Wounds (see detect_wound_candidates above)  2 Falls  3 Oxygen
#   4 PPS  5 KPS  6 ADLs  7 Weight loss  8 Dysphagia  9 Tube feeding
#   10 CHF EF  11 COPD oxygen needs  12 Infections  13 Hospitalizations
#
# Categories 4/5/9/10/13 (PPS, KPS, tube feeding, CHF ejection fraction,
# hospitalizations) and 6 (ADLs) have NO existing CONCEPT_REGISTRY
# destination / are too context-dependent to safely infer a discrete
# value from a keyword match alone (e.g. ADL assistance level is a 5-point
# scale that cannot be guessed from a keyword). For those, this scanner
# still detects and logs the trigger (so the evidence is never silently
# missed) but deliberately creates NO structured finding -- inventing a
# value here would violate the "never invent unsupported facts" rule just
# as badly as skipping it silently. This is a real, disclosed gap, not a
# claim of full coverage.
_FALLS_COUNT_RE = re.compile(
    r"(\d+)\s*falls?\b(?:[^.]{0,40}?(?:90\s*day|past|last)\s*(?:\d+\s*)?(?:day|month))?",
    re.IGNORECASE,
)
_OXYGEN_LPM_RE = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*(?:l|liters?|lpm)\b[^.]{0,40}?(?:oxygen|o2\b|nasal\s*cannula))"
    r"|(?:(?:oxygen|o2\b|nasal\s*cannula)[^.]{0,40}?(\d+(?:\.\d+)?)\s*(?:l|liters?|lpm)\b)",
    re.IGNORECASE,
)
_WEIGHT_LOSS_RE = re.compile(r"weight\s*loss", re.IGNORECASE)
_WEIGHT_AMOUNT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:lb|lbs|pounds|kg)\b", re.IGNORECASE)
_DYSPHAGIA_RE = re.compile(r"\bdysphagia\b|difficulty\s+swallowing|trouble\s+swallowing", re.IGNORECASE)
_UTI_RE = re.compile(r"\bUTI\b|urinary\s*tract\s*infection", re.IGNORECASE)
_RESPIRATORY_INFECTION_RE = re.compile(r"\bpneumonia\b|respiratory\s*(?:tract\s*)?infection|bronchitis", re.IGNORECASE)
_SEPSIS_RE = re.compile(r"\bsepsis\b|\bseptic\b", re.IGNORECASE)
_WOUND_INFECTION_RE = re.compile(r"infected\s*wound|wound\s*infection", re.IGNORECASE)

# Detected but no safe CONCEPT_REGISTRY destination exists yet -- logged
# only, never a structured finding. Flagged to the user as a real gap.
_PPS_TRIGGER_RE = re.compile(r"\bPPS\b|palliative\s*performance\s*scale", re.IGNORECASE)
_KPS_TRIGGER_RE = re.compile(r"\bKPS\b|karnofsky", re.IGNORECASE)
_TUBE_FEEDING_RE = re.compile(r"\bPEG\s*tube\b|feeding\s*tube|tube\s*feeding|\bG-?tube\b", re.IGNORECASE)
_CHF_EF_RE = re.compile(r"ejection\s*fraction|\bEF\s*\d{1,3}\s*%|\bEF\s*\d{1,3}\s*-\s*\d{1,3}\s*%", re.IGNORECASE)
_HOSPITALIZATION_RE = re.compile(
    r"hospitali[sz]ation|admitted\s*to\s*(?:the\s*)?hospital|\bER\s*visit\b|emergency\s*(?:room|department)\s*visit",
    re.IGNORECASE,
)


def _simple_presence_signal(
    *,
    signal_key: str,
    label: str,
    clinical_system: str,
    concept_code: str,
    excerpt: str,
    finding_source_type: str,
    seen_finding_keys: set[tuple[str, str]],
    value: Any = True,
) -> ExtractedSignal | None:
    fkey = (concept_code, str(value))
    if fkey in seen_finding_keys:
        return None
    raw_finding = {
        "concept_code": concept_code,
        "value": value,
        "source_excerpt": excerpt,
        "confidence": 0.85,
        "assertion_status": "CURRENT",
        "subject": "PATIENT",
    }
    validated = validate_findings([raw_finding], source_type=finding_source_type)
    if not validated:
        return None
    return ExtractedSignal(
        signal_key=signal_key[:128],
        signal_text=f"Deterministic hospice-priority detector: {label}.",
        original_text_excerpt=excerpt,
        trend=None,
        confidence=0.85,
        clinical_system=clinical_system,
        requires_idg_review=True,
        requires_poc_review=False,
        structured_findings=tuple(f.to_dict() for f in validated),
    )


def _detect_priority_deterministic_signals(
    text: str,
    *,
    finding_source_type: str,
    seen_finding_keys: set[tuple[str, str]],
) -> list[ExtractedSignal]:
    """Rule-based pre-scan for the hospice-priority categories (falls,
    oxygen, weight loss, dysphagia, infections -- see module docstring
    above for full priority list and the disclosed gaps). Never raises;
    returns [] on empty text.
    """

    if not text:
        return []

    signals: list[ExtractedSignal] = []
    seen_keys_local = set(seen_finding_keys)

    def _add(signal: ExtractedSignal | None) -> None:
        if signal is None:
            return
        for f in signal.structured_findings:
            seen_keys_local.add((f.get("concept_code"), str(f.get("value"))))
        signals.append(signal)

    # 2. Falls
    for m in _FALLS_COUNT_RE.finditer(text):
        window = text[max(0, m.start() - 60) : min(len(text), m.end() + 60)]
        assertion = _classify_assertion(window.lower())
        if assertion != "CURRENT":
            continue
        count = int(m.group(1))
        _add(
            _simple_presence_signal(
                signal_key=f"deterministic_falls_{count}",
                label=f"{count} fall(s) documented",
                clinical_system="functional",
                concept_code="MSK_FALLS_LAST_90_DAYS",
                excerpt=window.strip()[:300],
                finding_source_type=finding_source_type,
                seen_finding_keys=seen_keys_local,
                value=count,
            )
        )

    # 3. Oxygen (liters per minute via nasal cannula -- the common case)
    for m in _OXYGEN_LPM_RE.finditer(text):
        window = text[max(0, m.start() - 60) : min(len(text), m.end() + 60)]
        assertion = _classify_assertion(window.lower())
        if assertion != "CURRENT":
            continue
        lpm_raw = m.group(1) or m.group(2)
        try:
            lpm = float(lpm_raw)
        except (TypeError, ValueError):
            continue
        excerpt = window.strip()[:300]
        _add(
            _simple_presence_signal(
                signal_key="deterministic_oxygen_in_use",
                label="Supplemental oxygen use documented",
                clinical_system="respiratory",
                concept_code="RESP_OXYGEN_NASAL_CANNULA",
                excerpt=excerpt,
                finding_source_type=finding_source_type,
                seen_finding_keys=seen_keys_local,
                value=lpm,
            )
        )

    # 7. Weight loss
    for m in _WEIGHT_LOSS_RE.finditer(text):
        window_start = max(0, m.start() - 40)
        window_end = min(len(text), m.end() + 80)
        window = text[window_start:window_end]
        assertion = _classify_assertion(window.lower())
        if assertion != "CURRENT":
            continue
        amount_match = _WEIGHT_AMOUNT_RE.search(window)
        value = amount_match.group(0) if amount_match else "Weight loss documented"
        _add(
            _simple_presence_signal(
                signal_key="deterministic_weight_loss",
                label="Weight loss documented",
                clinical_system="nutrition",
                concept_code="NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS",
                excerpt=window.strip()[:300],
                finding_source_type=finding_source_type,
                seen_finding_keys=seen_keys_local,
                value=value[:30],
            )
        )

    # 8. Dysphagia
    for m in _DYSPHAGIA_RE.finditer(text):
        window = text[max(0, m.start() - 60) : min(len(text), m.end() + 60)]
        assertion = _classify_assertion(window.lower())
        if assertion != "CURRENT":
            continue
        _add(
            _simple_presence_signal(
                signal_key="deterministic_dysphagia",
                label="Dysphagia documented",
                clinical_system="nutrition",
                concept_code="NUTR_DYSPHAGIA",
                excerpt=window.strip()[:300],
                finding_source_type=finding_source_type,
                seen_finding_keys=seen_keys_local,
            )
        )

    # 12. Infections (deterministic backstop alongside the LLM catalog)
    for pattern, concept_code, label in (
        (_UTI_RE, "INFECT_CURRENT_UTI", "Current UTI documented"),
        (_RESPIRATORY_INFECTION_RE, "INFECT_CURRENT_RESPIRATORY", "Current respiratory infection documented"),
        (_SEPSIS_RE, "INFECT_CURRENT_SEPSIS", "Current sepsis documented"),
        (_WOUND_INFECTION_RE, "INFECT_CURRENT_WOUND_INFECTION", "Current wound infection documented"),
    ):
        for m in pattern.finditer(text):
            window = text[max(0, m.start() - 60) : min(len(text), m.end() + 60)]
            assertion = _classify_assertion(window.lower())
            if assertion != "CURRENT":
                continue
            _add(
                _simple_presence_signal(
                    signal_key=f"deterministic_{concept_code.lower()}",
                    label=label,
                    clinical_system="infection",
                    concept_code=concept_code,
                    excerpt=window.strip()[:300],
                    finding_source_type=finding_source_type,
                    seen_finding_keys=seen_keys_local,
                )
            )
            break  # one candidate per concept is enough for this backstop

    # 4/5/9/10/13 -- PPS, KPS, tube feeding, CHF EF, hospitalizations: no
    # safe CONCEPT_REGISTRY destination exists today. Detect and log only
    # -- never fabricate a value/field for these. This is a disclosed gap.
    for pattern, name in (
        (_PPS_TRIGGER_RE, "PPS"),
        (_KPS_TRIGGER_RE, "KPS"),
        (_TUBE_FEEDING_RE, "tube feeding"),
        (_CHF_EF_RE, "CHF ejection fraction"),
        (_HOSPITALIZATION_RE, "hospitalization"),
    ):
        m = pattern.search(text)
        if m:
            window = text[max(0, m.start() - 60) : min(len(text), m.end() + 60)].strip()
            logger.info(
                "evidence_harvester: hospice-priority scan detected %s language but no "
                "CONCEPT_REGISTRY destination exists -- REJECTED_NO_DESTINATION excerpt=%r",
                name,
                window[:300],
            )

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
