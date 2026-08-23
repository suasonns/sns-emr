# SNS Migration Complexity Ratings 1.0 — Phase 1, Deliverable 10

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

This document rates the implementation effort for every gap identified
in `SNS_IMPLEMENTATION_GAP_REPORT_1.0`. It does not modify any frozen
artifact, does not design a solution, and does not authorize
implementation — it prioritizes the build roadmap for a future phase.

Source of truth: `SNS_IMPLEMENTATION_GAP_REPORT_1.0` (all gaps rated
below are taken directly from that document; no new gaps are introduced
here).

## Rating scale

- **LOW** — existing field/table/endpoint, reuse or small addition, no schema change.
- **MEDIUM** — field exists but requires rework (new validation, new sync, new column), single-layer change.
- **HIGH** — new workflow required across two or more layers (DB + API, or API + UI).
- **CRITICAL** — new field(s) + database + API + UI all required, and/or directly affects compliance/reporting integrity (HOPE/CMS).

---

## 1. HOPE-derivation gaps (highest priority, per governance rule)

| Gap | Rating | Dependency Count | Data Migration Impact | API Impact | UI Impact | Compliance Risk |
|---|---|---|---|---|---|---|
| F3000 (Spiritual/Existential Concerns) — no RNICA field | **CRITICAL** | 0 (net-new) | New JSONB key only (no relational migration, per current persistence model) | New field(s) inside existing save/update payload — no new endpoint needed | New field(s) in Spiritual Screening section | High — CMS HOPE reporting element with zero current source |
| J0905 / J0910 (Pain Active Problem / Comprehensive Pain Assessment) — no field | **HIGH** | 0 | New JSONB keys only | Existing payload | New fields in Pain Assessment | High — required HOPE pain-assessment completeness items |
| J2030 / J2040 (SOB Screening / Treatment) — no field | **HIGH** | 0 | New JSONB keys only | Existing payload | New fields in Respiratory | High — required HOPE symptom items |
| N0500 / N0510 / N0520 (Scheduled Opioid / PRN Opioid / Bowel Regimen) — no field at all | **CRITICAL** | Depends on Medication Reconciliation / Hospice Orders Hub data model (Section 26) for opioid/bowel-regimen data that may already exist elsewhere | Likely needs new JSONB keys, possibly cross-referencing `med_reconciliation` data (`MedReconciliationItem` model) rather than duplicating it | May require reading from the medication reconciliation source instead of a duplicate RNICA field, per the "no duplicate clinician documentation" governance rule | New UI element(s), ideally derived/read-only rather than re-entered | Critical — entire N-section absent; also a governance-rule test case (must be DERIVED from medication data, not re-typed) |
| M1195 / M1200 (Types of Skin Conditions / Treatments) — no field | **HIGH** | Skin/Wounds section already has free-text wound-care fields; needs structured multi-select | New JSONB keys | Existing payload | New structured fields (multi-select) replacing/augmenting free text | Medium-high — HOPE skin-treatment reporting |
| ACP storage path mismatch (F2000/DPOA/Decision-Maker sync silently broken) | **MEDIUM** | 3 sync functions affected (`set_current_code_status`, DPOA/Decision-Maker `set_patient_contact` calls) | No schema change — path-read fix only | No new endpoint; fixes existing extractor logic | None required | High — silently broken sync directly affects code-status/contact accuracy relied on elsewhere (e.g. Facesheet) |
| J2050 naming/placement (misfiled under `sfv` instead of `symptomImpact`) | **MEDIUM** | 1 (SIDEBAR_CONFIG hope-array entry) | JSONB key relocation (if actually moved) | Existing payload | Section/label correction | Medium — CMS naming accuracy for audit purposes |
| J2051 SFV-trigger reads from `clinical_notes` instead of `rnica_assessments.form_data` | **HIGH** | `hope_phase_b_engine.py` trigger logic, `clinical_notes` model | No RNICA schema change; may need trigger source change | Trigger logic change, not a new endpoint | None required | High — SFV compliance timing depends on this pathway firing correctly |
| M1190 / J0050 dual-section listing (ambiguous authoritative section) | **LOW** | 0 | None | None | Documentation/labeling clarification only | Low — cosmetic/organizational, not a data-integrity risk by itself |
| Nutrition fields not consolidated to a single HOPE-adjacent outcome (Rule 4 gap) | **MEDIUM** | 4 existing fields (weight, weightChange, appetite, intake) + dysphagia | No schema change if only a computed rollup is added | Possibly a new computed/derived response field | New summary/rollup display | Medium — supports decline documentation quality, not a hard CMS requirement today |

---

## 2. Non-HOPE structural gaps (from Gap Report §2)

