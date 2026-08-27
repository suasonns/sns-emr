# SNS RNICA Build Sequencing 2.0 — Phase 2, Step 4

**STATUS: IN PROGRESS**

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## STEP RULE

This document sequences the 19 validated gaps
(`SNS_RNICA_GAP_VALIDATION_2.0`) into a build order. It does not design
implementation details, write code, or modify any frozen artifact. It
orders work by dependency and risk, using the complexity ratings already
established in `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0`.

Source artifacts (frozen/Phase-2, unmodified):
- `SNS_RNICA_GAP_VALIDATION_2.0.md` (Phase 2, Step 3)
- `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0.md` (Phase 1, frozen)
- `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md` (Phase 2, Step 1)

---

## Build Sequence

### Sequence 1 — Foundational (no dependents block on these; everything else benefits)

1. Fix ACP storage-path mismatch (F2000/F2100/F2200 sync) — MEDIUM
2. Fix J2051 SFV-trigger source mismatch (`clinical_notes` → `form_data`) — HIGH
3. Add audit trail columns + `log_event()` wiring (`created_by`/`updated_by`/`locked_by`) — HIGH
4. Fix backend lock-check on `update_rnica_assessment` (silent-overwrite risk) — HIGH
5. Fix `status` reset-to-DRAFT-on-update behavior — LOW

*Rationale: these are defects in already-implemented fields/flows, not
new fields. They are prerequisites for trustworthy data before new HOPE
fields are added on top of the same sync/audit/lock machinery.*

### Sequence 2 — Section Architecture Migration

6. Section reorganization (28 → 12 target sections, per
   `SNS_RNICA_MASTER_MAP_MAPPING_2.0`) — CRITICAL

*Rationale: new HOPE fields (Sequence 3) and new POC/Narrative
capability (Sequence 4) need a stable target section to be placed in;
sequencing the reorganization first avoids building new fields twice.*

### Sequence 3 — HOPE-Derivation Gap Closure (per Governance Rule: derive, do not duplicate)

7. N0500/N0510/N0520 (Scheduled Opioid, PRN Opioid, Bowel Regimen) — CRITICAL, must be DERIVED from Medication Reconciliation data, not re-entered
8. F3000 (Spiritual/Existential Concerns) — CRITICAL
9. J0905/J0910 (Pain Active Problem, Comprehensive Pain Assessment) — HIGH
10. J2030/J2040 (SOB Screening, SOB Treatment) — HIGH
11. M1195/M1200 (Types of Skin Conditions, Skin/Ulcer Treatments) — HIGH
12. J2050 naming/placement correction (`sfv` → `symptomImpact`) — MEDIUM
13. M1190 / J0050 dual-listing reconciliation (pick one authoritative section each) — LOW

*Rationale: ordered by Migration Complexity rating (CRITICAL before
HIGH before MEDIUM before LOW), consistent with
`SNS_MIGRATION_COMPLEXITY_RATINGS_1.0` §3 priority ranking.*

### Sequence 4 — Validation, POC, and Narrative Capability

14. Validation coverage expansion (27 → ~300 fields; add backend enforcement) — HIGH
15. No amendment/addendum workflow for locked assessments — HIGH
16. POC evidence linkage (Problem → Evidence → Goal → Intervention; builds target Section 11) — CRITICAL
17. Narrative generation/persistence (builds target Section 10; persist Decline Summary, add narrative-generation capability) — MEDIUM
18. Workflow automation / Action Center triggers reachable from RNICA — CRITICAL
19. PATCH/DELETE endpoints — MEDIUM

*Rationale: these depend on the section architecture (Sequence 2) and
the corrected/complete field set (Sequence 3) being in place — POC
evidence linkage and narrative generation both consume the full set of
clinical findings, including the newly-added HOPE fields.*

---

## Dependency Notes

- Sequence 3, Item 7 (N0500/N0510/N0520) explicitly depends on the
  Medication Reconciliation data model being confirmed as a viable
  DERIVED source, per the HOPE Governance Rule's "no duplicate
  clinician documentation" requirement — this must be checked before
  implementation, not assumed.
- Sequence 4, Item 16 (POC evidence linkage) and Item 18 (Action Center
  triggers) are both CRITICAL and independent of each other — they may
  be built in parallel once Sequences 1-3 are complete.
- Sequence 1 items are independent of each other and may be built in
  parallel.

## Status

**Phase 2, Step 4 (Build Sequencing) complete.** 19 validated gaps are
ordered into 4 build sequences (Foundational → Section Architecture →
HOPE-Derivation Gap Closure → Validation/POC/Narrative Capability), with
dependency notes. No implementation is authorized by this document.

---

## Phase 2 — Reconciliation: COMPLETE

1. Current RNICA → Master Map — `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md` ✅
2. Current RNICA → HOPE Crosswalk — `SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md` ✅
3. Current RNICA → Target Design (Gap Validation) — `SNS_RNICA_GAP_VALIDATION_2.0.md` ✅
4. Build Sequencing — `SNS_RNICA_BUILD_SEQUENCING_2.0.md` ✅ (this document)

No code changes are authorized. Phase 3 (Build Design) begins only on
explicit direction.
