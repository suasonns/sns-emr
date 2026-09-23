# Duplicate Authority Matrix (Phase 2, independent re-trace)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — see `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-010, Facesheet/RNICA duplication).

**Scope:** every clinical fact found in this pass to be **editable/writable
from two or more different screens, cards, or stores**. Commit `16264cf`.

A row qualifies only when two independent *write* paths exist. Read-only
mirrors are listed separately in §3 and are not duplicates of authority.

---

## 1. RN ICA `form_data.demographics` vs Patient Facesheet

RNICA persists demographics inside the assessment JSONB
(`form_data.demographics`, rendered by `renderDemographics()`
`RNICA.jsx:7966-8207`). The Facesheet persists the same facts on the patient
record (`PatientFacesheet.jsx` draft → `saveFacesheet` payload
`:398-412`). Neither reads the other.

| # | Clinical fact | Location A (RN ICA) | Location B (Facesheet) | Authoritative? | Status |
|---|---|---|---|---|---|
| 1 | First / last name | `RNICA.jsx:7984-7985` | `PatientFacesheet.jsx:398-412` payload identity block | Facesheet asserted authoritative by `RNICA.jsx:9759-9763` comment ("displays authoritative information. It does not duplicate…") — contradicted by the editable controls | DUPLICATE_EDITABLE_AUTHORITY |
| 2 | Date of birth (A0900) | `RNICA.jsx:7986` | `PatientFacesheet.jsx:398` (`dob`), rendered `:769-782` | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 3 | Gender / sex (A0810) | `RNICA.jsx:7987-7988` | `PatientFacesheet.jsx:1201` (`editable`) | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 4 | Phone | `RNICA.jsx:7989` | `PatientFacesheet.jsx:1192` (`editable`) | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 5 | Religion | `RNICA.jsx:8000` | `PatientFacesheet.jsx:1207` (`editable`) | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 6 | Marital status | `RNICA.jsx:8001-8002` | `PatientFacesheet.jsx:1208` (`editable`) | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 7 | Address (street/city/state/zip/county) — A0550 uses `.zip` | `RNICA.jsx:8011-8016` | `PatientFacesheet.jsx:406, 535-538` | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |
| 8 | Emergency contact name/relationship/phone | `RNICA.jsx:8022-8024` | `PatientFacesheet.jsx:2036` (`emergency_contact_phone`, `editable`) | REQUIRES_AUTHORITY_REVIEW | DUPLICATE_EDITABLE_AUTHORITY |

**Export consequence.** The HOPE exporter mixes the two stores in a single
record: A0550 ZIP comes from `demographics.address.zip`
(`hopeReportMapper.js:566`) while A0500 name, A0600 SSN/MBI and A0700
Medicaid number come from the Facesheet `patient` object (`:565, 567, 568`).
A record can therefore be internally inconsistent by construction.

## 2. Duplicates inside RN ICA itself

| # | Clinical fact | Location A | Location B | Authoritative? | Status |
|---|---|---|---|---|---|
| 9 | Clinical narrative | `finalization.clinicalNarrative` — textarea `RNICA.jsx:9714`, AI writer `:10313-10322` | `diagnoses.clinicalNarrative` — `RNICA.jsx:2029, 2038` (inside the undispatched `ClinicalNarrativeCard`, `:2013`/`:8353`) | `finalization.*` is the live one; `diagnoses.*` is what the Lock gate validates (`rnica_finalization_service.py:120-121`) | CONFLICTING |
| 10 | LCD eligibility narrative | `RNICA.jsx:1973-1974` (`LcdEligibilityCard`, `updateDiagnoses`) | `RNICA.jsx:1992-1993` (`LcdSupportingEvidenceCard`, `updateField`) | Same path `diagnoses.lcdEligibilityNarrative`; both cards dispatched (`:8934`, `:8943`) | DUPLICATE_EDITABLE_AUTHORITY |
| 11 | Assigned home aide | field config `RNICA.jsx:9671` | custom renderer `RNICA.jsx:8503` | Same path `haAssignment.assignedAide`; both render | DUPLICATE_EDITABLE_AUTHORITY |
| 12 | HA assignment N/A | field config `RNICA.jsx:9672` | custom renderer `RNICA.jsx:8504` | Same path `haAssignment.notApplicable` | DUPLICATE_EDITABLE_AUTHORITY |
| 13 | SFV completion | `sfv.inPersonSfvCompleted` checkbox `RNICA.jsx:9398` | `SFVRequirement.status` / `Task.status` (`hope_phase_b_engine.py:428-443`, driven from `backend/app/api/visits.py:3868-3904`) | Backend requirement is the regulatory record; the checkbox is self-attestation on the triggering visit | CONFLICTING |
| 14 | SFV trigger determination | `getSfvStatus()` `hopeReportMapper.js:400-429` | `maybe_trigger_sfv_from_hope_timepoint()` `hope_phase_b_engine.py:319-395` | Different predicates and different date sources; no reconciliation code found | CONFLICTING |
| 15 | J0050 imminence | `imminentDeath.appearsThreeDaysOrLess` (exported, `hopeReportMapper.js:609`) | `diagnoses.terminalPrognosis` tagged `hopeCode: "J0050"` (`RNICA.jsx:8925`) | `imminentDeath` is the exported one | CONFLICTING |
| 16 | BIMS vs opioid semantics on N0500-N0520 | `neurological.hopeItems.*` (`RNICA.jsx:9031-9033`) | `medications.*` (`hopeReportMapper.js:633-635`) | Undeterminable from repository | CONFLICTING |
| 17 | CHHA plan-of-care completion | `chhaPoc.completed` checkbox `RNICA.jsx:4113-4119` (Patient Chart mount `PatientChart.jsx:798`) | `CHHAPOC` model/endpoints `backend/app/api/chha_pocs.py:30, 99-114` | `RNICA.jsx:3350` comment states the RN ICA `form_data.chhaPoc` is the store and "there is no separate CHHA…" record for this flow; a separate `CHHAPOC` table nonetheless exists | REQUIRES_AUTHORITY_REVIEW |
| 18 | Vitals / MAC | `vitals.mac` in RN ICA (`RNICA.jsx:2906`) | `vitals.mac` in visit notes (`VisitNotes.jsx:700`) | Different encounters, not the same fact instance | NOT_APPLICABLE (documented to prevent a false-positive) |

## 3. Read-only mirrors (explicitly NOT duplicate authority)

| Fact | Read-only site |
|---|---|
| Height / weight / BMI / MAC on the nutrition screen | `RNICA.jsx:2932, 2947` (explicit "documented under Vitals & Measurements" notice) |
| Assigned aide on the CHHA card | `RNICA.jsx:3845` |
| CHHA completion badge in the HA Assignment renderer | `RNICA.jsx:8500, 8517` |
| PCG summary re-read for AI context | `RNICA.jsx:11400` |

## 4. Summary

| Status | Count |
|---|---|
| DUPLICATE_EDITABLE_AUTHORITY | 11 (rows 1-8, 10, 11, 12) |
| CONFLICTING | 5 (rows 9, 13, 14, 15, 16) |
| REQUIRES_AUTHORITY_REVIEW | 1 (row 17) |
| NOT_APPLICABLE | 1 (row 18) |

**Highest-risk row: #9** — the same clinical fact (the narrative that
justifies hospice eligibility) has one path the clinician writes and a
different path the Lock gate validates. See
`LOCK_GATE_DEPENDENCY_TRACE.md`.
