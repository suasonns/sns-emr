# RNICA Redesign Impact Analysis

**STATUS: DISCOVERY ONLY — NO REDESIGN — NO CODE — NO SCHEMA — NO MIGRATIONS**

This document evaluates, for every RNICA area identified in
`RNICA_SYSTEM_DEPENDENCY_MAP.md` and `RNICA_UI_DEPENDENCY_MAP.md`, what a
future redesign would be allowed to change and what it must preserve. It
proposes no implementation.

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has locked a product decision that `diagnoses.clinicalNarrative`
> was incorrectly placed and must not remain a nurse-facing narrative input in
> the redesigned RNICA; `finalization.clinicalNarrative` is the sole
> authoritative future Clinical Narrative. The risk table below reflects the
> current repository state and is unchanged.

---

## 1. Redesign Risk Table

| Area | Safe to Completely Redesign | Safe to Reorganize | Safe to Rename | Safe to Move | Must Remain | Do Not Remove | High Risk | Unknown Impact |
|---|---|---|---|---|---|---|---|---|
| Section navigation tree | Yes | Yes | Yes (labels only) | Yes | Ability to reach every canonical section key (`rn_ica_keys.py:6-41`) | Full section coverage | — | — |
| Progress/completion indicator | Yes | Yes | Yes | Yes | Accuracy of completion state shown | — | — | — |
| Patient summary header | Yes | Yes | Yes | Yes | Correct patient/admission context display | — | — | — |
| Clinical assessment sections (pain, respiratory, safety, musculoskeletal, neurological, imminent death, psychosocial) | Layout/visual only | Yes, if all fields remain reachable | Field labels — only with clinical/regulatory review | No (field keys are consumed by validation + intelligence engine) | Every field key read by `rnica_intelligence.py:57-176` and `clinical_note_validation_engine.py:380-470` | Field presence, not visual grouping | Field key changes without backend coordination | — |
| Diagnoses / LCD / clinical narrative fields | Layout only | No | No (regulatory terms) | No | `lcdEligibilityNarrative`, `clinicalNarrative`, `clinicalNarrativeReviewed` field keys (`rnica_finalization_service.py:118-136`) | All required fields | Renaming/removing LCD narrative field breaks finalization gate | Whether LCD should become a real evaluator (out of scope for this redesign) |
| PPS/KPS/Code Status/etc. required fields | Layout only | No | No | No | Field keys enforced server-side (`clinical_note_validation_engine.py:380-470`) | All 17 required fields | Any silent removal breaks server validation with no client warning if not kept in sync | — |
| RNICA Intelligence panel | Visual redesign yes | Yes | Yes, but must not imply real ML/AI capability it lacks | Yes | Underlying call to intelligence endpoint and full field set of output (`rnica_intelligence.py:184-222`) | The panel's existence and access to `missing_evidence` | Rebranding as "AI-powered" beyond what a rules engine provides is a compliance/marketing risk, not a technical one | Whether users rely on specific wording of recommendations clinically |
| Validation error/warning display | Visual style only | No structural suppression | Yes (wording) | Yes | Must always surface all validation failures, client and server | Never suppress or truncate errors | Hiding warnings to "simplify" UX | — |
| Autosave indicator | Yes | Yes | Yes | Yes | Underlying `useAssessmentAutosave` 30s cadence and manual save path | — | — | — |
| Manual Save button | Visual only | Yes | Yes | Yes | Must remain wired to save endpoint | — | — | — |
| Signature certification attestation checkbox | Visual only | No | No (regulatory attestation label) | Limited | Boolean gate wired to `signatureCertification` (`rnica_finalization_service.py:102-109`) | The control itself and its gating behavior | Any attempt to pre-check or auto-satisfy this is a compliance violation | — |
| Clinician signature field | Visual only | No | No | Limited | Nonblank enforcement (`rnica_finalization_service.py:111-116`) | The field itself | Same as above | Whether e-signature integration is planned (none found) |
| Finalization readiness checklist display | Visual only | Yes (grouping) | Yes | Yes | Must reflect exactly the 6 server-side checks (attestation, signature, narrative-reviewed, LCD narrative, referrals reviewed, POC completeness, CHHA POC) | All checks visible | Omitting any check from the UI while server still enforces it | — |
| Lock button/flow | Visual only | No | Label only | No | Must call the same lock endpoint and cannot bypass readiness re-check | The control and its confirmation step | Treat as **DO NOT TOUCH** for logic; irreversible in effect | — |
| HOPE status displays/actions | Visual only | No | No (CMS-facing terminology) | Limited | All HOPE lifecycle states and actions (`rnica_assessment.py:33-50`, `rnica_hope_workflow_service.py`) | Every HOPE action currently exposed | Changing HOPE terminology risks regulatory/CMS submission confusion | — |
| Amendment request/approve/deny UI | Visual only | Yes | Yes (labels) | Yes | Audit-triggering behavior and mandatory deny-reason validation (`visits.py:1504-1509`) | Reachability post-lock; audit event generation | Removing the deny-reason requirement | — |
| POC-linked actions (add order from suggestion, sync problems) | Visual only | Yes | Yes | Yes | Underlying adapter calls and `rule_key` dedup (`rnica_poc_adapter.py:295-367,432-668`) | Explicit, user-initiated nature of these actions (no auto-trigger) | — | — |
| Caregiver-related recommendation text | Yes | Yes | Yes | Yes | — | — | — | Whether users conflate this with a dedicated caregiver assessment (none exists) |

