# SNS Stage 2A Artifact Index

Status: documentation-preservation artifact. Lists and classifies every governance, requirements,
design, and compliance artifact produced or received during the Stage 2A design-hardening effort, and
the repository-review required before staging any of them for commit. No implementation artifact is
included in this index as eligible for this commit.

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
