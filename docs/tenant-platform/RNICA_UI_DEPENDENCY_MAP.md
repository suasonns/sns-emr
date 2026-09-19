# RNICA UI Dependency Map

**STATUS: DISCOVERY ONLY — NO REDESIGN — NO CODE — NO SCHEMA — NO MIGRATIONS**

This document classifies every major visible RNICA UI element
(`sns-emr-frontend/src/components/RNICA.jsx`) using the classification set
required by the discovery request:

- **VISUAL ONLY** — pure presentation, no behavior/data dependency
- **SAFE TO REDESIGN** — behavior can be preserved under a different visual
  treatment (layout/styling/component swap allowed; logic must stay wired)
- **WORKFLOW CRITICAL** — drives save/lock/finalize/amendment flow
- **AI CRITICAL** — depends on the RNICA intelligence/heuristics output
- **COMPLIANCE CRITICAL** — required for HOPE/LCD/finalization/regulatory
  correctness

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has locked a product decision that the Diagnoses-section Clinical
> Narrative card (`diagnoses.clinicalNarrative`) was incorrectly placed and
> must not remain a nurse-facing narrative input in the redesigned RNICA;
> `finalization.clinicalNarrative` is the sole authoritative future Clinical
> Narrative. The UI classification below reflects the current repository
> state and is unchanged.
- **BILLING CRITICAL** — required for billing/eligibility correctness
- **SYSTEM CRITICAL** — required for core system integrity (data integrity,
  audit trail, admission/tenant scoping)
- **DO NOT TOUCH** — high blast-radius; any visual or structural change
  requires a separate review before redesign

See `RNICA_SYSTEM_DEPENDENCY_MAP.md` for the underlying evidence citations.
Granularity note: elements are classified at the level of named UI
regions/controls as they exist in `RNICA.jsx` (sections, panels, buttons),
not at the level of every individual input field, since the assessment form
contains hundreds of fields across many clinical sections. Field-level detail
is called out only where it changes the classification (e.g. LCD/attestation
fields).

---

## 1. Navigation / Structure Elements

| Element | Classification | Rationale |
|---|---|---|
| Section/step navigation tree (assessment sections list) | **SAFE TO REDESIGN** | Purely organizes access to form sections; underlying section keys (`rn_ica_keys.py:6-41`) must remain addressable, but the visual nav pattern can change |
| Progress/completion tracking indicator | **SAFE TO REDESIGN** | Presentation of completion state; must continue to reflect true per-section completeness, but rendering can change |
| Patient summary header/banner | **VISUAL ONLY / SAFE TO REDESIGN** | Read-only display of patient/admission context; no write path |
| Care team area (if present) | **VISUAL ONLY** | Display-only, no dependency found in backend trace |

## 2. Clinical Assessment Sections (diagnoses, pain, respiratory, safety, musculoskeletal, neurological, imminent death, psychosocial, etc.)

| Element | Classification | Rationale |
|---|---|---|
| Diagnoses section (primary diagnosis, disease trajectory, clinical narrative, LCD eligibility narrative) | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Feeds required-field validation (`clinical_note_validation_engine.py:380-470`), finalization LCD gate (`rnica_finalization_service.py:120-136`), and AI intelligence input (`rnica_intelligence.py:66-75`). Field presence/keys must be preserved exactly. |
| Pain, respiratory, safety, musculoskeletal, neurological, imminent-death, psychosocial sections | **AI CRITICAL / COMPLIANCE CRITICAL** | Directly consumed as intelligence-engine input (`rnica_intelligence.py:57-176`) and/or required-field validation |
| PPS / KPS / Code Status / Life-Sustaining Treatment Preference / Hospitalization Preference fields | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Explicit required fields in server validation (`clinical_note_validation_engine.py:380-470`) |
| Referrals section + "reviewed" checkbox | **COMPLIANCE CRITICAL** | Required for finalization readiness (`rnica_finalization_service.py:138-144`) |
| Plan of Care narrative field | **COMPLIANCE CRITICAL / WORKFLOW CRITICAL** | Required field and feeds POC adapter (`rnica_poc_adapter.py`) |
| CHHA POC completion field | **COMPLIANCE CRITICAL** | Required when HHA assigned (`rnica_finalization_service.py:148-161`) |

## 3. RNICA "Intelligence" Panel

| Element | Classification | Rationale |
|---|---|---|
| Intelligence/priority summary display | **AI CRITICAL** | Directly renders `rnica_intelligence.py` output; note this is a rules engine, not ML/LLM — redesign must not imply real-time AI/ML branding it doesn't have |
| Findings list | **AI CRITICAL** | Same source |
| Recommendations list | **AI CRITICAL** | Same source |
| Missing-evidence indicators | **AI CRITICAL / COMPLIANCE CRITICAL** | Surfaces gaps that also affect finalization/compliance completeness |
| Structured findings signals display | **AI CRITICAL** | Sourced from `list_pending_structured_findings` / `structured_findings.py` |

