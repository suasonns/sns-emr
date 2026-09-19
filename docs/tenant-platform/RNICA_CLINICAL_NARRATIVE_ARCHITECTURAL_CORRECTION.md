# RNICA Clinical Narrative — Architectural Correction

**STATUS: LOCKED PRODUCT DECISION**
**PLANNING AND DOCUMENTATION ONLY — NO CODE AUTHORIZED — NO SCHEMA AUTHORIZED — NO MIGRATION AUTHORIZED**

This document is the authoritative correction of record for the RNICA
Clinical Narrative. It overrides the placement framing in
`RNICA_NARRATIVE_PLACEMENT_DECISION.md` and the neutral-duplication framing
in `RNICA_NARRATIVE_FIELDS_ANALYSIS.md` wherever those documents implied
both narrative fields should remain as parallel, permanent, user-facing
inputs. Every other document listed in Section 6 has been annotated with a
pointer to this correction; none were rewritten wholesale, to preserve
their original discovery evidence.

---

## 1. Correction

The current repository contains two narrative fields:

- `diagnoses.clinicalNarrative`
- `finalization.clinicalNarrative`

**That existing implementation does not establish the correct future
architecture.** Placing a nurse-authored Clinical Narrative inside the
Diagnosis workspace was incorrect and should not have happened. The
authoritative RNICA Clinical Narrative belongs only in Finalization, after
the nurse completes the assessment.

---

## 2. Authoritative Future Design

**Diagnosis Workspace retains:**
- Primary Diagnosis
- Secondary Diagnoses
- Comorbidities
- HOPE Diagnosis Category
- Disease Trajectory
- LCD Supporting Evidence
- LCD Eligibility Narrative
- Recent Hospitalizations
- Recent Emergency Room Visits
- Utilization Notes
- RN Addendum
- Clinician Clarification

**Diagnosis Workspace must NOT present:**
- Clinical Narrative
- Clinical Diagnosis Narrative
- Final Assessment Narrative
- Whole-Chart Synthesis Narrative
- Attestation Narrative

`diagnoses.clinicalNarrative` is not to be renamed and kept visible, and not
to be visually repositioned elsewhere. The future design removes that
mistaken duplicate narrative experience entirely from the nurse-facing
workspace.

**Finalization Workspace retains one authoritative nurse-authored
narrative:** `finalization.clinicalNarrative`, user-facing label **"Clinical
Narrative,"** used to synthesize the completed whole-patient assessment,
summarize clinical findings, changes and decline, interventions and
response, risks, and the plan, and to support final clinician review and
attestation.

"Final Assessment Narrative," "Clinical Synthesis Narrative," and
"Attestation Narrative" are descriptive **roles** of this one field — not
separate fields or separate UI controls. This is the only Clinical
Narrative Figma should display.

---

## 3. Current Wiring That Must Be Corrected Later

Marked **REQUIRES FORWARD-ONLY IMPLEMENTATION CORRECTION** (not authorized
by this document):

Current code depends on `diagnoses.clinicalNarrative` and
`diagnoses.clinicalNarrativeReviewed` for the `narrativeReviewed`
Lock-readiness check (`rnica_finalization_service.py:120-127`), and also
uses `diagnoses.clinicalNarrative` as the target of "Build Draft from
Documented Findings," an amendment `section_reference` target
(`rnica_amendment.py:78`), and a mid-assessment reviewed-state workflow.

Future implementation planning must evaluate and define:
1. Repoint the `narrativeReviewed` readiness behavior to the authoritative
   finalization narrative workflow, or remove the redundant reviewed-state
   gate if final attestation already provides the required review control.
2. Repoint "Build Draft from Documented Findings" to
   `finalization.clinicalNarrative`.
3. Repoint future amendment references to the authoritative Finalization
   Clinical Narrative.
4. Preserve historical records containing `diagnoses.clinicalNarrative`.
5. Preserve existing amendment and audit history.
6. Prevent new RNICA records from requiring two nurse-authored clinical
   narratives.
7. Prevent silent loss of existing data during transition.
8. Use forward-only migration and repair.
9. Do not rewrite historical migrations.
10. Do not use `alembic stamp`.

---

## 4. Historical Data Rule

Do not delete historical `diagnoses.clinicalNarrative` content. Do not merge
historical content automatically. Do not overwrite
`finalization.clinicalNarrative`.

Implementation planning must define: historical read-only presentation,
provenance, reconciliation rules, conflict handling, audit preservation,
verification queries, and a forward-only transition.

Historical content may remain accessible as legacy clinical-narrative data,
but it must not remain the future nurse-facing authoritative Clinical
Narrative input.

---

## 5. Corrected Classification (Authoritative)

| Field | Current State | Future State | Implementation Impact |
|---|---|---|---|
| `diagnoses.clinicalNarrative` | Existing legacy/mistaken implementation | Not shown as an active nurse-authored narrative in the redesigned RNICA | Requires controlled rewiring and historical preservation |
| `finalization.clinicalNarrative` | Existing Finalization narrative | Authoritative RNICA Clinical Narrative | Retained and enhanced as the sole nurse-facing Clinical Narrative |

---

## 6. Documents Corrected by Reference

The following documents contain a standardized correction notice pointing
back to this document (added, not rewritten, to preserve their original
discovery evidence and dates):

- `RNICA_NARRATIVE_PLACEMENT_DECISION.md`
- `RNICA_NARRATIVE_FIELDS_ANALYSIS.md`
- `RNICA_SECTION_BREAKDOWN.md`
- `RNICA_SYSTEM_DEPENDENCY_MAP.md`
- `RNICA_UI_DEPENDENCY_MAP.md`
- `RNICA_REDESIGN_IMPACT_ANALYSIS.md`
- `RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md`
- `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`
- `RNICA_USABILITY_AND_AI_REVIEW.md`

---

## 7. Replaced Statement

**Rejected:**
> "Both narrative fields must remain visible because they have different
> current consumers."

**Replacing statement (authoritative):**
> Current code contains two narrative fields with different consumers, but
> the approved future RNICA experience has one authoritative nurse-authored
> Clinical Narrative in Finalization. Existing dependencies on
> `diagnoses.clinicalNarrative` must be corrected through a separately
> approved, forward-only implementation plan while preserving historical
> data and auditability.

---

## 8. Figma Authority

Figma must design a Diagnosis Workspace with **no Clinical Narrative
field**, and a Finalization Workspace with **one Clinical Narrative
field**. Figma must not preserve a duplicate field merely because current
code contains it. Figma defines the approved future experience; GitHub
later implements that approved experience through a separately authorized,
forward-only correction plan.

---

## 9. Final Status

| | |
|---|---|
| Product decision | LOCKED |
| Authoritative Clinical Narrative | `finalization.clinicalNarrative` |
| Diagnosis Workspace Clinical Narrative | REMOVE FROM FUTURE FIGMA EXPERIENCE |
| Current dependency rewiring | REQUIRED IN FUTURE IMPLEMENTATION PLAN |
| Historical data | PRESERVE |
| Figma redesign | MAY FOLLOW THIS CORRECTED AUTHORITY |
| Code | BLOCKED |
| Schema | BLOCKED |
| Migrations | BLOCKED |
