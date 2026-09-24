# Missing-Field Reconciliation (Phase 2, independent verification)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — see `RNICA_PHASE3_REMEDIATION_REGISTER.md`.

**Scope:** the "missing field" claims carried in
`RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` §10 (TABLE G) and §15, re-verified
with fresh repository scans at commit `16264cf`. Every row records what I
found myself, not what the prior pass concluded.

**Scan method:** full-tree `Select-String` over `*.js, *.jsx, *.py, *.ts,
*.tsx` excluding `node_modules`, `.venv`, `dist`, `build`.

---

## 1. Claims explicitly named in the audit directive

| # | Field | Claimed status (prior pass) | Independent verification | Actual path found | Reconciliation status |
|---|---|---|---|---|---|
| 1 | `vitals.mac` (Mid-Arm Circumference) | Implied missing/under-used | **Exists and is writable.** Default `RNICA.jsx:417`; input control `RNICA.jsx:2906` (`AnthropometricsAutoBmiCard`, `<FormInput label="MAC (Mid-Arm Circumference)" … updateField("mac", v)>`); read-only mirror `RNICA.jsx:2947`; also captured in visit notes (`VisitNotes.jsx:64, 700`), trended (`ComplianceHopeBoard.jsx:166-179`), narrated (`clinicalNarrativeBuilder.js:200`), and served by the backend (`backend/app/api/patients.py:4014`, alias handling `backend/app/api/visits.py:6042-6049`) | `vitals.mac` | PRESENT_CORRECTLY_PLACED |
| 2 | `demographics.militaryService` | Implied missing | **Exists and is writable.** Default `RNICA.jsx:368`; control `RNICA.jsx:8003` (`FormSelect`, options Yes/No/Unknown) | `demographics.militaryService` | PRESENT_CORRECTLY_PLACED — but not harvested by `hopeReportMapper.js` (no read) → also PRESENT_NOT_HARVESTED for HOPE purposes |
| 3 | `demographics.pcg.healthStatus` | Implied missing | **Exists.** Default `RNICA.jsx:377`; control `RNICA.jsx:8060` (`FormRadioGroup "PCG Health Status"`); used in PCG-presence derivation `RNICA.jsx:1259` | `demographics.pcg.healthStatus` | PRESENT_CORRECTLY_PLACED |
| 4 | `demographics.pcg.anxietyLevel` | Implied missing | **Exists.** Default `RNICA.jsx:377`; control `RNICA.jsx:8062`; consumed `RNICA.jsx:1259, 11400` | `demographics.pcg.anxietyLevel` | PRESENT_CORRECTLY_PLACED |
| 5 | `demographics.pcg.ableToAdministerMeds` | Present but caregiver-scoped; "patient self-administration" missing | **Confirmed both halves.** Field exists (default `RNICA.jsx:378`, control `RNICA.jsx:8064`, CDPH warning `RNICA.jsx:998-999`). A scan for any *patient*-scoped medication self-administration field returned none | `demographics.pcg.ableToAdministerMeds` (caregiver only) | PRESENT_CORRECTLY_PLACED (caregiver) + MISSING_FROM_SNS (patient self-administration) |
| 6 | `demographics.pcg.caregiverEvaluation.cognitiveAbility` | Present but caregiver-scoped; patient "ability to understand/participate" missing | **Confirmed.** Default `RNICA.jsx:383`; control `RNICA.jsx:8086-8087`. No patient-scoped equivalent found | `demographics.pcg.caregiverEvaluation.cognitiveAbility` | PRESENT_CORRECTLY_PLACED (caregiver) + MISSING_FROM_SNS (patient) |

## 2. Other high-impact claims from TABLE G re-verified

