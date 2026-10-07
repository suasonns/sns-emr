# RNICA Disaster Triage — Field Classification & Reuse Map

**Status:** Requirements traceability (Exact Next Action, items 5–6). No UI, field, validation, or
schema change made. Every source-field claim below was verified directly in
`sns-emr-frontend/src/components/RNICA.jsx` by line reference — nothing is inferred from memory.

**Governing rule applied throughout:** *everything with duplication risk reuses the existing
authoritative field instead of collecting it again.* Every row below is classified as one of:
**Existing authoritative** (already exists, exact meaning, reuse as-is) · **Existing comparable**
(exists, adjacent meaning, reuse with mapping/derivation, do not duplicate) · **Derived display**
(computed from other existing fields, not stored again) · **Missing field** (no existing source;
genuinely new) · **Policy-specific configuration** (agency-level setting, not a patient field).

---

## 0. Major finding: Disaster Triage already exists

`safety` module, "Disaster Triage" card (`RNICA.jsx:11217-11234`) already implements:

```
disasterLevel                    — radio, 3 options, exact Level 1/2/3 policy-plain-text wording
disasterLevelOneConditions       — checkboxGroup, exact 4 policy factors
disasterLevelTwoConditions       — checkboxGroup, same exact 4 policy factors
disasterLevelThreeConditions     — checkboxGroup, "Lives in facility with disaster support" /
                                    "Has alternate location and available helper to go to"
notes                            — shared Safety Notes textarea
```

This is **not a gap to fill from scratch** — it is a working v1 that already matches your Section 4
"Policy-Exact Core Decision Rules" almost verbatim (same 4 Level-1/2 factors, same Level-3
conditions). The work here is (a) confirming which of your Sections A–I additions should feed this
existing structure by reuse rather than new collection, and (b) identifying what is genuinely new
(suggested-level logic, safety-review layer, contact/escalation workflow, survey evidence view,
facility verification, agency policy profile).

---

## A. Triage Decision

| Requirement | Classification | Detail |
|---|---|---|
| Disaster Triage Terminology (Level/Category) | Missing field | Currently hard-coded as "Level" in the option labels (`RNICA.jsx:11218`). Becoming agency-configurable requires a new agency-policy-profile setting (Section 13), not a per-patient field. |
| Disaster Triage Classification (I/II/III value) | **Existing authoritative** | `disasterLevel` (`RNICA.jsx:11218`) — reuse, do not create a second level field. |
| System-Suggested Category | Missing field | No suggested/derived level exists today — `disasterLevel` is entered directly by the nurse with no computed suggestion shown alongside it. This is new logic, not a new stored field (see Section 8 below). |
| Staff-Confirmed Category | **Existing authoritative** | Same `disasterLevel` field serves this role once suggestion logic exists — the nurse's saved value already *is* the confirmed category. No second "confirmed" field needed. |
| Override Used / Override Rationale | Missing field | No mechanism today to distinguish "matches suggestion" from "overridden," and no rationale field. Needed once suggested-category logic exists. |
| Assessment Date and Time / Assessed By / Assessor Role | **Existing comparable** | RNICA's visit-level metadata (visit date/time, assigned staff/discipline, already shown on every RNICA screen per the Screen Authority Matrix) covers this generically. Reuse the assessment's own timestamp/author rather than a Disaster-Triage-specific duplicate, unless a per-reassessment audit trail requires a dedicated log (see Section 12/17-item-10 below — that log is new, but should reference the existing visit record, not re-capture assessor identity). |
| Last Verified / Next Review Due | Missing field | No reassessment-due tracking exists for this card today. |

## B. Policy Classification Factors (the four factors)

