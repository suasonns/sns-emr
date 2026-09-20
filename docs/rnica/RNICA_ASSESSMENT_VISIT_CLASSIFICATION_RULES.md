# RNICA Assessment and Visit Classification Rules

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED
**SCHEMA:** BLOCKED
**MIGRATIONS:** BLOCKED
**AUTOMATIC VISIT CLASSIFICATION:** BLOCKED

Repository authority sources consulted: `docs/compliance/hope-sfv-guide.md`
(canonical CMS HOPE item mapping guide) and repository-discovered HOPE/SFV
implementation (`backend/app/services/sfv_engine.py`,
`backend/app/services/hope_phase_b_engine.py`,
`backend/app/models/sfv_requirement.py`).

External authority sources consulted:

- `42 CFR §418.54` (Federal RN Initial Assessment / Initial Comprehensive
  Assessment) —
  https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-B/part-418/subpart-C/section-418.54
- California `DPH-18-002E`, §74864 (California-specific assessment timing)
- CMS HOPE overview — https://www.cms.gov/medicare/quality/hospice/hope
- HOPE Guidance Manual v1.02 —
  https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf
- HOPE v1.01→v1.02 item-set change table —
  https://www.cms.gov/files/document/hope-v1-01-1-02-guidance-manual-item-set-change-table.pdf
- HOPE technical/iQIES submission information —
  https://www.cms.gov/medicare/quality/hospice-quality-reporting-program/hope-technical-information

## 1. Purpose

Define the authority rules governing RNICA assessment selection, visit
classification, HOPE timepoints, supervisory-visit prompts, discipline
authority, and finalization. `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` and
`RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` link here and must contain only
concise summaries, not duplicate rule text.

## 2. Scope

- Referral
- Hospice election
- Admission
- Initial Assessment
- Initial Comprehensive Assessment
- Comprehensive Assessment updates
- RNICA
- MSW ICA
- SC ICA
- HOPE Admission
- HUV1
- HUV2
- SFV
- Routine RN visits
- Supervisory visits
- Recertification
- Finalization
- Corrections and amendments

## 3. Authority Classification

- **`CALIFORNIA_REQUIRED`** — State-specific (California) documentation or
  filing requirement, per a controlling California source cited in §5.4.
- **`LCD_DOCUMENTATION_GUIDANCE`** — Local Coverage Determination /
  certification-support documentation guidance. Governs what evidence
  RNICA may present in support of recertification, without itself
  authorizing eligibility determination or certification.
- **`FEDERAL_CMS_REQUIRED`** — Controlling federal hospice Conditions of
  Participation requirement (Initial Assessment, Initial Comprehensive
  Assessment, Comprehensive Assessment Update, recertification timing).
- **`OFFICIAL_HOPE_REQUIRED`** — Controlling CMS HOPE data-collection
  requirement (HOPE Admission, HUV1, HUV2, SFV item logic, iQIES
  submission), validated against `docs/compliance/hope-sfv-guide.md` and
  the repository's HOPE/SFV engine where noted.
- **`SNS_INTERNAL_WORKFLOW`** — SNS operational policy. Not a federal, CMS
  HOPE, or California requirement. Must never be described as regulatory.
- **`REPOSITORY_CURRENT_STATE`** — Behavior or field confirmed present in
  current code, cited with file path.
- **`FUTURE_PRODUCT_DECISION`** — Desired future capability not yet
  established as current functionality or a locked decision.
- **`PENDING_SOURCE_VALIDATION`** — Discovery could not yet confirm an
  authoritative source. Do not treat as adopted until validated.
- **`LEGACY_REFERENCE`** — Historical-only terminology (e.g. legacy QIES)
  retained solely for documenting past HIS behavior, not for prospective
  use.
- **`PROHIBITED`** — A behavior this document explicitly forbids regardless
  of authority source (e.g. automated eligibility determination).
- **`PROHIBITED ASSUMPTION`** — A conflation this document explicitly
  forbids treating as equivalent (e.g. RN Initial Assessment = SFV).

## 4. Authoritative Dates

