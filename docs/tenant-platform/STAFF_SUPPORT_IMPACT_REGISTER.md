# Staff Support Impact Register (Phase 2)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — see `RNICA_PHASE3_REMEDIATION_REGISTER.md`.

**Audience:** the RN completing the RN Initial Comprehensive Assessment.
**Nothing here is recommended for visual or cosmetic reasons.** Every item
exists because it changes safety, data integrity, regulatory exposure, or
the amount of work the RN has to do at the point of care.

**Commit:** `16264cf`. Every recommendation references the evidence document
and file:line that produced it. No code change was made this pass.

---

## 1. Ranking method

Recommendations are ordered by the directive's precedence:
1. patient safety → 2. binding regulatory necessity (every regulatory claim
is marked per `AUTHORITY_APPLICABILITY_REGISTER.md` and none is confirmed
binding this pass) → 3. staff-support benefit → 4. data-integrity risk →
5. implementation effort (lower is better at equal rank) →
6. measurable operational benefit.

---

## 2. Register

### R1 — Resolve the N0500/N0510/N0520 semantic collision
*Evidence:* `ITEM_CODE_CONFLICT_MATRIX.md` Conflict 1 —
`RNICA.jsx:9030-9033` vs `hopeReportMapper.js:633-635` vs
`structured_findings.py:1224-1270`.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | RN answers three BIMS selects (`RNICA.jsx:9031-9033`) that no export ever reads |
| Duplicate-entry burden | The same code triplet is claimed by an opioid/bowel-regimen export the RN cannot answer anywhere |
| Error-prevention benefit | High — whichever semantics is wrong, a submitted HOPE record carries values under a code that does not mean what was documented |
| Point-of-work guidance | RN currently sees "HOPE N0500: BIMS repetition required" (`RNICA.jsx:1049-1050`), a warning that may be pointing at the wrong item entirely |
| Accessibility impact | Neutral |
| Workflow clarity | High — removes contradictory HOPE tagging from the neurological screen |
| Training requirement | Re-brief on which cognitive/medication items are HOPE-reportable, once adjudicated |
| Adoption risk | Low for the RN; the risk is in the adjudication decision, not the UI |
| Regulatory necessity | UNCONFIRMED — `AUTHORITY_APPLICABILITY_REGISTER.md` row 19 |
| Success indicator | Zero repository occurrences of a HOPE item code under two different clinical meanings (currently 3) |

### R2 — Fix the Lock-gate narrative dependency
*Evidence:* `LOCK_GATE_DEPENDENCY_TRACE.md` rows 3-5;
`rnica_finalization_service.py:120-128` vs `RNICA.jsx:9714`.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | RN writes the narrative at `finalization.clinicalNarrative`; the server-side gate never looks at it, so the only enforcement is a browser-side error (`RNICA.jsx:1091-1092`) |
| Duplicate-entry burden | Two narrative paths exist; a legacy record can hold narrative text at the other path with no way to mark it reviewed (`RNICA.jsx:2140` is undispatched) |
| Error-prevention benefit | High — today a record can lock server-side with no clinical narrative at all (`test_rnica_finalization.py:56-65, 116-119`) |
| Point-of-work guidance | RN sees "Narrative reviewed" as green on the readiness checklist regardless of what they wrote |
| Accessibility impact | Neutral |
| Workflow clarity | High — one narrative, one gate |
| Training requirement | None if the gate simply moves to the live path |
| Adoption risk | Medium — legacy records carrying the old path need a decision (migrate, ignore, or grandfather) |
| Regulatory necessity | UNCONFIRMED — register rows 23, 24 |
| Success indicator | 100% of newly locked assessments contain non-empty `finalization.clinicalNarrative`, enforced server-side |

### R3 — Reconcile SFV trigger/completion between frontend and backend
*Evidence:* `SFV_LIFECYCLE_TRACE_MATRIX.md` §4;
`hopeReportMapper.js:394-398, 421` vs `hope_phase_b_engine.py:40, 140-142, 356, 425-426`.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | RN may see "SFV required" (or not) from one predicate while the task list is driven by another; an SFV task can exist with no RN-visible signal on the assessment, or vice versa |
| Duplicate-entry burden | RN self-attests `inPersonSfvCompleted` on the triggering form (`RNICA.jsx:9398`) **and** a separate visit must exist to close the backend requirement |
| Error-prevention benefit | High — a self-attested checkbox can report an SFV as done when no qualifying separate in-person visit exists |
| Point-of-work guidance | High — showing the actual `SFVRequirement` due date beats a client-recomputed one |
| Accessibility impact | Neutral |
| Workflow clarity | High |
| Training requirement | Brief on "the SFV is closed by the follow-up visit, not by a checkbox" |
| Adoption risk | Medium — RNs accustomed to the checkbox will need the replacement status display |
| Regulatory necessity | UNCONFIRMED — register rows 15, 16 |
| Success indicator | Zero assessments where `sfv.inPersonSfvCompleted === true` with no `SFVRequirement` in `COMPLETED` status |

