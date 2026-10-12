// HOPE-E2E-UUID-REGRESSION-001: same literal pattern used by the
// existing static-scan regression test
// (src/test/noUuidInClinicalUi.test.js UUID_LITERAL_PATTERN) --
// duplicated intentionally rather than imported, because this file runs
// under Playwright's own TypeScript/Node toolchain (not Vitest), and a
// real-DOM check from a different runner is a stronger, independent
// regression signal than re-running the same static scan.
export const UUID_LITERAL_PATTERN = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

export function assertNoUuidLeak(bodyText: string, screenName: string) {
  const match = bodyText.match(UUID_LITERAL_PATTERN);
  if (match) {
    throw new Error(
      `[e2e] Clinician-facing screen "${screenName}" rendered an internal ` +
        `identifier (UUID-shaped value "${match[0]}") as visible text. ` +
        "Internal IDs may only exist in the DOM as non-visible attributes " +
        "(data-*, React keys) or inside audit/support tooling -- never as " +
        "rendered text in routine clinical workflow.",
    );
  }
}