---

## 2. Final Section — Required Answers

**1. What parts of RNICA are visual only?**
Section navigation tree, progress/completion indicator, patient summary
header, care team display area, autosave status indicator, general layout
of clinical sections (grouping/spacing/styling), wording of intelligence
panel recommendations (content structure must stay, exact prose can change),
label styling throughout.

**2. What parts are workflow critical?**
Manual Save button, client-side `validateRNICA` gating, Lock button and its
readiness re-check, amendment request/approve/deny flow (including mandatory
deny reason), POC-linked actions (add order from suggestion, POC problem
sync), autosave's underlying 30-second cadence.

**3. What parts are AI critical?**
The RNICA Intelligence panel and everything it renders (summary, findings,
recommendations, missing-evidence, structured-findings signals) — sourced
from `rnica_intelligence.py`. Note: this is a rules/heuristics engine, not an
LLM/ML system; redesign should not misrepresent its capability level.

**4. What parts are compliance critical?**
Diagnoses/LCD/clinical-narrative fields, PPS/KPS/Code Status/treatment- and
hospitalization-preference fields, referrals-reviewed checkbox, Plan of Care
narrative, CHHA POC completion, signature certification attestation,
clinician signature field, finalization readiness checklist (all 6 checks),
HOPE status displays and actions, amendment audit trail.

**5. What parts are billing critical?**
**None were found.** No RNICA field, action, or endpoint was found to
directly gate or feed billing readiness, claims, or NOE
(`billing_readiness_service.py:1-23` does not join RNICA data). RNICA's only
billing-adjacent element is the LCD eligibility narrative, which is a
required documentation field, not a billing computation.

**6. What parts should never be redesigned without additional review?**
Lock button/flow (irreversible in effect), signature certification
attestation and clinician signature fields, the full required-field set
enforced by `clinical_note_validation_engine.py`, the LCD eligibility
narrative field, HOPE status/action controls, and the amendment
approve/deny flow's mandatory deny-reason validation.

**7. If the entire RNICA UX changed tomorrow, what functionality must
survive unchanged?**
- All field keys read by `rnica_intelligence.py` and
  `clinical_note_validation_engine.py`
- The 6-check finalization readiness gate and its exact conditions
- Lock endpoint call, audit event (`RNICA_ASSESSMENT_LOCKED`), and re-check
  of readiness at lock time
- HOPE lifecycle states/actions and their CMS-facing semantics
- Amendment creation, approval, denial (with mandatory reason), and their
  audit events
- Autosave cadence and manual save path
- POC adapter calls and `rule_key` dedup behavior for any RNICA→POC actions
- Section coverage — every canonical RNICA section key must remain reachable
  and editable

---

## 3. Explicit Scope Reminder

This document does not authorize, propose, or begin any redesign. It exists
solely to define the safe/unsafe boundary so that a future, separately
authorized Tenant UX redesign can proceed without breaking AI, HOPE, CTI-
adjacent attestations, F2F (not connected), IDG (not connected), POC,
validation, billing readiness (not connected), compliance logic, or survey
readiness (not connected) — see `RNICA_SYSTEM_DEPENDENCY_MAP.md` Section 3
for the full connection/non-connection list.

**Inventory only. No implementation. No redesign. No modification.**