### R4 — Establish a single authority for demographics (Facesheet vs RN ICA)
*Evidence:* `DUPLICATE_AUTHORITY_MATRIX.md` §1 (8 duplicated facts);
`RNICA.jsx:7984-8024` vs `PatientFacesheet.jsx:398-412, 1192-1208`.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | RN re-keys name, DOB, gender, phone, religion, marital status, address and emergency contact that already exist on the Facesheet |
| Duplicate-entry burden | The largest single duplicate-entry block found in this audit — 8 facts |
| Error-prevention benefit | High — HOPE records mix the two stores in one submission (`hopeReportMapper.js:565-568` vs `:566`), so divergence is silently exportable |
| Point-of-work guidance | Read-only display with an "edit on Facesheet" affordance keeps the data visible without re-entry |
| Accessibility impact | Positive — fewer redundant inputs to traverse |
| Workflow clarity | High |
| Training requirement | Low — "demographics are owned by the Facesheet" |
| Adoption risk | Medium — RNs who currently correct demographics inline lose that shortcut unless an explicit path is provided |
| Regulatory necessity | Not a regulatory item per se; a data-integrity item |
| Success indicator | Zero divergence between `form_data.demographics` and the Facesheet for the 8 fields, measured on newly created assessments |

### R5 — Re-dispatch or formally retire `ClinicalNarrativeCard`
*Evidence:* `DEAD_EXPORT_PATH_ANALYSIS.md` §5 — 8 fields orphaned behind
`RNICA.jsx:8353` with no `SECTION_CONFIGS` card declaring that renderer.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | Disease trajectory, recent hospitalizations, recent ER visits, utilization notes, RN addendum and clinician clarification are **unreachable** — the RN cannot record them at all |
| Duplicate-entry burden | None today (they are simply absent) |
| Error-prevention benefit | Medium-High — disease trajectory and utilization history are the substance of hospice eligibility documentation, and one of them (`diagnoses.diseaseTrajectory`) is tracked by `clinical_note_validation_engine.py:421-428` as a required element |
| Point-of-work guidance | High — decline/utilization evidence belongs next to the LCD review |
| Accessibility impact | Neutral |
| Workflow clarity | High — removes a whole dead component or restores six real fields |
| Training requirement | Moderate if restored (six fields re-enter the workflow) |
| Adoption risk | Low |
| Regulatory necessity | UNCONFIRMED — register rows 23, 26 |
| Success indicator | Zero `SECTION_CONFIGS`-orphaned custom renderers (currently 1, holding 8 fields) |

### R6 — Wire or retire `medications.scheduledOpioid` / `.prnOpioid` / `.bowelRegimen`
*Evidence:* `DEAD_EXPORT_PATH_ANALYSIS.md` §2 rows 1-3.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | None (nothing to fill in) — but the HOPE report always reports "No"/"Not applicable" for the medication section regardless of the patient's actual regimen |
| Duplicate-entry burden | Potentially creates one if added naively: medication orders already exist elsewhere in the product (`OrdersHubCard`/`MedicationOrdersCard`, `PatientChart.jsx:11`) |
| Error-prevention benefit | High — an opioid patient with no bowel regimen is a recognised safety pattern, and the current export cannot detect it |
| Point-of-work guidance | High if derived from existing medication orders rather than re-asked |
| Accessibility impact | Neutral |
| Workflow clarity | Medium |
| Training requirement | Low if derived, moderate if newly asked |
| Adoption risk | Medium — a new three-question block is added burden unless derived |
| Regulatory necessity | UNCONFIRMED and **contingent on R1** — if N0500-N0520 turn out to be BIMS items, this recommendation changes shape entirely |
| Success indicator | N0500/N0510/N0520 export values differ across patients (today they are constant) |

### R7 — Referrals relocation (Screen 7, Caregiver & Support)
*Evidence:* `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` §17;
`rnicaThirteenScreenTaxonomy.js` places `referrals` under `evidenceIntake`.
The `referrals.reviewed` Lock gate is satisfiable today
(`RNICA.jsx:9704` → `rnica_finalization_service.py:137`).

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | Referral decisions are made while assessing caregiver/psychosocial needs but must be recorded on an intake screen |
| Duplicate-entry burden | None |
| Error-prevention benefit | Medium — `bereavement.bereavementVisitNeeded` never reaches the referral-review gate (`MISSING_FIELD_RECONCILIATION.md` row 12), so a needed bereavement referral can be missed at lock |
| Point-of-work guidance | High — decision and documentation co-located |
| Accessibility impact | Neutral |
| Workflow clarity | Medium-High |
| Training requirement | Low (screen location change only) |
| Adoption risk | Low |
| Regulatory necessity | Not established as binding |
| Success indicator | Reduction in assessments locked with `referrals.reviewed = true` while a discipline-need flag elsewhere is set and unreferred |