Document source ownership for each date below. None of these sources were
confirmed to a specific model/field during this discovery pass unless
marked `REPOSITORY_CURRENT_STATE`; all remain `PENDING_SOURCE_VALIDATION`
until an owning field is identified.

| Date | Authority | Source Status |
| --- | --- | --- |
| Referral received date/time | `SNS_INTERNAL_WORKFLOW` | `PENDING_SOURCE_VALIDATION` |
| Election completion date/time | `FEDERAL_CMS_REQUIRED` (clock trigger) | `PENDING_SOURCE_VALIDATION` |
| Admission effective date/time | `SNS_INTERNAL_WORKFLOW` | `PENDING_SOURCE_VALIDATION` |
| Start-of-care date/time | `FEDERAL_CMS_REQUIRED` (may coincide with election) | `PENDING_SOURCE_VALIDATION` |
| Visit service date/time | `REPOSITORY_CURRENT_STATE` | Confirmed field: `visit.visit_datetime` (`backend/app/services/sfv_engine.py`) |
| Benefit-period dates | `FEDERAL_CMS_REQUIRED` | `PENDING_SOURCE_VALIDATION` |
| Recertification due date | `FEDERAL_CMS_REQUIRED` | `PENDING_SOURCE_VALIDATION` |
| Initial Assessment due date | `FEDERAL_CMS_REQUIRED` (Election + 48h) | Derived; source election date `PENDING_SOURCE_VALIDATION` |
| Initial Comprehensive Assessment due date | `FEDERAL_CMS_REQUIRED` (Election + 5 calendar days) | Derived; source election date `PENDING_SOURCE_VALIDATION` |
| HUV1 window | `OFFICIAL_HOPE_REQUIRED` (Days 6-15 after election) | `PENDING_SOURCE_VALIDATION` in code (see §7.2) |
| HUV2 window | `OFFICIAL_HOPE_REQUIRED` (Days 16-30 after election) | `PENDING_SOURCE_VALIDATION` in code (see §7.3) |
| SFV timing | `OFFICIAL_HOPE_REQUIRED` (trigger + 2 calendar days) | `REPOSITORY_CURRENT_STATE`: `sfv_engine.py` `due_date=trigger_dt + timedelta(days=2)` |

Do not calculate regulatory timing from note creation date, note signing
date, task creation date, or schedule creation date, unless the
controlling source explicitly requires that date. Do not use "referral
date" and "hospice election date" interchangeably — the federal Initial
Assessment clock maps to the completed hospice-election event, not
referral creation.

## 5. Federal Assessment Rules

Keep these three regulatory events separately traceable. They are not
interchangeable and must not collapse into a single "assessment" concept.

### 5.1 Initial Assessment — `FEDERAL_CMS_REQUIRED` (`42 CFR §418.54`)

- RN authority: completed by a hospice RN.
- 48-hour deadline: due within 48 hours after completion of the hospice
  election, unless an earlier assessment is requested.
- Immediate-needs purpose: captures immediate patient and family needs.
- Completion evidence: service date/time, completion date/time, RN author,
  status, source evidence.
- Audit requirements: all of the above must be preserved and traceable.

### 5.2 Initial Comprehensive Assessment — `FEDERAL_CMS_REQUIRED` (`42 CFR §418.54`)

- IDG responsibility: completed by the interdisciplinary group, in
  consultation with the attending physician if any.
- Five-calendar-day deadline: due no later than 5 calendar days after
  election completion.
- Physician consultation: must be preserved as its own evidence field.
- Discipline contributions: physical, psychosocial, emotional, and
  spiritual needs, addressed via discipline contributors.
- Completion evidence: contributor list, completion dates, physician
  consultation record, source records.

### 5.3 Comprehensive Assessment Update — `FEDERAL_CMS_REQUIRED`

- Condition-driven updates: completed as frequently as the patient's
  condition requires.
- Fifteen-day maximum interval: completed at least every 15 days.
- Progress toward outcomes and response to care must be addressed.
- Plan-of-Care implications: updates may drive Plan of Care revisions
  (relationship to be confirmed during Plan of Care discovery, not this
  document).
