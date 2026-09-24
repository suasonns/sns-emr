# HOPE Audit Gap Analysis

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Classified
as an **RNICA DEPENDENCY WORKSTREAM**, not a future enhancement.

## What audit infrastructure exists in this repository

A generic, reusable audit logger exists: `audit_event()`
(`backend/app/services/audit_events.py`), which writes to the
`AuditLog` model (`backend/app/models/audit_log.py`) with
schema-drift-safe column discovery (`action`, `entity_type`, `entity_id`,
`user_id`, `role`, `ip_address`, `tenant_id`, `meta`). This is a solid,
reusable mechanism — the gap is that it is **never invoked** for any
HOPE workflow transition.

## Confirmed gap

A grep of `backend/app/api/visits.py` — the file containing every HOPE
workflow endpoint (close, ready-to-export, export-to-batch, submission-
update, inactivation, unlock, and the SFV completion endpoint) — for
`audit_events`/`log_audit`/`AuditLog(` returns **no matches**. None of
the following state transitions produce an `AuditLog` row today:

| Transition | Service function | Audit call present? |
|---|---|---|
| Close HOPE record | `apply_close()` | No |
| Mark ready to export | `apply_ready_to_export()` | No |
| Export to batch | `apply_export_to_batch()` | No |
| Submission number update | `apply_submission_update()` | No |
| Inactivation toggle | `apply_inactivation()` | No |
| Unlock | `apply_unlock()` | No |
| SFV completion | `POST /visits/sfv-requirements/{id}/complete` | No |

## What partial audit trail does exist

`RnicaAssessment` itself records **who and when** for several
transitions as columns on the row (`hope_closed_by`/`_at`,
`hope_ready_by`/`_at`, `hope_exported_to_batch_by`/`_at`,
`hope_submitted_by`/`_at`, `hope_inactivated_by`/`_at`,
`hope_unlocked_by`/`_at`/`hope_unlock_reason`). This is **embedded
current-state metadata, not an audit log** — it records only the *most
recent* transition of each kind, is overwritten on every repeat action
(e.g. re-locking and re-unlocking loses the prior unlock's timestamp),
and cannot answer "show me every state change for this record," "who
looked at / attempted to change this record and was denied," or "was
this record altered outside its normal workflow."

## Gaps

| Gap | Evidence | Severity |
|---|---|---|
| No append-only audit trail for any HOPE workflow transition | `visits.py` grep, above | HIGH |
| Embedded `_by`/`_at` columns are overwritten on repeat transitions, losing history | `rnica_assessment.py:33-50` (single-value columns, no history table) | MEDIUM |
| SFV completion — the highest-sensitivity transition remediated this session — has no audit trail either, despite its own row-level locking and idempotency guarantees | Confirmed via the same grep; SFV completion lives in `visits.py` alongside the other HOPE endpoints | HIGH |
| No audit trail for denied/failed authorization attempts (e.g. a rejected `can_complete_sfv` call) — only the successful path is even partially recorded (via the embedded columns, not an audit log) | `patient_access.py::can_complete_sfv` raises/returns without any `audit_event()` call on either branch | MEDIUM |

## Required before implementation

1. Add `audit_event(action=..., entity_type="RnicaAssessment", entity_id=str(record.id), ...)` calls to every service function in
   `rnica_hope_workflow_service.py` at its point of successful state
   change, using the existing `audit_events.py` helper — no new audit
   subsystem is required, per the directive's no-over-engineering
   instruction.
2. Add the same to the SFV completion endpoint in `visits.py`, both on
   success and on authorization denial, so the credential-based
   authorization decisions closed out in P3-009 are also independently
   auditable, not just enforced.
3. Do not remove the embedded `_by`/_at` columns — they remain useful as
   fast current-state reads; the audit log is additive, not a
   replacement.
