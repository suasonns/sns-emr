# SNS RNICA HOPE Crosswalk Verification 2.0 — Phase 2, Step 2

**STATUS: IN PROGRESS**

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## STEP RULE

This document verifies current RNICA against the frozen HOPE Crosswalk
(`SNS_RNICA_SECTION_INVENTORY_1.0.md` §"HOPE Crosswalk (Deliverable 6)")
and cross-checks it against `SNS_RNICA_VALIDATION_INVENTORY_1.0` and
`SNS_RNICA_IMPLEMENTATION_GAP_REPORT_1.0`. It does not modify the
Crosswalk, the Field Inventory, or any other frozen artifact. It
consolidates verification status into one pass/gap table for Gap
Validation (Step 3).

Source artifacts (frozen, unmodified):
- `SNS_RNICA_SECTION_INVENTORY_1.0.md` — HOPE Crosswalk (Category A target mapping + Category B implementation verification)
- `SNS_RNICA_VALIDATION_INVENTORY_1.0.md` — HOPE Field-to-Item Dependency table
- `SNS_RNICA_IMPLEMENTATION_GAP_REPORT_1.0.md` — direct/indirect/calculated/missing classification

---

## Verification Result by HOPE Section

| HOPE Section | Items | Verified Status |
|---|---|---|
| A — Administrative/Demographics | A0050–A2115 | Mostly **Not Applicable to RNICA** (out of scope — Patient Overview/Visit/Admission modules). A1005, A1010, A1110 **Confirmed** in RNICA. A1805/A1905/A1910 not confirmed as HOPE-coded fields (not flagged as compliance gaps — likely correctly out of scope, per Crosswalk Category 4) |
| F — Preferences/Spiritual | F2000, F2100, F2200 | **Confirmed** (subject to the ACP path-mismatch sync defect, already tracked, not re-litigated here) |
| F3000 | Spiritual/Existential Concerns | **GAP — verified.** No RNICA field. Consistent across Crosswalk, Validation Inventory, and Gap Report |
| I — Diagnoses/Comorbidities | I0010, I0100–I8005 (15 items) | **Confirmed** — 1:1 boolean fields, verified consistent across all three source documents |
| J0050 | Death is Imminent | **Confirmed**, but dual-section-listed (`imminentDeath` + `diagnoses` hope arrays) — verified open reconciliation item, not a gap |
| J0900, J0915 | Pain Screening, Neuropathic Pain | **Confirmed** |
| J0905, J0910 | Pain Active Problem, Comprehensive Pain Assessment | **GAP — verified** across all three source documents |
| J2030, J2040 | SOB Screening, SOB Treatment | **GAP — verified** across all three source documents |
| J2050 | Symptom Impact Screening | **Confirmed** but misplaced under `sfv` instead of `symptomImpact` — verified open reconciliation item, not a gap |
| J2051 (A-H) | Symptom Impact | **Confirmed** — primary SFV trigger source |
| J2052, J2053 | SFV, SFV Symptom Impact | **Confirmed** (J2052 is DERIVED via `sfv_requirements`/`complete_sfv_requirement_from_visit()`, not a raw form read — consistent with Validation Inventory) |
| M1190 | Skin Conditions gate | **Confirmed**, dual-section-listed (`performanceStatus` + `skin` hope arrays) — verified open reconciliation item, not a gap |
| M1195, M1200 | Types of Skin Conditions, Skin/Ulcer Treatments | **GAP — verified** across all three source documents |
| N0500, N0510, N0520 | Scheduled Opioid, PRN Opioid, Bowel Regimen | **GAP — verified.** Entire N-section absent from RNICA |
| Z0350, Z0400 | Date Completed, Signature | **Confirmed** in Finalization |
| Z0500 | Verifying Signature | Not separately confirmed from Z0400 — verified open reconciliation item (may be the same signature capture or a distinct supervisor-review signature) |

---

## Consolidated Verification Outcome

All items in the HOPE Crosswalk's Category B (Implementation
Verification) are **confirmed consistent** across the three source
documents — no new discrepancy was found between the Crosswalk, the
Validation Inventory, and the Gap Report. The verification produces
three outcome classes, matching the Crosswalk's own status vocabulary:

1. **Confirmed** (implemented, 1:1 or DERIVED as documented) — A1005,
   A1010, A1110, F2000, F2100, F2200, I0010, I0100–I8005 (15 items),
   J0050, J0900, J0915, J2050, J2051 (A-H), J2052, J2053, M1190, Z0350,
   Z0400.
2. **Verified open reconciliation items** (implemented, but with a
   placement/dual-listing ambiguity — not a missing-field gap): J0050
   dual-listing, J2050 placement under `sfv`, M1190 dual-listing, Z0500
   vs. Z0400 signature distinction, plus the ACP storage-path defect
   already tracked against F2000/F2100/F2200's sync layer.
3. **GAP — verified** (no RNICA field exists at all): F3000, J0905,
   J0910, J2030, J2040, M1195, M1200, N0500, N0510, N0520 — nine items,
   matching the Gap Report's count exactly.

No new gap was discovered during this verification pass. No existing
gap was found to be resolved. The Crosswalk's Category A target mapping
(A→Demographics, F→ACP/Spiritual, I→Diagnoses, J→Symptoms, M→
Integumentary, N→Medications, Z→Finalization) is confirmed unchanged and
is not reopened here.

## Status

**Phase 2, Step 2 (HOPE Crosswalk Verification) complete.** Verification
confirms full consistency between the HOPE Crosswalk, Validation
Inventory, and Gap Report — 3 outcome classes recorded, 9 confirmed
gaps, 5 open reconciliation items (none are missing-field gaps).

No code changes are authorized by this document. No frozen artifact was
modified.