- Must not overwrite the initial comprehensive assessment record.

### 5.4 California-Specific Assessment Timing — `CALIFORNIA_REQUIRED` (`DPH-18-002E`, §74864)

Per the controlling California source cited above:

- RN Initial Assessment: within 48 hours **of admission**.
- Comprehensive Assessment: completed by hospice-employee IDT members in
  collaboration with the attending physician, within 5 days **of
  admission**.
- Assessment documentation must be written, filed in the medical record,
  and support Plan-of-Care development.

**Date-anchor discovery note:** the federal timing in §5.1/§5.2 anchors to
hospice **election** completion, while this California source anchors to
**admission**. Do not assume these are always the same date/time for a
given patient — §4 already requires separate authoritative sources for
election completion vs. admission effective date. Reconciling whether
election and admission are contemporaneous in SNS's actual workflow (or
whether the earlier/controlling date governs) remains
`PENDING_SOURCE_VALIDATION` and must be resolved before any due-date
calculation logic is implemented.

## 6. SNS Assessment Package — `SNS_INTERNAL_WORKFLOW`

SNS may organize the Initial Comprehensive Assessment as a completion
package. **RNICA, MSW ICA, and SC ICA are documented here as SNS's chosen
discipline contributions** toward satisfying the federal Initial
Comprehensive Assessment requirement (§5.2). Do not state that federal or
California regulation specifically names or mandates these three forms —
no controlling source reviewed during this discovery pass identifies them
by name. Only the underlying requirement that an interdisciplinary
comprehensive assessment occur within 5 days is `FEDERAL_CMS_REQUIRED`;
the package composition itself is `SNS_INTERNAL_WORKFLOW`.

- **RNICA contribution** — tracked independently; does not by itself
  complete the package.
- **MSW ICA contribution** — tracked independently.
- **SC ICA contribution** — tracked independently.
- **Conditional disciplines** — other required discipline assessments
  identified during further repository discovery.
- **Exemptions** — a discipline may be `EXEMPTED_WITH_REASON` only via an
  authorized reason recorded per agency policy.
- **Package completion** — package status = `COMPLETE` only when all
  required disciplines are `COMPLETE` or `EXEMPTED_WITH_REASON`.
- **Late contributions** — a late discipline contribution must be recorded
  with its actual completion date, not backdated to the due date.
- **Corrections and amendments** — package or discipline status may move
  to `CORRECTED`/`AMENDED` only via an authorized workflow, never a silent
  overwrite.