### R8 — Decompose "Communications & Other Factors"
*Evidence:* `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` §14 (legacy block spans
Screens 1, 7, 8 and 9 in the target model).

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | A single legacy block mixes HOPE admin items (A0215/A1805), caregiver facts, medication-administration safety and ACP preferences |
| Duplicate-entry burden | None identified |
| Error-prevention benefit | Low-Medium |
| Point-of-work guidance | Medium |
| Accessibility impact | Neutral |
| Workflow clarity | Medium |
| Training requirement | Moderate — familiar content moves |
| Adoption risk | Medium — highest churn for the least safety benefit of any item here |
| Regulatory necessity | Not established |
| Success indicator | Each field in the block has exactly one owning screen in the taxonomy |

### R9 — Correct the sidebar HOPE tagging (M1190 on Performance Status; J0050 on Diagnoses)
*Evidence:* `ITEM_CODE_CONFLICT_MATRIX.md` Conflicts 2 and 3;
`RNICA.jsx:208-209` vs `hopeReportMapper.js:609, 625`;
completion math `hopeReportMapper.js:689-697`.

| Dimension | Assessment |
|---|---|
| Affected role | RN |
| Current burden | The completion indicator can mark a screen incomplete for an item the screen does not own, sending the RN to look for a field that is not there |
| Duplicate-entry burden | None |
| Error-prevention benefit | Medium — false-negative completion signals erode trust in the whole indicator |
| Point-of-work guidance | High relative to effort |
| Accessibility impact | Neutral |
| Workflow clarity | High |
| Training requirement | None |
| Adoption risk | Very low |
| Regulatory necessity | UNCONFIRMED — register rows 20, 14 |
| Success indicator | Zero screens whose declared HOPE codes are not exported from that screen's own module (currently 2) |

### R10 — Reconcile the registry inventory with the exporter inventory (incl. Z0400)
*Evidence:* `ITEM_CODE_CONFLICT_MATRIX.md` Conflicts 6 and 7;
`form_registry.py:371-376, 416` vs `hopeReportMapper.js:440-453, 603`.

| Dimension | Assessment |
|---|---|
| Affected role | RN (indirectly), plus compliance staff |
| Current burden | None at the point of care |
| Duplicate-entry burden | None |
| Error-prevention benefit | Medium — the registry is currently not a trustworthy statement of what RN ICA harvests, so gap reporting built on it under-reports |
| Point-of-work guidance | None directly |
| Accessibility impact | Neutral |
| Workflow clarity | Low direct effect |
| Training requirement | None |
| Adoption risk | Very low (declaration-only change) |
| Regulatory necessity | UNCONFIRMED — register rows 21, 22 |
| Success indicator | Registry code set == exporter code set (today: 13 emitted-not-declared, 1 declared-not-emitted) |

---

## 3. Ranked order

| Rank | Item | Primary driver |
|---|---|---|
| 1 | **R1** N0500/N0510/N0520 collision | Patient safety + submission correctness; contradictory clinical semantics live in production code |
| 2 | **R2** Lock-gate narrative dependency | Patient safety/record integrity; a legally significant record can lock with no narrative, and legacy records can become un-lockable |
| 3 | **R3** SFV trigger/completion reconciliation | Patient safety (a symptomatic patient's follow-up visit) + self-attestation risk |
| 4 | **R6** Opioid/bowel-regimen capture | Patient safety (opioid-induced constipation), but contingent on R1 |
| 5 | **R5** Re-dispatch or retire `ClinicalNarrativeCard` | Data integrity — 8 fields, including a validation-tracked one, are unreachable |
| 6 | **R4** Demographics authority | Largest duplicate-entry burden; data-integrity risk on exported identity items |
| 7 | **R9** Sidebar HOPE tagging | Very low effort, direct point-of-work benefit |
| 8 | **R7** Referrals relocation | Staff-support + a real missed-referral gap |
| 9 | **R10** Registry/exporter reconciliation | Data integrity for compliance reporting; declaration-only |
| 10 | **R8** "Communications & Other Factors" decomposition | Highest churn, lowest safety yield; do last |

**Standing caveat.** Every "regulatory necessity" line above is
UNCONFIRMED. See `AUTHORITY_APPLICABILITY_REGISTER.md`: no external
regulatory source was accessible in this environment, and human
compliance/legal review is required before any item here is treated as a
regulatory obligation rather than an internal quality decision.
