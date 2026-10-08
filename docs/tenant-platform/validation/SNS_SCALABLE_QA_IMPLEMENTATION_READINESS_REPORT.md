# SNS Scalable Quality Review — Implementation Readiness Report

**Status:** Analysis artifact only. No migration, model, API, route, frontend component, or test was
created. Nothing staged, committed, or pushed. This report supersedes nothing in
`SNS_AUTHORITY_CLASSIFICATION_MATRIX.md`; it reconciles the Stage 2A design contract against it and
against the four requirement documents, then returns a readiness scorecard.
**Implementation authorization:** NOT GRANTED by this report. Stage 2B remains blocked pending the
explicit decisions in §2.

**Branch note (reaffirmed):** current branch `suasonns-hope-complete-cms-alignment` remains classified
**CLOSED-PR LINEAGE + HISTORICALLY STALE** (tied to closed PR #167; 51 commits behind / 1 ahead of
`origin/main`). No implementation branch is cut from this report. See §3 for the recommended branch
plan, to be executed only once Stage 2B is authorized.

Documents reconciled:
1. `docs/tenant-platform/validation/SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md` (this session)
2. `SNS_AUTHORITY_CLASSIFICATION_MATRIX.md` (attached this turn)
3. `docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md` (repo, amended)
4. `SNS_SCALABLE_QA_WORKFLOW_REQUIREMENT.md` (session package)
5. `SNS_SCALABLE_QA_WORKFLOW_RULES.md` (session package)
6. `SNS_QA_SMALL_AND_LARGE_AGENCY_SCENARIOS.md` (session package)

---

## 1. Delta Report

### A. Items fully approved (Authority Matrix confirms or the requirement docs lock them; no further
product decision needed)

- Draft Workspace: saved/recoverable/editable, not automatically a legal-record version.
- Quality Review is a capability, not a job title; "Authorized Reviewer" terminology; dedicated QA
  department **not required** by any cited authority.
- Clinical status and QA status are stored/audited as independent dimensions; neither overwrites the
  other; assessment purpose (Initial/Update/Recertification) is a third independent dimension.
- `Quality Approved` never authenticates, certifies, signs, approves a POC, or makes a coverage
  determination.
- Self-review: allowed only by tenant policy, always labeled `Self-Review`, never `Independent
  Review`, does not satisfy independent review by default.
- Authenticated entries are immutable; corrections preserve original content + reason + discovery
  date + correction date + correction authentication; CA 48-hour correction-after-discovery
  requirement; addenda are distinct/traceable/dated/authenticated and separate from the Medicare
  election addendum domain.
- RNICA/`RNICA_UPDATE_TYPE` must never be clinician-facing; `UPDATE`/`RECERT` stored values map
  1:1 to `UPDATE_ASSESSMENT`/`RECERTIFICATION_ASSESSMENT` labels with **no data migration required**.
- Body Systems rollout proceeds one system at a time; no one-pass generation of system-specific forms.
- Recertification/QA compliance boundaries (§5–§6 below) — locked as written, no dissent found in any
  source document.
- Status indicators always paired with text, never color alone.
- QAPI (42 CFR 418.58) is the federal program; record-level Quality Review is an SNS tool that
  supports it but is **not** the complete QAPI program — these must stay visibly distinct in any
  reporting surface.

### B. Items still requiring product approval

- Finalized / Pending Signature full semantics (editable? chart-visible? legal record? QA-visible?
  return-to-draft authority?) — Authority Matrix confirms this is still open; see §2A for proposed
  defaults.
- Self-review/independent-review/second-reviewer matrix **by document type** (Initial, Update,
  Recertification, Visit Notes, IDG documents, Discharge) — no document-type risk taxonomy exists yet
  in the repository; see §2B.
- "Amendment" as a universal post-signature action — Authority Matrix explicitly marks this
  **Unresolved**; CA source only addresses Correction and Addendum. Recommendation: do not create a
  generic `Amendment` action; model only `Correction` and `Addendum` per document family, with
  `Amendment` reserved for document families (e.g. `RnicaAmendment`) that already have a bespoke,
  previously-approved amendment path.
- Quality finding controlled vocabularies (category/severity/status/escalation) — proposed in §2D,
  not yet product-approved.
- Second-reviewer trigger conditions (which risk categories require one) — unresolved, needs product
  input, no repository precedent found.

### C. Items requiring legal/compliance review