| Gap | Rating | Dependency Count | Data Migration Impact | API Impact | UI Impact | Compliance Risk |
|---|---|---|---|---|---|---|
| Section reorganization (28 sections → target 12-section architecture) | **CRITICAL** | All 28 sections, ~300 fields | Full JSONB key restructuring across every field | Full endpoint/payload shape change | Full UI rebuild | Low direct compliance risk, but high risk of data loss/mismapping during transition |
| JSONB-only persistence (no per-field DB columns/types/constraints) | **CRITICAL** | ~300 fields | Would require a normalized schema design and a one-time data migration of all existing `form_data` blobs | New per-field API contracts | Minimal UI change if done transparently | Medium — improves data integrity but current lack has not caused a known reporting failure |
| No PATCH/DELETE endpoints | **MEDIUM** | 0 (additive) | None | New endpoints | Minor UI change (optional partial-save UX) | Low |
| Validation coverage (27 of ~300 fields validated; frontend-only, unenforced server-side) | **HIGH** | ~270 unvalidated fields; also requires backend validation layer that does not exist today | None (validation logic only) | New backend validation must be added to `save`/`update`/`lock` handlers | Possible new inline error UI for newly-validated fields | High — currently any client can bypass all validation via direct API calls |
| No audit trail on `rnica_assessments` (no `created_by`/`updated_by`/`locked_by`, no `log_event()` calls) | **HIGH** | 3 new columns + `log_event()` wiring in 3 endpoints | New migration to add attribution columns | Handler changes only (no new endpoints) | None required | Critical-adjacent — audit readiness is a named compliance goal in the project's stated purpose, and this is currently a hard zero |
| No workflow automation (Action Center triggers) reachable from RNICA | **CRITICAL** | Unknown — depends on how many trigger rules are eventually designed | Likely new Task/Alert table linkage, no RNICA schema change | New trigger-evaluation logic in save/update handlers | New Action Center UI surfacing (may already exist for other order types) | Medium — this is a capability gap, not a currently-broken compliance requirement |
| No POC evidence linkage (Problem→Evidence→Goal→Intervention) | **CRITICAL** | POC engine, RNICA, HOPE Crosswalk all involved | Likely new linking table(s) | New endpoint(s) connecting RNICA findings to POC engine | New UI for evidence review before POC finalization | High — "no unsupported Plan of Care problems" is an explicit governance goal not currently met |
| Narrative generation minimal/non-persisted (Decline Summary is clipboard-only) | **MEDIUM** | 1 computed value (`summaryText`) | Would need a `form_data` field to persist it, or a new derived-field mechanism | Minor — could piggyback on existing save payload | Auto-insert vs. manual-copy UX change | Low-medium — improves defensibility of narrative evidence, not currently a hard failure |
| No amendment/addendum workflow for locked assessments; no backend lock-check on update | **HIGH** | Lock-state enforcement + new amendment data model | Possibly a new `amendments` table or versioning on `rnica_assessments` | New endpoint(s) or handler guard | New amendment UI | High — a locked/signed clinical record can currently be silently overwritten via `PUT`, which is a genuine documentation-integrity risk |
| `status` reset to `"DRAFT"` on every update regardless of prior state | **LOW** | 0 | None | Handler logic fix only | None required | Low-medium |

---

## 3. Priority ranking (highest risk/compliance impact first)

1. **CRITICAL — compliance-facing:** N0500/N0510/N0520 (entire missing section, and a governance-rule test case for "derive, don't duplicate"), F3000, no audit trail, no POC evidence linkage, no amendment workflow / silent-overwrite risk.
2. **HIGH — compliance-adjacent:** J0905/J0910, J2030/J2040, M1195/M1200, ACP path-mismatch sync fix, J2051 SFV-trigger source fix, validation-coverage/enforcement gap.
3. **MEDIUM — quality/architecture:** J2050 naming, Nutrition rollup, narrative persistence, PATCH/DELETE endpoints.
4. **LOW — cosmetic/organizational:** M1190/J0050 dual-listing, status-reset-on-update behavior.

Full section reorganization and the JSONB→relational persistence change
are rated CRITICAL but are **out of scope for prioritization ahead of**
the HOPE-derivation and compliance-integrity items above, per the
HOPE Governance Rule's emphasis on reporting-element correctness over
architectural restructuring.

## Status

**Deliverable #10 (`SNS_MIGRATION_COMPLEXITY_RATINGS_1.0`) complete.**
Every gap recorded in `SNS_IMPLEMENTATION_GAP_REPORT_1.0` has been rated
Low/Medium/High/Critical with dependency count, data migration impact,
API impact, UI impact, and compliance risk, and a priority ranking is
given. No implementation is authorized by this document.

No changes made to any frozen artifact. No code changes are authorized
by this document.

---

## Phase 1 — Current State Inventory: COMPLETE

All ten deliverables are now written:
1. `SNS_RNICA_FIELD_INVENTORY_1.0` ✅
2. `SNS_RNICA_DATABASE_MAPPING_1.0` ✅
3. `SNS_RNICA_API_MAPPING_1.0` ✅
4. `SNS_RNICA_VALIDATION_INVENTORY_1.0` ✅
5. `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` ✅
6. `SNS_RNICA_AUDIT_INVENTORY_1.0` ✅
7. `SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0` ✅
8. `SNS_POC_EVIDENCE_INVENTORY_1.0` ✅
9. `SNS_IMPLEMENTATION_GAP_REPORT_1.0` ✅
10. `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0` ✅

Per the project's stated Phase sequence, Phase 2 (Reconciliation) and
Phase 3 (Build Design) follow only on explicit direction — no further
action is taken here without that authorization.
