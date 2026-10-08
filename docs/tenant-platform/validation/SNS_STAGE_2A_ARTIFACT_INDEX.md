# SNS Stage 2A Artifact Index

Status: project-governance record. Lists and classifies every governance, requirements, design,
decision, and compliance artifact produced or received during the Stage 2A design-hardening effort.
These artifacts are now governing references for Stage 2B: future work must reference them rather than
re-deciding or duplicating their content outside this index.

No implementation artifact (migration, model, API, service, route, frontend, test, seed, or generated
code) is included in this index as eligible for any documentation-preservation commit.

---

## 0. Governance Artifact Register

| Artifact ID | Artifact Name | Purpose | Stage | Owner | Authority Classification | Status | Repository Path | Created Date | Last Updated | Supersedes | Superseded By | Implementation Impact | Approval Required | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GOV-A | Authority Classification Matrix | Citation-backed baseline classifying every requirement as Binding Federal/CA, CMS guidance, SNS Product/Operational Policy, Proposed Technical Design, Unresolved Decision, or Prohibited Product Boundary | Stage 2A | Product/Compliance (external author, repo-preserved by this session) | Governance baseline (source document) | Active — governing reference | `docs/tenant-platform/validation/SNS_AUTHORITY_CLASSIFICATION_MATRIX.md` | 2026-10-08 (date preserved into repo) | 2026-10-08 | None | None | None (classification only) | N/A — this is the approval-source document | Controls over informal classifications in GOV-B §2 wherever they differ |
| GOV-B | Stage 2A Design Contract | 20-section design-hardening contract covering lifecycle, QA data model, tenant policy, correction/amendment, CMS boundary, terminology | Stage 2A | This session (Copilot) | Proposed Technical Design / SNS Product Policy (mixed, see GOV-C delta log) | Active — governing reference, partially superseded by GOV-A classifications | `docs/tenant-platform/validation/SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md` | prior session turn | prior session turn | None | Partially superseded by GOV-A (see GOV-C) | Design-only; no code | Yes — 9 explicit OPEN items, now tracked as GOV-E rows |
| GOV-C | Stage 2A Reconciliation & Readiness Report | Governance checkpoint, lineage classification, authority-matrix reconciliation, delta log, blockers, 7-phase branch strategy, 22-point final report | Stage 2A | This session (Copilot) | Governance/readiness record | Active — governing reference | `docs/tenant-platform/validation/SNS_STAGE_2A_RECONCILIATION_AND_READINESS_REPORT.md` | prior session turn | prior session turn | None | None | Report only; no code | N/A — report itself requires no approval, but its contents point to GOV-E |
| GOV-D | Stage 2B Implementation Readiness Scorecard | 42-domain gate-based (not averaged) readiness scorecard with evidence citations | Stage 2A→2B gate | This session (Copilot) | Governance/readiness record | Active — governing reference; overall gate **BLOCKED** | `docs/tenant-platform/validation/SNS_STAGE_2B_IMPLEMENTATION_READINESS_SCORECARD.md` | prior session turn | prior session turn | 14-domain scorecard in `SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` §14 | None | Scorecard only; no code | N/A — scoring artifact; underlying blockers require approval per GOV-E |
| GOV-E | Stage 2B Unresolved Decisions Approval Matrix | 30-item (D-001–D-030) decision register, each with required approver | Stage 2A→2B gate | This session (Copilot) | Decision record | Active — governing reference; all 30 rows **NOT STARTED** | `docs/tenant-platform/validation/SNS_STAGE_2B_UNRESOLVED_DECISIONS_APPROVAL_MATRIX.md` | prior session turn | prior session turn | None | None | None; blocks all Stage 2B code | Yes — every row requires its own named approver (product/legal/architecture/privacy per row) |
| GOV-F | Stage 2A Artifact Index (this file) | Inventory, placement plan, and register of all Stage 2A governance artifacts | Stage 2A | This session (Copilot) | Governance index | Active — governing reference | `docs/tenant-platform/validation/SNS_STAGE_2A_ARTIFACT_INDEX.md` | this turn | this turn | Earlier version of this same file (pre-register section) | None | Index only; no code | N/A |
| GOV-G | Draft Workspace Validation | Validates draft-vs-legal-record behavior with repository evidence only | Stage 2A input | This session (Copilot) | Validation record (feeds GOV-A/GOV-C classifications) | Active — supporting evidence | `docs/tenant-platform/validation/SNS_DRAFT_WORKSPACE_VALIDATION.md` | earlier session turn | earlier session turn | None | None | None | No — analysis only | Referenced by GOV-C §4 ("Draft Workspace authority") |
| GOV-H | Signed Record Immutability Validation | Validates lock/sign/amendment/correction/addendum current behavior | Stage 2A input | This session (Copilot) | Validation record | Active — supporting evidence | `docs/tenant-platform/validation/SNS_SIGNED_RECORD_IMMUTABILITY_VALIDATION.md` | earlier session turn | earlier session turn | None | None | None | No — analysis only | Referenced by GOV-C §4 ("Authenticated-record immutability") |
| GOV-I | QA Workflow Validation | Validates current QA/correction separation and clinician-authorship evidence | Stage 2A input | This session (Copilot) | Validation record | Active — supporting evidence | `docs/tenant-platform/validation/SNS_QA_WORKFLOW_VALIDATION.md` | earlier session turn | earlier session turn | None | None | None | No — analysis only | Referenced by GOV-C §4 ("Federal QAPI distinction") |
| GOV-J | Assessment Lifecycle Validation | Validates Initial/Update/Recertification assessment model and uniqueness evidence | Stage 2A input | This session (Copilot) | Validation record | Active — supporting evidence | `docs/tenant-platform/validation/SNS_ASSESSMENT_LIFECYCLE_VALIDATION.md` | earlier session turn | earlier session turn | None | None | None | No — analysis only | Referenced by GOV-C §4 ("Initial Comprehensive uniqueness", D-018) |
| GOV-K | Body Systems Lifecycle Validation | Validates current Body Systems ownership (`Patient -> BodySystemsAssessment`, no sign/finalize path) | Stage 2A input | This session (Copilot) | Validation record | Active — supporting evidence | `docs/tenant-platform/validation/SNS_BODY_SYSTEMS_LIFECYCLE_VALIDATION.md` | earlier session turn | earlier session turn | None | None | None | No — analysis only | Referenced by GOV-C §4 ("Body Systems ownership", D-025) |
| GOV-L | Update Assessment vs. Recertification Requirement (+ §10 terminology amendment) | Locks clinician-facing "Comprehensive RN Assessment" terminology; confirms `UPDATE`/`RECERT` map without migration | Stage 2A input/requirement | Product (amended by this session per instruction) | SNS Product Policy | Active — governing reference | `docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md` | earlier session turn | earlier session turn (§10 amendment) | Earlier pre-amendment version (not separately preserved) | None | None; terminology/document only | Partially — toggle *behavior* (non-terminology) remains Unresolved per D-002/D-003 |
| GOV-M | Scalable QA Implementation Readiness Report | Delta report, resolved-decision recommendations, earlier 5-phase branch strategy, authority-validation table, 14-domain scorecard | Stage 2A input | This session (Copilot) | Readiness record | Active — superseded in granularity by GOV-D/GOV-C, content not retracted | `docs/tenant-platform/validation/SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` | earlier session turn | earlier session turn | None | Scorecard section superseded by GOV-D; branch-strategy section superseded by GOV-C §13 | Report only; no code | N/A |

