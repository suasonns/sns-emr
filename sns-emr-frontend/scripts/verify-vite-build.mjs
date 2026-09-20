#!/usr/bin/env node
// Regression guard for the PR #91 dependency-closure incident.
//
// The frontend's `npm run build` script is `tsc -b && vite build`. When
// `tsc -b` fails (even on pre-existing, unrelated type errors), the `&&`
// short-circuits and `vite build` never runs -- so Rollup's import
// resolution, which is what actually catches missing local files
// (unresolved `./x` imports, missing `.css` files, etc.), silently never
// executes. That gap is exactly how a selective file merge shipped several
// files (DashboardOverviewV2.jsx, shell/icons.jsx, shell/tailwind.css, plus
// the Tailwind toolchain itself) that referenced dependencies never
// committed anywhere, without CI or `npm run build` ever failing.
//
// This script runs `vite build` directly, independent of `tsc`, and fails
// loudly (non-zero exit) if any import cannot be resolved. It intentionally
// does not replace `npm run build` (which still enforces the project's
// TypeScript baseline) -- it exists purely to guarantee import resolution
// is always checked, regardless of TS status.
import { build } from 'vite';

try {
  await build({
    logLevel: 'info',
    build: {
      write: false,
      // Keep this check fast; we only care whether Rollup can resolve
      // every import, not about producing an optimized bundle.
      minify: false,
      reportCompressedSize: false,
    },
  });
  console.log('\n✅ vite build import-resolution check passed: every local import resolved.');
} catch (error) {
  console.error('\n❌ vite build import-resolution check FAILED.');
  console.error('One or more local imports could not be resolved. See error below:\n');
  console.error(error);
  process.exit(1);
}
