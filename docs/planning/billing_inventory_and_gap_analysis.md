# Billing Inventory and Gap Analysis

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Single master document. Supersedes and replaces any other billing
inventory/readiness drafts — this is the only billing discovery document.
No new billing features were built to produce this; it is evidence-based
discovery only, grounded in reading the actual backend models, services,
API routers, and frontend pages.

Legend: **IMPLEMENTED** (real, non-stub logic/persistence/UI confirmed) /
**PARTIAL** (real but with a confirmed gap or placeholder) / **MISSING**
(confirmed absent) / **UNKNOWN** (exists but not read closely enough this
pass to confirm — flagged for follow-up, not assumed working).

> **2026-09-08 follow-up update**: The items below that were previously
> UNKNOWN have now been read directly and are RESOLVED. All other content
> in Sections 1–5 is unchanged from the prior pass.
> - `POST /billing/export-patient-claim-edi` → **RESOLVED to PARTIAL**. It
>   is real: builds a valid 837I EDI text file via `edi_builder.py`, saves
>   it to disk (`save_edi_to_file`), logs a `ClaimExportLog` row, creates a
>   `ClaimEdiBatch` row, and marks the `Claim` status `SENT` with a
>   `claim_control_number`. **However there is no clearinghouse/payer
>   transmission channel** (no SFTP/API call found) — the file is produced
>   and the claim is marked SENT locally, but nothing sends it anywhere.
>   This is the single most important nuance for the demo: "generates a
>   real 837I claim file and tracks it as sent" is true; "electronically
>   transmits claims to payers" is **not yet true**.
> - `GET/POST /billing/credit-balance/cases`, `/cases/{id}`,
>   `/cases/{id}/actions` → **RESOLVED to IMPLEMENTED**. Full case
>   lifecycle is real: `open_case_for_claim`, `perform_action` with an
>   audited event trail (`CreditBalanceCaseEvent`), tenant-scoped
>   authorization on every route.
> - `GET /billing/credit-balance/cms-838-export` → **RESOLVED to
>   PARTIAL**. Real, but the response itself documents its own gap: fields
>   the current schema cannot supply (MBI, ICN, Type of Bill,
>   admission/discharge dates, Medicare Part) are explicitly returned as
>   `"NOT_AVAILABLE_IN_SCHEMA"` rather than fabricated, and the payload
>   carries `"data_completeness": "PARTIAL"`. Good practice (no fake
>   data), but not yet a fileable CMS-838 without manual completion.
> - `GET /billing/payment-posting/remittances`, `payments`,
>   `payment_adjustments`, `remittance_advices` tables → **RESOLVED to
>   PARTIAL**, same conclusion as before but now confirmed directly: the
>   read side (ERA registry, MTD totals, payer breakdown, unmatched
>   worklist) is fully real and backed by real tables. **No posting/match
>   write-endpoint was found** — payments and remittances must be getting
>   into these tables through some other/upstream ingestion path not
>   reviewed this pass, and there is no in-app "post/match this payment"
>   action.
> - `POST /billing/generate-patient`, `POST /billing/batch-generate`,
>   `GET /billing/agencies`, `billing_cycles` → **RESOLVED to
>   IMPLEMENTED**. All real: `generate_patient_billing` (billing engine),
>   batch version iterates every ACTIVE patient, checks readiness per
>   patient, skips (never force-bills) unready patients with blocker
>   reasons, one patient's failure doesn't abort the batch; `/agencies` is
>   a real tenant-scoped selector restricted to billing-department roles.
> - Referral / Admission / Discharge / Transfer linkage → **RESOLVED**.
>   Dedicated `Referral`, `Admission`, `AdmissionActionRequest`, and
>   `AdmissionStatusHistory` models exist in `app/models/`. Discharge is
>   not a separate model but a rich set of fields directly on `Patient`
>   (`discharge_date`, `discharge_reason`, `discharge_initiated_by`,
>   `discharge_projected_date`, plus CoP checklist booleans like
>   `discharge_plan_reviewed`/`discharge_notified`/`discharge_explained`).
>   No dedicated `Transfer` model was found. See Section 6 (Workflow
>   Linkage Audit) below for how these connect to billing.

---

# SECTION 1 — EXISTING SYSTEM INVENTORY

## 1.1 Screens (frontend, `/billing/*` in `App.tsx`, behind `BillerShell`)

| Screen | Status |
|---|---|
| Dashboard (`BillingOverviewPage.tsx`) | IMPLEMENTED |
| Visits & Notes (`VisitsNotesPage.tsx`) | IMPLEMENTED |
| POC/Certification (`PocCertificationPage.tsx`) | IMPLEMENTED |
| NOE Tracking (`NoeTrackingPage.tsx`) | IMPLEMENTED |
| Claims Management (`ClaimsManagementPage.tsx`) | IMPLEMENTED |
| Denials & Appeals (`DenialsAppealsPage.tsx`) | IMPLEMENTED |
| Eligibility Verification (`EligibilityVerificationPage.tsx`) | IMPLEMENTED |
| Payment Posting (`PaymentPostingPage.tsx`) | PARTIAL — monitoring/remittance view confirmed; write/posting-transaction path unconfirmed |
| Cap Calculation (`CapCalculationPage.tsx`) | IMPLEMENTED |
| Aging Report (`AgingReportPage.tsx`) | IMPLEMENTED |
| Credit Balance Report (`CreditBalanceReportPage.tsx`) | IMPLEMENTED |
| Facility Collections (`FacilityCollectionsReportPage.tsx`) | IMPLEMENTED |
| Reports (`ReportsPage.tsx`) | PARTIAL — live snapshot only; page's own copy states scheduled/downloadable export not implemented |
| Settings (`ComingSoonPage`) | MISSING |

## 1.2 Database tables

### `backend/app/billing/models/` (31 files)

| Table | Status |
|---|---|
| `claims` | IMPLEMENTED |
| `denials` | IMPLEMENTED |
| `credit_balance_cases`, `credit_balance_case_events` | IMPLEMENTED |
| `election_addendum_requests` | IMPLEMENTED |
| `facility_collection_alerts`, `facility_collection_alert_thresholds` | IMPLEMENTED |
| `facility_payment_allocations`, `facility_payment_expectations`, `facility_payment_audit_log` | IMPLEMENTED |
| `hospice_cap_records` | IMPLEMENTED |
| `noe_edi_submissions` | IMPLEMENTED |
| `payer_eligibility_checks` | IMPLEMENTED |
| `billing_provider_organizations`, `billing_provider_agency_assignments`, `billing_provider_agency_service_scopes` | IMPLEMENTED |
| `billing_cycles` | UNKNOWN — model exists, backing endpoint not read closely |
| `billing_provider_organization_memberships` | UNKNOWN |
| `billing_snapshots`, `billing_summaries` | UNKNOWN |
| `claim_edi_batches`, `claim_export_logs` | UNKNOWN — would confirm/deny real claim EDI transmission if read |
| `payer_contracts` (`contract.py`) | UNKNOWN |
| `appeals`, `authorization_records` | UNKNOWN |
| `gip_periods`, `respite_periods`, `continuous_care_events` (`loc_events.py`) | UNKNOWN |
| `orders_snapshots` | UNKNOWN |
| `patient_pos` | UNKNOWN |
| `payments`, `payment_adjustments` | UNKNOWN — likely back Payment Posting; needed to resolve that PARTIAL |
| `remittance_advices` | UNKNOWN — likely backs `/payment-posting/remittances` |
| `visit_minutes` | UNKNOWN |
| `payer.py` (re-export, not a new table) | IMPLEMENTED elsewhere (`app.models.payer.Payer`) |

### Outside `billing/models/`

| Table | Status |
|---|---|
| `benefit_periods` | IMPLEMENTED |
| `certifications`, `certification_status_events` | IMPLEMENTED |
| `rn_recert_assessment` | UNKNOWN — not read closely this pass |
| Patient payer/insurance records (consumed widely; exact model not located this pass) | IMPLEMENTED (consumed) |

## 1.3 API endpoints

~90 routes total. Full path-level detail below; grouped by confirmed status.

**IMPLEMENTED** (confirmed via direct code read or existing passing tests):
`GET /billing/visits-notes`, `GET /billing/poc-certification-status`,
`GET /billing/noe-tracking`, `GET /billing/credit-balance/report`,
`GET /billing/denials`, `POST /billing/claim-status`, all 6
`billing-provider/organizations|assignments` routes, `GET
/billing/aging-report`, `GET /billing/claims`, both
`eligibility-checks`/`eligibility-roster` routes, `GET
/billing/audit-history`, all 13 `facility-payment/*` routes (expectations
CRUD/lifecycle, allocations confirm/reverse, collections-report, alerts
lifecycle x6, alert-thresholds), `POST /billing/export-patient-claim`, `GET
/billing/readiness/{patient_id}`, `GET /billing/readiness-report`, all 3
`election-addendum-requests` routes, all 3 `hospice-cap` routes, 8 of the
12 `noe`/`notr` routes (submission GET/PATCH x2, generate-837i x2,
edi-submissions list + status PATCH), all 7 `certifications.py` routes
(list, status-history, draft, narrative update, submit, sign, legacy
create-and-sign).

**PARTIAL**: `GET /billing/payment-posting/remittances` (monitoring
confirmed, posting-write action unconfirmed); `POST
/billing/facility-payment/allocations/{id}/confirm` (real, but precedence
slots 1–4 internally stubbed).

**UNKNOWN** (exist, not read closely — do not assume working for the
demo): `credit-balance/reason-codes`, `credit-balance/cases` (POST/GET/GET
by id), `credit-balance/cases/{id}/actions`,
`credit-balance/cms-838-export`, `billing/tenants`, `billing/queue`,
`billing/cycles`, `billing/generate-patient`,
**`billing/export-patient-claim-edi`** (highest priority to confirm — this
name directly claims real claim EDI submission), `billing/agencies`,
`billing/batch-generate`, `{patient_id}/noe/generate-pdf`.

## 1.4 Services (backend)

| Service | Status |
|---|---|
| `billing_readiness_service.py` (patient/tenant/cross-agency readiness) | IMPLEMENTED |
| `benefit_period_service.py` (rollover, period-length calc) | IMPLEMENTED |
| `election_day_service.py` (cumulative election day) | PARTIAL — re-election-after-revocation/gap handling is an explicit TODO |
| `election_addendum_service.py` (5/3-day deadline compliance) | IMPLEMENTED |
| `certification_service.py` (draft/sign/finalize/supersede) | IMPLEMENTED |
| `recert_f2f_enforcement.py` | IMPLEMENTED |
| `hospice_cap_service.py` | IMPLEMENTED |
| `noe_penalty_service.py` | IMPLEMENTED |
| `noe_edi_builder.py` (837I text generation) | IMPLEMENTED |
| `claim_segment_service.py` (LOC→revenue code, claim lines) | PARTIAL — revenue code map hardcoded, explicitly commented "STRUCTURE ONLY" |
| `claim_financials.py` (balance/payments/adjustments) | IMPLEMENTED |
| `claim_export_service.py` (claim export payload) | IMPLEMENTED |
| `revenue_service.py` (rate schedule) | PARTIAL/MISSING — explicit "DEFAULT RATE SCHEDULE PLACEHOLDER" comment |
| `facility_payment_service.py` | PARTIAL — comment states "Precedence slots 1-4 are intentionally stubbed today" |
| `billing_provider_access_service.py` | IMPLEMENTED |

## 1.5 Reports

| Report | Status |
|---|---|
| Billing Readiness (patient + tenant rollup) | IMPLEMENTED |
| Aging Report | IMPLEMENTED |
| Credit Balance Report | IMPLEMENTED |
| Facility Collections Report | IMPLEMENTED |
| Hospice Cap usage | IMPLEMENTED |
| General Reports snapshot page | PARTIAL — live view only |
| Scheduled/downloadable export (PDF/CSV) of any report | MISSING |
| CMS-838 credit balance export | UNKNOWN |
| Denials historical trend/export | PARTIAL — current registry only |

---

# SECTION 2 — WORKFLOW INVENTORY

| Workflow stage | Status | Evidence |
|---|---|---|
| **Referral** | UNKNOWN | Not billing-owned; referral/intake exists elsewhere in the app but was not reviewed as part of billing this pass |
| **Admission** | UNKNOWN | Same — clinical/admissions module, not reviewed for billing linkage this pass |
| **Election** | IMPLEMENTED | `election_day_service.py` cumulative day tracking; election addendum tracked separately |
| **Benefit Period** | IMPLEMENTED | Storage (`benefit_periods` table), rollover calc (`benefit_period_service.py`), display wired into Dashboard/readiness views |
| **Certification** | IMPLEMENTED | Full draft→submit→sign→finalize lifecycle, physician-signer enforcement, status-event audit trail |
| **Recertification** | IMPLEMENTED | Same certification pipeline drives recert; F2F enforcement for BP3+ confirmed (`recert_f2f_enforcement.py`) |
| **NOE (Notice of Election)** | IMPLEMENTED, with PARTIAL edge | Submission tracking, 837I EDI generation, late-penalty calc all real; PDF generation endpoint UNKNOWN |
| **Claim Preparation** | IMPLEMENTED | Claim line building from LOC segments, claim financials, export payload all confirmed real |
| **Claim Tracking (status)** | IMPLEMENTED | Explicit `READY→SENT→ACCEPTED/DENIED→PAID` state machine with enforced transitions |
| **Claim Submission (EDI transmission)** | UNKNOWN | `export-patient-claim` payload is real; whether `export-patient-claim-edi` performs actual EDI transmission is unconfirmed — **do not claim this works for the demo without reading it first** |
| **Payment Tracking** | PARTIAL | Remittance monitoring view real; posting/matching write transaction and underlying `payments`/`payment_adjustments` tables unconfirmed |
| **Discharge** | UNKNOWN | Not reviewed as part of billing this pass — likely lives in clinical/admissions, billing-side impact (final claim, cap true-up) not traced |
| **Revocation** | PARTIAL/MISSING | Re-election-after-revocation is an explicit TODO in `election_day_service.py`; no confirmed revocation-triggered billing workflow found |
| **Transfer** | UNKNOWN | Not reviewed this pass |

---

# SECTION 3 — GAP ANALYSIS

| # | Area | Current State | Desired State | Gap | Priority |
|---|---|---|---|---|---|
| 1 | Claim EDI submission | Claim export *payload* exists; EDI-transmission endpoint exists but unread/unconfirmed | Confirmed, tested electronic claim submission (837 format) | Verify or build real EDI transmission | **HIGH** — blocks core "can we actually bill claims" answer |
| 2 | Payment posting (write path) | Read-only remittance monitoring only, confirmed | Ability to post/match payments to claims, updating claim status/balance | Missing (or unconfirmed) write path + tables (`payments`, `payment_adjustments`) | **HIGH** |
| 3 | Rate schedule / revenue pricing | Hardcoded revenue-code map, explicit placeholder rate schedule, `$0.00` fallback | Configurable payer rate schedules driving real claim line pricing | Rate schedule engine missing | **HIGH** — directly causes revenue leakage risk |
| 4 | Scheduled/downloadable report export | Live in-app snapshot only | Exportable (PDF/CSV) scheduled reports for billing staff | Missing | MEDIUM |
| 5 | Facility payment allocation precedence (slots 1–4) | Feature works but precedence logic stubbed | Full precedence-rule allocation | Partial implementation | MEDIUM |
| 6 | Revocation → billing workflow | Re-election/gap handling is a TODO; no confirmed revocation billing trigger | Revocation correctly closes benefit period, triggers final billing steps | Gap, likely MISSING | MEDIUM |
| 7 | Credit balance case management (create/act) | Endpoints exist, not confirmed real | Full CMS credit-balance case lifecycle incl. CMS-838 export | Unconfirmed — verify before assuming | MEDIUM |
| 8 | Discharge → billing linkage | Not traced this pass | Discharge correctly closes claims/benefit period, drives cap true-up | Unknown gap — needs tracing | MEDIUM |
| 9 | Referral/Admission → billing linkage | Not reviewed this pass | Confirmed data flow from intake into billing readiness | Unknown — needs tracing | LOW (pre-billing stage, less urgent for Thursday) |
| 10 | NOE PDF generation | Endpoint exists, unread | Confirmed working PDF output for compliance filing | Unconfirmed | LOW |

---

# SECTION 4 — AI OPPORTUNITIES

Explicitly excluded, per instruction: AI that writes claims, AI-generated
billing decisions of any kind (no eligibility, certification,
recertification, discharge, or claim-approval recommendations).

Opportunities scoped only to documentation/monitoring assistance:

1. **Documentation completeness monitoring** — flag patients whose visit
   notes, POC, or certification narrative are missing required elements
   before a claim is prepared (surfacing gaps, not deciding claims).
2. **Certification monitoring** — proactively surface certifications
   approaching their due date or missing F2F documentation for BP3+,
   using data already tracked in `certification_status_events` — this is
   an extension of what `rnica_evidence_synthesis`-style read-only
   aggregation (built for the recert reasoning framework) already proves
   out as a safe pattern.