Package statuses: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`,
`EXEMPTED_WITH_REASON`, `BLOCKED`, `CORRECTED`, `AMENDED`.

Discipline-level discovery required (not yet resolved — see
`RNICA_HOPE_SOURCE_VALIDATION_GAPS.md`):

- Which disciplines are required for a given patient.
- Which contribution is required vs. conditional.
- How exemptions are authorized.
- Which source record proves each contribution.
- How package completion is calculated.
- How late or corrected contributions are handled operationally.

Comprehensive Assessment Due Date = Hospice Election Date + 5 calendar
days. Initial Assessment Due Date = Hospice Election Date + 48 hours.

If SNS expires a referral after 48 hours without a completed Initial
Assessment, classify that referral-expiration rule as
`SNS_INTERNAL_WORKFLOW`, `PENDING_SOURCE_VALIDATION` — do not describe it
as a federal requirement unless a controlling source explicitly
establishes it. Do not silently reset either the referral timer or the
federal Initial Assessment / Initial Comprehensive Assessment timer.

## 7. HOPE Classification

Do not equate Initial Assessment, Initial Comprehensive Assessment, HOPE
Admission, SFV, HUV1, and HUV2 — HOPE is a separate CMS data-collection
model from the federal assessment clock. HOPE Admission is a HOPE
record/timepoint whose required items may draw from assessment evidence;
SFV is not the federal 48-hour Initial Assessment.

**Repository-discovered (`docs/compliance/hope-sfv-guide.md`):** the "SNS
Source Field" column lists "RN ICA/HUV/Update UI" for most HOPE items,
confirming the Admission RNICA, HUV1/HUV2, and Update Assessment forms
share the same underlying documentation UI — HUV1/HUV2 reuse the RNICA
form minus HOPE/SFV-only sections rather than being bespoke forms.

### 7.1 HOPE Admission — `OFFICIAL_HOPE_REQUIRED`

Initial HOPE data-collection timepoint at hospice admission. Required
items are enumerated in `docs/compliance/hope-sfv-guide.md`.

### 7.2 HUV1 — `OFFICIAL_HOPE_REQUIRED`

- Applicable window: Days 6 through 15 after hospice election.
- If an RN visit occurs in this window and HUV1 has not been conducted,
  display: "This RN visit may qualify as HUV1."
- Require confirmation that official HUV1 requirements are satisfied. Do
  not automatically classify the visit solely because it falls within the
  date window.
- Preserve the decision, actor, timestamp, reason, and source evidence.
- If missed or late: preserve the actual visit date, do not backdate, do
  not silently mark the window satisfied, follow controlling HOPE guidance
  for the late record, and create a compliance-review item.
- **Discovery status:** repository code (`hope_phase_b_engine.py`) defines
  `HUV1` task type/alert prefix constants, but the Day 6-15 window
  computation was not located during this discovery pass — classify the
  window's code enforcement as `PENDING_SOURCE_VALIDATION`; the regulatory
  requirement itself remains `OFFICIAL_HOPE_REQUIRED`.

### 7.3 HUV2 — `OFFICIAL_HOPE_REQUIRED`

- Applicable window: Days 16 through 30 after hospice election.
- Same confirmation-required, no-auto-classification, and missed/late
  handling as HUV1 (§7.2), scoped to HUV2.
- **Discovery status:** same as HUV1 — `HUV2` task type/alert prefix
  constants exist in `hope_phase_b_engine.py`; Day 16-30 window computation
  not located — `PENDING_SOURCE_VALIDATION` for code enforcement.

### 7.4 SFV — `OFFICIAL_HOPE_REQUIRED`

Kept separate from Initial Assessment, Initial Comprehensive Assessment,
HOPE Admission, HUV1, and HUV2. SFV follows applicable moderate/severe
symptom findings identified at HOPE Admission, HUV1, or HUV2 — never
completed solely because an Initial Assessment, RN visit, or RNICA exists.

**Repository-discovered (`backend/app/services/sfv_engine.py`,
`docs/compliance/hope-sfv-guide.md`):**

- SFV requirements are created per-symptom when `symptom_severity` is
  `MODERATE` or `SEVERE` (item J2051A-H), one active `PENDING` requirement
  per patient+symptom (duplicate-prevention confirmed in code).
- `due_date = trigger_date + 2 days`, matching current HOPE change
  material stating in-person SFV should occur within 2 calendar days.
- The SFV symptom-impact item (J2052/J2053) may be conducted by an RN or
  LPN/LVN — not RN-only.
- Discovery must still validate the complete SFV trigger, timing, record,
  and submission requirements against the controlling HOPE manual before
  any implementation is authorized.

### 7.5 iQIES Relationship — `OFFICIAL_HOPE_REQUIRED` (CMS HOPE technical information: https://www.cms.gov/medicare/quality/hospice-quality-reporting-program/hope-technical-information)

HOPE records are submitted through **iQIES** — prospective HOPE submission
references in RNICA/HOPE discovery documents must use iQIES, not the
legacy QIES system. Retain "QIES" only when documenting historical HIS
modification/inactivation behavior that predates iQIES. Do not mark any
record iQIES-ready solely from RNICA status; the iQIES submission
relationship to RNICA/HOPE/SFV finalization was not traced to a specific
code path in this discovery pass — see
`RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` (`PENDING_SOURCE_VALIDATION`).

## 8. Supervisory Fallback Rules

### 8.1 Day-14 CHHA/HUV1 Review — `SNS_INTERNAL_WORKFLOW`

If the patient is admitted, the visit occurs during the official HUV1
window, the visit is an RN-performed CHHA supervisory visit, and no
completed HUV1 (or other qualifying RN visit) exists, then: display a
high-priority HUV1 review prompt, do not automatically convert the visit,
require RN confirmation, require a reason if HUV1 is declined, and create
a compliance-review item when the HUV1 window is at risk.

### 8.2 Day-28 CHHA or LVN/HUV2 Review — `SNS_INTERNAL_WORKFLOW`

Same structure as §8.1, scoped to the HUV2 window (Days 16-30), an
RN-performed CHHA or LVN supervisory visit, and no completed HUV2.

### 8.3 Separate Evidence Requirements

Supervisory-visit evidence must be preserved separately from HUV1/HUV2
evidence in both fallback scenarios — the supervisory purpose and the HUV
purpose are not the same clinical event and must not share a single
evidence record.

## 9. Discipline Authority

Discipline must come from: authenticated user identity, verified
professional credential, active employment or contract status, assigned
visit discipline, and authorized scope for the selected assessment. Do not
infer discipline from free text, note title, or schedule label.

- **Mismatch handling:** if authenticated discipline and assigned
  discipline conflict, block final classification, require authorized
  correction or reassignment, and record the attempted action in the
  audit trail.

RN-only workflows must not be available to LVN, CHHA, MSW, spiritual-care,
or other users unless the controlling workflow explicitly authorizes that
discipline.

## 10. Non-HUV RN Visit Types

For an admitted patient, an RN visit not classified as HUV1 or HUV2 may
offer only applicable choices:

- Routine RN Visit
- Updated Comprehensive Assessment
- Significant-Change Assessment
- Recertification Assessment
- Supervisory Visit

Do not create a new Initial Comprehensive Assessment for every RN visit.
Do not allow an Initial Comprehensive Assessment package to be silently
restarted after completion.

### Recertification — `FEDERAL_CMS_REQUIRED` (timing) + `SNS_INTERNAL_WORKFLOW` (suggestion UX) + `LCD_DOCUMENTATION_GUIDANCE` (evidence boundary)

When recertification is due: suggest Recertification Assessment, display
the authoritative benefit period, display the verified recertification due
date, display certification/narrative status from authoritative records,
and display patient-specific decline, function, ADLs, nutrition, symptoms,
complications, utilization, comorbidities, stability, improvement, and
explanatory evidence supporting stability/improvement findings.

RNICA may present source-linked clinical evidence, but must not:

- Automatically determine hospice eligibility.
- Generate physician certification.
- Represent an RN assessment as physician certification.
- Treat a diagnosis alone as sufficient terminal-prognosis support.
- Treat LCD criteria as an automatic pass/fail verdict.
- Replace individualized physician judgment.

## 11. Finalization Gate — `SNS_INTERNAL_WORKFLOW`

- **Pre-finalization visibility:** RNICA may display pending labels (HOPE
  Admission, HUV1, HUV2, SFV) with status and source evidence, but must
  not display the final HOPE/SFV map, publish the RNICA-to-HOPE mapping as
  final, or mark any record iQIES-ready solely from RNICA status. Hiding
  the map until finalization is `SNS_INTERNAL_WORKFLOW`, not a CMS
  requirement.
- **Finalization blockers:** display the map only after source records and
  classifications pass validation.
- **Post-finalization map:** preserve finalizing user, finalization
  date/time, RNICA version, source record identifiers, HOPE
  Admission/HUV1/HUV2/SFV statuses, and unresolved warnings.
- **Correction / Amendment / Addendum / Void / Replacement /
  Re-finalization:** post-finalization changes must use one of these
  authorized workflows. Prohibit silent overwrite of a finalized record.

## 12. Audit Requirements

Every state transition described in this document (assessment completion,
package status change, HUV/SFV confirmation or decline, discipline
mismatch, finalization, and post-finalization correction) must preserve:
actor, timestamp, reason (where applicable), and source evidence
reference. This is a documentation requirement for future design; it does
not itself implement an audit log.

## 13. Duplicate and Conflict Prevention

- Prevent duplicate HUV1 or HUV2 records per election episode.
- Prevent duplicate active SFV requirements for the same patient+symptom
  (`REPOSITORY_CURRENT_STATE`, confirmed in `sfv_engine.py`).
- Block classification on discipline mismatch (§9) until resolved.
- Do not allow a completed Initial Comprehensive Assessment package to be
  silently restarted (§6, §10).

## 14. Source References

- `docs/compliance/hope-sfv-guide.md` — canonical CMS HOPE item mapping
  guide (`REPOSITORY_CURRENT_STATE` reference).
- `backend/app/services/sfv_engine.py` — SFV requirement creation logic.
- `backend/app/services/hope_phase_b_engine.py` — HOPE/HUV/SFV task-type
  constants.
- `backend/app/models/sfv_requirement.py` — SFV requirement model.
- `RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md`
- `RNICA_HOPE_SOURCE_VALIDATION_GAPS.md`
- `RNICA_ASSESSMENT_STATE_MODEL.md`
- `RNICA_CLASSIFICATION_TEST_SCENARIOS.md`

Cross-referenced from:

- `docs/tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
- `docs/tenant-platform/RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`