---

## 1. Repository Review — Untracked Files (full list, pre-commit)

```
?? backend/alembic/versions/b0d7sy5t3m5_create_body_systems_tables.py
?? backend/app/api/routes/body_systems.py
?? backend/app/models/body_systems.py
?? backend/tests/test_body_systems_api.py
?? backend/tests/test_body_systems_authorization_and_integrity.py
?? backend/tests/test_body_systems_models.py
?? docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md
?? docs/tenant-platform/validation/
?? sns-emr-frontend/scripts/fix-gi-overview-restore.mjs
?? sns-emr-frontend/scripts/gi-audit-output/
?? sns-emr-frontend/scripts/gi-density-audit.mjs
?? sns-emr-frontend/src/App.devPreviewRoute.test.ts
?? sns-emr-frontend/src/api/bodySystems.ts
?? sns-emr-frontend/src/components/rn-ica/BodySystemShell.css
?? sns-emr-frontend/src/components/rn-ica/BodySystemShell.jsx
?? sns-emr-frontend/src/components/rn-ica/BodySystemShell.test.jsx
?? sns-emr-frontend/src/domain/body-systems/respiratoryFieldInventory.test.ts
?? sns-emr-frontend/src/domain/body-systems/respiratoryFieldInventory.ts
?? sns-emr-frontend/src/domain/body-systems/respiratoryWorkflowRules.test.ts
?? sns-emr-frontend/src/domain/body-systems/respiratoryWorkflowRules.ts
?? sns-emr-frontend/src/features/body-systems/
```

`docs/tenant-platform/validation/` expands to the 11 files enumerated in §3 below plus this index
file (12 total after this task).

## 2. Repository Review — Modified (Tracked) Files

```
 M backend/app/api/registry.py
 M backend/app/models/__init__.py
 M sns-emr-frontend/src/App.tsx
 M sns-emr-frontend/src/components/RNICA.jsx
 M sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.css
 M sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.jsx
 M sns-emr-frontend/tailwind.config.js
```

All 7 modified files are part of the frozen Body Systems/Respiratory implementation milestone from an
earlier phase of this session, pending separate product review. **None are eligible for this
documentation-preservation commit.**

