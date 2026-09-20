# RNICA_IMPLEMENTATION_AUTHORITY.md

**Status:** Approved implementation baseline (v2 — repository-validated)
**Scope:** RNICA only
**Code changes:** Authorized only after repository validation, the Current-to-Target
Gap Report is approved, and a separate phased implementation plan is approved
in its own pull request
**Patient-chart redesign:** Not included; remains paused per explicit instruction

**Supersedes:** v1 of this document (commit `7836ca1`). v1 was written before
direct repository re-verification of routes/components/APIs/lock/amendment
behavior. Every claim below that differs from v1 is called out explicitly in
`RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`.

## 1. Purpose

Translate the approved RNICA workflow (13 screens) and Figma production-candidate
screens into engineering behavior without requiring engineers to reinterpret
design intent, and without requiring engineers to re-derive what the current
repository already does.

## 2. Controlling authority order

1. Newest controlling California CDPH hospice requirements
2. Current federal CMS hospice requirements and official HOPE guidance
3. Current CMS LCD terminal-status guidance
4. Approved RNICA authority documents (this 6-document package)
5. Approved Figma production-candidate screens
6. Current repository behavior — used as **discovery evidence**, not as
   product authority. Where repository behavior conflicts with an approved
   authority document (e.g. the `status` reset-to-`DRAFT` defect, see
   Gap Report), the repository behavior is recorded as a defect to fix, not
   as a reason to change the authority document.

If implementation authority conflicts with a newer controlling regulatory
requirement, stop the affected change, document the conflict, and follow the
newer controlling requirement.

## 3. Approved workflow (unchanged from Figma package)

1. Patient Story · 2. Evidence & Intake · 3. Functional Status · 4. Pain &
Symptom Burden · 5. Diagnosis & LCD · 6. Body Systems · 7. Caregiver &
Support · 8. Safety & Clinical Risk · 9. ACP & Goals of Care · 10. Orders &
POC · 11. Compliance & Readiness · 12. AI Action Center · 13. Finalization

`Clinical Review` may exist as a presentation/summary route only if it does
not duplicate ownership assigned to Diagnosis & LCD, Body Systems, Orders &
POC, or Finalization.

## 4. Repository entry point (confirmed)

- Route/page: `sns-emr-frontend/src/pages/RNICAPage.tsx:1-11` renders
  `<RNICA patientId=... />` from `sns-emr-frontend/src/components/RNICA.jsx`.
- `RNICA.jsx` is a single-file, 28-module component (per its own header
  comment) with legacy 28-section navigation (`NAV_SECTIONS`,
  `LEGACY_ROUTES`, lines ~157-190) that predates the approved 13-screen
  redesign. **The 13-screen navigation does not exist in code yet** — this
  is the single largest confirmed gap; see Gap Report Screen-level rows.
- Backend API base: `/visits/rnica` (`RNICA.jsx:143`); primary router in
  `backend/app/api/visits.py`.
- Frontend API surface: `sns-emr-frontend/src/api/icaAssessments.ts`
  (save/get/update/lock/delete/intelligence/POC/finalization-readiness/
  amendments/structured-findings-analytics/RN-productivity-metrics).

## 5. Locked product decisions (unchanged, restated for engineering)

- `finalization.clinicalNarrative` is the sole active nurse-facing Clinical
  Narrative. No duplicate Clinical Narrative may be introduced under
  another label (e.g. inside Diagnosis & LCD).
- Diagnosis & LCD may contain an LCD Supporting Narrative only.
- PPS and KPS are always visible; FAST/ECOG/NYHA are diagnosis-conditional
  (dementia / oncology-metastatic-hematologic / CHF-cardiomyopathy
  respectively) — enforced server-side today only for FAST and NYHA (see
  `clinical_note_validation_engine.py:987-1112`); **ECOG has no equivalent
  enforcement branch — confirmed open defect**, unchanged from prior
  verification.
- Hidden scales are not rendered as disabled, placeholder, or "Not
  Applicable."
