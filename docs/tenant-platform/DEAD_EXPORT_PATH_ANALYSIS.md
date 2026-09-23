# Dead Export Path Analysis (Phase 2, independent re-trace)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED for confirmed findings; the I8005 allegation specifically is REFUTED/CLOSED (real UI writer confirmed at `RNICA.jsx:2668`) — see `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-015 closed, P3-003/P3-004/P3-005 open).

**Scope:** every JSON path read by
`sns-emr-frontend/src/intake/hopeReportMapper.js` at commit `16264cf`,
checked against a repository-wide search for a writable UI control (or any
application writer) for that path.

**Method.** The full mapper (717 lines) was read. Each `formData.*` /
destructured section read was extracted, then each path was searched with
`Select-String` across `sns-emr-frontend/src` and `backend/app`. A path is
"reachable" only if an actual input control (or an AI/structured-finding
writer) targets it.

---

## 1. Headline correction — I8005 / `diagnoses.hopeComorbidities.other` is NOT dead

The prior pass asserted that `hopeComorbidities.other` has no input control
because `HOPE_COMORBIDITY_CATEGORIES` (`RNICA.jsx:2496-2512`) contains 14
entries and no `other` key. That reasoning is incomplete: the `other`
checkbox is rendered **outside** the category loop.

| Evidence | File:line |
|---|---|
| Default state declares `other: false` | `RNICA.jsx:534` |
| Dedicated writable checkbox, labelled "Other Medical Condition", `onChange={(e) => setHope("other", e.target.checked)}` | `RNICA.jsx:2668` |
| Its HOPE tag rendered as I8005 | `RNICA.jsx:2671` |
| `setHope` writer | `RNICA.jsx:2586` (`updateField('hopeComorbidities.${key}')`) |
| Card is reachable: `customRenderer: "hopeComorbidities"` declared on a Diagnoses card | `RNICA.jsx:8939` |
| Dispatch branch that renders it | `RNICA.jsx:8376-8379` |
| Structured-mode detection also honours `.other` | `hopeReportMapper.js:459` |
| Exporter | `hopeReportMapper.js:542` (structured), `:547` (legacy-derived) |

**Status: PRESENT_CORRECTLY_PLACED.** Finding C is refuted.

---

## 2. Genuinely unreachable export paths

| # | Export field | Path read | Exporter file:line | UI-control search result | Status |
|---|---|---|---|---|---|
| 1 | N0500 Scheduled Opioid | `medications.scheduledOpioid`, `.scheduledOpioidDate` | `hopeReportMapper.js:633` (+`:529`) | No writer. `medications` is not one of the 27 sections in `FORM_REGISTRY` (`RNICA.jsx:242-249`). Full-tree scan for `scheduledOpioid` returns only the mapper and `backend/scripts/populate_loren_shields.py:563` (a seed script) | PRESENT_NOT_WIRED |
| 2 | N0510 PRN Opioid | `medications.prnOpioid`, `.prnOpioidDate` | `hopeReportMapper.js:634` (+`:529`) | Same — only mapper + `populate_loren_shields.py:564` | PRESENT_NOT_WIRED |
| 3 | N0520 Bowel Regimen | `medications.bowelRegimen`, `.bowelRegimenDate` | `hopeReportMapper.js:635` (+`:530`) | Same — only mapper + `populate_loren_shields.py:565`. Note `gastrointestinal.reasonBowelRegimenNotInitiated` (`RNICA.jsx:9195`) exists but is never read by the mapper | PRESENT_NOT_WIRED |
| 4 | A0270 Discharge Date | `options.discharge.dischargeDate` | `hopeReportMapper.js:561` | Caller-supplied option object; no RN ICA control. Only reachable if a discharge caller passes it | PRESENT_NOT_WIRED |
| 5 | A2115 Reason for Discharge | `options.discharge.reasonCode/.reasonLabel` | `hopeReportMapper.js:562` | Same | PRESENT_NOT_WIRED |
| 6 | Z0500 submission bookkeeping | `finalization.hopeSubmissionNumber`, `.hopeAlreadySubmitted` | `hopeReportMapper.js:644` | Not an RN ICA form field; written server-side by `rnica_hope_workflow_service.py:45-51` and injected at `backend/app/api/visits.py:146-147` | PRESENT_CORRECTLY_PLACED (reachable, but not via the RN ICA form) |

## 3. Reachable-but-indirect paths (documented so they are not mistaken for dead)

