# SNS Scalable Quality Review — Stage 2A Design-Hardening & Contract Validation

**Status:** Analysis/decision-record artifact only. No application code, migration, model, API,
frontend component, or test was created or modified to produce this document.
**Stage:** 2A (design-hardening), per corrected instruction superseding the earlier Stage 2
implementation authorization.
**Outcome required before Stage 2B (actual implementation):** Explicit product approval of every
item marked `OPEN — PENDING APPROVAL` below.

---

## 1. Branch and Worktree Safety Gate

| Field | Value |
|---|---|
| Repository root | `C:/Users/rdsua/.copilot/repos/copilot-worktrees/sns-emr/suasonns-ideal-goggles` |
| Current worktree | same as above |
| Current branch | `suasonns-hope-complete-cms-alignment` |
| Current HEAD | `ab724d0661f36dcbd4f47882d317fdd09eaf684c` |
| origin/main HEAD | `e565797039c1980ad8675c8880d35541493a53d8` |
| merge-base(HEAD, origin/main) | `33c9eca64fcbcc013c923b42e6509fff38a813f6` |
| Ancestry | **Diverged** — 1 commit ahead, **51 commits behind** origin/main |
| Associated PR | #167, **closed, not merged** (`base: main`, `head: suasonns-hope-complete-cms-alignment`) |
| Staged files | none |
| Modified (tracked) files | `backend/app/api/registry.py`, `backend/app/models/__init__.py`, `sns-emr-frontend/src/App.tsx`, `sns-emr-frontend/src/components/RNICA.jsx`, `.../RNICACommandWorkspace.css`, `.../RNICACommandWorkspace.jsx`, `sns-emr-frontend/tailwind.config.js` — all pre-existing from the earlier frozen Body Systems milestone, 681 insertions / 107 deletions total |
| Untracked files | frozen Body Systems backend/frontend/test files + the 6 validation/requirement docs created this session (listed in prior reports) |
| Active worktrees | 12 total (listed in full; includes `sns-emr` main checkout at `origin/main`, several `suasonns-*` feature worktrees, and `sns-governance-clean`) |

**Classification: CLOSED-PR LINEAGE + HISTORICALLY STALE (51 behind main).**
Not `SAFE FEATURE LINEAGE`. This branch is a closed-PR branch that has not tracked `main` for 51
commits, carrying a large pre-existing uncommitted diff from the frozen Body Systems milestone.

Per instruction, branch history is **not** resolved in this task. Requirements for a later isolation
instruction:
- A Stage 2B implementation target should be a **new worktree/branch cut from current `origin/main`
  HEAD** (`e565797...`), not this branch, so the foundation work lands on current, mergeable history.
- The pre-existing uncommitted Body Systems diff and the 6 docs created this session must be
  explicitly triaged (ported deliberately, or left on this branch) — they must not be silently
  dropped or silently carried forward by an automated branch switch.
- This branch remains appropriate for **documentation/design-record work only** (as performed here),
  not for new schema/model/API changes.

---

## 2. Requirement Authority Classification

| Item | Classification |
|---|---|
| Draft Workspace | SNS PRODUCT POLICY |
| Finalization (Finalized/Pending-Signature state) | PROPOSED TECHNICAL DESIGN — not yet locked |
| Authentication/signature | SNS OPERATIONAL POLICY implementing a BINDING CALIFORNIA REQUIREMENT (authenticated clinical entries) |
| Signed-record immutability | SNS OPERATIONAL POLICY implementing a BINDING CALIFORNIA REQUIREMENT |
| Corrections | BINDING CALIFORNIA REQUIREMENT (reason, discovery date, correction date, authenticated correction, 48-hour requirement after discovery) |
| Amendments | SNS PRODUCT POLICY (CA text does not mandate "amendment" terminology, only traceable authenticated correction) |
| Addenda | BINDING CALIFORNIA REQUIREMENT (distinct, traceable, dated, authenticated) |
| Quality Review (the engine/workflow as designed here) | SNS PRODUCT POLICY — no CA or federal rule mandates this specific engine or a QA title/department |
| Self-review / Independent review / Second review | SNS PRODUCT POLICY — defaults are an UNRESOLVED DECISION (see §11) |
| Medicare Non-Covered Items Review | SNS OPERATIONAL POLICY implementing MEDICARE/CMS GUIDANCE (hospice election addendum, CMS-1851-F) |
| Election-addendum furnishing (5-day/3-day clocks) | BINDING FEDERAL REQUIREMENT |
| Recertification (the physician act) | BINDING FEDERAL REQUIREMENT; the *internal SNS review step* around it is SNS OPERATIONAL POLICY |
| Benefit-period linkage | BINDING FEDERAL REQUIREMENT (CMS hospice benefit-period construct) |
| Body Systems ownership (Patient→Assessment) | PROPOSED TECHNICAL DESIGN |

