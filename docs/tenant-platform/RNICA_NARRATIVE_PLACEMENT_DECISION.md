# RNICA Narrative Placement — Locked Decision

**Status:** LOCKED DECISION
**Type:** Redesign requirement / documentation only
**Scope:** RNICA clinical/diagnosis narrative fields vs. the finalization narrative field
**No code, schema, migration, or field changes are authorized by this document.**

---

## 1. Locked Decision

> The final clinical narrative belongs near Finalization.
> Do NOT present the end-of-assessment synthesis narrative in the Diagnosis workspace.
> The nurse completes the chart first, then writes or reviews the final narrative.
> The nurse is never asked to synthesize the entire patient story before the remainder of the RNICA is completed.

This confirms and closes the question raised in the prior turn: `finalization.clinicalNarrative` is the **correctly placed** field. `diagnoses.clinicalNarrative` is the field whose **workspace framing** (label "Clinical narrative," presented mid-chart in Section 10) creates the confusion — not its underlying data or backend dependency, both of which must be preserved.

**Explicitly preserved (not removed, not merged):**
- `diagnoses.clinicalNarrative`
- `finalization.clinicalNarrative`

Both fields, both backend dependencies, and all current consumers remain exactly as documented in `RNICA_SECTION_BREAKDOWN.md`. This document only assigns each field's narrative role a distinct name so future redesign work (UI copy, card grouping, workspace labeling) cannot re-conflate them.

---

## 2. Narrative Inventory — Diagnosis Workspace

All three items live in the current Diagnoses section (`RNICA.jsx`, Section 10) and stay there. None move.

| Redesign Name | Actual Field | Type | Current UI Card | Purpose |
|---|---|---|---|---|
| **Disease Trajectory Narrative** | `diagnoses.diseaseTrajectory` | Categorical selection (radio), not free text | `ClinicalNarrativeCard` (`RNICA.jsx:2051-2055`) | Classifies expected disease course; contextual input the "Clinical Diagnosis Narrative" template draws from (`buildClinicalNarrative`, `RNICA.jsx:2027`). |
| **LCD Narrative** | `diagnoses.lcdEligibilityNarrative` | Free text | `LcdEligibilityCard` (`RNICA.jsx:1601-1993`) | Physician's LCD (Local Coverage Determination) eligibility-support narrative. Explicitly documented in code as "distinct field, distinct purpose" from clinical narrative (`RNICA.jsx:2004-2005`). Feeds backend finalization check `lcdBaseline` (`rnica_finalization_service.py:130-134`). |
| **Clinical Diagnosis Narrative** | `diagnoses.clinicalNarrative` | Free text | `ClinicalNarrativeCard` (`RNICA.jsx:2004-2150`) | RN's mid-assessment documented clinical findings + disease trajectory synthesis, tied to the Diagnoses section specifically. Has "Build Draft from Documented Findings" deterministic template button and a `clinicalNarrativeReviewed` checkbox. Feeds backend finalization check `narrativeReviewed` (`rnica_finalization_service.py:120-127`). |

## 3. Narrative Inventory — Finalize Workspace

One field currently fulfills all three conceptual roles below. No new fields are created by this document — these are three **roles**, not three new inputs.

| Redesign Name | Actual Field | Current Behavior | Purpose |
|---|---|---|---|
| **Final Assessment Narrative** | `finalization.clinicalNarrative` | Required textarea, Section "Finalization & Signature" (`RNICA.jsx:9699`) | The RN's whole-chart narrative, written/reviewed after all other sections are complete. |
| **Clinical Synthesis Narrative** | `finalization.clinicalNarrative` (same field) | Placeholder text: "Synthesize the completed whole-patient assessment findings, changes, interventions, response, risks, and plan." | The synthesis role of the same field — explicitly requires the rest of the chart to already be documented before it is written. |
| **Attestation Narrative** | `finalization.clinicalNarrative` (same field) | Hard client error if empty: "Clinical narrative is required before attestation" (`RNICA.jsx:1091-1092`) | The gating role — this is the text the clinician's signature (`clinicianSignature`, `signatureCertification`) attests to. |

Also auto-fillable (blank-only-write) from a visit recording transcript via `handleInsertAiNarrative` (`RNICA.jsx:9698-9720`) — this AI-assist path targets this same field and is unaffected by this naming decision.

---

## 4. Why the Two Fields Are Not the Same and Must Not Be Merged

| | Diagnosis Workspace: Clinical Diagnosis Narrative | Finalize Workspace: Final Assessment / Synthesis / Attestation Narrative |
|---|---|---|
| Field | `diagnoses.clinicalNarrative` | `finalization.clinicalNarrative` |
| When authored | Mid-assessment, immediately after diagnoses/disease trajectory are entered | After all 27 sections are complete |
| Scope | Diagnoses-section findings only | Whole-chart synthesis (all sections) |
| Backend gate | `narrativeReviewed` check (Lock) | Client-side hard error (attestation) |
| AI-assist target | None (deterministic template only) | Yes — visit-recording transcript auto-fill |
| Reviewed-state tracking | `clinicalNarrativeReviewed` boolean, resets on edit | None — always required fresh at attestation |

Merging them would either (a) force the nurse to write the whole-chart synthesis before the chart is complete — the exact anti-pattern this decision prohibits — or (b) silently drop the `narrativeReviewed` backend Lock check, since it reads `diagnoses.clinicalNarrative` specifically.

---

## 5. What This Decision Authorizes and Blocks

**Authorized (naming/documentation only):**
- Using the redesign names above in future Figma, copy, and planning artifacts.
- Repositioning the *visual card* for `diagnoses.clinicalNarrative` within the Diagnosis workspace layout (e.g., de-emphasizing it, relabeling its UI copy to "Clinical Diagnosis Narrative") without changing its field path.

**Still blocked (requires separate Implementation Authorization):**
- Any code, schema, or component change.
- Removing, renaming, or merging either backing field (`diagnoses.clinicalNarrative`, `finalization.clinicalNarrative`).
- Changing the backend `narrativeReviewed` or `lcdBaseline` finalization checks.
- Moving the Finalization narrative UI earlier in the workspace order.

---

## 6. Cross-References

- `docs/tenant-platform/RNICA_SECTION_BREAKDOWN.md` — full field inventory for Diagnoses (Section 10) and Finalization (Section 27).
- `docs/tenant-platform/RNICA_SYSTEM_DEPENDENCY_MAP.md` — backend dependency trace for finalization checks.
- `docs/tenant-platform/RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` — governing redesign-protection rules this decision falls under.
