"""Presentation Readiness Check (Invariant 7).

Single composable PASS/FAIL gate over the invariants that must hold before
an RNICA assessment is presented for RN/clinical review. This module does
NOT re-implement diagnosis resolution, harvest tracking, or LCD/
certification evaluation -- it only reads the existing, already-wired
outputs of those systems (diagnosis_resolver, hospice_clinical_context,
PatientHarvestedSignal, RnicaAssessment.field_provenance) and reports
whether they agree.

Where an invariant's supporting mechanism does not exist yet (narrative
versioning/staleness/single-current-narrative), this check reports that
honestly as an open gap rather than fabricating a passing result. A
consumer must treat ANY non-PASS status (including
NOT_YET_IMPLEMENTED) as blocking presentation, per directive: "No manual
inspection required."
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

# Real, currently-persisted PatientHarvestedSignal.review_status values
# (see app.models.patient_evidence.PatientHarvestedSignal). Any row whose
# value falls outside this set is a signal that has silently fallen out of
# the tracked state machine -- Invariant 3 violation ("no signal may
# disappear").
# Authoritative, closed vocabulary per app.services.evidence.harvest_service
# ("review_status is always exactly one of NEW / APPLIED / DISMISSED --
# never a broader narrative-signal review vocabulary", see
# VALID_SIGNAL_REVIEW_DISPOSITIONS / _KNOWN_REVIEW_STATUSES there). Do not
# add PENDING_REVIEW/ACKNOWLEDGED/ESCALATED here -- no code path sets those;
# the model's own state-machine comment is stale and does not reflect the
# application's actual closed vocabulary.
KNOWN_REVIEW_STATUSES = {"NEW", "APPLIED", "DISMISSED"}
KNOWN_STRUCTURED_FINDINGS_STATUSES = {"PENDING", "COMPLETED", "FAILED"}

PASS = "PASS"
FAIL = "FAIL"
NOT_YET_IMPLEMENTED = "NOT_YET_IMPLEMENTED"


def _check_diagnosis_consistency(db: Session, patient_id: str) -> dict[str, Any]:
    from app.services.diagnosis_resolver import resolve_current_diagnosis_context
    from app.services.hospice_clinical_context import build_hospice_clinical_context

    resolved = resolve_current_diagnosis_context(db, patient_id)
    if not resolved.get("available"):
        return {
            "status": FAIL,
            "reason": f"DIAGNOSIS_RESOLVER_UNAVAILABLE: {resolved.get('unavailable_reason')}",
        }

    context = build_hospice_clinical_context(db, patient_id)
    if not context.get("available"):
        return {
            "status": FAIL,
            "reason": f"HOSPICE_CLINICAL_CONTEXT_UNAVAILABLE: {context.get('unavailable_reason')}",
        }

    authoritative_description = (resolved["primary"].get("description") or "").strip().casefold()

    # 1. hospice_clinical_context.diagnosis_context must echo the same
    #    resolver output verbatim (both now come from the same call in
    #    build_hospice_clinical_context -- this guards against future
    #    drift, not a currently-observed divergence).
    context_primary_description = (
        (context.get("diagnosis_context") or {}).get("primary_diagnosis_description") or ""
    ).strip().casefold()
    if context_primary_description != authoritative_description:
        return {
            "status": FAIL,
            "reason": "STALE_DIAGNOSIS_CONTEXT",
            "detail": {
                "resolver_primary": authoritative_description,
                "clinical_context_primary": context_primary_description,
            },
        }

    # 2. related_conditions.terminal (feeds LCD/certification support via
    #    _build_eligibility_sections) must be the same terminal diagnosis
    #    as the resolver's primary -- this is the exact gap fixed in
    #    _build_related_conditions() (resolver-supplied terminal entry,
    #    not an independently re-derived is_terminal scan).
    terminal_entries = (context.get("related_conditions") or {}).get("terminal") or []
    terminal_description = (terminal_entries[0].get("description") or "").strip().casefold() if terminal_entries else ""
    if terminal_description != authoritative_description:
        return {
            "status": FAIL,
            "reason": "CONTEXT_VERSION_MISMATCH",
            "detail": {
                "resolver_primary": authoritative_description,
                "related_conditions_terminal": terminal_description,
            },
        }

    # 3. certification_support (LCD/certification input) must trace back
    #    to the same disease_burden.primary_diagnosis, which is itself
    #    sourced from related_conditions.terminal above.
    disease_burden_primary = ((context.get("disease_burden") or {}).get("primary_diagnosis") or "").strip().casefold()
    if disease_burden_primary and disease_burden_primary != authoritative_description:
        return {
            "status": FAIL,
            "reason": "CERTIFICATION_INPUT_DIVERGES_FROM_RESOLVER",
            "detail": {
                "resolver_primary": authoritative_description,
                "disease_burden_primary": disease_burden_primary,
            },
        }

    return {"status": PASS, "authoritative_primary_diagnosis": resolved["primary"].get("description")}


def _check_rnica_diagnosis_conflict(db: Session, assessment: Any | None) -> dict[str, Any]:
    if assessment is None:
        return {"status": PASS, "reason": "NO_ASSESSMENT_SUPPLIED"}
    from app.api.visits import _build_chart_diagnosis_sync  # local import avoids a circular import at module load

    sync = _build_chart_diagnosis_sync(db, assessment)
    if sync is None:
        return {"status": PASS, "reason": "NOTHING_TO_RECONCILE_OR_LOCKED"}
    if sync.get("matches") is False:
        return {
            "status": FAIL,
            "reason": "PRIMARY_DIAGNOSIS_DIVERGENCE",
            "detail": sync,
        }
    return {"status": PASS}


def _check_harvest_reconciliation(db: Session, patient_id: str) -> dict[str, Any]:
    from app.models.patient_evidence import PatientHarvestedSignal

    rows = db.query(PatientHarvestedSignal).filter(PatientHarvestedSignal.patient_id == patient_id).all()
    unknown_review_status = [str(r.id) for r in rows if r.review_status not in KNOWN_REVIEW_STATUSES]
    unknown_findings_status = [
        str(r.id) for r in rows if r.structured_findings_status not in KNOWN_STRUCTURED_FINDINGS_STATUSES
    ]
    if unknown_review_status or unknown_findings_status:
        return {
            "status": FAIL,
            "reason": "UNMAPPED_HARVEST_SIGNAL_STATUS",
            "detail": {
                "unknown_review_status_ids": unknown_review_status,
                "unknown_structured_findings_status_ids": unknown_findings_status,
            },
        }
    return {"status": PASS, "signal_count": len(rows)}


def _check_provenance(assessment: Any | None) -> dict[str, Any]:
    if assessment is None:
        return {"status": PASS, "reason": "NO_ASSESSMENT_SUPPLIED"}
    # Verified gap (not fabricated as passing): RnicaAssessment.field_provenance
    # is currently only a pass-through write target for whatever the
    # frontend sends -- no server-side process populates it when
    # structured findings are auto-applied. Reporting this honestly.
    provenance = assessment.field_provenance or []
    if not provenance:
        return {
            "status": NOT_YET_IMPLEMENTED,
            "reason": "FIELD_PROVENANCE_NOT_POPULATED_SERVER_SIDE",
        }
    # Real persisted shape (see applyStructuredFindings.js /
    # _serialize_rnica_assessment's fieldProvenance): each entry carries
    # source_type, source_record_id, source_excerpt, confidence, recorded_at.
    missing_source = [
        entry for entry in provenance if not entry.get("source_type") and not entry.get("source_record_id")
    ]
    if missing_source:
        return {"status": FAIL, "reason": "PROVENANCE_MISSING", "detail": {"count": len(missing_source)}}
    return {"status": PASS, "provenance_count": len(provenance)}


def _check_narrative_single_current() -> dict[str, Any]:
    # No narrative-generator consolidation/versioning system exists yet
    # (open items: one authoritative generator, content hashes, context
    # versions, stale-marking). Reporting this as an explicit open gap
    # rather than a false PASS.
    return {"status": NOT_YET_IMPLEMENTED, "reason": "NARRATIVE_VERSIONING_NOT_IMPLEMENTED"}


def presentation_readiness_check(
    db: Session, patient_id: str, assessment: Any | None = None
) -> dict[str, Any]:
    """Runs every currently-implementable invariant check and returns one
    PASS/FAIL/NOT_YET_IMPLEMENTED verdict plus the per-check detail, so a
    caller never has to manually inspect multiple subsystems to decide
    whether an assessment is safe to present for RN review.
    """
    checks = {
        "diagnosis_consistency": _check_diagnosis_consistency(db, patient_id),
        "rnica_diagnosis_conflict": _check_rnica_diagnosis_conflict(db, assessment),
        "harvest_reconciliation": _check_harvest_reconciliation(db, patient_id),
        "provenance": _check_provenance(assessment),
        "narrative_single_current": _check_narrative_single_current(),
    }

    statuses = {c["status"] for c in checks.values()}
    if FAIL in statuses:
        overall = FAIL
    elif NOT_YET_IMPLEMENTED in statuses:
        overall = NOT_YET_IMPLEMENTED
    else:
        overall = PASS

    return {"overall": overall, "checks": checks}
