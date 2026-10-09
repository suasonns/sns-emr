import { describe, expect, it } from "vitest";

import appSource from "./App.tsx?raw";

/**
 * Regression test for the development-only Body Systems preview route added
 * to App.tsx. Verified empirically once (see the implementation session
 * notes): `npm run dev` served `/__dev-preview/body-systems` with HTTP 200,
 * and `npm run build`'s output bundle (`dist/assets/index-*.js`) contains no
 * occurrence of the string `__dev-preview` at all — Vite's static
 * replacement of `import.meta.env.DEV` with `false` lets its dead-code
 * elimination strip the Route, its element, and the gating `&&` entirely
 * from the production bundle. This test pins the *source* invariants that
 * make that behavior reliable, so a future edit can't silently reintroduce
 * the route unconditionally or surface it in navigation.
 */
describe("App.tsx — development-only Body Systems preview route", () => {
  it("imports BodySystemsWorkspacePreview only from the narrowed-shell feature barrel", () => {
    expect(appSource).toContain('import { BodySystemsWorkspacePreview } from "./features/body-systems";');
  });

  it("gates the preview route behind import.meta.env.DEV", () => {
    expect(appSource).toMatch(
      /\{import\.meta\.env\.DEV\s*&&\s*\(\s*<Route\s+path="\/__dev-preview\/body-systems"\s+element=\{<BodySystemsWorkspacePreview \/>\}\s*\/>\s*\)\s*\}/,
    );
  });

  it("does not reference the preview route path anywhere else in the app (no navigation/menu leakage)", () => {
    const modules = import.meta.glob("./**/*.{ts,tsx,js,jsx}", { eager: true, query: "?raw", import: "default" }) as Record<
      string,
      string
    >;
    for (const [filePath, content] of Object.entries(modules)) {
      if (filePath.endsWith("/App.tsx") || filePath.endsWith("App.devPreviewRoute.test.ts")) {
        continue;
      }
      expect(content, `unexpected "__dev-preview" reference in ${filePath}`).not.toContain("__dev-preview");
    }
  });
});
