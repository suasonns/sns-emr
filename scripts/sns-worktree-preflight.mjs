#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

function run(command, args, cwd, capture = false) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' },
  });
  if (result.status !== 0) {
    if (capture && result.stderr) process.stderr.write(result.stderr);
    process.exit(result.status ?? 1);
  }
  return capture ? (result.stdout || '').trim() : '';
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = run('git', ['rev-parse', '--show-toplevel'], scriptDir, true);
const verifier = path.join(root, 'scripts', 'verify-sns-worktree-rules.mjs');

const allowUntracked = process.argv.slice(2).includes('--allow-untracked');

if (allowUntracked) {
  console.log('INSTALLATION AUDIT ONLY');
  console.log('IMPLEMENTATION NOT AUTHORIZED');
  console.log('STRICT TRACKED-FILE VERIFICATION REQUIRED AFTER COMMIT');
} else {
  console.log('SNS GOVERNANCE PREFLIGHT');
  console.log('STRICT MODE');
  console.log('IMPLEMENTATION AUTHORIZATION DEPENDS ON COMPLETING THE CONSTITUTIONAL SESSION GATE');
}

const branch = run('git', ['branch', '--show-current'], root, true);
const head = run('git', ['rev-parse', 'HEAD'], root, true);
const detached = branch === '';

console.log(`\nRepository root: ${root}`);
console.log(`Current worktree: ${root}`);
console.log(`Branch: ${detached ? '(detached HEAD)' : branch}`);
console.log(`HEAD: ${head || '(unavailable)'}`);
console.log(`Detached HEAD: ${detached ? 'YES' : 'NO'}`);

if (allowUntracked) {
  run(process.execPath, [verifier, '--root', root, '--allow-untracked'], root);
} else {
  run(process.execPath, [verifier, '--root', root], root);
}

const manifestPath = path.join(root, 'docs', 'governance', 'SNS_RULES_MANIFEST.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const featureAuthorities = Array.isArray(manifest.featureAuthorities) ? manifest.featureAuthorities : [];
if (featureAuthorities.length) {
  console.log('\nConditional feature authorities (read only when the named workstream is in scope; not globally mandatory):');
  for (const entry of featureAuthorities) console.log(`- ${entry.path} — required when: ${entry.requiredWhen}`);
}

console.log('\nStaged files (git diff --cached --name-only):');
console.log(run('git', ['diff', '--cached', '--name-only'], root, true) || '(none)');

console.log('\nModified tracked files (git diff --name-only):');
console.log(run('git', ['diff', '--name-only'], root, true) || '(none)');

console.log('\nUntracked files (git ls-files --others --exclude-standard):');
console.log(run('git', ['ls-files', '--others', '--exclude-standard'], root, true) || '(none)');

console.log('\nFull git status (git status --short):');
run('git', ['status', '--short'], root);

console.log('\nGit worktrees:');
run('git', ['worktree', 'list', '--porcelain'], root);

console.log(`
Constitutional authorities (read in full; never modify without an explicit amendment):
- docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md
- docs/tenant-platform/SNS_CONSTITUTION.md

Conflict register:
- docs/governance/SNS_RULE_CONFLICT_REGISTER.md

Mandatory reading:
- AGENTS.md
- docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md
- docs/tenant-platform/SNS_CONSTITUTION.md
- .github/copilot-instructions.md
- docs/governance/SNS_RULES_MANIFEST.json
- docs/governance/SNS_GOVERNANCE_IMPLEMENTATION_GUIDE.md
- docs/governance/SNS_RULE_CONFLICT_REGISTER.md
- applicable workstream authorities

Before editing, complete Section 18 of the Repository-First Implementation Constitution with no blank fields.

Run a new SNS Governance Checkpoint after any branch change, worktree change, HEAD change, authority change, scope expansion, context compaction, summarization, restart, or model/context change. A prior checkpoint does not authorize continued work after any of these events. This preflight output proves required governance files are present and (in strict mode) tracked — it does not prove that the session has read, understood, or obeyed every rule.
`);
