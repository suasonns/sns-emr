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
