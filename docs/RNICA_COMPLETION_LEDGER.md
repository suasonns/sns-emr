# RNICA Completion Ledger

Source of scope: `SNS_RNICA_MASTER_MAP_1.1.md` + `SNS_RNICA_GAP_VALIDATION_2.0.md`
(19 cross-validated gaps: 9 HOPE-derivation, 10 non-HOPE structural). No new
requirements added. Status verified against current code on this branch, not
against the frozen docs' original (older) description.

States used: DONE, INCOMPLETE, BLOCKED, OWNER ACCEPTANCE REQUIRED.

## A. Section 1 — Patient & Encounter Snapshot

| Item | Status |
|---|---|
| Read-only frame calling existing `/patients/{id}/facesheet` (no new backend field/model) | DONE |
| Care Team responsive equal-width grid (3/2/1 col, badge top-right, compact UNASSIGNED) | DONE |
| Assigned RN/disciplines from existing `PatientAssignment` source (AUTO/MANUAL/UNASSIGNED) | DONE |
| Caregiver / decision-maker / emergency contact from existing `patient_contacts` | DONE |
| Plan of Care link reusing existing `/plan-of-care?patientId=` route | DONE |
| ACP path mismatch (F2000/F2100/F2200 sync defect, Gap Validation row 6) | INCOMPLETE |
| Browser verification of Section 1 (owner) | OWNER ACCEPTANCE REQUIRED |

**INCOMPLETE — ACP sync defect**
- Master Map section: Section 1 (Patient & Encounter Snapshot)
- Missing behavior: F2000/F2100/F2200 (advance directive/POLST/code status) values sync into HOPE/facesheet through a different field path than the one Section 1 reads, per Gap Validation row 6 ("Confirmed-implemented, sync defect only")
- Frontend file: `sns-emr-frontend/src/components/RNICA.jsx` (ACP fields), `sns-emr-frontend/src/charts/PatientFacesheet.jsx`
- Backend file: `backend/app/api/patients.py` (`_sync_facesheet_from_rnica`)
- Existing API/source: `PUT /rnica/{assessment_id}` sync path
- Smallest fix: align the ACP field key used by the RNICA→facesheet sync writer with the key Section 1/HOPE reads
- Verification: unit test on `_sync_facesheet_from_rnica` asserting ACP fields land in the same property Section 1/HOPE consumes
- Blocks completion: NO (does not prevent Section 1 or workflow from running; produces incorrect ACP value in one path)

## B. Remaining Master Map sections (2–12) — HOPE-derivation gaps

| Gap | Master Map section | Status |
|---|---|---|
| F3000 no RNICA source (Spiritual) | Section 8 | INCOMPLETE |
| J0905/J0910 no RNICA source (Pain) | Section 2 | INCOMPLETE |
| J2030/J2040 no RNICA source (Respiratory) | Section 5 | INCOMPLETE |
| M1195/M1200 no RNICA source (Integumentary) | Section 5 | INCOMPLETE |
| N0500/N0510/N0520 no RNICA source (medication orders) | Section 5 / Admission Action Center | INCOMPLETE |
| J2050 misplacement (Symptom Impact ownership conflict) | Section 7 | INCOMPLETE |
| J2051 SFV-trigger source mismatch (`clinical_notes` vs `form_data`) | Section 7 | INCOMPLETE |
| M1190/J0050 dual-listing (Integumentary/Performance/Imminent Death/Diagnoses) | Sections 3,4,5,7 | INCOMPLETE |

For each: no code change has been made this session; each requires adding the
specific field/subcard to the section's existing `form_data` shape and wiring
into the existing HOPE derivation layer. None have an existing frontend/backend
file to point to yet because the field literally does not exist in RNICA.
None of these block Section 1 or prevent the overall workflow from running
end-to-end; they block **HOPE reporting accuracy** for those specific items.

## C. Non-HOPE structural gaps

| Gap | Status | Verified against code |
|---|---|---|
| Section reorganization (28→12 sections) | DONE | `RNICA.jsx` section list already matches 12-section Master Map structure |
| JSONB-only persistence (no per-field DB types/constraints) | INCOMPLETE | `backend/app/models/rnica_assessment.py` — `form_data` is a single `JSONB` column, no per-field typed columns |
| No PATCH/DELETE endpoints | INCOMPLETE | `backend/app/api/visits.py` — only `POST /rnica/save`, `PUT /rnica/{id}`, `POST /rnica/{id}/lock` exist; no PATCH/DELETE on `/rnica/{id}` |
| Validation coverage (27/~300 fields) | INCOMPLETE | not re-counted this session; no evidence of a broader validation pass since the gap report |
| No audit trail (created_by/updated_by/locked_by, log_event) | INCOMPLETE | `rnica_assessment.py` has no `created_by`/`updated_by`/`locked_by` columns; `_safe_log_event` is called only at lock time (`visits.py:793`), not on every create/update |
| No workflow automation (Action Center triggers) | INCOMPLETE | no `ActionCenterTrigger` model/table exists anywhere in `backend/` |
| No POC evidence linkage | INCOMPLETE | `backend/app/models/poc.py` `POCProblem/POCGoal/POCIntervention` have `source_kind`/`source_diagnosis_code` but no `rnica_assessment_id` or field-level evidence FK |
| Narrative generation minimal/non-persisted | INCOMPLETE | no `ClinicalNarrative` model exists in `backend/app/models`; only referenced in a test file |
| No amendment workflow / silent-overwrite risk | **DONE** (superseded — built since the gap doc was written) | `visits.py` has `POST /rnica/{id}/correction-request`, `POST /rnica/{id}/amendments/{id}/approve`, `.../deny`; `PUT /rnica/{id}` returns HTTP 423 when `record.locked` is true, blocking silent overwrite at the API layer |
| `status` reset to `"DRAFT"` on every update | INCOMPLETE | `visits.py:703` — `record.status = "DRAFT"` still runs unconditionally on every `PUT /rnica/{id}`, even for trivial autosave updates |

## D. Blocked items

None currently BLOCKED. No attempted fix has produced an unresolved error.

## Summary

- Section 1: DONE (pending owner browser acceptance) except one non-blocking ACP sync defect.
- Completion-blocking incomplete items (items whose absence prevents declaring
  the FULL Master Map RNICA scope done, excluding cosmetic/subordinate items
  already logged as discrete non-blocking defects): **10**
  1. ACP sync defect (F2000/F2100/F2200)
  2. F3000 Spiritual field missing (Section 8)
  3. J0905/J0910 Pain fields missing (Section 2)
  4. J2030/J2040 Respiratory fields missing (Section 5)
  5. M1195/M1200 Integumentary fields missing (Section 5)
  6. N0500/N0510/N0520 medication-order fields missing (Section 5 / Admission Action Center)
  7. J2050/J2051 Symptom Impact/SFV-trigger wiring defects (Section 7)
  8. No workflow automation / Action Center triggers (Sections 2, 5, 9 + global)
  9. No POC evidence linkage (Section 11 — no current RNICA equivalent at all)
  10. Narrative generation not implemented/persisted (Section 10 — no current RNICA equivalent at all)

  Not counted as blocking (real but logged, non-blocking per stop-condition rules):
  JSONB-only persistence, no PATCH/DELETE, validation coverage gap, no per-create/update audit trail, status-reset-to-DRAFT bug, M1190/J0050 dual-listing.
