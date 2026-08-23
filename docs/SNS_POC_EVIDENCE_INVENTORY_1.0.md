# SNS POC Evidence Inventory 1.0 — Phase 1, Deliverable 8

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This document records the current, as-implemented linkage (or absence
of linkage) between RNICA assessment findings, HOPE-derived elements,
and Plan of Care (POC) creation. It does not modify any prior frozen
deliverable and does not propose a POC evidence design.

Source of truth: `backend/app/services/poc_engine.py`,
`poc_generation_service.py`, `poc_compiler_rn_mapper.py` (searched for
any reference to `rnica`/`RnicaAssessment`/`form_data` — none found);
`RNICA.jsx` `finalization.pocGenerationCompleted` /
`finalization.pocEntries` fields; `SNS_RNICA_SECTION_INVENTORY_1.0`
Cross-Cutting Gaps item #6.

## Key finding

**No RNICA field or HOPE-derived value is programmatically linked to
Problem/Goal/Intervention creation in the current codebase.** A direct
search of every POC-related service file
(`poc_engine.py`, `poc_generation_service.py`, `poc_compiler_rn_mapper.py`)
for any reference to RNICA (`rnica`, `RnicaAssessment`, `form_data`)
returns **zero matches**. The only place RNICA and POC intersect in the
UI is the manual checkbox `finalization.pocGenerationCompleted`
(validated as a warning only, per `SNS_RNICA_VALIDATION_INVENTORY_1.0`)
and a `finalization.pocEntries` field referenced in
`SNS_RNICA_SECTION_INVENTORY_1.0`'s Cross-Cutting Gaps item #6, which
notes: *"The relationship between RNICA-local POC entries and the
authoritative POC engine ... has no explicit sync call in any RNICA
endpoint. None found in codebase."*

Consequently, the requested Problem → Assessment Evidence → Supporting
Findings → Goal Linkage → Intervention Linkage → Narrative Linkage →
Traceability chain **cannot be populated from real code today** — there
is no automated evidence-to-problem mapping to inventory. This document
records that absence explicitly, field by field, rather than describing
a linkage that does not exist.

## Traceability chain (as implemented)

| Chain step | Current implementation | Status |
|---|---|---|
| Problem | No RNICA field or engine emits a "Problem" record | **Missing** |
| → Assessment Evidence | RNICA findings exist as raw `form_data` values only; not tagged as "evidence" for any Problem | **Missing** (findings exist, but not linked) |
| → Supporting Findings | `get_rnica_intelligence()` (`SNS_RNICA_API_MAPPING_1.0` §1.6) produces `findings`/`evidence` text, explicitly labeled `"mode": "recommendation_only"` — it is a read-only advisory summary, not a POC-feeding evidence record | Read-only, non-authoritative, not linked to POC |
| → Goal Linkage | No code path connects any RNICA field or intelligence finding to a POC Goal | **Missing** |
| → Intervention Linkage | No code path connects any RNICA field or intelligence finding to a POC Intervention | **Missing** |
| → Narrative Linkage | `lcdEligibilityNarrative` (manual) is the only narrative field that could plausibly reference decline evidence, and it is user-typed with no structural link back to specific findings (per `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`) | Manual only, no structural link |
| → Traceability | `finalization.pocGenerationCompleted` (boolean checkbox) is the sole marker that POC generation "occurred," with no reference to which RNICA fields, findings, or HOPE items justified any specific Problem/Goal/Intervention created elsewhere | Attestation only, not evidentiary |

## HOPE-derived findings that could plausibly support POC/problem generation (candidate evidence, not implemented linkage)

These are RNICA fields that carry HOPE significance (per
`SNS_RNICA_VALIDATION_INVENTORY_1.0` and the HOPE Crosswalk in
`SNS_RNICA_SECTION_INVENTORY_1.0`) and would be natural evidence sources
for hospice Problems if a POC-linkage engine existed — recorded here as
the current raw material, not as an implemented mapping:

| HOPE-derived RNICA field | Plausible hospice Problem area | Current POC linkage |
|---|---|---|
| `symptomImpact.pain` / `pain.*` (J0900, J0915, J2051-A) | Pain management | None |
| `symptomImpact.shortnessOfBreath` / `respiratory.*` (J2051-B) | Respiratory symptom management | None |
| `symptomImpact.{nausea,vomiting,diarrhea,constipation}` (J2051 C-F) | GI symptom management | None |
| `symptomImpact.anxiety`, `symptomImpact.agitation` (J2051-G/H) | Psychosocial/behavioral symptom management | None |
| `performanceStatus.pps`/`.kps`/`.fast` (M1190-adjacent) + Decline Summary (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` §1) | Functional decline / eligibility support | None (Decline Summary is clipboard-only, not POC-linked) |
| `skin.braden.total`, `skin.*` | Integumentary/pressure-injury prevention | None |
| `imminentDeath.appearsThreeDaysOrLess` (J0050) | Imminent-death care planning | None |
| `diagnoses.hopeComorbidities.*` (I0100-I8005) | Disease-specific eligibility/comorbidity management | None |

## Status

**Deliverable #8 (`SNS_POC_EVIDENCE_INVENTORY_1.0`) complete.** Direct
codebase search confirms there is currently **no** implemented linkage
between RNICA/HOPE-derived findings and POC Problems, Goals, or
Interventions. The full requested traceability chain is documented with
every link marked as either Missing, Manual-only, or Read-only/
non-authoritative, and the candidate HOPE-derived evidence fields that
a future POC-evidence engine would draw from are listed for reference —
without inventing or assuming an implementation that does not exist.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #9 — `SNS_IMPLEMENTATION_GAP_REPORT_1.0`.