SNS policy is not presented as law anywhere above; items without a binding citation are explicitly
labeled SNS PRODUCT/OPERATIONAL POLICY.

---

## 3. Record-Lifecycle Decision Record — **OPEN, PENDING PRODUCT APPROVAL**

### A. Draft
Saved, recoverable, editable, never presented as an authenticated legal-record version.
Retention period, access rules, and legal-hold/discovery treatment: **OPEN — PENDING APPROVAL.**

### B. Finalized / Pending Signature
Each of the following is **OPEN — PENDING APPROVAL** (no answer assumed):
ordinary editability · return-to-draft authority/required reason · chart visibility · legal-record
classification · QA visibility · timeout/expiration · RecordVersion creation at this step · audit
events emitted.

### C. Signed / Authenticated
Locked requirements (not open — these are the binding-requirement floor): exact author, date/time,
credentials when applicable, immutable authenticated version, ordinary editing blocked, traceable
correction/amendment/addendum only, exact `RecordVersion` snapshot taken at authentication.

### D. Correction (California controls — locked, binding)
Original authenticated content preserved · reason for alteration · date of discovery · date of
correction · correction authentication · completion within the applicable 48-hour requirement after
discovery · full audit history.

### E. Addendum (locked, binding)
Distinct from the original entry · linked to the original record · traceable · dated · authenticated ·
original record preserved.

---

## 4. Quality Review Modes — Normalized Design (PROPOSED)

Reject a single overloaded `review_kind` enum. Use three independent dimensions instead:

- **`review_timing`**: `PRE_AUTHENTICATION` | `POST_AUTHENTICATION`
- **`reviewer_relationship`**: `SELF` | `INDEPENDENT` | `SUPERVISORY`
- **`review_purpose`**: `DOCUMENTATION_SUPPORT` | `QUALITY_AUDIT` | `RETROSPECTIVE_AUDIT`

These are mutually independent dimensions, not states of one enum — e.g. a record can be
`PRE_AUTHENTICATION` + `SELF` + `DOCUMENTATION_SUPPORT` (clinician self-check before signing) or
`POST_AUTHENTICATION` + `INDEPENDENT` + `QUALITY_AUDIT` (Assistant DPCS post-signature review).

Mode rules (locked, not open):
- **Mode A (pre-authentication):** record stays Draft/Finalized-Pending-Signature; reviewer comments
  are separate from the clinician's content; reviewer cannot authenticate for the clinician; this is
  not post-authentication correction history.
- **Mode B (post-authentication):** reviewer cannot alter signed content; findings are separate and
  version-specific; resolution uses the correction/amendment/addendum path; `Quality Approved`
  applies to the exact reviewed version only.

---

## 5. Quality-Status Normalization (PROPOSED)

- `REVIEW_COMPLETED`: reviewer finished the review pass, but findings/closure conditions may remain
  open. **Non-terminal** unless there are zero blocking findings.
- `APPROVED`: all required review conditions satisfied, zero blocking findings remain. **Terminal.**

Full states: `NOT_ROUTED, PENDING_REVIEW, IN_REVIEW, FOLLOW_UP_REQUIRED, RESUBMITTED,
REVIEW_COMPLETED, APPROVED, ESCALATED` (+ `CANCELED` only if an existing repository convention
requires a cancel path — **OPEN**, no such convention found yet).

Transition-matrix skeleton (capability / required fields / blocking-condition columns to be filled in
during Stage 2B service design, not before — enums must not be created until this matrix is approved):

