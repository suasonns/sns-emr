# SNS Hospice Solutions Copilot Instructions

This repository is governed by two complementary active constitutions:

1. `docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
2. `docs/tenant-platform/SNS_CONSTITUTION.md`

Before planning or editing:

1. Open and read both constitutions from the current worktree. Do not rely on memory or a prior session.
2. Read `AGENTS.md`.
3. Read `docs/governance/SNS_RULES_MANIFEST.json` and every entry marked `mandatory: true`.
4. Run `node scripts/sns-worktree-preflight.mjs` from the repository root.
5. Complete the session-start response required by Section 18 of the Repository-First Implementation Constitution. Blank fields are prohibited.
6. Read the applicable workstream, feature, design, data-mapping, lock/readiness, AI, and handoff authorities.
7. Inspect current implementation and tests before recommending or changing anything.

## Authority reconciliation

- Repository process and implementation discipline: Repository-First Implementation Constitution.
- Clinical, compliance, regulatory, eligibility-support, evidence, audit, and product-authority matters: SNS Constitution.
- Specific active workstream authorities control only their explicit scope and may not weaken constitutional safety controls.
- Approved design references control appearance; verified repository clinical logic controls behavior.
- On unresolved conflict, stop only the affected item, report both provisions and scopes, and request an explicit decision.

## Non-negotiable quick-reference rules

These restate the highest-risk constitutional rules so they stay visible during implementation. They do not replace either constitution; read the full constitutions for complete detail.

- Repository-first inspection is required before recommendations or changes. Prior conversation memory is never authoritative on its own.
- The full Section 18 session-start gate must be completed, with no blank fields, before the first file edit.
- No-assumption rule: never assume a feature, field, component, API, or test is missing or present — classify as VERIFIED, PARTIAL, NOT VERIFIED, CONFLICTING, NOT FOUND, or SUPERSEDED only after searching.
- Reuse before create.
- Implement an existing approved plan rather than producing another audit or roadmap, unless explicitly requested or genuinely blocked.
- Preserve RNICA clinical behavior during presentation-only work unless an approved defect authorizes a behavior change.
- **shadcn/ui is a primitive toolkit only, restyled through SNS theme tokens. Do not adopt shadcn templates, dashboards, application shells, generated layouts, or a competing design system.**
- **Redesigned screens require Desktop Light, Desktop Dark, Mobile Light, and Mobile Dark runtime verification before being called visually complete. Source, DOM, or computed-style inspection does not establish visual parity.**
- Stop on data loss, cross-patient or cross-tenant data, authorization failure, duplicate records, lock bypass, signature loss, audit loss, or migration drift.
- Never stage or commit without explicit authorization.
- Never create another constitution or duplicate constitutional text in a supporting governance file.
- Do not add dependencies, routes, schemas, migrations, roles, permissions, enums, or parallel architecture without repository evidence and authorization.

A worktree is not authorized for implementation until strict governance verification passes.

## Recurring Governance Checkpoint

A governance checkpoint is required:

1. At the start of every new session.
2. After conversation compaction, summarization, restart, or model/context change.
3. Before changing from planning or auditing to implementation.
4. Before the first file edit.
5. Before expanding scope or touching a file not listed in the session-start report.
6. After switching branches or worktrees.
7. After a rebase, merge, cherry-pick, or HEAD change.
8. After changing any governance or authority document.
9. Before staging.
10. Before committing.
11. Whenever the user states or suggests that governance rules were missed.
12. Whenever the assistant cannot identify the current branch, HEAD, worktree, governing authorities, approved scope, or pre-existing changes.

At each checkpoint:

- Re-open `AGENTS.md`.
- Re-open both constitutions.
- Re-open this file.
- Re-read `docs/governance/SNS_RULES_MANIFEST.json`.
- Re-read applicable feature authorities.
- Run strict preflight (`node scripts/sns-worktree-preflight.mjs`) when governance files are tracked.
- Compare current branch, HEAD, worktree, and status with the last checkpoint.
- Verify that intended files remain within approved scope.
- Stop if verification fails or authority is unclear.

Do not claim implementation authorization merely because a prior checkpoint passed.

### SNS Governance Checkpoint response format

Use this exact minimal format at every checkpoint. Blank fields are prohibited; use `NOT VERIFIED`, `NOT APPLICABLE`, `NOT FOUND`, `CONFLICTING`, or `BLOCKED` when appropriate. If `Implementation authorized` is `NO`, do not modify files.

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

This checkpoint does not replace the full constitutional Section 18 session-start response. It is a shorter recurring refresh used after the full session gate has already been completed.

## Fail closed after context loss

If conversation context has been compacted, summarized, restarted, or is otherwise incomplete, prior claims that governance was reviewed or implementation was authorized are no longer sufficient. Re-run the recurring governance checkpoint from current repository evidence before continuing.

Never infer current authorization from conversation memory, a previous summary, an earlier worktree, or a prior branch. Current repository evidence controls.
