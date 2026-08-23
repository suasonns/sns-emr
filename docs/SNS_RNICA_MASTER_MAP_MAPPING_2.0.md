# SNS RNICA Master Map Mapping 2.0 — Phase 2, Step 1

**STATUS: IN PROGRESS**

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## STEP RULE

This document maps the frozen current-state inventory
(`SNS_RNICA_FIELD_INVENTORY_1.0`, 28 sections) to the frozen target
architecture (`SNS_RNICA_MASTER_MAP_1.0`, 12 sections + global Admission
Action Center). It does not modify either frozen artifact. It does not
redesign fields. It records which current section(s) supply each target
section, and flags any current section whose fields split across more
than one target section as a **mapping conflict** for Gap Validation
(Phase 2, Step 3), not for Phase 1 reopening.

Source artifacts (both frozen, unmodified):
- `SNS_RNICA_FIELD_INVENTORY_1.0.md` — current 28 sections
- `SNS_RNICA_MASTER_MAP_1.0.md` — target 12 sections + Admission Action Center

---

## Mapping Table: Current Section → Target Section

| # | Current Section (Field Inventory) | Target Section (Master Map) | Split? | Notes |
|---|---|---|---|---|
| 1 | Patient Demographics | Section 1 — Patient & Encounter Snapshot | No | Direct match |
| 2 | Vitals | Section 5 — Head-To-Toe (multiple subcards) | **Yes** | Temperature/Pulse → Cardiovascular & Infection subcards; Respirations → Respiratory subcard; Blood Pressure → Cardiovascular subcard. No single target subcard owns "Vitals" as a whole — flagged as a mapping conflict |
| 3 | Pain Assessment | Section 2 — Immediate Needs & Symptom Triage | No | Direct match |
| 4 | Symptom Impact | Section 2 — Immediate Needs & Symptom Triage / Section 7 — HOPE & Symptom Follow-Up | **Yes** | Symptom Impact (J2051) is HOPE-coded; Master Map places general symptom triage in Section 2 but isolates HOPE J-items in Section 7 — flagged as a mapping conflict (which section owns `symptomImpact.*`?) |
| 5 | Diagnoses | Section 3 — Disease History & Clinical Trajectory / Section 6 — Disease Specific Criteria | **Yes** | Primary/Related Diagnoses, Hospitalizations → Section 3; HOPE Comorbidities list → also referenced by Section 6 (CHF, COPD, Cancer, etc. disease-specific criteria) |
| 6 | Performance Status | Section 4 — Functional & Performance Status | No | Direct match (PPS, KPS, FAST) |
| 7 | Neurological | Section 5 — Head-To-Toe (Neurological subcard) | No | Direct match |
| 8 | Cardiovascular | Section 5 — Head-To-Toe (Cardiovascular subcard) | No | Direct match |
| 9 | Respiratory | Section 5 — Head-To-Toe (Respiratory subcard) | No | Direct match |
| 10 | Infection | Section 5 — Head-To-Toe (Infection subcard) | No | Direct match |
| 11 | Gastrointestinal | Section 5 — Head-To-Toe (Gastrointestinal subcard) | No | Direct match |
| 12 | Nutrition | Section 5 — Head-To-Toe (Nutrition/Hydration subcard) | No | Direct match |
| 13 | Endocrine | Section 5 — Head-To-Toe (Endocrine subcard) | No | Direct match |
| 14 | Genitourinary | Section 5 — Head-To-Toe (Genitourinary subcard) | No | Direct match |
| 15 | Musculoskeletal | Section 5 — Head-To-Toe (Musculoskeletal subcard) | No | Direct match |
| 16 | Skin / Wounds | Section 5 — Head-To-Toe (Integumentary subcard) | No | Direct match; Master Map explicitly renames target subcard "Integumentary" to match current RNICA section name |
| 17 | Imminent Death | Section 7 — HOPE & Symptom Follow-Up | No | Direct match (J0050 source) |
| 18 | SFV | Section 7 — HOPE & Symptom Follow-Up | No | Direct match (J2052/J2053 source) |
| 19 | Safety | Section 9 — Safety, Environment, Equipment & Supplies | No | Direct match |
| 20 | Psychosocial | Section 8 — Whole Person & Caregiver Assessment | No | Direct match |
| 21 | Spiritual | Section 8 — Whole Person & Caregiver Assessment | No | Direct match (F3000 gap carried here) |
| 22 | Bereavement | Section 8 — Whole Person & Caregiver Assessment | No | Direct match |
| 23 | Personal Care | Section 8 — Whole Person & Caregiver Assessment | No | Direct match |
| 24 | Teaching Needs | Section 8 — Whole Person & Caregiver Assessment | No | Direct match |
| 25 | Admissions Order | Admission Action Center (global, non-numbered) | No | Direct match — current section maps to the global Action Center, not a numbered section |
| 26 | Hospice Orders Hub | Admission Action Center (global, non-numbered) / Section 9 (DME, Supply, Oxygen identification) | **Yes** | Order *creation* → Admission Action Center; DME/Supply *identification* → Section 9 per Master Map's "Section 9 does NOT create orders, only identifies needs" rule |
| 27 | Referrals | Admission Action Center (global, non-numbered) | No | Direct match |
| 28 | Finalization | Section 12 — Final Review & Finalization | No | Direct match |
| — | *(no current section)* | Section 10 — Clinical Narrative & Disease Trajectory | N/A | Target section has **no dedicated current-RNICA section** — current narrative content is the single computed `summaryText` in `DeclineTrackerCard`, not a section (see `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` §1) — carried forward as a gap, not resolved here |
| — | *(no current section)* | Section 11 — Master Plan of Care Review | N/A | Target section has **no dedicated current-RNICA section** — current RNICA has no Master POC roll-up view at all (see `SNS_POC_EVIDENCE_INVENTORY_1.0`) — carried forward as a gap, not resolved here |