## 4. Validation / Warnings / Errors

| Element | Classification | Rationale |
|---|---|---|
| Client-side `validateRNICA` warning/error banners | **WORKFLOW CRITICAL / DO NOT TOUCH** | Gates section completion and finalize eligibility before hitting the server-side check |
| Server-validation error surfacing (required-field engine errors) | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Must always be shown; hiding/softening these risks incomplete regulatory documentation being locked |

## 5. Save / Autosave Controls

| Element | Classification | Rationale |
|---|---|---|
| Autosave indicator ("saving…"/"saved") | **SAFE TO REDESIGN** | Purely a status indicator on top of `useAssessmentAutosave`; underlying 30s autosave timing/behavior must be preserved |
| Manual Save button | **WORKFLOW CRITICAL** | Must remain wired to the save endpoint; visual treatment flexible |

## 6. Finalization / Lock / Sign Controls

| Element | Classification | Rationale |
|---|---|---|
| Signature certification attestation checkbox | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Required boolean gate for lock (`rnica_finalization_service.py:102-109`) |
| Clinician signature field | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Required nonblank field for lock (`rnica_finalization_service.py:111-116`) |
| Finalization readiness checklist/summary display | **COMPLIANCE CRITICAL / WORKFLOW CRITICAL** | Mirrors server readiness function; must not omit or misstate any check |
| Lock button | **WORKFLOW CRITICAL / SYSTEM CRITICAL / DO NOT TOUCH** | Triggers server lock + audit event (`visits.py:1177-1265,1238-1251`); irreversible in effect (locked content becomes amendment-only) |

## 7. HOPE Workflow Controls

| Element | Classification | Rationale |
|---|---|---|
| HOPE status display (ready/closed/submitted/inactivated/unlocked states) | **COMPLIANCE CRITICAL / DO NOT TOUCH** | Directly reflects HOPE lifecycle columns on the model (`rnica_assessment.py:33-50`) and CMS-facing workflow state (`rnica_hope_workflow_service.py`) |
| HOPE action buttons (mark ready, close, submit, etc.) | **COMPLIANCE CRITICAL / WORKFLOW CRITICAL / DO NOT TOUCH** | Drive regulated HOPE submission workflow (`backend/app/api/visits.py:1382-1479`) |

## 8. Amendment Workflow (post-lock)

| Element | Classification | Rationale |
|---|---|---|
| "Request correction/amendment" entry point | **WORKFLOW CRITICAL / COMPLIANCE CRITICAL** | Creates auditable `RnicaAmendment` row; must remain reachable post-lock |
| Amendment approve/deny UI (reviewer role) | **WORKFLOW CRITICAL / COMPLIANCE CRITICAL / DO NOT TOUCH** | Governs regulated correction process with mandatory audit trail (`rnica_amendment_service.py:125-139,189-201,227-239`); deny requires nonblank reason (`visits.py:1504-1509`) |

## 9. POC-Linked Actions

| Element | Classification | Rationale |
|---|---|---|
| "Add order from RNICA suggestion" action | **WORKFLOW CRITICAL** | Explicit, user-triggered POC/order-creation action (`rnica_poc.py:515-538`) — not automatic, so it's safe to relabel/restyle but must remain an explicit, discoverable action |
| POC problem sync/update actions from RNICA sections | **WORKFLOW CRITICAL / DO NOT TOUCH** | Relies on stable `rule_key` dedup logic in the adapter (`rnica_poc_adapter.py:295-367,432-668`); UI must keep triggering the same underlying calls |

## 10. Elements With No Backend Dependency Found (safe defaults)

| Element | Classification | Rationale |
|---|---|---|
| Any purely cosmetic layout, spacing, color, iconography, section ordering that doesn't change field keys or endpoint calls | **VISUAL ONLY / SAFE TO REDESIGN** | No dependency identified |
| Caregiver-related recommendation text within Intelligence panel | **AI CRITICAL (supporting)** | Sourced from intelligence output narrative only, not a standalone caregiver-assessment integration (`rnica_intelligence.py:98-156`) — no dedicated Caregiver Assessment model link found |

---

## 11. Explicit Non-Findings (documented so redesign doesn't assume otherwise)

- No direct UI/back-end tie to Face Sheet, CTI, F2F, IDG, Advance Care
  Planning, dedicated Caregiver Assessment, Medications, Benefit Period
  Logic, `PayerEligibilityCheck`/`EligibilityVerification`, Billing
  Readiness, QA/Compliance Review dashboards, or Survey Readiness was found
  in the RNICA layer. Any redesign that assumes these integrations already
  exist would be introducing new functionality, not preserving existing
  functionality — that would require a separate authorization.

**No implementation, redesign, schema change, or code change is proposed by
this document. Inventory only.**
