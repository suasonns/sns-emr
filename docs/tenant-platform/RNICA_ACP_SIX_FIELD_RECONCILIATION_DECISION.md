# RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md

**Status:** Approved target reconciliation. Documentation-only; does not
authorize application code, schema, or migration changes.
**Resolves:** `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` Discovery Item 7.

## 1. Current repository enforcement (discovery evidence, 3 fields)

Server hard-required at Lock (`RN_ICA_REQUIRED_FIELD_GROUPS`,
`backend/app/services/clinical_note_validation_engine.py:380-517`):

1. Code Status — `demographics.advancedCarePlanning.codeStatus`
2. Life-Sustaining Treatment Preference —
   `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference`
3. Hospitalization Preference —
   `demographics.advancedCarePlanning.hospitalizationPreference`

## 2. Approved target (6 fields — restated, not reduced)

1. CPR Preference Discussion Status
2. Code Status
3. Life-Sustaining Treatment Discussion Status
4. Life-Sustaining Treatment Preference
5. Hospitalization Preference Discussion Status
6. Hospitalization Preference

## 3. Confirmed: the three discussion-status fields already exist under different paths

Direct repository verification (`sns-emr-frontend/src/components/RNICA.jsx`)
confirms all three target discussion-status fields already exist in
`form_data`, under the following canonical paths, with an explicit HOPE
comment at the field-group declaration:

| Target value | Existing field path | HOPE item (per in-code comment) | Confirmed today |
|---|---|---|---|
| CPR Preference Discussion Status | `demographics.advancedCarePlanning.cprPreferenceAskedStatus` | F2000-A: "was the patient/responsible party asked?" (0 No / 1 Yes-discussed / 2 Yes-refused) | Field exists (`RNICA.jsx:406`); **not** in server hard-required list; client-side requiredness not confirmed |
| Code Status | `demographics.advancedCarePlanning.codeStatus` | — | Server hard-required today |
| Life-Sustaining Treatment Discussion Status | `demographics.advancedCarePlanning.lifeSustainingAskedStatus` | F2100-A | Field exists (`RNICA.jsx:406`); **confirmed client-required** (`RNICA.jsx:975-976`, error message cites "F2100"); **not** in server `RN_ICA_REQUIRED_FIELD_GROUPS` |
| Life-Sustaining Treatment Preference | `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | — | Server hard-required today |
| Hospitalization Preference Discussion Status | `demographics.advancedCarePlanning.hospitalizationAskedStatus` | F2200-A (inferred from the F2000/F2100/F2200 comment grouping at `RNICA.jsx:403`; not independently re-confirmed against official HOPE guidance this pass) | Field exists (`RNICA.jsx:406`); client/server requiredness not confirmed |
| Hospitalization Preference | `demographics.advancedCarePlanning.hospitalizationPreference` | — | Server hard-required today |

**Conclusion:** none of the six target fields requires new schema/storage.
All six already exist in `form_data` today. The gap is **validation-rule
parity**, not field creation.

## 4. Required labeling before implementation

Per the handoff instruction, every field must be labeled as an official
HOPE requirement or an SNS internal workflow requirement — do not describe
an SNS-only requirement as CMS-required.

- Code Status, Life-Sustaining Treatment Preference, Hospitalization
  Preference: labeled here as **official HOPE requirement candidates**
  (F2000/F2100/F2200 family), pending independent confirmation against
  current official CMS HOPE guidance — `[IMPLEMENTATION DISCOVERY
  REQUIRED]`. The in-code comments assert the HOPE linkage; this has not
  been independently cross-checked against the CMS HOPE manual/guidance
  document itself in this pass.
- CPR/Life-Sustaining/Hospitalization Discussion Status (the "-A"
  sub-items): same HOPE family per the in-code comment
  (`RNICA.jsx:403`), same caveat applies.
- No field in this set is currently labeled or evidenced as an SNS-only
  internal workflow requirement; if any of the six turn out not to map to
  an official HOPE item, they must be relabeled as SNS-internal before
  implementation, not silently treated as CMS-required.

## 5. Response-set integrity requirement

The existing "-AskedStatus" fields use a 3-value response set (`0 No / 1
Yes-discussed / 2 Yes-refused`, confirmed at `RNICA.jsx:8172,8179,8187` and
the F2000/F2100/F2200-A comment). Per the handoff instruction, distinct
states for **missing, not asked, declined, unable to respond, and
unknown** must be preserved where supported by controlling
specifications. The current 3-value set does not appear to distinguish
"unable to respond" from "declined" — `[IMPLEMENTATION DISCOVERY
REQUIRED]`: confirm whether the controlling HOPE response set has more
than 3 values and whether the current field's response set already
matches it exactly, before any validation-rule change is written.

## 6. Do not infer preferences from discussion status

A "Yes-discussed" (`1`) value on `cprPreferenceAskedStatus` /
`lifeSustainingAskedStatus` / `hospitalizationAskedStatus` must never be
used to infer or auto-populate the corresponding Preference field
(`codeStatus` / `lifeSustainingTreatmentPreference` /
`hospitalizationPreference`). No such inference logic was found in
`RNICA.jsx` in this pass — confirmed absent, which is the compliant state;
implementation must not introduce it.

## 7. Client/server validation parity requirement

- Confirmed today: `lifeSustainingAskedStatus` is enforced client-side
  (`RNICA.jsx:975-976`) but **not** in the server
  `RN_ICA_REQUIRED_FIELD_GROUPS` list. This is an existing client/server
  parity gap for one of the six target fields, independent of the
  3-vs-6-field question.
- `cprPreferenceAskedStatus` and `hospitalizationAskedStatus` have no
  confirmed client-side requiredness check found in this pass —
  `[IMPLEMENTATION DISCOVERY REQUIRED]`.
- Target state: client and server validation must enforce the same
  applicable values for all six fields (per handoff instruction). A truly
  missing applicable value blocks Lock. A permitted documented response
  (declined / unable to respond, once confirmed to exist per §5) must not
  be treated as missing.

## 8. Historical-record handling

- Existing signed or locked records must not be rewritten to retroactively
  require the three newly-added discussion-status fields.
- The six-field target must be applied prospectively only, through an
  approved release rule (e.g. effective-date gate on new assessments, not
  a backfill of historical ones).
- A forward-only migration is to be used **only if** repository validation
  proves new storage is required — per §3 above, no new storage is
  currently believed necessary, since all six fields already exist in
  `form_data`. This must be re-confirmed at implementation time, not
  assumed permanently true, since `form_data` schema could change before
  the ACP increment (Increment 9) is built.

## 9. Required decision before Increment 9 (ACP & Goals of Care) begins

1. Confirm the HOPE-vs-SNS-internal label for all six fields against
   current official CMS HOPE guidance (§4).
2. Confirm the exact controlling response-set values (§5) and whether the
   current 3-value set already satisfies them.
3. Confirm client-side requiredness status for all six fields (§7),
   including the two not yet checked.
4. Approve the prospective-only release rule (§8) before any server
   validation change ships.

Until items 1-4 are resolved, Increment 9 in
`RNICA_PHASED_IMPLEMENTATION_PLAN.md` remains blocked, consistent with
that document's cross-increment blocker table.
