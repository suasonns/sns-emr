#!/usr/bin/env node
import { access, constants, readFile, realpath, stat } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

function runGit(args, cwd) {
  const result = spawnSync('git', args, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' },
  });
  return {
    ok: result.status === 0,
    status: result.status,
    stdout: (result.stdout || '').trim(),
    stderr: (result.stderr || '').trim(),
  };
}

function parseArgs(argv) {
  const options = { allowUntracked: false, root: null };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--allow-untracked') options.allowUntracked = true;
    else if (argv[i] === '--root') options.root = argv[++i];
    else throw new Error(`Unknown argument: ${argv[i]}`);
  }
  return options;
}

function assertSafeRelativePath(value) {
  if (typeof value !== 'string' || value.length === 0) throw new Error('Manifest path must be a non-empty string.');
  if (path.isAbsolute(value)) throw new Error(`Manifest path must be relative: ${value}`);
  const normalized = path.normalize(value);
  if (normalized === '..' || normalized.startsWith(`..${path.sep}`)) throw new Error(`Manifest path escapes repository root: ${value}`);
  return normalized;
}

async function determineRoot(options) {
  if (options.root) return realpath(path.resolve(options.root));
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const result = runGit(['rev-parse', '--show-toplevel'], scriptDir);
  if (!result.ok) throw new Error(`Not inside a Git worktree: ${result.stderr || 'git rev-parse failed'}`);
  return realpath(result.stdout);
}

function detectTopLevelKeys(raw) {
  const keys = [];
  let i = 0;
  const len = raw.length;
  while (i < len && /\s/.test(raw[i])) i += 1;
  if (raw[i] !== '{') throw new Error('Manifest root must be a JSON object.');
  let depth = 1;
  i += 1;
  let expectKey = true;
  let inString = false;
  let escape = false;
  while (i < len) {
    const ch = raw[i];
    if (inString) {
      if (escape) { escape = false; i += 1; continue; }
      if (ch === '\\') { escape = true; i += 1; continue; }
      if (ch === '"') inString = false;
      i += 1;
      continue;
    }
    if (ch === '"') {
      if (depth === 1 && expectKey) {
        let j = i + 1;
        let key = '';
        let esc = false;
        while (j < len) {
          const c = raw[j];
          if (esc) { key += c; esc = false; j += 1; continue; }
          if (c === '\\') { esc = true; j += 1; continue; }
          if (c === '"') { j += 1; break; }
          key += c;
          j += 1;
        }
        keys.push(key);
        i = j;
        expectKey = false;
        continue;
      }
      inString = true;
      i += 1;
      continue;
    }
    if (ch === '{' || ch === '[') { depth += 1; i += 1; continue; }
    if (ch === '}' || ch === ']') { depth -= 1; i += 1; continue; }
    if (depth === 1 && ch === ',') { expectKey = true; i += 1; continue; }
    i += 1;
  }
  return keys;
}

const CONSTITUTION_PATHS = [
  'docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md',
  'docs/tenant-platform/SNS_CONSTITUTION.md',
];

const DRIFT_SCANNED_DOCS = [
  'AGENTS.md',
  '.github/copilot-instructions.md',
  'docs/governance/SNS_RULES_MANIFEST.json',
  'docs/governance/SNS_GOVERNANCE_IMPLEMENTATION_GUIDE.md',
  'docs/governance/SNS_RULE_CONFLICT_REGISTER.md',
  'docs/governance/SNS_CLINICAL_ARCHITECTURE.md',
  'docs/governance/SNS_DATA_HANDLING_RULES.md',
  'docs/governance/SNS_WORKTREE_PROTOCOL.md',
  '.github/workflows/sns-governance.yml',
];

