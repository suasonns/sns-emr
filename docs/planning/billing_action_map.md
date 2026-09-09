# Billing Action Map

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Phase 6 required deliverable. Every frontend control that could plausibly
change billing state was searched for by label (`Export To Excel`,
`Generate EDI`, `Generate Claim`, `Submit Claim`, `Transmit Claim`,
`Export Spreadsheet`) across `sns-emr-frontend/src`, then traced from
button → handler → endpoint → backend service → DB write.

## Finding: only one such button exists

Of the six labels named in the directive, **only one is actually present
in the codebase**: "Export to Excel" (`BillingDashboard.tsx`). There is
no "Generate EDI," "Generate Claim," "Submit Claim," "Transmit Claim," or
"Export Spreadsheet" button/label anywhere in the frontend. This matters
because it means the confusion is not "five similarly-named buttons that
might overlap" — it is **one single button whose label is unrelated to
its behavior.**

## Frontend actions that change billing state

| Label Seen By User | Actual Function | Frontend Component / Handler | Endpoint | Backend Service | Database Write | Claim Status Change | Payment Impact | Audit Trail | Safe For Demo | Safe For Production |
|---|---|---|---|---|---|---|---|---|---|---|
| **"Export to Excel"** | Generates an 837I EDI file and marks the claim exported | `BillingDashboard.tsx` → `handleExport(filteredRows[0])` (bound to the *first row of the currently filtered list*, not a selected row) | `POST /billing/export-patient-claim-edi` | `export_patient_claim_edi` (`app/billing/api/billing_router.py`) | `Claim.status="SENT"` (unconditional), `claim_control_number`, `exported_at`, `edi_batch_id`; creates `ClaimEdiBatch`, `ClaimExportLog` rows | **YES — unconditionally, from ANY current status**, confirmed by execution (`test_export_patient_claim_edi_bypasses_allowed_transitions_for_real`) | None directly, but can silently move a **PAID** claim back to **SENT**, corrupting downstream payment/remittance reconciliation | **NO** — no `append_audit_event` call anywhere in this code path | **NO** — filtering to "Paid"/"All" and clicking this button on stage/demo data will visibly corrupt a paid claim's status | **NO** — confirmed defect; must not be used against production claims in its current form |
| (No labeled button found) | Enforced status transition, the *intended* status-change mechanism | None found — no frontend code calls this endpoint | `POST /billing/claim-status` | `update_claim_status` (`app/billing/api/claim_status_router.py`) | `Claim.status` (only if in `ALLOWED_TRANSITIONS`), `last_status_reason` | **YES — but only to a legal next state; rejects illegal transitions with 409** | None directly | **YES** — `append_audit_event` records `CLAIM_STATUS_CHANGED` with previous/new status, actor, reason | N/A — not reachable from the UI | **YES**, behaviorally proven safe (Phase 4), but currently **unusable** because no UI calls it |
| (No labeled button found — this is a file upload, not a button click) | Parses an 835 remittance file and posts payments | None found in `BillingDashboard.tsx`'s "835 Remittance" panel — that panel renders hardcoded data with no upload control and no API call at all | `POST /billing/835/upload` | `post_payments_from_835` (`app/services/payment_service.py`) | Creates `Payment`/`Remittance` rows, conditionally creates `Denial` rows, conditionally writes `Claim.status` (`SENT/ACCEPTED → PAID` or `→ DENIED`, guarded — will not touch an already `PAID`/`DENIED` claim, confirmed by execution) | **YES, but guarded correctly** (confirmed by execution) | **YES** — this is the real payment-posting path | **NO** — no `append_audit_event` call in this path either (see `claim_status_architecture.md` §9) | N/A — no UI exists to trigger it at all | **Backend-safe behaviorally**, but **not reachable from any UI** — cannot be demoed or used by staff today |

## Same path / different path / accidentally shared?

Direct answer to the directive's question: **the three code paths above
are three fully independent implementations that happen to converge on
the same column (`Claim.status`) with no shared guard function between
them.** This is not "accidentally shared logic" (there is no shared
helper) — it is **duplicated, inconsistent enforcement**: one path
enforces correctly and audits, one path enforces correctly but does not
audit, and one path does neither. They are **different paths that should
have been the same path** (i.e., `export_patient_claim_edi` and
`post_payments_from_835` should both call through
`update_claim_status`'s guard/audit logic, or a shared equivalent,
instead of writing `claim.status` directly).

## Bottom line for Thursday

- **Do not click "Export to Excel" against PAID or DENIED claims** in any
  demo environment — it will visibly (and silently, with no audit
  record) revert the claim to SENT.
- The one *safe*, enforced status-change path has no UI — there is
  nothing to demo for "changing a claim's status," because the only
  reachable button that changes status is the unsafe one.
- The 835 payment-posting path is real and behaviorally correct, but is
  entirely invisible to any user — it can only be exercised today via a
  direct API call (as the Phase 4 tests do), not via any screen.