## 3. Classification of Every Artifact

| Path | Category | Eligible for this commit? | Recommended final location |
|---|---|---|---|
| `docs/tenant-platform/validation/SNS_AUTHORITY_CLASSIFICATION_MATRIX.md` | Governance / compliance artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md` | Design artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_STAGE_2A_RECONCILIATION_AND_READINESS_REPORT.md` | Governance / readiness artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_STAGE_2B_IMPLEMENTATION_READINESS_SCORECARD.md` | Readiness/gate artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_STAGE_2B_UNRESOLVED_DECISIONS_APPROVAL_MATRIX.md` | Decision-record / approval artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_DRAFT_WORKSPACE_VALIDATION.md` | Validation artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_SIGNED_RECORD_IMMUTABILITY_VALIDATION.md` | Validation artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_QA_WORKFLOW_VALIDATION.md` | Validation artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_ASSESSMENT_LIFECYCLE_VALIDATION.md` | Validation artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_BODY_SYSTEMS_LIFECYCLE_VALIDATION.md` | Validation artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` | Readiness/requirements artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/validation/SNS_STAGE_2A_ARTIFACT_INDEX.md` (this file) | Governance index artifact | Yes | `docs/tenant-platform/validation/` (already correct) |
| `docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md` | Requirements artifact (with locked terminology amendment) | Yes | `docs/tenant-platform/` (already correct) |
| `backend/alembic/versions/b0d7sy5t3m5_create_body_systems_tables.py` | Implementation artifact (migration) | **No** | Stays untracked pending Body Systems product review |
| `backend/app/api/routes/body_systems.py` | Implementation artifact (API) | **No** | Stays untracked pending Body Systems product review |
| `backend/app/models/body_systems.py` | Implementation artifact (model) | **No** | Stays untracked pending Body Systems product review |
| `backend/tests/test_body_systems_*.py` (3 files) | Implementation artifact (tests) | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/src/api/bodySystems.ts` | Implementation artifact (API client) | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/src/components/rn-ica/BodySystemShell.*` (3 files) | Implementation artifact (frontend) | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/src/domain/body-systems/*` (4 files) | Implementation artifact (domain logic + tests) | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/src/features/body-systems/` | Implementation artifact (feature dir) | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/scripts/fix-gi-overview-restore.mjs`, `gi-density-audit.mjs`, `gi-audit-output/` | Implementation/tooling artifact | **No** | Stays untracked pending Body Systems product review |
| `sns-emr-frontend/src/App.devPreviewRoute.test.ts` | Implementation artifact (test) | **No** | Stays untracked pending Body Systems product review |
| `backend/app/api/registry.py` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |
| `backend/app/models/__init__.py` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |
| `sns-emr-frontend/src/App.tsx` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |
| `sns-emr-frontend/src/components/RNICA.jsx` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |
| `sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.css/.jsx` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |
| `sns-emr-frontend/tailwind.config.js` (modified) | Implementation artifact | **No** | Remains modified-but-uncommitted pending Body Systems product review |

## 4. Files Staged for This Commit (13 total)

1. `docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md`
2. `docs/tenant-platform/validation/SNS_ASSESSMENT_LIFECYCLE_VALIDATION.md`
3. `docs/tenant-platform/validation/SNS_AUTHORITY_CLASSIFICATION_MATRIX.md`
4. `docs/tenant-platform/validation/SNS_BODY_SYSTEMS_LIFECYCLE_VALIDATION.md`
5. `docs/tenant-platform/validation/SNS_DRAFT_WORKSPACE_VALIDATION.md`
6. `docs/tenant-platform/validation/SNS_QA_WORKFLOW_VALIDATION.md`
7. `docs/tenant-platform/validation/SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md`
8. `docs/tenant-platform/validation/SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md`
9. `docs/tenant-platform/validation/SNS_SIGNED_RECORD_IMMUTABILITY_VALIDATION.md`
10. `docs/tenant-platform/validation/SNS_STAGE_2A_ARTIFACT_INDEX.md`
11. `docs/tenant-platform/validation/SNS_STAGE_2A_RECONCILIATION_AND_READINESS_REPORT.md`
12. `docs/tenant-platform/validation/SNS_STAGE_2B_IMPLEMENTATION_READINESS_SCORECARD.md`
13. `docs/tenant-platform/validation/SNS_STAGE_2B_UNRESOLVED_DECISIONS_APPROVAL_MATRIX.md`

No `backend/`, no `sns-emr-frontend/src` implementation path, no migration, no model, no API, no
service, no route, no test, no seed data, and no generated code is included.

## 5. Files Explicitly Excluded From This Commit (remain untracked/modified)

All Body Systems implementation files and all 7 pre-existing modified tracked files listed in §1–§2
above. These remain exactly as they were before this task; this task does not stage, commit, discard,
or otherwise alter them.
