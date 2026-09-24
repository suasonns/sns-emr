# HOPE Data Provenance Matrix

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). This is
the section-level companion to `RNICA_HOPE_FIELD_MAP.md`: for every HOPE
section, it records the required classification (RNICA | Facesheet |
Visit | Certification | Other), the concrete repository evidence for
that classification, and whether the section is single-sourced or split
across more than one origin (a split-origin section is a duplicate-
authority risk per `DUPLICATE_AUTHORITY_MATRIX.md`).

| HOPE Section | Item codes | Provenance classification | Evidence | Single-sourced? |
|---|---|---|---|---|
| Admin — identity/eligibility | A0500, A0600, A0700 | **Facesheet** | `splitPatientName()`, direct SSN/Medicare/Medicaid passthrough (`hopeReportMapper.js:328-340, 565-568`) | Yes |
| Admin — site of service / admitted-from / living arrangement | A0215, A1805, A1905, A1910 | **RNICA** | `demographics.livingSituation.*`, official code maps (`hopeReportMapper.js:58-103`) | Yes |
| Admin — timepoint/dates | A0220, A0250, A2115 | **Other (mixed)** | `patient.socDate` (Facesheet) → `admissionsOrder.levelOfCare.effectiveDate` (RNICA) → `completionDate` (signature) fallback chain; discharge fields are caller-supplied, not RNICA | **No — 3-way fallback chain is itself a provenance risk** |
| Admin — demographics (sex/race/ethnicity/language) | A0810, A1005, A1010, A1110 | **RNICA**, but overlaps a Facesheet-owned `patient.sex`/`.dob` also read as a fallback | `demographics.gender` ‖ `patient.sex` (`hopeReportMapper.js` `SEX_MAP` usage; `RNICA.jsx:7987-7999`) | **No — dual-source fallback (`‖`) between RNICA and Facesheet fields** |
| Admin — payer | A1400 | **Facesheet** | `patient.primaryPayerType`/`.secondaryPayerType`, crosswalk (`hopeReportMapper.js:152-183`) | Yes |
| Preferences | F2000, F2100, F2200, F3000 | **RNICA** | `demographics.advancedCarePlanning.*`, `spiritual.*` (`hopeReportMapper.js:311-325`) | Yes |
| Diagnoses | I0010, I0600, I6202, I8005 + 12 undeclared codes | **RNICA** | `diagnoses.primaryDiagnosis`, `diagnoses.hopeComorbidities.*` (`RNICA.jsx:2499-2668`) | Yes |
| Symptom screening/impact | J0050, J0900-J0915, J2030, J2040, J2050, J2051A-H | **RNICA** | `pain.*`, `respiratory.*`, `symptomImpact.*` | Yes, but J0050 is **CONFLICTING**: both `imminentDeath.appearsThreeDaysOrLess` and `diagnoses.terminalPrognosis` are tagged `J0050`, and only the former is read (`HOPE_FIELD_TRACE_MATRIX.md` §4) |
| SFV | J2052, J2053 | **Visit** (a separate follow-up encounter generated from the RNICA/HOPE workflow — the triggering RNICA visit is explicitly **not** the source of the completion outcome) | Backend: `SFVRequirement.completed_visit_id`, `hope_phase_b_engine.py:397-438`. **But the exporter still reads the pre-remediation self-attested RNICA-form field** (`hopeReportMapper.js:618` reading `sfv.inPersonSfvCompleted`) | **No — the authoritative source (Visit) and the exported source (legacy RNICA self-attestation) currently disagree; this is the single highest-priority provenance defect in this matrix** |
| Skin | M1190, M1195, M1200 | **RNICA** | `skin.*` (`RNICA.jsx:9360`) | Partially — `M1190` is also tagged on an unrelated `performanceStatus` field in `SIDEBAR_CONFIG` (`RNICA.jsx:209`), a **CONFLICTING** dual-tag, not a dual-write |
| Medications | N0500, N0510, N0520 | **Other / MISSING_FROM_SNS** | No live RNICA screen; `medications` absent from `FORM_REGISTRY` (`RNICA.jsx:242-249`); only a data-seed script writes these paths | N/A — no source exists today |
| Signatures | Z0500 (signature fields) | **Visit authentication** | `finalization.clinicianSignature`, `.signatureDate` (`RNICA.jsx:9719-9720`) | Yes |
| Finalization / submission metadata | Z0350, Z0500 (submission fields) | **RNICA workflow record** (`RnicaAssessment.hope_*` columns), synced from `finalization.*` | `rnica_hope_workflow_service.py:45-51, 95-99` | Yes, one-directional sync (form_data → workflow columns) |
| Encounter chronology / dates | (supports A0220, Z0350) | **Visit / RNICA workflow record** | `RnicaAssessment.hope_event_date`, `.hope_submission_due_at`, `.hope_overdue_at` | Not independently traced this pass — flagged open |
| Validation / acceptance / rejection state | (no item code — workflow state only) | **Certification (intended)** — i.e. should be sourced from an actual iQIES certification/receipt | **No source exists.** `hope_validation_status`, `hope_accepted_at`, `hope_rejected_at` are unpopulated columns | N/A — target source not yet connected |
| Correction / resubmission state | (no item code — workflow state only) | **Certification (intended)**, plus **RNICA** for the corrected content itself | `hope_correction_required`, `hope_corrected_assessment_id`, `RnicaHopeSubmissionAttempt` table all unpopulated; a **separate** `RnicaAmendment` mechanism exists for clinical corrections but is not wired to these columns | N/A — two disconnected mechanisms, neither reaching this state today |

## Summary counts

- **Facesheet-sourced sections:** Admin identity/eligibility, Payer (2 of 15 rows) — clean single-source.
- **RNICA-sourced sections:** Preferences, Diagnoses, Symptom screening, Skin, most Admin demographics (5 of 15 rows) — clean single-source except the noted J0050/M1190 tag conflicts (not dual-write, just dual-tagging — a registry hygiene issue, not a data-integrity issue).
- **Visit-sourced sections:** Signatures, SFV (2 of 15 rows) — SFV has an active provenance mismatch that must be corrected before any redesign proceeds (see `RNICA_HOPE_FIELD_MAP.md` §2 and `TOP_20_RNICA_HOPE_BLOCKERS.md` #1).
- **Mixed/fallback-chain sections:** Admin timepoint/dates, Admin sex/race/ethnicity/language (2 of 15 rows) — these are provenance risks even though each individual read succeeds, because a silent fallback can mask which system actually authored the value in a given record.
- **No source exists today:** Medications (1 of 15 rows).
- **Target source not yet connected:** Validation/acceptance/rejection, Correction/resubmission (2 of 15 rows) — these are the two stages with zero implementation, not merely provenance ambiguity.
