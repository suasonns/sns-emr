# SNS Implementation Gap Report 1.0 — Phase 1, Deliverable 9

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This is the first document in the sequence where a comparison against
target architecture (`SNS_RNICA_MASTER_MAP_1.0`, HOPE Crosswalk content
in `SNS_RNICA_SECTION_INVENTORY_1.0`) is authorized, per the governance
rule established for this deliverable. It does not modify any frozen
artifact. It compares current RNICA (Deliverables #1-#8) against target
architecture and records gaps; it does not redesign, remap, or propose
implementation.

Source of truth: this deliverable synthesizes Deliverables #1-#8
(`SNS_RNICA_FIELD_INVENTORY_1.0`, `SNS_RNICA_DATABASE_MAPPING_1.0`,
`SNS_RNICA_API_MAPPING_1.0`, `SNS_RNICA_VALIDATION_INVENTORY_1.0`,
`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`, `SNS_RNICA_AUDIT_INVENTORY_1.0`,
`SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0`, `SNS_POC_EVIDENCE_INVENTORY_1.0`)
against `SNS_RNICA_MASTER_MAP_1.0` and the HOPE Crosswalk research
recorded in `SNS_RNICA_SECTION_INVENTORY_1.0` ("HOPE Crosswalk
(Deliverable 6)" section and "Cross-Cutting Gaps Identified" section).

---

## 1. HOPE-item derivation status (RNICA vs. HOPE Crosswalk)

Per the existing HOPE Crosswalk research (`SNS_RNICA_SECTION_INVENTORY_1.0`),
classified into the four requested categories:

### Maps directly from RNICA (confirmed field exists and is wired)

A1005 (Ethnicity), A1010 (Race), A1110 (Language), F2000 (CPR
Preference), F2100 (Other Life-Sustaining Treatment Preferences), F2200
(Hospitalization Preference), I0010 (Principal Diagnosis), I0100-I8005
(15 HOPE comorbidity items — Cancer, Heart Failure, PVD/PAD,
Cardiovascular excl. HF, Liver Disease, Renal Disease, Sepsis, Diabetes
Mellitus, Neuropathy, Stroke, Dementia, Neurological Conditions, Seizure
Disorder, COPD, Other), J0050 (Death is Imminent — but cross-listed in
two sections, see §3), J0900 (Pain Screening), J0915 (Neuropathic Pain),
J2051 A-H (Symptom Impact, all 8), J2052 (SFV), J2053 (SFV Symptom
Impact), M1190 (Skin Conditions gate — but dual-listed, see §3).

### Maps indirectly from RNICA (requires a downstream engine/sync, not a raw field read)

- J2052/J2053 completion is tracked via `sfv_requirements` table and
  `complete_sfv_requirement_from_visit()` (`hope_phase_b_engine.py`),
  not read directly off `rnica_assessments.form_data`.
- F2000 (Code Status) is meant to sync to the shared
  `patient_code_statuses` table via `set_current_code_status()` — but
  see §3, this sync is currently broken by a path mismatch.

### Requires calculation (present as raw data, not yet an explicit HOPE-coded computed value)

- Functional decline evidence (PPS/KPS/FAST/Weight trend) supports
  hospice eligibility/M1190-adjacent documentation conceptually, but is
  only realized today as the client-side `summaryText` Decline Summary
  (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` §1) — a manually-copied
  sentence, not a stored, HOPE-coded calculated value.

### Has no RNICA source (confirmed gap — HOPE item exists, no RNICA field exists at all)

| HOPE Item | Description | Gap detail |
|---|---|---|
| F3000 | Spiritual/Existential Concerns | No SIDEBAR_CONFIG `hope` array reference anywhere in RNICA.jsx; Spiritual Screening content exists as a clinical field but is not wired as a HOPE item |
| J0905 | Pain Active Problem | No distinct field beyond general J0900/J0915 pain fields |
| J0910 | Comprehensive Pain Assessment | No distinct "comprehensive pain assessment completed" field |
| J2030 | Screening for Shortness of Breath | No distinct SOB-screening-completed/date field in Respiratory |
| J2040 | Treatment for Shortness of Breath | No distinct SOB-treatment-initiated field |
| N0500 | Scheduled Opioid | No RNICA field at all — entire N-section item absent |
| N0510 | PRN Opioid | Same as N0500 |
| N0520 | Bowel Regimen | Same as N0500; also relevant to GI assessment |
| M1195 | Types of Skin Conditions | No distinct multi-select field wired to a HOPE code |
| M1200 | Skin and Ulcer/Injury Treatments | No HOPE-coded treatments checklist; wound care exists only as free-text/POC fields |

**8 of the 10 previously-flagged "high-risk HOPE items"
(J2050-J2053, J0905-J0910, J2030-J2040, N0500-N0520, M1195-M1200, F3000)
are confirmed gaps or partial gaps** — J2052/J2053 are implemented
(indirectly), J2050 has a placement/naming issue (§3) rather than being
fully missing, and the remaining items (J0905/J0910, J2030/J2040,
N0500-N0520, M1195/M1200, F3000) have no RNICA field at all.

---

## 2. Other Current RNICA vs. Master Map gaps (non-HOPE)

| Area | Master Map / architecture expectation | Current RNICA reality | Status |
|---|---|---|---|
| Section structure | Target 12-section architecture (per `SNS_RNICA_MASTER_MAP_1.0`) | Current RNICA has 28 SIDEBAR_CONFIG sections in a different order/grouping (per `SNS_RNICA_FIELD_INVENTORY_1.0`) | Missing — reorganization not yet performed (by design; out of scope for Phase 1) |
| Field-level persistence | Implied normalized/relational data model | Single JSONB blob (`rnica_assessments.form_data`) for ~95% of fields, no per-field DB constraints (`SNS_RNICA_DATABASE_MAPPING_1.0`) | Gap — no per-field database validation or typing exists |
| API surface | Implied field/section-level API granularity | One whole-object save/update endpoint pair for the entire 28-section form; no PATCH, no DELETE (`SNS_RNICA_API_MAPPING_1.0`) | Gap — no partial update or delete capability |
| Validation | Implied comprehensive required/conditional rule coverage across all fields | Only 27 of ~300 fields have any validation rule; validation is 100% frontend, unenforced by backend or DB (`SNS_RNICA_VALIDATION_INVENTORY_1.0`) | Gap — validation coverage and enforcement layer both incomplete |
| Audit trail | Implied full audit logging | Zero `log_event()` calls in any RNICA endpoint; `rnica_assessments` has no `created_by`/`updated_by`/`locked_by` column (`SNS_RNICA_AUDIT_INVENTORY_1.0`) | Gap — no audit trail on RNICA rows themselves |
| Automation / Action Center | Implied trigger-driven task/alert generation from clinical findings | Zero Tasks, alerts, or escalations reachable from any RNICA endpoint (`SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0`) | Gap — no workflow automation exists |
| POC evidence linkage | Implied Problem→Evidence→Goal→Intervention traceability | Zero code linkage between RNICA/HOPE findings and POC generation; only a manual attestation checkbox (`SNS_POC_EVIDENCE_INVENTORY_1.0`) | Gap — no evidence-based POC linkage exists |
| Narrative generation | Implied evidence-linked generated narrative | One computed sentence (Decline Summary), clipboard-only, never persisted; all other narrative fields are plain manual text (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`) | Gap — narrative generation is minimal and not persisted |

---

## 3. Data-integrity defects found during inventory (not gaps vs. Master Map — bugs in current code, recorded as observed facts)

| Defect | Where found | Impact |
|---|---|---|
| ACP storage path mismatch | `demographics.advancedCarePlanning` (frontend/Field Inventory) vs. `form_data.advancedCarePlanning` top-level (backend `_extract_rnica_code_status`/`_extract_rnica_dpoa`/`_extract_rnica_decision_maker`, `visits.py:238-274`) | Code-status, DPOA, and Decision-Maker sync to `patient_code_statuses`/`patient_contacts` silently receives `None` on every real save — these three syncs are effectively dead code in production traffic (`SNS_RNICA_DATABASE_MAPPING_1.0` §3.3, `SNS_RNICA_API_MAPPING_1.0` §3.3, independently corroborated in `SNS_RNICA_SECTION_INVENTORY_1.0` Cross-Cutting Gaps #2) |
| M1190 dual-listing | Referenced in both `performanceStatus` and `skin` HOPE arrays | Unclear which section is authoritative for this HOPE item; a migration-time reconciliation question, not resolved today |
| J0050 dual-listing | Referenced in both `imminentDeath` and `diagnoses` HOPE arrays | Same class of issue as M1190 |
| J2050 naming/placement | RNICA's `sfv` HOPE array lists J2050, but its correct CMS meaning ("Symptom Impact Screening" gate) logically belongs with `symptomImpact`/J2051, not `sfv` | Conflates two distinct concepts under one section |
| J2051 read source for SFV trigger | SFV trigger engine reads J2051-equivalent values from `clinical_notes`, not `rnica_assessments.form_data.symptomImpact` (`SNS_RNICA_SECTION_INVENTORY_1.0` Cross-Cutting Gaps #7) | Saving/locking an RNICA assessment alone does not fire the SFV requirement |
| No backend lock-time completeness check | `lock_rnica_assessment` performs no validation at all (`SNS_RNICA_API_MAPPING_1.0` §1.5) | Any assessment can be locked via direct API call regardless of frontend rules |
| Status always reset to DRAFT on update | `update_rnica_assessment` sets `status = "DRAFT"` unconditionally (`visits.py:950`) | A previously-advanced status is silently reverted on every edit |
| No amendment/addendum workflow | Confirmed absent in codebase (`SNS_RNICA_SECTION_INVENTORY_1.0` Cross-Cutting Gaps #4) | Locked assessments cannot be formally amended; `update_rnica_assessment` has no lock check either (`SNS_RNICA_API_MAPPING_1.0` §1.4), so a locked assessment can still be silently overwritten |

## Status

**Deliverable #9 (`SNS_IMPLEMENTATION_GAP_REPORT_1.0`) complete.** HOPE
item derivation status fully classified across all four requested
categories; non-HOPE Master Map gaps recorded across section structure,
persistence, API, validation, audit, automation, POC linkage, and
narrative generation; known data-integrity defects catalogued
separately from architectural gaps. This report synthesizes only what
was already established as fact in Deliverables #1-#8 and the existing
HOPE Crosswalk research — no new architecture claims are introduced.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #10 — `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0`.
