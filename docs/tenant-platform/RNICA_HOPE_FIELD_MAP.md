# RNICA / HOPE Field Map

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). This
document does not change code; it records, for every HOPE field, the
source system, source screen, source database field, transformation
rule, HOPE destination field, validation rule, export rule, and audit
rule, so that a redesign treating RNICA+HOPE as a single lifecycle can be
scoped without re-deriving field-level evidence from scratch.

**Relationship to prior audits:** this document does not re-derive the
per-item-code UI/backend trace — that already exists, field-by-field, in
`HOPE_FIELD_TRACE_MATRIX.md` (55 registry-declared item codes) and
`RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md`. This document adds the columns
those two do not carry: **source system classification**,
**transformation rule**, **validation rule**, **export rule**, and
**audit rule**, at both the section level (required format) and, where
the source docs disagree or a field is a named example, the individual
item-code level.

---

## 1. Section-level source map (required format)

| HOPE Field / Section | Source = RNICA \| Facesheet \| Visit \| Certification \| Other |
|---|---|
| HOPE Demographics (A0500, A0550, A0600, A0700, A0900 partial) | **Facesheet** (patient record), re-displayed/edited on RNICA |
| HOPE Demographics — gender/race/ethnicity/language (A0810, A1005, A1010, A1110) | **RNICA** (`demographics.*` fields, `RNICA.jsx:7987-7999`) |
| HOPE Living Situation (A0215, A1805, A1905, A1910) | **RNICA** (`demographics.livingSituation.*`) |
| HOPE Payer (A1400) | **Facesheet** (`patient.primaryPayerType`/`.secondaryPayerType`) |
| HOPE Admission timepoint/dates (A0220, A0250, A0270, A2115) | **Visit** / **Other** — mixed: `patient.socDate` (Facesheet), `admissionsOrder.levelOfCare.effectiveDate` (RNICA order), `completionDate` (signature fallback), discharge fields (caller-supplied, no RNICA control) |
| HOPE Preferences — CPR/life-sustaining/hospitalization/spiritual (F2000, F2100, F2200, F3000) | **RNICA** (`demographics.advancedCarePlanning.*`, `spiritual.*`) |
| HOPE Diagnoses (I0010, I0600, I6202, I8005, + 12 undeclared comorbidity codes) | **RNICA** (`diagnoses.primaryDiagnosis`, `diagnoses.hopeComorbidities.*`) |
| HOPE Symptom Impact / Screening (J0050, J0900, J0905, J0910, J0915, J2030, J2040, J2050, J2051A-H) | **RNICA** (`pain.*`, `respiratory.*`, `symptomImpact.*`) |
| HOPE SFV Data (J2052, J2053) | **Visit** — a **Follow-Up Visit generated from the RNICA workflow** (`hope_phase_b_engine.py` trigger; completion recorded via `SFVRequirement`/`Visit`, not the triggering RNICA form) |
| HOPE Skin (M1190, M1195, M1200) | **RNICA** (`skin.*`) |
| HOPE Medications (N0500, N0510, N0520) | **Other / MISSING_FROM_SNS** — no live screen writes `medications.*` (see §5) |
| HOPE Signatures (Z0500 signature fields) | **Visit authentication** (`finalization.clinicianSignature`, `.signatureDate`) |
| HOPE Finalization/submission metadata (Z0350, Z0500 submission fields) | **RNICA workflow record** (`RnicaAssessment.hope_*` columns), synced server-side from `finalization.*` (`rnica_hope_workflow_service.py:45-51, 95-99`) |
| HOPE Dates generally | **Encounter chronology** — derived from visit/assessment timestamps (`hope_event_date`, `hope_submission_due_at`, signature date), not independently entered |

## 2. Per-field detail (worked examples per directive format)

For each row: (1) Source system, (2) Source screen, (3) Source DB field,
(4) Transformation rule, (5) HOPE destination field, (6) Validation
rule, (7) Export rule, (8) Audit rule.

### HOPE Demographics → Facesheet

1. Facesheet
2. Patient record / Facesheet screen
3. `patients.first_name/last_name/ssn/medicare_number/medicaid_number/dob`
4. `splitPatientName()` (`hopeReportMapper.js:328-340`); direct passthrough for SSN/Medicare/Medicaid
5. A0500, A0600, A0700, A0900
6. **NONE FOUND** — no backend validation of these values before export (see `HOPE_FIELD_TRACE_MATRIX.md` §1)
7. Included in `mapRnIcaToHopeReport()` output (`hopeReportMapper.js:565-570`); no server-side export artifact (see `HOPE_EXPORT_GAP_ANALYSIS.md`)
8. **NONE FOUND** — no `audit_event()` call records that these values were read/exported

### HOPE Symptom Impact → RNICA

1. RNICA
2. RN ICA "Symptom Impact" section (`RNICA.jsx:9396-9410`)
3. `rnica_assessments.form_data->symptomImpact.*`
4. `symptomEntries()` over `IMPACT_KEYS` (`hopeReportMapper.js:292-301, 384-392`)
5. J2050, J2051A-H (mapper emits a single `"J2051"` code — **CONFLICTING** with the 8 registry-declared codes; see `ITEM_CODE_CONFLICT_MATRIX.md`)
6. **NONE FOUND** on the backend; frontend-only completeness check via `getHopeAdmissionStatus()` (`hopeReportMapper.js:673-714`)
7. Included in mapper output; no dedicated per-code export validation
8. **NONE FOUND**

