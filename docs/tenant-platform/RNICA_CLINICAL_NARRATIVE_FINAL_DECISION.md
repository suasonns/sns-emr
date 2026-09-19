# RNICA Clinical Narrative — Final Decision

**STATUS: LOCKED PRODUCT DECISION**
**CODE: BLOCKED — SCHEMA: BLOCKED — MIGRATIONS: BLOCKED**

This document is the final, authoritative product decision on the RNICA
Clinical Narrative, superseding the framing of all prior narrative
documents in this directory. It does not authorize any implementation.

---

## 1. Accepted Findings

1. `diagnoses.clinicalNarrative` is currently unreachable dead UI code.
2. The Diagnosis card is not rendered because `SECTION_CONFIGS.diagnoses.cards`
   has no `customRenderer` entry for `clinicalNarrative`.
3. Also currently invisible to nurses: Disease Trajectory, RN Addendum,
   Clinician Clarification, and "Build Draft from Documented Findings."
4. Existing records may contain `diagnoses.clinicalNarrative` with
   `clinicalNarrativeReviewed=false` and become un-lockable with no visible
   UI path for correction.
5. No external CMS or HOPE requirement was found requiring a Clinical
   Narrative in the Diagnosis section.
6. `diagnoses.clinicalNarrative` and its reviewed-state behavior are
   internal product rules.
7. `finalization.clinicalNarrative` is already the canonical Clinical
   Narrative used by `RN_ICA_REQUIRED_FIELD_GROUPS`.
8. `finalization.clinicalNarrative` is the correct whole-chart synthesis,
   attestation, and AI visit-recording target.

---

## 2. Locked Product Decision

Do not restore `diagnoses.clinicalNarrative` to the Diagnosis user
interface. Do not preserve it as a second active nurse-authored narrative.
Do not present two Clinical Narrative fields in Figma.

The redesigned RNICA will contain **one** authoritative nurse-facing
Clinical Narrative: `finalization.clinicalNarrative`, located in
**Finalization**. The nurse completes the assessment first, then writes or
reviews the whole-chart Clinical Narrative before attestation and
signature.

---

## 3. Diagnosis Workspace — Retained Content and Required Classification

The Diagnosis workspace must contain only diagnosis-specific content whose
purpose is separately validated. The following items are retained for
redesign review (not automatically restored):

- Primary Diagnosis
- Secondary Diagnoses
- Comorbidities
- HOPE Diagnosis Category
- Terminal Prognosis
- Disease Trajectory
- LCD Supporting Evidence
- LCD Eligibility Narrative
- Recent Hospitalizations
- Recent Emergency Room Visits
- Utilization Notes
- RN Addendum
- Clinician Clarification

### Classification of Currently Invisible Diagnosis Items

| Item | Field | Currently Reachable? | Classification | Rationale |
|---|---|---|---|---|
| Disease Trajectory | `diagnoses.diseaseTrajectory` | No — dead card only | **REQUIRES CLINICAL REVIEW** | Structured categorical field (not free text). Currently the only input `rnica_intelligence.py:68` reads for disease-course context, but reads an always-empty value today since it can't be set. Wiring it live would activate a currently-inert AI input — clinical/product review should confirm the option set (`clinicalNarrativeBuilder.js:48-61`, including legacy value handling) still reflects desired disease-trajectory categories before it goes live. |
| RN Addendum | `diagnoses.rnAddendum` | No — dead card only | **REQUIRES CLINICAL REVIEW** | Free-text, pre-lock-only working field with no described purpose beyond its name and no backend consumer found. Whether this is still wanted, and what its intended scope is (vs. the removed diagnoses narrative), needs clinical/product definition before it is wired live — it is not self-evidently required or self-evidently redundant on current evidence. |
| Clinician Clarification | `diagnoses.clinicianClarification` | No — dead card only | **REQUIRES CLINICAL REVIEW** | Same evidence profile as RN Addendum: free-text, pre-lock-only, no backend consumer found, no documented purpose beyond its name. Needs the same clinical/product definition pass before being wired live. |
| "Build Draft from Documented Findings" | N/A (behavior, not a field) | No — dead, single call site | **FUTURE FORWARD-ONLY CORRECTION REQUIRED (repoint, not revive in place)** | Already directed by the rewiring decision (Section 4) to be repointed to `finalization.clinicalNarrative` rather than reintroduced in Diagnoses. Not classified in the five-value scale because its destination is already decided. |