- Exact CA §74888 text mapped to the 48-hour correction clock for *every* correction category (the
  Authority Matrix itself flags "legal review should confirm application to each correction
  category").
- Final codified CMS election-addendum furnishing/update deadline text and any CMS corrections
  (Authority Matrix: "final codified text and corrections must be checked at release") — affects
  nothing new here since SNS already reuses `ElectionAddendumRequest`/`ElectionAddendumDetermination`,
  but the deadline constants must be revalidated against final CMS text before Stage 2B touches that
  code.
- LCD version/effective-period verification at time of use (guidance, not a static citation).
- Whether "amendment" needs to exist as a named action for any document family beyond
  `RnicaAmendment` under California law — tied to item B above.

### D. Items requiring architecture review

- QualityReview → RecordVersion referential-integrity design (Stage 2A §6) — proposed, not yet
  architecture-approved.
- Task/QualityReview transactional state-ownership boundary (Stage 2A §8) — proposed service names
  only, no transaction/idempotency design yet.
- GuardrailPolicy schema-versioning mechanism for tenant QA policy (Stage 2A §9) — proposed, not
  approved.
- Document-family correction/amendment/addendum registration interface (Stage 2A §12, Option A) —
  architecture must confirm `RnicaAmendment`'s pattern generalizes cleanly to Update/Recertification/
  Visit Notes/IDG/Discharge without forcing a premature rewrite of `RnicaAmendment` itself.
- Body Systems `assessment_id` linkage rollout mechanics (Stage 2A §16) — nullable FK during
  compatibility period; orphan-detection job design not yet written.

### E. Items requiring migration review

- Any column/table from the Stage 1 proposed list (assessment lifecycle columns: `benefit_period_id`,
  `finalized_at`, `signed_at`, `version`, QA-routing fields on `rnica_assessments`; new `QualityReview`/
  `QualityFinding` tables; `body_systems_assessments.assessment_id` nullable FK) — **none created**;
  all remain Phase-A candidates per the Stage 2A §14 rollout plan, pending a dedicated migration-review
  pass once Stage 2B is authorized and a clean branch exists.
- Current row counts (confirmed Stage 1, dev DB `sns_emr_test_rnica_3patients`: `rnica_assessments` 13
  rows, `rn_recert_assessments` 0 rows, `benefit_periods` 0 rows, `body_systems_assessments` 0 rows,
  `election_addendum_requests` 0 rows) must be **re-verified immediately before** any migration is
  authored — they are not assumed current here.

---

## 2. Resolved Open Product Decisions — Recommendations (proposed defaults, not yet executed as code)

### A. Finalized / Pending Signature

| Question | Recommended default | Rationale |
|---|---|---|
| Editable? | No — ordinary edits blocked; only `Return to Draft` re-opens editing | Prevents Finalized from becoming a second uncontrolled draft state |
| Visible in chart? | Yes, labeled `Pending Signature` | Clinicians/coverage staff need visibility of work awaiting authentication |
| Legal record? | **No** | Only the Signed/Authenticated version is the legal record, per CA authentication requirement |
| QA-visible? | No — QA only reviews `Signed/Authenticated` versions by default; pre-authentication review (Stage 2A §4 Mode A) is a separate, policy-gated path, not default QA | Keeps the draft/legal-record line unambiguous, matches Authority Matrix "Post-authentication quality audit" default |
| Return-to-draft allowed? | Yes | Clinician must be able to keep investigating before authenticating |
| Who may return it? | The original author, or a supervisor/coverage clinician with an explicit reassignment reason | Mirrors existing reassignment-reason pattern already used for Task/IDG review |
| Audit requirement | `Finalized`, `Returned to Draft` (with actor + reason), and `Authenticated` are each separate audit events | Matches existing generic `AuditLog` free-text action convention |

This remains a **proposed default**, listed as still-open in §1B above — it requires explicit product
sign-off before an enum/migration is created.

### B. Self-review matrix (document type × action)

| Document type | Self-review allowed? | Independent review required? | Second reviewer required? |
|---|---|---|---|
| Initial Comprehensive RN Assessment | Tenant-configurable, default **No** | Default **Yes** | Tenant-configurable, default No |
| Update Assessment | Tenant-configurable, default **Yes** (checklist only) | Default policy-dependent | Default No |
| Recertification Assessment | Tenant-configurable, default **No** | Default **Yes** | Tenant-configurable, default No |
| Visit Notes | Tenant-configurable, default **Yes** | Default policy-dependent | Default No |
| IDG documents | Follows existing `IDGReview` follow-up pattern; not change by this effort | N/A — out of scope | N/A |
| Discharge documentation | Tenant-configurable, default **No** | Default **Yes** | Tenant-configurable, default No |

This table is a **recommendation**, explicitly listed as unresolved in the Authority Matrix and in
§1B. No code/policy value is created from it until approved.

### C. Quality status state machine (complete)

```text
NOT_ROUTED
   |
   v  (routing policy determines review is required)
PENDING_REVIEW
   |
   v  (reviewer claims or is assigned)
IN_REVIEW
   |
   +---> REVIEW_COMPLETED --(0 blocking findings)--> APPROVED  [terminal]
   |
   +---> REVIEW_COMPLETED --(>=1 blocking finding)--> FOLLOW_UP_REQUIRED
                                                        |
                                                        v (clinician correction/amendment/addendum)
                                                     RESUBMITTED
                                                        |
                                                        v (reviewer re-opens)
                                                     IN_REVIEW  (loop)

Any of {PENDING_REVIEW, IN_REVIEW, FOLLOW_UP_REQUIRED, RESUBMITTED} --(escalation trigger)--> ESCALATED
ESCALATED --(resolved by supervisor/compliance)--> IN_REVIEW | APPROVED | FOLLOW_UP_REQUIRED
```

Terminal states: `APPROVED`. All others are non-terminal. `ESCALATED` is re-enterable, not terminal.
A new authenticated `RecordVersion` always starts a **new** `QualityReview` at `NOT_ROUTED`/
`PENDING_REVIEW`; it never mutates the prior version's terminal `APPROVED` state.

### D. Quality finding controlled vocabulary (proposed)

- **category:** `INCONSISTENCY`, `MISSING_DOCUMENTATION`, `UNSUPPORTED_OBSERVATION`,
  `MEDICATION_DISCREPANCY`, `BODY_SYSTEMS_DISCREPANCY`, `NARRATIVE_CONTRADICTION`,
  `PLAN_OF_CARE_CONFLICT`, `SIGNATURE_AUTHENTICATION_ISSUE`, `RECERTIFICATION_SUPPORT_GAP`,
  `NON_COVERED_ITEMS_REVIEW_GAP`, `OTHER_AGENCY_DEFINED` (tenant-extensible via policy, not free text)
- **severity:** `LOW`, `MODERATE`, `HIGH`, `CRITICAL` — tenant policy configures which severities are
  blocking (default: `HIGH` and `CRITICAL` block `APPROVED`)
- **status:** `OPEN`, `ACKNOWLEDGED`, `RESOLUTION_SUBMITTED`, `VERIFIED`, `WITHDRAWN`, `REOPENED`
- **escalation_status:** `NOT_ESCALATED`, `ESCALATED`, `ESCALATION_RESOLVED`

This is a proposed vocabulary only — these are not yet CHECK constraints or enum types in any model.

---

## 3. Branch Strategy (recommended sequence, no code created)

| Phase | Branch name | Depends on | Migration impact | Rollback strategy | Expected files (design-time estimate, not created) |
|---|---|---|---|---|---|
| 1 — Assessment Lifecycle Foundation | `feature/qa-phase1-assessment-lifecycle` | Fresh cut from current `origin/main` | Additive: `finalized_at`, `signed_at`, `version`, `benefit_period_id` on `rnica_assessments`; no drops | Revert migration (additive-only, safe to down-migrate before backfill) | `backend/app/models/rnica_assessment.py`, new Alembic revision, `backend/app/services/assessment_lifecycle_service.py` |
| 2 — Quality Review Foundation | `feature/qa-phase2-quality-review` | Phase 1 merged | Additive: `quality_reviews`, `quality_findings` tables; extend `Task`/`TaskType` enum with `QUALITY_REVIEW` | Drop new tables only (no shared-table edits) | `backend/app/models/quality_review.py`, `quality_finding.py`, `backend/app/services/quality_review_service.py`, `backend/app/core/capabilities.py` additions |
| 3 — Medicare Non-Covered Items Review | `feature/qa-phase3-medicare-review` | Phase 1 merged (needs `benefit_period_id`) | None beyond Phase 1 columns; reuses `ElectionAddendumRequest`/`ElectionAddendumDetermination` | No schema rollback needed if scoped to service/UI wiring only | `backend/app/services/non_covered_items_service.py` (new, thin wrapper), frontend Recertification toggle wiring |
| 4 — Body Systems Ownership Migration | `feature/qa-phase4-body-systems-fk` | Phase 1 merged | Additive: nullable `body_systems_assessments.assessment_id` FK; orphan report before any future non-null transition | Nullable FK is drop-safe; no non-null constraint added in this phase | migration file, orphan-report script, model update |
| 5 — UI Terminology Remediation | `feature/qa-phase5-ui-terminology` | None (independent of 1–4) | None | Revert is a pure UI diff | `RnicaWorkflowRail.jsx`, `RNICACommandWorkspace.jsx`, `RnicaDesignSystem.jsx`, `PatientStoryShadcn.jsx`, `PatientChart.jsx` label changes |

Phase 5 has no dependency on 1–4 and could be sequenced first or in parallel if the product wants an
early visible terminology win; it touches no schema.

---

## 4. Authority Matrix Validation Per Planned Feature

| Planned feature | Classification | Blocked? |
|---|---|---|
| Initial Comprehensive RN Assessment controlled creation | Binding Federal Requirement (42 CFR 418.54) + SNS Product Policy for the uniqueness mechanism | Uniqueness mechanism blocked — depends on §2A (Finalized semantics), itself Unresolved |
| Update Assessment toggle/sections | Binding Federal Requirement (update-of-comprehensive-assessment standard) + SNS Product Policy for UI | Not blocked — mapping confirmed feasible without migration |
| Recertification Assessment + benefit-period link | Binding Federal Requirement (42 CFR 418.22, 418.24) | Not blocked for documentation/evidence purposes; **certification act itself is out of scope** (physician-only) |
| Medicare Non-Covered Items Review gate | SNS Product Policy (recertification gate) wrapping Binding Federal Requirement (election addendum, CMS-1851-F) | Not blocked — reuses existing addendum models |
| Quality Review engine (routing/queue/escalation) | SNS Product Policy | Not blocked at the policy level; **blocked at the architecture level** pending §1D items (RecordVersion linkage, Task/QualityReview ownership, policy schema) |
| Finalized/Pending Signature state | **Unresolved Decision** | **Blocked** until §2A is approved |
| Self-review/independent/second-reviewer matrix | SNS Operational Policy, matrix itself **Unresolved** | **Blocked** until §2B is approved |
| Universal "Amendment" action | **Unresolved Decision** | **Blocked** — do not implement a generic Amendment action |
| QualityReview↔RecordVersion linkage | **Proposed Technical Design** | **Blocked** pending architecture review (§1D) |
| Task/QualityReview transactional ownership | **Proposed Technical Design** | **Blocked** pending architecture review |
| GuardrailPolicy schema versioning for QA policy | **Proposed Technical Design** | **Blocked** pending architecture review |
| Body Systems `assessment_id` FK | SNS Product Policy / **Proposed Technical Design** | **Blocked** pending architecture + migration review |
| UI terminology remediation (remove "RNICA" strings) | SNS Product Policy (terminology lock) | **Not blocked** — pure UI copy change, no dependency on any open item |
| Automatic eligibility/certification/prognosis determination | **Prohibited Product Boundary** | Permanently blocked by design; not a Stage 2B candidate at all |

Everything marked **Blocked** above may not be implemented until its listed dependency is resolved.

---

## 5. Recertification Compliance Boundary — Confirmed

**Recertification Assessment supports:**
- Documentation of current clinical findings relevant to recertification.
- Evidence collection for the attending/hospice physician's recertification narrative.
- Completion of the Medicare Non-Covered Items Review gate before finalization.

**Recertification Assessment does NOT:**
- Certify or recertify terminal illness.
- Approve or stand in for the physician's clinical narrative.
- Approve the plan of care.
- Make an eligibility determination.

Certification/recertification authority remains exclusively with the authorized physician per 42 CFR
418.22. **Repository impact:** no `rnica_assessments`/`rn_recert_assessments` field may be labeled or
treated as a certification record; any future `RecertificationAssessment` status value such as
`COMPLETE` must be documented as "evidence gathering complete," never "recertification complete," in
both code comments and UI copy. No status transition in this workflow may auto-generate or
auto-approve a certification/recertification document.

---

## 6. Quality Review Compliance Boundary — Confirmed

**Quality Review may:**
- Identify documentation deficiencies (`QualityFinding`).
- Assign follow-up to the responsible clinician (`Task`).
- Verify resolution against the clinician's correction/amendment/addendum.
- Record `Quality Approved` once all blocking findings are verified resolved.

**Quality Review may NOT:**
- Edit authenticated clinician content (enforced by: no reviewer-write path to the
  `RecordVersion`-linked clinical fields; reviewer writes are confined to `QualityFinding`/
  `QualityReview` tables only).
- Certify eligibility, terminal illness, or recertification (enforced by: no `QualityReview`/
  `QualityFinding` field feeds `rnica_assessments`/`rn_recert_assessments` certification-adjacent
  fields; these remain physician-authored).
- Sign/authenticate records on the clinician's behalf (enforced by: `Signed/Authenticated` transition
  requires the clinician's own authentication capability; `QualityReview` has no authentication
  capability in `app/core/capabilities.py`).