### HOPE SFV Data → Follow-Up Visit generated from RNICA workflow

1. Visit (a separate, later encounter — **not** the triggering RNICA visit)
2. Visit Notes screen, `SymptomFollowUpVisitSection` (`VisitNotes.jsx`)
3. `sfv_requirements.completed_visit_id/status`; `visits.*` for the completion encounter itself
4. `complete_sfv_requirement_from_visit()` (`hope_phase_b_engine.py:397-438`) enforces `completing_visit_id != requirement.trigger_reference_id` plus the nursing-credential gate (`patient_access.py::can_complete_sfv`)
5. J2052, J2053
6. **Backend-authoritative**: separate-visit invariant + nursing-credential authorization (see `SNS_CONSTITUTION.md` §31). **CONFLICTING with the exporter**: `hopeReportMapper.js:618` still reads the triggering form's self-attested `sfv.inPersonSfvCompleted`/`.sfvDate`, not the backend `SFVRequirement` record — the authoritative completion and the exported J2052 value are **not the same data source today**
7. Not synced back into `form_data.sfv.*` for export; this is the primary RNICA/HOPE lifecycle break for SFV (tracked as a Top-20 blocker, see `TOP_20_RNICA_HOPE_BLOCKERS.md` #1)
8. SFV completion itself is captured on `SFVRequirement`/`Visit` rows (timestamps, completing user); no `audit_event()` call wraps the completion endpoint

### HOPE Signatures → Visit authentication

1. Visit
2. RN ICA finalization screen (`RNICA.jsx:9719-9720`)
3. `rnica_assessments.form_data->finalization.clinicianSignature/.signatureDate/.signatureCertification`
4. Direct passthrough
5. Z0350 (HUV timepoint only), Z0500
6. `_require_locked()` (`rnica_hope_workflow_service.py:40-42`) — workflow actions require the assessment already be locked (signed); no separate signature-content validation
7. Included in mapper output
8. Lock/unlock transitions are recorded as columns on `RnicaAssessment` itself (`hope_unlocked_at/_by/_reason`), not as rows in the generic `AuditLog` table — see `HOPE_AUDIT_GAP_ANALYSIS.md`

### HOPE Dates → Encounter chronology

1. Visit / RNICA workflow record
2. Not independently entered on any screen; derived from admission/visit/signature timestamps and `RnicaAssessment.hope_event_date`
3. `rnica_assessments.hope_event_date/.hope_submission_due_at/.hope_overdue_at`
4. Computed at assessment-creation/finalization time (exact derivation not covered by this pass — flagged as an open trace item)
5. A0220 (partial), Z0350
6. `CheckConstraint("hope_submission_due_at IS NULL OR hope_event_date IS NOT NULL")` (`rnica_assessment.py:115-117`) — DB-level only
7. Not exposed as a discrete exportable field beyond A0220/Z0350
8. **NONE FOUND**

## 3. Fields where the default expectation (AUTO-HARVESTED) is not met

Per directive: "If any HOPE field has MANUAL ENTRY REQUIRED, document
why. The default expectation should be AUTO-HARVESTED."

| Field(s) | Why not auto-harvested | Evidence |
|---|---|---|
| N0500, N0510, N0520 (Medications) | `medications` is not a registered RNICA form section at all (`FORM_REGISTRY`, `RNICA.jsx:242-249`); no live screen writes these paths | `HOPE_FIELD_TRACE_MATRIX.md` §7; `ITEM_CODE_CONFLICT_MATRIX.md` (N0500/510/520 also collide with unrelated BIMS codes) |
| A2115 (discharge reason) | Discharge is a caller-supplied option (`options.discharge.*`), not an RNICA-authored field — by design discharge is a separate event, not a symptom/clinical finding | `HOPE_FIELD_TRACE_MATRIX.md` §1 |
| Z0400 | Declared in the registry but never emitted by any code path — not merely manual, **absent** | `HOPE_FIELD_TRACE_MATRIX.md` §8 |
| J2052/J2053 (SFV) | Authoritative value now lives on a separate `SFVRequirement`/`Visit` record (correct, post-remediation architecture), but the exporter has not yet been re-pointed at that source — currently still reads the legacy self-attested `sfv.*` path | §2 above |
| hope_validation_status, hope_accepted_at, hope_rejected_at, hope_correction_required, hope_corrected_assessment_id, hope_last_submission_attempt_at | Columns exist on `RnicaAssessment` but no service or API reads or writes them — **schema-ready, logic-absent**, not merely manual-entry | grep of `backend/app` for each name returns only the model declaration; see `HOPE_SUBMISSION_GAP_ANALYSIS.md` / `HOPE_CORRECTION_GAP_ANALYSIS.md` |

## 4. Conclusion for the redesign

Every HOPE field that has a real RNICA or Facesheet source is already
architecturally "harvested" in the sense that a mapper function reads it
— the target architecture's first four stages (Facesheet → RNICA →
Derived HOPE Objects) are **largely already true in code**, not merely a
future goal. The break is downstream: validation, export, submission,
correction, and audit are schema-scaffolded but not implemented, and one
field family (SFV) reads from the pre-remediation self-attested path
instead of the new authoritative `SFVRequirement` record. See
`RNICA_HOPE_LIFECYCLE.md` for the stage-by-stage current-vs-target
comparison.
