import test from 'node:test';
import assert from 'node:assert/strict';
import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const mandatory = JSON.parse(await readFile(path.join(sourceRoot, 'docs/governance/SNS_RULES_MANIFEST.json'), 'utf8')).mandatoryFiles.filter((x) => x.mandatory).map((x) => x.path);

function run(command, args, cwd) {
  return spawnSync(command, args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), 'sns-governance-'));
  for (const relative of mandatory) {
    const src = path.join(sourceRoot, relative);
    const dest = path.join(root, relative);
    await cp(src, dest, { recursive: true, force: true });
  }
  run('git', ['init', '-q'], root);
  run('git', ['config', 'user.email', 'governance-test@example.invalid'], root);
  run('git', ['config', 'user.name', 'SNS Governance Test'], root);
  run('git', ['add', '--', ...mandatory], root);
  run('git', ['commit', '-qm', 'governance fixture'], root);
  return root;
}

test('passes when all mandatory files exist and are tracked', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.equal(result.status, 0, result.stderr);
});

test('fails when a mandatory file is missing', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await rm(path.join(root, 'AGENTS.md'));
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Missing:/);
});

test('fails when a mandatory file is present but untracked', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  run('git', ['rm', '--cached', '--quiet', '--', 'AGENTS.md'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Untracked:/);
});

test('verification does not modify tracked content or stage files', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const before = run('git', ['status', '--porcelain=v1'], root).stdout;
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  const after = run('git', ['status', '--porcelain=v1'], root).stdout;
  assert.equal(result.status, 0, result.stderr);
  assert.equal(after, before);
});

async function writeManifest(root, overrides) {
  const manifestPath = path.join(root, 'docs/governance/SNS_RULES_MANIFEST.json');
  const base = JSON.parse(await readFile(manifestPath, 'utf8'));
  const next = { ...base, ...overrides };
  await writeFile(manifestPath, JSON.stringify(next, null, 2));
  run('git', ['add', '--', 'docs/governance/SNS_RULES_MANIFEST.json'], root);
  run('git', ['commit', '-qm', 'manifest override'], root);
}

test('absent conditional featureAuthorities do not fail global verification', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeManifest(root, {
    featureAuthorities: [
      { name: 'Nonexistent feature', path: 'docs/design/does-not-exist/SPEC.md', requiredWhen: 'test only' },
    ],
  });
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /NOT FOUND — informational only, does not fail verification/);
});

test('duplicate feature-authority paths are detected', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeManifest(root, {
    featureAuthorities: [
      { name: 'Dup A', path: 'AGENTS.md', requiredWhen: 'test only' },
      { name: 'Dup B', path: 'AGENTS.md', requiredWhen: 'test only' },
    ],
  });
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Duplicate featureAuthorities paths/);
});

test('feature-authority paths escaping the repository root are rejected', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeManifest(root, {
    featureAuthorities: [
      { name: 'Escaping path', path: '../outside-repo/SPEC.md', requiredWhen: 'test only' },
    ],
  });
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /escapes repository root/);
});

test('duplicate mandatory manifest paths are detected', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifestPath = path.join(root, 'docs/governance/SNS_RULES_MANIFEST.json');
  const base = JSON.parse(await readFile(manifestPath, 'utf8'));
  base.mandatoryFiles.push({ ...base.mandatoryFiles[0] });
  await writeFile(manifestPath, JSON.stringify(base, null, 2));
  run('git', ['add', '--', 'docs/governance/SNS_RULES_MANIFEST.json'], root);
  run('git', ['commit', '-qm', 'duplicate mandatory path'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Duplicate mandatory manifest paths/);
});

test('absolute manifest paths are rejected', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifestPath = path.join(root, 'docs/governance/SNS_RULES_MANIFEST.json');
  const base = JSON.parse(await readFile(manifestPath, 'utf8'));
  base.mandatoryFiles.push({ path: path.join(root, 'AGENTS.md'), category: 'bad', mandatory: true });
  await writeFile(manifestPath, JSON.stringify(base, null, 2));
  run('git', ['add', '--', 'docs/governance/SNS_RULES_MANIFEST.json'], root);
  run('git', ['commit', '-qm', 'absolute mandatory path'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must be relative/);
});

