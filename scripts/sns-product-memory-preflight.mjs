#!/usr/bin/env node
// SNS Product-Memory Preflight
//
// Non-destructive, read-only verification of docs/governance/SNS_AUTHORITATIVE_DOCUMENTS.json.
// This is NOT a replacement for scripts/sns-worktree-preflight.mjs (repository/worktree governance);
// it specifically guards against the failure mode of architecture or implementation work being
// reasoned from an incomplete, missing, hash-mismatched, or ambiguously-superseded authoritative
// document (e.g. a truncated docs/SNS_DESIGN_SYSTEM_1.0.md).
//
// This script MUST NOT: stash, reset, checkout over work, clean untracked files, rewrite history,
// alter application files, stage files, or commit. It only reads and reports.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' },
  });
  return (result.stdout || '').trim();
}

function sha256(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex').toUpperCase();
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = run('git', ['rev-parse', '--show-toplevel'], scriptDir) || process.cwd();
const registryPath = path.join(root, 'docs', 'governance', 'SNS_AUTHORITATIVE_DOCUMENTS.json');

console.log('SNS PRODUCT-MEMORY PREFLIGHT');
console.log('READ-ONLY — NO STAGE, NO COMMIT, NO STASH, NO RESET, NO CHECKOUT, NO CLEAN');

const branch = run('git', ['branch', '--show-current'], root) || '(detached HEAD)';
const head = run('git', ['rev-parse', 'HEAD'], root) || '(unavailable)';
console.log(`\nRepository root: ${root}`);
console.log(`Branch: ${branch}`);
console.log(`HEAD: ${head}`);

console.log('\nWorking-tree status (git status --short) — protected, not modified by this script:');
console.log(run('git', ['status', '--short'], root) || '(clean)');

if (!existsSync(registryPath)) {
  console.log('\nFAIL CLOSED: docs/governance/SNS_AUTHORITATIVE_DOCUMENTS.json is missing.');
  console.log('No authoritative-document verification is possible. Do not proceed with architecture or implementation work.');
  process.exit(1);
}

let registry;
try {
  registry = JSON.parse(readFileSync(registryPath, 'utf8'));
} catch (err) {
  console.log(`\nFAIL CLOSED: docs/governance/SNS_AUTHORITATIVE_DOCUMENTS.json is not valid JSON (${err.message}).`);
  process.exit(1);
}

const documents = Array.isArray(registry.documents) ? registry.documents : [];
const problems = [];
const superseded = [];
const missing = [];
const ok = [];

for (const doc of documents) {
  const fullPath = path.join(root, doc.path);
  if (!existsSync(fullPath)) {
    missing.push(doc);
    problems.push(`MISSING: [${doc.id}] ${doc.path}`);
    continue;
  }
  if (doc.status === 'superseded') {
    superseded.push(doc);
    continue;
  }
  if (typeof doc.sha256 === 'string' && doc.sha256.length > 0) {
    const actual = sha256(fullPath);
    if (actual !== doc.sha256.toUpperCase()) {
      problems.push(
        `HASH MISMATCH: [${doc.id}] ${doc.path}\n  registry:  ${doc.sha256}\n  on disk:   ${actual}\n  This file may have been truncated, edited, or replaced since it was last verified. Treat as unverified until reconciled.`
      );
      continue;
    }
  }
  ok.push(doc);
}

// Ambiguous-supersession / numbering-collision check: multiple documents sharing a short
// ADR-style number token extracted from the title (e.g. "ADR-004") across different paths.
const numberGroups = new Map();
for (const doc of documents) {
  const match = /^(ADR-\d+)/i.exec(doc.title || '');
  if (!match) continue;
  const key = match[1].toUpperCase();
  if (!numberGroups.has(key)) numberGroups.set(key, []);
  numberGroups.get(key).push(doc);
}
const collisions = [...numberGroups.entries()].filter(([, docs]) => docs.length > 1);

console.log(`\nAuthoritative documents registered: ${documents.length}`);
console.log(`Verified OK (exists, hash matches or unspecified): ${ok.length}`);
console.log(`Superseded (skipped from hash check by design): ${superseded.length}`);
console.log(`Missing: ${missing.length}`);
console.log(`Hash mismatches / other problems: ${problems.length - missing.length}`);

if (collisions.length) {
  console.log('\nAmbiguous numbering detected (do not resolve silently):');
  for (const [number, docs] of collisions) {
    console.log(`  ${number} is shared by ${docs.length} unrelated documents:`);
    for (const doc of docs) console.log(`    - [${doc.id}] ${doc.title} (${doc.path})`);
  }
}

if (problems.length) {
  console.log('\nFAIL CLOSED — unresolved authoritative-document problems:');
  for (const p of problems) console.log(`- ${p}`);
  process.exit(1);
}

console.log('\nAUTHORITIES ALIGNED');
process.exit(0);