| Export field | Path read | Exporter file:line | Writer | Status |
|---|---|---|---|---|
| A0500/A0600/A0700/A1400 | `patient.*` (Facesheet object) | `:565, 567, 568, 574` | `PatientFacesheet.jsx` draft/save (`:398-412, 505-515`) | PRESENT_CORRECTLY_PLACED |
| A0100 | `agency.*` | `:555` | Agency configuration, not RN ICA | PRESENT_CORRECTLY_PLACED |
| A0220 admission date, 3rd fallback | `assessmentMeta.lockedAt/updatedAt/createdAt` via `completionDate` (`:479`) | `:557` | Assessment metadata; can emit a signature/lock date as the admission date | REQUIRES_AUTHORITY_REVIEW |
| J0905 | derived from `pain.painIntensity.current`, `.painManagementPlan`, `.painLocation` | `:611` | Pain module controls exist, but there is no discrete J0905 control | PRESENT_NOT_WIRED (item is inferred, never answered) |
| J2030 A | `respiratory.shortnessOfBreathScreened` ‖ `.sobSeverity` | `:614` | `respiratory` module | PRESENT_CORRECTLY_PLACED |
| M1200 | `skin.woundImpairment`, `skin.notes` (`deriveSkinTreatments` `:352-357`) | `:627` | `skin` module; the structured wound list (`RNICA.jsx:9360`, `WoundListCard`) is **not** read | PRESENT_NOT_HARVESTED |
| J2052 | `sfv.inPersonSfvCompleted`, `.sfvDate`, `.reasonNotCompleted` | `:618` | `RNICA.jsx:9398-9400` — self-attested on the triggering form | CONFLICTING (see SFV_LIFECYCLE_TRACE_MATRIX.md) |

## 4. Inverse problem — captured but never exported (dead *capture* paths)

| Captured path | Writer file:line | Read by exporter? | Status |
|---|---|---|---|
| `neurological.hopeItems.n0500/.n0510/.n0520` | `RNICA.jsx:9031-9033`; AI writer `backend/app/services/evidence/structured_findings.py:1226-1270` | No | PRESENT_NOT_HARVESTED |
| `diagnoses.hopeComorbidities.additionalNote` | `RNICA.jsx:2679-2682` (`setHope("additionalNote", …)`) | No | PRESENT_NOT_HARVESTED |
| `diagnoses.terminalPrognosis` (tagged J0050) | `RNICA.jsx:8925` | No | PRESENT_NOT_HARVESTED |
| `gastrointestinal.reasonBowelRegimenNotInitiated` | `RNICA.jsx:9195` | No | PRESENT_NOT_HARVESTED |
| Structured wound rows (`skin` wound list) | `RNICA.jsx:9360` (`customRenderer: "woundList"`) | No (only `woundImpairment`/`notes`) | PRESENT_NOT_HARVESTED |

## 5. Unreachable *capture* paths (whole card not dispatched)

Everything rendered by `ClinicalNarrativeCard` (`RNICA.jsx:2013-2160`) is
unreachable, because its dispatch branch
(`RNICA.jsx:8353-8362`, `card.customRenderer === "clinicalNarrative"`) is
never satisfied: no card in `SECTION_CONFIGS` declares
`customRenderer: "clinicalNarrative"` (full-file scan of
`customRenderer:` occurrences returned `anthropometricsAutoBmi`,
`secondaryDiagnoses`, `lcdEligibility`, `hopeComorbidities`,
`lcdSupportingEvidence`, `declineTracker`, `patientAllergies`,
`constipationAutoAssess`, `nutritionAnthropometricReference`,
`weightLossAutoCalc`, `woundList`, `dmeStatus`,
`disciplineFrequencyOfVisit`, `haAssignment`, `finalReviewDashboard` — no
`clinicalNarrative`).

| Orphaned field | Writer inside the unreachable card |
|---|---|
| `diagnoses.clinicalNarrative` | `RNICA.jsx:2029, 2038` |
| `diagnoses.clinicalNarrativeReviewed` | `RNICA.jsx:2033, 2039, 2140` |
| `diagnoses.diseaseTrajectory` | `RNICA.jsx:2055` |
| `diagnoses.recentHospitalizations` | `RNICA.jsx:2074` |
| `diagnoses.recentErVisits` | `RNICA.jsx:2084` |
| `diagnoses.utilizationNotes` | `RNICA.jsx:2094` |
| `diagnoses.rnAddendum` | `RNICA.jsx:2150` |
| `diagnoses.clinicianClarification` | `RNICA.jsx:2157` |

Status for all eight: **PRESENT_NOT_WIRED**. Consequences for the Lock gate
are in `LOCK_GATE_DEPENDENCY_TRACE.md`.

**Counts:** 5 genuinely unreachable export paths; 1 prior "dead path" claim
refuted; 5 dead capture paths; 8 fields orphaned behind an undispatched card.
