# RNICA Narrative Fields — Analysis

**Status:** DISCOVERY / ANALYSIS ONLY
**Scope:** `diagnoses.clinicalNarrative` and `finalization.clinicalNarrative`
**No placement change, redesign, rewiring, or code change is authorized or assumed by this document.**

This document supersedes any placement conclusion implied in
`RNICA_NARRATIVE_PLACEMENT_DECISION.md`'s framing. That prior document is not
retracted, but the analysis below is the evidence record it should be
weighed against — it treats both fields as separate, load-bearing fields
with separate consumers, and answers each of the 15 required questions on
that basis before any redesign decision is finalized.

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has since issued a locked product decision: `diagnoses.clinicalNarrative`
> was incorrectly placed and is not the future nurse-facing narrative;
> `finalization.clinicalNarrative` is the sole authoritative RNICA Clinical
> Narrative going forward. The per-field analysis below remains accurate as a
> record of the *current* repository state and its consumers, and is the
> evidence base the forward-only rewiring plan must work from.

---

## Field 1: `diagnoses.clinicalNarrative`

| # | Question | Answer |
|---|---|---|
| 1 | **Purpose** | RN-authored narrative of documented clinical findings and disease trajectory, scoped to the Diagnoses section. Has a deterministic "Build Draft from Documented Findings" template (`buildClinicalNarrative`) and a `clinicalNarrativeReviewed` reviewed-state checkbox that resets whenever the text changes. |
| 2 | **Current UI location** | `ClinicalNarrativeCard`, RNICA.jsx Section 10 ("Diagnoses"), lines 2004-2150. Rendered alongside the Disease Trajectory selector in the same card. |
| 3 | **Current backend consumers** | (a) `rnica_finalization_service.py:120-127` — `narrativeReviewed` Lock check. (b) `rnica_amendment.py:78` — amendment `section_reference` can point at `"diagnoses.clinicalNarrative"` for post-lock corrections. **Not** referenced in `clinical_note_validation_engine.py`'s `RN_ICA_REQUIRED_FIELD_GROUPS` (confirmed absent from that list). |
| 4 | **Validation dependencies** | Client warning only (not a hard error): `RNICA.jsx:1076-1077` — "Clinical narrative documented but not yet reviewed" if text is present but `clinicalNarrativeReviewed` is not `true`. |
| 5 | **HOPE dependencies** | None found. Not referenced by `rnica_hope_workflow_service.py`. |
| 6 | **POC dependencies** | None found. Not referenced by `rnica_poc_adapter.py`. |
| 7 | **Finalization dependencies** | Yes — feeds the `narrativeReviewed` check in `rnica_finalization_service.py`, one of the Layer-2 Lock-readiness checks. Logic: `narrative_ready = (not has_text(narrative)) or narrative_reviewed` — i.e., the check passes automatically if the field is empty, or if it has text and has been marked reviewed. |
| 8 | **Billing dependencies** | None. Consistent with the prior finding (`RNICA_SYSTEM_DEPENDENCY_MAP.md`) that RNICA has no billing-critical dependency. |
| 9 | **Audit dependencies** | Yes, indirectly — amendments referencing `"diagnoses.clinicalNarrative"` as `section_reference` are captured in the amendment audit trail (`test_rnica_amendments.py:190/203` uses `"section_10_clinical_narrative"` as the amendment section label). |
| 10 | **Lock dependencies** | Yes — via the `narrativeReviewed` Layer-2 finalization check described in #7. Note this check is a soft/self-satisfying gate: it only blocks Lock if text exists AND is unreviewed; an empty field never blocks. |
| 11 | **Clinically appropriate in current location?** | Debatable on the evidence. It is scoped to and physically adjacent to Diagnoses data (disease trajectory), which supports keeping it there as a diagnosis-specific note. However, its label ("Clinical Narrative") and its "reviewed" affordance visually resemble a finalization-style synthesis step, which is the source of confusion with `finalization.clinicalNarrative`. The field's *narrow scope* (diagnoses-only) is itself appropriate for its section; the *naming/labeling*, not the location, is what created ambiguity. |
| 12 | **Should the field remain?** | Yes. It is the sole backing field for the `narrativeReviewed` Lock check and the amendment `section_reference` target used in existing tests. Removing it silently changes Lock behavior (see prior turn's analysis) and orphans an amendment-audit reference pattern. |
| 13 | **Should it move visually?** | Not evaluated as a decision here (out of scope per "do not assume placement changes"). Evidence only: no backend dependency reads its UI position — only its data path (`formData.diagnoses.clinicalNarrative`) — so a visual move is technically decoupled from its backend wiring. |
| 14 | **Would moving it require backend rewiring?** | No, provided the field's data path (`diagnoses.clinicalNarrative`) is preserved. `rnica_finalization_service.py` and `rnica_amendment.py` both key off the data path, not the section's visual position in the RNICA workspace. A pure UI reposition (same data path, different card location) requires no backend change. Renaming or moving it to a different data path (e.g., under `finalization`) would require rewiring both consumers. |
| 15 | **Logically duplicated with the other field?** | No — different consumers, different scope (Diagnoses-only vs. whole-chart), different gating mechanism (soft Lock check vs. hard client error), different reviewed-state tracking (this field has one, the other does not). They share only a label ("Clinical Narrative") and a data type (free text), not a function. |

---

## Field 2: `finalization.clinicalNarrative`

| # | Question | Answer |
|---|---|---|
| 1 | **Purpose** | Whole-chart synthesis narrative written/reviewed at the end of the assessment, immediately preceding clinician attestation. Placeholder text explicitly instructs: "Synthesize the completed whole-patient assessment findings, changes, interventions, response, risks, and plan." |
| 2 | **Current UI location** | Finalization & Signature section, card "Clinical Narrative" (`RNICA.jsx:9699`), the last section of the 27-section RNICA workspace. |
| 3 | **Current backend consumers** | (a) `clinical_note_validation_engine.py:380-405` — listed as the canonical **"Clinical Narrative"** entry (section: "Finalization") in `RN_ICA_REQUIRED_FIELD_GROUPS`, a compliance-blocking field-group check run against `ClinicalNote` records whose discipline/note_type/form_key/assessment_type identify them as an RN ICA workflow. This is a **previously undocumented consumer** — not captured in `RNICA_SYSTEM_DEPENDENCY_MAP.md`. (b) `RNICA.jsx:9698-9720` — `handleInsertAiNarrative`, the blank-only-write AI visit-recording transcript auto-fill target. |
| 4 | **Validation dependencies** | Hard client error: `RNICA.jsx:1091-1092` — "Clinical narrative is required before attestation" if empty. This is a true blocking requirement, unlike the diagnoses field's soft warning. |
| 5 | **HOPE dependencies** | None found directly. Not referenced by `rnica_hope_workflow_service.py`. |
| 6 | **POC dependencies** | None found. Not referenced by `rnica_poc_adapter.py`. |
| 7 | **Finalization dependencies** | Yes, directly — it *is* a Finalization-section field, and its presence is one of the hard client-side gates before the RN can proceed to the signature/attestation checks (`signatureCertification`, `clinicianSignature`). |
| 8 | **Billing dependencies** | None found in backend billing services. |
| 9 | **Audit dependencies** | Yes, via `clinical_note_validation_engine.py`'s `_write_audit_log` / `audit_flags` / `_persist_validation_result_to_note` pipeline: a missing value produces `rn_ica_required_missing:finalization.clinicalNarrative` in `warnings`/`audit_flags`, persisted into `note.content["_validation"]` and surfaced via `get_note_validation_flags()`. |
| 10 | **Lock dependencies** | Yes, two independent gates: (a) the RNICA client hard-error attestation gate (#4), and (b) — when the assessment is represented as an RN-discipline `ClinicalNote` — the `compliance_blocking_items` produced by `_validate_required_rn_ica_sections()`, which downstream readiness surfaces treat as blocking (`finalization_allowed` flag in the persisted validation payload). |
| 11 | **Clinically appropriate in current location?** | Yes on the evidence: its own placeholder copy explicitly assumes the rest of the chart is "completed," and it sits immediately before attestation — the location matches its stated purpose. |
| 12 | **Should the field remain?** | Yes. It is required for attestation, is the AI transcript-draft insertion target, and is the field the separate `clinical_note_validation_engine.py` compliance layer treats as the canonical RN ICA "Clinical Narrative." Removing it would eliminate the only hard client gate for a synthesis narrative and orphan the AI-draft feature. |
| 13 | **Should it move visually?** | Not evaluated as a decision here. It is already in the Finalization workspace; no relocation evidence was requested for this field specifically. |
| 14 | **Would moving it require backend rewiring?** | If moved within the Finalization section, no. If moved out of Finalization into another section, yes — `clinical_note_validation_engine.py`'s field-group path (`finalization.clinicalNarrative`) and its "section" label ("Finalization") are asserted directly in code and would need updating to keep the compliance-blocker labeling accurate. |
| 15 | **Logically duplicated with the other field?** | No — see Field 1, #15. This field is also the one and only field referenced by the separate `clinical_note_validation_engine.py` compliance-blocker system; `diagnoses.clinicalNarrative` is not referenced there at all. |

---

## Cross-Field Findings (New Since Prior Documents)

1. **New consumer identified:** `clinical_note_validation_engine.py` (`RN_ICA_REQUIRED_FIELD_GROUPS`, lines 380-405) treats `finalization.clinicalNarrative` — not `diagnoses.clinicalNarrative` — as the canonical "Clinical Narrative" required field for RN ICA compliance blocking. This engine runs against `ClinicalNote` records (discipline=RN, note_type/form_key/assessment_type identifying an RN ICA workflow) and explicitly supports "newer RNICA.jsx payloads" (`_rn_ica_payload`, lines 1933-1957).
2. **Downstream consumers of that check:** `dashboard_service.py` (5 call sites) and `idg_engine.py` (3 call sites) both read the persisted validation payload via `get_note_validation_flags()` — meaning IDG readiness and dashboard alerting can be affected by whether `finalization.clinicalNarrative` is present, when the assessment flows through the `ClinicalNote` compliance path. This refines (does not contradict) the earlier "IDG only generic dashboard/history reads" finding from `RNICA_SYSTEM_DEPENDENCY_MAP.md` — the connection exists specifically through this compliance-blocking field-group mechanism, not a direct RNICA-to-IDG link.
3. **`diagnoses.lcdEligibilityNarrative`** and **`diagnoses.diseaseTrajectory`** are also members of the same `RN_ICA_REQUIRED_FIELD_GROUPS` list (labels "LCD Supporting Evidence" and "Disease Trajectory" respectively) — confirming these are the fields this particular compliance engine tracks for Diagnoses-section completeness, while `diagnoses.clinicalNarrative` itself is not tracked by it.
4. **No HOPE, POC, or billing dependency was found for either narrative field** in any backend service searched (`rnica_hope_workflow_service.py`, `rnica_poc_adapter.py`, and no billing service references either field name).

---

## Summary Table

| Question | `diagnoses.clinicalNarrative` | `finalization.clinicalNarrative` |
|---|---|---|
| Scope | Diagnoses-section only | Whole-chart synthesis |
| Gate type | Soft (self-satisfying if empty) | Hard client error + compliance blocker |
| Reviewed-state tracking | Yes (`clinicalNarrativeReviewed`) | No |
| AI-assist target | No | Yes (visit-recording transcript) |
| Compliance-engine tracked (`RN_ICA_REQUIRED_FIELD_GROUPS`) | No | Yes |
| Amendment `section_reference` target (existing test) | Yes | Not observed in tests reviewed |
| HOPE / POC / Billing dependency | None | None |
| Backend rewiring needed for a same-section visual move | No | No (only if moved out of Finalization) |
| Logically duplicated with the other | No | No |

---

## Cross-References

- `docs/tenant-platform/RNICA_SECTION_BREAKDOWN.md`
- `docs/tenant-platform/RNICA_SYSTEM_DEPENDENCY_MAP.md`
- `docs/tenant-platform/RNICA_NARRATIVE_PLACEMENT_DECISION.md` (prior turn's placement framing — to be reconciled with this analysis before any redesign proceeds)

**No redesign, move, or rewiring is authorized by this document.**
