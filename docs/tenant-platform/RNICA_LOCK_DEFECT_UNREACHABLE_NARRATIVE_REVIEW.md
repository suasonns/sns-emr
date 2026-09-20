# RNICA Lock Defect — Unreachable Narrative Review Control

**CLASSIFICATION: CURRENT DEFECT**
**STATUS: OPEN**
**This document records a defect for tracking. It does not authorize or
perform a repair. No code, schema, or migration changes are made here.**

---

## 1. Affected Data Condition

Any `rnica_assessments` row where:

- `form_data.diagnoses.clinicalNarrative` is present and contains non-empty
  text, **and**
- `form_data.diagnoses.clinicalNarrativeReviewed` is `false` (or absent /
  not exactly `true`).

Such rows were most likely created via direct API calls, test fixtures, or
a prior build of the application in which the Diagnosis-section Clinical
Narrative card was still reachable in the UI (before it became orphaned —
see `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`, Part 0). No mechanism was
found for creating such a row through the *current* running UI, since the
field cannot currently be written to at all through it.

---

## 2. Current Lock Behavior

`rnica_finalization_service.py:120-127` evaluates the `narrativeReviewed`
readiness check as part of Lock/finalization readiness:

```
narrative = diagnoses.clinicalNarrative
narrative_reviewed = diagnoses.clinicalNarrativeReviewed is True
narrative_ready = (not has_text(narrative)) or narrative_reviewed
```

For an affected record (non-empty narrative, `reviewed` not `true`),
`narrative_ready` evaluates to `False`, and the `narrativeReviewed` check
is reported as not-ready, blocking Lock finalization for that record.

**The current UI provides no reachable control to set
`clinicalNarrativeReviewed = true`** (the checkbox lives at
`RNICA.jsx:2137-2142`, inside the same dead `ClinicalNarrativeCard` — see
`RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`, Part 0), and no reachable
control to clear or edit `diagnoses.clinicalNarrative` itself. A nurse or
clinician working an affected record in the current build has no in-app
path to satisfy this specific readiness check.

---

## 3. Verification Query

Read-only query to identify currently affected records (PostgreSQL, JSONB
`form_data` column on `rnica_assessments`):

```sql
SELECT
    id,
    patient_id,
    tenant_id,
    locked,
    locked_at,
    form_data #>> '{diagnoses,clinicalNarrative}' AS narrative_text,
    form_data #>> '{diagnoses,clinicalNarrativeReviewed}' AS reviewed_flag
FROM rnica_assessments
WHERE
    trim(COALESCE(form_data #>> '{diagnoses,clinicalNarrative}', '')) <> ''
    AND COALESCE((form_data #>> '{diagnoses,clinicalNarrativeReviewed}')::boolean, false) = false;
```

This query is provided for verification/discovery only. It has not been
run against any environment as part of this document, and running it is
not authorized by this document (no destructive or corrective action is
implied — it is a read-only `SELECT`, but execution against any real
environment should follow the team's normal read-only-query approval
process).

---

## 4. Historical-Record Exposure

- **Locked records:** if an affected record is already `locked = true`, this
  defect has no effect (the readiness check only gates the *transition* to
  locked, not already-locked records).
- **Unlocked, previously-created records:** any record matching the query
  in Section 3 that is not yet locked is currently stuck: it cannot pass
  the `narrativeReviewed` readiness check and cannot be corrected via the
  UI, blocking Lock for that assessment until either the data or the check
  is addressed.
- **New records going forward (current build):** cannot enter this state
  going forward through the UI, since the field cannot be written to. Only
  direct API writes (e.g., integration, migration, or test tooling) could
  create a new affected record today.

The actual count/scope of currently affected records in any given
environment is unknown from repository inspection alone and would require
running the Section 3 query against that environment's database.

---

## 5. Forward-Only Repair Options (Not Authorized For Implementation)

Provided for future, separately authorized implementation planning only:

**Option 1 — Repoint the check.** Change `narrativeReviewed` to read
`finalization.clinicalNarrative` / a finalization-side reviewed concept
instead of the diagnoses fields, so affected historical records are
evaluated against the field a nurse can actually reach. Requires deciding
whether a "reviewed" concept is even needed on the finalization field (see
`RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`, Section 4, item 2).

**Option 2 — Retire the check.** Remove the `narrativeReviewed`
readiness check entirely, on the basis that the Finalization attestation
hard-error (`finalization.clinicalNarrative` required before signature)
already serves the same underlying purpose more strongly. Historical
`diagnoses.clinicalNarrative` / `clinicalNarrativeReviewed` values are
preserved as read-only data; they simply stop being evaluated for Lock
readiness.

**Option 3 — Targeted data correction.** For records matching the Section 3
query, set `clinicalNarrativeReviewed = true` via a forward-only, reviewed,
audited data-correction process (not a historical migration rewrite, not
`alembic stamp`) — only if the Owner determines the existing narrative text
should be treated as "reviewed" as-is rather than superseded by Option 1 or
2. This option is listed for completeness; it is not recommended over
Options 1/2 without a clinical review of the affected text, and is not
authorized for execution by this document.

Any of these requires its own audit trail, verification pass, and rollback
plan before execution — none of that is defined here.

---

## 6. Test Cases (Required Before Any Repair Is Implemented)

1. A record with non-empty `diagnoses.clinicalNarrative` and
   `clinicalNarrativeReviewed = false`, currently unlockable — confirm it
   is correctly identified by the Section 3 query.
2. A record with empty/absent `diagnoses.clinicalNarrative` — confirm the
   `narrativeReviewed` check already passes today (unaffected by this
   defect) and continues to pass after any repair.
3. A record with non-empty `diagnoses.clinicalNarrative` and
   `clinicalNarrativeReviewed = true` — confirm it already passes today
   and continues to pass after any repair.
4. An already-`locked = true` affected record — confirm Lock state is
   unaffected before and after any repair (no re-evaluation of a
   completed Lock).
5. Whichever repair option is eventually chosen: confirm no regression in
   the Finalization attestation hard-error
   (`finalization.clinicalNarrative` required before signature), which
   must continue to function independently of this defect.
6. Confirm no amendment or audit history row is altered by the repair
   (repair changes readiness-check behavior and/or specific field values
   only, per the option chosen — it must not touch `rnica_amendment`
   rows or audit logs).

---

## 7. Status

This defect is **not dismissed as redesign work**. It exists in the
current build independent of any future RNICA redesign and should be
tracked and resolved (per one of the Section 5 options) under its own
implementation authorization, separate from the Tenant Platform Redesign
track.

| | |
|---|---|
| Classification | CURRENT DEFECT |
| Status | OPEN |
| Repair authorized by this document | NO |
| Verification query authorized to run (read-only, subject to team process) | Documented in Section 3 |

---

## Cross-References

- `docs/tenant-platform/RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md` (Part 0 — origin of this finding)
- `docs/tenant-platform/RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`
