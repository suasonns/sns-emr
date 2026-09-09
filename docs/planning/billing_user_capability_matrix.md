# Billing User Capability Matrix

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Phase 7 required deliverable. Every capability below uses the Phase 6
classification taxonomy (not the old Implemented/Partial/Missing scale,
per the directive's explicit instruction that the old scale is no longer
precise enough).

Classification legend: **PRODUCTION READY**, **BACKEND ONLY**,
**FRONTEND ONLY**, **PARTIALLY INTEGRATED**, **DEMO ONLY**,
**PLACEHOLDER**, **BROKEN**, **UNKNOWN**.

| Capability | Backend | Frontend | Permissions | Data | Operational | Demo Safe | Production Safe | Classification |
|---|---|---|---|---|---|---|---|---|
| Enforced claim status update (`POST /billing/claim-status`) | YES | NO | Tenant-scoped, remittance fields gated by `tenant_has_automated_billing` | Real | NO (no UI can invoke it) | NO (nothing to show) | YES (behaviorally proven, Phase 4) | **BACKEND ONLY** |
| "Export to Excel" (`export_patient_claim_edi`) | YES | YES | None (no status-transition guard) | Real | YES (but unsafe) | **NO** — can corrupt a PAID/DENIED claim on stage data | **NO** — confirmed defect | **BROKEN** |
| 835 file upload | YES | NO | `require_automated_billing` gate exists backend-side | Real | NO | NO | YES (backend-only, correct) | **BACKEND ONLY** |
| 835 remittance widget (dashboard display) | NO (no backing query) | YES (renders) | N/A | **Fabricated** | NO | **NO — actively misleading** | NO (shows fake data) | **BROKEN** (looks like DEMO ONLY, is worse) |
| Payment posting / claim matching (post-upload) | YES | NO | N/A | Real | NO | NO | YES | **BACKEND ONLY** |
| Credit Balance case lifecycle (create/activate/correct/cancel) | YES | YES (`CreditBalanceReportPage.tsx` via `openCreditBalanceCase`/`performCreditBalanceCaseAction`) | Not separately audited this pass | Real | YES | YES | YES | **PRODUCTION READY** |
| CMS-838 credit-balance export | YES (`GET /billing/credit-balance/cms-838-export`) | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| Facility Payment expectation lifecycle (create/activate/correct/cancel) | YES | YES (`FacilityCollectionsReportPage.tsx` dialogs) | Not separately audited this pass | Real | YES | YES | YES | **PRODUCTION READY** |
| Facility Collection Alerts — resolve | YES | YES (`/billing/facility-payments/alerts/{id}/resolve`) | Not separately audited | Real | YES | YES | YES | **PRODUCTION READY** |
| Facility Collection Alerts — acknowledge/snooze/dismiss/reassign/start-progress | YES (endpoints exist) | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| Alert thresholds management | YES (endpoint exists) | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| NOE tracking (`fetchNoeTracking` / `GET /billing/noe-tracking`) | YES | YES (`NoeTrackingPage.tsx`) | Not separately audited | Real | YES | YES | YES | **PRODUCTION READY** |
| NOE 837I generation | YES (endpoint exists) | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| NOE PDF generation | YES (endpoint exists) | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| NOE ack-status update (`PATCH .../edi-submissions/{id}/status`) | YES | NO wiring found | N/A | Real | NO | NO | YES (backend), unusable | **BACKEND ONLY** |
| POC/Certification status (`fetchPocCertificationStatus` / `GET /billing/poc-certification-status`) | YES | YES (`PocCertificationPage.tsx`) | Not separately audited | Real | YES | YES | YES | **PRODUCTION READY** |
| Rate-gap EDI guard (blocks unpriced lines from `build_837i_text`) | YES, tested (`test_edi_builder_rate_gap.py`) | N/A (a backend safeguard, not a user-facing screen) | N/A | Real | YES (protective, silent) | YES | YES | **PRODUCTION READY** (as a safeguard, not a screen) |
| ClaimEdiBatch `ack_status` correction/update | **NO** — no code anywhere updates it after creation | NO | N/A | N/A | NO | NO | N/A | **PLACEHOLDER** (field exists, is set once, and is then permanently stale) |

## Direct examples requested by the directive

**835 Upload**
- Backend: YES
- Frontend: NO
- Operational: NO
- Demo Safe: NO
- Production Safe: NO (not because the backend is wrong — it is correct
  — but because "safe" here means "usable without engineering
  intervention," and today it is not reachable by any staff member)

**"Export to Excel"**
- Backend: YES (does something real)
- Frontend: YES (button exists and works — that's the problem)
- Operational: YES (staff can click it today)
- Demo Safe: **NO**
- Production Safe: **NO**

## Rollup

- **PRODUCTION READY** (both backend and frontend genuinely wired,
  behaviorally sound): Credit Balance case lifecycle, Facility Payment
  expectation lifecycle, Facility Collection Alert "resolve," NOE
  tracking, POC/Certification status, rate-gap EDI guard.
- **BACKEND ONLY** (correct, unreachable by any user): enforced claim
  status endpoint, 835 upload/parse/posting, CMS-838 export, most
  Facility Collection Alert actions, alert thresholds, NOE 837I/PDF
  generation, NOE ack-status update.
- **BROKEN** (worse than missing — active or reachable harm):
  "Export to Excel" (status-corruption bug reachable via UI), 835
  Remittance widget (fabricated data shown as if real).
- **PLACEHOLDER**: `ClaimEdiBatch.ack_status` (write-once, never
  corrected).
- **UNKNOWN** (not verified this pass, carried forward from Phase 5):
  Referral→Admission→Election automatic linkage; Discharge→billing
  closure trigger; Election tracking's own writer/SSOT; whether Facility
  Payment Allocation confirm/reverse (distinct from the expectation
  lifecycle) has its own frontend wiring; whether any background job
  proactively rolls benefit periods or re-checks stuck READY claims.