3. **Benefit period monitoring** — alert on approaching benefit-period
   rollover dates and cap-year thresholds using existing
   `benefit_period_service.py`/`hospice_cap_service.py` data, without
   recommending action.
4. **Missing billing data detection** — extend `billing_readiness_service.py`
   blocker categorization into an AI-summarized "what's blocking this
   patient's readiness" narrative, purely descriptive of existing
   structured blockers.
5. **Claim readiness summarization** — narrative rollup of the
   already-computed readiness/blocker data for staff triage, again purely
   descriptive.
6. **Revenue leakage detection** — flag claims/periods hitting the `$0.00`
   fallback pricing path or unmapped revenue codes so staff can catch
   pricing gaps before submission (detection only, no pricing decisions).
7. **Workflow prioritization** — rank the billing queue (patients/claims
   with the most urgent blockers or approaching deadlines) using existing
   status fields, surfaced as a sortable/priority view rather than an
   automated action.

All of the above are **detection/surfacing/summarization only** — no
proposal here generates a billing, eligibility, certification, or
discharge determination.

---

# SECTION 14 — PHASE 4: ARCHITECTURE VALIDATION (BEHAVIORAL PROOF)

**Methodology change from prior sections**: everything above was derived
by reading code. This section instead **executed the real, unmodified
production functions against the real isolated-Postgres test database**
and asserts on what was actually committed — proof of behavior, not
inference from source. New test file:
`backend/tests/test_phase4_billing_architecture_validation.py` (4 tests,
all passing, run via `python scripts/run_isolated_tests.py --
tests/test_phase4_billing_architecture_validation.py`). This test file
exercises the real `update_claim_status`, `export_patient_claim_edi`, and
`post_payments_from_835` functions directly (only the heavyweight,
already-independently-tested collaborators inside
`export_patient_claim_edi` — claim-export payload build, 837I text
generation, file save — were stubbed; the status-write logic itself runs
for real).

## Finding A — CONFIRMED BUG: Claim.status enforcement bypass is real

Executed proof, not inference:
1. `update_claim_status` (the enforced endpoint) was called against a
   claim already in terminal state `PAID`, attempting `PAID → SENT`.
   **Result: real `HTTPException(409)`, claim correctly remained `PAID`.**
   The enforcement mechanism itself works correctly when used.
2. `export_patient_claim_edi` was then called against the **same kind of
   already-`PAID` claim**. **Result: the claim's status was silently
   overwritten to `SENT`**, with no exception, no check of
   `ALLOWED_TRANSITIONS`, no check of the claim's current status at all.

This upgrades Gap #7 (Section 8) from "confirmed by code read" to
**confirmed by execution** — an already-paid claim can be silently
reverted to SENT simply by re-running EDI export against it (e.g. a biller
re-exporting for their own records, or a retry after a transient error).

## Finding B — CORRECTION: payment ingestion path exists and is real (backend), but has zero frontend integration

The original audit (Sections 1–9) concluded the `payments`/
`remittance_advices` writer was **unidentified/UNKNOWN** because the
search was scoped to `app/billing/`. Executing a repo-wide search found
the real writer at `app/services/payment_service.py:post_payments_from_835`,
reachable via a real, registered endpoint: `POST /billing/835/upload`
(`app/api/billing_835.py`, registered in `app/api/registry.py:register_routers`,
confirmed via `app.include_router(router)` loop over `tenant_routes`).

Executed proof of its behavior:
1. Posting a synthetic parsed-835 payment against a real `SENT` claim
   **correctly created a `RemittanceAdvice` row, a matched `Payment` row,
   and advanced the claim to `PAID`.**
2. Posting a synthetic parsed-835 payment with a denial CARC (96)
   **correctly created a real `Denial` row and moved the claim to
   `DENIED`.**
3. Posting a **second**, later remittance against the now-`DENIED` claim
   **correctly left it `DENIED`** — unlike `export_patient_claim_edi`,
   `post_payments_from_835` DOES guard its status write
   (`if matched_claim.status in ("SENT", "ACCEPTED")`), so repeat postings
   cannot silently corrupt an already-terminal claim.

**However**: a repo-wide frontend search for any 835-upload UI
(`835/upload`, `billing/835`) found **zero references** — there is no
upload button, file picker, or any UI path to this endpoint anywhere in
`sns-emr-frontend/`. The capability is real and correctly guarded on the
backend, but is **completely inaccessible to billing staff today** except
via a direct API call (e.g. Postman/curl), which is not a realistic
billing-staff workflow.

## Corrections this forces to earlier sections

- **Gap List (Section 8), Rank #2** ("no confirmed payments/remittance
  ingestion path") is **corrected, not removed**: the ingestion path
  exists and is proven correct on the backend, but is blocked by a
  missing frontend integration. Re-ranked below.
- **Maturity Score (Section 11)**: "Payment Posting (write/matching)"
  corrected from `0–1` to **backend 4 / frontend 0** — the backend logic
  is solid (proven by execution, including the correct status guard and
  denial handling), but there is no UI, so the *end-to-end, staff-usable*
  score remains low.
- **Demo Readiness Matrix (Section 12)**: Payment Posting should remain
  🟡 YELLOW, but the correct caveat is now: *"the system can correctly
  post and match electronic remittances and detect denials — proven by
  automated test — but only via direct API call; there is no in-app
  upload button for billing staff to use it."* Do not say posting isn't
  possible; do not say it's usable by staff today either.
- **Claim.status / Claim EDI export**: downgrade from 🟡 YELLOW to
  reflect a **confirmed** (not theoretical) status-corruption risk — safe
  to demo generating an 837I file and marking a claim SENT, but flag
  internally that re-running export on an already-paid/denied claim is a
  real, proven bug that should be fixed before this pathway is used in
  production for anything beyond a first-time export per claim.

## Re-ranked Top Gaps after Phase 4 validation

| Rank | Gap | Status after Phase 4 | Priority |
|---|---|---|---|
| 1 | Claim.status enforcement bypass in `export_patient_claim_edi` | **CONFIRMED BY EXECUTED TEST** (Finding A) | **CRITICAL** (upgraded — this is now a proven bug, not a risk) |
| 2 | No claim-transmission channel to a clearinghouse/payer (837I file generated, never sent) | Unchanged from Section 8 — not re-tested this pass since no clearinghouse integration exists to test against | **CRITICAL** |
| 3 | Payment/remittance ingestion has no frontend UI | **CORRECTED**: backend is proven real and correct (Finding B); the gap is now specifically "missing UI," not "missing capability" | **HIGH** (re-scoped from CRITICAL to HIGH — the hard part, correct ingestion logic, already exists and works) |
| 4 | No configurable rate schedule / revenue pricing (placeholder) | Unchanged | **HIGH** |
| 5 | Revenue code mapping hardcoded | Unchanged | **HIGH** |
| 6 | Revocation → re-election/gap handling TODO | Unchanged | **HIGH** |
| 7 | No dedicated Transfer model/workflow | Unchanged | **HIGH** |
| 8 | Discharge → billing-closure trigger unconfirmed | Unchanged (not tested this pass) | **MEDIUM** |
| 9 | Discharge has no dedicated audit-event trail | Unchanged | **MEDIUM** |
| 10 | No scheduled/downloadable report export | Unchanged | **LOW** |

## What Phase 4 did NOT validate (still code-read-only, not executed)

To be explicit about scope, honoring "proof of behavior, not code
existence" — the following were **not** behaviorally re-verified this
pass and remain at their Section 1–9 confidence level: rate-schedule
placeholder end-to-end pricing effect on a real generated claim; the
Referral→Admission→Election automatic-linkage question; Discharge→billing
closure trigger; Transfer/cap cross-agency attribution; CMS-838 export
correctness beyond its self-reported schema gaps; credit-balance case
action state machine edge cases. These remain open items for a future
Phase 4 continuation if prioritized.

---

# PHASE 5 — BILLING PLATFORM STABILIZATION REVIEW

Everything below was produced by directly reading the actual frontend
source (`sns-emr-frontend/src/`) against the actual backend endpoint list,
one capability at a time — not inference. Where a claim is "wired," an
exact file and import were located. Where a claim is "not wired," a
repo-wide search for the literal endpoint path found zero references in
`sns-emr-frontend/src`.

**Standalone companion deliverable**: `docs/planning/claim_status_architecture.md`
contains the full required Claim.status / ClaimTransmission / EDI
lifecycle writer inventory, classification, state-transition diagram, and
the direct answer to "is PAID terminal?" (Answer: **yes, by design and by
every writer except one confirmed-defective one — see that document for
full evidence**). Summarized here, not repeated in full.

## 1. Claim Status Architecture — summary (full detail in companion doc)

Three writers total, no more, no fewer (repo-wide search, not
`app/billing/`-scoped): `update_claim_status` (**PRIMARY**, enforces
`ALLOWED_TRANSITIONS`, but has **zero frontend wiring found anywhere**),
`export_patient_claim_edi` (**SECONDARY / CONFIRMED DEFECT**, bypasses
the transition check, writes `SENT` unconditionally), `post_payments_from_835`
(**IMPORT PATH**, has its own correct, independently-implemented guard,
confirmed correct by execution). No `ClaimTransmission` model exists
anywhere in the codebase (**MISSING**, not a writer gap — a data-model
gap). No **SYSTEM JOB**, **LEGACY**, or **CORRECTION PATH** writer was
found.

**New finding this pass — reachability confirmed**: `BillingDashboard.tsx`'s
"Unbilled Revenue Report" panel has a button literally labeled **"Export
to Excel"** whose `onClick` handler
(`handleExport(filteredRows[0])`) actually calls
`POST /billing/export-patient-claim-edi` on the first row of the
*currently filtered* claim list. The status filter on that same panel
includes `PAID` and `DENIED` as selectable options. **Filtering to "Paid"
and clicking "Export to Excel" re-triggers the confirmed status-bypass
bug against a real claim, through a button whose label has nothing to do
with claim submission.** This is not a theoretical API-level bypass — it
is one misleadingly-labeled click away in the shipped UI.

## 2. Payment Architecture Map

| Step | Screen | Endpoint | Service | Writer | Table | Audit Trail | Current Status |
|---|---|---|---|---|---|---|---|
| 835 Upload | **None** — no upload UI found anywhere in `sns-emr-frontend/src` | `POST /billing/835/upload` (real, registered) | `app.api.billing_835` | — (routes to parser) | — | — | Backend Complete / Frontend Missing |
| Parser | n/a | n/a | `app.services.edi_835_parser.parse_835_file` | — | — | — | Not behaviorally re-verified this pass (only `post_payments_from_835`, its caller, was executed) |
| Remittance Record | `PaymentPostingPage.tsx` (read-only) | `GET /billing/remittances` | `payment_posting_router.py` | `post_payments_from_835` | `remittance_advices` | Implicit via row itself (`status`, `received_at`); no dedicated event table | **Confirmed real by execution** (Phase 4) |
| Payment Record | `PaymentPostingPage.tsx` (read-only) | same | same | `post_payments_from_835` | `payments` | `match_status` field only; no event table | **Confirmed real by execution** |
| Claim Matching | n/a (no UI) | n/a | `post_payments_from_835` (matches by `claim_control_number`) | `post_payments_from_835` | `payments.claim_id` FK | none dedicated | **Confirmed real by execution** — unmatched payments correctly flagged `UNMATCHED` rather than dropped |
| Claim Status Change | n/a (no UI) | n/a | `post_payments_from_835` | `post_payments_from_835` | `claims.status` | none dedicated (contrast: `claim_status_router`'s path has `append_audit_event`; this path does not) | **Confirmed real by execution**, but **no audit event recorded for this specific writer** — a gap not previously flagged |
| Credit Balance | `CreditBalanceReportPage.tsx` | `GET /billing/credit-balance/report`, `POST /cases`, `POST /cases/{id}/actions` | `credit_balance_service.py`, `credit_balance_case_service.py` | `credit_balance_case_service.perform_action` | `credit_balance_cases`, `credit_balance_case_events` | **YES** — dedicated event table, confirmed wired end-to-end incl. frontend (corrects an earlier UNKNOWN in Section 1.3) | **Backend Complete + Frontend Complete** |
| Reporting | `PaymentPostingPage.tsx`, `AgingReportPage.tsx` | `GET /billing/remittances`, `GET /billing/aging-report` | respective services | read-only | reads above tables | n/a | **Backend Complete + Frontend Complete (read-only)** |

**New audit-trail gap identified this pass**: `post_payments_from_835`'s
claim-status transitions are not recorded in any audit event table, unlike
the `claim_status_router` path (which calls `append_audit_event`). A
claim that flips SENT→PAID via an 835 posting leaves no explicit event
record of *why* — only the row's own `last_status_reason` string field.
This is a real, if modest, auditability gap worth closing alongside the
Section 14 fixes.

## 3. User-Visible Billing Capability Matrix

Built by locating each backend capability's actual frontend import (not
assumed). "Frontend Exists" here means a confirmed UI element that calls
the real endpoint — not merely that the page renders.

