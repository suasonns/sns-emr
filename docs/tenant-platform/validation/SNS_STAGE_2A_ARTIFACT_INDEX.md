# SNS Stage 2A Artifact Index

Status: project-governance record. Lists and classifies every governance, requirements, design,
decision, and compliance artifact produced or received during the Stage 2A design-hardening effort.
These artifacts are now governing references for Stage 2B: future work must reference them rather than
re-deciding or duplicating their content outside this index.

No implementation artifact (migration, model, API, service, route, frontend, test, seed, or generated
code) is included in this index as eligible for any documentation-preservation commit.

---

## 0. Final Artifact Inventory (authoritative catalog)

Verification performed this turn: every row below was confirmed to (a) exist on disk, (b) be tracked
by git (`git ls-files --error-unmatch`), and (c) trace to the exact commit hash that introduced it
(`git log --follow --diff-filter=A`). All 13 artifacts returned `exists: True`, `tracked: yes`, and
introducing commit `9632a40b` (the artifact index itself was additionally updated in `58a44034`).

| Artifact ID | Artifact Name | Purpose | Authority Classification | Status | Repository Path | Owner | Stage | Last Updated | Supersedes | Superseded By | Implementation Blocking? | Approval Required? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ART-001 | `SNS_AUTHORITY_CLASSIFICATION_MATRIX.md` | Authority classification and compliance traceability baseline | Governance baseline (source document) | Governing | `docs/tenant-platform/validation/SNS_AUTHORITY_CLASSIFICATION_MATRIX.md` | Product/Compliance (external author; repo-preserved by this session) | Stage 2A | Introduced `9632a40b` (2026-10-08) | None | None | No (classification only) | N/A — this is the approval-source document | Controls over informal classifications in ART-002 wherever they differ |
| ART-002 | `SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md` | Stage 2A design-hardening contract | Proposed Technical Design / SNS Product Policy (mixed, see ART-003 delta log) | Governing, partially superseded by ART-001 classifications | `docs/tenant-platform/validation/SNS_SCALABLE_QA_STAGE_2A_DESIGN_CONTRACT.md` | This session (Copilot) | Stage 2A | Introduced `9632a40b` (2026-10-08) | None | Partially superseded by ART-001 (see ART-003) | Yes — design-only, no code, but its 9 OPEN items block Stage 2B | Yes — 9 explicit OPEN items, tracked as ART-005 rows | |
| ART-003 | `SNS_STAGE_2A_RECONCILIATION_AND_READINESS_REPORT.md` | Authority reconciliation and readiness analysis | Governance/readiness record | Governing | `docs/tenant-platform/validation/SNS_STAGE_2A_RECONCILIATION_AND_READINESS_REPORT.md` | This session (Copilot) | Stage 2A | Introduced `9632a40b` (2026-10-08) | None | None | No — report only | N/A — report itself requires no approval; its contents point to ART-005 | |
| ART-004 | `SNS_STAGE_2B_IMPLEMENTATION_READINESS_SCORECARD.md` | Implementation readiness gating | Governance/readiness record | Governing; overall gate **BLOCKED** | `docs/tenant-platform/validation/SNS_STAGE_2B_IMPLEMENTATION_READINESS_SCORECARD.md` | This session (Copilot) | Stage 2A→2B gate | Introduced `9632a40b` (2026-10-08) | 14-domain scorecard in `SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` §14 | None | Yes — gating artifact | N/A — scoring artifact; underlying blockers require approval per ART-005 | |
| ART-005 | `SNS_STAGE_2B_UNRESOLVED_DECISIONS_APPROVAL_MATRIX.md` | Decision approval tracking | Decision record | Governing; all 30 rows **NOT STARTED** | `docs/tenant-platform/validation/SNS_STAGE_2B_UNRESOLVED_DECISIONS_APPROVAL_MATRIX.md` | This session (Copilot) | Stage 2A→2B gate | Introduced `9632a40b` (2026-10-08) | None | None | Yes — blocks all Stage 2B code | Yes — every row requires its own named approver (product/legal/architecture/privacy per row) | |
| ART-006 | `SNS_STAGE_2A_ARTIFACT_INDEX.md` (this file) | Master inventory of all Stage 2A governance artifacts | Governance index | Governing | `docs/tenant-platform/validation/SNS_STAGE_2A_ARTIFACT_INDEX.md` | This session (Copilot) | Stage 2A | Introduced `9632a40b`; updated `58a44034` (2026-10-08) | Earlier pre-register version of this same file | None | No — index only | N/A | |
| ART-007 | `SNS_DRAFT_WORKSPACE_VALIDATION.md` | Validates draft-vs-legal-record behavior with repository evidence only | Validation record (feeds ART-001/ART-003 classifications) | Supporting evidence | `docs/tenant-platform/validation/SNS_DRAFT_WORKSPACE_VALIDATION.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | None | No — analysis only | No | Referenced by ART-003 §4 ("Draft Workspace authority") |
| ART-008 | `SNS_SIGNED_RECORD_IMMUTABILITY_VALIDATION.md` | Validates lock/sign/amendment/correction/addendum current behavior | Validation record | Supporting evidence | `docs/tenant-platform/validation/SNS_SIGNED_RECORD_IMMUTABILITY_VALIDATION.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | None | No — analysis only | No | Referenced by ART-003 §4 ("Authenticated-record immutability") |
| ART-009 | `SNS_QA_WORKFLOW_VALIDATION.md` | Validates current QA/correction separation and clinician-authorship evidence | Validation record | Supporting evidence | `docs/tenant-platform/validation/SNS_QA_WORKFLOW_VALIDATION.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | None | No — analysis only | No | Referenced by ART-003 §4 ("Federal QAPI distinction") |
| ART-010 | `SNS_ASSESSMENT_LIFECYCLE_VALIDATION.md` | Validates Initial/Update/Recertification assessment model and uniqueness evidence | Validation record | Supporting evidence | `docs/tenant-platform/validation/SNS_ASSESSMENT_LIFECYCLE_VALIDATION.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | None | No — analysis only | No | Referenced by ART-003 §4 ("Initial Comprehensive uniqueness", D-018) |
| ART-011 | `SNS_BODY_SYSTEMS_LIFECYCLE_VALIDATION.md` | Validates current Body Systems ownership (`Patient -> BodySystemsAssessment`, no sign/finalize path) | Validation record | Supporting evidence | `docs/tenant-platform/validation/SNS_BODY_SYSTEMS_LIFECYCLE_VALIDATION.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | None | No — analysis only | No | Referenced by ART-003 §4 ("Body Systems ownership", D-025) |
| ART-012 | `SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` | Delta report, resolved-decision recommendations, earlier 5-phase branch strategy, authority-validation table, 14-domain scorecard | Readiness record | Superseded in granularity by ART-003/ART-004; content not retracted | `docs/tenant-platform/validation/SNS_SCALABLE_QA_IMPLEMENTATION_READINESS_REPORT.md` | This session (Copilot) | Stage 2A input | Introduced `9632a40b` (2026-10-08) | None | Scorecard section superseded by ART-004; branch-strategy section superseded by ART-003 §13 | No — report only | N/A | |
| ART-013 | `SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md` (+ §10 amendment) | Locks clinician-facing "Comprehensive RN Assessment" terminology; confirms `UPDATE`/`RECERT` map without migration | SNS Product Policy | Governing | `docs/tenant-platform/SNS_UPDATE_ASSESSMENT_VS_RECERTIFICATION_REQUIREMENT.md` | Product (amended by this session per instruction) | Stage 2A input/requirement | Introduced `9632a40b` (2026-10-08); §10 amendment carried in same commit | Earlier pre-amendment version (not separately preserved) | None | No — terminology/document only | Partially — toggle *behavior* (non-terminology) remains Unresolved per D-002/D-003 | |

No additional Stage 2A governance artifact was discovered during this review beyond the 13 rows above.

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