- Replace physician judgment (enforced by: §5 boundary + UI copy requiring distinct, non-conflatable
  status chips for `Quality Approved` vs. `Certified`/`Recertified`).

These are enforcement **points**, not yet enforcement **code** — they describe where Stage 2B must
place the checks.

---

## 7. Implementation Readiness Scorecard

| Area | Status | Justification |
|---|---|---|
| Assessment Lifecycle (Finalized/Signed states) | **BLOCKED** | §2A semantics unresolved; nothing may be migrated until locked |
| Initial Comprehensive RN Assessment | **PARTIAL** | Federal requirement and product intent are clear; uniqueness mechanism blocked on Finalized semantics |
| Update Assessment | **READY** (design-only) | Mapping confirmed feasible without migration; toggle behavior fully specified; no open architecture item blocks a design spec, though no code is authorized without Stage 2B |
| Recertification Assessment | **PARTIAL** | Documentation/evidence role is clear and boundary-confirmed (§5); benefit-period linkage needs Phase 1 columns (not yet migrated) |
| Medicare Non-Covered Items Review | **READY** (design-only) | Reuses mature, already-built `ElectionAddendumRequest`/`ElectionAddendumDetermination`; gate logic fully specified |
| Quality Review (engine/workflow) | **PARTIAL** | Product policy and compliance boundary are locked (§6); RecordVersion linkage and Task-ownership architecture remain open (§1D) |
| Body Systems Ownership | **BLOCKED** | Architecture + migration review both outstanding; rollout plan is design-only (Stage 2A §16) |
| Corrections | **PARTIAL** | CA requirements and field set are locked; document-family registration interface (Option A) needs architecture confirmation beyond `RnicaAssessment` |
| Addenda | **PARTIAL** | CA requirements locked for the generic clinical addendum; Medicare election addendum path is already mature and separate; generic addendum registration interface not yet built |
| Amendment Model | **BLOCKED** | Explicitly Unresolved in the Authority Matrix; do not generalize beyond existing `RnicaAmendment` |
| Concurrency | **BLOCKED** | No transaction/idempotency design yet for Task/QualityReview (§1D); no version/concurrency token design for QualityReview/QualityFinding beyond a one-line mention in Stage 2A §18 |
| Authorization | **READY** (design-only) | Capability framework already exists in production (`app/core/capabilities.py`); only new `quality_review_*` capability names need adding, with zero default grants |
| Tenant Policy | **PARTIAL** | `GuardrailPolicy` infra exists and is reusable; schema-versioning/fail-closed validation mechanism is still a Proposed Technical Design |
| Audit | **READY** (design-only) | Generic `AuditLog` already supports free-text actions with no migration needed; full QA audit-event list specified in `SNS_SCALABLE_QA_WORKFLOW_RULES.md` |

**Overall:** No area is cleared for Stage 2B coding yet. `Update Assessment`, `Medicare Non-Covered
Items Review`, `Authorization`, and `Audit` are architecturally unblocked and could move fastest once
Stage 2B is authorized and a clean branch exists; everything else has at least one outstanding item
from §1B/§1C/§1D.

---

## 8. Stop Condition

No migration, model, API, route, frontend component, or test was created. Nothing was staged,
committed, pushed, or branched. This report stops here and awaits explicit Stage 2B implementation
authorization, including resolution of the items listed in §1B (product), §1C (legal/compliance),
§1D (architecture), and §1E (migration review) before any corresponding code is written.