async function removeLinesMatching(root, relative, pattern) {
  const target = path.join(root, relative);
  const original = await readFile(target, 'utf8');
  const mutated = original
    .split('\n')
    .filter((line) => !pattern.test(line))
    .join('\n');
  await writeFile(target, mutated);
  run('git', ['add', '--', relative], root);
  run('git', ['commit', '-qm', 'marker removal fixture'], root);
}

async function assertCopilotInstructionsMarkerFailure(t, pattern, expectedMessageFragment) {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await removeLinesMatching(root, '.github/copilot-instructions.md', pattern);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /missing required governance markers/i);
  assert.match(result.stderr, expectedMessageFragment);
}

test('missing recurring-checkpoint marker fails', (t) =>
  assertCopilotInstructionsMarkerFailure(t, /Recurring Governance Checkpoint/, /recurring governance checkpoint/i));

test('missing context-loss revalidation marker fails', (t) =>
  assertCopilotInstructionsMarkerFailure(t, /compacted, summarized, restarted/i, /context-loss revalidation/i));

test('missing shadcn primitive-only marker fails', (t) =>
  assertCopilotInstructionsMarkerFailure(t, /shadcn\/ui is a primitive toolkit only/i, /shadcn/i));

test('missing four-mode verification marker fails', (t) =>
  assertCopilotInstructionsMarkerFailure(t, /Desktop Light/, /four-mode visual verification/i));

test('missing no-auto-stage/no-auto-commit marker fails', (t) =>
  assertCopilotInstructionsMarkerFailure(t, /never stage or commit/i, /staging or committing/i));

test('duplicate top-level JSON keys fail before normal JSON parsing can silently apply last-key-wins behavior', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifestPath = path.join(root, 'docs/governance/SNS_RULES_MANIFEST.json');
  const original = await readFile(manifestPath, 'utf8');
  const mutated = original.replace('{', '{\n  "schemaVersion": 999,');
  await writeFile(manifestPath, mutated);
  run('git', ['add', '--', 'docs/governance/SNS_RULES_MANIFEST.json'], root);
  run('git', ['commit', '-qm', 'duplicate top-level key fixture'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Duplicate top-level manifest keys/);
});

test('CI workflow using --allow-untracked fails governance validation', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const relative = '.github/workflows/sns-governance.yml';
  const original = await readFile(path.join(root, relative), 'utf8');
  assert.ok(original.includes('node scripts/verify-sns-worktree-rules.mjs'), 'test fixture assumption failed');
  const mutated = original.replace('node scripts/verify-sns-worktree-rules.mjs', 'node scripts/verify-sns-worktree-rules.mjs --allow-untracked');
  await writeFile(path.join(root, relative), mutated);
  run('git', ['add', '--', relative], root);
  run('git', ['commit', '-qm', 'ci drift fixture'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must not pass --allow-untracked/i);
});

test('installation mode still reports implementation as unauthorized', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  run('git', ['rm', '--cached', '--quiet', '--', 'AGENTS.md'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root, '--allow-untracked'], root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stderr, /does not authorize implementation/);
});

test('strict mode still fails while mandatory governance files are untracked', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  run('git', ['rm', '--cached', '--quiet', '--', 'docs/governance/SNS_WORKTREE_PROTOCOL.md'], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Untracked:/);
});

test('detached HEAD is reported clearly and does not fail solely because HEAD is detached', async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const head = run('git', ['rev-parse', 'HEAD'], root).stdout.trim();
  run('git', ['checkout', '-q', head], root);
  const result = run(process.execPath, [path.join(root, 'scripts/verify-sns-worktree-rules.mjs'), '--root', root], root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Branch: \(detached HEAD\)/);
});
