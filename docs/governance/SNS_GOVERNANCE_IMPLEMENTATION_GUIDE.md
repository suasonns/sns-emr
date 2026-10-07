# SNS Governance Implementation Guide

**Status:** Active supporting governance

**Authority level:** Process supplement, not constitutional authority
**Purpose:** Reconcile, discover, verify, and safely apply existing SNS rules without creating a competing constitution.

## 1. Constitutional model

The repository has two complementary active constitutions:

- `docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
- `docs/tenant-platform/SNS_CONSTITUTION.md`

This guide does not supersede, restate, or weaken either constitution.

### Scope allocation

| Subject | Controlling constitutional layer |
|---|---|
| Repository refresh, session gate, reuse, implementation discipline, UI verification, dependency review, migrations, Git and commit safety | Repository-First Implementation Constitution |
| Clinical and product authority, regulatory applicability, source currency, eligibility support, evidence, ownership, audit, historical patient-data safeguards, HOPE/HUV/SFV policy | SNS Constitution |
| Explicit feature behavior | Most specific active workstream authority, within constitutional limits |
| Appearance | Approved design reference, within accessibility and theme rules |
| Current implemented behavior | Verified repository implementation and tests, unless intentionally superseded by an approved product decision |

## 2. Conflict-resolution rules

1. Do not decide authority from filenames alone.
2. Identify the exact provisions, subject, scope, effective context, and repository evidence.
3. Apply each provision only within its scope.
4. A specific workstream document may add stricter rules but may not weaken patient safety, privacy, tenant isolation, clinician authority, auditability, migration safety, Git safety, or accessibility.
5. An explicit current product decision may revise product behavior but cannot override binding external authority.
6. Stop only the affected item when a direct unresolved conflict exists. Continue unaffected authorized work.
7. Record the resolution in `SNS_RULE_CONFLICT_REGISTER.md` and update affected authority documents before implementation.

## 3. Reconciled rules

### 3.1 RNICA workflow order

The Repository-First Implementation Constitution records the explicit product-authority decision dated 2026-09-22:

1. Patient Story
2. Evidence & Intake
3. Pain & Symptom Burden
4. Diagnosis & LCD
5. Functional Status
6. Body Systems
7. Caregiver & Support
8. Safety & Clinical Risk
9. ACP & Goals of Care
10. Orders & POC
11. Compliance & Readiness
12. AI Action Center
13. Finalization

The SNS Constitution records an older unresolved inversion for screens 1 and 2. For implementation, the explicit 2026-09-22 product decision controls. The SNS Constitution should be amended separately to remove the stale discrepancy. This governance package does not silently edit either constitution.

### 3.2 Session-start templates

The full Section 18 template in the Repository-First Implementation Constitution is mandatory for every implementation session. It satisfies the shorter RNICA-specific refresh intent in the SNS Constitution when every field is completed. Do not output two duplicative templates.

### 3.3 Verification vocabularies

- Use the Repository-First statuses (`VERIFIED`, `PARTIAL`, `NOT VERIFIED`, `CONFLICTING`, `NOT FOUND`, `SUPERSEDED`, `BLOCKED BY EXPLICIT DECISION`) for general repository and implementation discovery.
- Use the detailed SNS Constitution statuses for field-level end-to-end, compliance, persistence, readiness, export, audit, and historical-compatibility verification.
- `NOT FOUND` never means missing unless search scope and commit are documented.
- `NOT VERIFIED` never means optional.

### 3.4 Implementation versus reporting

The implementation-over-reporting rule does not bypass the repository-first gate. Perform the minimum investigation needed to establish authority and safety, then implement an already approved plan. Create a new report only when requested or when a true conflict, data risk, schema decision, security ambiguity, or obsolete authority blocks work.

### 3.5 Design versus behavior

Approved design references control appearance. Verified repository clinical logic controls behavior. A mockup does not authorize new clinical logic, and legacy code does not authorize ignoring an approved design. Presentation-only work must preserve clinical behavior unless an approved defect says otherwise.

### 3.6 Eligibility and clinical evidence

LCDs, disease guides, checklists, and computed summaries are supporting evidence. They are not automatic eligibility, coverage, certification, coding, legal, accreditation, or survey determinations. Final clinical judgment remains with authorized clinicians and physicians as applicable.

## 4. Governance-file roles

- `AGENTS.md`: thin entry point.
- `.github/copilot-instructions.md`: Copilot bootstrap and mandatory reads.
- `SNS_RULES_MANIFEST.json`: machine-readable discovery and CI inventory.
- `SNS_WORKTREE_PROTOCOL.md`: worktree lifecycle.
- `SNS_CLINICAL_ARCHITECTURE.md`: cross-workstream clinical architecture, not regulatory authority.
- `SNS_DATA_HANDLING_RULES.md`: operational data safeguards expanding constitutional requirements.
- verification scripts: presence, tracked-state, and preflight automation only.
- CI workflow: deterministic enforcement of required governance artifacts.

Supporting files may clarify, reference, organize, automate, and verify. They may not create constitutional policy.

## 5. Safe phased rollout

### Phase 1: Documentation and discovery

Add the entry point, Copilot instructions, guide, manifest, architecture, data-handling rules, worktree protocol, and conflict register. Validate paths and conflicts. Do not change application behavior.

### Phase 2: Local verification

Add and run the verifier, preflight, and verifier tests. Use strict mode only after files are tracked. During installation, `--allow-untracked` may be used to inspect completeness, but it is not an implementation authorization.

### Phase 3: CI advisory rollout

Add the governance workflow on pull requests and manual dispatch. Do not make it a protected-branch requirement until active branches and worktrees have adopted the governance commit.

### Phase 4: Required enforcement

After adoption, make `SNS Governance / verify-governance` a required status check. Validate branch protection separately. This repository workflow cannot configure branch protection by itself.

## 6. Verification checklist

Before governance merge:

- [ ] Both constitutions exist, are tracked, and remain unmodified unless separately authorized.
- [ ] Copilot instructions and `AGENTS.md` point to both constitutions.
- [ ] Manifest JSON parses and contains no duplicate paths.
- [ ] All mandatory paths are repository-relative, regular files, readable, and tracked.
- [ ] No path escapes the repository root.
- [ ] Verifier tests pass.
- [ ] Strict verifier passes after explicit path staging or in a committed test branch.
- [ ] Preflight prints branch, HEAD, worktree, status, worktree list, mandatory reading list, and session-gate reminder.
- [ ] Scripts do not modify, stage, commit, access the network, or print environment variables.
- [ ] CI uses read-only permissions, no secrets, and pinned major action versions.
- [ ] CI runs the strict verifier and strict preflight only, never with `--allow-untracked`.
- [ ] No application, backend, schema, migration, package, lockfile, RNICA, HOPE, SFV, or patient-data file changed.
- [ ] Conflict register records the RNICA workflow-order and status-vocabulary reconciliations.
- [ ] Governance CI remains advisory until organizational adoption is confirmed.

## 7. Change control

Changes to constitutional files require an explicit constitutional amendment or product-authority decision. Changes to supporting governance files require review of both constitutions, conflict analysis, verifier tests, and CI validation.

## 8. What governance verification does and does not prove

Governance verification proves that required tracked governance files are present, readable, structurally valid, and internally consistent. It does not prove that an AI assistant read, understood, or obeyed every rule. Human review, visible checkpoints, scoped diffs, tests, and CI remain required.

## 9. Recurring governance checkpoint

A governance checkpoint is required at session start; after conversation compaction, summarization, restart, or model/context change; before moving from planning or auditing to implementation; before the first file edit; before expanding scope beyond the session-start report; after a branch, worktree, or HEAD change; after changing a governance or authority document; before staging; before committing; whenever the user indicates a governance rule may have been missed; and whenever the assistant cannot identify the current branch, HEAD, worktree, governing authorities, approved scope, or pre-existing changes. A prior checkpoint does not authorize continued work after any of these triggers, and current repository evidence always controls over conversation memory or an earlier summary.

Use this exact minimal format at every checkpoint. Blank fields are prohibited; use `NOT VERIFIED`, `NOT APPLICABLE`, `NOT FOUND`, `CONFLICTING`, or `BLOCKED` when appropriate. If `Implementation authorized` is `NO`, do not modify files. This checkpoint does not replace the full constitutional Section 18 session-start response — it is a shorter recurring refresh used after the full session gate has already been completed.

```
SNS GOVERNANCE CHECKPOINT

- Trigger:
- Repository root:
- Branch:
- HEAD:
- Worktree:
- Governance verification:
- Constitutions reviewed:
- Applicable feature authorities reviewed:
- Pre-existing changes protected:
- Approved scope:
- Intended files:
- Prohibited files:
- Implementation authorized: YES / NO
- Reason:
```