| # | Claim (prior pass) | Independent verification | Actual path | Reconciliation status |
|---|---|---|---|---|
| 7 | TABLE G #9: "I8005 Other Medical Condition checkbox — MISSING FROM SNS (exporter expects it)" | **Refuted.** Checkbox exists at `RNICA.jsx:2668` with HOPE tag `:2671`; default `:534`; reachable via `customRenderer: "hopeComorbidities"` (`:8939`) → dispatch `:8376-8379` | `diagnoses.hopeComorbidities.other` | PRESENT_CORRECTLY_PLACED |
| 8 | TABLE G #46: "`medications.scheduledOpioid/.prnOpioid/.bowelRegimen` inputs — PRESENT BUT NOT WIRED" | **Confirmed, and stronger than stated:** the paths have *no* application writer at all. `medications` is absent from `FORM_REGISTRY` (`RNICA.jsx:242-249`); only occurrences are the exporter (`hopeReportMapper.js:529-530, 633-635`) and a seed script (`backend/scripts/populate_loren_shields.py:563-565`) | none | PRESENT_NOT_WIRED |
| 9 | TABLE G #47 / TABLE I #10: "`chhaPoc.completed` writer — REQUIRES AUTHORITY REVIEW / none located" | **Refuted.** Writer is the CHHA POC completion checkbox `RNICA.jsx:4113-4119`, persisted at `RNICA.jsx:3780`; card mounted at `sns-emr-frontend/src/charts/PatientChart.jsx:798`; read-only mirror `RNICA.jsx:8500, 8517` | `chhaPoc.completed` | PRESENT_CORRECTLY_PLACED (writer lives outside the RN ICA screen flow — discoverability, not absence) |
| 10 | TABLE G #49: "Z0400 emission — PRESENT BUT NOT HARVESTED" | **Confirmed.** `"Z0400"` occurs only at `backend/app/domain/forms/form_registry.py:416`; no occurrence anywhere in `sns-emr-frontend/src` | n/a | PRESENT_NOT_HARVESTED |
| 11 | TABLE G #50: "Disease trajectory reachable UI — PRESENT BUT NOT WIRED" | **Confirmed.** Writer `RNICA.jsx:2055` sits inside `ClinicalNarrativeCard` (`:2013`), which no `SECTION_CONFIGS` card dispatches (`:8353` condition never satisfied) | `diagnoses.diseaseTrajectory` | PRESENT_NOT_WIRED |
| 12 | TABLE G #37: "Bereavement referral never reaches the referral-review gate" | **Confirmed by inspection of the gate:** `evaluate_finalization_readiness` reads only `referrals.reviewed` (`rnica_finalization_service.py:137`); nothing reads `bereavement.bereavementVisitNeeded` in the readiness path | `bereavement.bereavementVisitNeeded` | PRESENT_NOT_WIRED |
| 13 | TABLE G #16: "BIMS total score — MISSING FROM SNS" | **Confirmed.** `neurological.hopeItems.n0500/.n0510/.n0520` are captured individually (`RNICA.jsx:9031-9033`) but no summation exists; no exporter reads them | n/a | MISSING_FROM_SNS (and the three components are PRESENT_NOT_HARVESTED — see ITEM_CODE_CONFLICT_MATRIX.md) |
| 14 | TABLE G #18: "Braden total score — MISSING FROM SNS" | Not re-derived exhaustively this pass beyond confirming `skin.pressureInjuryRisk` is a manually selected band (`RNICA.jsx:9356` area) | — | NOT_VERIFIED |
| 15 | TABLE G #44: "Goals of care narrative — MISSING FROM SNS" | Confirmed only to the extent that `finalization.clinicalNarrative` (`RNICA.jsx:9714`) is the sole free narrative in the Finalization section and is not goals-scoped | `finalization.clinicalNarrative` | NOT_VERIFIED (absence of a goals-scoped field not exhaustively proven) |

## 3. Claims not re-verified this pass

TABLE G rows 1-8, 10-15, 17, 19-36, 38-43, 45, 48 and 51 and the whole of
TABLE H (26 incomplete response sets) were **not** independently re-derived
in this pass. They remain as recorded in
`RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` and carry status **NOT_VERIFIED**
for the purposes of this Phase 2 document. They are not contradicted by
anything found here; they are simply out of the verified evidence set.

## 4. Net effect on the prior pass

| Outcome | Count | Rows |
|---|---|---|
| Prior claim confirmed | 6 | 5 (partial), 6 (partial), 8, 10, 11, 12, 13 |
| Prior claim refuted (field does exist / is reachable) | 5 | 1, 2, 3, 4, 7, 9 |
| Carried forward unverified | 2 + all of §3 | 14, 15 |

**Practical consequence:** the placement map's "missing field" register
over-reports. Five of the eleven specifically re-checked rows describe
fields that exist and are writable today. Any remediation plan built on
TABLE G without this reconciliation would have added duplicate fields for
`vitals.mac`, `demographics.militaryService`, three PCG fields, the I8005
checkbox, and a `chhaPoc.completed` writer that all already exist.
