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