| Policy factor | Classification | Detail |
|---|---|---|
| Confined to bed or chair? | **Existing comparable** | Currently entered as a raw checkbox item *inside* `disasterLevelOneConditions`/`TwoConditions` (`RNICA.jsx:11221,11225`) — i.e., it is already collected as a triage-specific checkbox, not yet harvested from `mobility.ambulatoryStatus = "Bedbound"` (Musculoskeletal, `RNICA.jsx:11064`) or `gait = "Unable"` (`RNICA.jsx:11060`). Per the reuse rule, this should become a **harvested/derived** display sourced from Musculoskeletal, with the existing checkbox becoming a confirmation of currency rather than independent re-entry — this is a genuine current duplication risk your directive already anticipated in the requirements matrix ("Harvest mobility or functional status"). |
| Lives above ground floor? | Missing field | No floor-level field exists anywhere in RNICA (`livingSituation.*` covers site-of-service/admitted-from/living-arrangement/availability-of-assistance — HOPE A0215/A1805/A1905/A1910 — but not building floor or elevator status). Also currently double-collected as a raw checkbox inside the two condition groups. Needs one new authoritative field (Residence Floor / Elevator Available), with the existing checkbox becoming derived from it once built. |
| Dependent on walker or cane? | **Existing comparable** | Already derivable from Musculoskeletal's `assistiveDevices` (includes "Walker", "Cane" — `RNICA.jsx:11061`) or `mobility.transferAbility`. Currently also independently re-entered as a raw checkbox in the Disaster Triage card — same duplication pattern as above. |
| Requires electricity for medical equipment? | **Existing comparable, partially** | DME items exist (`dmeItems`, `DME_ITEM_LIST` — `RNICA.jsx:283-286` — includes Oxygen concentrator, Suction machine, Nebulizer, Hoyer lift, Bed) and Respiratory's `oxygenTherapy.inUse` exists, but **no field marks which specific item is electricity-dependent** — this is a real, narrow missing-field gap (a per-DME-item or per-oxygen-source "requires electricity" flag), not a full new module. |

**Reuse conclusion for Section B:** three of the four factors already have an authoritative or
comparable source elsewhere in RNICA; today's Disaster Triage card re-collects all four as
independent checkboxes instead of harvesting them. This is the single highest-value, lowest-risk
fix available — it removes duplicate charting without touching the policy thresholds at all.

## C. Residence and Setting

| Requirement | Classification | Detail |
|---|---|---|
| Current Care Setting | **Existing authoritative** | `livingSituation.siteOfService` (HOPE A0215, `RNICA.jsx:9411-9418`) already enumerates Patient's Home, Assisted Living, Nursing/LTC/NF, SNF, Inpatient Hospital, Inpatient Hospice, LTCH, Inpatient Psychiatric, Hospice Home Care — reuse directly, do not create a second setting field. |
| Patient Lives With | **Existing authoritative** | `livingSituation.livingArrangement` (HOPE A1905, `RNICA.jsx:9439-9445`) — Alone / With others / Congregate home / Inpatient facility / No permanent home. Reuse directly. |
| Residence Floor | Missing field | Confirmed absent everywhere in the codebase. |
| Elevator Required / Available During Power Failure | Missing field | Confirmed absent. |
| Accessible Exit Available | Missing field | Confirmed absent. |

## D. Mobility Detail

| Requirement | Classification | Detail |
|---|---|---|
| Patient Mobility | **Existing authoritative** | `mobility.ambulatoryStatus` (Musculoskeletal, `RNICA.jsx:11064` — Independent/Supervised/Assisted/Dependent/Bedbound) — reuse directly; do not re-collect as a separate Disaster-Triage-specific mobility field. |
| Transfer Ability | **Existing authoritative** | `mobility.transferAbility` (`RNICA.jsx:11066` — Independent/Standby/1-person/2-person/Hoyer lift) — reuse directly. |
| Can Patient Self-Evacuate? | Missing field | No existing field captures self-evacuation capability specifically — `transferAbility`/`ambulatoryStatus` are close but not identical in meaning (a patient can be "2-person assist" for transfers yet the household may still have no plan for *evacuation* specifically). Recommend deriving a default from `transferAbility`/`ambulatoryStatus` and letting the nurse confirm/override only the evacuation-specific question, rather than a fully independent field. |
| Can Patient Use Stairs? | Missing field | No existing field. |

## E. Oxygen and Respiratory Support