- HOPE, POC, Validation, Structured Findings, RNICA Intelligence, Autosave,
  Lock, Amendments, Audit Trail, Required Fields, and LCD Supporting
  Narrative must be preserved — all seven of these are confirmed present in
  code today (see `RNICA_DATA_MAPPING_MATRIX.md` §Cross-Cutting).

## 6. Implementation boundaries

### Preserve
- Existing source ownership and canonical field paths (`formData.*` shape
  documented in `RNICA_DATA_MAPPING_MATRIX.md`)
- HOPE mappings and lifecycle (`rnica_hope_workflow_service.py`)
- Client and server validation (`clinical_note_validation_engine.py`)
- Explicit POC/order actions (`rnica_poc_adapter.py`, `rnica_poc.py`) — POC
  is confirmed **not** auto-generated at lock, by deliberate documented
  decision (`docs/rnica-poc-lock-no-autogen-disposition.md`)
- Lock-time server validation (`evaluate_finalization_readiness`,
  re-run server-side at `POST /visits/rnica/{id}/lock`, confirmed
  `backend/app/api/visits.py:1178-1250`)
- Amendment and audit history (`rnica_amendment.py`,
  `rnica_amendment_service.py`, `_safe_log_event`)
- Historical legacy narrative data

### Do not introduce
- AI eligibility determination, physician certification, or AI-generated
  prognosis (the existing `detectLCD`/`evaluateLCD`/`getLCDConfig` API
  returns supporting evidence facts only — confirmed in
  `sns-emr-frontend/src/api/eligibility.ts:62-87` — it must continue to be
  presented as evidence-support, never as an eligibility verdict)
- AI-generated Final Clinical Narrative
- Derived caregiver burden scoring or derived global safety/risk scoring
- Silent creation of orders or POC content
- Silent overwrite of manual clinical entries
- CTI, F2F, Survey Readiness, chart-wide AI, or Billing Readiness presented
  as connected RNICA capabilities unless separately authorized

## 7. Required terminology

Use evidence-support language: "LCD Supporting Evidence Present", "Evidence
alignment identified", "Supports LCD documentation review", "Physician
certification required."
Do not use: "Eligible", "Eligibility confirmed", "LCD match: high",
"Satisfies LCD", "Prognosis generated."

## 8. Engineering sequence

1. Inventory current routes, components, APIs, schemas, validators,
   adapters, and tests — **done this pass**; see
   `RNICA_DATA_MAPPING_MATRIX.md` and `RNICA_LOCK_READINESS_MATRIX.md`.
2. Produce a current-to-target gap report for every RNICA screen — **done
   this pass**; see `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`.
3. Confirm canonical ownership before modifying any field path.
4. Implement presentation changes (13-screen navigation shell) before
   data-model changes where possible.
5. Use forward-only migrations only when repository validation proves a
   schema change is necessary.
6. Preserve backward compatibility for historical, locked, and amended
   records.
7. Add automated tests for navigation, conditional scales, validation, AI
   boundaries, autosave, signature, lock, amendment, and audit behavior.
   17 backend test files already cover RNICA today (see
   `RNICA_LOCK_READINESS_MATRIX.md` §6); new navigation work must not
   regress them.
8. Release behind a feature flag or controlled rollout mechanism if
   available in the repository.

## 9. Definition of done

Unchanged from v1 — see `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` for the
measured distance from today's code to this definition.

## 10. Reading order for this 6-document package

1. `RNICA_IMPLEMENTATION_AUTHORITY.md` (this file) — ground rules
2. `RNICA_SCREEN_AUTHORITY_MATRIX.md` — per-screen ownership/prohibition
3. `RNICA_DATA_MAPPING_MATRIX.md` — field/API/schema mapping worksheet
4. `RNICA_AI_GOVERNANCE.md` — AI trigger/output/language rules
5. `RNICA_LOCK_READINESS_MATRIX.md` — validation/signature/lock/amendment/audit
6. `RNICA_GITHUB_HANDOFF_PLAN.md` — process for this and the follow-on PRs
7. `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` — the required classification deliverable