| From | To | Capability required |
|---|---|---|
| NOT_ROUTED | PENDING_REVIEW | system routing (policy-driven) or `quality_review_assign` |
| PENDING_REVIEW | IN_REVIEW | `quality_review_claim` or `quality_review_assign` |
| IN_REVIEW | REVIEW_COMPLETED | `quality_review_complete` |
| REVIEW_COMPLETED | APPROVED | `quality_review_resolve` (zero blocking findings) |
| REVIEW_COMPLETED | FOLLOW_UP_REQUIRED | `quality_review_request_follow_up` (≥1 blocking finding) |
| FOLLOW_UP_REQUIRED | RESUBMITTED | clinician correction/amendment/addendum linked |
| RESUBMITTED | IN_REVIEW | `quality_review_claim`/`quality_review_assign` (reviewer re-opens) |
| any non-terminal | ESCALATED | `quality_review_escalate` |

---

## 6. QualityReview Data Contract

**A. Referential integrity — adopt the instruction's preferred approach:**
`QualityReview` references `RecordVersion` as the authoritative reviewed object (FK to
`record_versions.id`). Any `source_record_type`/`source_record_id` fields are denormalized
read-conveniences only, service-validated against the referenced `RecordVersion` row, never a
substitute for the FK.

**B. Tenant/patient consistency** — enforced at the service layer (not achievable as a cross-table DB
constraint across polymorphic families): every write path must assert
`QualityReview.tenant_id == RecordVersion.tenant_id`, `QualityReview.patient_id == <resolved from
source record>`, and the same for `Task`/`QualityFinding` rows created against it. **OPEN — PENDING
APPROVAL** of exactly which service function owns this assertion (proposed: a single
`quality_review_service.assert_consistency()` called by every mutating entry point).

**C. Deletion** — no hard delete of `QualityReview`/`QualityFinding`. Findings are withdrawn
(status transition), not deleted. Retention/legal-hold behavior: **OPEN — PENDING APPROVAL.**

