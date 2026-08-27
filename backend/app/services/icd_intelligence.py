from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "lcd" / "diagnosis_recommendation_hints.json"


def _flatten_json_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def _load_guidance() -> dict[str, Any]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.lower().strip()
    return "".join(ch for ch in cleaned if ch.isalnum() or ch.isspace())


def gather_patient_evidence(
    db: Session | None,
    patient_id: str | None,
    *,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate real patient evidence from diagnosis_sources and clinical_notes into one text corpus.

    This keeps the engine tied to actual patient data when the request includes a patient_id,
    while preserving the existing free-text fallback when no patient record is available.
    """
    if not db or not patient_id:
        return {"text": "", "diagnosis_sources": [], "clinical_notes": [], "source_count": 0}

    evidence_parts: list[str] = []
    diagnosis_rows: list[dict[str, Any]] = []
    note_rows: list[dict[str, Any]] = []
    diagnosis_summaries: list[dict[str, Any]] = []

    diagnosis_sql = """
        SELECT source, dx_type, icd_code, description, documented_at
        FROM diagnosis_sources
        WHERE patient_id = :patient_id
          AND is_active = true
        ORDER BY documented_at DESC NULLS LAST
        LIMIT 20
    """
    try:
        diagnosis_rows = db.execute(text(diagnosis_sql), {"patient_id": patient_id}).mappings().all()
    except Exception:
        db.rollback()
        diagnosis_rows = []

    for row in diagnosis_rows:
        source = row.get("source")
        dx_type = row.get("dx_type")
        icd_code = row.get("icd_code")
        description = row.get("description")
        evidence = " ".join(part for part in [source, dx_type, icd_code, description] if part)
        if evidence:
            evidence_parts.append(evidence)
            diagnosis_summaries.append({
                "source": source,
                "dx_type": dx_type,
                "icd_code": icd_code,
                "description": description,
            })

    note_sql = """
        SELECT note_type, discipline, content, plan_of_care_updates
        FROM clinical_notes
        WHERE patient_id = :patient_id
    """
    params: dict[str, Any] = {"patient_id": patient_id}
    if tenant_id:
        note_sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id
    note_sql += " ORDER BY updated_at DESC NULLS LAST LIMIT 20"

    try:
        note_rows = db.execute(text(note_sql), params).mappings().all()
    except Exception:
        # A failed statement leaves the session's transaction aborted for
        # every subsequent query on this same request/session -- roll back
        # so callers (e.g. list_pending_structured_findings, right after
        # this in the /intelligence endpoint) don't inherit a poisoned
        # transaction and fail with an unrelated-looking 500.
        db.rollback()
        note_rows = []

    for row in note_rows:
        text_values: list[str] = []
        for key in ["content", "note_type", "discipline"]:
            candidate = row.get(key)
            if candidate:
                text_values.append(_flatten_json_text(candidate))
        # observed_data / patient_reported / caregiver_reported / assessment
        # are nested keys inside the `content` JSON column, not their own
        # SQL columns -- only plan_of_care_updates is a real top-level column.
        content_payload = row.get("content") if isinstance(row.get("content"), dict) else {}
        for key in ["observed_data", "patient_reported", "caregiver_reported", "assessment"]:
            candidate = content_payload.get(key)
            if candidate:
                text_values.append(_flatten_json_text(candidate))
        plan_updates = row.get("plan_of_care_updates")
        if plan_updates:
            text_values.append(_flatten_json_text(plan_updates))
        note_text = " ".join(part for part in text_values if part)
        if note_text:
            evidence_parts.append(note_text)

    return {
        "text": " \n ".join(part for part in evidence_parts if part),
        "diagnosis_sources": diagnosis_summaries,
        "clinical_notes": note_rows,
        "source_count": len(diagnosis_summaries) + len(note_rows),
    }


def recommend_icd_candidates(
    text: str | None,
    *,
    max_results: int = 5,
    patient_evidence: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return ICD recommendation candidates by matching free-text evidence to the shared LCD guidance config.

    This is intentionally conservative: it is a recommendation-only baseline for physician review,
    not an automated final diagnosis engine.
    """
    evidence_text = text or ""
    if patient_evidence:
        patient_text = patient_evidence.get("text", "")
        if patient_text:
            evidence_text = "\n".join(part for part in [evidence_text, patient_text] if part)
    if not evidence_text:
        return []

    guidance = _load_guidance()
    normalized = _normalize_text(evidence_text)
    if not normalized:
        return []

    matches: list[dict[str, Any]] = []
    for category in guidance.get("categories", []):
        keywords = category.get("hnp_keywords", [])
        matched: list[str] = []
        score = 0
        for keyword in keywords:
            normalized_keyword = _normalize_text(keyword)
            if not normalized_keyword:
                continue
            if normalized_keyword in normalized:
                matched.append(keyword)
                score += 2
        if not matched:
            continue

        examples = category.get("icd10_family_examples", [])
        confidence = min(0.55 + (score / max(len(keywords) * 2, 1)) * 0.45, 0.99)
        matches.append(
            {
                "category_key": category.get("category_key"),
                "display_name": category.get("display_name"),
                "matched_keywords": matched,
                "score": score,
                "confidence": round(confidence, 2),
                "icd10_family_examples": examples,
            }
        )

    matches.sort(key=lambda item: (-item["score"], item["display_name"]))
    return matches[: max_results]


def primary_dx_guardrails() -> dict[str, Any]:
    guidance = _load_guidance()
    return {
        "deny_prefixes": guidance.get("primary_dx_guardrail", {}).get("deny_prefixes", []),
        "note": guidance.get("primary_dx_guardrail", {}).get("note", ""),
    }
