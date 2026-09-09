# Payment Posting Architecture (835 Ingestion)

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Phase 6 required deliverable. Traces the full 835 remittance pipeline:
upload → parse → validation → remittance → payment → matching → claim
status → credit balance → reporting. Every row below is grounded in code
read directly (file:line) plus the Phase 4 executed test evidence
(`backend/tests/test_phase4_billing_architecture_validation.py`).

## Pipeline trace

| Step | Writer / Function | Table(s) | Endpoint | Service | UI | Audit Trail | Current Readiness |
|---|---|---|---|---|---|---|---|
| **1. Upload** | `upload_835` | — (reads file only) | `POST /billing/835/upload` | `app/api/billing_835.py` | **NONE FOUND** — no upload control anywhere in `sns-emr-frontend/src`; the dashboard's "835 Remittance" panel has no file input and no API call at all | Implicit only (the created `RemittanceAdvice` row itself, no separate log) | **BACKEND ONLY** |
| **2. Parse** | `parse_835_file` | — (returns parsed dict, no writes) | (called in-process, not a separate endpoint) | `app/services/edi_835_parser.py` | N/A | Raises `EDI835ParseError` → `400` on malformed input (validation exists) | **BACKEND ONLY** |
| **3. Validation** | `_is_denied` + explicit CARC code table (`DENIAL_CARC_CODES`) | — | in-process | `app/services/payment_service.py` | N/A | N/A | **BACKEND ONLY** — denial detection is explicit/allowlisted (8 CARC codes), not a full CARC/RARC engine; unrecognized codes are stored on the `PaymentAdjustment` row but do not trigger denial classification |
| **4. Remittance (header)** | `post_payments_from_835` | `RemittanceAdvice` (one row per uploaded file, `status="POSTED"`, `claim_count`, `total_paid_amount`, `payer_name`, raw file content retained) | same | same | **NONE** | The row itself is the record; `raw_content` is retained for reprocessing/audit | **BACKEND ONLY** |
| **5. Payment (per claim line)** | same | `Payment` (one row per `CLP` claim segment; `match_status` = `MATCHED`/`UNMATCHED` — unmatched payments are **never silently dropped**) | same | same | **NONE** | Row itself; no separate audit event | **BACKEND ONLY** |
| **6. Matching** | same | matches by `claim_control_number` against `Claim` (same tenant) | same | same | **NONE** | `match_status` field is the record of match/no-match | **BACKEND ONLY, correct by design** (explicitly does not silently drop unmatched payments — good defensive design) |
| **7. Claim status update** | same | `Claim.status` (`SENT/ACCEPTED → PAID` or `→ DENIED`, **only** if matched and current status is `SENT`/`ACCEPTED` — confirmed correct-and-guarded by execution in Phase 4) | same | same | **NONE** | **NO** `append_audit_event` call (see `claim_status_architecture.md` §9) — this is a real gap: payment-driven status changes are not logged the same way manual ones are | **BACKEND ONLY, behaviorally correct, but unaudited** |
| **8. Denial creation** | same | `Denial` (created when a CARC code matches `DENIAL_CARC_CODES`; carries `carc_code`, human-readable reason, computed appeal deadline using `DEFAULT_APPEAL_WINDOW_DAYS=120`) | same | same | N/A | Row itself | **BACKEND ONLY** |
| **9. Credit balance** | *not written by this pipeline* | — | — | — | — | — | **NOT LINKED** — no code path connects 835 posting to `CreditBalanceCase` creation; credit balance case creation is a separate, independently-triggered feature (confirmed wired to its own UI in Phase 5) with no evidence of automatic linkage from an overpayment detected via 835 |
| **10. Reporting** | *reads, does not write* | `Payment`, `RemittanceAdvice`, `Denial` | — | — | **NONE FOUND** for remittance/payment data specifically; `BillingDashboard.tsx`'s "835 Remittance" widget shown to users is **hardcoded/fabricated** and does not query any of these tables | — | **DEMO WILL MISLEAD** — see below |

## What this corrects from earlier phases

Phase 4 already proved steps 4–8 execute correctly against the real
database. This document adds the missing pieces the earlier phases
didn't cover: **step 1 (no upload UI), step 9 (no credit-balance
linkage), and step 10 (the one UI surface that claims to show this data
is fake).**

**Update to maturity/gap scoring per the directive's Critical Finding
#3**: 835 ingestion is not "unproven" or "UNKNOWN" — it is
**PRODUCTION-CORRECT BACKEND CODE** (194/194 broader billing tests
passing, plus 4 targeted behavioral tests). The gap is entirely on the
frontend/operational side: nobody can upload a file, and nobody can see
the real results even if one were uploaded via API. This is a "backend
exists, frontend does not" case in its purest form.

## The 835 widget specifically (Critical Finding #5)

`render835Remittance()` in `BillingDashboard.tsx` renders:
- A metric card row with hardcoded numbers ("835 Files Processed: 27",
  "Total Remitted: $1.08M", etc. — literal values in the component, not
  props or state derived from a fetch).
- A static table of fake remittance rows.
- **Zero** `fetch`/`api.` calls anywhere in the function body (confirmed
  by direct read of the function, not inference).

**Classification: DEMO ONLY / actually BROKEN-AS-A-CLAIM** — it is not
merely an empty state or a loading placeholder; it actively displays
specific, plausible-looking numbers that are entirely invented. If shown
in the Thursday demo without disclosure, a biller could reasonably
believe 27 real files have been processed and $1.08M has been remitted,
when the true count today is zero (no upload path exists at all).

## Capability classification (Phase 6 taxonomy)

| Step | Classification |
|---|---|
| Upload | BACKEND ONLY |
| Parse/Validate | BACKEND ONLY |
| Remittance/Payment/Matching | BACKEND ONLY |
| Claim status update | BACKEND ONLY (correct, but unaudited) |
| Denial creation | BACKEND ONLY |
| Credit balance linkage | MISSING (not built, not just unwired) |
| Reporting/UI | **BROKEN** — the only UI surface for this feature is fabricated, not merely absent |

## Recommendation (not yet implemented, awaiting go-ahead)

1. Before Thursday: either remove `render835Remittance()`'s fake content
   or replace it with an explicit "not yet available" empty state. This
   is the single highest-priority "what to remove/fix before Thursday"
   item from this document.
2. Do not claim 835 processing counts, remitted totals, or "processed
   files" numbers in the demo under any circumstance — there is no real
   data behind any number currently shown.
3. Phase-1-after-Thursday candidate: a real upload screen + a real
   remittance list screen, both of which can be built directly against
   the already-correct `post_payments_from_835`/`RemittanceAdvice`/
   `Payment` backend with no backend changes required except adding the
   missing audit-event call noted in `claim_status_architecture.md` §9.
