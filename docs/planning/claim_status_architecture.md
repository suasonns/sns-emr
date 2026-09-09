# Claim Status Architecture

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Standalone deliverable requested in Phase 5 (Billing Platform
Stabilization Review). Companion to
`docs/planning/billing_inventory_and_gap_analysis.md` Section 14/15.
Every claim below is evidence-based — grep'd across the entire backend
(`backend/app/`, not scoped to `app/billing/`) and, where noted,
confirmed by executing real code
(`backend/tests/test_phase4_billing_architecture_validation.py`).

---

## 1. Every code path that writes `Claim.status`

Repo-wide search (`claim.status =` / `matched_claim.status =`) found
exactly **three** writers. No fourth writer exists anywhere in the
backend.

| # | Writer | File | Trigger | Enforces `ALLOWED_TRANSITIONS`? | Classification |
|---|---|---|---|---|---|
| 1 | `update_claim_status` | `app/billing/api/claim_status_router.py` | `POST /billing/claim-status` | **YES** — checks `ALLOWED_TRANSITIONS.get(current_status)` before writing, raises `409` otherwise | **PRIMARY** (the intended, designed status-transition authority) |
| 2 | `export_patient_claim_edi` | `app/billing/api/billing_router.py` | `POST /billing/export-patient-claim-edi` | **NO** — writes `claim.status = "SENT"` unconditionally, no read of current status, no transition check | **SECONDARY / CONFIRMED DEFECT** — a second, uncoordinated writer that bypasses the primary's own rule |
| 3 | `post_payments_from_835` | `app/services/payment_service.py` | `POST /billing/835/upload` | **PARTIAL** — does NOT consult `ALLOWED_TRANSITIONS` directly, but has its own equivalent guard: only writes `PAID`/`DENIED` `if matched_claim.status in ("SENT", "ACCEPTED")` | **IMPORT PATH** (an external-data-driven writer with its own correct, independently-implemented guard) |

No **SYSTEM JOB** (scheduled/cron) writer was found. No **LEGACY**
writer was found (the codebase has one claim-status model and one claim
table; there is no deprecated parallel claim/status table). No
**CORRECTION PATH** (an explicit "revert/undo/correct a claim status"
endpoint) was found — meaning writer #2's bypass is not an intentional,
documented correction workflow; it is simply unguarded.

## 2. `ClaimTransmission.status` writers

**No `ClaimTransmission` model exists in the codebase.** Repo-wide search
for `ClaimTransmission`/`claim_transmission` returned zero results. There
is no dedicated transmission-tracking entity — the closest analog is
`ClaimEdiBatch` (file-generation record, see below), which is not the
same thing as a transmission-confirmation record. **Classification:
MISSING** — this is not a gap in a writer, it's a gap in the data model
itself; there is nothing to write to.

## 3. Every code path that writes EDI lifecycle state

| Entity/field | Writer | Trigger | Ever updated after creation? | Classification |
|---|---|---|---|---|
| `ClaimEdiBatch` (row creation, `ack_status="PENDING"`) | `export_patient_claim_edi` | `POST /billing/export-patient-claim-edi` | **NO** — repo-wide search for `ClaimEdiBatch` found only its import, its model definition, and this one creation site. **Nothing in the codebase ever updates `ack_status` after the row is created.** | **PRIMARY (creation only) — NO CORRECTION/ACK PATH EXISTS** |
| `NoeEdiSubmission.ack_status` | `update_notice_edi_submission_status` | `PATCH /{patient_id}/edi-submissions/{submission_id}/status` | **YES** — this is a real, callable PATCH endpoint that updates `ack_status` after creation | **PRIMARY + CORRECTION PATH (by contrast, NOE has one and Claim EDI does not)** |
| `ClaimExportLog.status` | `export_patient_claim_edi` (creation only, `status="SUCCESS"`) | same endpoint | Not searched further this pass — treated as an audit log, not a lifecycle state | **IMPORT PATH / audit record** |

**Key finding**: the NOE side of the codebase has a working ack-status
update path (`update_notice_edi_submission_status`); the Claim EDI side
does not. This is an asymmetry worth closing if/when claim transmission
is built for real — the pattern to follow already exists in the NOE code.

## 4. State-transition diagram