---

## Mapping Conflicts Identified (for Phase 2, Step 3 — Gap Validation)

1. **Vitals section split** — current `vitals.*` fields have no single
   target-section owner; they distribute across three Section 5
   subcards (Cardiovascular, Respiratory, Infection) plus Nutrition
   (weight, if tracked under Vitals rather than Nutrition — see Field
   Inventory §2 vs. §12 for exact field location).
2. **Symptom Impact ownership** — `symptomImpact.*` (J2051) could map to
   either Section 2 (Immediate Needs & Symptom Triage) or Section 7
   (HOPE & Symptom Follow-Up); Master Map's HOPE-isolation principle
   (§7) argues for Section 7, but the content is symptom-triage in
   nature and overlaps Section 2's subject matter.
3. **Diagnoses/Comorbidities dual use** — `diagnoses.hopeComorbidities.*`
   fields are both a Section 3 (Disease History) input and a Section 6
   (Disease Specific Criteria) input; Master Map's Rule ("Section 6
   links to existing problems, does not duplicate") implies Section 3
   is the authoritative data owner and Section 6 only reads/links —
   this is consistent, not contradictory, but is recorded here for
   completeness.
4. **Hospice Orders Hub split** — order creation vs. need identification
   are explicitly separated by the Master Map's Section 9 rule
   ("does NOT create orders, only identifies needs"); current RNICA's
   single "Hospice Orders Hub" section does not make this distinction
   today.

No conflict above requires reopening a frozen Phase 1 deliverable —
each is a target-architecture allocation question, not a defect in the
current-state record.

## Status

**Phase 2, Step 1 (Master Map Mapping) complete.** All 28 current
sections are mapped to the 12 target sections / global Admission Action
Center, with 4 mapping conflicts flagged for Step 3 (Gap Validation).
Sections 10 and 11 of the target architecture have no current-RNICA
equivalent at all (already known gaps from Phase 1).

No code changes are authorized by this document. No frozen artifact was
modified.