| Requirement | Classification | Detail |
|---|---|---|
| Oxygen Use / Source / Flow Rate | **Existing authoritative** | Respiratory's `oxygenTherapy.inUse/.type/.litersPerMinute/.deliveryMode` (per this session's own Field Inventory) — reuse directly, do not re-collect inside Disaster Triage. |
| Portable Oxygen Available / Estimated Portable Supply Duration | Missing field | No existing field distinguishes portable vs. stationary oxygen supply or estimates runtime. |
| Ventilator or Respiratory-Support Device Present | **Existing authoritative** | Respiratory's ventilator/tracheostomy fields exist per the inventory (though flagged in Unresolved Decisions as lacking a clean "present" trigger — the same open item applies here; reuse once resolved, do not build a second ventilator-presence field for Disaster Triage). |
| Suction Machine Present | **Existing authoritative** | Already a `dmeItems` entry ("Suction machine," `RNICA.jsx:285`) — reuse the existing DME status rather than re-asking. |
| Respiratory Equipment Requires Electricity | Missing field | Same gap as Section B's fourth factor — one new flag, not a new module. |

## F. Essential DME

| Requirement | Classification | Detail |
|---|---|---|
| Essential DME list (bed, concentrator, ventilator, suction, nebulizer, lift, wheelchair, etc.) | **Existing authoritative** | `DME_ITEM_LIST`/`dmeItems` (`RNICA.jsx:283-286`) already contains Bed, Oxygen concentrator, Suction machine, Nebulizer, Hoyer lift, Wheelchair, and more, each with a Has/Needs/Ordered/Delivered/Declined/N/A status. Feeding pump and ventilator specifically are not in this list (feeding is tracked in GI's `feedingTube.*`, ventilator in Respiratory) — reuse those, do not duplicate. |
| Equipment Clinically Essential During Disruption | Missing field | No existing flag marks *which* of a patient's DME items are disaster-critical vs. routine comfort items — this is a real new flag, ideally attached per-item to the existing `dmeItems` array rather than a separate list. |
| Equipment Requires Electricity | Missing field | Same electricity-dependence gap as B/E above — one flag, reusable across all three requirement sections rather than three separate new fields. |
| Manual Alternative Available / Backup Power Available / Backup Power Function Verified | Missing field | Confirmed absent. |
| DME Vendor Emergency Support Confirmed / DME Vendor Contact | **Existing comparable** | Vendor management already exists at the ordering level (`vendors.ts`, `VendorManagement.jsx` per this session's earlier search) — reuse vendor contact data rather than re-entering it inside the nursing assessment; only the "emergency support confirmed" verification flag itself is new. |

## G. Assistance and Support (Primary Caregiver)

| Requirement | Classification | Detail |
|---|---|---|
| Primary Caregiver Present / Availability | **Existing authoritative** | `livingSituation.availabilityOfAssistance` (HOPE A1910, `RNICA.jsx:9443-9445` — 24/7 available / Daytime only / Nighttime only / Limited / None) already captures availability at the household level — reuse this as the primary source; do not create a second, differently-worded availability field for Disaster Triage. |
| Primary Caregiver Mobility / Can Transfer / Can Evacuate / Can Operate Essential DME / Can Drive | Missing field | Confirmed absent everywhere. RNICA's existing `pcg.caregiverEvaluation.overallCapability` (1-5 scale, `RNICA.jsx:~9393-9398`) and `.supportSystemAdequacy` (Adequate/Inadequate/Needs reinforcement) capture *general* caregiver capability, but not the specific physical-capability facts (mobility, transfer, evacuation, equipment competency, driving) your directive correctly insists must be recorded as actual facts rather than inferred from age. These are genuinely new, narrow fields — but they should live in (or reference) the existing caregiver evaluation structure rather than becoming a wholly separate "Disaster Triage caregiver" section, to avoid creating two caregiver-capability records that can drift apart. |
| Accessible Vehicle Available | Missing field | Confirmed absent. |

## H. Backup Support

| Requirement | Classification | Detail |
|---|---|---|
| Backup Caregiver Available / Relationship / Contact / Arrival Availability | Missing field | Confirmed absent — no backup-caregiver concept exists anywhere in RNICA today (verified: no match for "backup caregiver" in the entire frontend). This is the single largest genuinely-new data concept in the whole directive. |
| Patient Has a Place to Go / Alternate Location Type / Confirmed | **Existing authoritative (partial)** | `disasterLevelThreeConditions` already includes "Has alternate location and available helper to go to" (`RNICA.jsx:11229-11230`) as a single combined checkbox. Your directive wants "place to go" and "person able to help" tracked as two separate, independently verifiable facts (Section 8's Level-3 logic requires *both* confirmed, not one combined checkbox) — this is a real, worthwhile split of an existing field, not a brand-new field from nothing. |
| Person Available to Help / Helper Can Safely Meet Needs | Missing field (see above) | Same combined-checkbox issue — "capability" of the helper is not captured at all today, only presence. |
| Transportation Available | Missing field | Confirmed absent. |
| Communication Backup Available | Missing field | Confirmed absent. |

## I. Facility Disaster Support

| Requirement | Classification | Detail |
|---|---|---|
| Facility Emergency Program Confirmed | **Existing comparable (partial)** | `disasterLevelThreeConditions` includes "Lives in facility with disaster support" (`RNICA.jsx:11228`) as a single yes/no checkbox — your directive correctly requires this to become a *verified* fact (contact + verification date), not a self-reported checkbox alone. Reuse the existing checkbox as the entry point/trigger for the new verification fields, rather than replacing it. |
| Facility Emergency Contact / Verification Date and Time | Missing field | Confirmed absent. |
| Facility Can Maintain Oxygen / Essential DME / Backup Power / Staffing | Missing field | Confirmed absent. |
| Facility Evacuation Status / Evacuation Destination Confirmed | Missing field | Confirmed absent. |
| Patient-Specific Gap Identified | Missing field | Confirmed absent — this is the field that operationalizes your Section 9 "Necessary Safety Exception" for facility-based patients (Test 7 in your directive). |

---

## Summary: What Is Genuinely New vs. What Must Be Reused

**Already exists and must be reused, not duplicated (do this first — zero new fields, pure
de-duplication):**
- Care setting → `livingSituation.siteOfService` (A0215)
- Living arrangement → `livingSituation.livingArrangement` (A1905)
- Caregiver availability → `livingSituation.availabilityOfAssistance` (A1910)
- Mobility/ambulatory status → `mobility.ambulatoryStatus`, `mobility.transferAbility` (Musculoskeletal)
- Assistive devices (walker/cane) → `assistiveDevices` (Musculoskeletal)
- Bed/chair confinement → derivable from `mobility.ambulatoryStatus = "Bedbound"` / `gait = "Unable"`
- Oxygen use/type/flow → `oxygenTherapy.*` (Respiratory)
- DME inventory (bed, concentrator, suction, nebulizer, Hoyer lift, wheelchair) → `dmeItems`
- General caregiver capability score → `pcg.caregiverEvaluation.overallCapability`/`.supportSystemAdequacy`
- The 4-factor Level 1/2 checkboxes and the combined Level-3 checkbox already in `safety.disasterLevel*`

**Genuinely new (no existing source anywhere in the repository) — the real gap list:**
1. Residence floor number + elevator status (Section C)
2. Per-DME-item / per-oxygen-source "requires electricity" flag (Sections B/E/F — one flag, reused across all three, not three separate flags)
3. Backup caregiver identity/relationship/contact/capability (Section H) — the largest single gap
4. Splitting "place to go" and "person able to help" into two independently-verifiable facts, each with a capability sub-field (Section H)
5. Facility verification detail: contact, verification date, oxygen/DME/power/staffing/evacuation confirmation, patient-specific-gap flag (Section I)
6. Suggested-vs-confirmed category distinction, override + rationale, last-verified/next-review-due (Section A)
7. Contact-verification/escalation event log, emergency-event activation workflow, survey evidence view (Sections 6/11/12/17 of your directive — genuinely new workflow, not fields)
8. Agency policy profile (terminology, policy name/number/version, thresholds, accreditation context) — configuration, not a patient field (Section 13)

---

*No code, schema, or UI change was made to produce this classification. This satisfies Exact Next
Action items 5 and 6. Items 2–3 (policy crosswalk extraction/verification against the actual Love &
Faith/Care Me/Global Home policy documents) are explicitly outside what can be done from the
repository alone and remain your/the agency's action, not this analysis's.*
