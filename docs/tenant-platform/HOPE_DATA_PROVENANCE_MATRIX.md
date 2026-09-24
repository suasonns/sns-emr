# HOPE Data Provenance Matrix

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23), and
revised 2026-09-23 per the "HOPE SOURCE MODEL CORRECTION" directive to
use the official HOPE timepoint model and the allowed SNS
workflow-source categories below. This is the section-level companion
to `RNICA_HOPE_FIELD_MAP.md`: for every HOPE section, it records the
official HOPE timepoint, the authoritative SNS workflow-source
category, the concrete repository evidence for that classification,
and whether the section is single-sourced or split across more than
one origin (a split-origin section is a duplicate-authority risk per
`DUPLICATE_AUTHORITY_MATRIX.md`).

**Allowed HOPE timepoint values:** `ADM`, `HUV1`, `HUV2`, `DC`,
`SFV-linked item within the applicable ADM/HUV record`.

**Allowed SNS workflow-source categories:** `FACESHEET`,
`RNICA_ADMISSION`, `HUV1`, `HUV2`, `SFV`, `DISCHARGE`, `DERIVED`,
`NOT_VERIFIED`. The categories `GENERIC_FOLLOW_UP_VISIT`,
`CERTIFICATION`, and `RECERTIFICATION` are **removed** — every row
below that previously used a `Certification (intended)` classification
has been reclassified `NOT_VERIFIED` because no exact item-level CMS
and repository trace currently establishes a certification/iQIES
source for those items. Only the current SFV row is sourced from a
Visit, and only because it is the specific, linked SFV completion
visit identified by `SFVRequirement.completed_visit_id` — not a
generic routine follow-up visit.

| HOPE Section | Item codes | HOPE Timepoint | SNS Workflow Source | Evidence | Single-sourced? |
|---|---|---|---|---|---|
| Admin — identity/eligibility | A0500, A0600, A0700 | ADM | **FACESHEET** | `splitPatientName()`, direct SSN/Medicare/Medicaid passthrough (`hopeReportMapper.js:328-340, 565-568`) | Yes |
| Admin — site of service / admitted-from / living arrangement | A0215, A1805, A1905, A1910 | ADM | **RNICA_ADMISSION** | `demographics.livingSituation.*`, official code maps (`hopeReportMapper.js:58-103`) | Yes |
| Admin — timepoint/dates | A0220, A0250, A2115 | ADM / DC | **DERIVED** (mixed fallback chain) | `patient.socDate` (FACESHEET) → `admissionsOrder.levelOfCare.effectiveDate` (RNICA_ADMISSION) → `completionDate` (signature) fallback chain; discharge fields are caller-supplied, not RNICA | **No — 3-way fallback chain is itself a provenance risk** |
| Admin — demographics (sex/race/ethnicity/language) | A0810, A1005, A1010, A1110 | ADM | **RNICA_ADMISSION**, but overlaps a FACESHEET-owned `patient.sex`/`.dob` also read as a fallback | `demographics.gender` ‖ `patient.sex` (`hopeReportMapper.js` `SEX_MAP` usage; `RNICA.jsx:7987-7999`) | **No — dual-source fallback (`‖`) between RNICA_ADMISSION and FACESHEET fields** |
| Admin — payer | A1400 | ADM | **FACESHEET** | `patient.primaryPayerType`/`.secondaryPayerType`, crosswalk (`hopeReportMapper.js:152-183`) | Yes |
| Preferences | F2000, F2100, F2200, F3000 | ADM (also applicable at HUV1/HUV2 per official item set — not yet independently traced for those timepoints) | **RNICA_ADMISSION** | `demographics.advancedCarePlanning.*`, `spiritual.*` (`hopeReportMapper.js:311-325`) | Yes for ADM |
| Diagnoses | I0010, I0600, I6202, I8005 + 12 undeclared codes | ADM | **RNICA_ADMISSION** | `diagnoses.primaryDiagnosis`, `diagnoses.hopeComorbidities.*` (`RNICA.jsx:2499-2668`) | Yes |
| Symptom screening/impact | J0050, J0900-J0915, J2030, J2040, J2050, J2051A-H | ADM (also applicable at HUV1/HUV2 — not yet independently traced for those timepoints) | **RNICA_ADMISSION** | `pain.*`, `respiratory.*`, `symptomImpact.*` | Yes, but J0050 is **CONFLICTING**: both `imminentDeath.appearsThreeDaysOrLess` and `diagnoses.terminalPrognosis` are tagged `J0050`, and only the former is read (`HOPE_FIELD_TRACE_MATRIX.md` §4) |
| SFV | J2052, J2053 | **SFV-linked item within the applicable ADM/HUV record** | **SFV** — the exact linked completion visit identified by `SFVRequirement.completed_visit_id`, never a generic follow-up visit, the triggering assessment, or a patient-level "latest visit" | Backend/mapper: `SFVRequirement.completed_visit_id` → `ClinicalNote.content.symptom_impact`, `backend/app/api/visits.py` (`_extract_symptom_impact_from_content`, `list_sfv_requirements`); frontend: `hopeReportMapper.js` reads `sfvRequirement.status`/`.completedAt`/`.symptomImpact` exclusively — **VERIFIED, RESOLVED** at the mapper-function level (corrected by commits `b4da769`/`0f177a3`; see `J2052_LINEAGE_VERIFICATION.md`). **However, VERIFIED BY REPOSITORY TRACE that the *caller* (`HopeReport.jsx`) currently selects `sfvRequirement` as the patient's single most-recently-completed SFVRequirement, not one scoped to the specific ADM/HUV1/HUV2 record being viewed** (see `HUV1_PROVENANCE_TRACE.md` OPEN QUESTION). This is a UI-wiring-level open question, not a regression of the mapper fix. J2052C's reason-not-completed source remains **NOT_VERIFIED** — see `J2052C_SOURCE_DISCOVERY.md` (no authoritative source exists). | **Partially — the mapper function itself has no cross-assignment risk; the caller's selection does, pending Romel decision** |
| Skin | M1190, M1195, M1200 | ADM | **RNICA_ADMISSION** | `skin.*` (`RNICA.jsx:9360`) | Partially — `M1190` is also tagged on an unrelated `performanceStatus` field in `SIDEBAR_CONFIG` (`RNICA.jsx:209`), a **CONFLICTING** dual-tag, not a dual-write |
| Medications | N0500, N0510, N0520 | ADM | **NOT_VERIFIED** | No live RNICA screen; `medications` absent from `FORM_REGISTRY` (`RNICA.jsx:242-249`); only a data-seed script writes these paths | N/A — no source exists today |
| Signatures | Z0500 (signature fields) | ADM / HUV1 / HUV2 / DC (per the applicable assessment being signed) | **DERIVED** (visit/assessment authentication metadata, not a distinct HOPE data source) | `finalization.clinicianSignature`, `.signatureDate` (`RNICA.jsx:9719-9720`) | Yes |
| Finalization / submission metadata | Z0350, Z0500 (submission fields) | ADM (not yet independently traced for HUV1/HUV2/DC) | **RNICA_ADMISSION** workflow record (`RnicaAssessment.hope_*` columns), synced from `finalization.*` | `rnica_hope_workflow_service.py:45-51, 95-99` | Yes, one-directional sync (form_data → workflow columns) |
| Encounter chronology / dates | (supports A0220, Z0350) | ADM (not yet independently traced for HUV1/HUV2/DC) | **RNICA_ADMISSION** workflow record | `RnicaAssessment.hope_event_date`, `.hope_submission_due_at`, `.hope_overdue_at` | Not independently traced this pass — flagged open |
| Validation / acceptance / rejection state | (no item code — workflow state only) | N/A — cross-timepoint submission state | **NOT_VERIFIED** — no certification/iQIES source is connected today; this is intentionally not classified `CERTIFICATION` because no verified item-level relationship exists | **No source exists.** `hope_validation_status`, `hope_accepted_at`, `hope_rejected_at` are unpopulated columns | N/A — target source not yet connected |
| Correction / resubmission state | (no item code — workflow state only) | N/A — cross-timepoint submission state | **NOT_VERIFIED**, plus **RNICA_ADMISSION** for the corrected content itself | `hope_correction_required`, `hope_corrected_assessment_id`, `RnicaHopeSubmissionAttempt` table all unpopulated; a **separate** `RnicaAmendment` mechanism exists for clinical corrections but is not wired to these columns | N/A — two disconnected mechanisms, neither reaching this state today |