| Capability | Backend Exists | Frontend Exists | Permission Exists | Operational | Demo Ready |
|---|---|---|---|---|---|
| 835 Remittance Upload | YES | **NO** (no upload UI found anywhere) | Endpoint requires `require_automated_billing`, but nothing to gate at the UI since no UI exists | NO | **NO** |
| Payment Posting (monitoring) | YES | YES (`PaymentPostingPage.tsx`) | Tenant-scoped, `require_automated_billing` | YES (read-only) | YES, with the "monitoring only" caveat |
| Claim Status Update (enforced path) | YES | **NO** (no frontend wiring found for `POST /billing/claim-status`) | n/a — unreachable from UI | NO | **NO** |
| Claim EDI Export (unenforced path) | YES | YES — but mislabeled ("Export to Excel" button in `BillingDashboard.tsx`) | `require_automated_billing` | **YES, but with a confirmed live bug** (see Claim Status Architecture) | **NO — do not demo this button** |
| Certification Draft/Sign/Finalize | YES | YES (`PocCertificationPage.tsx` + certifications API, physician-only signer enforced) | Physician-role enforced at sign step | YES | YES |
| NOE/NOTR Submission Tracking | YES | YES (`NoeTrackingPage.tsx`, read-only) | Tenant-scoped | YES (read-only) | YES, monitoring only |
| NOE/NOTR 837I Generation | YES | **NO** (no frontend wiring found for `generate-837i`) | n/a — unreachable from UI | NO | **NO** |
| NOE PDF Generation | YES (endpoint exists) | **NO** | n/a | UNKNOWN (endpoint itself not behaviorally tested this pass) | **NO** |
| Denials & Appeals registry | YES | YES (`DenialsAppealsPage.tsx`) | Tenant-scoped | YES (read-only registry) | YES |
| Eligibility Verification/Roster | YES | YES (`EligibilityVerificationPage.tsx`) | Tenant-scoped | YES | YES |
| Hospice Cap Calculation | YES | YES (`CapCalculationPage.tsx`) | Tenant-scoped | YES | YES, with the cross-agency-transfer caveat |
| Aging Report | YES | YES (`AgingReportPage.tsx`) | Tenant-scoped | YES | YES |
| Credit Balance Report + Case Actions | YES | YES (`CreditBalanceReportPage.tsx` — confirmed real dialog/action wiring via `openCreditBalanceCase`/`performCreditBalanceCaseAction`) | Tenant-scoped | YES | YES |
| CMS-838 Export | YES | **NO** (no frontend wiring found) | n/a | NO | **NO** |
| Facility Payment Expectation lifecycle (create/activate/correct/cancel) | YES | YES (`FacilityCollectionsReportPage.tsx` — confirmed real dialog wiring for create/activate/correction/cancel) | Tenant-scoped | YES | YES |
| Facility Payment Allocation confirm/reverse | YES (backend) | **UNCONFIRMED this pass** — not specifically searched; the expectation lifecycle around it is confirmed wired, allocation-specific buttons not individually verified | Tenant-scoped | Backend Complete / Frontend UNKNOWN | Verify before claiming |
| Facility Collection Alert lifecycle | YES (6 actions: resolve/ack/start-progress/snooze/dismiss/reassign) | **PARTIAL** — only `resolve` confirmed wired (`/billing/facility-payments/alerts/{id}/resolve` found in `api/dashboard.ts`); acknowledge/snooze/dismiss/reassign/start-progress **not found wired anywhere** | Tenant-scoped | Partially Operational | Only demo "resolve"; do not claim the other 5 actions are usable |
| Alert Thresholds management | YES | **NO** (no frontend wiring found) | n/a | NO | **NO** |
| Billing Readiness (patient + tenant) | YES | YES (`BillingDashboard.tsx`) | Tenant-scoped | YES | YES |
| Reports (scheduled/export) | NO (backend doesn't exist) | NO | n/a | NO | **NO** |
| 835 Remittance widget on Billing Dashboard | n/a (not backed by any real endpoint) | Present, but **entirely hardcoded mock data** ("27 files processed," static rows like "2026-01-15 Medicare Part A...") — confirmed by reading `render835Remittance()` in `BillingDashboard.tsx`: no `fetch`/`api.` call anywhere in that function | n/a | **NOT OPERATIONAL — fabricated display data** | **DO NOT DEMO — this panel will show fake numbers that look real** |

## 4. Billing SSOT Audit (Phase 7 — extends Section 6/10)

Applying the RNICA lesson (duplicate writers create instability) to the
areas explicitly requested:

| Domain | Authoritative Table | Authoritative Writer | Authoritative Service | Authoritative API | Authoritative UI | Audit Trail | Multiple writers? |
|---|---|---|---|---|---|---|---|
| Claim | `claims` | *(see Claim Status below — the row itself has 3 separate writers, this is the one domain with a confirmed problem)* | `claim_export_service.py` (creation), various (status) | multiple, see below | `BillingDashboard.tsx` (partial), `ClaimsManagementPage.tsx` (read-only) | Partial (`ClaimExportLog`, no dedicated claim-status event table) | — |
| Claim Status | `claims.status` | **update_claim_status is the intended one; export_patient_claim_edi and post_payments_from_835 also write it** | n/a | `claim_status_router.py` (intended), `billing_router.py` (defective), `payment_service.py` (import path) | **NONE for the intended writer; the defective one has UI** | Only the intended writer calls `append_audit_event` | **YES — 3 writers, documented in full in `claim_status_architecture.md`** |
| Payment | `payments` | `post_payments_from_835` (only writer found) | `payment_service.py` | `app/api/billing_835.py` | None (no upload UI) | Field-only (`match_status`), no event table | No — single writer, but no UI |
| Remittance | `remittance_advices` | `post_payments_from_835` (only writer found) | `payment_service.py` | `app/api/billing_835.py` | `PaymentPostingPage.tsx` (read-only) | Field-only (`status`) | No — single writer |
| Benefit Period | `benefit_periods` | `benefit_period_service.py` | same | (embedded in several routers) | `BillingDashboard.tsx`/readiness views | Not separately audited this pass | Not found — clean per Section 6 |
| Certification | `certifications`, `certification_status_events` | `certification_service.py` | same | `app/api/certifications.py` | `PocCertificationPage.tsx` + certification UI | **YES** — dedicated event table | No — clean, confirmed in Section 6 |
| NOE | `noe_edi_submissions`, patient NOTR columns | `app/api/noe.py` handlers | same | `app/api/noe.py` | `NoeTrackingPage.tsx` (read-only monitoring) | Partial — `ack_status` field, updatable via a real PATCH endpoint, but that endpoint has no frontend wiring | No — single writer, but write-side UI missing |
| Election | (fields on `Patient`/election tracking) | `election_day_service.py` | same | not fully re-enumerated this pass | not confirmed this pass | Not re-audited this pass | UNKNOWN — not re-verified this pass, carry forward as open item |
| Credit Balance | `credit_balance_cases`, `credit_balance_case_events` | `credit_balance_case_service.perform_action` | same | `credit_balance_router.py` | `CreditBalanceReportPage.tsx` — **confirmed wired** | **YES** — dedicated event table | No — clean, and now confirmed end-to-end incl. UI |
| Revenue Reporting | n/a — no dedicated revenue-reporting table; computed on read | `claim_financials.py` (computed, not stored) | same | embedded in report endpoints | `ReportsPage.tsx`, `AgingReportPage.tsx` | n/a (nothing stored to audit) | No — correct "compute on read" pattern, no duplication risk |

**The one confirmed multi-writer instability in the entire billing
system is `Claim.status`.** Every other audited domain either has a
single writer or, where NOE/Payment lack a writer/UI mismatch, that is a
missing-feature gap rather than a duplicate-writer instability risk.

## 5. Revenue Leakage Analysis (Phase 11)

Tracing Patient → Election → Benefit Period → Certification → Claim →
Transmission → Payment → Remittance → Revenue, identifying every point
revenue can become blocked:

| Blockage point | Cause | Evidence | Detection method today | Potential AI alert (detection-only) |
|---|---|---|---|---|
| Election never captured/mis-dated | No confirmed automatic Referral→Admission→Election trigger (Section 7, still UNKNOWN) | `election_day_service.py` computes from an election date but its upstream trigger wasn't traced | None found | Flag patients admitted N days ago with no election date captured |
| Benefit period rollover missed/late | Rollover is calculated, not scheduled — no cron/job found this pass to proactively roll periods | Not re-verified this pass whether rollover is triggered on read vs. a background job | Unknown | Flag patients approaching a benefit-period boundary with no successor period yet created |
| Certification/recert missing or unsigned | Real, tracked in `certification_status_events` | Confirmed real (Section 6) | `billing_readiness_service.py` already checks this as a blocker | *(already exists — Priority 2 in Section 13)* |
| Rate/pricing gap ($0.00 fallback) | Confirmed placeholder rate schedule | `revenue_service.py` explicit "DEFAULT RATE SCHEDULE PLACEHOLDER"; `edi_builder.py` has a real, tested guard (`test_edi_builder_rate_gap.py`) that **blocks** an 837I submission carrying an unresolved `rate_gap_reason` | **Already enforced at the EDI-build layer** — a $0 rate-gap claim line cannot reach a real submission; this is a stronger existing safeguard than earlier sections credited | Flag claims/periods with a live `rate_gap_reason` before they even reach export, so billers fix it proactively instead of hitting the EDI-build error |
| Claim generated but never exported | No confirmed scheduled job to catch claims stuck in READY | `billing_readiness_service.py`/batch-generate skip unready patients but don't re-check later | None found | Flag claims stuck in READY beyond N days |
| Claim exported, status corrupted back to SENT | **Confirmed real bug**, see Claim Status Architecture | Executed test proof | None — this is invisible today, no monitoring exists | Flag any claim whose status regresses (e.g., PAID→SENT) as a data-integrity alert, not a billing decision |
| Claim "sent" but never actually transmitted | No transmission channel confirmed to exist (Section 8/14) | File generated, marked SENT, no clearinghouse call found | None | Flag claims SENT for >N days with no matching remittance as a "possible non-transmission" signal |
| Payment received but unmatched | Confirmed handled correctly — `post_payments_from_835` marks unmatched payments `UNMATCHED` rather than dropping them | Confirmed by execution | `payment_posting_router.py` surfaces an `unmatched_payments` worklist already | *(monitoring layer exists already; an AI narrative summarizing the worklist would be low-risk, Priority-adjacent to existing Section 13 #2)* |
| Denial not appealed within window | `Denial.appeal_deadline` is computed and stored | Confirmed in `payment_service.py` | No confirmed proactive alert on approaching deadline | Flag denials approaching `appeal_deadline` with no appeal action recorded |
| Credit balance case stalls | Full lifecycle exists with audit trail | Confirmed real + wired | Case list is read-only-browsable via UI | Flag cases open >N days past `repayment_due_at` |

**Most valuable new finding here**: the rate-gap safeguard
(`test_edi_builder_rate_gap.py`) is **stronger than Section 3/8
originally credited** — it isn't just "a known placeholder," it is an
enforced gate that provably blocks a bad claim line from reaching an
837I. The actual leakage risk is therefore narrower than previously
stated: it's about claims *silently sitting* with an unresolved rate gap
(no proactive alert), not about bad pricing slipping through undetected
at export time.

## 6. NOE Validation (Phase 12) — dedicated, verified, not inferred

| Item | Finding | Verified how |
|---|---|---|
| NOE Table | `noe_edi_submissions` + NOTR-tracking columns on `Patient` | Model read directly |
| NOE Writer | `app/api/noe.py` handlers (submission PATCH, 837I generation, edi-submission status PATCH) | Grep + direct read of `noe.py` |
| NOE UI | `NoeTrackingPage.tsx` — **read-only monitoring only** | Confirmed only `fetchNoeTracking` import; no write-action import found |
| NOE Endpoint | 12+ routes confirmed in Section 1.3 (submission GET/PATCH, generate-837i, edi-submissions list/status) | Direct read of `noe.py` |
| NOE Statuses | Submission status (open text field, not a formal enum re-verified this pass) + `ack_status` (updatable via real PATCH, but that PATCH has no UI) | Direct read |
| NOE Reports | None dedicated — NOE data surfaces only via `NoeTrackingPage.tsx`'s monitoring table | Confirmed by absence |
| NOE Readiness Rules | `billing_readiness_service.py` checks "NOE on file" as a readiness blocker (per Section 1.4/2) | Not re-executed this pass — carried from prior code-read confidence, **not upgraded to behaviorally-verified this pass** |
| NOE Source of Truth | `noe_edi_submissions` table, single writer path (`app/api/noe.py`) — no duplicate writer found | Grep confirmed no other writer |
| NOE Demo Readiness | 🟡 YELLOW — tracking/monitoring is real and safe to demo; **837I generation and PDF generation have no frontend wiring and should not be demoed as staff-usable**, only as "the backend can do this" | Direct grep of frontend for `generate-837i`/`generate-pdf` — zero matches |

## 7. Biller Persona Review (Phase 13)

| Question | Current answer available? | Screen | API | Report | Gap |
|---|---|---|---|---|---|
| Has NOE been submitted? | YES | `NoeTrackingPage.tsx` | `GET /billing/noe-tracking` | Table view, no export | None significant |
| When is recert due? | YES | `PocCertificationPage.tsx` | `GET /billing/poc-certification-status` | Table view | None significant |
| Why is this patient not billable? | YES | `BillingDashboard.tsx` (readiness) | `GET /billing/readiness/{patient_id}`, `/readiness-report` | Blocker labels shown | Blocker reasons are structured but not narrated (Priority-2 AI opportunity, Section 13) |
| Which certifications expire this week? | **PARTIAL** | `PocCertificationPage.tsx` shows current-period status; a specific "expiring this week" filter/sort was not confirmed to exist | same endpoint | none dedicated | Needs a due-date filter/sort, or an AI monitor (Section 13 Priority 3) |
| Which claims remain unpaid? | YES | `ClaimsManagementPage.tsx`, `AgingReportPage.tsx` | `GET /billing/claims`, `/billing/aging-report` | Aging Report | None significant |
| Which claims failed transmission? | **NO** | none | none — no `ClaimTransmission`/ack-status UI exists for claims (unlike NOE's ack_status field, which itself has no UI either) | none | **Real gap** — there is no concept of "failed transmission" tracked anywhere for claims, because there is no transmission channel to fail from (Section 14 Finding) |
| Which claims have matching remittances? | **PARTIAL** | `PaymentPostingPage.tsx` shows an `unmatched_payments` worklist (the inverse view) | `GET /billing/remittances` | none dedicated "claim ↔ remittance match" report | The data to answer this exists (`payments.claim_id`, `match_status`) but there's no claims-side view of "which of my claims have a posted payment" — only the payments-side "which payments are unmatched" |

## 8. Top Critical Billing Risks (Phase 8 — replaces the generic Top 10)

| Rank | Risk | Evidence | Severity |
|---|---|---|---|
| 1 | **Claim status rollback after payment, reachable via a live, mislabeled UI button** | Executed test proof (Finding A) + confirmed frontend reachability via `BillingDashboard.tsx`'s "Export to Excel" button + `PAID`/`DENIED` filter options | **CRITICAL** |
| 2 | **Backend billing capability lacking UI** (835 upload, enforced claim-status endpoint, NOE 837I/PDF generation, CMS-838 export, 5 of 6 alert actions, alert thresholds) | Confirmed by repo-wide frontend search per capability (Section 3 above) | **CRITICAL** |
| 3 | **Fabricated/mock data rendered inside a real billing screen** (835 Remittance widget on `BillingDashboard.tsx` shows hardcoded numbers with no backing `fetch` call) | Direct code read of `render835Remittance()` | **CRITICAL** (new this pass — highest-risk-to-credibility item for Thursday specifically) |
| 4 | Payment writer architecture (backend) is real and correct, but has no audit-event trail for claim-status changes it causes | Confirmed by execution + absence check | **HIGH** |
| 5 | Claim transmission workflow not proven to exist at all (no clearinghouse channel, no `ClaimTransmission` model) | Repo-wide search, zero results | **HIGH** |
| 6 | NOE workflow's write-side (837I/PDF generation, ack-status update) not reachable from any UI | Confirmed by repo-wide frontend search | **HIGH** |
| 7 | No configurable rate schedule / hardcoded revenue codes | Unchanged from Section 3/8 | **HIGH** |
| 8 | Revenue reporting lineage is "compute on read," correctly avoiding duplication, but means no historical/point-in-time revenue snapshot exists for audit | New observation this pass | **MEDIUM** |
| 9 | Hospice cap tracking visibility is real, but cross-agency transfer attribution is a self-acknowledged accuracy risk | Unchanged from Section 3/8 | **MEDIUM** |
| 10 | Facility Collection Alert lifecycle is 1/6 actions usable from the UI (only "resolve") | New finding this pass | **MEDIUM** |

## 9. Thursday Demo Rules (Phase 9)

| Capability | CAN DEMONSTRATE | EXISTS BUT NOT USABLE | DO NOT CLAIM |
|---|---|---|---|
| Billing Readiness | ✅ | | |
| Benefit Period tracking | ✅ | | |
| Certification/Recert lifecycle | ✅ | | |
| NOE/NOTR tracking (monitoring) | ✅ | | |
| NOE 837I/PDF generation | | ✅ (backend only) | Don't demo as staff-usable |
| Claims Management (viewing) | ✅ | | |
| Claim status enforced endpoint | | ✅ (backend only, no UI) | |
| Claim EDI export ("Export to Excel" button) | | | ❌ **DO NOT CLICK THIS BUTTON LIVE** — real risk of triggering the confirmed status-rollback bug on a real claim, and its label is misleading regardless |
| Claim transmission to a payer | | | ❌ **DO NOT CLAIM** — no channel exists |
| 835 Remittance widget (dashboard) | | | ❌ **DO NOT DEMO — data is fabricated**, not a real feed |
| Payment Posting (monitoring) | ✅ (as monitoring only) | | Don't claim staff can post payments in-app |
| 835 Upload (real capability) | | ✅ (backend only) | Don't demo — no UI |
| Denials & Appeals | ✅ | | |
| Eligibility Verification | ✅ | | |
| Hospice Cap Calculation | ✅ | | Caveat cross-agency transfer risk if asked |
| Aging Report | ✅ | | |
| Credit Balance Report + Case Actions | ✅ (now confirmed frontend-wired) | | |
| CMS-838 Export | | ✅ (backend only) | Don't demo — no UI |
| Facility Payment expectation lifecycle | ✅ (now confirmed frontend-wired) | | |
| Facility Collection Alerts | ✅ (resolve action only) | ✅ (5 other actions, backend only) | Don't demo acknowledge/snooze/dismiss/reassign/start-progress |
| Alert Thresholds management | | ✅ (backend only) | Don't demo — no UI |
| Scheduled/exportable reports | | | ❌ **DO NOT CLAIM** — doesn't exist at all |
| Rate schedule / revenue code configuration | | | ❌ **DO NOT CLAIM** — hardcoded placeholder |

## 10. AI Billing Prioritization — refined roadmap only (Phase 10, no development)

The five priorities specified are accepted as-is, cross-checked against
this pass's new evidence, with one addition and one re-ordering
rationale:

1. **Billing Readiness AI** (READY/BLOCKED/AT RISK with evidence) —
   inputs (Election, Benefit Period, Certification, NOE, Claim) are all
   confirmed real, tracked data as of this pass. No new gap found that
   would block this being priority 1.
2. **Certification Monitor** — unchanged, data confirmed real
   (`certification_status_events`).
3. **Revenue Leakage Monitor** — this pass's Revenue Leakage Analysis
   (item 5 above) sharpens the detection targets: rate-gap claims stuck
   pre-export, claims SENT >N days with no remittance, denials
   approaching `appeal_deadline`, unmatched payments aging.
4. **Claim Risk Monitor** — **new evidence to fold in**: this monitor
   should explicitly include "claim status regressed unexpectedly"
   (PAID→SENT) as a detection target — this is no longer hypothetical,
   it's a proven, currently-invisible failure mode with zero existing
   monitoring.
5. **Daily Billing Work Queue** — unchanged, data sources for all four
   listed categories are confirmed to exist.

Confirmed still explicitly out of scope, per instruction: AI Claim
Creation, AI Coding, AI Payment Prediction, AI Denial Appeals, AI Billing
Decisions. Every priority above remains detect-and-explain only.

## 11. Updated Maturity Scores (Phase 14) — behavioral evidence only

Re-scored only where this pass produced new behavioral evidence (execution
or confirmed frontend reachability); domains not re-tested keep their
Section 11 score with a note.

| Domain | Prior score (code-read) | Updated score (behavior/reachability) | Basis |
|---|---|---|---|
| Claim Status Tracking | 3 | **2** (Functional, not Operational) | Confirmed by execution that the primary writer is correct but unreachable from UI, and the reachable UI path is defective |
| Claim Export / EDI Generation | 4 | **2** | Real generation confirmed, but the only UI path to it is mislabeled and can trigger the confirmed status bug |
| Payment Posting (write/matching) | 0–1 | **2** (backend), **0** (staff-usable) | Backend confirmed correct and operational by execution; zero UI, so end-to-end score for a biller remains 0 |
| Credit Balance Case Management | 5 | **5** (confirmed, unchanged) | Frontend wiring now positively confirmed, not just inferred |
| Facility Payment (expectations/allocations/alerts) | 4 | **3** (Operational for expectations, Functional-only for 5/6 alert actions) | Frontend confirmed for expectation lifecycle and alert "resolve"; other 5 alert actions have no UI |
| NOE / NOTR | 4 | **2** for the write side (837I/PDF generation, ack-status), **4** unchanged for tracking/monitoring | Tracking is real and demoable; generation/ack-update has no UI |
| CMS-838 Export | 3 | **1** | Backend logic is real and honest about its own gaps, but zero reachability |
| Reports (Aging/Credit Balance/Facility Collections/Cap) | 4 | **4** (unchanged) | Already confirmed frontend-wired |
| Revenue code / rate schedule | 1 | **1** (unchanged), but note the rate-gap **guard** at EDI-build time scores separately as **4** (a real, tested, enforced safeguard) | `test_edi_builder_rate_gap.py` proves the guard works |
| Election / Referral / Admission / Discharge / Transfer / Revocation | unchanged from Section 11 | unchanged | Not behaviorally re-verified this pass |

**Overall weighted maturity, revised**: prior estimate (Section 11) was
~3.1/5 based on code-existence confidence. Applying "behavior, not
existence" drops several previously-4-scored items to 2, driven almost
entirely by the frontend-reachability gap, not new backend defects (with
the one exception of the confirmed Claim.status bug). Revised overall
estimate: **~2.6/5** for *staff-usable, demoable, behaviorally-proven*
maturity — versus ~3.1/5 for *code-exists* maturity. The gap between
those two numbers (0.5) is, numerically, the size of the
"Implemented-Backend ≠ Usable-Feature" problem across the whole billing
platform.

---

# FINAL SUMMARY

## A. What is VERIFIED (executed, not inferred)

- `update_claim_status` correctly refuses an invalid transition (409),
  proven by execution.
- `export_patient_claim_edi` genuinely and unconditionally overwrites
  `claim.status = "SENT"` regardless of current status — proven by
  execution against a `PAID` claim.
- `post_payments_from_835` correctly posts a real `RemittanceAdvice` +
  matched `Payment`, advances a `SENT` claim to `PAID`, creates a real
  `Denial` row on a denial CARC code, and correctly refuses to move an
  already-`DENIED` claim on a later posting — all proven by execution.
- The rate-gap EDI-build guard (`test_edi_builder_rate_gap.py`) correctly
  blocks an unpriced claim line from reaching 837I text — proven by
  existing, passing tests.
- Credit Balance case actions and Facility Payment expectation lifecycle
  are genuinely wired end-to-end to real frontend UI (confirmed by
  locating their exact imports/handlers), correcting this pass's initial
  assumption that they might not be.
- The "Export to Excel" button on `BillingDashboard.tsx` genuinely calls
  the claim-EDI-export endpoint against an arbitrary filtered row,
  confirmed by reading its `onClick` handler and the endpoint it calls.
- The 835 Remittance widget on `BillingDashboard.tsx` genuinely renders
  hardcoded, non-live data with no backing API call, confirmed by reading
  its render function in full.

## B. What is IMPLEMENTED but NOT USABLE (backend real, no frontend path)

835 Upload; the enforced claim-status endpoint; NOE 837I generation; NOE
PDF generation; NOE ack-status update; CMS-838 export; Facility
Collection Alert actions other than "resolve" (acknowledge, snooze,
dismiss, reassign, start-progress); Alert Thresholds management.

## C. What remains UNKNOWN (neither executed nor frontend-checked this pass)

Referral→Admission→Election automatic linkage; Discharge→billing closure
trigger; Transfer/cross-agency cap attribution beyond the code's own
caveats; Election tracking's own writer/SSOT (not re-audited this pass);
whether Facility Payment Allocation confirm/reverse specifically has its
own frontend wiring (the surrounding expectation lifecycle is confirmed,
this specific action pair was not individually checked); whether a
background job exists anywhere to proactively roll benefit periods or
re-check stuck READY claims.

## D. What should be built next (sequencing recommendation, not a decision)

Given everything above, the two highest-leverage, lowest-risk fixes —
**before any new feature work** — are:
1. **Fix the confirmed Claim.status bug**: make `export_patient_claim_edi`
   consult the same transition rule `update_claim_status` already
   enforces (or the equivalent guard `post_payments_from_835` already
   implements correctly) before writing a new status. This is a small,
   surgical, well-evidenced fix, not a redesign.
2. **Remove or clearly label the fabricated 835 widget** on
   `BillingDashboard.tsx` before Thursday — this is a demo-credibility
   risk independent of any engineering roadmap decision.

Beyond those two, prioritization (which missing UI to build first: 835
upload, alert actions, NOE generation, CMS-838, etc.) is a genuine
product decision this document does not make — it only supplies the
evidence. Recommend making that call after Thursday's biller feedback, so
the missing-UI backlog is prioritized by what billers actually ask for
first, rather than by engineering guesswork.

---

# SECTION 5 — DEMO READINESS (Thursday)

## Can demonstrate
- Billing dashboard / patient & tenant readiness rollups
- Benefit period tracking and rollover
- Certification lifecycle (draft → sign → finalize) with physician
  signing and audit trail
- NOE tracking, submission status, 837I EDI generation, late-penalty calc
- Claims management screen, claim status state machine, claim export
  payload
- Denials & Appeals registry
- Eligibility verification / roster
- Aging Report, Credit Balance Report, Facility Collections Report,
  Hospice Cap Calculation
- Facility payment expectation/allocation/alert full lifecycle
- Election addendum deadline compliance tracking

## Cannot demonstrate (confirmed missing/placeholder)
- Configurable payer rate schedules / real revenue pricing (placeholder only)
- Scheduled/downloadable report exports (no format export exists)
- Settings screen (ComingSoon placeholder)
- Re-election-after-revocation billing workflow (explicit TODO, not built)

## Needs development or verification before claiming it works
- Real claim EDI transmission (`export-patient-claim-edi`) — **verify by
  reading the code before Thursday**; do not demo this as "submits
  claims" unless confirmed
- Payment posting write/matching path and underlying `payments`/
  `payment_adjustments`/`remittance_advices` tables
- Credit balance case creation/action endpoints and CMS-838 export
- Facility payment allocation precedence slots 1–4 (currently stubbed)
- Discharge/referral/admission billing linkage — not traced this pass

## Recommended next step
Before Thursday, spend a short, targeted follow-up pass (not a rebuild)
confirming the 5 "needs verification" items above by reading their exact
code — each is a fast read, not new development — so the demo team knows
precisely what to say "yes" vs. "not yet" to.

> **2026-09-08 update**: That follow-up pass is now done (see the update
> note in the header and Sections 6–9 below). Demo-readiness conclusions
> above are superseded where Section 6–9 findings differ; the most
> important correction: claim EDI *generation* is real, claim EDI
> *transmission* to a clearinghouse is not.

---

# SECTION 6 — SSOT (SINGLE SOURCE OF TRUTH) AUDIT

Purpose: for each billing-relevant data element, confirm there is exactly
one canonical writer/owner, and flag any element that is duplicated,
derived-and-cached, or ambiguous about which table/service governs it.

| Data element | Canonical source (SSOT) | Duplication / ambiguity risk | Status |
|---|---|---|---|
| Patient demographic/insurance identity | `app.models.patient.Patient`, `PatientPayer` | None found — billing services consistently read through `resolve_primary_secondary_payer_names`/`resolve_payer_type_for_claim` rather than re-deriving payer identity locally | CLEAN |
| Admission status | `app.models.admission.Admission` + `AdmissionStatusHistory` (audit trail) + `Patient.admission_status` (denormalized current value) | `Patient.admission_status` is a denormalized copy of `Admission`/`AdmissionStatusHistory` — standard current-value cache pattern, low risk **if** it's only ever written by one code path | PARTIAL — verify only `AdmissionStatusHistory`-writing code path also updates `Patient.admission_status`, not two independent writers |
| Discharge data | Fields live directly on `Patient` (`discharge_date`, `discharge_reason`, etc.) — no separate `Discharge` table | Single owner (`Patient` row itself), so no cross-table duplication, but it means discharge has no dedicated audit-event trail the way certifications/credit-balance cases do | PARTIAL — SSOT is clean (one table) but lacks an audit trail comparable to `CertificationStatusEvent`/`CreditBalanceCaseEvent` |
| Benefit period | `app.models.benefit_period.BenefitPeriod`, rollover computed by `benefit_period_service.py` | Downstream consumers (readiness, cap service) read the table rather than recompute period boundaries independently | CLEAN |
| Certification status | `Certification` + `CertificationStatusEvent` (explicit audit trail) | None found | CLEAN |
| Claim status | `Claim.status`, transitions enforced centrally in `claim_status_router.py` `ALLOWED_TRANSITIONS` (`READY→SENT`, `SENT→ACCEPTED/DENIED`, `ACCEPTED→PAID/DENIED`); also set directly by `export-patient-claim-edi` (`claim.status = "SENT"`) | **Confirmed: two write paths, and the second bypasses the enforced state machine.** `export_patient_claim_edi` sets `claim.status = "SENT"` directly with no check of `ALLOWED_TRANSITIONS` or the claim's current status — it will happily overwrite a claim that's already `ACCEPTED`, `PAID`, or `DENIED` back to `SENT` | **PARTIAL — confirmed enforcement gap**, not just a risk. Should require the same transition check before allowing an EDI re-export to move status |
| Claim financials (balance) | Computed on read by `claim_financials.py:load_claim_financials()` from `Claim` + `Payment` + `PaymentAdjustment`, not stored/cached | Correct pattern — no risk of a stale cached balance | CLEAN |
| Revenue code mapping | Hardcoded dict in `claim_segment_service.py:_map_revenue_code()` | Single location, but it's a **hardcoded map, not a data-driven master table** — so "SSOT" here is source code itself, not configurable data. Flagged already in Section 3, gap #3 | PARTIAL — technically single-sourced, but wrong kind of source for production configurability |
| Rate schedule / pricing | `revenue_service.py`, explicit "DEFAULT RATE SCHEDULE PLACEHOLDER" | Same as above — one placeholder source, no real payer-specific rate table | PARTIAL/MISSING |
| NOE/NOTR submission status | `NoeEdiSubmission` records, updated via `noe.py:/edi-submissions/{id}/status` | None found | CLEAN |
| Credit balance case status | `CreditBalanceCase` + `CreditBalanceCaseEvent` audit trail, all writes funneled through `credit_balance_case_service.perform_action` | None found — good pattern, single service owns all transitions | CLEAN |
| Facility payment expectation/allocation | `FacilityPaymentExpectation`/`FacilityPaymentAllocation` + `FacilityPaymentAuditLog` | None found | CLEAN |
| Hospice cap usage | `HospiceCapRecord`, computed by `hospice_cap_service.py` | Service's own comments flag that transfers/live-discharges to another agency during the cap year are a known risk to correctly attributing usage across agencies — an accuracy risk in the calculation itself, not a duplication/SSOT problem | PARTIAL — calculation-accuracy caveat, not a structural SSOT issue |
| Payments / remittances | `Payment`, `RemittanceAdvice` tables — read-only via `payment_posting_router.py` | **No in-app write/ingestion path found this pass.** Unclear if these are populated by an external ERA-import job, a manual seed, or something not yet reviewed. This is the biggest open SSOT question: without knowing the writer, we cannot confirm there's exactly one | UNKNOWN — needs a follow-up read of how `payments`/`remittance_advices` rows are actually created before relying on this data being trustworthy for the demo |

**SSOT audit conclusion**: most billing state has a clean single writer
with proper audit trails (certifications, credit-balance cases, facility
payments, NOE). The two areas needing attention are (1) confirming
`Claim.status` isn't written from two uncoordinated code paths, and (2)
identifying the actual writer of `payments`/`remittance_advices` before
trusting Payment Posting data in a live demo.

---

# SECTION 7 — WORKFLOW LINKAGE AUDIT

Traces how each pre-billing clinical/operational event actually connects
into the billing pipeline, based on the models found this pass.

| Link | Confirmed connection | Status |
|---|---|---|
| Referral → Admission | `Referral` model exists; not traced this pass whether it auto-creates/links to an `Admission` record or is a manual staff action | UNKNOWN |
| Admission → Election | Not traced whether `Admission` finalization automatically triggers election-day tracking (`election_day_service.py`) or whether election is entered independently | UNKNOWN |
| Election → Benefit Period | Confirmed — `election_day_service.py` and `benefit_period_service.py` share the same election-date basis for period-length math | IMPLEMENTED |
| Benefit Period → Certification/Recertification | Confirmed — certification due dates and F2F enforcement (`recert_f2f_enforcement.py`) are keyed to benefit period boundaries | IMPLEMENTED |
| Certification → Claim readiness | Confirmed — `billing_readiness_service.py` explicitly checks for signed CTI/certification as a claim-readiness blocker | IMPLEMENTED |
| NOE filing → Claim readiness | Confirmed — `check_patient_billing_readiness` checks "NOE on file" as a blocker (per `batch_generate_patient_billing` docstring) | IMPLEMENTED |
| Claim readiness → Claim generation | Confirmed — `generate_patient_billing`/`batch_generate_patient_billing` both gate on readiness before generating, skipping unready patients rather than force-billing | IMPLEMENTED |
| Claim generation → Claim export/EDI | Confirmed — `export-patient-claim` then `export-patient-claim-edi` chain, both real | IMPLEMENTED |
| Claim EDI → Payment | **Not confirmed.** No transmission channel was found from EDI export to a clearinghouse/payer, and no confirmed ingestion path was found for how `payments`/`remittance_advices` get created — so the link between "claim sent" and "payment received" in this codebase is not demonstrably closed-loop yet | PARTIAL/UNKNOWN — this is the biggest workflow gap: the pipeline is real up through "claim marked SENT," but what happens after that (transmission, ERA ingestion) was not found |
| Payment → Credit Balance detection | Confirmed — `credit_balance_service.py:build_credit_balance_report()` computes net balance directly from `Payment`/adjustment data | IMPLEMENTED |
| Discharge → Hospice Cap true-up | Partially confirmed — `hospice_cap_service.py` comments explicitly acknowledge live-discharge/transfer scenarios as an accuracy risk for cap usage attribution across agencies, implying the calculation is aware of discharge but may not fully solve for cross-agency transfer cases | PARTIAL |
| Discharge → Claim finalization | Not traced this pass whether a discharge automatically triggers final-claim generation or closes the benefit period; `Patient.discharge_date` exists but no confirmed billing-side trigger was found | UNKNOWN |
| Revocation → Benefit Period closure | `election_day_service.py` has an explicit TODO for re-election-after-revocation/gap handling — meaning the reverse direction (revocation properly closing out billing) is also unconfirmed and likely incomplete | PARTIAL/MISSING |
| Transfer (agency-to-agency) → Cap/claim continuity | No dedicated `Transfer` model found; only inferred from cap-service comments about "transferred in/out" patients. This is the least-modeled workflow stage in the entire billing pipeline | MISSING (as a distinct, modeled workflow) |

**Workflow linkage audit conclusion**: the core middle of the pipeline
(Election → Benefit Period → Certification → Readiness → Claim
Generation → Claim Export/EDI) is solidly and consistently linked with
real gating logic. The two ends of the pipeline are the weakest links:
**upstream** (Referral → Admission → Election is not confirmed to be an
automatic/enforced chain) and **downstream** (Claim SENT → actual
payment receipt has no confirmed transmission or ERA-ingestion path, and
Discharge/Revocation/Transfer's effect on billing closure is largely
unconfirmed).

---

# SECTION 8 — TOP 10 GAP LIST (FINAL, RANKED)

Refined and re-ranked using the Section 6/7 findings (supersedes the
draft gap table in Section 3, which remains as supporting detail):

| Rank | Gap | Why it matters | Priority |
|---|---|---|---|
| 1 | **No confirmed claim transmission channel** — EDI file is generated and claim is marked SENT, but no SFTP/clearinghouse/payer API call was found | Directly determines whether "the system bills claims" is true end-to-end, or stops at file generation | **CRITICAL** |
| 2 | **No confirmed payments/remittance ingestion path** — `payments`/`remittance_advices` tables are read-only from the app's perspective this pass | Without knowing how money gets into these tables, Payment Posting data can't be trusted as live/trustworthy for the demo | **CRITICAL** |
| 3 | **No configurable rate schedule / revenue pricing** — explicit placeholder, `$0.00` fallback | Direct revenue-leakage risk; every claim's dollar amount is suspect until this is real | **HIGH** |
| 4 | **Revenue code mapping is hardcoded, not a master table** | Blocks onboarding new payers/LOC types without a code change | **HIGH** |
| 5 | **Revocation → re-election/gap handling is an explicit TODO** | Leaves a known correctness gap in benefit-period continuity for revoked patients | **HIGH** |
| 6 | **No dedicated Transfer model/workflow** | Cap-usage attribution across agencies is explicitly flagged as a risk in `hospice_cap_service.py`'s own comments | **HIGH** |
| 7 | **Claim.status enforcement bypass — confirmed** (status-transition endpoint enforces `ALLOWED_TRANSITIONS`, but `export-patient-claim-edi` writes `claim.status = "SENT"` directly with no check of current status) | Re-exporting EDI for an already `ACCEPTED`/`PAID`/`DENIED` claim would silently revert it to `SENT`, corrupting the audit trail | **HIGH** (upgraded from MEDIUM — confirmed, not hypothetical) |
| 8 | **Discharge → billing-closure trigger unconfirmed** | Unclear whether discharging a patient reliably finalizes their billing (final claim, cap true-up) or requires manual staff follow-up | **MEDIUM** |
| 9 | **Discharge has no dedicated audit-event trail** (unlike certifications/credit-balance cases) | Weaker auditability for one of the most compliance-sensitive events in the workflow | **MEDIUM** |
| 10 | **No scheduled/downloadable report export (PDF/CSV)** | Operational inconvenience for billing staff, but does not block core billing correctness | **LOW** |

---

# SECTION 10 — BILLING SSOT AUDIT (STATUS: COMPLETE)

The SSOT audit itself was already completed in **Section 6** above
(2026-09-08 pass) — this section is a status marker plus the rollup
verdict, not a re-audit, per instruction not to repeat completed work.

**Rollup verdict**: 9 of 12 audited data domains are **CLEAN** (single
writer, no duplication) — Patient/Payer identity, Benefit Period,
Certification, Claim financials, NOE/NOTR submission, Credit Balance
case, Facility Payment expectation/allocation. 3 are **PARTIAL/UNKNOWN**
and carry forward as open items into the Gap List (Section 8) and
Maturity Score (Section 11) rather than being repeated here:
- Claim.status (confirmed enforcement-bypass — Gap #7)
- Admission status denormalization (`Patient.admission_status` vs.
  `AdmissionStatusHistory`) — needs a one-time confirmation that only one
  code path writes both
- Payments/remittance_advices writer — unidentified (Gap #2)

No further SSOT investigation is planned unless one of these three specific
open items needs resolution before a specific engineering task depends on it.

---

# SECTION 11 — BILLING MATURITY SCORE

Scoring rubric per functional domain, 0–5 scale:
**0** = missing, **1** = stub/placeholder only, **2** = partial/read-only,
**3** = functional core with confirmed gaps, **4** = solid with minor
caveats, **5** = fully implemented, audited, production-grade.

| Domain | Score | Basis |
|---|---|---|
| Election / Election Addendum | 4 | Deadline compliance calc real; revocation/re-election gap keeps it off 5 |
| Benefit Period | 5 | Storage, rollover calc, display, downstream consumers all confirmed real |
| Certification / Recertification | 5 | Full lifecycle + F2F enforcement + audit trail, physician-signer enforced |
| NOE / NOTR | 4 | Submission tracking + real 837I generation + penalty calc; PDF generation endpoint unread |
| Claim Preparation (lines, financials) | 4 | Real claim-line building and balance computation; pricing depends on placeholder rate schedule (domain below) |
| Revenue Code / Rate Schedule | 1 | Hardcoded map + explicit placeholder rate schedule + `$0.00` fallback |
| Claim Status Tracking | 3 | Real state machine, but confirmed enforcement bypass in EDI-export write path |
| Claim Export / EDI Generation | 4 | Real 837I file generation, batch tracking, claim marked SENT |
| Claim Transmission (to payer/clearinghouse) | 0 | No transmission channel found — file is generated and stops there |
| Payment Posting (read/monitoring) | 4 | Real ERA registry, MTD totals, payer breakdown, unmatched worklist |
| Payment Posting (write/matching) | 0–1 | No in-app posting/matching action found; ingestion writer unidentified |
| Credit Balance Case Management | 5 | Full lifecycle, audited events, reason codes, tenant scoping |
| CMS-838 Export | 3 | Real, but self-reports schema gaps (MBI/ICN/ToB/dates NOT_AVAILABLE) |
| Facility Payment (expectations/allocations/alerts) | 4 | Full lifecycle real; allocation precedence slots 1–4 internally stubbed |
| Hospice Cap Calculation | 4 | Real calc against published CMS values; cross-agency transfer attribution flagged as an accuracy risk by the code's own comments |
| Billing Readiness (patient + tenant) | 4 | Real, enforced 4-point pre-check; does not cover pricing accuracy or transmission (see Section 9 map) |
| Reports (Aging/Credit Balance/Facility Collections/Cap) | 4 | All real, live | 
| Reports (scheduled/exportable) | 0 | Explicitly not implemented |
| Referral/Admission linkage into billing | 1 | Models exist; automatic linkage into election/billing not confirmed |
| Discharge linkage into billing | 2 | Rich fields exist on Patient; no confirmed automatic billing-closure trigger, no dedicated audit trail |
| Revocation handling | 1 | Explicit TODO for re-election/gap handling |
| Transfer handling | 0 | No dedicated model; only referenced as a risk in cap-service comments |
| Billing Provider / Agency Access Control | 5 | Full org/assignment/scope model, consistently enforced across every router |

**Overall weighted maturity**: approximately **3.1 / 5** — the system is
strong in the compliance-heavy middle of the pipeline (certification,
benefit period, NOE, claim preparation) and weak at the financial edges
(rate configuration, claim transmission, payment ingestion) and at the
clinical-operational edges (referral/admission linkage, revocation,
transfer).

---

# SECTION 12 — THURSDAY DEMO READINESS MATRIX

| Feature | Demo status | What to say | What NOT to say |
|---|---|---|---|
| Billing Dashboard / Readiness | 🟢 GREEN | "Confirms every patient has a signed cert, F2F when required, active POC, NOE on file, and a resolvable payer sequence before billing" | Don't say readiness confirms pricing accuracy |
| Benefit Period tracking | 🟢 GREEN | Full storage/rollover/display, safe to demo live | — |
| Certification / Recertification lifecycle | 🟢 GREEN | Draft→sign→finalize, physician-only signing, audit trail | — |
| NOE Tracking + 837I generation | 🟢 GREEN | Real EDI text generation, late-penalty calc | Don't claim PDF generation works — unverified |
| Claims Management / Claim Status | 🟡 YELLOW | State machine is real | Don't claim the status can never be corrupted — the EDI re-export path bypasses the transition check |
| Claim Export (837I file) | 🟡 YELLOW | "Generates a valid 837I claim file and marks the claim SENT" | **Do not say the system electronically transmits/submits claims to a clearinghouse or payer** — no transmission channel found |
| Denials & Appeals | 🟢 GREEN | Real registry | — |
| Eligibility Verification | 🟢 GREEN | Real check + roster | — |
| Payment Posting | 🟡 YELLOW | "Shows received ERAs, MTD totals, unmatched worklist" | Don't say staff can post/match payments in-app — no write action found; don't claim to know where the data comes from |
| Cap Calculation | 🟢 GREEN | Real calc vs. published CMS values | Caveat: cross-agency transfer attribution is a known accuracy risk per the code's own comments |
| Aging Report | 🟢 GREEN | Live and real | — |
| Credit Balance Report + Case Management | 🟢 GREEN | Full case lifecycle, reason codes, audit events | — |
| CMS-838 Export | 🟡 YELLOW | "Produces a CMS-838-shaped export for Medicare-reportable cases" | Don't say it's fileable as-is — several required fields are explicitly `NOT_AVAILABLE_IN_SCHEMA` |
| Facility Collections / Facility Payment lifecycle | 🟢 GREEN | Full expectation/allocation/alert lifecycle | Caveat: allocation precedence slots 1–4 are internally stubbed |
| Reports (general snapshot) | 🟡 YELLOW | Live in-app view is real | Don't say reports can be scheduled or exported to PDF/CSV — not implemented |
| Settings | 🔴 RED | — | It's a placeholder ("Coming Soon") screen, don't open it live |
| Revenue code / rate configuration | 🔴 RED | — | Do not demo pricing as configurable — it's a hardcoded map + placeholder rate schedule |
| Revocation handling | 🔴 RED | — | Don't claim revoked patients' benefit periods/re-elections are fully handled — explicit TODO in code |
| Referral/Admission → billing auto-linkage | 🔴 RED (unverified) | — | Don't claim this is automatic without a direct verification read first |
| Discharge → billing closure | 🔴 RED (unverified) | — | Don't claim discharge automatically finalizes billing without verification first |

**Overall demo-readiness color**: 🟡 YELLOW — a strong, honest demo is
very achievable by leading with the 🟢 GREEN items (readiness,
certification, benefit period, NOE, cap, aging, credit balance, facility
collections) and being explicit and confident about the 🟡/🔴 caveats
rather than avoiding them; nothing found this pass indicates a 🔴 item was
ever falsely presented as done.

---

# SECTION 13 — AI BILLING PRIORITIZATION MATRIX

Scope reminder, per explicit instruction: **no AI that writes claims, and
no AI-generated billing/eligibility/certification/discharge decisions.**
Every item below is detection, monitoring, or summarization only — the
same constraint as Section 4, now scored for prioritization.

Scored on **Impact** (1–5, business value if built) × **Effort** (1–5,
lower = easier) × **Risk** (1–5, lower = safer to ship) → **Priority
Score = Impact ÷ Effort ÷ Risk-weight**, ranked descending.

| # | AI opportunity | Impact | Effort | Risk | Priority | Rationale |
|---|---|---|---|---|---|---|
| 1 | Revenue leakage detection (flag claims hitting the `$0.00` fallback or unmapped revenue codes) | 5 | 2 | 1 | **HIGHEST** | Directly protects revenue; purely a detection query over existing data (claim lines vs. `_map_revenue_code()`), no new data model needed, zero decision-making involved |
| 2 | Claim-readiness blocker summarization (narrate existing `check_patient_billing_readiness` blockers) | 4 | 1 | 1 | **HIGHEST** | Cheapest to build — the structured blocker data already exists; this is pure narrative rendering of existing computed facts, same safe pattern already proven by the recert evidence-synthesis work |
| 3 | Certification/F2F due-date monitoring & alerting | 4 | 2 | 1 | **HIGH** | Data already tracked in `CertificationStatusEvent`/benefit period; purely a proactive surfacing layer, no new judgment |
| 4 | Benefit period / cap-year threshold monitoring | 4 | 2 | 1 | **HIGH** | Same pattern, existing `hospice_cap_service.py`/`benefit_period_service.py` data |
| 5 | Documentation completeness monitoring (visit notes/POC gaps before claim prep) | 3 | 3 | 2 | **MEDIUM** | Valuable but requires reading across visit-note/POC data not yet centrally exposed for this purpose — more integration effort |
| 6 | Billing queue prioritization / triage ranking | 3 | 2 | 2 | **MEDIUM** | Useful, but needs care that "priority" ranking doesn't drift into an implicit billing recommendation — must stay purely urgency/deadline-based sorting |
| 7 | Claim-readiness narrative rollup at the tenant level (cross-agency) | 3 | 3 | 2 | **MEDIUM** | Same building blocks as #2, but aggregated — more moving parts, still low risk |
| 8 | Missing-billing-data detection (broader than current readiness blockers) | 3 | 3 | 3 | **MEDIUM-LOW** | Would need to define what "missing" means beyond current checks — some risk of scope creep into judgment territory if not carefully bounded |

**Recommendation**: build #1 and #2 first if/when AI billing work is
greenlit — both are low-effort, low-risk, and high-impact, and reuse the
same safe read-only narrative pattern already validated by the recert
reasoning framework (`build_recertification_evidence_summary`). Do **not**
begin any of this work now — per instruction, this matrix is for future
prioritization only.


---

# SECTION 9 — BILLING READINESS MAP

A single map of exactly what feeds the two central readiness computations
(`check_patient_billing_readiness` / `build_tenant_billing_readiness_report`
in `billing_readiness_service.py`), so it's clear what's actually checked
today versus what a "billing readiness" claim might imply but doesn't yet
cover.

```
                        ┌─────────────────────────────┐
                        │   PATIENT BILLING READINESS  │
                        │  (billing_readiness_service)  │
                        └───────────────┬───────────────┘
                                        │ confirmed blockers checked:
        ┌───────────────┬──────────────┼──────────────┬────────────────┐
        ▼               ▼              ▼              ▼                ▼
  Signed CTI /     F2F encounter   Active/approved   NOE on file   Resolvable
  Certification    (when BP3+       Plan of Care     (per batch-   payer sequence
  on file          required)        (POC)            generate      (MSP/primary/
                                                       docstring)    secondary)

        │ NOT checked / not confirmed as part of readiness this pass:
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ • Documentation completeness beyond CTI/POC (e.g. visit notes)  │
  │ • Discharge-pending status effect on readiness                 │
  │ • Revenue-code/rate-schedule availability for the LOC period    │
  │   (readiness can say "ready" while pricing still $0.00-falls   │
  │   back — these are two independent checks today)                │
  │ • Prior claim's transmission/payment status (no dependency on   │
  │   whether previous period was actually paid)                    │
  └─────────────────────────────────────────────────────────────────┘

  READY  ──▶  generate_patient_billing / batch_generate_patient_billing
                (skips any patient failing the checks above)
              │
              ▼
       export_patient_claim (payload)
              │
              ▼
       export_patient_claim_edi (837I file + Claim.status = SENT)
              │
              ▼
       ??? ── no confirmed transmission channel ─── ???
              │
              ▼
       payments / remittance_advices  (read-only from app's view;
                                        writer not confirmed this pass)
              │
              ▼
       credit_balance_service (net balance, overpayment detection)
```

**Reading this map**: "billing readiness" today is a real, enforced
pre-check on four specific things (cert/CTI, F2F, POC, NOE, payer
sequence) — that part is solid and demo-safe. But "ready" does **not**
currently mean "the price will be correct" (rate schedule is a
placeholder) or "this will actually reach the payer" (no confirmed
transmission channel) — those are the two claims to avoid making in the
demo without an explicit caveat.

---

# PHASE 6 — BILLING STABILIZATION AND DEMO HARDENING

Date: 2026-09-08. Triggered by a directive stating the audit had reached
the point where new information was correcting prior conclusions, and
requiring dedicated standalone documents rather than further growth of
this one file. This section is a short index + the required final
summary; the substantive content lives in the five new/updated
documents below, each independently reviewable:

- `docs/planning/billing_action_map.md` — every frontend control that
  changes billing state, traced button → handler → endpoint → DB write.
  Finding: only one such control exists ("Export to Excel"), and its
  label has nothing to do with its actual behavior.
- `docs/planning/claim_status_architecture.md` (updated) — now includes
  readers of `Claim.status`, the authoritative 5-value status enum, and
  a per-writer audit-trail table showing only 1 of 3 writers emits an
  audit event.
- `docs/planning/payment_posting_architecture.md` — full 835 pipeline
  trace (upload → parse → remittance → payment → matching → claim
  status → credit balance → reporting). Finding: backend is correct
  end-to-end; there is no upload UI, no credit-balance auto-linkage, and
  the one UI surface claiming to show this data is fabricated.
- `docs/planning/billing_user_capability_matrix.md` — every billing
  capability classified against the new 8-value taxonomy (PRODUCTION
  READY / BACKEND ONLY / FRONTEND ONLY / PARTIALLY INTEGRATED / DEMO
  ONLY / PLACEHOLDER / BROKEN / UNKNOWN), replacing the old 3-value scale.
- `docs/planning/biller_persona_matrix.md` — 7 real biller questions,
  answered by tracing to an actual screen/API, not assumed. 4 of 7 have
  a real live answer, 1 of 7 has an answer that can be silently wrong,
  2 of 7 have no answer at all.
- `docs/planning/revenue_leakage_review.md` — full pipeline trace with
  severity-ranked leakage points. No evidence of money silently
  disappearing was found; the real risk profile is operational/
  visibility-based (can't upload 835s, one widget is fake, one button
  can corrupt status with no audit trail).

## Updated Demo Readiness Matrix (replaces Section 12's scale)

| Item | Classification |
|---|---|
| Benefit Period tracking/display | **CAN DEMONSTRATE** |
| Certification/Recertification lifecycle + F2F enforcement | **CAN DEMONSTRATE** |
| NOE tracking screen | **CAN DEMONSTRATE** |
| POC/Certification expiration tracking | **CAN DEMONSTRATE** |
| Credit Balance case lifecycle | **CAN DEMONSTRATE** |
| Facility Payment expectation lifecycle | **CAN DEMONSTRATE** |
| Facility Collection Alert "resolve" | **CAN DEMONSTRATE** |
| Billing readiness pre-check (cert/F2F/POC/NOE/payer sequence) | **CAN DEMONSTRATE**, with the caveat that "ready" ≠ "priced correctly" ≠ "will transmit" |
| Claim status list/filter view | **EXISTS BUT DO NOT DEMO WITH "Export to Excel"** — the list itself is fine to show; do not click that button against PAID/DENIED rows |
| Enforced claim-status endpoint | **EXISTS BUT DO NOT DEMO** — real and correct, but has no UI, so there is nothing to click |
| 835 upload/posting/matching | **EXISTS BUT DO NOT DEMO** — real and correct backend, but no UI exists to demonstrate it live |
| 835 Remittance dashboard widget | **DEMO WILL MISLEAD** — remove or replace with an explicit empty state before Thursday |
| Claim Transmission (to payer/clearinghouse) | **DO NOT CLAIM** — no model, no channel, no evidence exists anywhere |
| Claim correction/reopen workflow | **DO NOT CLAIM** — confirmed not to exist; PAID is intended terminal and the only path that reverses it is a bug |
| Failed-transmission reporting | **DO NOT CLAIM** — no such concept exists in the data model |
| Unmatched-remittance reporting | **DO NOT CLAIM** — data exists (`match_status="UNMATCHED"`), no screen surfaces it |

## AI Billing Roadmap (design only — nothing here is built)

1. **Billing Readiness AI** — outputs Ready / Blocked / At Risk with
   evidence, built as an explanation layer over the already-real
   `check_patient_billing_readiness` blockers, not a new decision engine.
2. **Certification Monitor** — proactive surfacing of the already-real
   14-day expiration window data (`PocCertificationPage`) before a biller
   has to go looking for it.
3. **Revenue Leakage Detector** — flags the operational gaps found in
   `revenue_leakage_review.md` (unmatched payments, claims stuck in
   READY, missing transmission confirmation) for human review.
4. **Claim Risk Monitor** — flags claims exported without a subsequent
   payment/denial after a configurable window, using existing
   `exported_at`/`Payment` data.
5. **Biller Daily Work Queue** — aggregates the answers already proven
   real in `biller_persona_matrix.md` into one prioritized list.

**Explicitly out of scope, per the directive — AI must explain, not
decide**: AI coding, AI claims creation, AI claim submission, AI denial
appeals, AI reimbursement prediction, AI billing decisions of any kind.

## Most Important Question — direct answer

**"If a hospice administrator asks: show me every way a claim status can
change — can SNS answer that question completely?"**

**NO.** Full reasoning in `claim_status_architecture.md` §9–10: two of
the three writers do not emit an audit event, and one of those two does
not even enforce which transitions are legal. The writer inventory
itself is complete (this document set answers "which code paths exist"
fully); what is missing is a uniform audit trail across all three.

## Final Summary (A–G)

**A. What is genuinely production-ready** (backend + frontend + proven
behavior): Benefit Period tracking, Certification/Recertification
lifecycle with F2F enforcement, NOE tracking screen, POC/Certification
expiration tracking, Credit Balance case lifecycle, Facility Payment
expectation lifecycle, Facility Collection Alert "resolve," the
billing-readiness pre-check, and the rate-gap EDI safeguard.

**B. What exists only in backend**: the enforced claim-status endpoint,
835 upload/parse/posting/matching, CMS-838 export, most Facility
Collection Alert actions (acknowledge/snooze/dismiss/reassign/
start-progress), alert-thresholds management, NOE 837I/PDF generation,
NOE ack-status update.

**C. What exists only in frontend (looks real, isn't backed)**: the 835
Remittance dashboard widget — the only capability found this session
where the frontend is more "complete-looking" than the backend actually
supports.

**D. What is misleading**: the "Export to Excel" button (label unrelated
to its real, dangerous behavior); the 835 Remittance widget (fabricated
numbers shown as if live); a claim's displayed status can be wrong if
the Export-to-Excel bug has already fired against it.

**E. What should be removed before Thursday**: the fabricated content in
`render835Remittance()` — replace with an explicit "not yet available"
empty state.

**F. What should be fixed before Thursday**: nothing is required to be
*fixed* (as opposed to *hidden/labeled honestly*) to safely demo — the
minimum bar is (1) removing the fake widget content and (2) not clicking
"Export to Excel" against PAID/DENIED claims during the demo. Fixing the
underlying bug itself is recommended but is engineering work, not a
same-day demo-prep task.

**G. What becomes Phase 1 billing development after Thursday** (ranked):
1. Fix `export_patient_claim_edi` to enforce `ALLOWED_TRANSITIONS` (or
   an equivalent guard) before writing `claim.status`.
2. Add `append_audit_event` calls to `export_patient_claim_edi` and
   `post_payments_from_835` so all three writers share one audit trail.
3. Build a real 835 upload screen + a real remittance list screen against
   the already-correct backend (no backend changes needed beyond #2).
4. Surface unmatched-remittance and stuck-in-READY claims to billers
   (`biller_persona_matrix.md`, `revenue_leakage_review.md`).
5. Wire the enforced claim-status endpoint to a real UI so the *safe*
   path becomes the *used* path.
6. Design (not build) a real `ClaimTransmission` model/channel and a
   documented claim-correction workflow, since both are currently
   entirely absent rather than merely unwired.

No billing feature development and no billing AI development has begun.
All of the above are recommendations awaiting explicit go-ahead.

---

# PHASE 7 — ELIGIBILITY-FIRST REFRAMING

Date: 2026-09-08. Triggered by a directive stating hospice billing must
be evaluated eligibility-first (Referral → Admission → Election →
Certification → Benefit Period → Plan of Care → Recertification → Level
of Care → Claim → NOE → Submission → Remittance → Payment), not
claims-first, because early-stage failures should mean claims never
exist at all. Full detail lives in two new standalone documents:

- `docs/planning/hospice_billing_architecture_review.md` — the
  eligibility-first Lifecycle Map plus dedicated Eligibility,
  Certification, Benefit Period, NOE, Claim (in-context), and Level of
  Care architecture reviews, plus a reframed Top 10 Billing Risks list.
- `docs/planning/biller_question_matrix.md` — the specific eligibility-
  first biller question set (why billable/not billable, recert due,
  active benefit period, NOE submitted, transmitted, paid, unpaid,
  partially paid, no remittance).

**Headline correction this pass**: there is no separate `Election`
model — `election_date` is a single column on `BenefitPeriod`. This
resolves the previously-open "Election SSOT" question (the SSOT is
`BenefitPeriod`, by construction) but also demotes "Election" from a
peer inventory line-item to a fact about Benefit Period, and surfaces a
new gap: election has no dedicated screen or audit trail independent of
the benefit-period row.

**New highest-ranked risk surfaced this pass**: no confirmed
benefit-period rollover/advancement logic was found — only *resolving
the current* period (`get_active_benefit_period`), not *advancing to the
next* one. This now ranks above the previously-#1 claim-transmission gap
in the reframed Top 10, because it sits further upstream: if the next
benefit period isn't reliably created, every downstream step for that
period (recert, claim, NOE) has nothing to attach to.

**AI roadmap addition** (still design-only, nothing built): insert
**Benefit Period Monitor** as Priority 3 (before Revenue Leakage
Monitor/Claim Risk Monitor), answering "who is entering the next benefit
period," "who is overdue," "who has inconsistent dates" — directly
targeting the new #1 risk above.

**Direct answer to the two eligibility questions the directive asked
for**: "Can SNS answer why this patient is eligible for hospice today?"
— **partially** (billing-readiness eligibility: yes; underlying clinical
six-month-prognosis support: out of scope this pass, RNICA is frozen).
"Can SNS answer why this patient is eligible for billing today?" —
**YES**, unambiguously, via `check_patient_billing_readiness` — this
remains the single strongest, most production-ready capability found
across the entire billing review.

No billing feature development and no billing AI development has begun
as a result of this reframing either — it is a re-prioritization of
findings, not new implementation.

---

# PHASE 8 — BENEFIT PERIOD ENGINE VERIFICATION + PRIORITY SPECS

Date: 2026-09-08. Five new design/verification documents produced per
directive, spanning Priorities 0–5 of the new development order.

## Correction (stated plainly)

The Phase 7 document (`hospice_billing_architecture_review.md`)
concluded "no benefit-period rollover/advancement logic found" and
ranked this as the #1 risk. **That conclusion was a false negative**,
caused by grepping only `benefit_period_resolver.py` and missing the
separate `benefit_period_service.py`. A real, tested, production-grade
`rollover_benefit_period` function exists — confirmed by re-running its
existing guardrail test suite (4/4 passing against the real isolated
test DB). Full correction and re-analysis:
`docs/planning/benefit_period_engine_review.md`.

**Revised understanding**: the benefit-period *engine* is not the gap —
it is one of the most defensively-written pieces of code found in this
entire review (row locking, idempotency, chronology validation, correct
CMS 90/90/60-day period lengths, atomic close-old/create-new). **The gap
is that nothing calls it** — no frontend control, no scheduled job.
This moves the risk from "missing logic" to "missing exposure," the same
category as several other findings already documented (835 upload, the
enforced claim-status endpoint).

**Also confirmed**: nothing today prevents a benefit period from being
created without a finalized certification — the rollover engine and its
endpoint have no such precondition. This is a real, newly-confirmed gap,
distinct from the exposure gap above.

## Direct answers to the three required questions

1. **"What benefit period is this patient currently in?" — YES.**
   Source: `get_active_benefit_period` (`benefit_period_resolver.py`).
2. **"When is recertification due?" — YES.** Source:
   `BenefitPeriod.end_date`, surfaced in `PocCertificationPage.tsx`.
3. **"What benefit period comes next?" — the engine can compute and
   create it correctly (confirmed by test), but no user or process can
   currently ask for or trigger it.** Practically: still effectively NO
   for a hospice administrator using the running system today, though
   for a different reason than previously stated (exposure, not logic).

## The four remaining specs (design only, nothing implemented)

- `docs/planning/certification_monitor_spec.md` — Priority 2. What
  exists (14-day window, finalized-cert gate) vs. what's missing
  (configurable windows, missing-signature/physician/medical-director
  states, an explained risk composite, push alerts).
- `docs/planning/billing_readiness_spec.md` — Priority 3, the intended
  first AI feature ("why can/can't I bill this patient," never "generate
  a claim"). Confirms the underlying engine (`check_patient_billing_
  readiness`) is already largely real and already explains its reasons;
  specifies the missing AT RISK tier and the still-unconfirmed
  auditability of past readiness computations.
- `docs/planning/claim_state_machine.md` — Priority 4. Formalizes the
  already-documented state/writer/audit table, reaffirms PAID is
  intended terminal with evidence, and specifies (without building) the
  three governance additions needed: single enforcement point, universal
  audit trail, and a real administrative-correction workflow.
- `docs/planning/revenue_leakage_detector_spec.md` — Priority 5. Restates
  `revenue_leakage_review.md` in the requested stall/money-loss/
  silent-failure/AI-alertability format, and re-ranks the benefit-period
  rollover-exposure gap as the new #1 risk given this pass's correction.

## AI Roadmap (updated per directive, design-only, nothing built)

1. Benefit Period Monitor (new #1 — targets the rollover-exposure gap)
2. Certification Monitor
3. Billing Readiness Engine (intended first AI feature; "why can/can't I
   bill this patient," not "generate a claim")
4. Revenue Leakage Monitor
5. Claim Risk Monitor
6. Biller Command Center

**Still explicitly not to be built**: AI Claim Creation, AI Claim
Submission, AI Coding, AI Denial Appeals, AI Payment Prediction, AI
Billing Decisions. Every AI recommendation, when eventually built, must
show Reason, Evidence, Source Data, Dependency, and Missing Requirement —
no black-box decisions, per explicit design principle.

No billing feature development and no billing AI development has begun.
The benefit-period rollover engine itself was found already built and
tested from a prior, unrelated development effort — it was not built as
part of this review, only discovered and verified.

---

# PHASE 9 — CERTIFICATION-GATED ELIGIBILITY REVIEW

Date: 2026-09-08. Triggered by a directive course-correction: the
benefit-period *engine* is confirmed real and tested, but the primary
risk is now framed as "can SNS create the next benefit period without a
valid certification state," not "can SNS create the next benefit period
at all." Full detail: `docs/planning/certification_gated_eligibility_review.md`.

## A. Eligibility Integrity Assessment

The eligibility chain (Election → Certification → Benefit Period →
Recertification → Benefit Period) is **not integrity-protected at the
point of advancement**. Every transition upstream of the final billing-
readiness check is unenforced: `rollover_benefit_period` performs zero
certification/recertification validation of any kind. The only
protections present (row locking, idempotency, chronology validation)
are technical/structural, not business-rule protections. **A patient's
eligibility can currently advance (i.e., a new benefit period can be
created) with no certification, an expired certification, or a
`benefit_type="RECERT"` with no actual recertification having occurred.**

## B. Certification-Gating Assessment

**Direct answer: SNS can currently create a billable benefit period for
a patient who lacks a finalized certification. YES.** Confirmed by
direct read of `rollover_benefit_period` and its endpoint
(`POST /benefits/`) — neither contains a certification check of any
kind. This applies equally to UI-driven calls (RN/Administrator roles)
and direct API calls (same code path, same lack of gating).

## C. Benefit Period Protection Review

Real protections confirmed: row-level locking against concurrent
double-rollover, idempotency against duplicate calls, chronology
validation against backward-dated periods. **Not present**: any
certification-state check, any recertification-occurred check, any
consistency check between `benefit_type` and an actual clinical
recertification event. The engine is safe against *technical* misuse
(races, duplicates, bad dates) and completely open to *business-rule*
misuse (creating a period for an ineligible patient).

## D. Audit Trail Review

**Zero audit events exist for any benefit-period lifecycle action**
(create, roll, close). `BenefitPeriod.created_by` is a real column on
the model that is **never populated** by the one writer that exists.
This is the same architectural pattern already documented for two of
the three `Claim.status` writers — an organization-wide gap, not a
billing-specific one.

## E. Final Recommended Development Order

Per the directive's strict rule (no new billing features until
eligibility chain, certification gating, benefit period protections, and
audit trail are verified — now done — the order below reflects that the
answer to "can certification be bypassed" is **YES**, which promotes
eligibility-integrity work above every monitor/AI item):

1. **Eligibility Integrity / Certification Gating** (new #1, supersedes
   Benefit Period Monitor) — add a certification-validity check to
   `rollover_benefit_period` (and its endpoint) before allowing
   `BenefitPeriod` creation/advancement; add the missing audit event
   (`append_audit_event` with actor/previous-state/new-state, matching
   the pattern `update_claim_status` already uses correctly) to every
   benefit-period lifecycle action; populate `created_by`.
2. **Benefit Period Monitor** — now safe to build once #1 lands, since
   monitoring ungated data would otherwise just faithfully report an
   ungated reality.
3. **Certification Monitor**
4. **Billing Readiness Engine** (first AI feature; already largely real,
   per `billing_readiness_spec.md`'s Phase 3 addendum, its core
   safety property — not inferring certification validity from benefit
   period existence — already holds; benefit-period *sequencing*
   validity is a smaller remaining gap to close before build)
5. **Claim Status Governance** (single enforcement point + universal
   audit trail + designed correction workflow, per
   `claim_state_machine.md`)
6. **Revenue Leakage Detection**
7. **Claim Risk Monitor**
8. **Biller Command Center**

## F. Updated Top 10 Billing Risks (supersedes the Phase 7 list)

1. **CRITICAL (new #1)** — Benefit periods can be created/advanced with
   no certification check at all — an eligibility-integrity gap, not
   merely an exposure gap.
2. **CRITICAL** — Zero audit trail for any benefit-period lifecycle
   action; `created_by` exists but is never populated.
3. **CRITICAL** — Claim status can regress (PAID→SENT) via "Export to
   Excel," with no audit trail on that specific writer either.
4. **CRITICAL** — No transmission-confirmation data model exists.
5. **HIGH** — Benefit-period rollover, while correct, has no UI/job
   trigger — even once gated, nothing calls it.
6. **HIGH** — 835 remittances cannot be uploaded through any UI.
7. **MEDIUM** — No benefit-type/recertification-occurred consistency
   check (a `"RECERT"` string can be passed with no real recert event).
8. **MEDIUM** — Unmatched payments retained but not surfaced to billers.
9. **MEDIUM** — 835 Remittance dashboard widget shows fabricated data.
10. **LOW** — Certification/recert alerts are passive (visual only), not
    push-based.

No billing feature development and no billing AI development has begun.
This phase re-prioritizes findings only; the eligibility-gating fix
recommended in E.1 has not been implemented and awaits explicit
go-ahead.

## PHASE 10 — Eligibility Integrity Review (index)

Full detail: `eligibility_integrity_review.md`, `certification_gated_eligibility_model.md`. Addenda
appended to `benefit_period_engine_review.md` (Phase 12/13), `certification_monitor_spec.md`
(Phase 14), `billing_readiness_spec.md` (Phase 15).

### A. Eligibility Integrity Assessment
A patient can currently enter a new benefit period with no certification of any kind on file (missing,
draft, expired, or a claimed recert with no actual recertification event). The gap exists at exactly
one function (`rollover_benefit_period`, `app/services/benefit_period_service.py`) and its one caller
endpoint (`POST /benefits/`). No other code path creates or advances a benefit period.

### B. Certification-Gating Assessment
`Certification` itself has a real, correct lifecycle (`DRAFT → PENDING_SIGNATURE → FINALIZED →
SUPERSEDED`) with a genuine, already-working append-only audit trail (`CertificationStatusEvent`).
The gap is not that certifications are poorly modeled — it is that `BenefitPeriod` creation never
reads that model at all. Fixing this is a scoped, well-understood change: add one query
(`_has_finalized_certification`-equivalent, a function that already exists and works correctly for
billing-readiness) as a precondition inside `rollover_benefit_period`, before the existing
locking/idempotency/chronology logic runs.

### C. Benefit Period Protection Assessment
Technical protections (locking, idempotency, atomic commit/rollback) are correct and proven by
execution (4/4 guardrail tests). Newly confirmed this phase: the idempotency check is exact-tuple-only
and does not prevent two *different* `start_date` values from producing two plausible "next" periods
for the same patient — a distinct data-integrity gap, separate from certification gating. No
update/correct/delete operation exists for benefit periods at all (not even ungated) — those lifecycle
actions are simply not implemented as code paths.

### D. Audit Trail Assessment
Confirmed narrower than earlier stated: the audit-trail gap is specific to `BenefitPeriod` (no
`created_by` population, no status-event table), not organization-wide. `Certification` already has a
working, real audit trail using the exact pattern (`created_by` FK + append-only status-event table)
that would fix the `BenefitPeriod` gap if replicated. An auditor cannot today reconstruct benefit-period
transition history for a patient; they can for certification transition history.

### E. Compliance Assessment
CMS hospice election-period rules (42 CFR §418.21/§418.22) require a valid, physician-signed
certification/recertification before the corresponding benefit period is billable. SNS's
billing-readiness layer already correctly enforces this at claim time
(`check_patient_billing_readiness` → `_has_finalized_certification`, real and working). The compliance
exposure is that a `BenefitPeriod` can exist and be marked `is_current=True` in the system of record
before that check ever runs — an auditor or surveyor reviewing raw benefit-period data (not filtered
through the billing-readiness lens) could see a "current" period with no supporting certification.

### F. Final Priority Order
1. Certification-gate `rollover_benefit_period` (add the missing precondition check).
2. Add `BenefitPeriod` audit trail (`created_by` population + status-event table, mirroring
   `Certification`'s existing pattern).
3. Tighten idempotency to prevent duplicate "next" periods with differing `start_date`.
4. Benefit Period Monitor (only meaningful once 1–3 are in place).
5. Certification Monitor (Recert Overdue derived query, per Phase 14 addendum).
6. Billing Readiness Engine enhancements (already largely built; extend per Phase 15 addendum).
7. Claim Status Governance fix (pre-existing, documented in Phase 5/6).
8. Revenue Leakage Detection.
9. NOE Dashboard / Remittance UI / LOC Validation / Biller Command Center.
10. Claim Risk AI (last, per repeated explicit instruction).

### G. Recommended First Engineering Task
Add a single precondition check inside `rollover_benefit_period`, before its existing
locking/idempotency logic: query for a `Certification` row matching
`(tenant_id, patient_id, cert_type, status='FINALIZED', signed_at IS NOT NULL)` appropriate to the
requested `benefit_type` (`INITIAL` or `RECERT`), and raise if none exists. This reuses an
already-proven query shape (`_has_finalized_certification` in `billing_readiness_service.py`) rather
than inventing new logic, and directly closes the Q1/Q2 gap in `eligibility_integrity_review.md`.

### Direct answer restated
**Can an ineligible patient become billable? NO — not today.** A benefit period can be created without
certification, but `check_patient_billing_readiness` independently re-verifies certification at claim
time and will block billing if it's missing. The integrity failure is that the *system of record*
(the `BenefitPeriod` table itself) can contain uncertified "current" periods, not that an uncertified
claim can currently be submitted successfully. Both facts are true simultaneously and are not in
tension: the front door (benefit-period creation) is open; the back door (claim submission) is locked.

No production code has changed. No billing feature or AI has been built. This phase is verification
and design only, awaiting explicit go-ahead before any implementation begins.

## PHASE 18-26 — Hospice Reimbursement Reference Model & Regulatory Gap Matrix (index)

Full detail: `hospice_reimbursement_reference_model.md` (Phases 18-22, sections A-D of the final
deliverable), `regulatory_gap_matrix.md` (Phase 23). This phase deliberately re-validated prior
conclusions against real-world regulation and code together, per the explicit instruction not to
assume current findings are final.

### F. Revised Billing Development Order

The working hypothesis in the directive is largely confirmed, with one insertion:

1. **(New, time-boxed) Election Statement Addendum — mandatory-furnish version.** SNS's
   `election_addendum_service.py` implements only the pre-10/1/2026 on-request rule. CMS's
   mandatory-for-every-election version takes effect 10/1/2026 — approximately three weeks from this
   review. This is inserted ahead of item 2 purely because of its hard external deadline, not because
   it is architecturally more important than certification gating.
2. Eligibility Integrity / Certification-Gating (unchanged from Phase 9 — confirmed, not weakened, by
   regulatory research: 42 CFR 418.22 independently requires exactly the gate SNS is missing).
3. Certification / Recertification workflow enhancements (Recert Overdue derived signal).
4. Benefit Period audit trail (elevated in urgency by new CDPH Title 22 auditability requirements,
   which apply to the same category of gap).
5. Benefit Period Monitoring.
6. Billing Readiness Engine enhancements (add an affirmative "why Medicare would pay" statement, not
   just absence-of-blocker; see reference model section A).
7. NOE acceptance-date tracking (new follow-up flagged — verify SNS tracks MAC acceptance, not just
   submission, since the 5-day clock legally runs to acceptance).
8. Revenue Leakage Detection / Claim Status Governance (pre-existing, unchanged findings).
9. Remittance Operations / NOE Dashboard / Biller Command Center.
10. Claim Risk AI (last, per repeated explicit instruction).

Explicitly removed from the backlog: any Medicare-Advantage-hospice-specific engineering work — the
VBID hospice carve-in ended 12/31/2024, and MA hospice fully reverted to traditional Medicare rules;
building special-case MA logic today would be solving a problem that no longer exists.

Explicitly flagged as unscoped, not ranked (need a dedicated follow-up review before they can be
placed in this order at all): Revocation, Discharge, Transfer, Plan-of-Care audit trail, IDG task
completion tracking, California Title 22 clinical-note addendum/correction workflow, medical-record
retention/export.

### G. Revised AI Roadmap

Unchanged in ordering logic from Phase 9 (Eligibility Integrity before any monitor/AI), reinforced by
regulatory research: every requirement CMS attaches to certification/benefit-period validity is a
prerequisite condition, not a scoring input — an AI feature that scores billing readiness without a
gated eligibility chain underneath it would be scoring on top of potentially-invalid data, which
regulatory review confirms is a compliance risk, not just an architecture preference. First AI feature
remains: "why can't I bill this patient," now explicitly extended to also answer "why *would* Medicare
pay" (affirmative case), since the regulatory model shows CMS/CDPH auditors expect an affirmative,
itemized satisfaction statement, not merely an absence of objections.

### H. Top 10 Reimbursement Risks (supersedes the Phase 9 list)

1. Certification can be bypassed at benefit-period creation (unchanged, regulation-confirmed).
2. Election Statement Addendum mandatory-furnish rule not implemented ahead of its 10/1/2026 effective
   date (new).
3. Benefit period lifecycle lacks business-rule gating generally (unchanged).
4. Benefit-period audit trail incomplete, now with added CDPH Title 22 weight (unchanged scope, higher
   urgency).
5. NOE acceptance-vs-submission tracking not verified (new follow-up, not yet confirmed as a gap).
6. Claim status regression bug — 2 of 3 writers unenforced/unaudited (unchanged, pre-existing).
7. Remittance/835 dashboard widget renders fabricated data (unchanged, pre-existing).
8. Recert Overdue has no derived signal distinct from generic "expiring" (unchanged from Phase 14).
9. Payer-specific (PPO/commercial) rule variability has no configuration surface (unchanged from Phase
   Ph. reference model section C).
10. California Title 22 clinical-note addendum/correction workflow entirely unscoped by this engagement
    — could contain its own findings once reviewed, currently an unknown rather than a confirmed risk.

No production code has changed. No billing feature or AI has been built. Every finding above is either
a direct code-read confirmation or an explicitly-labeled open question awaiting a dedicated follow-up
review — none are assumed. This phase deliberately re-validated (not assumed) all Phase 9 conclusions
against real-world regulation; all of them held, and one new time-critical gap was found that no prior
phase had surfaced.

## PHASE 27-34 — Reimbursement Defensibility Review (index)

Full detail: `reimbursement_defensibility_review.md` (Phases 27, 29, 31, 32),
`election_addendum_2026_gap_review.md` (Phase 28), `payer_reimbursement_matrix.md` (Phase 30). This
phase reframed the objective from "can SNS bill" to "can SNS defend hospice reimbursement during
audit" and deliberately re-validated every prior conclusion rather than assuming it still held.

### A. CMS Gap Assessment
Two confirmed gaps, correctly distinguished by urgency vs. structural significance:
- **Structural**: Benefit Period creation is not gated by Certification and has no audit trail of its
  own (unchanged conclusion, now reframed precisely — see Phase 27's per-checkpoint table: the
  *records* are strong, the *linkage and audit between* Certification and Benefit Period is the gap).
- **Time-critical**: Election Statement Addendum mandatory-furnish rule (10/1/2026) is not implemented;
  SNS's real, non-fabricated tracking system only models the on-request version.

### B. CDPH Gap Assessment
**Revised from the prior phase.** Clinical-note addendum/correction workflow — previously flagged
"unscoped/unknown" — is now confirmed **compliant**: `app/models/amendment.py` (`Amendment`) and
`rnica_amendment.py` implement exactly the structured, signed, timestamped, reason-required addendum
pattern CDPH's new Title 22 hospice sections require. Physician-notification-tracking and the ~48-hour
correction window remain genuinely unconfirmed (not assumed either way). Admission documentation has a
real model with its own status-history audit table, following the same pattern as `CertificationStatusEvent`
— likely strong, not deeply verified this pass.

### C. Medicare / HMO / PPO Comparison
Medicare Advantage hospice billing is operationally identical to Medicare FFS today (VBID carve-in
ended 12/31/2024) — no MA-specific engineering work should be scoped. The most real, actionable
difference across payer types is **Authorization**, which Medicare doesn't require at all but
commercial PPO/managed-care commonly do — SNS has the payer-agnostic infrastructure to build this on,
but no payer-specific rule configuration exists yet. NOE is confirmed Medicare-only; no commercial-payer
NOE-equivalent should be modeled.

### D. Election Addendum Review
Confirmed **PARTIAL** non-compliance risk on 10/1/2026: the existing on-request compliance-clock math
is CMS-correct and remains valid; the gap is that no record is created at all when no request occurs,
which after 10/1/2026 is the normal case (furnishing becomes automatic/mandatory, not request-triggered).
Full transition strategy in `election_addendum_2026_gap_review.md`.

### E. Eligibility Defensibility Scorecard
Election 4, Certification 5, Benefit Period 2, Recertification 3, NOE 3, Claim 2, Payment 2
(provisional), Audit Trail (overall) 3, Documentation (overall) 4. The scorecard confirms the same
narrow conclusion every phase of this engagement has converged on: individual clinical/regulatory
records are strong; Benefit Period's creation-gating and audit trail remain the one consistently weak
link, with Claim-status and remittance-fabrication as unchanged, pre-existing secondary risks.

### F. Revised Top 10 Risks
1. Election Statement Addendum mandatory-furnish gap (10/1/2026 deadline — time-critical, inserted
   ahead of #2 solely due to its fixed external date).
2. Benefit Period lacks certification gating at creation (structural, unchanged core finding).
3. Benefit Period has no audit trail (`created_by` unpopulated, no status-event table).
4. Certification-to-Benefit-Period-to-Billing-Readiness traceability chain is not reconstructable as a
   single auditable narrative, even though each individual record is strong (new, precise framing from
   Phase 29).
5. Recertification lacks a distinct "Recert Overdue" derived signal.
6. Claim status regression — 2 of 3 writers unenforced/unaudited (unchanged, pre-existing).
7. Remittance/835 dashboard widget renders fabricated data (unchanged, pre-existing).
8. NOE acceptance-vs-submission tracking unconfirmed (flagged, not yet proven a gap).
9. No payer-specific authorization-rule configuration for commercial/managed-care payers.
10. CDPH physician-notification-tracking and ~48-hour correction-window enforcement unconfirmed.

### G. Revised Development Priorities
1. Election Addendum automatic-furnish path (deadline-driven).
2. Certification-gate `rollover_benefit_period` (structural root cause).
3. Benefit Period audit trail (`created_by` + status-event table, mirroring `Certification`'s existing,
   proven pattern).
4. Persist billing-readiness check results historically (closes the Phase 29 traceability gap — today
   the function is pure compute/return with no persistence, confirmed by code read).
5. Recert Overdue derived signal.
6. Certification Monitor → Recertification Monitor → Benefit Period Monitor (AI roadmap order affirmed
   unchanged from Phase 9/18-26 — monitors remain sequenced after gating/audit fixes, not before).
7. Billing Readiness Engine enhancement (affirmative "why Medicare would pay," not just absence-of-blocker).
8. Claim Status Governance fix / Revenue Leakage Detection (pre-existing, unchanged).
9. Payer-specific authorization-rule configuration (commercial/managed-care).
10. Biller Command Center / Claim Risk AI (last, per repeated explicit instruction).

No production code has changed. No billing feature or AI has been built. Every finding above is either
a direct code-read confirmation or an explicitly-labeled open question — this phase corrected one prior
"unknown" (CDPH clinical-note addendum workflow) to "confirmed compliant" transparently, and reframed
(without weakening) the core certification-gating finding as a traceability/audit problem rather than a
raw eligibility-bypass problem, per the directive's own reasoning.

## PHASE 35-42 — Reimbursement Compliance Hardening (index)

Full detail: `reimbursement_compliance_hardening.md` (Phases 35, 39, 40),
`election_addendum_transition_plan.md` (Phase 36), `eligibility_traceability_chain.md` (Phase 37),
`benefit_period_audit_design.md` (Phase 38), `compliance_defensibility_scorecard.md` (Phase 41).

### A. Election Addendum Assessment
**PARTIALLY COMPLIANT on 10/1/2026.** Existing on-request compliance-clock math is CMS-correct and
unaffected; the gap is structural — no record is created absent a manual request, and the new rule
makes automatic furnishing the default case, so compliance would depend entirely on staff diligence
with zero system enforcement. Full transition plan (affected APIs/fields/forms/reports) in
`election_addendum_transition_plan.md`. Priority #1, purely due to its fixed external deadline.

### B. Reimbursement Defensibility Assessment
SNS can defend an individual claim's *current* eligibility live (billing-readiness re-derives
certification/F2F/POC/NOE/payer-sequence in real time, confirmed real and non-fabricated). SNS **cannot**
defend a *historical* claim retrospectively, because no readiness verdict is ever persisted — this is
the single most consequential finding of this compliance-focused phase, more precise than any prior
phase's framing: the gap is not that eligibility can be faked, it's that eligibility-at-a-past-moment
cannot be reconstructed after the fact.

### C. Eligibility Traceability Assessment
Referral and Admission both have real creator/reviewer attribution (Admission additionally has a full
`AdmissionStatusHistory` audit trail, confirmed this phase). Certification has the strongest trail in
the system. Benefit Period has none. Billing Readiness has none (by design — it is a pure live
computation, confirmed via code read that no persistence call exists in it). Full per-transition table
in `eligibility_traceability_chain.md`.

### D. BenefitPeriod Audit Assessment
Design-only `BenefitPeriodStatusEvent` table specified, directly modeled on the already-proven
`CertificationStatusEvent`/`AdmissionStatusHistory` pattern. Of the six requested event types, three
(`Updated`, `Corrected`, `Reopened`) have no corresponding code path today — no update/correct/delete
endpoint exists for benefit periods at all — so their audit design is groundwork only, not a closable
gap until those actions themselves are built. The minimum viable, immediately actionable fix needs no
new table at all: populate `BenefitPeriod.created_by` using `current_user`, already available at the
`POST /benefits/` call site.

### E. Recertification Monitoring Assessment
All requested signals are queryable from existing columns; no schema change required except for the
"Recert Overdue" derived query, which does not exist yet but needs no new storage. "Missing Benefit
Period Association" is confirmed **not a real risk** — `Certification.benefit_period_id` is a
non-nullable FK, so this specific failure mode is prevented by the database schema itself and should be
removed from future gap lists, the same way the Medicare Advantage carve-in concern was retired in the
prior phase.

### F. Compliance Scorecard
Election 4, Certification 5, Recertification 3, Benefit Period 2, NOE 3, Claim 2, Remittance 2, Payment
2 (provisional), Audit Trail (overall) 3, Medical Record (overall) 4, Plan of Care 3 (provisional), IDG
3 (provisional). Full evidence in `compliance_defensibility_scorecard.md`.

### G. Updated Priority Order
1. Election Addendum automatic-furnish transition (deadline-driven).
2. Benefit Period audit trail — minimum viable version: `created_by` population (no new table) +
   `BenefitPeriodStatusEvent` for `CREATED`/`ROLLED`/`CLOSED` only (the three real, existing actions).
3. Certification-gate `rollover_benefit_period` (structural root cause, unchanged from every prior phase).
4. Persist Billing Readiness verdicts historically (closes the single most consequential Phase 35/37
   finding: retrospective defensibility).
5. Recertification Monitor (Recert Overdue query + Missing Medical Director/Physician alerts — all
   buildable from existing columns).
6. Certification Monitor.
7. Billing Readiness Engine enhancement (affirmative "why Medicare would pay," not just absence-of-blocker).
8. Claim State Governance fix / Revenue Leakage Detection (pre-existing, unchanged).
9. Payer-specific authorization-rule configuration (commercial/managed-care, from Phase 30).
10. Biller Command Center / Claim Risk AI (last, per repeated explicit instruction).

### H. Recommended First Engineering Task
Two independent, minimal, evidence-grounded changes, either of which could be done first without
waiting on the other: (1) add `created_by=<current_user.id>` to the existing `BenefitPeriod(...)`
constructor call in `rollover_benefit_period`, using `current_user` already available in
`app/api/benefits.py` — zero new plumbing; (2) add one precondition query inside
`rollover_benefit_period` checking for a `FINALIZED`, signed `Certification` matching the requested
`benefit_type`, reusing the exact query shape already proven correct in
`_has_finalized_certification()`. Neither requires new tables, new endpoints, or new AI — both are
surgical insertions into an already-well-understood, already-tested function.

---

## Most Important Question — Direct Answer

**Can SNS currently defend a Medicare hospice payment during an audit using SNS records alone?**

**PARTIAL.**

Evidence: for the clinical/regulatory substance of eligibility — was the patient certified, by whom, in
what role, with what narrative evidence — SNS's records are strong and reconstructable
(`CertificationStatusEvent` audit trail, structured narrative fields). For the *procedural* chain
connecting that certification to an actual billing event — was the benefit period properly gated by
it, who created/rolled it and when, and what did the readiness check show at the time billing
occurred — SNS cannot reconstruct this today, because Benefit Period has no audit trail and Billing
Readiness verdicts are never persisted. An auditor would find the clinical justification well-
documented and the procedural/audit chain connecting it to payment incomplete. This is not a hedge — it
is the precise, evidence-based answer: some parts fully defensible (Certification), one part not yet
defensible at all (Benefit Period/traceability), and no part actively fraudulent or fabricated (aside
from the already-documented, unrelated remittance-widget issue from Phase 5/6).

No production code has changed. No billing feature or AI has been built. This phase corrected and
sharpened prior framing without discarding any earlier finding: every conclusion in Phases 1-34 was
re-checked against the compliance-hardening lens and none were reversed — three were made more precise
(Benefit Period risk reframed as a traceability/audit gap, not a raw bypass risk; Missing Benefit Period
Association retired as a non-issue; retrospective defensibility identified as the single most
consequential open gap, more foundational than any individual missing check).

## PHASE 43-50 — Audit-Scenario Reorganization & Eligibility Integrity Epic (index)

Full detail: `cms_audit_simulation.md` (Phase 43), `cdph_survey_simulation.md` (Phase 44),
`reimbursement_defensibility_chain.md` (Phase 45), `traceability_scorecard.md` (Phase 46). This phase
reorganized every prior finding around audit scenarios (what a CMS reviewer, CDPH surveyor, payer, or
attorney would actually ask for) instead of by module/file/service, per explicit instruction. No new
code investigation was required to reorganize; all underlying evidence traces back to prior phases'
direct code reads.

### A. CMS Audit Simulation
Walking a realistic paid claim through Election→Payment: Certification/Recertification fully pass
(strong, evidenced, physician-attributed, timestamped). Benefit Period requires inference (no
certification-gate confirmation, no creator attribution). NOE/Claim/Payment carry pre-existing,
narrower gaps. **Direct answer: PARTIAL** survivability for a documentation review of a paid claim.

### B. CDPH Survey Simulation
Section-by-section: Admission **PASS**, Certification **PASS**, Clinical Documentation/Addenda **PASS**
(confirmed this pass — the `Amendment` model satisfies CDPH's newest structured-addendum requirement),
Medical Record (overall) **PASS** with retention/export unevaluated, Benefit Period **FAIL** (unchanged
core finding), Plan of Care and IDG **PARTIAL** (real trigger/check exists, completion/version history
unconfirmed), Assessment/Discharge/Transfer **UNKNOWN** (outside this engagement's investigated scope,
honestly labeled rather than assumed).

### C. Reimbursement Defensibility Chain
Clinical Findings → Recertification is fully system-evidenced, no human memory required. The chain
breaks at exactly two links: Benefit Period (no gate, no attribution) and Billing Readiness→Claim→Payment
(no persisted verdict, known pre-existing claim/payment gaps). **Direct answer to the most important
question ("can SNS explain why payment occurred, without relying on human memory?"): PARTIAL** — precise,
not a hedge: the strong half is fully evidenced, the weak half is exactly identified.

### D. Traceability Scorecard
Certification 5, Recertification 4, Medical Record 4, NOE/Election 3, Audit Trail 3, Claim/Plan of Care
2, **Benefit Period 1, Payment 1 (provisional), Chronology 2** (new dimension this phase — measures
whether facts are causally linked into one narrative, not just individually documented). Chronology's
weak score is the most diagnostic number in this engagement: individual facts are well-recorded: the
causal thread connecting them is not.

### E. Updated Top Risks — translated to business/audit language

| Technical finding | Business/audit risk |
|---|---|
| Election addendum on-request-only tracking | Potential CMS compliance exposure beginning 10/1/2026 — every election without a logged request would have no system record that the (now-mandatory) addendum obligation was met. |
| `rollover_benefit_period` has no certification check | Unable to demonstrate, using system records alone, that every active benefit period was authorized by a valid certification at the moment it was created. |
| `BenefitPeriod.created_by` unpopulated, no status-event table | Unable to fully reconstruct benefit-period progression (who, when, why) during a CMS or CDPH review — an examiner would have to accept staff testimony in place of system evidence. |
| Billing-readiness verdict not persisted | Unable to prove, after the fact, why a specific past claim was considered billable at the time it was submitted — only today's live state is queryable, not history. |
| No "Recert Overdue" derived signal | Reduced visibility into recertification compliance risk before it becomes a claim-level problem — a monitoring gap, not a documentation gap. |
| No update/correct endpoint for Benefit Period | If a benefit-period entry error is ever discovered, there is currently no system-supported, auditable way to correct it — any correction today would have to happen outside the system of record. |
| 2 of 3 `Claim.status` writers unenforced/unaudited (pre-existing) | Claim-status history cannot be fully trusted or reconstructed for 2 of 3 possible change paths. |
| 835 remittance dashboard widget fabricated (pre-existing) | Staff-facing remittance figures do not reflect real payer adjudication data, creating a risk of decisions being made on non-real numbers. |

### F. First Engineering Epic — Eligibility Integrity & Traceability

Explicitly **not** Billing Readiness Engine, Claim Risk AI, or Revenue Leakage AI, per instruction.
Scope, in priority order within the epic:
1. Certification gating inside `rollover_benefit_period` (one precondition query, reusing the proven
   `_has_finalized_certification` shape).
2. `BenefitPeriod.created_by` population (uses `current_user` already available at the call site — no
   new plumbing).
3. `BenefitPeriodStatusEvent` audit table for the three real, existing actions (`CREATED`, `ROLLED`,
   `CLOSED`) — design already complete in `benefit_period_audit_design.md`.
4. Eligibility chronology — a query/view layer that presents the full Referral→Payment chain for a
   single patient as one ordered narrative, using data that already exists, closing the "Chronology"
   gap identified in Phase 46 without needing new source data.
5. Billing-readiness persistence — store each computed verdict (blockers, pass/fail, timestamp) rather
   than discarding it after return, closing the single most consequential gap identified across Phases
   35-45.
6. User attribution audit — extend the same `created_by`/event-table pattern to any other unattributed
   write path discovered during this epic's implementation (not newly discovered this phase; a
   consequence of items 2-3 above, not a separate investigation).
7. Audit reconstruction — a read-side report/screen that answers "why is this patient billable" as an
   affirmative, itemized statement (not just absence-of-blocker), directly reusable for CMS/CDPH/payer/
   legal-discovery requests.

This epic is deliberately scoped to close the exact gaps this entire engagement identified, using
patterns already proven elsewhere in the codebase (`CertificationStatusEvent`, `AdmissionStatusHistory`,
`Amendment`) — no new architecture is invented, and no AI is required to deliver it.

### G. Updated AI Roadmap
1. Eligibility Traceability (a genuine capability — presenting the reconstructed chain automatically —
   only meaningful once the epic above closes the underlying data gaps it would need to summarize).
2. Recertification Monitor.
3. Certification Monitor.
4. Billing Readiness Engine (affirmative "why is this patient billable," building directly on epic item
   7 above).
5. Revenue Leakage Detection.
6. Claim Risk Detection.
7. Biller Command Center.

Ordering rationale unchanged and reinforced by this phase's findings: "why was this patient billable"
(audit defense) is sequenced ahead of "why can't I bill this patient" (workflow optimization), because
every audit-scenario simulation in this phase confirmed that reconstructing the past is the weaker,
higher-consequence capability gap — not scoring the present, which SNS can already do live.

No production code has changed. No billing feature or AI has been built. This phase's contribution was
reorganization and epic definition, not new findings that reverse any prior conclusion — every score and
gap traces to evidence already established in Phases 1-42.

## PHASE 51-58 — Hospice Reimbursement Chronology (epic renamed; final index)

Full detail: `reimbursement_chronology_model.md` (Phase 51), `certification_to_payment_chain.md`
(Phase 54), `cms_audit_package.md` (Phase 55), `cdph_survey_package.md` (Phase 56). Per directive, the
epic previously named "Eligibility Integrity & Traceability" (Phase 49) is **renamed to "Hospice
Reimbursement Chronology"** — the scope is unchanged, the name now accurately reflects the actual
finding: not that eligibility/certification/claims/payments are individually wrong, but that the
chronology connecting them cannot always be reconstructed.

### Chronology Model (Phase 51) — the one structural break point
Every event from Clinical Findings through Recertification is fully reconstructable (WHO/WHEN/WHY/
EVIDENCE all answerable). Every event at and after Benefit Period has at least one dimension missing.
This is one structural break point, not eight independent gaps — because Benefit Period itself has no
actor/reason/linkage record, nothing built on top of it (Billing Readiness, Claim, Payment) can cite it
as a justified, attributed cause either, even where those later stages have their own partial records.

### Phase 52 — Billing Readiness Persistence
**Confirmed, unchanged**: `check_patient_billing_readiness()` is a pure live computation; nothing is
persisted. **Can SNS answer "why was patient billable on DATE X"? NO.** Only "why is patient billable
right now" is answerable. This is the single largest gap in the entire engagement, reconfirmed at every
phase since Phase 29 and not weakened by any subsequent review.

### Phase 53 — Benefit Period Audit Epic (design, extends Phase 38)
Adds one field not previously specified: `related_certification_id` on the proposed
`BenefitPeriodStatusEvent` table — capturing which certification (if any) was checked and satisfied the
gate at the moment of creation/rollover, turning today's reverse-only FK (`certifications.benefit_period_id`)
into a forward, causal record. This directly closes the Phase 54 "missing link" finding below.

### Phase 54 — Certification-to-Payment Chain
**Cannot be traced without inference.** The one confirmed missing link: no record exists that a
certification check occurred *at the moment* a benefit period was created — `Certification.benefit_period_id`
enables a reverse lookup (which certifications reference this period) but not a forward causal record
(this period was created *because of* certification X). Claim→Payment carries the same pre-existing,
already-documented gaps (2 of 3 status writers unaudited; fabricated remittance widget).

### Phase 55 — CMS Audit Package
6 of 13 requested items **Automatically Available**, 4 **Partially Available**, 3 **Unavailable**
(Benefit Period authorization trail, historical billing-readiness verdict, remittance/payment). The
clinical/regulatory core is strong; the audit-trail/historical-reconstruction layer is where the
package would be incomplete today.

### Phase 56 — CDPH Survey Package
Every section this engagement directly investigated (Admission, Certification, Clinical Notes,
Addenda, Medical Record core) is demonstrable, including the newest CDPH requirement (structured
addenda) which is a confirmed strength. Assessment, Transfer, and Discharge remain honestly labeled
unknown — never investigated, not assumed either way.

### Phase 57 — Reimbursement Defensibility Score (replaces simple component scoring)

| Category | Score | Basis |
|---|---|---|
| Eligibility (composite: election+certification+benefit period) | 3 (Adequate) | Strong individually for election/certification; the composite is pulled down by Benefit Period's break point |
| Certification | 5 (Fully Defensible) | Unchanged strongest area in the system |
| Recertification | 4 (Strong) | Same model as Certification; lacks only a dedicated overdue signal |
| Benefit Period | 1 (High Risk) | No attribution, no audit trail, no forward causal link to its authorizing certification |
| Chronology (the reframed core finding) | 2 (Weak) | Individual facts well-recorded; the causal thread connecting them across the whole chain is not, confirmed across Phases 45-51 |
| Claim | 2 (Weak) | Pre-existing, unchanged |
| Payment | 1 (High Risk) | Fabricated dashboard widget confirmed; no independently-confirmed real ledger |
| Medical Record | 4 (Strong) | Referral/Admission/Certification/clinical-note amendments all real and structured |
| Audit Trail (cross-cutting) | 3 (Adequate, uneven) | Excellent in 3 areas, absent in the one most consequential area (Benefit Period) |

### Phase 58 — First Engineering Epic: Hospice Reimbursement Chronology
Explicitly **not** Billing Readiness Engine, Revenue Leakage, Claim Risk AI, or Biller Command Center.
Scope (unchanged from Phase 49's epic, renamed and refined with the Phase 53 addition):
1. Certification gating inside `rollover_benefit_period`.
2. `BenefitPeriod.created_by` attribution.
3. `BenefitPeriodStatusEvent` audit table, including `related_certification_id` (Phase 53 addition) —
   this single field is what converts the Phase 54 "missing link" into a closed one.
4. Billing-readiness persistence (historical verdict storage) — closes Phase 52's confirmed largest gap.
5. Chronology reporting — a single reconstructed-narrative view spanning Referral→Payment for one
   patient, consuming data made available by items 1-4 above.
6. Audit reconstruction — an affirmative "why is this patient billable" statement, reusable for CMS/
   CDPH/payer/legal-discovery requests, per the Phase 58 success criteria below.

### Success criteria (verbatim from directive, restated as the epic's definition of done)
An auditor can ask "why was this patient billable on DATE X," "who made the patient billable," "what
evidence justified reimbursement," and "show chronology" — and SNS answers automatically, from
persisted records, not live re-computation or staff recollection. Only once these four questions are
answerable should Certification Monitor, Billing Readiness Engine, Revenue Leakage Detection, and Claim
Risk AI proceed.

### Findings re-categorized (per directive: stop describing as technical issues)

| Category | Finding |
|---|---|
| **Chronology Gap** | Cannot answer "why was this patient billable on a past date" — only today's live state is computable. |
| **Chronology Gap** | Cannot answer "why was this benefit period created" as a causal record — only "does a certification happen to also exist" as a reverse lookup. |
| **Attribution Gap** | Benefit Period creation/rollover has no recorded actor (`created_by` unpopulated). |
| **Attribution Gap** | Election signing event has a timestamp but no confirmed user-attribution field. |
| **Audit Gap** | No event stream exists for any Benefit Period lifecycle action (created, rolled, closed). |
| **Audit Gap** | 2 of 3 `Claim.status` writers are unenforced and unaudited (pre-existing, unchanged). |
| **Audit Gap** | Remittance dashboard data is fabricated, not sourced from real payer adjudication (pre-existing, unchanged). |
| **Traceability Gap** | No forward causal link from a satisfied certification to the benefit period it should have authorized. |
| **Traceability Gap** | NOE tracks submission but not confirmed to track MAC acceptance, the point the legal timeliness clock actually runs to. |
| **Traceability Gap** | Recertification has no dedicated "overdue" signal distinct from "expiring soon." |

No production code has changed. No billing feature or AI has been built. This phase's contribution is a
rename and refinement of the epic already defined in Phase 49, one new design field (`related_certification_id`),
and a re-categorization of every finding into business-facing gap language — no prior technical
conclusion was reversed or newly discovered; every item above traces to evidence already established in
Phases 1-50.

## IMPLEMENTATION PLANNING — Eligibility Traceability Epic

Full detail: `eligibility_traceability_epic.md`. Per directive, review/research/documentation phases are
now complete; this is the engineering-ready specification for the "Hospice Reimbursement Chronology"
epic (Phase 49/58), covering exactly the 5 requested scope items — BenefitPeriod audit trail, eligibility
chronology, readiness persistence, user attribution, eligibility timeline reporting — and none of the
still-deferred AI features (Billing Readiness Engine, Revenue Leakage, Claim Risk AI, Biller Command
Center, Certification/Recertification Monitors). It specifies two new tables
(`benefit_period_status_events`, `billing_readiness_verdicts`), one new read-only chronology service, one
new reporting endpoint, and a strict build sequence (audit trail + readiness persistence first, in
parallel; chronology composition second; timeline reporting last). It resolves nothing new — every
scope item traces to a gap already confirmed in Phases 1-58 — and it changes no code itself. No
production code has changed. No billing feature or AI has been built.

