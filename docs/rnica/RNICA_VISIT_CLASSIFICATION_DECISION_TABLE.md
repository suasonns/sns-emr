# RNICA Visit Classification Decision Table

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.

## 1. Purpose

Define deterministic discovery scenarios without creating application
logic. This table translates `RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md`
into a decision-table format for discovery review. No row authorizes
automatic classification — every row whose outcome is a "candidate" or
"prompt" still requires explicit RN/authorized-user confirmation before
finalization.

## 2. Input Fields

- Referral status
- Election complete
- Patient admitted
- Admission effective date
- Visit service date
- Days after election
- Days after admission
- Authenticated discipline
- Assigned discipline
- Initial Assessment status
- Comprehensive Assessment package status
- Existing HOPE Admission
- Existing HUV1
- Existing HUV2
- SFV applicability
- Supervisory visit type
- Recertification due
- RNICA finalization status

## 3. Decision Table

| Scenario | Required Inputs | Suggested Classification | Alternatives | Blocking Conditions | Required Evidence | Authority |
| --- | --- | --- | --- | --- | --- | --- |
| Referral received, election not complete | Referral status = received; Election complete = false | No classification (no clock started) | n/a | Election not complete | Referral record | `SNS_INTERNAL_WORKFLOW` |
| Election complete, Initial Assessment pending | Election complete = true; Initial Assessment status = pending | Initial Assessment (due = election + 48h) | n/a | 48h clock not yet elapsed | Election date/time | `FEDERAL_CMS_REQUIRED` |
| Initial Assessment overdue | Election complete = true; Initial Assessment status = pending; Days after election > 2 | Initial Assessment (overdue) | SNS referral-expiration review | None (still due) | Election date/time, elapsed-time calc | `FEDERAL_CMS_REQUIRED` + `SNS_INTERNAL_WORKFLOW` (expiration) |
| RNICA complete, MSW/SC ICA pending | Comprehensive Assessment package status = IN_PROGRESS | Package = IN_PROGRESS | n/a | Missing discipline contributions | Discipline completion records | `SNS_INTERNAL_WORKFLOW` |
| All required disciplines complete or exempted | Comprehensive Assessment package status inputs all COMPLETE/EXEMPTED_WITH_REASON | Package = COMPLETE | n/a | None | Discipline completion + exemption records | `SNS_INTERNAL_WORKFLOW` |
| RN visit Day 6-15, HUV1 absent | Days after election = 6-15; Existing HUV1 = false; Patient admitted = true | HUV1 candidate (pending confirmation) | Routine RN Visit, Updated Comprehensive Assessment | Requires confirmation before finalization | Visit service date, election date | `OFFICIAL_HOPE_REQUIRED` |
| Day-14 RN CHHA supervisory visit, HUV1 absent | Days after election = 14; Supervisory visit type = CHHA; Existing HUV1 = false | HUV1 review prompt (high priority) | Supervisory visit only (if declined, reason required) | Requires RN confirmation | Supervisory evidence (separate from HUV1 evidence) | `SNS_INTERNAL_WORKFLOW` |
| RN visit Day 16-30, HUV2 absent | Days after election = 16-30; Existing HUV2 = false; Patient admitted = true | HUV2 candidate (pending confirmation) | Routine RN Visit, Updated Comprehensive Assessment | Requires confirmation before finalization | Visit service date, election date | `OFFICIAL_HOPE_REQUIRED` |
| Day-28 RN CHHA/LVN supervisory visit, HUV2 absent | Days after election = 28; Supervisory visit type = CHHA or LVN; Existing HUV2 = false | HUV2 review prompt (high priority) | Supervisory visit only (if declined, reason required) | Requires RN confirmation | Supervisory evidence (separate from HUV2 evidence) | `SNS_INTERNAL_WORKFLOW` |
| HUV window closes with no qualifying visit | Days after election > 15 (HUV1) or > 30 (HUV2); Existing HUV1/HUV2 = false | Missed/late HUV | n/a | Compliance-review item required | Actual (non-backdated) visit date, if any | `OFFICIAL_HOPE_REQUIRED` |
| Moderate/severe symptom at HOPE Admission/HUV1/HUV2 | SFV applicability = true; no PENDING SFV requirement exists for patient+symptom | SFV required (due = trigger + 2 calendar days) | n/a | None | Trigger visit, symptom severity | `OFFICIAL_HOPE_REQUIRED` |
| SFV already PENDING for same patient+symptom | SFV applicability = true; existing PENDING requirement | Reuse existing SFV requirement | n/a | Duplicate prevented | Existing requirement record | `OFFICIAL_HOPE_REQUIRED` (repository-confirmed, `sfv_engine.py`) |
| Authenticated discipline ≠ assigned discipline | Authenticated discipline ≠ Assigned discipline | Blocked | n/a | Classification blocked until corrected/reassigned | Audit-log entry of attempted action | `SNS_INTERNAL_WORKFLOW` (authority control) |
| Recertification due | Recertification due = true | Recertification Assessment (suggested) | n/a | No automatic eligibility determination | Benefit period, due date, certification/narrative status, patient-specific evidence | `FEDERAL_CMS_REQUIRED` (timing) + `SNS_INTERNAL_WORKFLOW` (suggestion) |
| RNICA finalized | RNICA finalization status = FINALIZED; validation passed | Finalized; HOPE/SFV map published | n/a | None | Finalizer, timestamp, version, source IDs, statuses, warnings | `SNS_INTERNAL_WORKFLOW` + `OFFICIAL_HOPE_REQUIRED` (map content) |
| Change requested after finalization | RNICA finalization status = FINALIZED; change requested | Correction/Amendment/Addendum/Void/Replacement/Re-finalization | n/a | No silent overwrite | Authorized workflow record | `SNS_INTERNAL_WORKFLOW` |