**D. PHI minimization** — no clinical narrative text copied into `QualityReview`, `QualityFinding`,
`Task`, `AuditLog`, or `GuardrailPolicy`; only IDs, enums, and short administrative text (e.g. a
finding's `source_section`/`source_field` label, not quoted clinical content).

---

## 7. QualityFinding Contract

Controlled (CHECK-constrained) string sets, not free text — mirroring the existing
`RnicaAmendment.AMENDMENT_CATEGORIES`/`AMENDMENT_REASON_CODES` pattern already in the repo:
`category`, `severity`, `finding_status`, `escalation_status`, `resolution_type` are all fixed
vocabularies to be enumerated during Stage 2B, not invented here.

Blocking-vs-non-blocking: a finding blocks `APPROVED` iff `severity` is in the tenant-configured
blocking-severity set AND `finding_status` is not in `{VERIFIED, WITHDRAWN}`.

Allowed finding actions: withdrawn, reopened. **Merged/duplicated/superseded: OPEN — PENDING
APPROVAL** (no existing repository pattern for finding-level merge was found).

No finding record may alone constitute an eligibility/certification/coverage/coding/compliance/survey
conclusion.

---

## 8. Task / QualityReview State Ownership (PROPOSED, per instruction's preferred ownership)

- **`Task`** owns assignment, claim, due date, SLA, escalation.
- **`QualityReview`** owns the clinical quality-review state/outcome.
- **`QualityFinding`** owns deficiencies and resolution verification.

Locked transactional mappings: `Task CLAIMED` ⇔ `QualityReview IN_REVIEW` (same transaction);
`Task COMPLETED` only once `QualityReview` reaches `APPROVED`/`REVIEW_COMPLETED`/`ESCALATED`;
follow-up `Task` completion never auto-resolves a `QualityFinding` (clinician action required).
Transaction boundaries/idempotency keys/reconciliation-job design: **OPEN — PENDING APPROVAL**,
deferred to Stage 2B service design.

---

## 9. Tenant Policy Contract (GuardrailPolicy reuse)

Proposed policy-key namespace: `QUALITY_REVIEW.<KEY>` (e.g. `QUALITY_REVIEW.DOCUMENT_TYPES_REQUIRED`,
`QUALITY_REVIEW.SELF_REVIEW_ALLOWED`). Each key's `value` JSONB validated against a typed schema
(Pydantic model) before write — **OPEN — PENDING APPROVAL** of the schema-versioning mechanism
(proposed: a `schema_version` field inside each policy value, validated by key-specific model at read
time).

**Fail-closed defaults (locked, not open):** no reviewer access unless explicitly granted · no
self-review auto-approval · no silent second-review bypass · no cross-location/program expansion ·
QA requirement never silently disabled. Malformed policy is treated as **deny**, never as "permission
granted."

---

## 10. Capability and Role Rules

Reaffirms the already-correct existing `app/core/capabilities.py` design. New `quality_review_*`
capabilities get **zero default role grants** except the existing `QA_REVIEWER`/`QA_MANAGER`
(view/report only, per current `ROLE_CAPABILITIES`). Per-tenant grants to DPCS, Assistant DPCS,
Clinical Manager, Case Manager, etc. are made exclusively through the `GuardrailPolicy` overlay
described in §9 — never a code-level blanket grant. A reviewer-role *display* snapshot, if retained,
is explicitly non-authoritative and never substitutes for a live capability check.

---

## 11. Self-Review Decision — Locked Defaults

Per your explicit "Lock this default" direction and endorsement:
- Clinician pre-finalization self-check: allowed, not Quality Approval.
- Post-authentication self-review: recorded as `Self-Review`, never labeled `Independent Review`.
- Self-review does not satisfy independent review by default.
- No broad Case Manager self-review grant exists by default.
- Tenant policy may permit self-review for selected low-risk documents; high-risk documents may
  require independent/supervisory review.

Policy matrix (document type × risk category × review timing × self-review-allowed ×
independent-required × second-reviewer-required × escalation threshold): **OPEN — PENDING APPROVAL.**
No document-type/risk-category taxonomy exists in the repository yet to populate this matrix: this is
a genuine new product decision, not a discoverable repository fact.

---

## 12. Correction/Amendment/Addendum Boundary — Option A (recommended)

Repository evidence supports Option A: a document-family-registration interface
(`source_record_type` → registered correction handler), because `RnicaAmendment` already demonstrates
the exact shape needed (category/reason-code vocab, snapshot-before/proposed-after, request source
including `INTERNAL_QA`, PENDING→APPROVED/DENIED). Stage 2B would generalize this into a thin
registration contract rather than a single generic table, and explicitly report any document family
with no registered handler as **UNSUPPORTED** (not silently allowed). `ElectionAddendumRequest`/
`ElectionAddendumDetermination` remain scoped to the Medicare non-covered-items purpose only and are
never reused as the general clinical addendum mechanism.

California controls carried into the contract (locked): written explanation for altered entries,
authenticated correction, discovery/correction dates retained, 48-hour correction window, addenda
distinct/traceable/dated/authenticated.

---

## 13. CMS Certification Boundary (locked constraints)

The quality workflow must never: certify or recertify terminal illness, substitute for physician
certification, alter the physician narrative, approve a plan of care on the physician's behalf,
produce an automatic eligibility result, or convert LCD criteria into a pass/fail determination. QA
may surface a documentation gap only. The UI must visually distinguish quality-review completion,
clinician authentication, physician certification/recertification, plan-of-care approval, and
Medicare-addendum furnishing as four separate concepts.

---

## 14. Migration Rollout Plan (phases, not executed in Stage 2A)

Phase A (nullable additive columns/tables) → B (dual-read compatibility code) → C (deterministic
backfill with reconciliation report) → D (row/orphan validation) → E (non-null/uniqueness/check
constraints after validation) → F (retire legacy writes after dual-read verification). The Stage 1
proposed column/table list stands as the Phase-A candidate set; no migration file is created in this
stage.

---

## 15. Initial Comprehensive Assessment Uniqueness — **OPEN, PENDING APPROVAL**

Cannot be finalized until §3-B (Finalized/Pending-Signature semantics) is locked, since "which
statuses count as an active authoritative Initial assessment" depends on it. Candidate shape: a
partial unique index on `(patient_id, admission_id)` filtered to the approved "active" status set —
explicitly deferred until that status set is approved, to avoid blocking legitimate readmissions or
treating abandoned drafts as permanent blockers.

---

## 16. Body Systems Migration Boundary

`body_systems_assessments` already has `signed_at`/`signed_by`/`version` — not duplicated. Proposed
(deferred) linkage: nullable `assessment_id` FK during a compatibility period, orphan report before
any non-null transition, patient/admission consistency validation, current dev DB confirmed at **0
rows** as of the Stage 1 check (must be revalidated immediately before any future migration run, not
assumed to still hold). Body Systems clinical-detail implementation remains frozen; this stage designs
linkage only, and no linkage migration is created here.

---

## 17. Real-Data / Development-Patient Gate

**Do not use the three existing development patients for any QA-workflow test or screenshot until** an
explicit checklist is confirmed by the product owner: organizational authorization, test purpose,
minimum-necessary fields, isolated environment, dedicated account, encryption, audit logging,
screenshot/export/backup restrictions, rollback plan, retention period, cleanup/disposal, post-test
verification. **Default for Stage 2B testing: synthetic/de-identified data**, until that checklist is
explicitly confirmed. No patient identifiers/narratives/screenshots will be placed in GitHub reports
or this conversation regardless.

---

## 18. Threat Model (summary)

| Threat | Control |
|---|---|
| Privilege escalation via policy JSON | schema-validated policy, fail-closed on invalid value |
| Self-review bypass | reviewer-relationship is a separate field, never inferred from role/title |
| Queue-claim race | atomic claim (DB-level conditional update), audited |
| Cross-tenant/cross-patient access | service-layer consistency assertion (§6-B) on every mutation |
| Reviewer-author conflict | author-exclusion check in reviewer-eligibility gate |
| Forged RecordVersion linkage | FK + service assertion, no client-supplied version acceptance without validation |
| Stale review approval / concurrency | version/concurrency token on `QualityReview`/`QualityFinding` |
| PHI leakage into Task/AuditLog | §6-D minimization rule |
| Policy downgrade / deletion abuse | no hard delete (§6-C), audited withdrawal only |

Full control/test/monitoring mapping per threat is Stage 2B work, not produced here.

---

## 19. Observability (deferred list)

Overdue review / overdue clinician-response / unassigned-queue / no-eligible-reviewer /
Task-vs-QualityReview divergence / orphaned RecordVersion link / failed escalation / policy-validation
error / authorization-denial / concurrency-conflict / correction-deadline / QA-turnaround /
self-review-vs-independent-review metrics — to be built in Stage 2B, none built now.

---

## 20. Terminology & Accessibility (locked, reaffirmed)

User-facing term: **Quality Review**. Workflow actor: **Authorized Reviewer**. "QA Nurse" is never
required or displayed as the only reviewer identity; reviewer name/org role may be shown where
authorized, but access is capability-based. All status indicators (including any color/icon) must be
accompanied by text (e.g. a green icon must say "Quality Approved"; a yellow icon must say "Pending
Quality Review" or the applicable text) — never color alone.

---

## Summary for product approval

**Locked (no further approval needed to proceed to Stage 2B design on these points):** §3-C, §3-D,
§3-E, §4 mode rules, §5 REVIEW_COMPLETED/APPROVED distinction, §6-A/§6-D, §9 fail-closed defaults,
§10, §11 top-level defaults, §12 California controls, §13, §20.

**OPEN — require explicit product approval before Stage 2B implementation:**
1. §1 — branch/worktree target for Stage 2B (recommend fresh branch from `origin/main`).
2. §3-B — Finalized/Pending-Signature full behavior.
3. §5 — final state-transition matrix (required fields/blocking conditions per transition).
4. §6-B/§8 — exact service ownership/transaction design (names only proposed here).
5. §7 — controlled vocabularies for findings; merge/duplicate/supersede support.
6. §9 — policy schema-versioning mechanism.
7. §11 — document-type/risk-category self-review policy matrix.
8. §15 — Initial Comprehensive Assessment uniqueness rule (blocked on #2).
9. §17 — development-patient test-data authorization checklist.

No code, migration, model, API, frontend component, or test was created. Nothing staged, committed,
or pushed. Awaiting your decisions on the 9 open items above before Stage 2B begins.