```
                     ┌────────────────────────────────────────┐
                     │        Claim.status (as designed)       │
                     │   claim_status_router.ALLOWED_TRANSITIONS│
                     └────────────────────────────────────────┘

        READY ──────────────▶ SENT ──────────┬─────────────▶ ACCEPTED ──────────┬────────▶ PAID
          │(enforced:            │(enforced:  │                  │(enforced:      │
          │ update_claim_status) │ same)      │                  │ same)          │
          │                      │            │                  │                │
          │                      │            ▼                  │                ▼
          │                      │          DENIED  ◀─────────────┘              DENIED
          │                      │       (terminal)                            (terminal)
          │                      │
          │                      │  ▲ BYPASS (confirmed by execution):
          │                      │  │ export_patient_claim_edi writes
          │                      │  │ claim.status = "SENT" from ANY
          │                      │  │ current status, including PAID
          │                      │  │ or DENIED (terminal states) — no
          │                      │  │ read of ALLOWED_TRANSITIONS at all.
          │                      │  │
          ▼                      │  │
   ┌─────────────────────────────┴──┴───────────────────────────────┐
   │  ACTUAL observed behavior (test_phase4_billing_architecture_    │
   │  validation.py::test_export_patient_claim_edi_bypasses_         │
   │  allowed_transitions_for_real):                                 │
   │                                                                  │
   │      PAID ───(export_patient_claim_edi called again)───▶ SENT   │
   │      (terminal, per design)     (real, unguarded overwrite)     │
   └──────────────────────────────────────────────────────────────────┘

                     ┌────────────────────────────────────────┐
                     │  post_payments_from_835 (import path,   │
                     │  its own independent guard)             │
                     └────────────────────────────────────────┘
        SENT ──(matched, not denied)──▶ PAID     [only if current status
        SENT ──(matched, denied CARC)──▶ DENIED   is SENT or ACCEPTED —
        ACCEPTED ──(matched, not denied)──▶ PAID  confirmed correct by
        ACCEPTED ──(matched, denied CARC)──▶ DENIED  execution]
        DENIED ──(any later posting)──▶ (no change — guard holds,
                                          confirmed by execution)
```

## 5. THE QUESTION THAT MUST BE ANSWERED

**"Which is intended: (A) PAID is terminal, nothing may move a claim
backward, or (B) PAID may move backward in a defined correction
workflow?"**

**Answer, from evidence, not opinion: (A) is intended. There is no
evidence anywhere in the codebase of (B).**

Evidence for (A):
- `claim_status_router.ALLOWED_TRANSITIONS["PAID"] = set()` — the
  primary, designed status authority explicitly encodes PAID (and
  DENIED) as terminal with **zero** allowed outbound transitions. This is
  not ambiguous; it is a literal empty set.
- `post_payments_from_835`, the one other writer with its own
  independent guard logic, was written to **only** transition claims
  that are `SENT`/`ACCEPTED` — it was deliberately coded to leave
  `PAID`/`DENIED` claims alone (proven by execution: posting a second
  remittance against an already-`DENIED` claim left it `DENIED`).

Evidence against (B) — i.e., searched for and NOT found:
- No endpoint, service function, comment, docstring, or test anywhere in
  the codebase describes, names, or implements a "claim correction,"
  "claim reopen," "claim status rollback," or "claim reversal" workflow.
- `export_patient_claim_edi`'s unconditional write carries no comment
  explaining it as an intentional correction path — its surrounding code
  and docstring describe it purely as "submit an EDI export," with no
  reference to claim-status semantics at all.

**Conclusion: writer #2 (`export_patient_claim_edi`) is a defect, not an
undocumented feature.** It should be changed to consult
`ALLOWED_TRANSITIONS` (or an equivalent guard, matching the pattern
`post_payments_from_835` already uses correctly) before writing
`claim.status = "SENT"`.

## 6. Reachability (why this matters for Thursday)

This is not merely a theoretical/API-only bypass. The frontend
`BillingDashboard.tsx` "Unbilled Revenue Report" panel has a button
labeled **"Export to Excel"** whose `onClick` handler
(`handleExport(filteredRows[0])`) actually calls
`POST /billing/export-patient-claim-edi` against the **first row of the
currently filtered claim list** — not a specifically selected claim. The
status filter dropdown on that same panel includes `PAID` and `DENIED`
as selectable filters. **Filtering to "Paid" or "All Statuses" and
clicking "Export to Excel" would silently re-trigger this confirmed bug
against a real, already-paid claim, via a button whose label has nothing
to do with claim submission.** This upgrades the finding from "a bypass
exists in the API" to "a bypass is one misleadingly-labeled click away
in the shipped UI."