const LEAKED_ARTIFACT_PATTERNS = [
  { label: 'SharePoint link', pattern: /sharepoint/i },
  { label: 'PDF citation artifact', pattern: /\.pdf\b/i },
  { label: 'bare URL', pattern: /https?:\/\//i },
  { label: 'attachment path', pattern: /attachments[\\/]/i },
  { label: 'temporary extraction path', pattern: /sns-reconciled-extracted|sns-governance-[A-Za-z0-9]/i },
  { label: 'Windows absolute path', pattern: /[A-Za-z]:\\\\?Users|[A-Za-z]:\/Users/i },
  { label: 'OS temp directory path', pattern: /AppData[\\/]Local[\\/]Temp/i },
];

const COPILOT_INSTRUCTIONS_MARKERS = [
  ['references the Repository-First Implementation Constitution', (c) => c.includes('docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md')],
  ['references the SNS Constitution', (c) => c.includes('docs/tenant-platform/SNS_CONSTITUTION.md')],
  ['includes the recurring governance checkpoint requirement', (c) => c.includes('Recurring Governance Checkpoint')],
  ['includes the shadcn/ui primitive-only rule', (c) => c.toLowerCase().includes('shadcn/ui is a primitive toolkit only')],
  ['includes the four-mode visual verification rule', (c) => ['Desktop Light', 'Desktop Dark', 'Mobile Light', 'Mobile Dark'].every((token) => c.includes(token))],
  ['includes the context-loss revalidation rule', (c) => c.toLowerCase().includes('compacted, summarized, restarted')],
  ['prohibits automatic staging or committing', (c) => c.toLowerCase().includes('never stage or commit')],
];

async function readIfExists(absolute) {
  try {
    return await readFile(absolute, 'utf8');
  } catch {
    return null;
  }
}

async function runDriftChecks(root) {
  for (const relative of DRIFT_SCANNED_DOCS) {
    const content = await readIfExists(path.resolve(root, relative));
    if (content === null) continue;
    if (/SNS_RULES_MANIFEST\.md/.test(content)) {
      throw new Error(`Stale manifest reference to SNS_RULES_MANIFEST.md found in ${relative}`);
    }
    for (const { label, pattern } of LEAKED_ARTIFACT_PATTERNS) {
      if (pattern.test(content)) throw new Error(`${label} found in ${relative}`);
    }
  }

  const legacyManifest = await readIfExists(path.resolve(root, 'docs/governance/SNS_RULES_MANIFEST.md'));
  if (legacyManifest !== null) throw new Error('Legacy docs/governance/SNS_RULES_MANIFEST.md must not exist.');

  const copilotInstructions = await readIfExists(path.resolve(root, '.github/copilot-instructions.md'));
  if (copilotInstructions !== null) {
    const missingMarkers = COPILOT_INSTRUCTIONS_MARKERS.filter(([, test]) => !test(copilotInstructions)).map(([label]) => label);
    if (missingMarkers.length) {
      throw new Error(`.github/copilot-instructions.md is missing required governance markers: ${missingMarkers.join('; ')}`);
    }
  }

  const ciWorkflow = await readIfExists(path.resolve(root, '.github/workflows/sns-governance.yml'));
  if (ciWorkflow !== null && ciWorkflow.includes('--allow-untracked')) {
    throw new Error('.github/workflows/sns-governance.yml must use strict verification only; it must not pass --allow-untracked.');
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const root = await determineRoot(options);
  const rootWithSep = `${root}${path.sep}`;
  const manifestRelative = 'docs/governance/SNS_RULES_MANIFEST.json';
  const manifestPath = path.join(root, manifestRelative);
  const manifestRaw = await readFile(manifestPath, 'utf8');

  const topLevelKeys = detectTopLevelKeys(manifestRaw);
  const topLevelDuplicates = topLevelKeys.filter((value, index) => topLevelKeys.indexOf(value) !== index);
  if (topLevelDuplicates.length) {
    throw new Error(`Duplicate top-level manifest keys: ${[...new Set(topLevelDuplicates)].join(', ')}`);
  }
  const mandatoryFilesKeyCount = topLevelKeys.filter((key) => key === 'mandatoryFiles').length;
  if (mandatoryFilesKeyCount !== 1) {
    throw new Error(`Manifest must contain exactly one "mandatoryFiles" key (found ${mandatoryFilesKeyCount}).`);
  }
  const featureAuthoritiesKeyCount = topLevelKeys.filter((key) => key === 'featureAuthorities').length;
  if (featureAuthoritiesKeyCount > 1) {
    throw new Error(`Manifest must not duplicate the "featureAuthorities" key (found ${featureAuthoritiesKeyCount}).`);
  }

  const manifest = JSON.parse(manifestRaw);

  if (manifest.schemaVersion !== 1 || !Array.isArray(manifest.mandatoryFiles)) {
    throw new Error('Unsupported or invalid governance manifest schema.');
  }

  const required = manifest.mandatoryFiles.filter((entry) => entry.mandatory === true);
  const paths = required.map((entry) => assertSafeRelativePath(entry.path));
  const duplicates = paths.filter((value, index) => paths.indexOf(value) !== index);
  if (duplicates.length) throw new Error(`Duplicate mandatory manifest paths: ${[...new Set(duplicates)].join(', ')}`);

  for (const constitutionPath of CONSTITUTION_PATHS) {
    if (!paths.includes(path.normalize(constitutionPath))) throw new Error(`Manifest is missing required constitutional authority: ${constitutionPath}`);
  }
  for (const explicitPath of ['AGENTS.md', '.github/copilot-instructions.md']) {
    if (!paths.includes(path.normalize(explicitPath))) throw new Error(`Manifest must list ${explicitPath} as mandatory.`);
  }

  const featureAuthorities = Array.isArray(manifest.featureAuthorities) ? manifest.featureAuthorities : [];
  const featurePaths = featureAuthorities.map((entry) => assertSafeRelativePath(entry.path));
  const featureDuplicates = featurePaths.filter((value, index) => featurePaths.indexOf(value) !== index);
  if (featureDuplicates.length) throw new Error(`Duplicate featureAuthorities paths: ${[...new Set(featureDuplicates)].join(', ')}`);

  await runDriftChecks(root);

  const missing = [];
  const unreadable = [];
  const untracked = [];

  for (const relative of paths) {
    const absolute = path.resolve(root, relative);
    if (absolute !== root && !absolute.startsWith(rootWithSep)) throw new Error(`Resolved path escapes repository root: ${relative}`);
    try {
      const info = await stat(absolute);
      if (!info.isFile()) unreadable.push(`${relative} (not a regular file)`);
      else await access(absolute, constants.R_OK);
    } catch {
      missing.push(relative);
      continue;
    }
    const tracked = runGit(['ls-files', '--error-unmatch', '--', relative], root);
    if (!tracked.ok) untracked.push(relative);
  }

  const featureStatus = [];
  for (const relative of featurePaths) {
    const absolute = path.resolve(root, relative);
    if (absolute !== root && !absolute.startsWith(rootWithSep)) throw new Error(`Resolved path escapes repository root: ${relative}`);
    try {
      await stat(absolute);
      featureStatus.push({ relative, present: true });
    } catch {
      featureStatus.push({ relative, present: false });
    }
  }

  const branchResult = runGit(['branch', '--show-current'], root);
  const headResult = runGit(['rev-parse', '--short=12', 'HEAD'], root);
  const worktreeResult = runGit(['rev-parse', '--show-toplevel'], root);

  console.log(`Repository: ${root}`);
  console.log(`Worktree: ${worktreeResult.ok ? worktreeResult.stdout : root}`);
  console.log(`Branch: ${branchResult.stdout || '(detached HEAD)'}`);
  console.log(`HEAD: ${headResult.ok ? headResult.stdout : '(unavailable)'}`);
  console.log('\nMandatory governance files:');
  for (const relative of paths) console.log(`- ${relative}`);

  if (featureStatus.length) {
    console.log('\nConditional feature authorities (not globally mandatory):');
    for (const entry of featureStatus) console.log(`- ${entry.relative}${entry.present ? '' : ' (NOT FOUND — informational only, does not fail verification)'}`);
  }

  if (missing.length) console.error(`\nMissing:\n${missing.map((x) => `- ${x}`).join('\n')}`);
  if (unreadable.length) console.error(`\nUnreadable:\n${unreadable.map((x) => `- ${x}`).join('\n')}`);
  if (untracked.length) console.error(`\nUntracked:\n${untracked.map((x) => `- ${x}`).join('\n')}`);

  const strictFailure = missing.length || unreadable.length || (!options.allowUntracked && untracked.length);
  if (strictFailure) {
    process.exitCode = 1;
    return;
  }
  if (options.allowUntracked && untracked.length) {
    console.warn('\nInstallation audit passed with untracked files allowed. This does not authorize implementation.');
    return;
  }
  console.log('\nSNS governance verification passed.');
}

main().catch((error) => {
  console.error(`SNS governance verification failed: ${error.message}`);
  process.exitCode = 1;
});
