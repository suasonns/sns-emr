# SNS RNICA Audit Inventory 1.0 — Phase 1, Deliverable 6

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This document records audit-trail behavior as it actually exists today.
It does not modify any prior frozen deliverable and does not propose new
audit logging.

Source of truth: `backend/app/models/rnica_assessment.py`;
`backend/app/api/visits.py` (RNICA endpoints, lines 751-1027, and the
`_safe_log_event`/`log_event` call sites across the rest of the file);
`backend/app/services/audit_logger.py`. No global request-logging
middleware was found in the codebase (`app/main.py` / `registry.py`
searched — no audit middleware registered).

## Key finding

**RNICA create, update, and lock produce no audit-log events at all.**
`log_event()` (imported at `visits.py:70`, wrapped by the file-local
`_safe_log_event()` at `visits.py:2028`) is called from many other
endpoints in this same file (first call site at line 2631), but **none**
of the calls fall within the RNICA route handlers
(`save_rnica_assessment` 751-795, `update_rnica_assessment` 930-975,
`lock_rnica_assessment` 978-999). The only record that an RNICA
assessment was created, edited, or locked is the state of the row itself
— three plain timestamp/boolean columns, with **no user-attribution
column on the table at all** (`rnica_assessments` has no `created_by`,
`updated_by`, or `locked_by` column — confirmed against the full column
list in `rnica_assessment.py:14-31`).

## Action-by-action audit capture (current implementation)

| Action | Endpoint | Timestamp captured | User Attribution captured | Audit Trail Storage | Notes |
|---|---|---|---|---|---|
| **Create** | `POST /visits/rnica/save` | `created_at` (set by column default, `visits.py`/model, not explicitly passed) | **None** — `current_user` is used only for tenant/patient authorization (`get_authorized_patient`), never written to the row | `rnica_assessments` row itself only; no separate audit-log entry | No `log_event()` call in this handler |
| **Edit / Update** | `PUT /visits/rnica/{assessment_id}` | `updated_at` (auto-updates via SQLAlchemy `onupdate=datetime.utcnow`) | **None** | `rnica_assessments` row itself only (prior `form_data` is fully overwritten, not versioned or diffed — no history of what changed or who changed it) | No `log_event()` call; `status` is reset to `"DRAFT"` on every update regardless of who made it |
| **Delete** | — | n/a | n/a | n/a | **No DELETE endpoint exists for RNICA assessments** (`SNS_RNICA_API_MAPPING_1.0` §1) — deletion is not a currently implemented capability, so there is nothing to audit |
| **Sign** | — | — | — | — | **RNICA has no distinct "sign" action separate from Lock.** `finalization.clinicianSignature` is a plain form field (validated as required before lock, per `SNS_RNICA_VALIDATION_INVENTORY_1.0`) — its value is just a string inside `form_data`, not a cryptographic or database-level signature event |
| **Co-sign** | — | — | — | — | **Not implemented.** No supervisor/co-signer field, endpoint, or workflow exists anywhere in the RNICA save/update/lock code. (Section 28 "Supervisor Review" fields, per the Field Inventory, are plain form fields inside `form_data` with no distinct co-sign action or endpoint.) |
| **Finalize / Lock** | `POST /visits/rnica/{assessment_id}/lock` | `locked_at` (explicitly set to `datetime.now(timezone.utc)`, `visits.py:997`) | **None** — no `locked_by` column exists; `current_user` is used only for authorization | `rnica_assessments.locked = True`, `.status = "LOCKED"`, `.locked_at` | No `log_event()` call; no re-validation of form completeness server-side (see `SNS_RNICA_API_MAPPING_1.0` §1.5) |
| **Approve** | — | — | — | — | **Not implemented.** No approval field, status value, or endpoint exists for RNICA beyond `DRAFT`/`LOCKED` |

## Cross-reference: what IS audited elsewhere as a byproduct of RNICA data

Although the `rnica_assessments` row itself carries no user attribution,
several of the sync-dependency writes triggered by save/update (see
`SNS_RNICA_DATABASE_MAPPING_1.0` §3 and `SNS_RNICA_API_MAPPING_1.0` §3.2)
land in tables that **do** carry attribution/history:

| Synced table | Attribution captured | History behavior |
|---|---|---|
| `patient_diagnoses` | `created_by`/`updated_by` (FK→`users.id`) | Append/update with governance fields (IDG discussion tracking, etc.) — real audit-relevant columns exist here, unlike `rnica_assessments` |
| `patient_code_statuses` | `source` (string, e.g. `"RN_ICA"`) — not a user FK | **Append-only** (`is_current` flag flips old rows to false rather than overwriting) — this table has row-level history even though it lacks a `changed_by` user FK |
| `patient_contacts` | `updated_by` (FK→`users.id`), `source` | Update-in-place (one row per patient+role, no history retained) |
| `patient_allergies` | none (`source`-style column not present) | Update-in-place |
| `patient_facesheets` | `updated_by`, `created_by` (FK→`users.id`, per Database Mapping §3.5 note) | Update-in-place |

So the *only* place a user's identity is ever actually recorded in
connection with an RNICA save is indirectly, through these synced
records — never on the `rnica_assessments` row that represents the
assessment itself.

## Timestamp Requirements (as implemented, not as designed)

| Column | Set on | Mechanism |
|---|---|---|
| `created_at` | row insert | SQLAlchemy column default (`datetime.utcnow`), not request-time-explicit |
| `updated_at` | every `db.commit()` that touches the row | SQLAlchemy `onupdate=datetime.utcnow` |
| `locked_at` | lock action only | Explicitly set in `lock_rnica_assessment` (`visits.py:997`) |

No `signed_at`, `finalized_at`, `approved_at`, or `deleted_at` columns
exist.

## Status

**Deliverable #6 (`SNS_RNICA_AUDIT_INVENTORY_1.0`) complete.** Every
action category in the requested scope (Create/Edit/Delete/Sign/
Co-sign/Finalize/Approve) has been checked directly against the RNICA
route handlers and the `rnica_assessments` model. The dominant finding
is a near-total absence of user-attributed audit trail on the RNICA
table itself — timestamps exist, `log_event()` is never invoked, and
there is no `created_by`/`updated_by`/`locked_by` column at all. This is
recorded as an observed fact, not a defect assessment or a proposed fix.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #7 — `SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0`.