## Summary counts

- **FACESHEET-sourced sections:** Admin identity/eligibility, Payer (2 of 15 rows) — clean single-source.
- **RNICA_ADMISSION-sourced sections:** Preferences, Diagnoses, Symptom screening, Skin, most Admin demographics, Finalization/submission metadata, Encounter chronology (7 of 15 rows) — clean single-source except the noted J0050/M1190 tag conflicts (not dual-write, just dual-tagging — a registry hygiene issue, not a data-integrity issue). **HUV1/HUV2-specific re-derivation of Preferences/Symptom screening is NOT_VERIFIED** — those sections are currently traced only for the ADM timepoint.
- **SFV-sourced sections:** SFV (J2052/J2053) — 1 of 15 rows — now single-sourced and RESOLVED (see row above); this was the single highest-priority provenance defect in this matrix (`RNICA_HOPE_FIELD_MAP.md` §2, `TOP_20_RNICA_HOPE_BLOCKERS.md` #1) and is now closed.
- **DERIVED (mixed/fallback-chain) sections:** Admin timepoint/dates, Admin sex/race/ethnicity/language, Signatures (3 of 15 rows) — these are provenance risks even though each individual read succeeds, because a silent fallback can mask which system actually authored the value in a given record.
- **NOT_VERIFIED:** Medications, Validation/acceptance/rejection, Correction/resubmission (3 of 15 rows) — these are stages/sections with zero implementation or unverified source claims, not merely provenance ambiguity. None may be treated as a `CERTIFICATION` source until an exact item-level CMS and repository trace proves otherwise.
- **HUV1/HUV2/Discharge (DC) timepoint provenance is now independently traced** in `HUV1_PROVENANCE_TRACE.md`, `HUV2_PROVENANCE_TRACE.md`, and `DC_PROVENANCE_TRACE.md` — VERIFIED BY REPOSITORY TRACE for: Day-0/window timing math (election date + 6-15 / +16-30 days), source-record selection (a distinct locked `RnicaAssessment` row per admission, never an admission-data fallback), UI honest-placeholder gating, and Discharge's administrative-only scope with CMS-coded reason via `GRANULAR_DISCHARGE_REASONS`. Each trace also records its own NOT_VERIFIED items (chiefly: full CMS item-set *completeness* per timepoint was not cross-checked item-by-item in this pass, and `validate_huv_visit_completion`'s internal arithmetic was not re-opened). The rows in the table above still only enumerate item-level detail for ADM; HUV1/HUV2/DC-specific item enumeration lives in the three trace documents rather than being duplicated here. This is required before `HopeGenerationService` implementation may begin per `HOPE_GENERATION_SERVICE_DESIGN.md`, and remains blocked on: (1) item-set completeness verification for HUV1/HUV2/DC, (2) the `HopeReport.jsx` SFV-selection open question, and (3) J2052C source resolution.

