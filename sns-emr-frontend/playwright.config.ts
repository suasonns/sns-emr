// HOPE-E2E-INFRA-001: Playwright config for SNS EMR frontend e2e tests.
//
// Deliberately does NOT auto-start the frontend dev server or the
// backend API via `webServer` (Playwright's reuseExistingServer /
// auto-spawn feature). In a multi-worktree environment it is entirely
// possible for ports 5173/8000 to already be bound by a *different*
// worktree's dev servers -- auto-reusing "whatever is listening" would
// silently test the wrong branch/commit and misreport results as
// passing/failing for this branch. Strict fail-not-fallback instead:
// the operator must start (or already have running) THIS worktree's
// `npm run dev` (port 5173) and backend `uvicorn` (port 8000) and verify
// that manually before running `npm run test:e2e`. If nothing is
// listening, tests simply fail with a clear connection-refused error
// instead of silently standing up or reusing an ambiguous server.
import { defineConfig, devices } from "@playwright/test";
import { RN_STORAGE_STATE_PATH } from "./e2e/support/storageStatePath";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: RN_STORAGE_STATE_PATH,
      },
      dependencies: ["setup"],
    },
  ],
});
