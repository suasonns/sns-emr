# SNS Hospice Solutions Agent Entry Point

**Status:** Active governance entry point

**Authority:** This file is not a constitution and does not create independent clinical, compliance, or engineering policy.

## Required authorities

Before planning, recommending, or modifying repository content, read both active constitutions from the current worktree:

1. `docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
2. `docs/tenant-platform/SNS_CONSTITUTION.md`

Also read:

- `.github/copilot-instructions.md`
- `docs/governance/SNS_RULES_MANIFEST.json`
- every manifest entry marked `mandatory: true`
- every feature or workstream authority applicable to the requested task

## Mandatory preflight

Run from the repository root:

```bash
node scripts/sns-worktree-preflight.mjs
```

No implementation is authorized until preflight passes and the mandatory session-start response in the Repository-First Implementation Constitution is completed with no blank fields.

## Reconciled authority model

- The Repository-First Implementation Constitution governs repository process, implementation discipline, reuse, UI verification, migrations, Git safety, and session gates.
- The SNS Constitution governs clinical, regulatory, compliance, eligibility-support, data-ownership, evidence, audit, and product-authority matters.
- A more specific active workstream authority may control its explicit subject, but it may not weaken either constitution's safety controls.
- If an unresolved conflict remains, stop only the affected item, identify both provisions and their scopes, and request an explicit product-authority decision. Continue only unaffected authorized work.

## Non-negotiable safety rules

- Repository evidence must be refreshed in the current worktree. Conversation memory is not authority.
- Preserve unrelated modified and untracked work.
- Never run `git add .`, `git add -A`, `git reset --hard`, `git clean`, or an automatic stash.
- Do not stage or commit unless the current request explicitly authorizes it.
- Use synthetic data by default. Never place identifiable patient data or secrets in source, fixtures, prompts, logs, screenshots, tickets, or commits.
- Do not convert LCD or other supporting guidance into an automatic eligibility determination.
- AI may assist with extraction and suggestions but may not replace clinician judgment or mark clinical review complete without authorized clinician action.

## Recurring Governance Checkpoint

A governance checkpoint is required at session start; after compaction, summarization, restart, or model/context change; before moving from planning/auditing to implementation; before the first file edit; before expanding scope beyond the session-start report; after a branch, worktree, or HEAD change (including rebase, merge, or cherry-pick); after changing a governance or authority document; before staging; before committing; whenever the user indicates a rule may have been missed; and whenever the current branch, HEAD, worktree, governing authorities, approved scope, or pre-existing changes cannot be identified.

At each checkpoint, re-open this file, both constitutions, and `.github/copilot-instructions.md`; re-read `docs/governance/SNS_RULES_MANIFEST.json` and applicable feature authorities; run strict preflight when governance files are tracked; compare current branch/HEAD/worktree/status against the last checkpoint; and stop if verification fails or authority is unclear. A prior checkpoint does not authorize continued work after any of the triggers above. Use the exact `SNS GOVERNANCE CHECKPOINT` response format defined in `.github/copilot-instructions.md`.

If conversation context has been compacted, summarized, restarted, or is otherwise incomplete, a prior claim that governance was reviewed or implementation was authorized is no longer sufficient — re-run the checkpoint from current repository evidence. Never infer authorization from conversation memory, a previous summary, an earlier worktree, or a prior branch.

If this file conflicts with either active constitution, stop and apply the conflict process in `docs/governance/SNS_GOVERNANCE_IMPLEMENTATION_GUIDE.md`.