## 4. Duplicate Prevention

- One active `PENDING` SFV requirement per patient+symptom
  (`REPOSITORY_CURRENT_STATE`, confirmed in `sfv_engine.py`).
- One HUV1 record and one HUV2 record per election episode (target rule;
  code enforcement status tracked in `RNICA_HOPE_SOURCE_VALIDATION_GAPS.md`).
- No re-creation of a completed Initial Comprehensive Assessment package.

## 5. Missed-Window Handling

- Preserve the actual visit date; never backdate.
- Do not silently mark a missed HUV1/HUV2 window as satisfied.
- Create a compliance-review item when a window is missed or at risk.
- Follow controlling HOPE guidance for submitting a late record.

## 6. Discipline Mismatch

- Authenticated discipline vs. assigned discipline conflict blocks final
  classification (see rules doc §9).
- Requires authorized correction or reassignment; attempted action is
  audit-logged.

### 6.1 LVN Encounters a Severe/Qualifying HOPE Symptom (`SNS_INTERNAL_WORKFLOW`)

If an LVN visit identifies a severe or otherwise qualifying HOPE symptom
finding, the workflow must:

- Display: "RN Assessment Review Required".
- Create a compliance-review item.
- Offer discipline-authorized next actions:
  - Request RN Visit
  - Request RN Assessment Review
  - Document Existing RN Review
- Preserve as immutable evidence:
  - LVN finding
  - Symptom source
  - Service date/time
  - Escalation decision
  - Reviewing RN
  - Review completion date/time
- Must **not** automatically create an SFV.
- Must **not** automatically classify the LVN visit as an SFV.
- Must **not** automatically mark an SFV complete.
- An RN must review the triggering symptom findings and determine whether:
  - SFV requirements apply.
  - Additional RN assessment is required.
  - Existing RN documentation already satisfies the review requirement.

This is an SNS operational escalation control, not a CMS HOPE or federal
requirement; it exists to route a discipline-restricted finding to RN
review without silently substituting LVN judgment for RN judgment.

## 7. Corrected-Date Recalculation

- If admission or election date is corrected after classification, all
  downstream due dates (Initial Assessment, Initial Comprehensive
  Assessment, HUV1/HUV2 windows) must be re-evaluated against the
  corrected date, not left stale (rules doc §15/§28 test scenario
  reference in `RNICA_CLASSIFICATION_TEST_SCENARIOS.md`).

## 8. Finalization Behavior

- See rules doc §11 (Finalization Gate). No row in this table authorizes
  automatic finalization; finalization always requires validation plus an
  explicit finalizing action.

## 9. Open Repository-Mapping Questions

See `RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` for the full gap register,
including HUV1/HUV2 window enforcement, election-vs-admission date
reconciliation (rules doc §5.4), and iQIES submission code paths.

## 10. Implementation Boundary

`NOT_AUTHORIZED`.
