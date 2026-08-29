"""Verified-write engine for the RN ICA "Apply structured finding(s)" flow.

Root cause this exists to fix: the field-merge/apply computation
(applyStructuredFindings.js / applyAllNonConflicting on the frontend) is
entirely client-side. Historically, marking a PatientHarvestedSignal
APPLIED (see harvest_service.review_harvested_signal) was a completely
separate, uncoordinated HTTP call from the RNICA form_data save (PUT
/rnica/{assessment_id}) -- the backend had no mechanism to verify a
destination field write actually landed in the persisted assessment record
before a signal could be marked APPLIED. A signal could therefore be
recorded as APPLIED while its intended chart field was never written, or
was overwritten again before the RN ever saw it -- silent data loss.

This module is the single place that:
  1. Takes the field writes the frontend's apply pass claims to have made
     (section, dotted path, proposed value, write kind) alongside the
     form_data that was just persisted in the SAME request/transaction as
     the field writes (see visits.update_rnica_assessment).
  2. Re-reads the assessment's form_data with a FRESH, uncached SQL SELECT
     (bypassing the SQLAlchemy identity map / session cache) immediately
     after commit, so verification reflects what is truly durable, not
     merely what the in-memory ORM object still holds.
  3. Resolves each claimed write's destination path in that freshly-read
     data and compares it against the proposed value -- scalars/booleans by
     exact equality, arrays by membership.
  4. Aggregates a verified disposition per signal_id: APPLIED only when
     every one of that signal's claimed writes verified as persisted.

Nothing in this module marks anything APPLIED by assumption. A signal with
zero verified writes can never receive "APPLIED" from
compute_signal_dispositions().
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

_PATH_TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _tokenize_path(path: str) -> list[str | int]:
    """Splits a frontend-convention path like "wounds[2].location" into
    ["wounds", 2, "location"]. Mirrors applyStructuredFindings.js's own
    dotted+bracket-index path convention so a claimed write's destination
    can be located in the persisted JSON exactly the way the frontend
    addressed it.
    """
    tokens: list[str | int] = []
    for match in _PATH_TOKEN_RE.finditer(path or ""):
        key, idx = match.group(1), match.group(2)
        if idx is not None:
            tokens.append(int(idx))
        elif key:
            tokens.append(key)
    return tokens


def get_nested_value(data: Any, path: str) -> Any:
    """Reads a dotted/bracket-indexed path out of a plain JSON-shaped dict,
    returning None for any missing/mistyped segment rather than raising --
    a missing destination is a legitimate "not persisted" verification
    outcome, not a bug in this reader.
    """
    current = data
    for token in _tokenize_path(path):
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current) or token < 0:
                return None
            current = current[token]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(token)
        if current is None:
            return current
    return current


@dataclass
class FieldWriteClaim:
    """One destination field write a frontend apply pass claims to have
    made, as reported by RNICA.jsx (built from applyStructuredFindings.js's
    `appliedFields`)."""

    signal_id: str
    section: str
    path: str
    value: Any
    concept_code: str | None = None
    kind: str = "scalar"  # "scalar" | "array_member"


@dataclass
class FieldWriteResult:
    signal_id: str
    section: str
    path: str
    concept_code: str | None
    proposed_value: Any
    persisted_value: Any
    verified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "section": self.section,
            "path": self.path,
            "concept_code": self.concept_code,
            "proposed_value": self.proposed_value,
            "persisted_value": self.persisted_value,
            "verified": self.verified,
        }


def fetch_fresh_form_data(db: Session, assessment_id: UUID) -> dict[str, Any]:
    """Reads form_data with a plain SQL SELECT, deliberately bypassing the
    SQLAlchemy ORM identity map, so verification can never be fooled by an
    in-memory object that merely LOOKS committed. Must be called only
    after the caller's own db.commit() for the write being verified.
    """
    row = db.execute(
        text('SELECT form_data FROM rnica_assessments WHERE id = :id'),
        {"id": str(assessment_id)},
    ).first()
    if row is None:
        return {}
    return row[0] or {}


def verify_field_writes(
    persisted_form_data: dict[str, Any],
    claims: list[FieldWriteClaim],
) -> list[FieldWriteResult]:
    """Resolves every claimed write's destination path in the freshly-read
    persisted form_data and compares it against the proposed value."""
    results: list[FieldWriteResult] = []
    for claim in claims:
        section_data = (persisted_form_data or {}).get(claim.section)
        actual = get_nested_value(section_data, claim.path)
        if claim.kind == "array_member":
            verified = isinstance(actual, list) and claim.value in actual
        else:
            verified = actual == claim.value
        results.append(
            FieldWriteResult(
                signal_id=claim.signal_id,
                section=claim.section,
                path=claim.path,
                concept_code=claim.concept_code,
                proposed_value=claim.value,
                persisted_value=actual,
                verified=verified,
            )
        )
    return results


def compute_signal_dispositions(
    field_results: list[FieldWriteResult],
    conflict_signal_ids: set[str] | None = None,
) -> dict[str, str]:
    """Aggregates per-field verification results into one verified
    disposition per signal_id.

      - APPLIED: this signal had >=1 claimed write, ALL verified, and it
        has no unresolved conflict on another finding.
      - PARTIALLY_APPLIED: some (not all) claimed writes verified, OR all
        verified but the signal also has a separate unresolved conflict.
      - FAILED: this signal had >=1 claimed write and NONE verified.
      - CONFLICT: this signal had zero claimed writes and >=1 conflict
        (every finding was blocked before anything was attempted).

    A signal with zero claimed writes and zero conflicts (e.g. every
    finding was HISTORICAL/NEGATED -- nothing actionable) is deliberately
    left out of the returned map; the caller decides how to record "nothing
    to apply" (see visits.update_rnica_assessment), since that is not a
    verified-write outcome this function should guess at.
    """
    conflict_signal_ids = conflict_signal_ids or set()
    by_signal: dict[str, list[FieldWriteResult]] = {}
    for r in field_results:
        by_signal.setdefault(r.signal_id, []).append(r)

    dispositions: dict[str, str] = {}
    for signal_id, results in by_signal.items():
        verified_count = sum(1 for r in results if r.verified)
        has_conflict = signal_id in conflict_signal_ids
        if verified_count == 0:
            dispositions[signal_id] = "FAILED"
        elif verified_count == len(results) and not has_conflict:
            dispositions[signal_id] = "APPLIED"
        else:
            dispositions[signal_id] = "PARTIALLY_APPLIED"

    # Signals that conflicted on every finding and never attempted a write.
    for signal_id in conflict_signal_ids:
        if signal_id not in dispositions:
            dispositions[signal_id] = "CONFLICT"

    return dispositions