By contrast, the enforced endpoint (`update_claim_status`,
`POST /billing/claim-status`) has **no frontend wiring found anywhere**
in `sns-emr-frontend/src` — the safe, designed path is unused by the UI,
while the unsafe path is live and mislabeled.

---

## 7. Readers of `Claim.status` (Phase 6 addition)

Repo-wide search for every place `Claim.status`/`claim.status` is read
(not written) found exactly one reader location:

| Reader | File | Endpoint | Purpose |
|---|---|---|---|
| `list_claims` | `app/billing/api/claims_router.py` | `GET /billing/claims` | Returns claim rows including `status`; supports a `status` query filter (`Claim.status == status.upper()`). This is the query that powers `BillingDashboard.tsx`'s claim table and its status filter dropdown (`ALL, READY, SENT, ACCEPTED, PAID, DENIED`). |

No other backend module reads `Claim.status` directly (the one other
hit found by a broad grep, `owner_billing_service.py`, reads
`PlatformSubscription`/`PlatformInvoice.status` — the SNS-the-platform's
own billing-of-its-tenants status, an unrelated model that happens to
share the field name — confirmed a false positive, not a Claim reader).

## 8. All statuses (authoritative enum, from the model + router)

`READY`, `SENT`, `ACCEPTED`, `PAID`, `DENIED` — five values, defined by
usage in `ALLOWED_TRANSITIONS` and `Claim.status`'s column comment
(`app/billing/models/claim.py`). No `GENERATED` status exists in the
real code, despite one appearing in the Phase 6 directive's illustrative
example diagram (`READY → GENERATED → SENT → ACCEPTED → PAID`) — that
five-state illustrative diagram does not match the actual system, which
has no `GENERATED` state. This is called out explicitly so the
illustrative example in the directive is not mistaken for a real gap.

## 9. Audit trail — per writer (Phase 6 addition)

This is the most important corrective finding in this section: **audit
coverage is not uniform across the three writers.**

| Writer | Calls `append_audit_event`? | Audit event type | Consequence |
|---|---|---|---|
| `update_claim_status` (PRIMARY) | **YES** | `CLAIM_STATUS_CHANGED`, records `previous_status`, `new_status`, `actor`, `reason` | Every transition through the enforced path is fully auditable. |
| `export_patient_claim_edi` (SECONDARY/DEFECT) | **NO** — repo-wide search for `append_audit_event`/`build_audit_event` in `billing_router.py` found zero matches | — | The one writer that can silently move a claim backward is also the one writer that leaves **no audit trail** of having done so. There is a `ClaimExportLog` row created (`status="SUCCESS"`), but it records the export action, not a status-transition event, and does not capture `previous_status`. |
| `post_payments_from_835` (IMPORT PATH) | **NO** — repo-wide search for `append_audit_event`/`build_audit_event` in `payment_service.py` found zero matches | — | Payment-driven status changes (`SENT/ACCEPTED → PAID/DENIED`) are not recorded in the same audit log as manual transitions. Remittance data itself is persisted (so the *payment* is traceable), but the *status change event* specifically is not logged the way the primary path logs it. |

**Net finding**: if a hospice administrator asks "show me every way a
claim's status changed, and who/what changed it," the honest answer
today is **"only for changes made through the one enforced endpoint."**
Changes made via EDI export or via 835 payment posting are reconstructable
only indirectly (via `exported_at`/`ClaimExportLog` timestamps, or via
`Remittance`/`Payment` row timestamps), not via a first-class audit
event. This is a real gap, not a false alarm.

## 10. Direct answer to the Phase 6 "Most Important Question"

**"If a hospice administrator asks: show me every way a claim status can
change — can SNS answer that question completely?"**

**Answer: NO.**

SNS can answer *which code paths exist* (this document, complete) and
*what happened to a specific claim's `status` column* (by querying the
row). SNS **cannot** currently produce a complete, first-class audit log
of every status-changing event for a claim, because two of the three
writers do not emit an audit event at all, and one of those two writers
does not even enforce which transitions are legal. A complete answer
requires: (1) fixing `export_patient_claim_edi` to enforce
`ALLOWED_TRANSITIONS` (or an equivalent guard) before writing, and (2)
adding `append_audit_event` calls to both `export_patient_claim_edi` and
`post_payments_from_835` so all three writers log through the same audit
mechanism the primary path already uses.