No item above is classified **REQUIRED AND SHOULD BE WIRED**,
**USEFUL AND SHOULD BE WIRED**, **REDUNDANT**, or **LEGACY** at this time —
current repository evidence (no backend consumer, no compliance citation,
no documented business purpose beyond a field name) is insufficient to
assign any of those four classifications responsibly. All three data
fields are marked **REQUIRES CLINICAL REVIEW** pending the Owner/clinical
team defining their intended purpose. This is a discovery-evidence
limitation, not a recommendation to discard them.

The remaining retained items (Primary Diagnosis, Secondary Diagnoses,
Comorbidities, HOPE Diagnosis Category, Terminal Prognosis, LCD Supporting
Evidence, LCD Eligibility Narrative) are already live and reachable today
via existing cards (`RNICA.jsx:8890-8935`) and are unaffected by this
decision.

*Recent Hospitalizations, Recent Emergency Room Visits, and Utilization
Notes were not located as existing fields anywhere in `diagnoses.*` in this
repository under any name searched (see
`RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`, Part 0 footnote). They cannot be
classified against current code because no current implementation exists;
if intended, they are new fields, not a rewiring target, and are out of
scope for this decision.*

---

## 4. Rewiring Decision — FUTURE FORWARD-ONLY CORRECTION REQUIRED

Marked for future, separately authorized implementation planning:

1. Remove `diagnoses.clinicalNarrative` from the future active RNICA
   authoring workflow.
2. Remove or replace the redundant `diagnoses.clinicalNarrativeReviewed`
   workflow.
3. Repoint any legitimate "Build Draft from Documented Findings" behavior
   to `finalization.clinicalNarrative`.
4. Preserve `finalization.clinicalNarrative` as: the canonical Clinical
   Narrative; the whole-chart synthesis; the hard compliance-blocking
   narrative; the AI visit-recording insertion target; the
   pre-attestation narrative.
5. Preserve existing `diagnoses.clinicalNarrative` values as historical
   legacy data.
6. Preserve existing amendment references and audit history.
7. Do not overwrite `finalization.clinicalNarrative` with legacy diagnosis
   narrative content.
8. Do not automatically merge the two narratives.

---

## 5. Required Future-State Classification (Authoritative)

| Field | Current State | Future State | Data Handling | Dependency Handling |
|---|---|---|---|---|
| `diagnoses.clinicalNarrative` | Legacy/mistaken field with unreachable UI and residual dependencies | Not an active nurse-facing narrative | Historical preservation required | Forward-only rewiring required |
| `finalization.clinicalNarrative` | Existing Finalization Clinical Narrative | Sole authoritative nurse-facing RNICA Clinical Narrative | Retain | Preserve and receive approved draft/review functionality |

---

## 6. Figma Authority

Figma must show:
- **Diagnosis Workspace:** No Clinical Narrative field.
- **Finalization Workspace:** One Clinical Narrative field.

Figma must not show: "Clinical Diagnosis Narrative," a mid-assessment
Clinical Narrative, a duplicate whole-chart narrative, or separate "Final
Assessment," "Clinical Synthesis," and "Attestation" narrative inputs.
Those descriptions represent one field and one control:
`finalization.clinicalNarrative`.

---

## 7. Final Status

| | |
|---|---|
| Rewiring map | APPROVED AS DISCOVERY |
| Product decision | LOCKED |
| Authoritative Clinical Narrative | `finalization.clinicalNarrative` |
| Diagnosis Clinical Narrative | REMOVE FROM FUTURE ACTIVE EXPERIENCE |
| Historical data | PRESERVE |
| Current unreachable-lock defect | OPEN — see `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md` |
| Figma | MAY FOLLOW THIS CORRECTED AUTHORITY |
| Code | BLOCKED |
| Schema | BLOCKED |
| Migrations | BLOCKED |

No `alembic stamp`. No historical migration rewrite.

---

## Cross-References

- `docs/tenant-platform/RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`
- `docs/tenant-platform/RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`
- `docs/tenant-platform/RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`