## 15. Open Questions

See `RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` for the full list. Highlights:

- Where (if anywhere) is the HUV1 (Days 6-15) / HUV2 (Days 16-30) window
  computed in code today?
- What is the authoritative source/model field for hospice election date,
  as distinct from referral date and admission effective date?
- Is there a California-specific (`CALIFORNIA_REQUIRED`) documentation or
  filing requirement beyond the federal rules in §5? None was located in
  this discovery pass.
- What is the current iQIES submission code path, if any, and how does it
  relate to RNICA/HOPE/SFV finalization?

## Final Classification Summary

| Rule | Classification |
| --- | --- |
| RN Initial Assessment timing | `FEDERAL_CMS_REQUIRED` |
| Initial Comprehensive Assessment timing | `FEDERAL_CMS_REQUIRED` |
| Comprehensive Assessment update at least every 15 days | `FEDERAL_CMS_REQUIRED` |
| California assessment documentation and filing | `CALIFORNIA_REQUIRED` (§5.4) |
| RNICA/MSW ICA/SC ICA package composition | `SNS_INTERNAL_WORKFLOW` |
| SNS referral expiration | `SNS_INTERNAL_WORKFLOW`, `PENDING_SOURCE_VALIDATION` |
| HUV1 Days 6-15 | `OFFICIAL_HOPE_REQUIRED` |
| HUV2 Days 16-30 | `OFFICIAL_HOPE_REQUIRED` |
| Day-14 supervisory fallback | `SNS_INTERNAL_WORKFLOW` |
| Day-28 supervisory fallback | `SNS_INTERNAL_WORKFLOW` |
| SFV relationship to HOPE Admission/HUV findings | `OFFICIAL_HOPE_REQUIRED` |
| Hidden map until RNICA finalization | `SNS_INTERNAL_WORKFLOW` |
| HOPE submission through iQIES | `OFFICIAL_HOPE_REQUIRED` |

## Appendix A: Full Authority Classification Table

The full authority classification table, controlling sources, and source
priority order have moved to a dedicated document:
[`RNICA_AUTHORITY_MATRIX.md`](./RNICA_AUTHORITY_MATRIX.md). Refer to that
document as the single source of truth for per-topic authority
classification; this document's §3 legend and narrative sections remain
authoritative for scope and rule explanation.

## Current Project Status

- Discovery: `AUTHORIZED`
- Documentation: `AUTHORIZED`
- Workflow mapping: `AUTHORIZED`
- Implementation: `NOT_AUTHORIZED`
- Database changes: `NOT_AUTHORIZED`
- UI development: `NOT_AUTHORIZED`

## 16. Implementation Boundary

`NOT_AUTHORIZED`. This document is discovery/documentation only. No
application behavior, JSX, Tailwind, routes, APIs, migrations, schemas,
enums, or production data are introduced or implied by this document.
